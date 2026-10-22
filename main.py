"""Executa o pipeline completo: coleta -> tratamento -> arquivos para o Power BI -> gráficos.

Uso:
    python main.py                      # desde 2015 até hoje
    python main.py --inicio 2020-01-01  # período personalizado
"""

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from src.coleta import SERIE_DOLAR_VENDA, baixar_serie
from src.tratamento import dim_calendario, enriquecer, limpar, resumo_mensal
from src.visualizacao import grafico_cotacao, grafico_variacao_mensal

RAIZ = Path(__file__).parent
PASTA_BRUTO = RAIZ / "dados" / "bruto"
PASTA_TRATADO = RAIZ / "dados" / "tratados"
PASTA_IMAGENS = RAIZ / "imagens"

# Separador ";" e decimal "," para o Power BI em português abrir sem ajustes
OPCOES_CSV = {"sep": ";", "decimal": ",", "float_format": "%.4f", "index": False, "encoding": "utf-8-sig"}


def salvar(df, caminho: Path):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, **OPCOES_CSV)
    print(f"  salvo: {caminho.relative_to(RAIZ)} ({len(df)} linhas)")


def resumo_no_terminal(diario, mensal):
    ultimo = diario.iloc[-1]
    maximo = diario.loc[diario["cotacao"].idxmax()]
    um_ano_atras = diario[diario["data"] <= ultimo["data"] - pd.DateOffset(years=1)]
    print("\nResumo")
    print(f"  Última cotação: R$ {ultimo['cotacao']:.4f} em {ultimo['data']:%d/%m/%Y}")
    print(f"  Máxima do período: R$ {maximo['cotacao']:.4f} em {maximo['data']:%d/%m/%Y}")
    if not um_ano_atras.empty:
        base = um_ano_atras.iloc[-1]["cotacao"]
        print(f"  Variação em 12 meses: {(ultimo['cotacao'] / base - 1) * 100:+.2f}%")
    mais_volatil = mensal.loc[mensal["volatilidade_pct"].idxmax()]
    print(f"  Mês mais volátil: {mais_volatil['mes']:%m/%Y}")


def main():
    parser = argparse.ArgumentParser(description="Pipeline da cotação do dólar (BCB/SGS)")
    parser.add_argument("--inicio", type=date.fromisoformat, default=date(2015, 1, 1))
    parser.add_argument("--fim", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()

    print(f"Baixando série {SERIE_DOLAR_VENDA} de {args.inicio:%d/%m/%Y} a {args.fim:%d/%m/%Y}...")
    bruto = baixar_serie(SERIE_DOLAR_VENDA, args.inicio, args.fim)
    if bruto.empty:
        raise SystemExit("Nenhum dado retornado pela API para o período informado.")
    salvar(bruto, PASTA_BRUTO / "dolar_bruto.csv")

    print("Tratando dados...")
    diario = enriquecer(limpar(bruto))
    mensal = resumo_mensal(diario)
    calendario = dim_calendario(diario)
    salvar(diario, PASTA_TRATADO / "cotacao_diaria.csv")
    salvar(mensal, PASTA_TRATADO / "resumo_mensal.csv")
    salvar(calendario, PASTA_TRATADO / "dim_calendario.csv")

    print("Gerando gráficos...")
    PASTA_IMAGENS.mkdir(exist_ok=True)
    for caminho in (grafico_cotacao(diario, PASTA_IMAGENS), grafico_variacao_mensal(mensal, PASTA_IMAGENS)):
        print(f"  salvo: {caminho.relative_to(RAIZ)}")

    resumo_no_terminal(diario, mensal)


if __name__ == "__main__":
    main()
