# RAG Knowledge Base — Claude Bootcamp Edition

**Plug & play vektorová znalostná báza.** Postavená Jarom Chrapkom + Claude pre členov Claude Bootcampu. Použiteľná pre content creation, customer support, internal knowledge hub, sales enablement, legal/compliance — Claude ti pri inštalácii pomôže nakonfigurovať to presne na **tvoj** use case.

---

## 🚀 Quickstart

> **Si úplný začiatočník a nikdy si neotvoril terminál?** Pohoda. Tu je presne čo treba urobiť. Najskôr si nainštaluj 3 veci (5 minút), potom si vyber jednu z dvoch ciest — odporúčam **Cestu A (bez terminálu)**.

---

### 📦 Predpoklady — toto si nainštaluj **pred** štartom

Sú to 3 bezplatné veci. Bez nich to nepôjde, ale s nimi to zvládne každý.

#### 1. Python 3.10 alebo novší

Programovací jazyk, na ktorom RAG beží. Nemusíš mu rozumieť — len ho nainštaluj a zabudni na neho.

- **Mac:** Otvor [python.org/downloads/macos](https://www.python.org/downloads/macos/) → klikni na najnovší **macOS 64-bit installer** → stiahni a klikni 2× na `.pkg` súbor → Next, Next, Install.
- **Windows:** Otvor [python.org/downloads/windows](https://www.python.org/downloads/windows/) → stiahni najnovší **Windows installer (64-bit)** → klikni 2× na `.exe`. **DÔLEŽITÉ:** Na prvej obrazovke installera **zaškrtni „Add Python to PATH"**, inak to nebude fungovať. Potom Install.

Overenie že máš (voliteľné, len pre istotu): otvor terminál (viď nižšie ako) a napíš `python3 --version`. Ak vidíš číslo `3.10` alebo viac, je to OK.

#### 2. Git

Nástroj na sťahovanie kódu z GitHubu. Automaticky funguje v pozadí.

- **Mac:** Otvor `Terminal.app` (viď nižšie ako) a napíš `git --version`. Ak ti vyskočí dialóg „Install Command Line Developer Tools", klikni **Install** a počkaj 5 minút. Hotovo.
- **Windows:** Stiahni installer z [git-scm.com/download/win](https://git-scm.com/download/win) → klikni 2× na `.exe` → klikni **Next** všade (defaulty sú OK) → Install.

#### 3. Claude Code (desktop app alebo CLI)

Toto je AI asistent, ktorý za teba spraví celý setup.

- **Najjednoduchšie — desktop app:** Stiahni z [claude.com/code](https://claude.com/code) a nainštaluj.
- Alternatíva pre pokročilých — CLI: `npm install -g @anthropic-ai/claude-code`.

---

### 💡 Čo je „terminál" a ako ho otvoriť

Terminál (alebo „príkazový riadok") je čierne okno, kam píšeš textové príkazy namiesto klikania myšou. Vyzerá technicky, ale na to čo budeme robiť stačí kopírovať a vlepiť.

- **Mac:** Stlač `Cmd + Space` (otvorí Spotlight vyhľadávanie) → napíš `Terminal` → Enter. Otvorí sa biele alebo čierne okno s blikajúcim kurzorom.
- **Windows:** Stlač klávesu Windows → napíš `PowerShell` → Enter. Alebo (lepšie) ak si nainštaloval Git, napíš `Git Bash` → Enter.

**Dobrá správa:** ak si vyberieš **Cestu A** nižšie, terminál ani **nemusíš otvárať**. Claude to spraví za teba.

---

### 🅰️ Cesta A — Bez terminálu (odporúčané)

> Pre nepokročilých. **Nemusíš otvárať terminál ani nič klikať vo Finder/Explorer okrem dvoch klikov.**

#### A.1 — Vytvor si prázdnu zložku, kde chceš RAG mať

- **Mac (Finder):** Otvor Finder → choď do Documents → klikni pravým tlačidlom → **New Folder** → pomenuj ju napríklad `MyRAG`. Hotovo. Cesta bude `~/Documents/MyRAG`.
- **Windows (Explorer):** Otvor File Explorer → choď do Documents → pravý klik do prázdnej plochy → **New → Folder** → pomenuj ju `MyRAG`.

> Táto zložka bude **trvalé miesto pre tvoju RAG**. Odtiaľ to pobeží, sem budeš dávať obsah. Zapamätaj si jej cestu.

#### A.2 — Otvor Claude Code app a otvor v ňom tú zložku

1. Spusti **Claude Code** aplikáciu
2. Klikni **File → Open Folder…** (alebo `Cmd+O` na Macu / `Ctrl+O` na Windows)
3. Naviguj na zložku `MyRAG`, ktorú si práve vytvoril, a klikni **Open**
4. V ľavom paneli teraz vidíš prázdnu zložku — to je v poriadku, ešte v nej nič nie je

#### A.3 — Vlep tento prompt do chat-input okna Claude Code a stlač Enter

```
Práve som otvoril prázdnu zložku, do ktorej chcem nainštalovať RAG knowledge base
z https://github.com/jarosatori/rag-knowledge-base-bootcamp

Som člen Claude Bootcampu, podnikateľ, nie programátor. Nikdy som neotvoril
terminál a chcem všetko spraviť cez teba.

Postup:

1. Najprv skontroluj, či mám nainštalovaný git a python (3.10+). Ak niečo
   chýba, povedz mi presne ako to nainštalovať na môj systém a počkaj kým to
   dokončím.

2. Keď bude všetko pripravené, stiahni repo do TEJTO zložky príkazom:
   git clone https://github.com/jarosatori/rag-knowledge-base-bootcamp.git .
   (POZOR: bodka na konci je dôležitá — znamená "do aktuálnej zložky")

3. Po stiahnutí prečítaj SETUP_GUIDE.md a postupuj presne podľa neho. Začni
   Fázou 0 a pýtaj sa ma postupne.

4. Rieš všetko za mňa — spúšťaj príkazy, edituj súbory, rieš chyby. Pýtaj sa
   len keď to fakt potrebuješ alebo keď ide o platené/nevratné veci. Vysvetľuj
   v ľudskej reči, nie v žargóne. Hovor po slovensky a tykaj mi.

Pripravený? Začni.
```

**To je všetko.** Od tejto chvíle Claude robí všetko sám — stiahne kód, skontroluje predpoklady, pomôže s API kľúčmi, naliuje obsah, otestuje, deploynuje. Ty len odpovedáš na jeho otázky.

---

### 🅱️ Cesta B — S terminálom (pre tých čo ho ovládajú)

> Rýchlejšie ak vieš čo robíš.

#### B.1 — Otvor terminál a stiahni repo

```bash
mkdir -p ~/Documents/MyRAG
cd ~/Documents/MyRAG
git clone https://github.com/jarosatori/rag-knowledge-base-bootcamp.git
```

Vytvorí sa cesta `~/Documents/MyRAG/rag-knowledge-base-bootcamp/`.

> **Tip:** Pre vlastné meno zložky pridaj ho za URL:
> ```bash
> git clone https://github.com/jarosatori/rag-knowledge-base-bootcamp.git moja-rag
> ```

#### B.2 — Otvor zložku v Claude Code

**Desktop app:** File → Open Folder → vyber `rag-knowledge-base-bootcamp/`.

**CLI:**
```bash
cd ~/Documents/MyRAG/rag-knowledge-base-bootcamp
claude
```

#### B.3 — Vlep prompt

```
Ahoj. Práve som naklonoval tento RAG knowledge base repo a chcem si ho rozbehnúť.
Som člen Claude Bootcampu, podnikateľ, nie programátor. Potrebujem, aby si ma
previedol celou inštaláciou krok za krokom — od nuly po deploynutý systém,
ku ktorému sa pripojím cez MCP.

Prečítaj si SETUP_GUIDE.md a postupuj presne podľa neho. Začni Fázou 0 a pýtaj
sa ma postupne. Rieš všetko za mňa — spúšťaj príkazy, edituj súbory, rieš
chyby. Pýtaj sa len keď to fakt potrebuješ alebo keď ide o platené/nevratné
veci. Vysvetľuj v ľudskej reči, nie v žargóne. Hovor po slovensky a tykaj mi.

Pripravený? Začni.
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

- **Python 3.10+** (ak nemáš, Claude ti pri setupe povie ako nainštalovať)
- **Git** (Mac má built-in, Windows: [git-scm.com](https://git-scm.com/download/win))
- **Claude Code** — buď desktop app alebo CLI. **Stačí jedno z:**
  - Desktop app: stiahni z [claude.com/code](https://claude.com/code)
  - CLI: `npm install -g @anthropic-ai/claude-code` (vyžaduje Node.js)
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

- **Bootcamp Skool** — primárny kanál
- **Issues** na tomto GitHub repe
- **Sám sebe** — otvor Claude Code v tomto repo a povedz "mám problém s RAG, pomôž"

---

## Kredity

Postavené Jarom Chrapkom (Dedoles, Miliónová Evolúcia) + Claude (Anthropic).
Pre Claude Bootcamp 2026.

Licencia: použi voľne na svoj biznis. Ak ti to pomohlo, pošli to ďalej.
