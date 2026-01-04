"""
RSS Worker - Always-on Container App for reliable RSS feed ingestion

Architecture:
- DIRECT POLLING: No queue dependency, simpler and more reliable
- Polls 10 feeds per cycle every 10 seconds
- Stores articles in Cosmos DB
- Circuit breaker prevents hammering failing feeds
- Tracks feed poll states in Cosmos DB for round-robin coverage
- Health endpoint for monitoring

This replaces the flaky Azure Functions timer trigger with
a bulletproof always-on worker.
"""

import os
import asyncio
import json
import logging
import signal
import sys
import time
import hashlib
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

import aiohttp
import feedparser
from azure.cosmos import CosmosClient
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# Configuration from environment
COSMOS_CONNECTION_STRING = os.getenv('COSMOS_CONNECTION_STRING', '')
COSMOS_DATABASE_NAME = os.getenv('COSMOS_DATABASE_NAME', 'newsreel-db')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Worker configuration
FEEDS_PER_CYCLE = int(os.getenv('FEEDS_PER_CYCLE', '10'))  # 10 feeds per cycle
POLL_INTERVAL_SECONDS = int(os.getenv('POLL_INTERVAL_SECONDS', '10'))  # Every 10 seconds
FEED_TIMEOUT_SECONDS = int(os.getenv('FEED_TIMEOUT_SECONDS', '30'))
CIRCUIT_BREAKER_THRESHOLD = int(os.getenv('CIRCUIT_BREAKER_THRESHOLD', '3'))
CIRCUIT_BREAKER_TIMEOUT_MINUTES = int(os.getenv('CIRCUIT_BREAKER_TIMEOUT_MINUTES', '30'))
FEED_COOLDOWN_MINUTES = int(os.getenv('FEED_COOLDOWN_MINUTES', '5'))  # Don't poll same feed within 5 min

# Logging setup with structured output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('rss-worker')


def format_iso_date(dt: datetime) -> str:
    """Format datetime to ISO8601 with seconds precision (no microseconds).
    
    Standardizes all dates to: 2026-01-04T12:30:45Z
    This ensures consistent parsing across all clients.
    """
    if dt.tzinfo:
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    return dt.strftime('%Y-%m-%dT%H:%M:%S')


# =============================================================================
# FEED CONFIGURATIONS - Verified working feeds (excluding broken ones)
# =============================================================================

VERIFIED_FEEDS = [
    # WIRE SERVICES (Tier 1)
    # NOTE: Reuters and AP direct feeds are broken (DNS/403), using alternatives
    {"id": "bbc_world", "name": "BBC World News", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "source_id": "bbc", "category": "world", "tier": 1},
    
    # US NEWS
    {"id": "nyt", "name": "New York Times", "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", "source_id": "nyt", "category": "us", "tier": 2},
    {"id": "cnn", "name": "CNN Top Stories", "url": "http://rss.cnn.com/rss/cnn_topstories.rss", "source_id": "cnn", "category": "us", "tier": 2},
    {"id": "washpost", "name": "Washington Post", "url": "https://feeds.washingtonpost.com/rss/national", "source_id": "washingtonpost", "category": "us", "tier": 2},
    {"id": "npr", "name": "NPR News", "url": "https://feeds.npr.org/1001/rss.xml", "source_id": "npr", "category": "us", "tier": 2},
    {"id": "cbs", "name": "CBS News", "url": "https://www.cbsnews.com/latest/rss/main", "source_id": "cbs", "category": "us", "tier": 2},
    {"id": "nbc", "name": "NBC News", "url": "https://feeds.nbcnews.com/nbcnews/public/news", "source_id": "nbc", "category": "us", "tier": 2},
    {"id": "abc_us", "name": "ABC News", "url": "https://abcnews.go.com/abcnews/topstories", "source_id": "abc_us", "category": "us", "tier": 2},
    {"id": "fox", "name": "Fox News", "url": "https://moxie.foxnews.com/google-publisher/latest.xml", "source_id": "fox", "category": "us", "tier": 2},
    {"id": "latimes", "name": "Los Angeles Times", "url": "https://www.latimes.com/rss2.0.xml", "source_id": "latimes", "category": "us", "tier": 2},
    # NOTE: Politico returns 403, excluded
    
    # UK NEWS
    {"id": "guardian_world", "name": "The Guardian", "url": "https://www.theguardian.com/world/rss", "source_id": "guardian", "category": "world", "tier": 2},
    {"id": "telegraph", "name": "The Telegraph", "url": "https://www.telegraph.co.uk/rss.xml", "source_id": "telegraph", "category": "europe", "tier": 2},
    {"id": "independent", "name": "The Independent", "url": "https://www.independent.co.uk/rss", "source_id": "independent", "category": "europe", "tier": 2},
    
    # AUSTRALIAN & NZ NEWS
    {"id": "abc_au", "name": "ABC Australia", "url": "https://www.abc.net.au/news/feed/51120/rss.xml", "source_id": "abc_au", "category": "australia", "tier": 2},
    {"id": "smh", "name": "Sydney Morning Herald", "url": "https://www.smh.com.au/rss/feed.xml", "source_id": "smh", "category": "australia", "tier": 2},
    {"id": "theage", "name": "The Age", "url": "https://www.theage.com.au/rss/feed.xml", "source_id": "theage", "category": "australia", "tier": 2},
    {"id": "newscomau", "name": "News.com.au", "url": "https://www.news.com.au/content-feeds/latest-news-national/", "source_id": "newscomau", "category": "australia", "tier": 2},
    {"id": "nzherald", "name": "NZ Herald", "url": "https://www.nzherald.co.nz/arc/outboundfeeds/rss/", "source_id": "nzherald", "category": "australia", "tier": 2},
    
    # ASIAN NEWS
    {"id": "japantimes", "name": "Japan Times", "url": "https://www.japantimes.co.jp/feed/", "source_id": "japantimes", "category": "world", "tier": 2},
    {"id": "scmp", "name": "South China Morning Post", "url": "https://www.scmp.com/rss/91/feed", "source_id": "scmp", "category": "world", "tier": 2},
    {"id": "straitstimes", "name": "Straits Times", "url": "https://www.straitstimes.com/news/rss.xml", "source_id": "straitstimes", "category": "world", "tier": 2},
    {"id": "cgtn", "name": "CGTN China", "url": "https://www.cgtn.com/subscribe/rss/section/world.xml", "source_id": "cgtn", "category": "world", "tier": 2},
    {"id": "bangkokpost", "name": "Bangkok Post", "url": "https://www.bangkokpost.com/rss/data/news.xml", "source_id": "bangkokpost", "category": "world", "tier": 2},
    {"id": "jakartapost", "name": "Jakarta Post", "url": "https://www.thejakartapost.com/rss", "source_id": "jakartapost", "category": "world", "tier": 2},
    
    # MIDDLE EAST NEWS
    {"id": "aljazeera", "name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "source_id": "aljazeera", "category": "world", "tier": 2},
    {"id": "timesofisrael", "name": "Times of Israel", "url": "https://www.timesofisrael.com/feed/", "source_id": "timesofisrael", "category": "world", "tier": 2},
    {"id": "middleeasteye", "name": "Middle East Eye", "url": "https://www.middleeasteye.net/rss", "source_id": "middleeasteye", "category": "world", "tier": 2},
    
    # EUROPEAN NEWS
    {"id": "france24", "name": "France 24", "url": "https://www.france24.com/en/rss", "source_id": "france24", "category": "world", "tier": 2},
    {"id": "dw", "name": "Deutsche Welle", "url": "https://rss.dw.com/xml/rss-en-all", "source_id": "dw", "category": "world", "tier": 2},
    {"id": "euronews", "name": "Euronews", "url": "https://www.euronews.com/rss", "source_id": "euronews", "category": "world", "tier": 2},
    {"id": "lemonde", "name": "Le Monde English", "url": "https://www.lemonde.fr/en/rss/une.xml", "source_id": "lemonde", "category": "europe", "tier": 2},
    {"id": "spiegel", "name": "Der Spiegel", "url": "https://www.spiegel.de/international/index.rss", "source_id": "spiegel", "category": "europe", "tier": 2},
    {"id": "ansa", "name": "ANSA English", "url": "https://www.ansa.it/english/news/general_news.xml", "source_id": "ansa", "category": "europe", "tier": 2},
    {"id": "elpais", "name": "El País English", "url": "https://elpais.com/rss/elpais/inenglish.xml", "source_id": "elpais", "category": "europe", "tier": 2},
    {"id": "irishtimes", "name": "Irish Times", "url": "https://www.irishtimes.com/cmlink/news-1.1319192", "source_id": "irishtimes", "category": "europe", "tier": 2},
    {"id": "dutchnews", "name": "DutchNews.nl", "url": "https://www.dutchnews.nl/feed/", "source_id": "dutchnews", "category": "europe", "tier": 2},
    {"id": "swissinfo", "name": "SwissInfo", "url": "https://www.swissinfo.ch/eng/rss", "source_id": "swissinfo", "category": "europe", "tier": 2},
    
    # CANADIAN NEWS
    {"id": "cbc", "name": "CBC News", "url": "https://www.cbc.ca/webfeed/rss/rss-topstories", "source_id": "cbc", "category": "world", "tier": 2},
    {"id": "globeandmail", "name": "Globe and Mail", "url": "https://www.theglobeandmail.com/rss/", "source_id": "globeandmail", "category": "world", "tier": 2},
    
    # TECHNOLOGY
    {"id": "techcrunch", "name": "TechCrunch", "url": "https://techcrunch.com/feed/", "source_id": "techcrunch", "category": "tech", "tier": 2},
    {"id": "theverge", "name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "source_id": "theverge", "category": "tech", "tier": 2},
    {"id": "arstechnica", "name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "source_id": "arstechnica", "category": "tech", "tier": 2},
    {"id": "wired", "name": "Wired", "url": "https://www.wired.com/feed/rss", "source_id": "wired", "category": "tech", "tier": 2},
    
    # BUSINESS
    {"id": "bloomberg", "name": "Bloomberg", "url": "https://feeds.bloomberg.com/markets/news.rss", "source_id": "bloomberg", "category": "business", "tier": 2},
    {"id": "cnbc", "name": "CNBC", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "source_id": "cnbc", "category": "business", "tier": 2},
    {"id": "ft", "name": "Financial Times", "url": "https://www.ft.com/?format=rss", "source_id": "ft", "category": "business", "tier": 2},
    
    # SCIENCE
    {"id": "phys", "name": "Phys.org", "url": "https://phys.org/rss-feed/", "source_id": "phys", "category": "science", "tier": 2},
    {"id": "nasa", "name": "NASA", "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss", "source_id": "nasa", "category": "science", "tier": 1},
    {"id": "nature", "name": "Nature", "url": "https://www.nature.com/nature.rss", "source_id": "nature", "category": "science", "tier": 2},
    
    # SPORTS
    {"id": "espn", "name": "ESPN", "url": "https://www.espn.com/espn/rss/news", "source_id": "espn", "category": "sports", "tier": 2},
    {"id": "bbc_sport", "name": "BBC Sport", "url": "http://feeds.bbci.co.uk/sport/rss.xml", "source_id": "bbc", "category": "sports", "tier": 2},
]


# =============================================================================
# CIRCUIT BREAKER
# =============================================================================

class CircuitBreaker:
    """Circuit breaker pattern to prevent hammering failing feeds."""
    
    def __init__(self, threshold: int = 3, timeout_minutes: int = 30):
        self.threshold = threshold
        self.timeout = timedelta(minutes=timeout_minutes)
        self._states: Dict[str, Tuple[int, Optional[datetime], bool]] = {}
        self._lock = asyncio.Lock()
    
    async def record_success(self, feed_id: str):
        """Reset circuit on success"""
        async with self._lock:
            self._states[feed_id] = (0, None, False)
    
    async def record_failure(self, feed_id: str) -> bool:
        """Record failure, return True if circuit is now open"""
        async with self._lock:
            count, _, _ = self._states.get(feed_id, (0, None, False))
            count += 1
            now = datetime.now(timezone.utc)
            is_open = count >= self.threshold
            self._states[feed_id] = (count, now, is_open)
            if is_open:
                logger.warning(f'CIRCUIT_OPEN feed={feed_id} failures={count}')
            return is_open
    
    async def should_allow(self, feed_id: str) -> bool:
        """Check if request should be allowed"""
        async with self._lock:
            if feed_id not in self._states:
                return True
            count, last_failure, is_open = self._states[feed_id]
            if not is_open:
                return True
            if last_failure and datetime.now(timezone.utc) - last_failure > self.timeout:
                logger.info(f'CIRCUIT_HALF_OPEN feed={feed_id}')
                return True
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        open_circuits = [fid for fid, (_, _, is_open) in self._states.items() if is_open]
        return {
            'total_tracked': len(self._states),
            'open_circuits': len(open_circuits),
            'open_feeds': open_circuits[:10]
        }


# =============================================================================
# RSS FETCHER
# =============================================================================

class RSSFetcher:
    """Async RSS feed fetcher with connection pooling."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
        self.executor = ThreadPoolExecutor(max_workers=FEEDS_PER_CYCLE * 2)
        self.user_agent = 'Newsreel/2.0 (+https://newsreel.app) RSS-Worker'
    
    async def start(self):
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers={'User-Agent': self.user_agent}
            )
            logger.info('HTTP_SESSION_INITIALIZED')
    
    async def stop(self):
        if self.session:
            await self.session.close()
            self.session = None
        self.executor.shutdown(wait=False)
        logger.info('HTTP_SESSION_CLOSED')
    
    async def fetch_feed(self, feed_url: str, feed_id: str) -> Optional[Dict[str, Any]]:
        """Fetch and parse a single RSS feed."""
        if not self.session:
            await self.start()
        
        start_time = time.time()
        try:
            async with self.session.get(feed_url) as response:
                fetch_time_ms = int((time.time() - start_time) * 1000)
                
                if response.status == 304:
                    logger.debug(f'FEED_NOT_MODIFIED feed={feed_id}')
                    return None
                
                if response.status != 200:
                    logger.warning(f'FEED_HTTP_ERROR feed={feed_id} status={response.status} url={feed_url}')
                    return None
                
                content = await response.text()
                
                # Parse feed in thread pool (feedparser is sync/blocking)
                loop = asyncio.get_event_loop()
                feed = await loop.run_in_executor(self.executor, feedparser.parse, content)
                
                entry_count = len(feed.entries)
                logger.info(f'FEED_FETCHED feed={feed_id} entries={entry_count} time_ms={fetch_time_ms}')
                
                return {
                    'feed': feed,
                    'url': feed_url,
                    'fetch_time_ms': fetch_time_ms,
                    'entry_count': entry_count
                }
                
        except asyncio.TimeoutError:
            logger.error(f'FEED_TIMEOUT feed={feed_id} url={feed_url}')
            return None
        except aiohttp.ClientError as e:
            logger.error(f'FEED_CLIENT_ERROR feed={feed_id} error={e}')
            return None
        except Exception as e:
            logger.error(f'FEED_ERROR feed={feed_id} error={e}')
            return None


# =============================================================================
# ARTICLE PROCESSOR
# =============================================================================

class ArticleProcessor:
    """Process RSS entries into articles and store in Cosmos DB."""
    
    def __init__(self, cosmos_client: CosmosClient, database_name: str):
        self.database = cosmos_client.get_database_client(database_name)
        self.articles_container = self.database.get_container_client('raw_articles')
        self.feed_states_container = self.database.get_container_client('feed_poll_states')
        self.openai_client = None
        
        if OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f'OPENAI_INIT_FAILED error={e}')
    
    def generate_article_id(self, source_id: str, url: str, published_at: datetime) -> str:
        """Generate unique article ID"""
        # Article ID must be STABLE across ingestion cycles to prevent duplicates
        # Use only URL hash (the unique identifier) + date (not time) for partitioning
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        date_str = published_at.strftime('%Y%m%d')  # Date only, no time - prevents duplicate IDs
        return f'{source_id}_{date_str}_{url_hash}'
    
    def clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        if not text:
            return ''
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()
    
    def parse_date(self, entry) -> datetime:
        """Parse entry published date"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass
        return datetime.now(timezone.utc)
    
    def is_spam(self, title: str, description: str, url: str) -> bool:
        """Filter spam/promotional content"""
        spam_patterns = [
            'sponsored', 'advertisement', 'promoted', 'partner content',
            'buy now', 'shop now', 'limited time', 'exclusive offer',
            'click here', 'subscribe now', 'sign up', 'free trial'
        ]
        text = f'{title} {description} {url}'.lower()
        return any(pattern in text for pattern in spam_patterns)
    
    def generate_embedding(self, title: str, description: str) -> Optional[List[float]]:
        """Generate semantic embedding using OpenAI"""
        if not self.openai_client:
            return None
        
        try:
            text = f'{title}. {description or ""}'[:2000]
            response = self.openai_client.embeddings.create(
                model='text-embedding-3-small',
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f'EMBEDDING_FAILED error={e}')
            return None
    
    def is_lifestyle_content(self, title: str, description: str) -> bool:
        """Detect lifestyle content that should never be in Top Stories.
        
        Lifestyle includes: how-to guides, product reviews, recipes, gift ideas,
        personal advice, "best X for Y" lists, cooking tips, holiday ideas.
        """
        import re
        title_lower = title.lower()
        text = f'{title} {description}'.lower()
        
        lifestyle_patterns = [
            r'\bbest\b.*\b(?:for|of|to|in)\b',       # "best X for/of/to/in"
            r'\btop\s+\d+\b',                         # "top 10", "top 5"
            r'\b\d+\s+best\b',                        # "7 best", "10 best"
            r'\breviewed?\b',                         # "review", "reviewed"
            r'\btested\b',                            # "tested"
            r'\bguide\s+to\b',                        # "guide to"
            r'\bhow\s+to\b',                          # "how to"
            r'\btips?\s+(?:for|on|to)\b',            # "tips for/on/to"
            r'\badvice\b',                            # "advice"
            r'\brecipes?\b',                          # "recipe", "recipes"
            r'\bdeal[s]?\b.*\b(?:on|for)\b',         # "deals on/for"
            r'\bgift\s+(?:guide|ideas?)\b',          # "gift guide", "gift ideas"
            r'\bwe\s+stopped\s+using\b',             # "we stopped using X"
            r'\bwhy\s+(?:i|we)\s+(?:stopped|switched)\b',  # "why I stopped X"
            r'\bmother\'?s?\s+day\b',                # Mother's Day
            r'\bfather\'?s?\s+day\b',                # Father's Day
            r'\bvalentine\'?s?\b',                   # Valentine's
            r'\bholiday\s+(?:gift|idea|tip)\b',      # holiday gifts/ideas/tips
            r'\bcooking\s+(?:tip|hack|trick)\b',    # cooking tips
            r'\bkitchen\s+(?:tip|hack|trick)\b',    # kitchen tips
            r'\bfoil\s+(?:for|in)\s+cooking\b',     # foil for cooking
            r'\b(?:our|my)\s+(?:top\s+)?picks?\b',  # "our picks"
            r'\bbest\s+(?:buys?|picks?|choices?)\b', # "best buys"
            r'\bwhat\s+to\s+(?:buy|get|wear)\b',    # "what to buy"
        ]
        
        return any(re.search(p, title_lower) for p in lifestyle_patterns)
    
    def categorize(self, title: str, description: str, url: str, feed_category: str = None) -> str:
        """Category detection with lifestyle override.
        
        IMPORTANT: Lifestyle detection takes priority over feed category.
        This prevents "Top Stories" from CNN/ABC from including lifestyle content.
        """
        # ALWAYS check for lifestyle first - this overrides feed category
        if self.is_lifestyle_content(title, description):
            logger.debug(f'Lifestyle detected: {title[:50]}...')
            return 'lifestyle'
        
        # Use feed category if provided (for hard news feeds)
        if feed_category and feed_category not in ('general', 'unknown'):
            return feed_category
        
        # Fallback to keyword-based detection
        text = f'{title} {description} {url}'.lower()
        if any(w in text for w in ['tech', 'software', 'app', 'ai', 'crypto', 'startup']):
            return 'tech'
        if any(w in text for w in ['business', 'market', 'stock', 'economy', 'trade']):
            return 'business'
        if any(w in text for w in ['sport', 'football', 'basketball', 'soccer', 'nfl', 'nba']):
            return 'sports'
        if any(w in text for w in ['science', 'research', 'study', 'nasa', 'space']):
            return 'science'
        if any(w in text for w in ['health', 'medical', 'vaccine', 'disease', 'hospital']):
            return 'health'
        return 'world'
    
    async def process_entry(self, entry, feed_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single feed entry into an article"""
        try:
            title = self.clean_html(entry.get('title', ''))
            if not title:
                return None
            
            description = self.clean_html(entry.get('description', '') or entry.get('summary', ''))
            url = entry.get('link', '')
            
            if not url:
                return None
            
            if self.is_spam(title, description, url):
                return None
            
            published_at = self.parse_date(entry)
            
            # Generate embedding for semantic clustering
            embedding = self.generate_embedding(title, description)
            
            article = {
                'id': self.generate_article_id(feed_config['source_id'], url, published_at),
                'source': feed_config['source_id'],
                'source_url': feed_config['url'],
                'source_tier': feed_config.get('tier', 2),
                'article_url': url,
                'title': title,
                'description': description,
                'published_at': format_iso_date(published_at),
                'published_date': published_at.strftime('%Y-%m-%d'),
                'fetched_at': format_iso_date(datetime.now(timezone.utc)),
                'updated_at': format_iso_date(datetime.now(timezone.utc)),
                'category': self.categorize(title, description, url, feed_config.get('category')),
                'embedding': embedding,
                'processed': False,
                'processing_attempts': 0
            }
            
            return article
            
        except Exception as e:
            logger.error(f'ENTRY_PROCESS_ERROR error={e}')
            return None
    
    def store_article(self, article: Dict[str, Any]) -> bool:
        """Store article in Cosmos DB (upsert)"""
        try:
            self.articles_container.upsert_item(article)
            return True
        except Exception as e:
            logger.error(f'ARTICLE_STORE_ERROR id={article.get("id")} error={e}')
            return False
    
    def update_feed_state(self, feed_id: str, success: bool, articles_count: int, error: Optional[str] = None):
        """Update feed poll state in Cosmos DB"""
        try:
            now = format_iso_date(datetime.now(timezone.utc))
            state = {
                'id': feed_id,
                'last_poll': now,
                'last_success': now if success else None,
                'last_error': error,
                'articles_fetched': articles_count,
                'consecutive_failures': 0 if success else 1,  # Will be updated on next poll
                'updated_at': now
            }
            
            # Try to get existing state to preserve consecutive_failures
            try:
                existing = self.feed_states_container.read_item(item=feed_id, partition_key=feed_id)
                if not success:
                    state['consecutive_failures'] = existing.get('consecutive_failures', 0) + 1
                state['total_polls'] = existing.get('total_polls', 0) + 1
                state['total_articles'] = existing.get('total_articles', 0) + articles_count
            except Exception:
                state['total_polls'] = 1
                state['total_articles'] = articles_count
            
            self.feed_states_container.upsert_item(state)
        except Exception as e:
            logger.warning(f'FEED_STATE_UPDATE_ERROR feed={feed_id} error={e}')
    
    def get_feeds_ready_to_poll(self, all_feeds: List[Dict], cooldown_minutes: int) -> List[Dict]:
        """Get feeds that are ready to poll (not recently polled)"""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes)
        ready_feeds = []
        
        for feed in all_feeds:
            try:
                state = self.feed_states_container.read_item(item=feed['id'], partition_key=feed['id'])
                last_poll = state.get('last_poll')
                if last_poll:
                    last_poll_dt = datetime.fromisoformat(last_poll.replace('Z', '+00:00'))
                    if last_poll_dt > cutoff:
                        continue  # Skip recently polled
            except Exception:
                pass  # No state = never polled = ready
            
            ready_feeds.append(feed)
        
        return ready_feeds


# =============================================================================
# POLLING WORKER
# =============================================================================

class PollingWorker:
    """Main worker that continuously polls RSS feeds."""
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            threshold=CIRCUIT_BREAKER_THRESHOLD,
            timeout_minutes=CIRCUIT_BREAKER_TIMEOUT_MINUTES
        )
        self.fetcher = RSSFetcher(timeout=FEED_TIMEOUT_SECONDS)
        self.processor: Optional[ArticleProcessor] = None
        self.is_running = False
        self.feeds = VERIFIED_FEEDS.copy()
        self.current_feed_index = 0
        self.stats = {
            'feeds_processed': 0,
            'articles_stored': 0,
            'errors': 0,
            'circuit_breaks': 0,
            'cycles_completed': 0,
            'start_time': None
        }
        self.feed_stats = defaultdict(lambda: {'success': 0, 'errors': 0, 'articles': 0})
    
    async def start(self):
        """Initialize connections"""
        logger.info('WORKER_STARTING')
        
        cosmos_client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
        self.processor = ArticleProcessor(cosmos_client, COSMOS_DATABASE_NAME)
        
        await self.fetcher.start()
        
        self.stats['start_time'] = format_iso_date(datetime.now(timezone.utc))
        self.is_running = True
        
        logger.info(f'WORKER_STARTED feeds_count={len(self.feeds)} feeds_per_cycle={FEEDS_PER_CYCLE} poll_interval={POLL_INTERVAL_SECONDS}s')
    
    async def stop(self):
        """Clean shutdown"""
        logger.info('WORKER_STOPPING')
        self.is_running = False
        await self.fetcher.stop()
        logger.info('WORKER_STOPPED')
    
    async def process_feed(self, feed_config: Dict[str, Any]) -> Tuple[bool, int]:
        """Process a single feed. Returns (success, articles_stored)."""
        feed_id = feed_config['id']
        feed_url = feed_config['url']
        
        # Check circuit breaker
        if not await self.circuit_breaker.should_allow(feed_id):
            self.stats['circuit_breaks'] += 1
            return (False, 0)
        
        # Fetch feed
        result = await self.fetcher.fetch_feed(feed_url, feed_id)
        
        if not result:
            await self.circuit_breaker.record_failure(feed_id)
            self.stats['errors'] += 1
            self.feed_stats[feed_id]['errors'] += 1
            self.processor.update_feed_state(feed_id, False, 0, 'fetch_failed')
            return (False, 0)
        
        # Process entries
        feed = result['feed']
        articles_stored = 0
        
        for entry in feed.entries:
            article = await self.processor.process_entry(entry, feed_config)
            if article:
                if self.processor.store_article(article):
                    articles_stored += 1
        
        # Record success
        await self.circuit_breaker.record_success(feed_id)
        self.stats['feeds_processed'] += 1
        self.stats['articles_stored'] += articles_stored
        self.feed_stats[feed_id]['success'] += 1
        self.feed_stats[feed_id]['articles'] += articles_stored
        
        self.processor.update_feed_state(feed_id, True, articles_stored)
        
        logger.info(f'FEED_PROCESSED feed={feed_id} articles_stored={articles_stored} entries={result["entry_count"]} time_ms={result["fetch_time_ms"]}')
        
        return (True, articles_stored)
    
    def get_next_feeds(self) -> List[Dict[str, Any]]:
        """Get next batch of feeds to poll using round-robin with cooldown."""
        # Get feeds ready to poll (not recently polled)
        ready_feeds = self.processor.get_feeds_ready_to_poll(self.feeds, FEED_COOLDOWN_MINUTES)
        
        if not ready_feeds:
            logger.info('NO_FEEDS_READY all feeds recently polled, waiting...')
            return []
        
        # Round-robin selection from ready feeds
        selected = []
        for i in range(min(FEEDS_PER_CYCLE, len(ready_feeds))):
            idx = (self.current_feed_index + i) % len(ready_feeds)
            selected.append(ready_feeds[idx])
        
        self.current_feed_index = (self.current_feed_index + len(selected)) % len(self.feeds)
        
        return selected
    
    async def run(self):
        """Main worker loop - poll feeds continuously"""
        await self.start()
        
        logger.info(f'POLLING_LOOP_STARTED interval={POLL_INTERVAL_SECONDS}s feeds_per_cycle={FEEDS_PER_CYCLE}')
        
        while self.is_running:
            try:
                cycle_start = time.time()
                
                # Get next batch of feeds
                feeds_to_poll = self.get_next_feeds()
                
                if feeds_to_poll:
                    # Process feeds concurrently
                    tasks = [self.process_feed(feed) for feed in feeds_to_poll]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Log cycle summary
                    success_count = sum(1 for r in results if isinstance(r, tuple) and r[0])
                    articles_count = sum(r[1] for r in results if isinstance(r, tuple))
                    error_count = sum(1 for r in results if isinstance(r, Exception) or (isinstance(r, tuple) and not r[0]))
                    
                    cycle_time_ms = int((time.time() - cycle_start) * 1000)
                    self.stats['cycles_completed'] += 1
                    
                    logger.info(f'CYCLE_COMPLETE cycle={self.stats["cycles_completed"]} feeds_polled={len(feeds_to_poll)} success={success_count} errors={error_count} articles={articles_count} time_ms={cycle_time_ms}')
                
                # Wait for next cycle
                elapsed = time.time() - cycle_start
                sleep_time = max(0, POLL_INTERVAL_SECONDS - elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    
            except Exception as e:
                logger.error(f'CYCLE_ERROR error={e}')
                await asyncio.sleep(1)
        
        await self.stop()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        return {
            **self.stats,
            'circuit_breaker': self.circuit_breaker.get_status(),
            'is_running': self.is_running,
            'total_feeds': len(self.feeds),
            'feeds_per_cycle': FEEDS_PER_CYCLE,
            'poll_interval_seconds': POLL_INTERVAL_SECONDS,
            'top_feeds': sorted(
                [{'feed_id': k, **v} for k, v in self.feed_stats.items()],
                key=lambda x: x['articles'],
                reverse=True
            )[:10]
        }


# =============================================================================
# HEALTH API
# =============================================================================

worker = PollingWorker()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    asyncio.create_task(worker.run())
    yield
    await worker.stop()

app = FastAPI(
    title='Newsreel RSS Worker',
    description='Always-on RSS feed polling worker',
    lifespan=lifespan
)


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    stats: Dict[str, Any]


@app.get('/health', response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Container Apps"""
    stats = worker.get_stats()
    
    uptime = 0
    if stats['start_time']:
        start = datetime.fromisoformat(stats['start_time'])
        uptime = (datetime.now(timezone.utc) - start).total_seconds()
    
    # Determine health status
    status = 'healthy'
    if not worker.is_running:
        status = 'unhealthy'
    elif stats['errors'] > stats['feeds_processed'] * 0.5:  # >50% error rate
        status = 'degraded'
    
    return HealthResponse(
        status=status,
        uptime_seconds=uptime,
        stats=stats
    )


@app.get('/stats')
async def get_stats():
    """Detailed statistics endpoint"""
    return worker.get_stats()


@app.get('/feeds')
async def get_feeds():
    """List all configured feeds"""
    return {
        'total': len(worker.feeds),
        'feeds': worker.feeds
    }


@app.post('/circuit-breaker/reset/{feed_id}')
async def reset_circuit(feed_id: str):
    """Manually reset circuit breaker for a feed"""
    await worker.circuit_breaker.record_success(feed_id)
    return {'status': 'reset', 'feed_id': feed_id}


# =============================================================================
# MAIN
# =============================================================================

def handle_shutdown(signum, frame):
    """Handle shutdown signals"""
    logger.info(f'SIGNAL_RECEIVED signal={signum}')
    worker.is_running = False


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    
    if not COSMOS_CONNECTION_STRING:
        logger.error('COSMOS_CONNECTION_STRING not set')
        sys.exit(1)
    
    logger.info(f'CONFIG feeds={len(VERIFIED_FEEDS)} per_cycle={FEEDS_PER_CYCLE} interval={POLL_INTERVAL_SECONDS}s')
    
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8080,
        log_level='info'
    )
