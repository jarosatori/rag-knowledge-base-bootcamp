---
name: RAG Architecture Guide
description: Kontextový dokument pre Claude — ako navrhnúť a postaviť RAG databázu podľa use case užívateľa. Súčasť Claude Bootcamp RAG databáza produktu.
type: knowledge
category: rag
audience: claude-bootcamp-member
content_type: guide
tags: [rag, architektura, chunking, embedding, retrieval, hybrid-search, reranking, use-cases]
sensitivity: public
language: sk
version: 1.0
last_updated: 2026-04-07
---

# RAG Architecture Guide — Ako postaviť RAG databázu podľa use case

> Tento dokument je **kontext pre Claude**. Keď užívateľ (člen Claude Bootcampu) spustí setup RAG databázy, Claude si prečíta tento guide a podľa zadefinovaného use case navrhne správnu architektúru, chunking stratégiu, metadata schému a retrieval logiku. Následne upraví kód podľa návrhu.

---

## Časť 1 — Princípy, ktoré platia vždy

### 1.1 RAG je index, nie archív

Vektorová databáza **nie je úložisko súborov**. Je to vyhľadávací index. Originály (PDF, DOCX, txt) drž vždy bokom — vo file systéme, S3, Vercel Blob alebo Google Drive. V RAG ukladáš len chunky + embeddingy + metadata. V metadata drž `source_url` alebo cestu k originálu, aby sa dal kedykoľvek stiahnuť.

### 1.2 Tri vrstvy, ktoré rozhodujú o kvalite

Každý RAG stojí a padá na týchto troch vrstvách. V tomto poradí dôležitosti:

1. **Chunking** — ako rozsekáš dokumenty. Zlé chunky = žiadna architektúra to nezachráni.
2. **Retrieval logika** — ako hľadáš. Čistý vector similarity je začiatočnícka úroveň. Production je hybrid + rerank.
3. **Embedding model** — akým modelom vektorizuješ. Rozhoduje o semantike, najmä pre iné jazyky než angličtinu.

### 1.3 Vektorová podobnosť ≠ business relevancia

Embedding nájde, čo je **matematicky podobné**, nie čo je **správne pre daný problém**. Preto potrebuješ nad vektormi **business layer** — metadata, filtre, prípadne graph vzťahy.

### 1.4 Curation vs. comprehensiveness

Rozlíš dva typy RAGov:
- **Curated RAG** — malý počet kvalitných, destilovaných dokumentov. Používa sa na *content, mentoring, osobné know-how*. Cieľ: konzistentná kvalita výstupu.
- **Comprehensive RAG** — veľký objem dokumentov (tisíce až milióny). Používa sa na *support, legal, research*. Cieľ: nájsť ihlu v kope sena.

**Architektúra pre každý je iná.** Nikdy nemiešaj — buď jedno, alebo druhé, alebo dva oddelené indexy.

### 1.5 Signal-to-noise

Ak do RAG nalieješ nečistené transkripty, surové emaily, Slack debaty — kvalita retrieval klesá pre všetky otázky. Noise zaťažuje embeddingy a rieďuje výsledky. Pred ingestion vždy čisti a filtruj.

---

## Časť 2 — Chunking stratégie

### 2.1 Zlaté pravidlo

**Jeden chunk = jedna myšlienka / jedna sémanticky uzavretá jednotka.**

Ak chunk obsahuje tri rôzne témy, jeho embedding je priemer troch významov a podobnosť je rozmazaná.

### 2.2 Stratégie

| Stratégia | Popis | Kedy použiť |
|---|---|---|
| **Fixed-size** | Každých N tokenov, bez ohľadu na štruktúru | Nikdy ako primárna. Len ako fallback. |
| **Paragraph-aware** | Rešpektuje `\n\n`, fallback na vety pri dlhých blokoch | Default pre voľne písaný text (know-how, články) |
| **Structural** | Podľa nadpisov, sekcií, kapitol | Dokumentácia, manuály, zmluvy, knihy |
| **Semantic** | AI rozhoduje, kde rozseknúť podľa zmeny témy | Najvyššia kvalita, ale najdrahšie. Pre premium use cases. |
| **Sliding window s overlap** | Chunky sa prekrývajú (napr. 15-25% overlap) | Vždy — overlap zachová kontext pre chunky na okraji |
| **Parent-child (small-to-big)** | Embedduj malé chunky (200 tok), vráť väčší parent (1500 tok) | Keď chceš presný retrieval + veľa kontextu pre LLM |

### 2.3 Praktické parametre

| Typ obsahu | Chunk size | Overlap |
|---|---|---|
| Know-how, mentoring, príbehy | 300–500 tokenov | 15–20% |
| Technická dokumentácia | 500–800 tokenov | 10–15% |
| Zmluvy, legal | 400–600 tokenov | 20–25% (kontext kritický) |
| Support tikety / FAQ | 200–400 tokenov | 10% (jeden tiket = jeden chunk) |
| Kód | Podľa funkcií / tried | 0 (AST chunking) |

### 2.4 Čo NIKDY nechunkovať fixne

- Kód (použij AST-aware chunker — podľa funkcií/tried)
- Tabuľky (nechaj ako jeden chunk, alebo konvertuj na markdown s hlavičkami)
- Štruktúrované dáta JSON/YAML (chunk = jeden záznam)
- Zoznamy (nerozdeľ uprostred)

---

## Časť 3 — Embedding modely

### 3.1 Odporúčané modely (2026)

| Model | Dimenzie | Multilingual | Cena | Kedy |
|---|---|---|---|---|
| **OpenAI `text-embedding-3-large`** | 3072 | ✅ Výborný pre SK/CZ | $$ | Default pre väčšinu use cases |
| **OpenAI `text-embedding-3-small`** | 1536 | ✅ Dobrý | $ | Budget / veľký objem |
| **Cohere `embed-multilingual-v3`** | 1024 | ✅ Excelentný pre non-EN | $$ | Ak máš hlavne slovenčinu/češtinu |
| **BGE-M3** (open source) | 1024 | ✅ | Hosting | Self-hosted, plná kontrola |
| **Voyage `voyage-3-large`** | 1024 | ✅ | $$ | Najvyššia kvalita benchmark (2025) |

### 3.2 Dôležité pravidlá

- **Nikdy nemiešaj modely** v jednej kolekcii. Embeddings z rôznych modelov nie sú porovnateľné.
- **Pri zmene modelu musíš re-indexovať celú databázu.**
- **Pre slovenčinu/češtinu nepoužívaj staré modely** (`ada-002`, `text-embedding-ada-002`) — sú trénované primárne na EN a strácajú nuansy.
- **Dimenzionalita vs. kvalita:** Viac dimenzií ≠ vždy lepšie. Drahšie na storage aj search. 1024-1536 je sweet spot.

### 3.3 Translate-then-embed (edge case)

Ak máš zmiešaný obsah (SK + EN + DE) a chceš cross-lingual retrieval, jedna technika je preložiť všetko do angličtiny pre embedding, ale ukladať originál pre zobrazenie. Ľahko strácaš autentickosť — používaj opatrne.

---

## Časť 4 — Retrieval stratégie

### 4.1 Naivný vector RAG (začiatočnícka úroveň)

```
query → embed → vector search → top K → LLM
```

**Problém:** Nízka kvalita pre komplexné otázky, keyword presnosť zlá (mená, čísla, kódy), žiadny business context.

**Použi len na:** Quick prototypy, interné experimenty, content brainstorming kde je variabilita OK.

### 4.2 Metadata-filtered RAG

```
query → embed → vector search WITH filter (category, date, audience...) → top K → LLM
```

**Výhoda:** Zužuje search priestor na relevantné dokumenty pred podobnosťou.

**Použi vždy, keď máš aspoň základné metadata.**

### 4.3 Hybrid search (production štandard)

```
query → embed (dense) + tokenize (sparse/BM25) → paralelný search → Reciprocal Rank Fusion → top K
```

**Výhoda:** Dense zachytí sémantiku, sparse zachytí presné termíny (mená, čísla, kódy článkov). Kombinácia pokrýva obidva typy otázok.

**Použi pre:** Customer support, legal, technická dokumentácia, akýkoľvek use case s presnými identifikátormi.

### 4.4 Hybrid + Reranker (top úroveň)

```
query → hybrid search → top 20-30 → reranker (Cohere Rerank / BGE / Jina) → top 5 → LLM
```

Reranker je druhý, menší model, ktorý pre každú dvojicu (query, chunk) spočíta presný relevance score. Výrazne zlepšuje kvalitu (+15-30% relevancia podľa benchmarkov).

**Použi pre:** Všetky produkčné systémy, kde kvalita > cena.

### 4.5 Query rewriting / HyDE

**Problém:** Otázka užívateľa nemusí byť sémanticky podobná chunkom, aj keď odpoveď existuje.

**Riešenia:**
- **Multi-query:** Claude Haiku rozšíri otázku do 3-5 variantov, každý embedduje, výsledky spojí
- **HyDE (Hypothetical Document Embeddings):** LLM si predstaví ideálnu odpoveď a embedduje tú (nie otázku)
- **Query decomposition:** Komplexná otázka sa rozloží na podotázky, každá sa rieši zvlášť

### 4.6 Graph RAG

Chunky prepojené vzťahmi (napr. "Dedoles" → "2022" → "odchod" → "dôvody"). Namiesto čistej podobnosti systém prechádza graf.

**Kedy použiť:** Keď sú vzťahy medzi entitami kritické (organizácie, osoby, udalosti). Napr. pre "Jaro brain" RAG alebo analýzu investičného portfólia.

**Cena:** Výrazne drahšie na postavenie aj údržbu. Prvý krok: často stačí bohatá metadata.

### 4.7 Document-level retrieval

Niekedy užívateľ nechce chunky, ale celý dokument. Pridaj do metadata `document_id` + `chunk_index`. Funkcia `get_full_document(id)` vytiahne všetky chunky, zoradí, zlepí. Alebo ešte lepšie — drž originál v object storage a vráť URL.

---

## Časť 5 — Metadata schéma

Metadata je **business layer** nad vektormi. Čím lepšia, tým lepší retrieval. Pri ingestion investuj čas do správnej schémy.

### 5.1 Povinné polia (vždy)

```yaml
document_id: "unique_doc_id"        # Na zlepenie dokumentu späť
chunk_index: 0                       # Poradie v dokumente
total_chunks: 47                     # Koľko chunkov dokument má
source: "file_path_or_url"           # Odkiaľ to je
ingested_at: "2026-04-07T10:00:00Z"  # Kedy sa to tam dostalo
language: "sk"                       # ISO kód jazyka
```

### 5.2 Odporúčané polia (podľa use case)

```yaml
category: "leadership"               # Hlavná kategória
subcategory: "delegation"            # Podkategória
audience: "founder"                  # Pre koho je to určené
content_type: "framework" | "story" | "how-to" | "data"
tags: ["hiring", "culture"]          # Voľné tagy
sensitivity: "public" | "internal" | "private"
author: "Jaro Chrapko"               # Autor pôvodu
created_at: "2026-01-15"             # Dátum vzniku obsahu
version: 2                            # Verzia dokumentu
```

### 5.3 Kritické pravidlo

**Metadata musia byť filtrovateľné, nie opisné.** Každé pole, ktoré v metadata uložíš, by malo dávať zmysel ako filter pri retrieval. Ak ho nikdy nebudeš filtrovať, patrí do textu chunku, nie do metadata.

---

## Časť 6 — Use case → architektúra (rozhodovací strom)

Keď užívateľ zadefinuje svoj use case, podľa tejto tabuľky navrhni architektúru:

### 6.1 Content creation / personal know-how (Jarov use case)

**Cieľ:** Generovať autentický obsah z vlastných myšlienok a príbehov.

**Čo nalievať:**
- ✅ Destilované know-how (frameworky, lekcie, príbehy)
- ✅ Hotové kusy obsahu (posty, newslettery, scripty)
- ❌ Surové transkripty, emaily, Slack (patria do iných systémov)

**Architektúra:**
- Chunking: paragraph-aware, 400 tok, 15% overlap
- Embedding: `text-embedding-3-large`
- Metadata: category, content_type, tags, audience, sensitivity
- Retrieval: Metadata-filtered vector search (stačí — variabilita je tu feature)
- Reranker: Voliteľný, nie kritický

**Čo NEriešiť:** Hybrid BM25 (keywords nie sú dôležité pre inšpiráciu).

---

### 6.2 Customer support

**Cieľ:** Odpovedať zákazníkom presne a konzistentne, citovať zdroj, eskalovať pri nízkej istote.

**Čo nalievať:**
- ✅ Produktová dokumentácia, manuály, FAQ, help centre články
- ✅ Vyriešené tikety (otázka + odpoveď + kategória + produkt)
- ✅ Policies (returns, warranty, shipping, GDPR)
- ✅ Troubleshooting guides
- ❌ Surové email threads bez čistenia
- ❌ Interné Slack debaty
- ❌ Marketing materiály (iný tón, mätie model)
- ❌ Osobné údaje zákazníkov (GDPR)

**Architektúra:**
- Chunking: Structural pre docs (podľa nadpisov), 300-500 tok. Tikety: 1 tiket = 1 chunk.
- Embedding: `text-embedding-3-large` alebo Cohere multilingual (ak > 1 jazyk)
- Metadata: `source`, `category`, `product`, `language`, `last_updated`, `audience` (customer vs. agent), `resolution_status`
- Retrieval: **Hybrid (vector + BM25)** — čísla objednávok, kódy produktov musia match presne
- Reranker: **Áno** (Cohere Rerank) — kvalita kritická
- Fallback: Ak top score < threshold, eskaluj na človeka, nehalucinovať
- Citation: VŽDY vracať link na zdroj
- Dva indexy: `customer_facing` (verejné) + `agent_facing` (interné tipy)

**Synchronizácia:** Cron job zo Zendesk/Intercom/Notion každú hodinu. Pri update článku: zmaž staré chunky toho `document_id` a nahraď, neNapridávaj.

---

### 6.3 Internal knowledge hub (ChatGPT pre firmu)

**Cieľ:** Zamestnanci nájdu odpovede o firme, procesoch, HR, technike.

**Čo nalievať:**
- ✅ Confluence / Notion / SharePoint dumps
- ✅ HR policies, benefity, onboarding
- ✅ SOPs a procesy
- ✅ Meeting notes a rozhodnutia z porád (čistené)
- ✅ Architectural Decision Records (ADRs)
- ❌ Osobné dáta zamestnancov nad rámec roles
- ❌ Platové dáta (iný index s prísnym access control)

**Architektúra:**
- Chunking: Structural (rešpektuj hlavičky Confluence/Notion)
- Embedding: `text-embedding-3-large`
- Metadata: `source_system`, `author`, `team`, `access_level`, `last_updated`, `type` (policy/decision/howto)
- Retrieval: Hybrid + metadata filter podľa teamu a access_level
- Access control: **Kritický** — každý user má access_level, filter sa aplikuje vždy
- Reranker: Odporúčaný

---

### 6.4 Legal / Compliance

**Cieľ:** Nájsť precedenty v zmluvách, regulačné odpovede, compliance checks.

**Čo nalievať:**
- ✅ Historické zmluvy + templates
- ✅ Regulácie (GDPR, AML, sektorové)
- ✅ Právne stanoviská
- ✅ Interné policies
- ❌ Pracovné drafty bez verzie

**Architektúra:**
- Chunking: Structural podľa článkov/paragrafov zmluvy, 400-600 tok, 20-25% overlap
- Embedding: Špecializovaný legal model (ak existuje pre jazyk), inak `text-embedding-3-large`
- Metadata: `contract_type`, `counterparty`, `effective_date`, `jurisdiction`, `article_number`, `section`
- Retrieval: **Hybrid (vector + BM25) je povinný** — čísla článkov a presné termíny
- Document-level fetch: **Povinný** — právnik chce vidieť celú zmluvu
- Reranker: Áno
- Audit log: Každý query sa loguje (compliance)

---

### 6.5 Sales enablement

**Cieľ:** Sales rep pred callom dostane briefing, case studies, battle cards.

**Čo nalievať:**
- ✅ Case studies, win/loss reporty
- ✅ Competitor battle cards
- ✅ Pricing, discount policies
- ✅ Call transkripty (čistené, cez Gong/Fathom)
- ✅ Proposal templates

**Architektúra:**
- Chunking: Paragraph-aware, 400 tok
- Metadata: `industry`, `company_size`, `deal_size`, `stage`, `competitor`, `outcome`
- Retrieval: Metadata-filtered vector search + reranker
- Integration: CRM sync (HubSpot/Salesforce) — automaticky pridáva kontext k leadu

---

### 6.6 Engineering docs / codebase

**Cieľ:** Dev nájde architektúrne rozhodnutia, API, postmortems.

**Čo nalievať:**
- ✅ Codebase (AST chunking)
- ✅ ADRs, RFCs
- ✅ Postmortems
- ✅ API docs
- ❌ Auto-generovaná dokumentácia bez úpravy

**Architektúra:**
- Chunking: AST-aware pre kód, structural pre markdown
- Embedding: Code-specific model (napr. `voyage-code-3`) pre kód, text model pre docs
- Dva indexy: `code` a `docs`
- Retrieval: Hybrid (presné názvy funkcií kritické)
- Metadata: `repo`, `file_path`, `language`, `function_name`, `last_commit`

---

## Časť 7 — Setup workflow pre Claude

Keď Claude Bootcamp člen spustí setup svojej RAG databázy, postupuj takto:

### Krok 1 — Discovery (pýtaj sa)

1. **Aký je tvoj use case?** (content / support / internal / legal / sales / engineering / iné)
2. **Aký objem dokumentov očakávaš?** (< 100 / 100-1000 / 1000-10000 / 10000+)
3. **Aký typ obsahu?** (PDF / Markdown / web / databáza / kód / kombinácia)
4. **Aký jazyk?** (SK / EN / multilingual)
5. **Kto bude pristupovať?** (len ja / tím / zákazníci verejne)
6. **Potrebuješ access control / sensitivity levels?**
7. **Akú kvalitu potrebuješ?** (experiment / production)
8. **Rozpočet na API?** (minimal / standard / unlimited)

### Krok 2 — Navrhni architektúru

Na základe odpovedí použij rozhodovací strom z Časti 6 a priprav návrh:
- Chunking stratégia + parametre
- Embedding model
- Metadata schéma (YAML)
- Retrieval pipeline (naivný / hybrid / hybrid+rerank / graph)
- Access control schéma (ak potrebná)
- Sync strategy (cron / webhook / manual)

### Krok 3 — Ukáž návrh a získaj súhlas

Prezentuj návrh v tabuľke + stručné zdôvodnenie každého rozhodnutia. Spýtaj sa, či súhlasí alebo chce zmeny.

### Krok 4 — Uprav kód

Východiskový kód je v `src/` tohto repa (ingest.py, chunker.py, embedder.py, retrieve.py, api.py, mcp_server.py). Podľa schváleného návrhu:
- Uprav `config.py` (chunk_size, embedding model, collection name)
- Uprav `chunker.py` ak treba inú stratégiu (structural / AST / semantic)
- Uprav metadata schému v `ingest.py`
- Uprav `retrieve.py` — pridaj filtre, hybrid search, reranker podľa potreby
- Uprav `api.py` a `mcp_server.py` aby exponovali nové parametre

### Krok 5 — Test

Pred ingestion reálnych dát:
- Spusti ingest na 5-10 vzorkových dokumentoch
- Otestuj 10 reprezentatívnych otázok
- Skontroluj, či retrieval vracia zmysluplné výsledky
- Ak nie → diagnostika (najčastejšie: zlé chunky alebo zlý embedding model pre jazyk)

### Krok 6 — Evaluation harness

Vytvor `tests/eval_retrieval.py` — 20-30 otázok s očakávanými chunk IDs. Po každej zmene retrieval logiky spusti eval a porovnaj metriky (Recall@5, MRR).

---

## Časť 8 — Časté chyby a ako sa im vyhnúť

| Chyba | Príznak | Riešenie |
|---|---|---|
| Miešanie curated + comprehensive | Retrieval vracia raz kvalitné, raz náhodné | Dva oddelené indexy |
| Fixed-size chunking bez ohľadu na štruktúru | Chunky končia uprostred viet, stráca sa kontext | Paragraph-aware alebo structural |
| Nulový overlap | Informácia na hranici chunku sa nikdy nenájde | 10-25% overlap |
| Žiadne metadata | Nedá sa filtrovať, všetky výsledky zmiešané | Schéma od začiatku |
| Starý embedding model na slovenčinu | Sémantika rozmazaná, zlé výsledky | `text-embedding-3-large` alebo Cohere multilingual |
| Ingestion bez čistenia | Noise riedi výsledky | Pre-processing: odstráň hlavičky, pätičky, navigáciu, boilerplate |
| Žiadny eval harness | Nevieš, či zmeny pomáhajú alebo škodia | 20-30 testovacích otázok, automatizovaný test |
| LLM halucinuje nad slabými výsledkami | Odpovede vyzerajú dobre ale sú vymyslené | Fallback: ak top score < threshold, povedz "neviem" |
| Duplikáty po re-ingestion | Ten istý obsah 3x v databáze | Pri update: zmaž staré chunky `document_id`, potom pridaj nové |
| Originály len v RAG | Nedajú sa stiahnuť celé | Drž originály v object storage, v metadata `source_url` |

---

## Časť 9 — Kedy RAG nie je správna odpoveď

RAG nie je univerzálne riešenie. Nepoužívaj ho keď:

- **Dáta sa menia v reálnom čase** (ceny, stav skladu) → použi priame API query
- **Potrebuješ presné agregácie** (koľko, priemer, max) → použi SQL, nie RAG
- **Dokumentov je málo** (< 20) → daj všetko do kontextu LLM priamo
- **Potrebuješ deterministické odpovede** → štruktúrovaná databáza + lookup
- **Dáta sú vysoko štruktúrované** (tabuľky, JSON) → SQL alebo JSON query je lepší
- **Malá doména, veľa dotazov** → fine-tune model môže byť efektívnejší

**Dobrá otázka pred stavbou:** "Potrebujem vôbec RAG, alebo mi stačí dať dáta priamo do promptu / použiť SQL?"

---

## Časť 10 — Checklist pred produkciou

Pred tým, než spustíš RAG do produkcie, over:

- [ ] Chunking stratégia sedí typu obsahu
- [ ] Embedding model podporuje jazyk(y) obsahu
- [ ] Metadata schéma je definovaná a konzistentná
- [ ] Retrieval používa aspoň metadata filter (ideálne hybrid + rerank)
- [ ] Access control je implementovaný (ak treba)
- [ ] Eval harness existuje a metriky sú prijateľné
- [ ] Sync stratégia je definovaná (ako sa budú updaty dostávať do RAG)
- [ ] Originály sú v object storage, nie len v RAG
- [ ] Logging a audit trail existuje
- [ ] Fallback pre low-confidence otázky existuje
- [ ] PII a citlivé dáta sú ošetrené
- [ ] Cena na query je známa a udržateľná pri očakávanom objeme

---

**Koniec guide.** Tento dokument je živý — upravuj podľa nových poznatkov a feedback od členov Bootcampu.
