# RAG Knowledge Base — Claude Bootcamp Edition

**Plug & play vektorová znalostná báza.** Postavená Jarom Chrapkom + Claude pre členov Claude Bootcampu. Použiteľná pre content creation, customer support, internal knowledge hub, sales enablement, legal/compliance — Claude ti pri inštalácii pomôže nakonfigurovať to presne na **tvoj** use case.

---

## 🚀 Quickstart

> **Si úplný začiatočník a nikdy si neotvoril terminál?** Pohoda. Tu je presne čo treba urobiť. Najskôr si nainštaluj 3 veci (5 minút), potom si vyber jednu z dvoch ciest — odporúčam **Cestu A (bez terminálu)**.

---

### 📦 Predpoklady — toto si nainštaluj **pred** štartom

Stačí **jedna jediná vec**: **Claude Code**.

Všetko ostatné (git, Python, Homebrew, gh, Docker...) **nainštaluje za teba samotný Claude** počas setup-u, cez balíčkové manažéry tvojho systému (`brew` na Macu, `winget` na Windows). Ty len odpovedáš na jeho otázky a on robí robotu.

#### Nainštaluj si Claude Code

- **Najjednoduchšie — desktop app (odporúčané pre nepokročilých):** Stiahni z [claude.com/code](https://claude.com/code) a nainštaluj. Hotovo.
- Alternatíva pre pokročilých — CLI: `npm install -g @anthropic-ai/claude-code` (vyžaduje Node.js).

To je všetko. Choď rovno na **Cestu A** nižšie.

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
Práve som otvoril prázdnu zložku v Claude Code, do ktorej chcem nainštalovať
RAG knowledge base z https://github.com/jarosatori/rag-knowledge-base-bootcamp

Som člen Claude Bootcampu, podnikateľ, nie programátor. Nikdy som neotvoril
terminál a chcem všetko spraviť cez teba. NEPOSIELAJ ma sťahovať veci z
internetu, ak sa to dá nainštalovať príkazom — to spravíš ty za mňa.

DÔLEŽITÉ ROZLIŠENIE GitHub:
- Na STIAHNUTIE tohto repa GitHub účet NEPOTREBUJEM (repo je verejné, git
  clone funguje anonymne).
- Neskôr v procese (Fáza 6) si budem chcieť vytvoriť VLASTNÝ súkromný GitHub
  repo ako zálohu mojej kópie. Vtedy si vytvorím GitHub účet (5 minút,
  zadarmo) a ty ma cez to prevedieš automaticky cez "gh" CLI s autentifikáciou
  cez prehliadač. Žiadne SSH kľúče, žiadne tokeny ručne.

POSTUP:

1. Zisti, na akom operačnom systéme bežím (macOS / Windows / Linux).

2. Skontroluj, či mám tieto základné nástroje:
   - git
   - python3 (verzia 3.10 alebo vyššia)

3. Pre čokoľvek čo chýba alebo je staré:

   AK SOM NA macOS:
   - git: spusti `xcode-select --install`. Vyskočí mi systémový popup,
     kliknem "Install" a počkám 5-10 minút. Toto nainštaluje aj git aj
     kompilery, ktoré budeme neskôr potrebovať na inštaláciu Python balíčkov.
   - python3 (ak chýba alebo je < 3.10):
     a) Najprv skontroluj, či mám Homebrew (`brew --version`).
     b) Ak Homebrew mám: spusti `brew install python@3.12`.
     c) Ak Homebrew nemám: daj mi PRESNE jeden riadok, ktorý mám vlepiť do
        aplikácie Terminal.app. Vysvetli mi, ako Terminal otvoriť (Cmd+Space →
        napíš "Terminal" → Enter). Upozorni ma vopred, že si bude pýtať heslo
        k Macu (rovnaké ako keď sa prihlasujem na svoj počítač). Počkaj kým
        ti poviem, že je hotovo, potom over `brew --version` a pokračuj
        inštaláciou Pythonu cez brew.

   AK SOM NA Windows:
   - git: `winget install --id Git.Git -e --source winget` (winget je
     vstavaný vo Win10 a Win11, nemusíš ho inštalovať).
   - python: `winget install --id Python.Python.3.12 -e --source winget`.
   - Po každej inštalácii môže byť potrebné zavrieť a otvoriť Claude Code,
     aby sa nový PATH načítal — povedz mi keď treba.
   - Ak winget nefunguje (starý Windows), navrhni mi alternatívu (napr.
     Chocolatey).

   AK SOM NA Linux:
   - Použi balíčkový manažér mojej distribúcie (apt / dnf / pacman).

4. Keď máme git aj python3 (≥ 3.10), stiahni repo do TEJTO prázdnej zložky:
   git clone https://github.com/jarosatori/rag-knowledge-base-bootcamp.git .
   (POZOR: bodka na konci znamená "do aktuálnej zložky" — bez nej by vznikla
   podzložka, čo nechcem.)

5. Po stiahnutí si prečítaj SETUP_GUIDE.md (ten z disku, nie z pamäte) a
   postupuj presne podľa neho. Začni Fázou 0 a pokračuj fázami 1 až 8. Pýtaj
   sa ma postupne, jeden krok naraz.

6. Rieš všetko za mňa — spúšťaj príkazy, edituj súbory, rieš chyby. Pýtaj sa
   len keď to fakt potrebuješ alebo keď ide o platené/nevratné veci (API
   kľúče, vytvorenie GitHub účtu, platený deploy do cloudu). Vysvetľuj v
   ľudskej reči, nie v žargóne. Hovor po slovensky a tykaj mi.

Pripravený? Začni.
```

**To je všetko.** Od tejto chvíle Claude robí všetko sám — nainštaluje git/python cez balíčkový manažér, stiahne kód, prejde s tebou všetkých 8 fáz (discovery → konfigurácia → ingest → test → GitHub backup → deploy → verifikácia). Ty len odpovedáš na jeho otázky a na 1-2 miestach klikneš v browseri (GitHub auth, Railway login).

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

- ✅ **Detekuje OS** (Mac/Windows/Linux) a **inštaluje git + Python za teba** cez `brew` alebo `winget` (žiadne sťahovanie z webu)
- ✅ Spýtať sa ťa **na čo** RAG bude (content / support / internal / sales / legal / iné) a podľa toho **automaticky** zvolí správnu architektúru
- ✅ Pomôcť ti získať **OpenAI, Qdrant Cloud a Cohere API kľúče** (presné URL a kroky)
- ✅ Vytvoriť `.env` súbor a **automaticky vygenerovať bezpečné access kľúče**
- ✅ Pomôcť ti **pripraviť tvoj obsah** (.md/.docx/.pdf) — vrátane automatického pridania YAML frontmatter ak chýba
- ✅ Spustiť **ingestion**, audit a sanity-test retrieval s tvojimi reálnymi otázkami
- ✅ **Vytvoriť ti súkromný GitHub repo ako zálohu** (cez `gh` CLI s browser auth — žiadne tokeny ručne)
- ✅ **Deploynúť** to do cloudu (Railway / Render) **alebo lokálne cez Docker + ngrok** — podľa tvojej voľby
- ✅ Pripojiť hotovú RAG do tvojho **Claude Code cez MCP server**

Celý setup trvá **30-60 minút** podľa toho koľko obsahu naliuvaš.

---

## ❓ FAQ — Otázky, ktoré možno máš teraz

**„Potrebujem GitHub účet?"**
Na **stiahnutie** tohto repa **nie** — je verejné, `git clone` funguje anonymne. Na **zálohovanie tvojej vlastnej kópie** (Fáza 6, voliteľná ale silne odporúčaná) **áno** — vytvoríš si zadarmo cez email/Google a Claude ťa cez to prevedie automaticky cez `gh` CLI s browser autentifikáciou (žiadne SSH kľúče, žiadne tokeny ručne).

**„Musím platiť za niečo?"**
- **OpenAI:** Áno, treba ~$5 kreditu (jednorazovo, vystačí na desaťtisíce dokumentov)
- **Qdrant Cloud:** Free tier stačí na desaťtisíce chunkov
- **Cohere:** Trial zadarmo (10 req/min, dosť na testovanie)
- **Deploy:** ~$5/mes Railway, alebo **$0** ak ideš lokálne + ngrok
- **GitHub:** $0 (súkromné repá zadarmo)

**„Nikdy som neotvoril terminál, zvládnem to?"**
Áno. Cesta A (vyššie) je navrhnutá tak, **aby si terminál ani nemusel otvárať**. Claude robí všetky príkazy za teba cez Bash tool. Ty len odpovedáš a 1-2× klikneš v browseri (pri OAuth login).

**„Kde to bude bežať?"**
Na konci si vyberáš jednu z 3 ciest:
- **Lokálne na tvojom počítači + ngrok** — zadarmo, ale len keď je laptop zapnutý
- **Railway cloud** — $5/mes, beží 24/7
- **Render** — alternatíva k Railway

Claude ti pri rozhodovaní pomôže.

**„Čo ak sa mi to nepodarí alebo niečo zlyhá?"**
Claude rieši errory automaticky. Ak neviete ďalej, otvorte issue na tomto repe alebo napíšte do Bootcamp Skool.

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
