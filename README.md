# Brazilian Economic Intelligence — Data Pipeline + AI Agent

End-to-end **Data Engineering, Data Analysis and Applied AI** project using real Brazilian economic indicators from the Central Bank of Brazil.

The project extracts economic data from the public BCB API, stores it in a structured SQLite database, generates statistical analyses and charts, and exposes an AI-powered API capable of answering natural-language questions using retrieved economic data as context.

---

## Project Overview

This project combines three areas in a single workflow:

- **Data Engineering** — extraction, transformation and structured storage
- **Data Analysis** — statistical analysis and visualization
- **Applied AI** — natural-language answers based on retrieved economic data

The objective is to demonstrate a complete workflow from raw public data to an API capable of answering questions using current information stored in the database.

---

## Architecture

```text
Central Bank of Brazil API
        |
        v
   extract.py
        |
        v
 Raw JSON files
   data/raw/
        |
        v
    load.py
        |
        v
     SQLite
 data/painel.db
     /      \
    /        \
   v          v
analysis.py  agent.py
    |        FastAPI
    |           |
    v           v
Statistics   SQL retrieval
and charts      |
                v
          Economic context
                |
                v
             Groq LLM
                |
                v
      Natural-language response
```

---

## Economic Indicators

The pipeline currently collects approximately one year of historical data for three Brazilian economic indicators:

- **USD/BRL exchange rate**
- **IPCA inflation index**
- **SELIC interest rate**

The data is retrieved from the public **SGS API of the Central Bank of Brazil**.

Different indicators have different publication frequencies, so the number of observations is not necessarily the same for every series.

---

# Data Pipeline

## 1. Extraction

File:

```text
scripts/extract.py
```

The extraction stage connects to the Central Bank API and retrieves the economic series using an explicit date range.

Main responsibilities:

- connect to the BCB public API;
- retrieve approximately one year of historical data;
- define request timeouts;
- handle HTTP errors;
- preserve raw API responses;
- save each execution as timestamped JSON files.

Generated files follow this pattern:

```text
data/raw/dolar_YYYYMMDD_HHMMSS.json
data/raw/ipca_YYYYMMDD_HHMMSS.json
data/raw/selic_YYYYMMDD_HHMMSS.json
```

Raw datasets are generated locally and are not committed to Git.

---

## 2. Transformation and Loading

File:

```text
scripts/load.py
```

The loading stage processes the JSON files created during extraction and stores the observations in SQLite.

The pipeline:

- reads the raw JSON files;
- validates required fields;
- converts BCB dates from `DD/MM/YYYY` to ISO `YYYY-MM-DD`;
- converts indicator values to numeric values;
- ignores invalid records;
- stores the transformed data in SQLite;
- prevents duplicate observations.

Database:

```text
data/painel.db
```

Main table:

```text
indicadores
```

The table uses the following uniqueness rule:

```text
UNIQUE(indicador, data)
```

Combined with:

```sql
INSERT OR IGNORE
```

this makes the loading process **idempotent**.

Running the same dataset multiple times does not create duplicate observations.

This behavior was validated by executing the load process more than once and confirming that subsequent executions inserted zero duplicate records.

---

## 3. Data Analysis

File:

```text
scripts/analysis.py
```

The analysis layer uses **Pandas** and **Matplotlib** to generate descriptive statistics and historical visualizations.

Metrics calculated for each indicator include:

- latest value;
- average;
- minimum;
- maximum;
- standard deviation.

The analysis process also generates one historical chart for each indicator.

Generated charts:

```text
data/graficos/dolar.png
data/graficos/ipca.png
data/graficos/selic.png
```

The charts are generated locally and are intentionally excluded from Git.

---

# AI Agent

File:

```text
scripts/agent.py
```

The project exposes a **FastAPI application** that allows users to ask questions about the stored economic data.

Example:

```text
Como está o dólar nos últimos 30 dias?
```

The application does not rely only on the language model's internal knowledge.

Before calling the LLM, the application retrieves relevant information directly from the SQLite database.

The request flow is:

```text
User question
      |
      v
FastAPI endpoint
      |
      v
SQLite query
      |
      v
Structured economic context
      |
      v
Groq LLM
      |
      v
Natural-language response
```

---

## Structured Retrieval Approach

The project uses a **retrieval-augmented approach over structured data**.

Economic observations are retrieved from SQLite through SQL queries and then injected into the model context before the response is generated.

This allows the model to answer based on the economic data stored by the pipeline.

The current implementation does **not** use:

- embeddings;
- semantic search;
- vector databases;
- model fine-tuning.

Instead, it uses direct structured retrieval from SQLite.

---

# REST API

The AI layer is exposed through **FastAPI**.

Start the API with:

```bash
uvicorn scripts.agent:app --reload
```

The server runs locally at:

```text
http://127.0.0.1:8000
```

Interactive Swagger documentation is automatically available at:

```text
http://127.0.0.1:8000/docs
```

---

## Health Check

Endpoint:

```http
GET /saude
```

Example response:

```json
{
  "status": "ok"
}
```

---

## Ask the AI Agent

Endpoint:

```http
POST /perguntar
```

Example request:

```json
{
  "texto": "Como está o dólar nos últimos 30 dias?",
  "dias": 30
}
```

The API:

1. receives the question;
2. queries the SQLite database;
3. builds a structured context using recent economic observations;
4. sends the question and context to the language model;
5. returns the generated answer.

The complete flow was tested locally through the FastAPI Swagger interface.

---

# Tech Stack

| Area | Technology |
|---|---|
| Programming Language | Python |
| Data Source | Central Bank of Brazil API |
| HTTP Requests | Requests |
| Data Processing | Pandas |
| Database | SQLite |
| Data Visualization | Matplotlib |
| API Framework | FastAPI |
| API Server | Uvicorn |
| Validation | Pydantic |
| LLM Provider | Groq |
| Current LLM | `openai/gpt-oss-120b` |
| Environment Variables | python-dotenv |
| Version Control | Git / GitHub |

---

# Project Structure

```text
painel-economico-ia/
│
├── scripts/
│   ├── extract.py
│   ├── load.py
│   ├── analysis.py
│   └── agent.py
│
├── data/
│   ├── raw/
│   ├── graficos/
│   └── painel.db
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

The content inside `data/` is generated locally during pipeline execution.

Generated datasets, charts and database files are not committed to the repository.

---

# Running the Project

## 1. Clone the repository

```bash
git clone <repository-url>
cd painel-economico-ia
```

The repository URL can be replaced after the project is published on GitHub.

---

## 2. Create a virtual environment

```bash
python -m venv .venv
```

On Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure the Groq API key

Copy:

```text
.env.example
```

to:

```text
.env
```

On PowerShell:

```powershell
Copy-Item .env.example .env
```

Then configure:

```env
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

The real `.env` file is ignored by Git and must never be committed.

---

## 5. Extract economic data

```bash
python scripts/extract.py
```

This creates the raw JSON files under:

```text
data/raw/
```

---

## 6. Load data into SQLite

```bash
python scripts/load.py
```

This creates:

```text
data/painel.db
```

Running this command multiple times with the same raw data does not duplicate existing observations.

---

## 7. Generate the analysis

```bash
python scripts/analysis.py
```

The command prints descriptive statistics and generates charts under:

```text
data/graficos/
```

---

## 8. Start the AI API

```bash
uvicorn scripts.agent:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

to access the interactive Swagger interface.

---

# Data Quality and Reliability

The pipeline contains several safeguards designed to make execution more reliable.

These include:

- HTTP error handling;
- request timeout configuration;
- validation of incoming JSON fields;
- ISO date normalization;
- numeric value conversion;
- invalid-record handling;
- unique database constraints;
- duplicate prevention;
- idempotent loading;
- separation between raw data and structured storage;
- environment-based secret management.

---

# Security

Sensitive credentials are not stored directly in the source code.

The project uses:

```text
.env
```

for local secrets.

Only:

```text
.env.example
```

is intended to be committed.

The real API key must never be published.

The `.gitignore` excludes resources such as:

```text
.env
.venv/
data/raw/
data/*.db
data/graficos/
__pycache__/
*.pyc
```

---

# Technical Decisions

## Why SQLite?

SQLite was selected to keep the project:

- lightweight;
- easy to reproduce;
- simple to run locally;
- independent of external database infrastructure.

For the current dataset size, SQLite is sufficient for the analytical and retrieval requirements of the application.

A future version could migrate the persistence layer to PostgreSQL.

---

## Why Preserve Raw Data?

The extraction stage stores the original API responses before transformation.

This separates:

```text
Extraction
     ↓
Raw data
     ↓
Transformation
     ↓
Structured data
```

This design makes it easier to:

- inspect the original source data;
- reproduce transformations;
- debug data-quality problems;
- reprocess the dataset without requesting the API again.

---

## Why Retrieve Data Before Calling the LLM?

Economic indicators change over time.

Instead of relying on information the language model may have learned during training, the application retrieves stored economic values before generating the response.

This makes the SQLite database the source of context for numerical information used by the AI agent.

---

# Environment Example

The project includes:

```text
.env.example
```

with:

```env
GROQ_API_KEY=sua_chave_aqui
GROQ_MODEL=openai/gpt-oss-120b
```

Users must create their own local `.env` file and provide a valid Groq API key.

---

# Dependencies

Main Python dependencies:

```text
requests==2.32.3
pandas==2.2.3
matplotlib==3.9.2
fastapi==0.115.0
uvicorn==0.30.6
pydantic==2.9.2
python-dotenv==1.0.1
groq==1.7.0
```

---

# Future Improvements

Potential future improvements include:

- automated tests with Pytest;
- continuous integration with GitHub Actions;
- additional economic indicators;
- GDP and unemployment data;
- PostgreSQL support;
- persistence of AI question/answer history;
- interactive web dashboard;
- Docker support;
- scheduled pipeline execution;
- data pipeline orchestration;
- n8n or Airflow integration;
- public deployment of the FastAPI application;
- monitoring and logging improvements.

These items are **future improvements** and are not presented as currently implemented features.

---

# Author

**Vladison Costa**

Computer Science student focused on:

- Backend Development
- Data Engineering
- Data Analysis
- Software Engineering

GitHub: [VladisonCosta](https://github.com/VladisonCosta)