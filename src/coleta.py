"""Coleta da cotação do dólar na API de Séries Temporais (SGS) do Banco Central."""

import time
from datetime import date, timedelta

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL_SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"

# Série 1: Taxa de câmbio livre - Dólar americano (venda) - diária
SERIE_DOLAR_VENDA = 1

# A API aceita até 10 anos por consulta, mas costuma ficar lenta com janelas grandes.
# Pedir um ano por vez deixa cada resposta pequena e rápida.
DIAS_POR_JANELA = 365

# (tempo para conectar, tempo para receber a resposta), em segundos
TIMEOUT = (10, 90)

CABECALHOS = {
    "User-Agent": "Mozilla/5.0 (analise-cotacao-dolar; +https://github.com/pedromeneghelli/analise-cotacao-dolar)",
    "Accept": "application/json",
}


def criar_sessao() -> requests.Session:
    """Sessão HTTP que tenta de novo automaticamente em caso de lentidão ou erro do servidor."""
    tentativas = Retry(
        total=5,
        backoff_factor=2,  # espera 2s, 4s, 8s, 16s... entre as tentativas
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    sessao = requests.Session()
    sessao.headers.update(CABECALHOS)
    sessao.mount("https://", HTTPAdapter(max_retries=tentativas))
    return sessao


def gerar_janelas(inicio: date, fim: date, dias: int = DIAS_POR_JANELA):
    """Divide o período em janelas consecutivas, sem buracos nem sobreposição."""
    if inicio > fim:
        raise ValueError("A data inicial não pode ser maior que a data final.")
    atual = inicio
    while atual <= fim:
        limite = min(atual + timedelta(days=dias - 1), fim)
        yield atual, limite
        atual = limite + timedelta(days=1)


def baixar_serie(codigo: int, inicio: date, fim: date) -> pd.DataFrame:
    """Baixa uma série do SGS e devolve um DataFrame com as colunas 'data' e 'valor'."""
    registros = []
    janelas = list(gerar_janelas(inicio, fim))
    with criar_sessao() as sessao:
        for numero, (ini, fi) in enumerate(janelas, start=1):
            print(f"  [{numero}/{len(janelas)}] {ini:%d/%m/%Y} a {fi:%d/%m/%Y}")
            params = {
                "formato": "json",
                "dataInicial": ini.strftime("%d/%m/%Y"),
                "dataFinal": fi.strftime("%d/%m/%Y"),
            }
            resposta = sessao.get(URL_SGS.format(codigo=codigo), params=params, timeout=TIMEOUT)
            if resposta.status_code == 404:
                # Janela sem dados (ex.: só fim de semana ou feriado)
                continue
            resposta.raise_for_status()
            registros.extend(resposta.json())
            time.sleep(0.5)  # pausa curta para não sobrecarregar a API

    return pd.DataFrame(registros, columns=["data", "valor"])
