"""RSS feed configuration - Complete 100 feed list"""
from typing import List
from .models import RSSFeedConfig


def get_all_feeds() -> List[RSSFeedConfig]:
    """Get complete list of 100 RSS feeds"""
    return [
        # ========================================
        # WORLD NEWS & INTERNATIONAL (15 feeds)
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
            id="bbc_world",
            name="BBC World News",
            url="http://feeds.bbci.co.uk/news/world/rss.xml",
            source_id="bbc",
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
        RSSFeedConfig(
            id="aljazeera",
            name="Al Jazeera English",
            url="https://www.aljazeera.com/xml/rss/all.xml",
            source_id="aljazeera",
            category="world",
            tier=2,
            language="en",
            country="global"
        ),
        RSSFeedConfig(
            id="guardian_world",
            name="The Guardian World",
            url="https://www.theguardian.com/world/rss",
            source_id="guardian",
            category="world",
            tier=2,
            language="en",
            country="global"
        ),
        RSSFeedConfig(
            id="reuters_top",
            name="Reuters Top News",
            url="https://feeds.reuters.com/reuters/topNews",
            source_id="reuters",
            category="world",
            tier=1,
            language="en",
            country="global"
        ),
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
            id="cgtn",
            name="CGTN",
            url="https://www.cgtn.com/subscribe/rss/section/world.xml",
            source_id="cgtn",
            category="world",
            tier=2,
            language="en",
            country="CN"
        ),
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
            id="middleeasteye",
            name="Middle East Eye",
            url="https://www.middleeasteye.net/rss",
            source_id="middleeasteye",
            category="world",
            tier=2,
            language="en",
            country="UK"
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
            id="jakartapost",
            name="Jakarta Post",
            url="https://www.thejakartapost.com/rss",
            source_id="jakartapost",
            category="world",
            tier=2,
            language="en",
            country="ID"
        ),
        RSSFeedConfig(
            id="reuters_africa",
            name="Reuters Africa",
            url="https://feeds.reuters.com/reuters/AFRICAWorldNews",
            source_id="reuters",
            category="world",
            tier=1,
            language="en",
            country="global"
        ),
        RSSFeedConfig(
            id="reuters_asia",
            name="Reuters Asia",
            url="https://feeds.reuters.com/reuters/AsiaWorldNews",
            source_id="reuters",
            category="world",
            tier=1,
            language="en",
            country="global"
        ),
        
        # ========================================
        # US NEWS (15 feeds)
        # ========================================
        
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
            id="usatoday",
            name="USA Today News",
            url="http://rssfeeds.usatoday.com/usatoday-NewsTopStories",
            source_id="usatoday",
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
            id="abc",
            name="ABC News Top Stories",
            url="https://abcnews.go.com/abcnews/topstories",
            source_id="abc",
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
            id="thehill",
            name="The Hill News",
            url="https://thehill.com/feed/",
            source_id="thehill",
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
        RSSFeedConfig(
            id="chicagotribune",
            name="Chicago Tribune",
            url="https://www.chicagotribune.com/arcio/rss/",
            source_id="chicagotribune",
            category="us",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="bostonglobe",
            name="Boston Globe",
            url="https://www.bostonglobe.com/rss/",
            source_id="bostonglobe",
            category="us",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="miamiherald",
            name="Miami Herald",
            url="https://www.miamiherald.com/news/?widgetName=rssfeed&widgetContentId=712015",
            source_id="miamiherald",
            category="us",
            tier=2,
            language="en",
            country="US"
        ),
        
        # ========================================
        # EUROPEAN NEWS (15 feeds)
        # ========================================
        
        RSSFeedConfig(
            id="bbc_uk",
            name="BBC UK News",
            url="http://feeds.bbci.co.uk/news/uk/rss.xml",
            source_id="bbc",
            category="europe",
            tier=2,
            language="en",
            country="UK"
        ),
        RSSFeedConfig(
            id="guardian_uk",
            name="The Guardian UK",
            url="https://www.theguardian.com/uk/rss",
            source_id="guardian",
            category="europe",
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
            id="thetimes",
            name="The Times UK",
            url="https://www.thetimes.co.uk/rss",
            source_id="thetimes",
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
        RSSFeedConfig(
            id="skynews",
            name="Sky News UK",
            url="https://feeds.skynews.com/feeds/rss/uk.xml",
            source_id="skynews",
            category="europe",
            tier=2,
            language="en",
            country="UK"
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
            id="thelocal_de",
            name="The Local Germany",
            url="https://www.thelocal.de/feed/",
            source_id="thelocal",
            category="europe",
            tier=2,
            language="en",
            country="DE"
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
            id="thelocal_se",
            name="The Local Sweden",
            url="https://www.thelocal.se/feed/",
            source_id="thelocal",
            category="europe",
            tier=2,
            language="en",
            country="SE"
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
            id="thelocal_es",
            name="The Local Spain",
            url="https://www.thelocal.es/feed/",
            source_id="thelocal",
            category="europe",
            tier=2,
            language="en",
            country="ES"
        ),
        RSSFeedConfig(
            id="thelocal_it",
            name="The Local Italy",
            url="https://www.thelocal.it/feed/",
            source_id="thelocal",
            category="europe",
            tier=2,
            language="en",
            country="IT"
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
            id="notesfrompoland",
            name="Notes from Poland",
            url="https://notesfrompoland.com/feed/",
            source_id="notesfrompoland",
            category="europe",
            tier=2,
            language="en",
            country="PL"
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
        RSSFeedConfig(
            id="politico_eu",
            name="Politico Europe",
            url="https://www.politico.eu/feed/",
            source_id="politico",
            category="europe",
            tier=2,
            language="en",
            country="EU"
        ),
        
        # ========================================
        # AUSTRALIAN & ASIA-PACIFIC NEWS (10 feeds)
        # ========================================
        
        RSSFeedConfig(
            id="abc_au",
            name="ABC News Australia",
            url="https://www.abc.net.au/news/feed/51120/rss.xml",
            source_id="abc",
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
            id="theaustralian",
            name="The Australian",
            url="https://www.theaustralian.com.au/feed/",
            source_id="theaustralian",
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
            id="guardian_au",
            name="The Guardian Australia",
            url="https://www.theguardian.com/australia-news/rss",
            source_id="guardian",
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
        RSSFeedConfig(
            id="stuff",
            name="Stuff NZ",
            url="https://www.stuff.co.nz/rss/",
            source_id="stuff",
            category="australia",
            tier=2,
            language="en",
            country="NZ"
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
            id="bangkokpost",
            name="Bangkok Post",
            url="https://www.bangkokpost.com/rss/data/news.xml",
            source_id="bangkokpost",
            category="world",
            tier=2,
            language="en",
            country="TH"
        ),
        
        # ========================================
        # TECHNOLOGY (15 feeds)
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
        RSSFeedConfig(
            id="engadget",
            name="Engadget",
            url="https://www.engadget.com/rss.xml",
            source_id="engadget",
            category="tech",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="zdnet",
            name="ZDNet",
            url="https://www.zdnet.com/news/rss.xml",
            source_id="zdnet",
            category="tech",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="cnet",
            name="CNET",
            url="https://www.cnet.com/rss/news/",
            source_id="cnet",
            category="tech",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="hackernews",
            name="Hacker News",
            url="https://news.ycombinator.com/rss",
            source_id="hackernews",
            category="tech",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="mittech",
            name="MIT Technology Review",
            url="https://www.technologyreview.com/feed/",
            source_id="mittech",
            category="tech",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="gizmodo",
            name="Gizmodo",
            url="https://gizmodo.com/rss",
            source_id="gizmodo",
            category="tech",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="techradar",
            name="TechRadar",
            url="https://www.techradar.com/rss",
            source_id="techradar",
            category="tech",
            tier=2,
            language="en",
            country="UK"
        ),
        RSSFeedConfig(
            id="thenextweb",
            name="The Next Web",
            url="https://thenextweb.com/feed/",
            source_id="thenextweb",
            category="tech",
            tier=2,
            language="en",
            country="NL"
        ),
        RSSFeedConfig(
            id="androidauthority",
            name="Android Authority",
            url="https://www.androidauthority.com/feed/",
            source_id="androidauthority",
            category="tech",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="9to5mac",
            name="9to5Mac",
            url="https://9to5mac.com/feed/",
            source_id="9to5mac",
            category="tech",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="venturebeat",
            name="VentureBeat",
            url="https://venturebeat.com/feed/",
            source_id="venturebeat",
            category="tech",
            tier=2,
            language="en",
            country="US"
        ),
        
        # ========================================
        # BUSINESS & FINANCE (10 feeds)
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
            id="wsj",
            name="Wall Street Journal",
            url="https://feeds.a.dj.com/rss/RSSWorldNews.xml",
            source_id="wsj",
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
        RSSFeedConfig(
            id="reuters_business",
            name="Reuters Business",
            url="https://feeds.reuters.com/reuters/businessNews",
            source_id="reuters",
            category="business",
            tier=1,
            language="en",
            country="global"
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
            id="marketwatch",
            name="MarketWatch",
            url="https://www.marketwatch.com/rss/topstories",
            source_id="marketwatch",
            category="business",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="businessinsider",
            name="Business Insider",
            url="https://www.businessinsider.com/rss",
            source_id="businessinsider",
            category="business",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="forbes",
            name="Forbes Business",
            url="https://www.forbes.com/business/feed/",
            source_id="forbes",
            category="business",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="economist",
            name="The Economist",
            url="https://www.economist.com/rss",
            source_id="economist",
            category="business",
            tier=2,
            language="en",
            country="UK"
        ),
        RSSFeedConfig(
            id="barrons",
            name="Barron's",
            url="https://www.barrons.com/rss",
            source_id="barrons",
            category="business",
            tier=2,
            language="en",
            country="US"
        ),
        
        # ========================================
        # SCIENCE & HEALTH (10 feeds)
        # ========================================
        
        RSSFeedConfig(
            id="sciencedaily",
            name="Science Daily",
            url="https://www.sciencedaily.com/rss/all.xml",
            source_id="sciencedaily",
            category="science",
            tier=2,
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
        RSSFeedConfig(
            id="sciam",
            name="Scientific American",
            url="https://www.scientificamerican.com/feed/",
            source_id="sciam",
            category="science",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="newscientist",
            name="New Scientist",
            url="https://www.newscientist.com/feed/home",
            source_id="newscientist",
            category="science",
            tier=2,
            language="en",
            country="UK"
        ),
        RSSFeedConfig(
            id="livescience",
            name="Live Science",
            url="https://www.livescience.com/feeds/all",
            source_id="livescience",
            category="science",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="space",
            name="Space.com",
            url="https://www.space.com/feeds/all",
            source_id="space",
            category="science",
            tier=2,
            language="en",
            country="US"
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
            id="webmd",
            name="WebMD Health News",
            url="https://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC",
            source_id="webmd",
            category="health",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="medicalnews",
            name="Medical News Today",
            url="https://www.medicalnewstoday.com/rss",
            source_id="medicalnews",
            category="health",
            tier=2,
            language="en",
            country="US"
        ),
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
        
        # ========================================
        # SPORTS (10 feeds)
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
        RSSFeedConfig(
            id="skysports",
            name="Sky Sports",
            url="https://www.skysports.com/rss/12040",
            source_id="skysports",
            category="sports",
            tier=2,
            language="en",
            country="UK"
        ),
        RSSFeedConfig(
            id="theathletic",
            name="The Athletic",
            url="https://theathletic.com/feeds/rss/",
            source_id="theathletic",
            category="sports",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="si",
            name="Sports Illustrated",
            url="https://www.si.com/rss/si_topstories.rss",
            source_id="si",
            category="sports",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="reuters_sports",
            name="Reuters Sports",
            url="https://feeds.reuters.com/reuters/sportsNews",
            source_id="reuters",
            category="sports",
            tier=1,
            language="en",
            country="global"
        ),
        RSSFeedConfig(
            id="foxsports",
            name="Fox Sports",
            url="https://api.foxsports.com/v1/rss?partnerKey=zBaFxRyGKCfxBagJG9b8pqLyndmvo7UU",
            source_id="foxsports",
            category="sports",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="yahoosports",
            name="Yahoo Sports",
            url="https://sports.yahoo.com/rss/",
            source_id="yahoosports",
            category="sports",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="bleacher",
            name="Bleacher Report",
            url="https://bleacherreport.com/articles/feed",
            source_id="bleacher",
            category="sports",
            tier=2,
            language="en",
            country="US"
        ),
        RSSFeedConfig(
            id="guardian_sport",
            name="The Guardian Sport",
            url="https://www.theguardian.com/sport/rss",
            source_id="guardian",
            category="sports",
            tier=2,
            language="en",
            country="UK"
        ),
    ]


def get_initial_feeds() -> List[RSSFeedConfig]:
    """
    Get initial feeds for testing
    Using verified working feeds only
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Import from working_feeds module
    try:
        from .working_feeds import get_verified_working_feeds
        feeds = get_verified_working_feeds()
        logger.info(f"✅ Loaded {len(feeds)} verified working feeds")
        return feeds
    except ImportError as e:
        logger.error(f"❌ Failed to import working_feeds: {e}")
        # Fallback to manually defined feeds if import fails
        logger.warning("Falling back to manual feed definitions")
        all_feeds = get_all_feeds()
        bbc_feeds = [feed for feed in all_feeds if feed.source_id in ["bbc", "bbc_uk", "bbc_tech", "bbc_business", "bbc_science"]]
        guardian_feeds = [feed for feed in all_feeds if feed.source_id in ["guardian", "guardian_us", "guardian_tech"]]
        other_feeds = [feed for feed in all_feeds if feed.source_id in ["aljazeera", "techcrunch", "theverge", "arstechnica", "wired", "reuters", "ap"]]
        return bbc_feeds + guardian_feeds + other_feeds[:5]  # At least 13 feeds
    except Exception as e:
        logger.error(f"❌ Unexpected error in get_initial_feeds: {e}")
        # Last resort: Return BBC only to ensure something works
        logger.warning("Last resort: Using BBC only")
        all_feeds = get_all_feeds()
        return [feed for feed in all_feeds if feed.id == "bbc_world"]


def get_feeds_by_category(category: str) -> List[RSSFeedConfig]:
    """Get feeds filtered by category"""
    all_feeds = get_all_feeds()
    return [feed for feed in all_feeds if feed.category == category]


def get_feeds_by_tier(tier: int) -> List[RSSFeedConfig]:
    """Get feeds filtered by tier (1 or 2)"""
    all_feeds = get_all_feeds()
    return [feed for feed in all_feeds if feed.tier == tier]


def get_feeds_by_region(region: str) -> List[RSSFeedConfig]:
    """Get feeds filtered by region/country"""
    all_feeds = get_all_feeds()
    return [feed for feed in all_feeds if feed.country and region.upper() in feed.country.upper()]


# Feed statistics
TOTAL_FEEDS = 100
FEEDS_BY_CATEGORY = {
    'world': 15,
    'us': 15,
    'europe': 15,
    'australia': 10,
    'tech': 15,
    'business': 10,
    'science': 8,
    'health': 2,
    'sports': 10
}

FEEDS_BY_TIER = {
    1: 8,   # Wire services - poll every 5 minutes
    2: 92   # Major outlets - poll every 10-15 minutes
}

FEEDS_BY_REGION = {
    'global': 40,
    'us': 20,
    'europe': 25,
    'australia_apac': 15
}
