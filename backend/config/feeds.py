"""
RSS Feed-Konfiguration — Cross-Platform: Windows + Apple + Android + plattformübergreifende Security/IT.
Jeder Eintrag: { "name": str, "url": str, "priority": "high"|"medium"|"low",
                 "platform": "windows"|"apple"|"android"|"cross" }
"""

FEEDS: list[dict] = [
    # --- Microsoft / Windows (platform=windows) ---
    {"name": "M365 Message Center",     "url": "https://mc.merill.net/rss.xml",                                     "priority": "high",   "platform": "windows"},
    {"name": "Azure Blog",              "url": "https://azure.microsoft.com/en-us/blog/feed/",                      "priority": "high",   "platform": "windows"},
    {"name": "Microsoft Security Blog", "url": "https://www.microsoft.com/en-us/security/blog/feed/",               "priority": "high",   "platform": "windows"},
    {"name": "Microsoft Tech Community","url": "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=AzureNewsCategory", "priority": "high",   "platform": "windows"},
    {"name": "Windows Blog",            "url": "https://blogs.windows.com/feed/",                                   "priority": "medium", "platform": "windows"},
    {"name": "Microsoft 365 Blog",      "url": "https://www.microsoft.com/en-us/microsoft-365/blog/feed/",          "priority": "medium", "platform": "windows"},
    {"name": "MSRC",                    "url": "https://msrc.microsoft.com/blog/feed/",                             "priority": "high",   "platform": "windows"},

    # --- Cross-Platform Security & IT (platform=cross) ---
    {"name": "BleepingComputer",        "url": "https://www.bleepingcomputer.com/feed/",                            "priority": "high",   "platform": "cross"},
    {"name": "Krebs on Security",       "url": "https://krebsonsecurity.com/feed/",                                 "priority": "high",   "platform": "cross"},
    {"name": "The Hacker News",         "url": "https://feeds.feedburner.com/TheHackersNews",                       "priority": "high",   "platform": "cross"},
    {"name": "Heise Security",          "url": "https://www.heise.de/security/rss/news-atom.xml",                   "priority": "high",   "platform": "cross"},
    {"name": "BSI Warnungen",           "url": "https://wid.cert-bund.de/content/public/securityAdvisory/rss",      "priority": "high",   "platform": "cross"},
    {"name": "CISA Advisories",         "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml",             "priority": "high",   "platform": "cross"},
    {"name": "Heise Developer",         "url": "https://www.heise.de/developer/rss/news-atom.xml",                  "priority": "medium", "platform": "cross"},
    {"name": "iX",                      "url": "https://www.heise.de/ix/news.rdf",                                  "priority": "medium", "platform": "cross"},

    # --- Apple / macOS / iOS (platform=apple) ---
    {"name": "Jamf Blog",               "url": "https://www.jamf.com/blog/rss",                                     "priority": "high",   "platform": "apple"},
    {"name": "Apple Developer Releases","url": "https://developer.apple.com/news/releases/rss/releases.rss",        "priority": "medium", "platform": "apple"},
    {"name": "Intego Mac Security",     "url": "https://www.intego.com/mac-security-blog/feed/",                    "priority": "medium", "platform": "apple"},
    {"name": "Mr. Macintosh",           "url": "https://mrmacintosh.com/feed/",                                     "priority": "medium", "platform": "apple"},
    {"name": "Eclectic Light",          "url": "https://eclecticlight.co/feed/",                                    "priority": "low",    "platform": "apple"},

    # --- Android / Mobile-MDM ---
    # TODO: Offizielle Android Security Bulletins + Samsung SMR haben kein RSS -> siehe android_scraper.py (T9)
    {"name": "Android Developers",      "url": "https://android-developers.googleblog.com/feeds/posts/default",     "priority": "medium", "platform": "android"},
    {"name": "Google Workspace Updates","url": "https://workspaceupdates.googleblog.com/feeds/posts/default",       "priority": "medium", "platform": "cross"},
    {"name": "NowSecure",               "url": "https://www.nowsecure.com/feed/",                                   "priority": "low",    "platform": "android"},
]
