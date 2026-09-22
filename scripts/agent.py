"""
agent.py
Camada de "Agentic AI" do projeto.

Expõe um endpoint HTTP (/perguntar) que:
1. Recebe uma pergunta em linguagem natural sobre os indicadores
   (ex: "como está o dólar nos últimos 30 dias?")
2. Busca no SQLite os dados relevantes para dar contexto
3. Envia pergunta + contexto para um LLM (via API da Groq)
4. Retorna a resposta gerada

Isso é uma versão simples do padrão "RAG" (Retrieval-Augmented Generation):
em vez do modelo "chutar" a resposta, ele responde com base nos dados reais
do seu banco.

Para rodar:
    1. Crie uma conta gratuita em https://console.groq.com e gere uma API key
    2. Copie .env.example para .env e cole sua chave em GROQ_API_KEY
    3. pip install -r requirements.txt
    4. uvicorn scripts.agent:app --reload
    5. Acesse http://localhost:8000/docs para testar
"""

import os
import sqlite3
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq

load_dotenv()

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "painel.db"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

app = FastAPI(title="Agente do Painel Econômico")


class Pergunta(BaseModel):
    texto: str
    dias: int = 30  # janela de dados usada como contexto


def buscar_contexto(dias: int) -> str:
    """Monta um resumo textual dos dados recentes, para dar contexto ao LLM."""
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=400,
            detail="Banco de dados não encontrado. Rode extract.py e load.py primeiro.",
        )

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        """
        SELECT indicador, data, valor
        FROM indicadores
        WHERE data >= date('now', ?)
        ORDER BY indicador, data
        """,
        conn,
        params=(f"-{dias} days",),
    )
    conn.close()

    if df.empty:
        return "Nenhum dado disponível para o período solicitado."

    linhas = []
    for indicador, grupo in df.groupby("indicador"):
        ultimo = grupo.iloc[-1]
        media = grupo["valor"].mean()
        linhas.append(
            f"- {indicador}: último valor = {ultimo['valor']:.4f} "
            f"(em {ultimo['data']}), média no período = {media:.4f}"
        )
    return "\n".join(linhas)


def perguntar_ao_llm(pergunta: str, contexto: str) -> str:
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY não configurada. Veja o .env.example.",
        )

    client = Groq(api_key=GROQ_API_KEY)

    prompt_sistema = (
        "Você é um assistente especializado em indicadores econômicos brasileiros. "
        "Responda SOMENTE com base nos dados de contexto fornecidos. "
        "Se o contexto não for suficiente para responder, diga isso claramente, "
        "em vez de inventar números."
    )

    mensagens = [
        {"role": "system", "content": prompt_sistema},
        {
            "role": "user",
            "content": f"Dados disponíveis:\n{contexto}\n\nPergunta: {pergunta}",
        },
    ]

    resposta = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=mensagens,
        temperature=0.2,
    )
    return resposta.choices[0].message.content


@app.post("/perguntar")
def perguntar(pergunta: Pergunta):
    contexto = buscar_contexto(pergunta.dias)
    resposta = perguntar_ao_llm(pergunta.texto, contexto)
    return {
        "pergunta": pergunta.texto,
        "contexto_usado": contexto,
        "resposta": resposta,
    }


@app.get("/saude")
def saude():
    return {"status": "ok"}
