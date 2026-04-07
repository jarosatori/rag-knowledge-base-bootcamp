# RAG Knowledge Base — Claude Bootcamp Edition

**Plug & play vektorová znalostná báza.** Postavená Jarom Chrapkom + Claude pre členov Claude Bootcampu. Použiteľná pre content creation, customer support, internal knowledge hub, sales enablement, legal/compliance — Claude ti pri inštalácii pomôže nakonfigurovať to presne na **tvoj** use case.

---

## 🚀 Quickstart (5 minút prípravy + Claude ťa prevezme)

### Krok 1 — Skopíruj a spusti tieto 3 príkazy

```bash
cd ~/Documents
git clone https://github.com/jarosatori/rag-knowledge-base-bootcamp.git
cd rag-knowledge-base-bootcamp
```

### Krok 2 — Otvor Claude Code v tomto adresári

```bash
claude
```

### Krok 3 — Skopíruj a vlep tento prompt do Claude Code

```
Ahoj. Práve som naklonoval tento RAG knowledge base repo a chcem si ho rozbehnúť.
Som člen Claude Bootcampu, podnikateľ, nie programátor. Potrebujem aby si ma
previedol celou inštaláciou krok za krokom — od nuly po deploynutý systém,
ku ktorému sa pripojím cez MCP.

Prečítaj si SETUP_GUIDE.md a postupuj presne podľa neho. Začni Fázou 0 a pýtaj
sa ma postupne. Riešiš všetko za mňa — spúšťaj príkazy, edituj súbory, riešiš
chyby. Pýtaj sa len keď to fakt potrebuješ alebo keď ide o platené/nevratné
veci. Vysvetľuj v ľudskej reči, nie v žargóne.

Pripravený si? Začni.
```

**To je všetko.** Claude od tej chvíle vie:

- ✅ Spýtať sa ťa **na čo** RAG bude (content / support / internal / sales / legal / iné) a podľa toho **automaticky** zvolí správnu architektúru
- ✅ Skontrolovať Python, git, závislosti a doinštalovať čo chýba
- ✅ Pomôcť ti získať **OpenAI, Qdrant Cloud a Cohere API kľúče** (presné URL a kroky)
- ✅ Vytvoriť `.env` súbor a vygenerovať bezpečné API kľúče prístupových úrovní
- ✅ Pomôcť ti **pripraviť tvoj obsah** (.md/.docx/.pdf) — vrátane automatického pridania YAML frontmatter ak chýba
- ✅ Spustiť **ingestion**, audit a sanity-test retrieval s tvojimi reálnymi otázkami
- ✅ **Deploynúť** to na Railway alebo Render (alebo nechať lokálne)
- ✅ Pripojiť hotovú RAG do tvojho **Claude Code cez MCP server**, takže ju vieš použiť hneď

Celý setup trvá **20-40 minút** podľa toho koľko obsahu naliuvaš.

---

## Čo dostávaš (technické zhrnutie)

**Pipeline:**
- OpenAI `text-embedding-3-large` (3072 dim, multilingual vrátane SK/CZ)
- Paragraph-aware chunking s overlap
- YAML frontmatter parsing + path-based metadata extraction
- Strict validácia (žiadne silent fallbacky)

**Retrieval (4 vrstvy):**
1. Vector search (Qdrant)
2. Metadata filtering (category / audience / sensitivity / tags)
3. **Cohere reranker** (`rerank-multilingual-v3.0`) — +15-30% Recall@5
4. **Query expansion** (HyDE / multi-query cez Claude Haiku) — opt-in

**Plus:**
- `get_full_document()` — vytiahne celý dokument naspäť slovo-od-slova
- Access control cez API kľúče (3 úrovne: public_only / internal / full)
- Eval harness (28 testovacích otázok, Recall@K, MRR, A/B test framework)
- Data hygiene audit (porovná source vs Qdrant, hlási nekonzistencie)
- Taxonomy consolidation tool (mapovanie chaotických kategórií na kanonickú schému)

**Rozhrania:**
- **MCP server** (stdio pre Claude Code, SSE pre Claude Cowork) s nástrojmi: `search_knowledge_base`, `get_full_document`, `get_kb_stats`
- **FastAPI HTTP API** (`/api/search`, `/api/document`, `/api/stats`)

**Merané výsledky** na Jarovej reálnej KB (2073 chunkov):

| Metrika | Pôvodný stav | Po upgrade |
|---|---|---|
| Category Hit Rate @5 | 75.0% | **89.3%** |
| Category MRR | 0.544 | **0.627** |
| Top-1 confidence | 0.633 | **0.702** |

---

## Štruktúra repa

```
src/                    # Production kód (ingest, retrieve, reranker, MCP, API)
tests/                  # Eval harness, audit, A/B test framework
tools/                  # Taxonomy consolidation tool
knowledge-base/         # SEM dáš svoj obsah (Claude ti pomôže)
SETUP_GUIDE.md          # Inštrukcie ktoré číta Claude pri setupe
RAG_ARCHITECTURE_GUIDE.md  # Hlboký guide o RAG architektúre podľa use case
```

---

## Predpoklady

- **Python 3.10+**
- **Git**
- **Claude Code CLI** (`claude`) — predpokladá sa, že ho už máš ako Bootcamp člen
- **Docker** (voliteľný — len ak chceš lokálny Qdrant namiesto Qdrant Cloud)
- **Účty:**
  - OpenAI (s ~$5 kreditom)
  - Qdrant Cloud (free tier stačí na desaťtisíce chunkov)
  - Cohere (trial zadarmo — silne odporúčané)
  - Railway alebo Render (ak chceš deploy do cloudu)

---

## Pre pokročilých — manuálny setup

Ak nechceš sprievodcu a vieš čo robíš, čítaj `SETUP_GUIDE.md` priamo. Obsahuje všetky príkazy a flow.

Pre hlboké pochopenie architektúry pred kustomizáciou — `knowledge-base/RAG_ARCHITECTURE_GUIDE.md` (10-dielny guide s rozhodovacím stromom use case → architektúra).

---

## Podpora

- **Bootcamp Discord/Skool** — primárny kanál
- **Issues** na tomto GitHub repe
- **Sám sebe** — otvor Claude Code v tomto repo a povedz "mám problém s RAG, pomôž"

---

## Kredity

Postavené Jarom Chrapkom (Dedoles, Miliónová Evolúcia) + Claude (Anthropic).
Pre Claude Bootcamp 2026.

Licencia: použi voľne na svoj biznis. Ak ti to pomohlo, pošli to ďalej.
