"""Limpeza dos dados brutos e criação das tabelas usadas no Power BI."""

import pandas as pd

MESES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}
DIAS_SEMANA = {
    0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo",
}


def limpar(df_bruto: pd.DataFrame) -> pd.DataFrame:
    """Converte tipos, remove linhas inválidas e duplicadas e ordena por data."""
    df = df_bruto.copy()
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
    df["cotacao"] = pd.to_numeric(df["valor"], errors="coerce")
    df = (
        df.dropna(subset=["data", "cotacao"])
        .drop_duplicates(subset="data", keep="last")
        .sort_values("data")
        .loc[:, ["data", "cotacao"]]
        .reset_index(drop=True)
    )
    return df


def enriquecer(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona variação diária e médias móveis (21 pregões ≈ 1 mês, 63 ≈ 3 meses)."""
    df = df.copy()
    df["variacao_diaria_pct"] = df["cotacao"].pct_change() * 100
    df["media_movel_21d"] = df["cotacao"].rolling(21, min_periods=21).mean()
    df["media_movel_63d"] = df["cotacao"].rolling(63, min_periods=63).mean()
    return df


def resumo_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por mês: abertura, fechamento, média, mínima, máxima, variação e volatilidade."""
    serie = df.set_index("data")
    mensal = serie["cotacao"].resample("ME").agg(
        abertura="first", fechamento="last", media="mean", minima="min", maxima="max"
    )
    mensal["volatilidade_pct"] = serie["variacao_diaria_pct"].resample("ME").std()
    mensal["variacao_mes_pct"] = mensal["fechamento"].pct_change() * 100
    mensal = mensal.dropna(subset=["fechamento"])
    mensal.index = mensal.index.to_period("M").to_timestamp()
    return mensal.reset_index().rename(columns={"data": "mes"})


def dim_calendario(df: pd.DataFrame) -> pd.DataFrame:
    """Tabela de datas contínua, de 1º de janeiro a 31 de dezembro dos anos com dados.

    Anos completos permitem marcar a tabela como tabela de datas no Power BI e usar
    funções de inteligência temporal como SAMEPERIODLASTYEAR.
    """
    inicio = pd.Timestamp(year=df["data"].min().year, month=1, day=1)
    fim = pd.Timestamp(year=df["data"].max().year, month=12, day=31)
    datas = pd.date_range(inicio, fim, freq="D")
    cal = pd.DataFrame({"data": datas})
    cal["ano"] = cal["data"].dt.year
    cal["trimestre"] = "T" + cal["data"].dt.quarter.astype(str)
    cal["mes_numero"] = cal["data"].dt.month
    cal["mes_nome"] = cal["mes_numero"].map(MESES)
    cal["ano_mes"] = cal["data"].dt.strftime("%Y-%m")
    cal["dia_semana"] = cal["data"].dt.dayofweek.map(DIAS_SEMANA)
    cal["dia_util"] = cal["data"].dt.dayofweek < 5
    return cal
