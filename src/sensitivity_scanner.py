"""
Sensitivity scanner — detects potentially sensitive content in text chunks.
Scans for names, emails, phone numbers, company names, financial data, addresses.
"""

import re


def scan_chunk(text: str) -> list[str]:
    """
    Scan a text chunk for sensitive content patterns.
    Returns a list of warning labels found.
    """
    warnings = []

    if _contains_names(text):
        warnings.append("contains_names")

    if _contains_emails(text):
        warnings.append("contains_emails")

    if _contains_phone_numbers(text):
        warnings.append("contains_phone_numbers")

    if _contains_company_names(text):
        warnings.append("contains_company_names")

    if _contains_financial_data(text):
        warnings.append("contains_financial_data")

    if _contains_addresses(text):
        warnings.append("contains_addresses")

    return warnings


def _contains_names(text: str) -> bool:
    """Detect patterns like 'Ján Novák', 'Peter Kováč', etc."""
    # Pattern: Capitalized word followed by capitalized word (likely name + surname)
    # Exclude common sentence starts by requiring it not to be at line/sentence start
    name_pattern = r'(?<=[,;:\s])[A-ZÁÉÍÓÚČĎĽŇŘŠŤŽÝŽ][a-záéíóúčďľňřšťžýž]+\s+[A-ZÁÉÍÓÚČĎĽŇŘŠŤŽÝŽ][a-záéíóúčďľňřšťžýž]+'
    matches = re.findall(name_pattern, text)

    # Filter out common false positives (Slovak/Czech common phrases)
    false_positives = {
        "Growth Mindset", "Fixed Mindset", "Discovery Call",
        "Knowledge Base", "Mentor Bot", "Docker Compose",
    }
    real_matches = [m.strip() for m in matches if m.strip() not in false_positives]
    return len(real_matches) > 0


def _contains_emails(text: str) -> bool:
    """Detect email addresses."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return bool(re.search(email_pattern, text))


def _contains_phone_numbers(text: str) -> bool:
    """Detect phone numbers (Slovak, Czech, international formats)."""
    patterns = [
        r'\+\d{1,3}\s?\d{3}\s?\d{3}\s?\d{3,4}',  # +421 903 123 456
        r'0\d{3}\s?\d{3}\s?\d{3}',                  # 0903 123 456
        r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',             # 123-456-7890
        r'\+\d{10,13}',                              # +421903123456
    ]
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False


def _contains_company_names(text: str) -> bool:
    """Detect company name patterns."""
    company_patterns = [
        r'\b\w+\s+(s\.r\.o\.|a\.s\.|s\.p\.|k\.s\.)\b',    # Slovak
        r'\b\w+\s+(s\.r\.o\.|a\.s\.|v\.o\.s\.)\b',         # Czech
        r'\b\w+\s+(Ltd\.?|Inc\.?|GmbH|LLC|Corp\.?|AG)\b',  # International
        r'\b\w+\s+(spol\.\s*s\s*r\.\s*o\.)\b',             # Slovak full form
    ]
    for pattern in company_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _contains_financial_data(text: str) -> bool:
    """Detect financial information."""
    patterns = [
        r'[\$€£]\s?\d+[\d\s,.]*',                          # $1,000 or €500
        r'\d+[\d\s,.]*\s?(EUR|USD|CZK|GBP|SKK)\b',        # 1000 EUR
        r'\b(revenue|salary|plat|mzda|tržby|zisk|profit|faktur|invoice)\b',
        r'\b(IBAN|BIC|SWIFT)\b',
        r'\b[A-Z]{2}\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{0,4}\b',  # IBAN
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _contains_addresses(text: str) -> bool:
    """Detect street addresses."""
    patterns = [
        r'\b\w+\s+(ulica|ul\.|námestie|nám\.|cesta|trieda)\s+\d+',  # Slovak
        r'\b\w+\s+(ulice|nám\.)\s+\d+',                              # Czech
        r'\b\d{3}\s?\d{2}\b',                                         # Slovak/Czech ZIP (e.g. 811 01)
        r'\bPSČ\s*:?\s*\d{3}\s?\d{2}\b',                             # PSČ: 811 01
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False
