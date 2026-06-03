"""
Server-seitige Topic-Erkennung anhand Keywords in Titel + Summary.
Spiegelt frontend/src/utils/topics.js — Single source of truth liegt hier.
"""
from __future__ import annotations

TOPICS: list[dict] = [
    {"key": "security",  "label": "Security",          "keywords": [
        "security", "sicherheits", "cve-", "cve ", "vulnerab", "exploit", "patch tuesday",
        "malware", "ransomware", "phishing", "breach", "datenleck", "leak", "angriff",
        "hack", "zero-day", "zero day", "cyber", "krebs", "bsi ", "cisa", "0-day",
        "trojaner", "backdoor", "rootkit", "spyware", "ddos", "exfiltrat",
    ]},
    {"key": "microsoft", "label": "Microsoft / Azure", "keywords": [
        "microsoft", "azure", "windows ", "windows10", "windows11", "office 365",
        "microsoft 365", "m365", "teams ", "sharepoint", "outlook", "exchange",
        "entra", "active directory", " ad ", "intune", "defender", "sentinel",
        "copilot", "edge ", "surface ", "visual studio", "dotnet", ".net",
        "powershell", "hyper-v", "sql server", "msrc",
    ]},
    {"key": "ai",        "label": "AI / KI",           "keywords": [
        " ai ", " ai,", " ai.", "a.i.", "künstliche intelligenz", "kuenstliche intelligenz",
        " ki ", " ki,", " ki.", "chatgpt", "gpt-", "gpt ", "llm", "gemini", "claude",
        "anthropic", "openai", "mistral", "deepseek", "copilot", "machine learning",
        "neural", "sprachmodell", "agentic", "rag ",
    ]},
    {"key": "cloud",     "label": "Cloud / DevOps",    "keywords": [
        "cloud", "aws ", "amazon web services", "gcp", "google cloud", "kubernetes",
        "docker", "container", "serverless", "devops", "ci/cd", "terraform", "iac",
        "ansible", "helm", "openshift",
    ]},
    {"key": "dev",       "label": "Entwicklung",       "keywords": [
        "javascript", "typescript", "python", "java ", "rust", "golang", " go ",
        "react", "vue", "angular", "node.js", "npm ", "framework", "api ", "rest",
        "graphql", "git ", "github", "gitlab", "vscode", "visual studio code",
        "open source", "open-source",
    ]},
    {"key": "hardware",  "label": "Hardware / Chips",  "keywords": [
        "cpu", "gpu", "chip", "prozessor", "intel", "amd ", " arm ", "nvidia", "rtx",
        "ryzen", "core ultra", "snapdragon", "apple silicon", "mainboard", "ssd",
        "arbeitsspeicher", "ram ", "ddr5",
    ]},
    {"key": "mobile",    "label": "Mobile",            "keywords": [
        "iphone", "ipad", "ios ", "android", "samsung", "google pixel", "smartphone",
        "tablet", "5g ", "6g ",
    ]},
]

_TOPIC_LOOKUP = {t["key"]: t for t in TOPICS}


def detect_topics(title: str, summary: str = "") -> list[str]:
    """Erkennt Topics aus Titel + Summary. Mehrfachzuordnung möglich."""
    text  = f" {(title or '').lower()} {(summary or '').lower()} "
    found = []
    for topic in TOPICS:
        if any(kw in text for kw in topic["keywords"]):
            found.append(topic["key"])
    return found


def topic_label(key: str) -> str:
    return _TOPIC_LOOKUP.get(key, {}).get("label", key)
