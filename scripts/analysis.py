"""
analysis.py
Etapa de ANÁLISE do pipeline.

Lê os dados já carregados no SQLite (data/painel.db) e gera:
- um resumo estatístico por indicador (impresso no console)
- gráficos de evolução temporal salvos em data/graficos/
"""

import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # não depende de display gráfico
import matplotlib.pyplot as plt
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "painel.db"
GRAFICOS_DIR = DATA_DIR / "graficos"


def carregar_dados() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT indicador, data, valor FROM indicadores ORDER BY indicador, data",
        conn,
        parse_dates=["data"],
    )
    conn.close()
    return df


def resumo_estatistico(df: pd.DataFrame) -> pd.DataFrame:
    resumo = df.groupby("indicador")["valor"].agg(
        ultimo="last",
        media="mean",
        minimo="min",
        maximo="max",
        desvio_padrao="std",
    ).round(4)
    return resumo


def gerar_graficos(df: pd.DataFrame) -> None:
    GRAFICOS_DIR.mkdir(parents=True, exist_ok=True)
    for indicador, grupo in df.groupby("indicador"):
        plt.figure(figsize=(10, 4))
        plt.plot(grupo["data"], grupo["valor"], linewidth=1.5)
        plt.title(f"Evolução — {indicador}")
        plt.xlabel("Data")
        plt.ylabel("Valor")
        plt.tight_layout()
        caminho = GRAFICOS_DIR / f"{indicador}.png"
        plt.savefig(caminho, dpi=120)
        plt.close()
        print(f"[analysis] gráfico salvo em {caminho}")


def main():
    if not DB_PATH.exists():
        print("[analysis] banco não encontrado — rode extract.py e load.py primeiro.")
        return

    df = carregar_dados()
    if df.empty:
        print("[analysis] nenhum dado encontrado no banco.")
        return

    print("\n=== Resumo estatístico por indicador ===")
    print(resumo_estatistico(df).to_string())

    gerar_graficos(df)


if __name__ == "__main__":
    main()
