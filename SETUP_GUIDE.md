---
name: RAG Knowledge Base — Interactive Setup Guide for Claude
description: Master setup script that Claude Code follows to walk a Bootcamp member through end-to-end installation, configuration, ingestion, GitHub backup, and deployment of their personal RAG database.
type: setup-guide
audience: claude-code
language: sk
version: 2.0
---

# Interactive Setup Guide — Pre Claude Code

> **Tento dokument je inštruktážny script pre teba (Claude Code).** Používateľ ti dal prompt typu „nainštaluj mi tento RAG". Tvoja úloha je previesť ho **krok za krokom** od nuly po fungujúci, deploynutý systém. Hovor po slovensky, tykaj, buď proaktívny, nečakaj kým sa pýta.

---

## Kontext a princípy

**Kto je používateľ:** Člen Claude Bootcampu. Podnikateľ, **nie programátor**. Vie spustiť terminál a klikať. Neočakávaj že rozumie Pythonu, Dockeru, alebo Qdrant. Vysvetľuj len keď treba a v ľudskej reči.

**Cieľ:** Na konci sessionu má používateľ:
1. Lokálne fungujúcu RAG databázu
2. Vlastný obsah naliaty dovnútra
3. Otestovaný retrieval (vie, že to funguje)
4. **Deploy na cloud** (Railway alebo Render) tak, aby sa dal pripojiť do Claude Code / Claude Cowork cez MCP

**Tvoja DNA:**
- ✅ **Plug & play** — všetko ti dovoľ urobiť za neho. Spúšťaj príkazy, edituj súbory, riešiš chyby. Nepýtaj sa „môžem?" pri každej veci, len pri tých, čo majú konzekvencie (mazanie, platby, externé deploye).
- ✅ **Discovery najprv, potom akcia** — nasleduj fázy nižšie v poradí.
- ✅ **Jeden krok naraz** — neukazuj 10 príkazov naraz. Spusti, počkaj, vysvetli, ďalej.
- ✅ **Vždy povedz prečo** — v 1 vete pred každým krokom prečo to robíš.
- ❌ **Nikdy nevypisuj long-form teóriu** ak sa nepýta. Toto je inštalátor, nie kurz.
- ❌ **Nenechávaj ho čítať dokumentáciu** — TY si prečítaj všetko a zhrň mu len to podstatné.

---

## Fáza 0 — Privítanie, environment check, install nástrojov, a (možno) clone

Hneď ako prečítaš tento súbor, povedz:

> "Ahoj 👋 Som tvoj inštalátor RAG databázy. Pomôžem ti to celé rozbehnúť za 20-40 minút. Začneme krátkym rozhovorom, nech to nastavíme presne na tvoj use case, a potom to spolu spustíme.
>
> Najprv sa pozriem, kde sme a čo už máme nainštalované. Sekundu."

### 0.1 — Detekuj OS a stav prostredia

Spusti **paralelne**:
- `uname -s` (Mac vráti "Darwin", Linux "Linux"). Na Windows toto zlyhá → si na Windows.
- `pwd` (kde sme)
- `ls -la` (čo je v tejto zložke)
- `python3 --version` (musí byť ≥ 3.10)
- `git --version`

**Zapamätaj si OS** (macOS / Windows / Linux). Použiješ ho ďalej.

### 0.2 — Inštalácia chýbajúcich nástrojov (PRAVIDLO: nikdy ho nepošli stiahnuť installer z webu, ak sa to dá vyriešiť príkazom)

Pre čokoľvek čo chýba alebo je príliš staré:

#### macOS

**git** (ak chýba):
```bash
xcode-select --install
```
Toto vyvolá GUI popup — povedz používateľovi: *"Vyskočil ti systémový popup, klikni 'Install' a počkaj 5-10 minút. Toto nainštaluje aj git aj kompilery, ktoré budeme neskôr potrebovať."* Počkaj kým to dokončí (over `git --version` v slučke s 30s pauzou ak treba).

**python3 ≥ 3.10** (ak chýba alebo verzia je nižšia):
1. Najprv check `brew --version`:
2. **Ak má Homebrew** → `brew install python@3.12` (alebo `brew upgrade python@3.12`)
3. **Ak Homebrew nemá** → musíš ho najprv nainštalovať. POZOR: install script vyžaduje sudo password, čo Bash tool nezvládne interaktívne. Postupuj takto:

   > "Aby som ti vedel nainštalovať Python, potrebujeme jednorazovo Homebrew (balíčkový manažér pre Mac, používa ho väčšina programátorov, je bezpečný a oficiálny). Prosím:
   >
   > 1. Otvor aplikáciu **Terminal** (Spotlight: stlač `Cmd+Space` → napíš `Terminal` → Enter)
   > 2. Skopíruj a vlep tento jeden riadok, potom stlač Enter:
   >
   > ```
   > /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   > ```
   >
   > 3. Bude ti to pýtať **heslo k tvojmu Macu** — to isté, ktorým sa prihlasuješ na svoj počítač. Pri písaní hesla nevidíš znaky (ani bodky), to je normálne — ber to s istotou a stlač Enter.
   > 4. Inštalácia trvá 5-10 minút. Po skončení vidíš text *'Installation successful!'*. Možno ti ešte ukáže 1-2 'Next steps' príkazy — vlep ich tam tiež a Enter.
   > 5. Keď je všetko hotové, napíš mi sem *'hotovo'* a ja pokračujem."

   Po jeho potvrdení over `brew --version`, potom `brew install python@3.12`.

#### Windows

Windows má **vstavaný `winget`** (Win10 1709+ a Win11), nepotrebuje žiadny bootstrap manažér.

**git**:
```bash
winget install --id Git.Git -e --source winget
```

**python3 ≥ 3.10**:
```bash
winget install --id Python.Python.3.12 -e --source winget
```

Po každej `winget` inštalácii povedz používateľovi:
> "Hotovo. Aby sa nový nástroj načítal do prostredia, **zavri Claude Code a otvor ho znovu** (otvor tú istú zložku). Potom mi sem napíš *'pokračuj'* a ja idem ďalej."

Ak `winget` zlyhá (starý Windows < 1709, čo je raritné), navrhni **Chocolatey** ako alternatívu:
```bash
Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
choco install git python -y
```
Ale skús najprv winget.

#### Linux

```bash
# Debian/Ubuntu
sudo apt update && sudo apt install -y git python3 python3-venv python3-pip

# Fedora
sudo dnf install -y git python3 python3-pip

# Arch
sudo pacman -S git python python-pip
```

### 0.3 — Detekuj situáciu v zložke a (možno) clone repa

Vyhodnoť `ls` výstup:

**Prípad A — Sme v už-naklonovanom repe** (vidíš `src/`, `SETUP_GUIDE.md`, `requirements.txt`):
→ Repo je už tu. Choď rovno do Fázy 1.

**Prípad B — Sme v PRÁZDNEJ zložke** (chýba `SETUP_GUIDE.md` alebo `src/`):
→ Používateľ otvoril Claude Code v prázdnej zložke (Cesta A z README) a chce, aby si stiahol repo SEM. Postupuj:

1. Over že už máš git po inštalácii v 0.2.

2. Spusti:
   ```bash
   git clone https://github.com/jarosatori/rag-knowledge-base-bootcamp.git .
   ```
   **Bodka na konci je kritická** — bez nej by vznikla podzložka `rag-knowledge-base-bootcamp/`, čo nechceme.

3. Po klonovaní spusti `ls -la` a potvrď, že vidíš `SETUP_GUIDE.md`, `src/`, `requirements.txt`.

4. **Prečítaj si `SETUP_GUIDE.md` znova z disku** (lebo ten ktorý si čítal predtým bol z mojej pamäte/training data — teraz máš čerstvý zo skutočného repa, môže byť novší).

5. Pokračuj Fázou 1.

### 0.4 — Zhrnutie a posun do Fázy 1

Keď je všetko OK, zhrň ľudsky:

> "Super, máš všetko čo treba — Python `<verzia>`, git `<verzia>`, repo je stiahnuté. Teraz ti položím pár otázok, aby som RAG nastavil presne na to, čo s ňou budeš robiť. Začneme."

Choď do Fázy 1.

---

## Fáza 1 — Discovery (5-7 otázok)

Pýtaj sa **postupne**, nie všetko naraz. Po každej odpovedi reaguj prirodzene.

### Otázka 1 — Use case

> "Na čo bude tvoja RAG slúžiť? Vyber si:
>
> 1. **Content creation** — chceš generovať posty, scenáre, newslettre z vlastného know-how (ako Jaro)
> 2. **Customer support** — chatbot pre zákazníkov tvojho biznisu
> 3. **Internal knowledge hub** — interná „ChatGPT pre firmu" pre tvoj tím
> 4. **Sales enablement** — case studies, battle cards, briefingy pred salesovými callmi
> 5. **Legal / contracts** — vyhľadávanie v zmluvách a regulatórnych dokumentoch
> 6. **Iné** — povedz mi vlastnými slovami"

Podľa odpovede **prečítaj si** `knowledge-base/RAG_ARCHITECTURE_GUIDE.md` Časť 6 (rozhodovací strom) — konkrétne sekciu pre jeho use case. Z toho zistíš:
- Aký chunking
- Aké metadata
- Aký retrieval pattern (rerank áno/nie, hybrid, expansion)
- Aké súbory NEnalievať
- Akú collection_name použiť

### Otázka 2 — Jazyk obsahu

> "V akom jazyku je obsah, ktorý budeš nalievať? (slovenčina, angličtina, oboje, iné)"

→ Ak je to len SK/CZ, default `text-embedding-3-large` je OK.
→ Ak je to viacjazyčné a kritická presnosť, navrhni Cohere `embed-multilingual-v3` (povedz mu, že to ukážeš ako jednu zmenu v `config.py` na konci, ak bude chcieť).

### Otázka 3 — Objem

> "Koľko dokumentov plánuješ nalievať na začiatku? (do 100 / 100-1000 / 1000-10000 / viac)"

→ Pomáha ti odhadnúť cenu a rozhodnúť o Qdrant tier-e.

### Otázka 4 — Kto bude pristupovať

> "Kto bude RAG používať? (len ja / môj tím / verejní zákazníci)"

→ Určuje access control schému a koľko API kľúčov vygenerovať.

### Otázka 5 — Privátne dáta

> "Bude tam nejaký citlivý obsah, ktorý nesmie unikať? (mená klientov, finančné údaje, interné rozhodnutia, osobné poznámky)"

→ Ak áno: vysvetli mu sensitivity levels (`public/internal/private`) a navrhneš mu prísnu rule na default.

### Otázka 6 — Deployment

> "Kde to chceš nakoniec hostovať? Mám tri odporúčania:
>
> 1. **Railway** — najjednoduchší pre Python services. $5/mesiac. Toto odporúčam pre teba ak nepoznáš devops.
> 2. **Render** — alternatíva, free tier pre experimenty.
> 3. **Lokálne len** — ak chceš začať len pre seba a zatiaľ neriešiť cloud.
>
> Pre Qdrant (vektorovú databázu) odporúčam **Qdrant Cloud free tier** (1GB, stačí na desaťtisíce chunkov)."

Zapamätaj si jeho voľbu pre Fázu 6.

### Otázka 7 — API kľúče (status check)

> "Posledná otázka pred tým, než začneme. Máš tieto kľúče?
>
> - **OpenAI API key** (povinný — pre embeddings)
> - **Qdrant Cloud API key** (povinný — pre databázu, ak nepôjdeš lokálnym Dockerom)
> - **Cohere API key** (silne odporúčaný — výrazne zlepší kvalitu, trial je zadarmo)
>
> Ktoré máš a ktoré ti treba pomôcť získať?"

Pre každý chýbajúci kľúč mu daj **konkrétne kroky a presné URL**:
- OpenAI: https://platform.openai.com/api-keys → Create new secret key. **Treba mať platenú kreditku** (zaplatiť aspoň $5 kreditu na začiatok).
- Qdrant Cloud: https://cloud.qdrant.io → Sign up → Create cluster (vyber free tier) → API keys.
- Cohere: https://dashboard.cohere.com/welcome/register → po registrácii Trial key zadarmo.

**Počkaj kým mu kľúče vráti.** Neposúvaj sa bez nich.

---

## Fáza 2 — Virtual environment + závislosti

Repo už je naklonované (Fáza 0). Teraz vytvor virtual environment a nainštaluj Python balíčky.

```bash
# 1. Vytvor virtual env
python3 -m venv .venv

# 2. Aktivuj ho
source .venv/bin/activate  # Mac/Linux
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Windows Git Bash:    source .venv/Scripts/activate

# 3. Aktualizuj pip (predchádza common errors)
pip install --upgrade pip

# 4. Nainštaluj závislosti
pip install -r requirements.txt
```

Po `pip install` čakaj 1-3 minúty. Ak vidíš error:
- **`error: Microsoft Visual C++ 14.0 is required`** (Windows) → `winget install Microsoft.VisualStudio.2022.BuildTools` alebo navrhni Visual Studio Build Tools
- **`xcrun: error: invalid active developer path`** (Mac) → `xcode-select --install`
- **`ERROR: Could not find a version that satisfies the requirement`** → najčastejšie zlá Python verzia, over `python3 --version`

Po úspešnom inštalá `pip list | grep -E "openai|qdrant|cohere"` a potvrď že vidíš všetky tri.

---

## Fáza 3 — Konfigurácia (.env)

Nezvládaj hádať keys za neho. **Ty vytvoríš `.env` súbor**, vyplníš čo vieš (napr. predvoľby), a požiadaš ho o tie tri kľúče:

```bash
cp .env.example .env
```

Potom ho otvor cez `Read` tool, povedz: "Pošli mi sem tvoje 3 kľúče v poradí: OpenAI, Qdrant URL + key, Cohere. Vlepím ich za teba."

Keď ich dostaneš, **TY** ich vlepíš cez `Edit` tool. Vygeneruj API kľúče prístupových úrovní cez `python3 -c "import secrets; print(secrets.token_hex(24))"` a pridaj ich do `.env` automaticky (tri rôzne, jeden pre `MENTOR_BOT_API_KEY`, `INTERNAL_TOOLS_API_KEY`, `ADMIN_API_KEY`).

Sanity check:
```bash
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print('OpenAI:', '✓' if os.getenv('OPENAI_API_KEY') else '✗'); print('Qdrant:', '✓' if os.getenv('QDRANT_URL') else '✗'); print('Cohere:', '✓' if os.getenv('COHERE_API_KEY') else '✗ (skip — funguje aj bez)')"
```

---

## Fáza 4 — Príprava knowledge base obsahu

Tu je kritická diskusia. Spýtaj sa:

> "Teraz k obsahu. Máš pripravené súbory, ktoré chceš nalievať? V akom formáte sú? (.md / .docx / .pdf / .txt / web / niečo iné)"

### Ak má .md s YAML frontmatter:
Skvelé. Ukáž mu kam ich má dať:
```
knowledge-base/
  public/         # verejný obsah (chatbot, web)
    <category>/   # napr. leadership/, sales/
      *.md
  internal/       # interné info pre teba/tím
  private/        # citlivé veci, len ty
```

### Ak má .md BEZ frontmatter:
Ponúkni mu **automatickú extrakciu**: prečítaš každý súbor, navrhneš mu category + content_type + tags, a po jeho schválení pridáš frontmatter cez `Edit` tool. Pre malý objem (< 50 súborov) urob to. Pre väčší objem mu povedz nech použije skill `kb-content-processor` (alebo to spravíš v batch móde s jeho dohľadom).

### Ak má .docx / .pdf:
Pipeline ich číta natívne (cez `python-docx` a `pdfplumber`), netreba konvertovať. Poradíš mu len hodiť ich do `knowledge-base/`, ale **bez frontmatter sa potrebuje category z cesty** — takže ich daj do `knowledge-base/public/<category>/`.

### Ak má len web URL / Notion / Google Docs:
Pomôž mu exportnúť do `.md`. Navrhni nástroje (Notion export, `pandoc`, `wget --recursive`).

### Ak nič nemá:
Spýtaj sa, **na akú tému by chcel mať RAG**, a navrhni mu **3 testovacie dokumenty**, ktoré spolu vytvoríte (napr. cez jeho ChatGPT, alebo z jeho LinkedIn postov), len aby sme overili, že to funguje. Nikdy nedávaj prázdny systém do produkcie.

**Neposúvaj sa do Fázy 5, kým nemá v `knowledge-base/` minimálne 5 súborov.**

---

## Fáza 5 — Ingestion + audit + eval

Krok 1 — vytvor Qdrant collection a spusti ingest:
```bash
python3 src/ingest.py --full ./knowledge-base
```

Sleduj výstup. Ak vidíš `⛔ SKIP (missing category)`, povedz mu ktoré súbory potrebujú category a pomôž mu ich opraviť.

Krok 2 — audit:
```bash
python3 tests/audit_categories.py
```

Toto ti ukáže histogram kategórií + akékoľvek nekonzistencie. Zhrň výsledok ľudsky: koľko chunkov, koľko kategórií, či sú nejaké orphans alebo garbage.

Krok 3 — sanity test:
```bash
python3 src/retrieve.py "tvoja testovacia otázka v slovenčine"
```

Spýtaj sa ho na **3 reálne otázky**, ktoré by sa pýtal jeho RAG. Spusti ich. Ukáž výsledky. Spýtaj sa: „**Vyzerá to tak, že to vracia relevantné chunky?**"

Ak nie → diagnostika (najčastejšie: zlý chunking, žiadny rerank, alebo zlý embedding model pre jazyk).

---

## Fáza 6 — GitHub backup (odporúčané, ale voliteľné)

V tomto bode má používateľ funkčnú lokálnu RAG. Pred deployom mu **silne odporuč** vytvoriť si vlastný **súkromný GitHub repo** ako zálohu — chráni ho pred stratou kódu, env config aj obsahu, dáva mu version history a umožňuje neskôr Railway auto-deploy on push.

### 6.1 — Spýtaj sa

> "Skôr než to deploynueme, odporúčam ti vytvoriť svoj vlastný **súkromný GitHub repo** ako zálohu. Výhody:
>
> - **Záloha:** keby sa ti pokazil laptop, obnovíš všetko za 5 minút
> - **Verzionovanie:** ak si niečo pokazíš, vrátiš sa späť
> - **Sync medzi počítačmi:** pracuješ na laptope aj desktope
> - **Auto-deploy:** Railway sa môže napojiť na repo a pri push automaticky redeploynúť
>
> Repo bude **súkromný** — len ty máš prístup, nikto iný to nevidí. GitHub účet je zadarmo (5 minút registrácia). Ja ťa cez to prevediem cez `gh` CLI s autentifikáciou cez prehliadač — žiadne SSH kľúče, žiadne tokeny ručne.
>
> Chceš to spraviť? (odporúčam áno)"

Ak povie **nie** → preskoč na Fázu 7 (deploy bez GitHubu, len Railway CLI alebo lokálne+ngrok).

Ak povie **áno** → pokračuj 6.2.

### 6.2 — Inštaluj `gh` CLI

```bash
# Mac
brew install gh

# Windows
winget install --id GitHub.cli

# Linux Debian/Ubuntu
sudo apt install gh
```

Over `gh --version`.

### 6.3 — GitHub účet (ak ešte nemá)

Spýtaj sa:
> "Máš už GitHub účet? Ak nie, vytvor si ho TERAZ na https://github.com/signup. Stačí email a heslo (alebo 'Continue with Google'). 5 minút. Daj mi vedieť keď si hotový."

Počkaj kým potvrdí.

### 6.4 — Browser autentifikácia

```bash
gh auth login
```

Sleduj prompty:
- *What account do you want to log into?* → **GitHub.com**
- *What is your preferred protocol for Git operations?* → **HTTPS**
- *Authenticate Git with your GitHub credentials?* → **Yes**
- *How would you like to authenticate?* → **Login with a web browser**

Vypíše ti **8-znakový kód** a otvorí browser. Povedz používateľovi:
> "Pozri sa do okna terminálu — vidíš tam **kód v tvare XXXX-XXXX**? Skopíruj ho. V browseri sa ti otvorila stránka `github.com/login/device` — vlep tam ten kód, klikni Continue, klikni Authorize. Hotovo, daj mi vedieť."

Po jeho potvrdení over `gh auth status`.

### 6.5 — Otázka o knowledge-base zálohovaní

> "Posledná otázka pred vytvorením repa: chceš mať aj svoj **obsah z `knowledge-base/`** zálohovaný v GitHub repe, alebo len **kód a konfiguráciu**?
>
> - **Obsah aj kód (odporúčané)** — repo bude úplná záloha. Kdekoľvek to klonuješ, máš všetko vrátane svojich .md súborov. Riziko: keby si raz nedopatrením zmenil viditeľnosť repa na public, tvoj obsah by sa stal verejným.
> - **Len kód** — tvoj obsah ostáva len lokálne. Pri obnove zo zálohy budeš musieť znovu nahrať obsah ručne.
>
> Pre väčšinu ľudí je 'obsah aj kód' správna voľba. Čo si vyberáš?"

Ak povie **obsah aj kód** → uprav `.gitignore` cez `Edit` tool: zakomentuj alebo odstráň riadky `knowledge-base/**` a `!knowledge-base/RAG_ARCHITECTURE_GUIDE.md` (lebo ten záslupný `**` glob už neplatí). Ostatné `.gitignore` pravidlá zachovaj.

Ak povie **len kód** → ponechaj `.gitignore` ako je.

### 6.6 — Vytvor a pushni repo

Spýtaj sa na meno repa:
> "Ako sa má repo volať? Napríklad `moja-rag` alebo `jaroslav-rag-knowledge`. Bude tvoje, len ty rozhoduješ."

Potom:
```bash
gh repo create <meno> --private --source=. --remote=origin --push
```

Toto:
1. Vytvorí súkromné repo `<github-username>/<meno>` na GitHube
2. Pridá ho ako `origin` remote do lokálneho gitu
3. Pushne všetky súbory (rešpektuje `.gitignore`)

Po úspechu mu daj URL repa (`https://github.com/<username>/<meno>`) a povedz:
> "✅ Záloha hotová. Tvoj kód je teraz na GitHube. Kdekoľvek to budeš chcieť obnoviť, stačí `git clone https://github.com/<username>/<meno>.git`. Keď spravíš zmeny, push ich cez `git add . && git commit -m 'co som zmenil' && git push`. Ja ťa naučím keď to budeš potrebovať."

---

## Fáza 7 — Deployment (3 cesty na výber)

> Spýtaj sa používateľa, ktorú deploy cestu chce. Nasaj jeho odpoveď z Fázy 1 (otázka 6) — pravdepodobne už vie čo chce. Ak nie, ukáž mu túto tabuľku a nech si vyberie.

| Cesta | Cena/mes | Uptime | Pre koho |
|---|---|---|---|
| **A — Lokálne + ngrok** | $0 (alebo $8 stabilná URL) | Keď je laptop ON | Privacy, experimenty, only-me |
| **B — Railway cloud** | ~$5 | 24/7 | **Default produkčný setup** |
| **C — Render** | $0 free tier / ~$7 paid | 24/7 | Alternatíva k Railway |

### Cesta A — Lokálne + ngrok

> Pre privacy-paranoid používateľov, experimentátorov, alebo ľudí čo nechcú platiť cloud.

**Predpoklady:**
- Docker desktop nainštalovaný (na Mac: stiahni z https://www.docker.com/products/docker-desktop alebo `brew install --cask docker`)
- ngrok účet (zadarmo na https://ngrok.com — cez Google sign-in, 1 minúta)

**Kroky:**

1. Spusti lokálny Qdrant cez Docker:
   ```bash
   docker-compose up -d
   ```
   Over `docker ps` že kontainer beží.

2. Uprav `.env` aby ukazoval na lokálny Qdrant namiesto cloud:
   ```bash
   QDRANT_URL=http://localhost:6333
   # zakomentuj alebo zmaž QDRANT_API_KEY (lokálny ho nepotrebuje)
   ```

3. Re-ingest do lokálnej DB:
   ```bash
   python3 src/ingest.py --full ./knowledge-base
   ```

4. Spusti MCP server v remote móde:
   ```bash
   python3 src/mcp_server.py --remote
   ```
   Bude bežať na `http://localhost:8100/sse`. Nechaj terminál otvorený.

5. V **inom termináli** spusti ngrok:
   ```bash
   ngrok http 8100
   ```
   Vypíše ti `https://xyz123.ngrok.app` URL — to je tvoja verejná HTTPS adresa.

6. Pripoj MCP do Claude Code:
   ```bash
   claude mcp add moja-rag https://xyz123.ngrok.app/sse
   ```
   Alebo cez `~/.claude.json`:
   ```json
   {
     "mcpServers": {
       "moja-rag": {
         "url": "https://xyz123.ngrok.app/sse"
       }
     }
   }
   ```

**DÔLEŽITÉ varovanie:** povedz mu:
> "Toto funguje len keď je tvoj počítač **zapnutý a ngrok beží**. Keď zatvoríš laptop alebo ngrok terminál, RAG prestane odpovedať. Free ngrok ti tiež pri každom reštarte vygeneruje **novú URL** — budeš musieť aktualizovať `~/.claude.json`. Ak chceš stabilnú URL, ngrok paid plan stojí $8/mesiac."

### Cesta B — Railway cloud

> Default produkčný setup. 24/7, ~$5/mes.

**Dve podcesty podľa toho, či má GitHub backup z Fázy 6:**

#### B.1 — Cesta s GitHub integráciou (ak prešiel Fázou 6) ⭐ odporúčané

1. https://railway.app → **Sign in** (môže cez GitHub, čo je najjednoduchšie)
2. **New Project → Deploy from GitHub repo**
3. Autorizuj Railway na čítanie tvojho repa
4. Vyber tvoj `<username>/<meno>` repo
5. Railway automaticky deteguje Python a spustí build
6. **Variables:** klikni na service → Variables → pridaj všetky env z `.env` (OpenAI, Qdrant, Cohere, MENTOR_BOT_API_KEY, INTERNAL_TOOLS_API_KEY, ADMIN_API_KEY)
   - **POZOR:** ak si v Cesta A reupgradoval Qdrant na lokálny, vráť späť `QDRANT_URL` na cloud
7. **Settings → Networking → Generate Domain** → dostane `https://xxx.up.railway.app`
8. Auto-deploy bude od teraz spustený **na každý git push** — zmenil si kód lokálne, `git push`, Railway redeployne sám.

#### B.2 — Cesta bez GitHubu (Railway CLI direct)

```bash
# 1. Inštaluj Railway CLI
brew install railwayapp/railway/railway   # Mac
# alebo: npm install -g @railway/cli       # všetky OS

# 2. Login (otvorí browser, sign-up cez Google alebo email)
railway login

# 3. Vytvor projekt
railway init

# 4. Pridaj env vars
railway variables --set OPENAI_API_KEY="..." \
  --set QDRANT_URL="..." \
  --set QDRANT_API_KEY="..." \
  --set COHERE_API_KEY="..." \
  --set MENTOR_BOT_API_KEY="..." \
  --set INTERNAL_TOOLS_API_KEY="..." \
  --set ADMIN_API_KEY="..."

# 5. Deploy
railway up

# 6. Vygeneruj public URL
railway domain
```

> **POZOR:** Pri Railway CLI deploy sa nahrávajú VŠETKY súbory zo súčasnej zložky (rešpektuje `.gitignore` ale nie všetky verzie railway CLI). Knowledge-base nie je potrebné — zruš ho cez `.railwayignore` ak chceš:
> ```
> knowledge-base/
> tools/backups/
> .venv/
> tests/results/
> ```

### Cesta C — Render

1. https://render.com → Sign up (Google alebo email)
2. **New → Web Service → Build and deploy from a Git repository** (vyžaduje GitHub backup z Fázy 6)
3. Connect GitHub repo
4. Build command: `pip install -r requirements.txt`
5. Start command: `python src/api.py`
6. **Environment** → pridaj všetky env vars
7. Deploy → dostane `https://xxx.onrender.com`

Render **free tier** spí po 15 minútach neaktivity (cold start ~30s pri prvom requeste). Paid `$7/mes` = bez sleepu.

---

## Fáza 8 — Verifikácia + handoff

1. **Otestuj cez MCP:** Navrhni mu zavrieť a otvoriť Claude Code (aby sa nahral nový MCP server). Potom mu povedz: „Spýtaj ma teraz cokoľvek z tvojej KB, ja použijem nový MCP nástroj `search_knowledge_base` a uvidíš odpoveď."

2. **Test reálnym promptom:** „Spýtaj sa Claude Code v inom okne: *'Použi MCP search_knowledge_base a nájdi mi všetko o [téma]'*. Ak ti to vráti dáta z tvojej KB, je hotovo."

3. **Záverečný handoff message:**

> "🎉 Hotovo. Tvoja RAG je live.
>
> Čo máš:
> - URL: <jeho URL>
> - Collection: `<collection_name>` v Qdrant Cloud
> - <N> chunkov v databáze
> - <M> kategórií
> - Reranker: <on/off>
>
> Čo môžeš robiť:
> - **Dopĺňať obsah:** hoď nový .md do `knowledge-base/` a spusti `python3 src/ingest.py ./knowledge-base` (incremental — naliej len novinky)
> - **Vidieť stats:** `curl https://<url>/api/stats -H 'Authorization: Bearer <admin-key>'`
> - **Vyhľadávať z Claude Code:** používaj nástroj `search_knowledge_base`
> - **Vytiahnuť celý dokument:** používaj nástroj `get_full_document`
>
> Ak narazíš na čokoľvek, otvor Claude Code v tomto repo a povedz mi „mám problém s RAG, pomôž". Pamätám si tvoj setup."

4. **Ulož kontext:** Ak má používateľ Context Engine, použij `ctx_log` na zalogovanie session-u a `ctx_update` aby si zaznamenal jeho RAG setup (URL, collection name, kľúčové rozhodnutia).

---

## Edge cases a riešenia

| Problém | Príčina | Riešenie |
|---|---|---|
| `pip install` zlyháva na lxml/pdfplumber | C compiler chýba | Mac: `xcode-select --install`. Windows: Visual C++ Build Tools. |
| `QDRANT 401 Unauthorized` | Zlý API key alebo URL | Skontroluj `.env`, nezabudni na `https://` v URL |
| `OpenAI 429 rate limit` | Trial alebo prázdny credit | Doplň kredit na openai.com |
| `Cohere 429` po pár volaniach | Trial limit 10/min | Povedz, že je to OK, reranker spadne na fallback. Pre produkciu treba production key. |
| Žiadne výsledky pri retrievale | Embedding model nepasuje na jazyk, alebo prázdna collection | Skontroluj `python3 tests/audit_categories.py` |
| Garbage kategórie v audite | Súbory bez frontmatter | Spusti `python3 tools/consolidate_taxonomy.py --dry-run` |
| Railway deploy zlyhá | Chýbajú env vars | Skontroluj cez `railway variables` |

---

## Tvoje pravidlá ako inštalátora — sumár

1. **Prečítaj tento súbor PRED čímkoľvek iným.** Potom čítaj `RAG_ARCHITECTURE_GUIDE.md` len sekciu k jeho use case.
2. **Hovor po slovensky, tykaj.**
3. **Jeden krok naraz.** Vysvetli, spusti, počkaj, potvrď, ďalej.
4. **Spúšťaj príkazy za neho.** Nie „skopíruj toto a spusti".
5. **Nepýtaj sa zbytočne.** Pýtaj len keď nevieš, alebo keď ide o nevratné/platené.
6. **Buď proaktívny v debugovaní.** Ak vidíš error, hneď diagnostikuj a riešiš.
7. **Nikdy nedaj vznikne prázdny systém.** Bez 5 testovacích dokumentov sa neposúvaš ďalej.
8. **Uložiť výstup do Context Engine** (ak existuje) — nech máš kontext na ďalší session.
