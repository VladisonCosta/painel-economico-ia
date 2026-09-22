import json
import sqlite3

from scripts.load import carregar_arquivo, parse_data_bcb


def test_parse_data_bcb_converts_to_iso():
    assert parse_data_bcb("21/09/2026") == "2026-09-21"


def test_carregar_arquivo_is_idempotent(tmp_path):
    raw_file = tmp_path / "dolar_test.json"

    registros = [
        {"data": "20/09/2026", "valor": "5.10"},
        {"data": "21/09/2026", "valor": "5.11"},
    ]

    raw_file.write_text(
        json.dumps(registros),
        encoding="utf-8",
    )

    conn = sqlite3.connect(":memory:")

    conn.execute(
        """
        CREATE TABLE indicadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicador TEXT NOT NULL,
            data TEXT NOT NULL,
            valor REAL NOT NULL,
            UNIQUE(indicador, data)
        );
        """
    )

    primeira_carga = carregar_arquivo(conn, "dolar", raw_file)
    segunda_carga = carregar_arquivo(conn, "dolar", raw_file)

    total = conn.execute(
        "SELECT COUNT(*) FROM indicadores"
    ).fetchone()[0]

    conn.close()

    assert primeira_carga == 2
    assert segunda_carga == 0
    assert total == 2