"""
extract.py
Etapa de EXTRAÇÃO (Extract) do pipeline.

Busca séries econômicas públicas do Banco Central do Brasil (BCB/SGS)
e salva os dados brutos em arquivos JSON versionados por execução.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import requests


BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"

SERIES = {
    "dolar": 1,
    "ipca": 433,
    "selic": 4390,
}

RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"

DIAS_HISTORICO = 365


def buscar_serie(nome: str, codigo: int) -> list:
    """Busca uma série do BCB dentro de um intervalo de datas."""

    data_final = datetime.now()
    data_inicial = data_final - timedelta(days=DIAS_HISTORICO)

    url = f"{BASE_URL}.{codigo}/dados"

    params = {
        "formato": "json",
        "dataInicial": data_inicial.strftime("%d/%m/%Y"),
        "dataFinal": data_final.strftime("%d/%m/%Y"),
    }

    print(
        f"[extract] buscando série '{nome}' (codigo={codigo}) "
        f"de {params['dataInicial']} até {params['dataFinal']}"
    )

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def salvar_dados(nome: str, dados: list) -> Path:
    """Salva os dados brutos da série em JSON."""

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    caminho = RAW_DATA_DIR / f"{nome}_{timestamp}.json"

    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=2,
        )

    return caminho


def main():
    for nome, codigo in SERIES.items():
        try:
            dados = buscar_serie(nome, codigo)

            caminho = salvar_dados(nome, dados)

            print(
                f"[extract] '{nome}': "
                f"{len(dados)} registros salvos em {caminho}"
            )

        except requests.RequestException as erro:
            print(f"[extract] ERRO ao buscar '{nome}': {erro}")

        except (ValueError, TypeError) as erro:
            print(f"[extract] ERRO ao processar '{nome}': {erro}")


if __name__ == "__main__":
    main()