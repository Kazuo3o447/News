"""
RSS Feed-Konfiguration — kuratiert auf Microsoft + Security + Enterprise-IT.
Generalisten und Consumer-Tech-Feeds wurden bewusst entfernt.
Jeder Eintrag: { "name": str, "url": str, "priority": "high"|"medium"|"low" }
"""

FEEDS: list[dict] = [
    # --- Microsoft (offizielle Blogs + Message Center) ---
    {"name": "M365 Message Center",     "url": "https://mc.merill.net/rss.xml",                                     "priority": "high"},
    {"name": "Azure Blog",              "url": "https://azure.microsoft.com/en-us/blog/feed/",                      "priority": "high"},
    {"name": "Microsoft Security Blog", "url": "https://www.microsoft.com/en-us/security/blog/feed/",               "priority": "high"},
    {"name": "Microsoft Tech Community","url": "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=AzureNewsCategory", "priority": "high"},
    {"name": "Windows Blog",            "url": "https://blogs.windows.com/feed/",                                   "priority": "medium"},
    {"name": "Microsoft 365 Blog",      "url": "https://www.microsoft.com/en-us/microsoft-365/blog/feed/",          "priority": "medium"},
    {"name": "MSRC",                    "url": "https://msrc.microsoft.com/blog/feed/",                             "priority": "high"},

    # --- Security (spezialisiert) ---
    {"name": "BleepingComputer",        "url": "https://www.bleepingcomputer.com/feed/",                            "priority": "high"},
    {"name": "Krebs on Security",       "url": "https://krebsonsecurity.com/feed/",                                 "priority": "high"},
    {"name": "The Hacker News",         "url": "https://feeds.feedburner.com/TheHackersNews",                       "priority": "high"},
    {"name": "Heise Security",          "url": "https://www.heise.de/security/rss/news-atom.xml",                   "priority": "high"},
    {"name": "BSI Warnungen",           "url": "https://wid.cert-bund.de/content/public/securityAdvisory/rss",      "priority": "high"},
    {"name": "CISA Advisories",         "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml",             "priority": "high"},

    # --- IT-Infra / Enterprise (gezielte Subfeeds, keine Generalisten) ---
    {"name": "Heise Developer",         "url": "https://www.heise.de/developer/rss/news-atom.xml",                  "priority": "medium"},
    {"name": "iX",                      "url": "https://www.heise.de/ix/news.rdf",                                  "priority": "medium"},
]
