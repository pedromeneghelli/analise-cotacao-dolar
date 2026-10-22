"""Gráficos estáticos para o README do projeto."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import pandas as pd  # noqa: E402

AZUL = "#2a78d6"
LARANJA = "#eb6834"
CINZA = "#8a8984"
TEXTO = "#52514e"
GRADE = "#e6e5e1"


def _estilo(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRADE)
    ax.tick_params(colors=TEXTO, labelsize=9)
    ax.grid(axis="y", color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)


def _formato_reais(valor, _pos):
    return f"R$ {valor:.2f}".replace(".", ",")


def grafico_cotacao(df: pd.DataFrame, destino: Path) -> Path:
    """Linha da cotação diária com a média móvel de 63 pregões."""
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
    ax.plot(df["data"], df["cotacao"], color=AZUL, linewidth=1.2, label="Cotação diária")
    ax.plot(df["data"], df["media_movel_63d"], color=CINZA, linewidth=2,
            label="Média móvel (63 pregões ≈ 3 meses)")
    ultimo = df.iloc[-1]
    ax.annotate(
        _formato_reais(ultimo["cotacao"], None),
        xy=(ultimo["data"], ultimo["cotacao"]),
        xytext=(6, 0), textcoords="offset points",
        va="center", fontsize=9, color=TEXTO, fontweight="bold",
    )
    _estilo(ax)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_formato_reais))
    ax.set_title("Dólar comercial (venda) em reais", loc="left", fontsize=12, color="#0b0b0b")
    ax.legend(frameon=False, fontsize=9, labelcolor=TEXTO, loc="upper left")
    fig.tight_layout()
    caminho = destino / "cotacao_historica.png"
    fig.savefig(caminho)
    plt.close(fig)
    return caminho


def grafico_variacao_mensal(mensal: pd.DataFrame, destino: Path, meses: int = 24) -> Path:
    """Barras com a variação % do fechamento mês a mês (últimos N meses)."""
    recorte = mensal.dropna(subset=["variacao_mes_pct"]).tail(meses)
    cores = [LARANJA if v > 0 else AZUL for v in recorte["variacao_mes_pct"]]
    rotulos = recorte["mes"].dt.strftime("%m/%y")

    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
    ax.bar(rotulos, recorte["variacao_mes_pct"], color=cores, width=0.7)
    ax.axhline(0, color=CINZA, linewidth=1)
    _estilo(ax)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _p: f"{v:+.0f}%".replace("+0%", "0%"))
    )
    ax.tick_params(axis="x", rotation=60)
    ax.set_title(
        f"Variação mensal do dólar (últimos {len(recorte)} meses)",
        loc="left", fontsize=12, color="#0b0b0b",
    )
    alta = plt.Rectangle((0, 0), 1, 1, color=LARANJA)
    queda = plt.Rectangle((0, 0), 1, 1, color=AZUL)
    ax.legend([alta, queda], ["Dólar subiu", "Dólar caiu"], frameon=False,
              fontsize=9, labelcolor=TEXTO, loc="upper left")
    fig.tight_layout()
    caminho = destino / "variacao_mensal.png"
    fig.savefig(caminho)
    plt.close(fig)
    return caminho
