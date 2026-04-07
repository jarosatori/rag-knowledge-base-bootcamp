# RAG Knowledge Base — Claude Bootcamp Edition

Production-ready vektorová znalostná báza. Toto nie je toy demo — je to reálny kód, ktorý Jaro používa na svoj content a know-how. Je tu ako **štartovací bod pre členov Claude Bootcampu** — fork, priprav si vlastný use case, uprav pod seba.

## Čo je v balíku

**Pipeline:**
- `src/ingest.py` — file scanner, chunker, embedder, uploader. Incremental aj full mode. Deduplikácia pri re-ingestion. Strict validácia metadata (žiadny silent fallback na filename ako kategóriu).
- `src/file_reader.py` — .md / .txt / .docx / .pdf reader s YAML frontmatter parserom a path-based metadata extractorom.
- `src/chunker.py` — paragraph-aware chunker s overlap. Rešpektuje štruktúru textu.
- `src/embedder.py` — OpenAI `text-embedding-3-large` (3072 dim, multilingual, vrátane slovenčiny).
- `src/sensitivity_scanner.py` — detekcia PII a citlivých dát na úrovni chunku.

**Retrieval:**
- `src/retrieve.py` — hlavný retrieval modul. Access-level filtering cez API kľúče (hardcoded access map — klient nemôže eskalovať). 4 vrstvy:
  1. Vector search (OpenAI embeddings + Qdrant)
  2. Metadata filtering (category / audience / content_type / tags / sensitivity)
  3. Reranker (Cohere `rerank-multilingual-v3.0`, +15-30% Recall@5)
  4. Query expansion (HyDE alebo multi-query, opt-in)
- `src/reranker.py` — Cohere rerank integrácia s graceful fallback. Ak API key chýba, rerank je no-op.
- `src/query_expansion.py` — HyDE + multi-query cez Claude Haiku, opt-in, graceful fallback.
- `get_full_document(file_path)` — vytiahne celý dokument naspäť (všetky chunky zoradené, zlepené).

**Rozhrania:**
- `src/mcp_server.py` — MCP server (stdio pre Claude Code aj SSE pre Claude Cowork). Nástroje: `search_knowledge_base`, `get_full_document`, `get_kb_stats`.
- `src/api.py` — FastAPI REST server. Endpointy: `GET /api/search`, `GET /api/document`, `GET /api/stats` (vrátane histogramu kategórií).

**Tooling:**
- `tests/eval_retrieval.py` — eval harness. Meria Category Hit Rate @K, Keyword Hit Rate, MRR, avg top-1 score. `--save`, `--compare`, `--only` flagy.
- `tests/eval_dataset.yaml` — testovací dataset (uprav pod svoj use case).
- `tests/audit_categories.py` — data hygiene audit. Porovná source súbory vs. Qdrant, hlási nekonzistencie, broken YAML, garbage kategórie.
- `tools/consolidate_taxonomy.py` — consolidation tool pre re-mapping kategórií z chaotických source frontmatterov na kanonickú taxonómiu. Dry-run + apply + automatický backup.

**Dokumentácia:**
- `knowledge-base/RAG_ARCHITECTURE_GUIDE.md` — veľký kontextový dokument o tom, **ako navrhnúť RAG podľa use case**. Chunking stratégie, embedding modely, retrieval patterns, metadata schémy, use case → architektúra rozhodovací strom (content / support / internal / legal / sales / engineering), setup workflow pre Claude, časté chyby, production checklist.

---

## Ako si to postaviť pod svoj use case

### Krok 1 — Definuj use case

Prečítaj si `knowledge-base/RAG_ARCHITECTURE_GUIDE.md` Časť 6 (rozhodovací strom) a Časť 7 (setup workflow). Zisti do ktorej z 6 kategórií tvoj use case spadá:

1. **Content creation / personal know-how** — ako Jarova RAG
2. **Customer support** — deflection, tiket automatizácia
3. **Internal knowledge hub** — "ChatGPT pre firmu"
4. **Legal / compliance** — zmluvy, regulácie
5. **Sales enablement** — case studies, battle cards
6. **Engineering docs** — codebase + ADRs

Každý má v guide pripravený playbook: čo nalievať, čo nenalievať, aká architektúra, aká metadata schéma.

### Krok 2 — Pýtaj sa Claude

Spusti Claude Code v tomto repo a povedz:

> "Chcem postaviť RAG pre [tvoj use case]. Prečítaj si `knowledge-base/RAG_ARCHITECTURE_GUIDE.md`, pozri sa na súčasný kód v `src/`, a navrhni mi čo presne upraviť."

Claude prejde guide, pozrie kód, a navrhne zmeny v:
- `config.py` (chunk size, embedding model, collection name)
- `chunker.py` (ak treba inú stratégiu — structural, AST, semantic)
- `ingest.py` (metadata schéma)
- `retrieve.py` (filtre, reranker on/off, query expansion)

### Krok 3 — Priprav svoje dáta

Štruktúra:
```
knowledge-base/
  public/
    <category>/
      <content_type>/
        my-doc.md
  internal/
  private/
```

Každý `.md` súbor by mal mať YAML frontmatter:
```yaml
---
title: "Názov dokumentu"
category: leadership
content_type: framework
sensitivity: public
audience: founder
source: "zdroj"
date: 2026-04-07
tags: [delegation, management]
---

Samotný obsah dokumentu...
```

### Krok 4 — Spusti ingestion

```bash
python src/ingest.py --full ./knowledge-base
```

### Krok 5 — Skontroluj kvalitu

```bash
# Data hygiene audit
python tests/audit_categories.py

# Retrieval eval (po úprave eval_dataset.yaml pod tvoje témy)
python tests/eval_retrieval.py --save baseline
```

### Krok 6 — Iteruj

Pri každej zmene retrieval logiky:
```bash
python tests/eval_retrieval.py --save experiment_1 --compare baseline
```

---

## Environment

```bash
# Povinné
OPENAI_API_KEY=sk-...
QDRANT_URL=https://xxx.cloud.qdrant.io   # alebo localhost pre Docker
QDRANT_API_KEY=...

# API keys (generuj si vlastné)
MENTOR_BOT_API_KEY=...        # public_only
INTERNAL_TOOLS_API_KEY=...    # public + internal
ADMIN_API_KEY=...             # full

# Voliteľné — reranker (výrazne zlepší kvalitu, trial key zadarmo na cohere.com)
COHERE_API_KEY=...

# Voliteľné — query expansion (HyDE / multi-query cez Claude Haiku)
ANTHROPIC_API_KEY=...
```

Bez `COHERE_API_KEY` reranker tiché no-op (systém ďalej funguje, len s horšou kvalitou).
Bez `ANTHROPIC_API_KEY` query expansion tiché no-op.

---

## Merané výsledky na Jarovej reálnej databáze (2073 chunkov)

| Verzia | Category Hit @5 | MRR | Top-1 score |
|---|---|---|---|
| Baseline (naivný vector) | 75.0% | 0.544 | 0.633 |
| + Data hygiene (Fáza 1.5) | 92.9% | 0.694 | 0.633 |
| + Reranker (Fáza 3) | 89.3% | 0.627 | 0.702 |

Reranker spravil top-1 odpovede výrazne presnejšími (avg score +11%). Category hit rate mierny pokles je artefakt eval datasetu (reranker ide po skutočnej relevancii, nie po kategórii — tri "zlyhania" sú vlastne lepšie odpovede s inou kategóriou).

---

## Čo sa plánuje v ďalšej verzii

- **Fáza 4 — Hybrid search (vector + BM25)** — pre customer support a legal use cases, kde presné termíny a identifikátory rozhodujú. Qdrant sparse vectors.
- **Parent-child chunking** — malé chunky pre retrieval, veľké pre LLM kontext.
- **Graph RAG** — pre komplexné vzťahy medzi entitami (osoby, firmy, rozhodnutia).

---

## Kredity

Interný Bootcamp produkt. Upravuj, forkuj, stavaj nad tým. Ak ti to pomohlo, daj vedieť v komunite čo si postavil.

Autor originálu: Jaroslav Chrapko + Claude (Anthropic).
Postavené pre členov Claude Bootcampu 2026.
