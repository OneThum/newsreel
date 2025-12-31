"""
Curated list of verified working RSS feeds
These have been tested and confirmed accessible
Updated Dec 2025: Added global diversity - US, AU, Asia, Middle East, Europe
"""
from typing import List
from .models import RSSFeedConfig


def get_verified_working_feeds() -> List[RSSFeedConfig]:
    """
    Return verified working feeds with GLOBAL diversity
    Includes US, Australian, Asian, Middle Eastern, and European sources
    """
    return [
        # ========================================
        # WIRE SERVICES (Tier 1 - Most reliable)
        # ========================================
        RSSFeedConfig(
            id="reuters_world",
            name="Reuters World News",
            url="https://feeds.reuters.com/reuters/worldNews",
            source_id="reuters",
            category="world",
            tier=1,
            language="en",
            country="global"
        ),
        RSSFeedConfig(
            id="ap_world",
            name="Associated Press World",
            url="https://rsshub.app/apnews/topics/apf-topnews",
            source_id="ap",
            category="world",
            tier=1,
            language="en",
            country="global"
        ),
        
        # ========================================
        # US NEWS (15 feeds)
        # ========================================
        RSSFeedConfig(
            id="nyt",
            name="New York Times HomePage",
            url="https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
            source_id="nyt",
            category="us",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="cnn",
            name="CNN Top Stories",
            url="http://rss.cnn.com/rss/cnn_topstories.rss",
            source_id="cnn",
            category="us",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="washpost",
            name="Washington Post National",
            url="https://feeds.washingtonpost.com/rss/national",
            source_id="washingtonpost",
            category="us",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="npr",
            name="NPR News",
            url="https://feeds.npr.org/1001/rss.xml",
            source_id="npr",
            category="us",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="cbs",
            name="CBS News",
            url="https://www.cbsnews.com/latest/rss/main",
            source_id="cbs",
            category="us",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="nbc",
            name="NBC News Top Stories",
            url="https://feeds.nbcnews.com/nbcnews/public/news",
            source_id="nbc",
            category="us",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="abc_us",
            name="ABC News Top Stories",
            url="https://abcnews.go.com/abcnews/topstories",
            source_id="abc_us",
            category="us",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="fox",
            name="Fox News Latest",
            url="https://moxie.foxnews.com/google-publisher/latest.xml",
            source_id="fox",
            category="us",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="politico",
            name="Politico",
            url="https://www.politico.com/rss/politics08.xml",
            source_id="politico",
            category="us",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="latimes",
            name="Los Angeles Times",
            url="https://www.latimes.com/rss2.0.xml",
            source_id="latimes",
            category="us",
            tier=2,
            language="en",
            country="US"
        ),
        
        # ========================================
        # UK NEWS
        # ========================================
        RSSFeedConfig(
            id="bbc_world",
            name="BBC World News",
            url="http://feeds.bbci.co.uk/news/world/rss.xml",
            source_id="bbc",
            category="world",
            tier=1,
            language="en",
            country="UK"
        ),
        RSSFeedConfig(
            id="guardian_world",
            name="The Guardian World",
            url="https://www.theguardian.com/world/rss",
            source_id="guardian",
            category="world",
            tier=2,
            language="en",
            country="UK"
        ),
        RSSFeedConfig(
            id="telegraph",
            name="The Telegraph",
            url="https://www.telegraph.co.uk/rss.xml",
            source_id="telegraph",
            category="europe",
            tier=2,
            language="en",
            country="UK"
        ),
        RSSFeedConfig(
            id="independent",
            name="The Independent",
            url="https://www.independent.co.uk/rss",
            source_id="independent",
            category="europe",
            tier=2,
            language="en",
            country="UK"
        ),
        
        # ========================================
        # AUSTRALIAN & NEW ZEALAND NEWS
        # ========================================
        RSSFeedConfig(
            id="abc_au",
            name="ABC News Australia",
            url="https://www.abc.net.au/news/feed/51120/rss.xml",
            source_id="abc_au",
            category="australia",
            tier=2,
            language="en",
            country="AU"
        ),
        RSSFeedConfig(
            id="smh",
            name="Sydney Morning Herald",
            url="https://www.smh.com.au/rss/feed.xml",
            source_id="smh",
            category="australia",
            tier=2,
            language="en",
            country="AU"
        ),
        RSSFeedConfig(
            id="theage",
            name="The Age",
            url="https://www.theage.com.au/rss/feed.xml",
            source_id="theage",
            category="australia",
            tier=2,
            language="en",
            country="AU"
        ),
        RSSFeedConfig(
            id="newscomau",
            name="News.com.au",
            url="https://www.news.com.au/content-feeds/latest-news-national/",
            source_id="newscomau",
            category="australia",
            tier=2,
            language="en",
            country="AU"
        ),
        RSSFeedConfig(
            id="nzherald",
            name="New Zealand Herald",
            url="https://www.nzherald.co.nz/arc/outboundfeeds/rss/",
            source_id="nzherald",
            category="australia",
            tier=2,
            language="en",
            country="NZ"
        ),
        
        # ========================================
        # ASIAN NEWS
        # ========================================
        RSSFeedConfig(
            id="japantimes",
            name="Japan Times",
            url="https://www.japantimes.co.jp/feed/",
            source_id="japantimes",
            category="world",
            tier=2,
            language="en",
            country="JP"
        ),
        RSSFeedConfig(
            id="scmp",
            name="South China Morning Post",
            url="https://www.scmp.com/rss/91/feed",
            source_id="scmp",
            category="world",
            tier=2,
            language="en",
            country="HK"
        ),
        RSSFeedConfig(
            id="straitstimes",
            name="Straits Times Singapore",
            url="https://www.straitstimes.com/news/rss.xml",
            source_id="straitstimes",
            category="world",
            tier=2,
            language="en",
            country="SG"
        ),
        RSSFeedConfig(
            id="cgtn",
            name="CGTN China",
            url="https://www.cgtn.com/subscribe/rss/section/world.xml",
            source_id="cgtn",
            category="world",
            tier=2,
            language="en",
            country="CN"
        ),
        RSSFeedConfig(
            id="bangkokpost",
            name="Bangkok Post",
            url="https://www.bangkokpost.com/rss/data/news.xml",
            source_id="bangkokpost",
            category="world",
            tier=2,
            language="en",
            country="TH"
        ),
        RSSFeedConfig(
            id="jakartapost",
            name="Jakarta Post",
            url="https://www.thejakartapost.com/rss",
            source_id="jakartapost",
            category="world",
            tier=2,
            language="en",
            country="ID"
        ),
        
        # ========================================
        # MIDDLE EAST NEWS
        # ========================================
        RSSFeedConfig(
            id="aljazeera",
            name="Al Jazeera English",
            url="https://www.aljazeera.com/xml/rss/all.xml",
            source_id="aljazeera",
            category="world",
            tier=2,
            language="en",
            country="QA"
        ),
        RSSFeedConfig(
            id="timesofisrael",
            name="Times of Israel",
            url="https://www.timesofisrael.com/feed/",
            source_id="timesofisrael",
            category="world",
            tier=2,
            language="en",
            country="IL"
        ),
        RSSFeedConfig(
            id="middleeasteye",
            name="Middle East Eye",
            url="https://www.middleeasteye.net/rss",
            source_id="middleeasteye",
            category="world",
            tier=2,
            language="en",
            country="UK"
        ),
        
        # ========================================
        # EUROPEAN NEWS
        # ========================================
        RSSFeedConfig(
            id="france24",
            name="France 24 World",
            url="https://www.france24.com/en/rss",
            source_id="france24",
            category="world",
            tier=2,
            language="en",
            country="FR"
        ),
        RSSFeedConfig(
            id="dw",
            name="Deutsche Welle Top Stories",
            url="https://rss.dw.com/xml/rss-en-all",
            source_id="dw",
            category="world",
            tier=2,
            language="en",
            country="DE"
        ),
        RSSFeedConfig(
            id="euronews",
            name="Euronews World",
            url="https://www.euronews.com/rss",
            source_id="euronews",
            category="world",
            tier=2,
            language="en",
            country="EU"
        ),
        RSSFeedConfig(
            id="lemonde",
            name="Le Monde English",
            url="https://www.lemonde.fr/en/rss/une.xml",
            source_id="lemonde",
            category="europe",
            tier=2,
            language="en",
            country="FR"
        ),
        RSSFeedConfig(
            id="spiegel",
            name="Der Spiegel International",
            url="https://www.spiegel.de/international/index.rss",
            source_id="spiegel",
            category="europe",
            tier=2,
            language="en",
            country="DE"
        ),
        RSSFeedConfig(
            id="ansa",
            name="ANSA English",
            url="https://www.ansa.it/english/news/general_news.xml",
            source_id="ansa",
            category="europe",
            tier=2,
            language="en",
            country="IT"
        ),
        RSSFeedConfig(
            id="elpais",
            name="El País English",
            url="https://elpais.com/rss/elpais/inenglish.xml",
            source_id="elpais",
            category="europe",
            tier=2,
            language="en",
            country="ES"
        ),
        RSSFeedConfig(
            id="irishtimes",
            name="Irish Times",
            url="https://www.irishtimes.com/cmlink/news-1.1319192",
            source_id="irishtimes",
            category="europe",
            tier=2,
            language="en",
            country="IE"
        ),
        RSSFeedConfig(
            id="dutchnews",
            name="DutchNews.nl",
            url="https://www.dutchnews.nl/feed/",
            source_id="dutchnews",
            category="europe",
            tier=2,
            language="en",
            country="NL"
        ),
        RSSFeedConfig(
            id="swissinfo",
            name="SWI swissinfo.ch",
            url="https://www.swissinfo.ch/eng/rss",
            source_id="swissinfo",
            category="europe",
            tier=2,
            language="en",
            country="CH"
        ),
        
        # ========================================
        # CANADIAN NEWS (NEW!)
        # ========================================
        RSSFeedConfig(
            id="cbc",
            name="CBC News Canada",
            url="https://www.cbc.ca/webfeed/rss/rss-topstories",
            source_id="cbc",
            category="world",
            tier=2,
            language="en",
            country="CA"
        ),
        RSSFeedConfig(
            id="globeandmail",
            name="Globe and Mail",
            url="https://www.theglobeandmail.com/rss/",
            source_id="globeandmail",
            category="world",
            tier=2,
            language="en",
            country="CA"
        ),
        
        # ========================================
        # TECHNOLOGY (International mix)
        # ========================================
        RSSFeedConfig(
            id="techcrunch",
            name="TechCrunch",
            url="https://techcrunch.com/feed/",
            source_id="techcrunch",
            category="tech",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="theverge",
            name="The Verge",
            url="https://www.theverge.com/rss/index.xml",
            source_id="theverge",
            category="tech",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="arstechnica",
            name="Ars Technica",
            url="https://feeds.arstechnica.com/arstechnica/index",
            source_id="arstechnica",
            category="tech",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="wired",
            name="Wired",
            url="https://www.wired.com/feed/rss",
            source_id="wired",
            category="tech",
            tier=2,
            language="en",
            country="US"
        ),
        
        # ========================================
        # BUSINESS
        # ========================================
        RSSFeedConfig(
            id="bloomberg",
            name="Bloomberg",
            url="https://feeds.bloomberg.com/markets/news.rss",
            source_id="bloomberg",
            category="business",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="cnbc",
            name="CNBC",
            url="https://www.cnbc.com/id/100003114/device/rss/rss.html",
            source_id="cnbc",
            category="business",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="ft",
            name="Financial Times",
            url="https://www.ft.com/?format=rss",
            source_id="ft",
            category="business",
            tier=2,
            language="en",
            country="UK"
        ),
        
        # ========================================
        # SCIENCE
        # ========================================
        RSSFeedConfig(
            id="phys",
            name="Phys.org",
            url="https://phys.org/rss-feed/",
            source_id="phys",
            category="science",
            tier=2,
            language="en",
            country="global"
        ),
        RSSFeedConfig(
            id="nasa",
            name="NASA Breaking News",
            url="https://www.nasa.gov/rss/dyn/breaking_news.rss",
            source_id="nasa",
            category="science",
            tier=1,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="nature",
            name="Nature News",
            url="https://www.nature.com/nature.rss",
            source_id="nature",
            category="science",
            tier=2,
            language="en",
            country="UK"
        ),
        
        # ========================================
        # SPORTS
        # ========================================
        RSSFeedConfig(
            id="espn",
            name="ESPN",
            url="https://www.espn.com/espn/rss/news",
            source_id="espn",
            category="sports",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="bbc_sport",
            name="BBC Sport",
            url="http://feeds.bbci.co.uk/sport/rss.xml",
            source_id="bbc",
            category="sports",
            tier=2,
            language="en",
            country="UK"
        ),
    ]


def get_working_feeds_count() -> int:
    """Return count of verified working feeds"""
    return len(get_verified_working_feeds())
