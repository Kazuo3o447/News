"""
Unit-Tests für services/rule_classifier.py
"""
import pytest
from services.rule_classifier import apply_rules


# ---------------------------------------------------------------------------
# Hilfsfunktion
# ---------------------------------------------------------------------------

def _r(title: str, summary: str = "", source: str = "BleepingComputer") -> dict:
    return apply_rules(title, summary, source)


# ---------------------------------------------------------------------------
# forced_critical — CVE
# ---------------------------------------------------------------------------

class TestCveSignal:
    def test_cve_in_title(self):
        r = _r("Microsoft patches CVE-2024-21413 — critical RCE in Outlook")
        assert r["forced_critical"] is True
        assert "cve" in r["signals"]

    def test_cve_in_summary(self):
        r = _r("Patch released", "Fixes CVE-2023-36884 in Windows HTML platform")
        assert r["forced_critical"] is True
        assert "cve" in r["signals"]

    def test_cve_case_insensitive(self):
        r = _r("cve-2025-12345 exploited in the wild")
        assert r["forced_critical"] is True

    def test_no_cve_no_signal(self):
        r = _r("Windows 11 24H2 feature update ships new widgets")
        assert "cve" not in r["signals"]


# ---------------------------------------------------------------------------
# forced_critical — CVSS
# ---------------------------------------------------------------------------

class TestCvssSignal:
    def test_cvss_critical(self):
        r = _r("CVSS 9.8 vulnerability in Apache Log4j")
        assert r["forced_critical"] is True
        assert "cvss_critical" in r["signals"]

    def test_cvss_v3_notation(self):
        r = _r("Severity: CVSS:v3 10.0 — network-exposed RCE")
        assert "cvss_critical" in r["signals"]

    def test_cvss_below_threshold(self):
        r = _r("CVSS 7.5 medium severity issue patched")
        assert "cvss_critical" not in r["signals"]

    def test_cvss_exactly_9(self):
        r = _r("CVSS 9.0 flaw in Cisco IOS")
        assert "cvss_critical" in r["signals"]


# ---------------------------------------------------------------------------
# forced_critical — Active Exploit
# ---------------------------------------------------------------------------

class TestActiveExploitSignal:
    def test_zero_day(self):
        r = _r("Zero-day in Chrome exploited by nation-state actors")
        assert r["forced_critical"] is True
        assert "active_exploit" in r["signals"]

    def test_in_the_wild(self):
        r = _r("Vulnerability actively exploited in the wild")
        assert "active_exploit" in r["signals"]

    def test_rapid_security_response(self):
        r = _r("Apple issues Rapid Security Response for iOS 17.4.1")
        assert "active_exploit" in r["signals"]

    def test_emergency_update(self):
        r = _r("Microsoft releases emergency update for Exchange Server")
        assert "active_exploit" in r["signals"]

    def test_notfall_patch_german(self):
        r = _r("BSI veröffentlicht Notfall-Patch für kritische Lücke")
        assert "active_exploit" in r["signals"]


# ---------------------------------------------------------------------------
# forced_critical — Android Security Bulletin
# ---------------------------------------------------------------------------

class TestAndroidBulletinSignal:
    def test_android_bulletin_critical(self):
        r = _r("Android Security Bulletin — June 2025 includes Critical RCE")
        assert r["forced_critical"] is True
        assert "android_critical" in r["signals"]

    def test_android_bulletin_no_critical(self):
        r = _r("Android Security Bulletin — minor fixes for June 2025")
        assert "android_critical" not in r["signals"]


# ---------------------------------------------------------------------------
# forced_critical — Samsung SMR
# ---------------------------------------------------------------------------

class TestSamsungSMRSignal:
    def test_smr_critical(self):
        r = _r("Samsung SMR June 2025 patch includes critical kernel fix")
        assert "samsung_critical" in r["signals"]

    def test_smr_without_critical(self):
        r = _r("Samsung SMR June 2025 released")
        assert "samsung_critical" not in r["signals"]


# ---------------------------------------------------------------------------
# forced_critical — Advisory Sources
# ---------------------------------------------------------------------------

class TestAdvisorySourceSignal:
    def test_msrc_source(self):
        r = _r("Update guide for May 2025", source="MSRC")
        assert r["forced_critical"] is True
        assert "advisory_source" in r["signals"]

    def test_bsi_source(self):
        r = _r("Kritische Sicherheitswarnung", source="BSI Warnungen")
        assert r["forced_critical"] is True
        assert "advisory_source" in r["signals"]

    def test_cisa_source(self):
        r = _r("Known Exploited Vulnerabilities catalog updated", source="CISA Advisories")
        assert r["forced_critical"] is True
        assert "advisory_source" in r["signals"]

    def test_non_advisory_source_not_forced(self):
        r = _r("New Azure features announced", source="Azure Blog")
        assert "advisory_source" not in r["signals"]
        assert r["forced_critical"] is False


# ---------------------------------------------------------------------------
# platform_hint — Source → Platform mapping
# ---------------------------------------------------------------------------

class TestPlatformHint:
    def test_windows_sources(self):
        for source in ("MSRC", "Azure Blog", "Windows Blog", "Microsoft Security Blog",
                       "Microsoft Tech Community", "Microsoft 365 Blog", "M365 Message Center"):
            r = apply_rules("test", "", source)
            assert r["platform_hint"] == "windows", f"Expected windows for {source}"

    def test_apple_sources(self):
        for source in ("Jamf Blog", "Apple Developer Releases", "Intego Mac Security",
                       "Mr. Macintosh", "Eclectic Light"):
            r = apply_rules("test", "", source)
            assert r["platform_hint"] == "apple", f"Expected apple for {source}"

    def test_android_sources(self):
        for source in ("Android Developers", "NowSecure", "Android Security Bulletin",
                       "Samsung SMR"):
            r = apply_rules("test", "", source)
            assert r["platform_hint"] == "android", f"Expected android for {source}"

    def test_cross_sources(self):
        for source in ("BleepingComputer", "Krebs on Security", "The Hacker News",
                       "Heise Security", "BSI Warnungen", "CISA Advisories",
                       "Heise Developer", "iX", "Google Workspace Updates"):
            r = apply_rules("test", "", source)
            assert r["platform_hint"] == "cross", f"Expected cross for {source}"

    def test_unknown_source_returns_none(self):
        r = apply_rules("test", "", "Unbekannter Blog")
        assert r["platform_hint"] is None


# ---------------------------------------------------------------------------
# No false positives for normal content
# ---------------------------------------------------------------------------

class TestNoFalsePositives:
    def test_normal_product_announcement(self):
        r = _r("Microsoft announces new Teams features for 2025", source="Microsoft Tech Community")
        assert r["forced_critical"] is False
        assert r["signals"] == []

    def test_iphone_review_no_forced_critical(self):
        r = _r("iPhone 17 Pro review: best camera yet", source="BleepingComputer")
        assert r["forced_critical"] is False

    def test_multiple_signals_collected(self):
        r = _r(
            "CVE-2024-1234 actively exploited — CVSS 9.8",
            source="MSRC",
        )
        assert r["forced_critical"] is True
        assert len(r["signals"]) >= 3   # cve + cvss_critical + active_exploit + advisory_source
