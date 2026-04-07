"""
Test script — creates sample documents, ingests them, and tests retrieval + filters.

Tests the full workflow:
1. Ingestion (all content defaults to internal, public flagged as pending)
2. Pre-approval retrieval (public queries return nothing — correct!)
3. Approval step (simulate approving pending chunks)
4. Post-approval retrieval (public queries now return results)
5. Security filters (private content never leaks to public/internal)
"""

import os
import sys
import shutil
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from ingest import run_ingestion, get_qdrant_client, ensure_collection, COLLECTION_NAME
from retrieve import retrieve_public, retrieve_internal, retrieve_private
from approve_public import get_pending_chunks, approve_chunk
from qdrant_client.models import Filter, FieldCondition, MatchValue


# ── Sample documents ────────────────────────────────────────

SAMPLE_DOCS = {
    "public/leadership/frameworks/delegation-framework.md": """---
category: leadership
content_type: framework
audience: founder
tags: [delegation, management, scaling]
---

# Framework delegovania úloh

Efektívne delegovanie je kľúčová zručnosť každého lídra. Bez neho sa nedá škálovať.

## 4 úrovne delegovania

1. **Urob presne toto** — Dáš konkrétny návod krok za krokom. Vhodné pre juniora alebo novú úlohu.
2. **Preskúmaj a navrhni** — Zamestnanec preskúma situáciu a navrhne riešenie. Ty schvaľuješ.
3. **Rozhodní sa a informuj ma** — Zamestnanec rozhodne sám, ale ťa informuje o výsledku.
4. **Rozhodní sa** — Plná autonómia. Zamestnanec nemusí reportovať každú úlohu.

## Kedy použiť ktorú úroveň

Záleží od dvoch faktorov: skúsenosť človeka a kritickosť úlohy. Čím skúsenejší človek a menej kritická úloha, tým vyššia úroveň delegovania.
""",

    "public/sales/how-to/sales-discovery.md": """---
category: sales
content_type: how-to
audience: manager
tags: [sales, discovery, closing]
---

# Ako viesť discovery call

Discovery call je najdôležitejší krok v predajnom procese. Bez správneho discovery sa nedá predávať.

## Štruktúra discovery callu

1. **Rapport** (2 min) — Buduj vzťah. Neskáč hneď do biznisu.
2. **Situácia** (5 min) — Zisti aktuálny stav. Aké nástroje používajú? Koľko ľudí v tíme?
3. **Problém** (10 min) — Čo ich bolí? Prečo hľadajú riešenie práve teraz?
4. **Dopad** (5 min) — Čo sa stane ak problém nevyriešia? Koľko ich to stojí?
5. **Riešenie** (5 min) — Ukáž ako tvoj produkt rieši ich problém.

## Najčastejšie chyby

- Hovoríš viac ako klient (80/20 pravidlo — klient hovorí 80%)
- Preskočíš fázu problému a ideš rovno na riešenie
- Nepýtaš sa na budget a rozhodovací proces
""",

    "internal/operations/checklists/onboarding-checklist.md": """---
category: operations
content_type: checklist
audience: manager
tags: [onboarding, hiring, process]
sensitivity: internal
---

# Onboarding checklist pre nového zamestnanca

## Pred nástupom (T-7 dní)
- [ ] Priprav pracovné miesto / laptop
- [ ] Vytvor email a prístupy do nástrojov
- [ ] Pošli uvítací email s agendou prvého dňa
- [ ] Priraď buddyho / mentora

## Prvý deň
- [ ] Welcome meeting s CEO/founderom
- [ ] Predstavenie tímu
- [ ] Prejdenie firemných hodnôt a kultúry
- [ ] Setup nástrojov (Slack, Notion, Git)

## Prvý týždeň
- [ ] Shadowing senior kolegu
- [ ] Prvá menšia úloha
- [ ] 1on1 s manažérom — feedback z prvých dní
""",

    "public/mindset/principles/growth-mindset.md": """---
category: mindset
content_type: princíp
audience: general
tags: [mindset, growth, learning]
---

# Growth Mindset ako základ úspechu

Ľudia s growth mindsetom veria, že ich schopnosti sa dajú rozvíjať. Fixed mindset ľudia veria, že talent je vrodený.

## Praktické rozdiely

- **Výzvy**: Growth mindset ich víta, fixed sa im vyhýba
- **Chyby**: Growth sa z nich učí, fixed ich skrýva
- **Feedback**: Growth ho hľadá, fixed sa ho bojí
- **Úspech iných**: Growth inšpiruje, fixed ohrozuje

## Ako budovať growth mindset v tíme

Oceňuj proces, nie výsledok. Namiesto "Si šikovný" povedz "Oceňujem ako si to vyriešil". Vytváraj prostredie kde je bezpečné robiť chyby.
""",

    "private/personal-notes/quarterly-reflection.md": """---
category: mindset
content_type: analýza
audience: founder
tags: [reflection, quarterly, personal]
sensitivity: private
---

# Q4 2024 Reflexia

## Čo fungovalo
- Delegovanie operatívy na COO uvoľnilo 15h/týždeň
- Nový sales proces zvýšil conversion o 23%
- Tímové retrospektívy každé 2 týždne zlepšili morálku

## Čo nefungovalo
- Príliš veľa projektov naraz — rozptýlenie focusu
- Nedostatočný onboarding nových ľudí
- Málo času na strategické myslenie

## Poučenia
Menej je viac. Vybrať 3 priority a povedať nie všetkému ostatnému.
""",

    "public/leadership/how-to/feedback-guide.md": """---
category: leadership
content_type: how-to
audience: manager
tags: [feedback, 1on1, communication]
---

# Ako dávať efektívny feedback

Feedback je dar. Ale len ak je podaný správne.

## SBI Model (Situation-Behavior-Impact)

1. **Situation** — Kedy a kde sa to stalo? "Na včerajšom meetingu..."
2. **Behavior** — Čo presne človek urobil? Fakty, nie interpretácie. "Prerušil si Petra 3x..."
3. **Impact** — Aký to malo dopad? "Peter sa odmlčal a nepovedal svoj návrh."

## Zásady

- Dávaj feedback do 24 hodín od situácie
- Súkromne pre kritický, verejne pre pochvalu
- Pýtaj sa na pohľad druhej strany
- Konči dohodou na konkrétnom kroku
""",
}


def create_test_files(base_dir: str):
    """Create sample files in a temporary directory."""
    for rel_path, content in SAMPLE_DOCS.items():
        full_path = os.path.join(base_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
    print(f"Created {len(SAMPLE_DOCS)} test documents in {base_dir}")


def reset_collection():
    """Delete and recreate the collection for clean testing."""
    client = get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME in collections:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing collection: {COLLECTION_NAME}")
    ensure_collection(client)


def auto_approve_all_pending(client):
    """Simulate approval: approve all pending chunks for testing."""
    pending = get_pending_chunks(client)
    approved = 0
    for point in pending:
        approve_chunk(client, point)
        approved += 1
    print(f"  Auto-approved {approved} chunks for testing")
    return approved


def run_tests():
    """Run the full test suite."""
    print("=" * 60)
    print("RUNNING KNOWLEDGE BASE TESTS")
    print("=" * 60)

    # Setup: create temp directory with sample docs
    test_dir = tempfile.mkdtemp(prefix="kb_test_")
    try:
        # Step 1: Create test files
        print("\n[1/6] Creating test documents...")
        create_test_files(test_dir)

        # Step 2: Reset and ingest
        print("\n[2/6] Resetting collection and ingesting...")
        reset_collection()
        run_ingestion(test_dir)

        client = get_qdrant_client()

        # Step 3: Test PRE-APPROVAL — public queries should return NOTHING
        print("\n[3/6] Testing pre-approval security (public should be empty)...")

        pre_tests = [
            {
                "name": "Pre-approval: public retrieval returns nothing",
                "query": "Ako delegovať úlohy?",
                "fn": retrieve_public,
                "expect_empty": True,
            },
            {
                "name": "Pre-approval: internal retrieval works (pending chunks are internal)",
                "query": "Ako delegovať úlohy?",
                "fn": retrieve_internal,
                "expect_empty": False,
                "expected_category": "leadership",
            },
            {
                "name": "Pre-approval: private content stays private",
                "query": "Čo fungovalo v Q4?",
                "fn": retrieve_private,
                "expect_empty": False,
                "expected_sensitivity": "private",
            },
        ]

        passed = 0
        failed = 0

        for test in pre_tests:
            success = _run_single_test(test)
            if success:
                passed += 1
            else:
                failed += 1

        # Step 4: Approve pending chunks
        print("\n[4/6] Simulating approval workflow...")
        auto_approve_all_pending(client)

        # Step 5: Test POST-APPROVAL — public queries should now return results
        print("\n[5/6] Testing post-approval retrieval...")

        post_tests = [
            {
                "name": "Post-approval: delegation (public)",
                "query": "Ako delegovať úlohy?",
                "fn": retrieve_public,
                "expect_empty": False,
                "expected_category": "leadership",
            },
            {
                "name": "Post-approval: sales discovery (public)",
                "query": "Ako viesť predajný hovor?",
                "fn": retrieve_public,
                "expect_empty": False,
                "expected_category": "sales",
            },
            {
                "name": "Post-approval: public still blocks private",
                "query": "Kvartálna reflexia a poučenia",
                "fn": retrieve_public,
                "expect_empty": False,
                "should_not_contain_sensitivity": "private",
            },
            {
                "name": "Internal retrieval — onboarding",
                "query": "Onboarding nového zamestnanca",
                "fn": retrieve_internal,
                "expect_empty": False,
                "expected_category": "operations",
            },
            {
                "name": "Private access — returns everything",
                "query": "Čo fungovalo v Q4?",
                "fn": retrieve_private,
                "expect_empty": False,
                "expected_sensitivity": "private",
            },
        ]

        for test in post_tests:
            success = _run_single_test(test)
            if success:
                passed += 1
            else:
                failed += 1

        total = len(pre_tests) + len(post_tests)

        # Step 6: Summary
        print(f"\n{'=' * 60}")
        print(f"RESULTS: {passed} passed, {failed} failed out of {total} tests")
        print(f"{'=' * 60}")

        return failed == 0

    finally:
        # Cleanup temp directory
        shutil.rmtree(test_dir, ignore_errors=True)


def _run_single_test(test: dict) -> bool:
    """Run a single test case and return True if passed."""
    print(f"\n  Test: {test['name']}")
    print(f"  Query: {test['query']}")

    results = test["fn"](test["query"], top_k=3)

    # Check if we expected empty results
    if test.get("expect_empty"):
        if not results:
            print(f"  PASS — Correctly returned no results")
            return True
        else:
            print(f"  FAIL — Expected no results, got {len(results)}")
            return False

    # We expected results
    if not results:
        print(f"  FAIL — No results returned")
        return False

    top_result = results[0]
    success = True

    # Check expected category
    if "expected_category" in test:
        actual = top_result["metadata"].get("category")
        if actual != test["expected_category"]:
            print(f"  FAIL — Expected category '{test['expected_category']}', got '{actual}'")
            success = False

    # Check that specific sensitivity is NOT in results
    if "should_not_contain_sensitivity" in test:
        for r in results:
            if r["metadata"].get("sensitivity") == test["should_not_contain_sensitivity"]:
                print(f"  FAIL — Found {test['should_not_contain_sensitivity']} content in filtered results")
                success = False
                break

    # Check expected sensitivity in results
    if "expected_sensitivity" in test:
        found = any(
            r["metadata"].get("sensitivity") == test["expected_sensitivity"]
            for r in results
        )
        if not found:
            print(f"  FAIL — Expected to find '{test['expected_sensitivity']}' content")
            success = False

    if success:
        print(f"  PASS (score: {top_result['score']:.4f})")

    return success


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
