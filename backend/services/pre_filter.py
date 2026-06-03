"""
Pre-Filter vor der Groq-Klassifizierung.

Ziel: Off-Topic-Artikel früh aussortieren, damit:
1. die Nutzer nur relevantes IT-Material sehen (Fokus: Windows + Apple + Android + Security)
2. das Groq-Kontingent nicht mit Schrott verbraucht wird.

Logik:
- Harte Phrasen-Denylist (E-Auto, Gaming-Konsolen-Deals, Lifestyle …) → OFF_TOPIC
- Keine erkannten Topics UND keine Allowlist-Keyword-Treffer    → OFF_TOPIC
- Sonst → an Groq weitergeben.
"""
from __future__ import annotations

from services.topics import detect_topics

# Keywords, die einen Artikel als „IT-relevant" qualifizieren —
# wenn mindestens eines getroffen wird, wird der Artikel zur Klassifizierung
# durchgereicht (auch wenn kein Topic erkannt wurde).
ALLOWLIST_KEYWORDS: tuple[str, ...] = (
    # Microsoft-Ökosystem
    "microsoft", "azure", "windows", "office 365", "microsoft 365", "m365",
    "teams", "sharepoint", "outlook", "exchange online", "entra", "intune",
    "defender", "sentinel", "copilot", "active directory", "msrc",
    "powershell", "hyper-v", "sql server", "sysmon",
    # M365 Message Center / Roadmap IDs (mc.merill.net)
    "mc1", "mc2", "mc3", "mc4", "mc5", "mc6", "mc7", "mc8", "mc9",
    "rm1", "rm2", "rm3", "rm4", "rm5", "rm6", "rm7", "rm8", "rm9",
    # Security generisch
    "security", "sicherheits", "cve-", "vulnerab", "exploit", "patch",
    "malware", "ransomware", "phishing", "breach", "datenleck", "leak",
    "hack", "zero-day", "0-day", "cyber", "bsi", "cisa", "ddos",
    "trojaner", "backdoor", "rootkit", "spyware", "exfiltrat",
    # IT-Infra / Enterprise
    "kubernetes", "docker", "container", "vmware", "linux", "openshift",
    "kerberos", "ldap", "saml", "oauth", "zero trust", "iam", "siem",
    "soc ", "incident response", "edr", "xdr",
    # Purview / Compliance (häufig in MC-Einträgen)
    "purview", "dlp", "compliance", "ediscovery", "retention",
    # Apple / macOS / iOS — Admin-relevante Begriffe
    "macos", "ios ", "ipados", "jamf", "mdm", "apple business manager",
    "abm ", "xprotect", "gatekeeper", "rapid security response", "filevault",
    "munki", "vpp", "dep ", "automated device enrollment", "platform sso",
    # Android Enterprise / Mobile-MDM
    "android enterprise", "samsung knox", "knox", " smr ", "play protect",
    "work profile", "zero-touch", "managed google play", "android management api",
)

# Phrasen, die Artikel sicher als off-topic kennzeichnen — selbst wenn
# zufällig ein Allowlist-Wort vorkommt (z. B. „Windows zur PS5-Konsole").
# WICHTIG: Keine pauschalen Apple/Android-Blocker hier — Reviews/Leaks
# werden vom LLM als DUMP klassifiziert, nicht schon hier geblockt.
DENYLIST_PHRASES: tuple[str, ...] = (
    "e-auto", "elektroauto", " ev ", "tesla ", "byd ", "vw ", "volkswagen",
    "bmw ", "mercedes", "porsche", "rivian", "traktor", "lkw ",
    "fahrassistenz", "ladesäule", "lade-säule",
    "ps5", "ps4", "playstation", "nintendo", "switch 2", "xbox series",
    "steam deck",
    "anzeige:", "sponsored", "deal:", "deals:", "rabatt", "gewinnspiel",
    "schnäppchen", "prime day", "black friday", "cyber monday",
    "kryptowährung", "krypto-", "bitcoin-kurs", "ethereum-kurs", "nft ",
    "stellenanzeige", "stellenmarkt",
    "horoskop", "lifestyle", "fitness", "kochrezept",
)


def pre_filter(title: str, summary: str = "") -> dict:
    """
    Liefert ein dict:
        {
            "topics":        [...],   # erkannte Topic-Keys
            "off_topic":     bool,    # True = Groq überspringen
            "reason":        str,     # menschenlesbar
            "platform_hint": None,    # wird in der Regelschicht (rule_classifier) aus
                                      # der Feed-Source abgeleitet, nicht hier
        }
    """
    text = f" {(title or '').lower()} {(summary or '').lower()} "

    # 1) Denylist greift hart
    for phrase in DENYLIST_PHRASES:
        if phrase in text:
            return {
                "topics":        detect_topics(title, summary),
                "off_topic":     True,
                "reason":        f"Pre-Filter: Denylist-Treffer '{phrase.strip()}'",
                "platform_hint": None,
            }

    topics = detect_topics(title, summary)
    if topics:
        return {"topics": topics, "off_topic": False, "reason": "", "platform_hint": None}

    # Kein Topic — fällt zurück auf Allowlist
    if any(kw in text for kw in ALLOWLIST_KEYWORDS):
        return {"topics": [], "off_topic": False, "reason": "", "platform_hint": None}

    return {
        "topics":        [],
        "off_topic":     True,
        "reason":        "Pre-Filter: kein IT-Topic & kein Allowlist-Keyword",
        "platform_hint": None,
    }

# Keywords, die einen Artikel als „IT-relevant" qualifizieren —
# wenn mindestens eines getroffen wird, wird der Artikel zur Klassifizierung
# durchgereicht (auch wenn kein Topic erkannt wurde).
ALLOWLIST_KEYWORDS: tuple[str, ...] = (
    # Microsoft-Ökosystem
    "microsoft", "azure", "windows", "office 365", "microsoft 365", "m365",
    "teams", "sharepoint", "outlook", "exchange online", "entra", "intune",
    "defender", "sentinel", "copilot", "active directory", "msrc",
    "powershell", "hyper-v", "sql server", "sysmon",
    # M365 Message Center / Roadmap IDs (mc.merill.net)
    "mc1", "mc2", "mc3", "mc4", "mc5", "mc6", "mc7", "mc8", "mc9",
    "rm1", "rm2", "rm3", "rm4", "rm5", "rm6", "rm7", "rm8", "rm9",
    # Security generisch
    "security", "sicherheits", "cve-", "vulnerab", "exploit", "patch",
    "malware", "ransomware", "phishing", "breach", "datenleck", "leak",
    "hack", "zero-day", "0-day", "cyber", "bsi", "cisa", "ddos",
    "trojaner", "backdoor", "rootkit", "spyware", "exfiltrat",
    # IT-Infra / Enterprise
    "kubernetes", "docker", "container", "vmware", "linux", "openshift",
    "kerberos", "ldap", "saml", "oauth", "zero trust", "iam", "siem",
    "soc ", "incident response", "edr", "xdr",
    # Purview / Compliance (häufig in MC-Einträgen)
    "purview", "dlp", "compliance", "ediscovery", "retention",
)

# Phrasen, die Artikel sicher als off-topic kennzeichnen — selbst wenn
# zufällig ein Allowlist-Wort vorkommt (z. B. „Windows zur PS5-Konsole").
DENYLIST_PHRASES: tuple[str, ...] = (
    "e-auto", "elektroauto", " ev ", "tesla ", "byd ", "vw ", "volkswagen",
    "bmw ", "mercedes", "porsche", "rivian", "traktor", "lkw ",
    "autopilot", "fahrassistenz", "ladesäule", "lade-säule",
    "ps5", "ps4", "playstation", "nintendo", "switch 2", "xbox series",
    "steam deck",
    "anzeige:", "sponsored", "deal:", "deals:", "rabatt", "gewinnspiel",
    "schnäppchen", "prime day", "black friday", "cyber monday",
    "kryptowährung", "krypto-", "bitcoin-kurs", "ethereum-kurs", "nft ",
    "stellenanzeige", "stellenmarkt",
    "horoskop", "lifestyle", "fitness", "kochrezept",
)


def pre_filter(title: str, summary: str = "") -> dict:
    """
    Liefert ein dict:
        {
            "topics":   [...],           # erkannte Topic-Keys
            "off_topic": bool,           # True = Groq überspringen
            "reason":    str             # menschenlesbar
        }
    """
    text = f" {(title or '').lower()} {(summary or '').lower()} "

    # 1) Denylist greift hart
    for phrase in DENYLIST_PHRASES:
        if phrase in text:
            return {
                "topics":   detect_topics(title, summary),
                "off_topic": True,
                "reason":    f"Pre-Filter: Denylist-Treffer '{phrase.strip()}'",
            }

    topics = detect_topics(title, summary)
    if topics:
        return {"topics": topics, "off_topic": False, "reason": ""}

    # Kein Topic — fällt zurück auf Allowlist
    if any(kw in text for kw in ALLOWLIST_KEYWORDS):
        return {"topics": [], "off_topic": False, "reason": ""}

    return {
        "topics":   [],
        "off_topic": True,
        "reason":    "Pre-Filter: kein IT-Topic & kein Allowlist-Keyword",
    }
