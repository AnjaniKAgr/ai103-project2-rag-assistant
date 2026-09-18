# AI-103 Project 2 — RAG Study Assistant

An interactive study assistant that answers AI-103 questions from a curated
document collection. It uses Azure OpenAI for embeddings and answer generation,
Azure AI Search for hybrid retrieval, and the Azure AI Evaluation SDK for
repeatable quality measurements.

## Architecture

```text
Markdown documents
       |
       v
ingest.py -> chunk text -> create embeddings -> Azure AI Search index
                                                   |
User question -> query embedding -> hybrid search -+
                                      |
                                      v
                             retrieved context
                                      |
                                      v
                              gpt-4o generation
                                      |
                                      v
                          grounded answer + citations
```

## What this project demonstrates

- Document loading and overlapping word-based chunking
- Vector embeddings with `text-embedding-3-small`
- An Azure AI Search index using HNSW vector search
- Hybrid keyword and vector retrieval
- Grounded answer generation with citations and refusal instructions
- Interactive multi-turn conversation history
- RAG evaluation for retrieval, groundedness, and relevance
- Microsoft Entra authentication through `DefaultAzureCredential`

## Project files

- `data/` — curated AI-103 study documents
- `ingest.py` — chunks, embeds, indexes, and verifies the documents
- `rag-assistant.py` — interactive retrieval and answer-generation application
- `eval-data.jsonl` — repeatable evaluation questions
- `eval-unsupported.jsonl` — out-of-scope questions and forbidden answers
- `evaluate-rag.py` — generates RAG outputs and runs Microsoft evaluators
- `EVALUATION.md` — baseline, tuning changes, results, and lessons learned
- `.env.example` — required configuration template

Generated files `eval-generated.jsonl` and `eval-results.json` are ignored by
Git because they can be recreated and may contain retrieved source content.

## Azure resources

The application requires:

- A Microsoft Foundry project
- A `gpt-4o` deployment
- A `text-embedding-3-small` deployment
- An Azure AI Search service
- The `Search Service Contributor` role for index management
- The `Search Index Data Contributor` role for document access

## Setup

Create and activate a virtual environment in PowerShell:

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
az login
```

Set the variables shown in `.env.example` in the active PowerShell session:

```powershell
$env:AZURE_OPENAI_ENDPOINT = "https://<resource-name>.openai.azure.com"
$env:EMBEDDING_MODEL_DEPLOYMENT = "text-embedding-3-small"
$env:CHAT_MODEL_DEPLOYMENT = "gpt-4o"
$env:AZURE_SEARCH_ENDPOINT = "https://<search-name>.search.windows.net"
$env:AZURE_SEARCH_INDEX_NAME = "ai103-study-index"
```

## Ingest the documents

```powershell
python .\ingest.py
```

The script creates or updates the index, embeds every chunk, uploads the
documents, and runs a verification search.

## Run the assistant

```powershell
python .\rag-assistant.py
```

Ask an AI-103 question or enter `exit` to stop. Answers include numbered source
citations. If the retrieved evidence is insufficient, the assistant is
instructed to say so rather than fabricate an answer.

## Run the evaluation

```powershell
python .\evaluate-rag.py
```

The runner first creates query, response, and retrieved-context rows, then
scores them with the Retrieval, Groundedness, and Relevance evaluators. See
`EVALUATION.md` for the baseline and tuned results. It also runs a deterministic
regression test that requires unsupported questions to receive an explicit
insufficient-evidence response instead of an answer from model memory.

## Authentication and security

The code uses Microsoft Entra credentials instead of API keys. Do not commit
`.env`, secrets, tokens, or generated evaluation output containing private
source material. Apply least-privilege Azure roles and enforce authorization
during retrieval for production RAG systems.
