"""
Configuration for RSS Worker Container App
All settings are loaded from environment variables for 12-factor compliance.
"""

import os
from typing import List
from pydantic import BaseModel


class FeedConfig(BaseModel):
    """RSS Feed configuration"""
    id: str
    name: str
    url: str
    source_id: str
    category: str
    tier: int = 2
    language: str = 'en'
    country: str = 'global'


def get_all_feeds() -> List[FeedConfig]:
    """
    Return all RSS feeds to poll.
    This is the same feed list as in Azure Functions,
    kept in sync for consistency.
    """
    return [
        # WIRE SERVICES (Tier 1)
        FeedConfig(
            id='reuters_world', name='Reuters World News',
            url='https://feeds.reuters.com/reuters/worldNews',
            source_id='reuters', category='world', tier=1
        ),
        FeedConfig(
            id='ap_world', name='Associated Press World',
            url='https://rsshub.app/apnews/topics/apf-topnews',
            source_id='ap', category='world', tier=1
        ),
        
        # US NEWS
        FeedConfig(
            id='nyt', name='New York Times',
            url='https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
            source_id='nyt', category='us', tier=2
        ),
        FeedConfig(
            id='cnn', name='CNN Top Stories',
            url='http://rss.cnn.com/rss/cnn_topstories.rss',
            source_id='cnn', category='us', tier=2
        ),
        FeedConfig(
            id='washpost', name='Washington Post',
            url='https://feeds.washingtonpost.com/rss/national',
            source_id='washingtonpost', category='us', tier=2
        ),
        FeedConfig(
            id='npr', name='NPR News',
            url='https://feeds.npr.org/1001/rss.xml',
            source_id='npr', category='us', tier=2
        ),
        FeedConfig(
            id='cbs', name='CBS News',
            url='https://www.cbsnews.com/latest/rss/main',
            source_id='cbs', category='us', tier=2
        ),
        FeedConfig(
            id='nbc', name='NBC News',
            url='https://feeds.nbcnews.com/nbcnews/public/news',
            source_id='nbc', category='us', tier=2
        ),
        FeedConfig(
            id='abc_us', name='ABC News',
            url='https://abcnews.go.com/abcnews/topstories',
            source_id='abc_us', category='us', tier=2
        ),
        FeedConfig(
            id='fox', name='Fox News',
            url='https://moxie.foxnews.com/google-publisher/latest.xml',
            source_id='fox', category='us', tier=2
        ),
        FeedConfig(
            id='politico', name='Politico',
            url='https://www.politico.com/rss/politics08.xml',
            source_id='politico', category='us', tier=2
        ),
        FeedConfig(
            id='latimes', name='Los Angeles Times',
            url='https://www.latimes.com/rss2.0.xml',
            source_id='latimes', category='us', tier=2
        ),
        
        # UK NEWS
        FeedConfig(
            id='bbc_world', name='BBC World News',
            url='http://feeds.bbci.co.uk/news/world/rss.xml',
            source_id='bbc', category='world', tier=1
        ),
        FeedConfig(
            id='guardian_world', name='The Guardian World',
            url='https://www.theguardian.com/world/rss',
            source_id='guardian', category='world', tier=2
        ),
        FeedConfig(
            id='telegraph', name='The Telegraph',
            url='https://www.telegraph.co.uk/rss.xml',
            source_id='telegraph', category='europe', tier=2
        ),
        FeedConfig(
            id='independent', name='The Independent',
            url='https://www.independent.co.uk/rss',
            source_id='independent', category='europe', tier=2
        ),
        
        # AUSTRALIAN NEWS
        FeedConfig(
            id='abc_au', name='ABC News Australia',
            url='https://www.abc.net.au/news/feed/51120/rss.xml',
            source_id='abc_au', category='australia', tier=2
        ),
        FeedConfig(
            id='smh', name='Sydney Morning Herald',
            url='https://www.smh.com.au/rss/feed.xml',
            source_id='smh', category='australia', tier=2
        ),
        FeedConfig(
            id='theage', name='The Age',
            url='https://www.theage.com.au/rss/feed.xml',
            source_id='theage', category='australia', tier=2
        ),
        FeedConfig(
            id='nzherald', name='New Zealand Herald',
            url='https://www.nzherald.co.nz/arc/outboundfeeds/rss/',
            source_id='nzherald', category='australia', tier=2
        ),
        
        # ASIAN NEWS
        FeedConfig(
            id='japantimes', name='Japan Times',
            url='https://www.japantimes.co.jp/feed/',
            source_id='japantimes', category='world', tier=2
        ),
        FeedConfig(
            id='scmp', name='South China Morning Post',
            url='https://www.scmp.com/rss/91/feed',
            source_id='scmp', category='world', tier=2
        ),
        FeedConfig(
            id='straitstimes', name='Straits Times',
            url='https://www.straitstimes.com/news/rss.xml',
            source_id='straitstimes', category='world', tier=2
        ),
        
        # MIDDLE EAST NEWS
        FeedConfig(
            id='aljazeera', name='Al Jazeera English',
            url='https://www.aljazeera.com/xml/rss/all.xml',
            source_id='aljazeera', category='world', tier=2
        ),
        FeedConfig(
            id='timesofisrael', name='Times of Israel',
            url='https://www.timesofisrael.com/feed/',
            source_id='timesofisrael', category='world', tier=2
        ),
        
        # EUROPEAN NEWS
        FeedConfig(
            id='france24', name='France 24',
            url='https://www.france24.com/en/rss',
            source_id='france24', category='world', tier=2
        ),
        FeedConfig(
            id='dw', name='Deutsche Welle',
            url='https://rss.dw.com/xml/rss-en-all',
            source_id='dw', category='world', tier=2
        ),
        FeedConfig(
            id='euronews', name='Euronews',
            url='https://www.euronews.com/rss',
            source_id='euronews', category='world', tier=2
        ),
        
        # CANADIAN NEWS
        FeedConfig(
            id='cbc', name='CBC News',
            url='https://www.cbc.ca/webfeed/rss/rss-topstories',
            source_id='cbc', category='world', tier=2
        ),
        FeedConfig(
            id='globeandmail', name='Globe and Mail',
            url='https://www.theglobeandmail.com/rss/',
            source_id='globeandmail', category='world', tier=2
        ),
        
        # TECH
        FeedConfig(
            id='techcrunch', name='TechCrunch',
            url='https://techcrunch.com/feed/',
            source_id='techcrunch', category='tech', tier=2
        ),
        FeedConfig(
            id='theverge', name='The Verge',
            url='https://www.theverge.com/rss/index.xml',
            source_id='theverge', category='tech', tier=2
        ),
        FeedConfig(
            id='arstechnica', name='Ars Technica',
            url='https://feeds.arstechnica.com/arstechnica/index',
            source_id='arstechnica', category='tech', tier=2
        ),
        FeedConfig(
            id='wired', name='Wired',
            url='https://www.wired.com/feed/rss',
            source_id='wired', category='tech', tier=2
        ),
        
        # BUSINESS
        FeedConfig(
            id='bloomberg', name='Bloomberg',
            url='https://feeds.bloomberg.com/markets/news.rss',
            source_id='bloomberg', category='business', tier=2
        ),
        FeedConfig(
            id='cnbc', name='CNBC',
            url='https://www.cnbc.com/id/100003114/device/rss/rss.html',
            source_id='cnbc', category='business', tier=2
        ),
        FeedConfig(
            id='ft', name='Financial Times',
            url='https://www.ft.com/?format=rss',
            source_id='ft', category='business', tier=2
        ),
        
        # SCIENCE
        FeedConfig(
            id='phys', name='Phys.org',
            url='https://phys.org/rss-feed/',
            source_id='phys', category='science', tier=2
        ),
        FeedConfig(
            id='nasa', name='NASA',
            url='https://www.nasa.gov/rss/dyn/breaking_news.rss',
            source_id='nasa', category='science', tier=1
        ),
        FeedConfig(
            id='nature', name='Nature',
            url='https://www.nature.com/nature.rss',
            source_id='nature', category='science', tier=2
        ),
        
        # SPORTS
        FeedConfig(
            id='espn', name='ESPN',
            url='https://www.espn.com/espn/rss/news',
            source_id='espn', category='sports', tier=2
        ),
        FeedConfig(
            id='bbc_sport', name='BBC Sport',
            url='http://feeds.bbci.co.uk/sport/rss.xml',
            source_id='bbc', category='sports', tier=2
        ),
    ]


def get_feed_by_category() -> dict:
    """Group feeds by category for round-robin distribution"""
    feeds = get_all_feeds()
    by_category = {}
    
    for feed in feeds:
        if feed.category not in by_category:
            by_category[feed.category] = []
        by_category[feed.category].append(feed)
    
    return by_category


# Environment variables with defaults
class Config:
    # Service Bus
    SERVICE_BUS_CONNECTION_STRING = os.getenv('SERVICE_BUS_CONNECTION_STRING', '')
    SERVICE_BUS_QUEUE_NAME = os.getenv('SERVICE_BUS_QUEUE_NAME', 'rss-feeds')
    
    # Cosmos DB
    COSMOS_CONNECTION_STRING = os.getenv('COSMOS_CONNECTION_STRING', '')
    COSMOS_DATABASE_NAME = os.getenv('COSMOS_DATABASE_NAME', 'newsreel-db')
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # Worker settings
    MAX_CONCURRENT_FEEDS = int(os.getenv('MAX_CONCURRENT_FEEDS', '10'))
    FEED_TIMEOUT_SECONDS = int(os.getenv('FEED_TIMEOUT_SECONDS', '30'))
    
    # Circuit breaker
    CIRCUIT_BREAKER_THRESHOLD = int(os.getenv('CIRCUIT_BREAKER_THRESHOLD', '3'))
    CIRCUIT_BREAKER_TIMEOUT_MINUTES = int(os.getenv('CIRCUIT_BREAKER_TIMEOUT_MINUTES', '30'))
    
    # Feed scheduling
    FEED_POLL_INTERVAL_SECONDS = int(os.getenv('FEED_POLL_INTERVAL_SECONDS', '180'))  # 3 minutes
    FEEDS_PER_BATCH = int(os.getenv('FEEDS_PER_BATCH', '10'))


config = Config()

