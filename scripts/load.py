"""
load.py
Etapa de CARGA (Load) do pipeline.

Lê os arquivos JSON brutos gerados por extract.py (data/raw/*.json)
e carrega em um banco SQLite estruturado (data/painel.db), na tabela
`indicadores`, evitando duplicatas.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "painel.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS indicadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicador TEXT NOT NULL,
    data TEXT NOT NULL,
    valor REAL NOT NULL,
    UNIQUE(indicador, data)
);
"""


def parse_data_bcb(data_str: str) -> str:
    """Converte 'dd/mm/aaaa' (formato do BCB) para 'aaaa-mm-dd' (formato ISO)."""
    return datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")


def get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_TABLE_SQL)
    return conn


def carregar_arquivo(conn: sqlite3.Connection, indicador: str, caminho: Path) -> int:
    with open(caminho, encoding="utf-8") as f:
        registros = json.load(f)

    inseridos = 0
    for registro in registros:
        try:
            data_iso = parse_data_bcb(registro["data"])
            valor = float(registro["valor"])
        except (KeyError, ValueError) as e:
            print(f"[load] registro inválido ignorado ({indicador}): {registro} ({e})")
            continue

        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO indicadores (indicador, data, valor)
            VALUES (?, ?, ?)
            """,
            (indicador, data_iso, valor),
        )
        inseridos += cursor.rowcount

    conn.commit()
    return inseridos


def main():
    conn = get_conn()
    if not RAW_DATA_DIR.exists():
        print("[load] nenhum dado bruto encontrado — rode extract.py primeiro.")
        return

    total = 0
    for arquivo in sorted(RAW_DATA_DIR.glob("*.json")):
        indicador = arquivo.stem.rsplit("_", 2)[0]  # remove timestamp do nome do arquivo
        n = carregar_arquivo(conn, indicador, arquivo)
        print(f"[load] '{indicador}' <- {arquivo.name}: {n} novos registros")
        total += n

    print(f"[load] total de novos registros inseridos: {total}")
    conn.close()


if __name__ == "__main__":
    main()
