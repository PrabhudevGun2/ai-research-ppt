# AI Research PPT Generator

A **multi-agent AI pipeline** that searches ArXiv, synthesizes findings, and generates a professional PowerPoint presentation — with human-in-the-loop review at every stage.

Built with **LangGraph**, **FastAPI**, **Streamlit**, **OpenRouter**, and deployed on **Kubernetes (minikube)**.

---

## Architecture

```
Streamlit UI  (NodePort 30080)
      ↕  HTTP polling & POST
FastAPI Backend  (LangGraph + agents, port 8000)
      ↕
Redis  (LangGraph checkpointer / state store, port 6379)
      ↕
PersistentVolume  (generated .pptx files at /app/outputs)
```

### Agent Pipeline

```
START
  └─► topic_discovery_node     (ArXiv multi-query search → LLM topic scoring)
        └─► [INTERRUPT] human_topic_review    ← UI: select topics
              └─► research_node               (deep ArXiv dive per topic)
                    └─► [INTERRUPT] human_research_review  ← UI: approve findings
                          └─► synthesis_node  (LLM → SlideContent[])
                                └─► [INTERRUPT] human_synthesis_review ← UI: edit slides
                                      └─► ppt_generation_node  (python-pptx)
                                            └─► review_node    (LLM QA)
                                                  └─► [INTERRUPT] human_final_review
                                                        └─► END
```

---

## Features

- **12 suggested topic tiles** on the start page — click any to pre-fill the query
- **Free-text query** input for custom research topics
- **Model selector** — choose any OpenRouter model (Claude, GPT-4o, Gemini, Llama, etc.)
- **4 human-in-the-loop checkpoints** — review and edit before each stage proceeds
- **ArXiv live search** — always uses the latest papers
- **Professional PPT** — dark header theme, two-column layouts, speaker notes
- **One-click download** of the generated `.pptx`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM provider | [OpenRouter](https://openrouter.ai) (OpenAI-compatible API) |
| Paper search | [ArXiv Python](https://github.com/lukasschwab/arxiv.py) |
| Slide generation | [python-pptx](https://python-pptx.readthedocs.io) |
| Backend API | [FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org) |
| State persistence | [Redis](https://redis.io) via `langgraph-checkpoint-redis` |
| Frontend | [Streamlit](https://streamlit.io) |
| Containers | Docker + docker-compose |
| Orchestration | Kubernetes (minikube) |

---

## File Structure

```
ai-research-ppt/
├── backend/
│   ├── main.py                    # FastAPI entrypoint
│   ├── config.py                  # pydantic-settings (env vars)
│   ├── llm_client.py              # OpenRouter client + per-session model override
│   ├── agents/
│   │   ├── topic_discovery.py     # ArXiv search → LLM-scored topics
│   │   ├── research.py            # Per-topic deep ArXiv search + synthesis
│   │   ├── synthesis.py           # LLM → SlideContent[]
│   │   ├── ppt_generation.py      # python-pptx slide builder
│   │   └── review.py              # LLM QA pass
│   ├── graph/
│   │   ├── state.py               # ResearchState TypedDict
│   │   └── builder.py             # StateGraph + 4 interrupt nodes
│   ├── tools/
│   │   ├── arxiv_tools.py         # ArXiv search helpers
│   │   └── pptx_tools.py          # Slide template utilities
│   └── api/
│       └── routes.py              # REST endpoints
├── frontend/
│   ├── app.py                     # Streamlit router + polling loop
│   ├── pages/
│   │   ├── p01_start.py           # Topic input, model selector, quick-pick tiles
│   │   ├── p02_topics.py          # HITL: select topics
│   │   ├── p03_research.py        # HITL: review findings
│   │   ├── p04_slides.py          # HITL: edit slide content
│   │   └── p05_final.py           # HITL: download PPT
│   └── utils/
│       ├── api_client.py          # requests wrapper
│       └── session_state.py       # st.session_state helpers
├── k8s/
│   ├── namespace.yaml
│   ├── backend/  (configmap, secret, deployment, service, pvc)
│   ├── frontend/ (deployment, service NodePort 30080, configmap)
│   └── redis/    (deployment, service, pvc)
├── docker/
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── docker-compose.yml
├── requirements.txt
├── Makefile
└── .env.example
```

---

## Quick Start (Local — docker-compose)

### 1. Prerequisites

- Docker + Docker Compose
- An [OpenRouter](https://openrouter.ai) API key (free tier available)

### 2. Configure

```bash
cd ai-research-ppt
cp .env.example .env
# Edit .env — set OPENROUTER_API_KEY and optionally LLM_MODEL
```

### 3. Run

```bash
docker-compose up --build
```

Open **http://localhost:8501** in your browser.

---

## Deploy to Kubernetes (minikube)

### Prerequisites

- [minikube](https://minikube.sigs.k8s.io/docs/start/) installed
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed
- Docker

### Step-by-step

```bash
# 1. Start minikube
minikube start --cpus=4 --memory=4096 --driver=docker

# 2. Point your shell at minikube's Docker daemon
eval $(minikube docker-env)

# 3. Build images inside minikube
make build

# 4. Create namespace + apply all manifests
kubectl apply -f k8s/namespace.yaml

# 5. Create the API key secret (prompts for your OpenRouter key)
make set-secret

# 6. Deploy everything
make deploy

# 7. Open the UI
make port-forward       # http://localhost:8501
# OR
minikube service frontend -n ai-research-ppt
```

### Useful commands

```bash
make status             # Show pod status
make logs-backend       # Tail backend logs
make logs-frontend      # Tail frontend logs
make rollout-backend    # Rolling restart backend
make clean              # Delete K8s resources (keep namespace)
make destroy            # Delete namespace (remove everything)
```

---

## API Reference

All endpoints are prefixed with `/api/v1`.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/sessions` | Create session, start pipeline async |
| `GET` | `/sessions/{id}/status` | Poll stage + interrupt payload |
| `POST` | `/sessions/{id}/resume` | Submit human feedback, resume graph |
| `GET` | `/sessions/{id}/ppt/download` | Download generated `.pptx` |
| `GET` | `/health` | Liveness probe |

### POST /sessions

```json
{
  "user_query": "latest generative AI trends",
  "model": "openai/gpt-4o"   // optional — overrides LLM_MODEL env var
}
```

### POST /sessions/{id}/resume

```json
{
  "action": "approve",
  "feedback_text": "Focus on practical applications",
  "approved_topics": [...],      // for topic review stage
  "approved_research": [...],    // for research review stage
  "approved_slides": [...]       // for synthesis review stage
}
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | **required** | Your OpenRouter API key (`sk-or-v1-...`) |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter endpoint |
| `LLM_MODEL` | `anthropic/claude-sonnet-4-5` | Default model slug (overridable per session) |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection string |
| `OUTPUT_DIR` | `/app/outputs` | Where `.pptx` files are saved |
| `ARXIV_MAX_RESULTS` | `50` | Max papers per ArXiv query |
| `LOG_LEVEL` | `INFO` | Logging level |
| `BACKEND_URL` | `http://localhost:8000` | Frontend → backend URL (used by Streamlit only) |

### Supported OpenRouter Models (examples)

| Model ID | Notes |
|----------|-------|
| `anthropic/claude-sonnet-4-5` | Default — excellent quality |
| `anthropic/claude-3-haiku` | Fast and cheap |
| `openai/gpt-4o` | Strong performance |
| `openai/gpt-4o-mini` | Fast and cheap |
| `google/gemini-pro-1.5` | Long context |
| `meta-llama/llama-3.1-70b-instruct` | Free tier available |
| `mistral/mistral-large` | European alternative |
| `deepseek/deepseek-chat` | Cost-effective |

Full list: https://openrouter.ai/models

---

## Human-in-the-Loop Flow

```
User enters query + selects model
         │
         ▼
 [Agent] Topic Discovery (ArXiv + LLM)
         │
         ▼  interrupt
 [UI] Review Topics ── select 3-5 topics, optional feedback
         │
         ▼
 [Agent] Deep Research (per-topic ArXiv + LLM)
         │
         ▼  interrupt
 [UI] Review Findings ── approve, add feedback
         │
         ▼
 [Agent] Slide Synthesis (LLM → slide outline)
         │
         ▼  interrupt
 [UI] Edit Slides ── edit titles, bullet points inline
         │
         ▼
 [Agent] PPT Generation (python-pptx)
 [Agent] QA Review (LLM quality check)
         │
         ▼  interrupt
 [UI] Final Review ── metrics, QA notes, download .pptx
```

The Streamlit UI polls `/api/v1/sessions/{id}/status` every 2 seconds. When the pipeline hits an `interrupt()` the status transitions to `awaiting_*` and the UI renders the appropriate review page automatically.

---

## Development

### Local Setup (Virtual Environment)

```bash
cd ai-research-ppt

# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set OPENROUTER_API_KEY
```

### Run backend locally (no Docker)

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in OPENROUTER_API_KEY

# Start Redis (must use RedisStack for JSON module required by langgraph-checkpoint-redis)
docker run -d --name redis-local -p 6379:6379 redis/redis-stack-server:latest

# Start backend
python -m uvicorn backend.main:app --reload --port 8000
```

### Run frontend locally

```bash
BACKEND_URL=http://localhost:8000 streamlit run frontend/app.py
```

### Project dependencies

```
langgraph>=0.2.0
openai>=1.35.0           # OpenRouter uses the OpenAI-compatible API
arxiv>=2.1.0
python-pptx>=0.6.23
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
redis>=5.0.0
langgraph-checkpoint-redis>=0.1.0
pydantic>=2.7.0
pydantic-settings>=2.3.0
httpx>=0.27.0
streamlit>=1.36.0
requests>=2.32.0
```

---

## Kubernetes Resource Summary

| Component | Replicas | CPU Request | Memory Request | Storage |
|-----------|----------|-------------|----------------|---------|
| backend | 1 | 500m | 512Mi | 1Gi PVC (outputs) |
| frontend | 1 | 200m | 256Mi | — |
| redis | 1 | 100m | 128Mi | 512Mi PVC |

- **Namespace**: `ai-research-ppt`
- **Frontend access**: NodePort `30080` or `minikube service frontend -n ai-research-ppt`
- **Backend**: ClusterIP `:8000` (internal only)
- **Redis**: ClusterIP `:6379` (internal only)

---

## Troubleshooting

**Backend fails to start**
- Check `OPENROUTER_API_KEY` is set correctly
- Verify Redis is reachable: `redis-cli -u $REDIS_URL ping`

**Redis "unknown command JSON.SET" error**
- The `langgraph-checkpoint-redis` library requires Redis with the JSON module
- Use `redis/redis-stack-server:latest` instead of `redis:7-alpine`
- The JSON module is included in RedisStack but not in the standard Alpine image

**Topic discovery returns no results**
- ArXiv rate-limits requests — wait a minute and retry
- Try a broader query

**LLM call fails / JSON parse error**
- The agent falls back to a rule-based result automatically
- Check backend logs: `make logs-backend`
- Try a different model — some models return markdown-wrapped JSON
- Recommended models: `anthropic/claude-sonnet-4-5`, `openai/gpt-4o`, `google/gemini-pro-1.5`

**minikube image not found**
- Run `eval $(minikube docker-env)` before `make build`
- Ensure `imagePullPolicy: Never` in the deployment YAML

**Port-forward drops**
- Re-run `make port-forward`
- Alternatively use `minikube service frontend -n ai-research-ppt --url`
