"""
B2 — User-Identität ohne Login-Bau.

Reihenfolge:
  1. X-MS-CLIENT-PRINCIPAL-NAME  (Azure App Service Easy Auth / Entra)
  2. X-User                      (Dev-Header)
  3. "anonymous"                 (Fallback)

E-Mail-Adressen werden auf den lokalen Teil (vor @) gekürzt.
"""
from __future__ import annotations

from fastapi import Request


def _trim(name: str) -> str:
    """max.muster@gema.de -> max.muster; reiner Username bleibt unverändert."""
    if "@" in name:
        return name.split("@")[0]
    return name


def current_user(request: Request) -> str:
    """Gibt den normalisierten Usernamen aus den Request-Headers zurück."""
    for header in ("x-ms-client-principal-name", "x-user"):
        val = request.headers.get(header, "").strip()
        if val:
            return _trim(val)
    return "anonymous"
