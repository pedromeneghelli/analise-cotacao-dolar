from datetime import date, timedelta

import pandas as pd
import pytest

from src.coleta import gerar_janelas
from src.tratamento import dim_calendario, enriquecer, limpar, resumo_mensal


def bruto_exemplo():
    return pd.DataFrame({
        "data": ["03/01/2025", "02/01/2025", "02/01/2025", "06/01/2025", "data ruim", "31/01/2025", "03/02/2025"],
        "valor": ["6.10", "6.00", "6.05", "6.20", "6.30", "x", "5.90"],
    })


def test_janelas_cobrem_o_periodo_sem_buracos():
    inicio, fim = date(2000, 1, 1), date(2026, 10, 22)
    janelas = list(gerar_janelas(inicio, fim))
    assert janelas[0][0] == inicio
    assert janelas[-1][1] == fim
    for (_, fim_a), (ini_b, _) in zip(janelas, janelas[1:]):
        assert ini_b == fim_a + timedelta(days=1)
    assert all((f - i).days < 3650 for i, f in janelas)


def test_janelas_rejeitam_periodo_invertido():
    with pytest.raises(ValueError):
        list(gerar_janelas(date(2026, 1, 2), date(2026, 1, 1)))


def test_limpar_converte_ordena_e_remove_invalidos():
    df = limpar(bruto_exemplo())
    assert list(df.columns) == ["data", "cotacao"]
    assert df["data"].is_monotonic_increasing
    assert df["data"].is_unique
    assert len(df) == 4  # duplicada, data inválida e valor inválido removidos
    assert df.loc[0, "cotacao"] == pytest.approx(6.05)  # mantém o último registro da data


def test_enriquecer_calcula_variacao_diaria():
    df = enriquecer(limpar(bruto_exemplo()))
    assert pd.isna(df.loc[0, "variacao_diaria_pct"])
    assert df.loc[1, "variacao_diaria_pct"] == pytest.approx((6.10 / 6.05 - 1) * 100)


def test_resumo_mensal():
    mensal = resumo_mensal(enriquecer(limpar(bruto_exemplo())))
    jan = mensal.iloc[0]
    assert jan["mes"] == pd.Timestamp("2025-01-01")
    assert jan["abertura"] == pytest.approx(6.05)
    assert jan["fechamento"] == pytest.approx(6.20)
    assert mensal.iloc[1]["variacao_mes_pct"] == pytest.approx((5.90 / 6.20 - 1) * 100)


def test_calendario_cobre_anos_completos():
    cal = dim_calendario(limpar(bruto_exemplo()))
    assert cal["data"].min() == pd.Timestamp("2025-01-01")
    assert cal["data"].max() == pd.Timestamp("2025-12-31")
    assert len(cal) == 365
    assert cal.loc[cal["data"] == "2025-03-01", "mes_nome"].item() == "Março"
