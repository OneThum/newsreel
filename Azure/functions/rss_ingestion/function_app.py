"""
RSS Ingestion Function
Timer-triggered function that polls RSS feeds every 10 seconds with staggered feed distribution
"""
import azure.functions as func
import logging
import asyncio
import aiohttp
import feedparser
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import config
from shared.cosmos_client import cosmos_client
from shared.models import RawArticle, Entity
from shared.rss_feeds import get_initial_feeds
from shared.utils import (
    generate_article_id,
    generate_story_fingerprint,
    extract_simple_entities,
    categorize_article,
    clean_html,
    truncate_text
)

logger = logging.getLogger(__name__)
app = func.FunctionApp()


class RSSFetcher:
    """RSS feed fetcher with HTTP conditional requests"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.feeds_cache: Dict[str, Dict[str, str]] = {}
    
    async def __aenter__(self):
        """Create aiohttp session"""
        timeout = aiohttp.ClientTimeout(total=config.RSS_TIMEOUT_SECONDS)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={'User-Agent': config.RSS_USER_AGENT}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def fetch_feed(self, feed_config) -> Optional[Dict[str, Any]]:
        """Fetch a single RSS feed with conditional requests"""
        try:
            headers = {}
            
            # Add conditional request headers if we have cached values
            cache_key = feed_config.id
            if cache_key in self.feeds_cache:
                if self.feeds_cache[cache_key].get('etag'):
                    headers['If-None-Match'] = self.feeds_cache[cache_key]['etag']
                if self.feeds_cache[cache_key].get('last_modified'):
                    headers['If-Modified-Since'] = self.feeds_cache[cache_key]['last_modified']
            
            async with self.session.get(feed_config.url, headers=headers) as response:
                # HTTP 304 Not Modified - no new content
                if response.status == 304:
                    logger.info(f"Feed {feed_config.name} not modified (304)")
                    return None
                
                if response.status != 200:
                    logger.warning(f"Feed {feed_config.name} returned status {response.status}")
                    return None
                
                # Cache the ETag and Last-Modified headers
                if cache_key not in self.feeds_cache:
                    self.feeds_cache[cache_key] = {}
                
                if 'ETag' in response.headers:
                    self.feeds_cache[cache_key]['etag'] = response.headers['ETag']
                if 'Last-Modified' in response.headers:
                    self.feeds_cache[cache_key]['last_modified'] = response.headers['Last-Modified']
                
                content = await response.text()
                
                # Parse RSS feed
                feed = feedparser.parse(content)
                
                if feed.bozo:  # Parse error
                    logger.warning(f"Feed {feed_config.name} has parse errors: {feed.bozo_exception}")
                
                return {
                    'config': feed_config,
                    'feed': feed,
                    'fetched_at': datetime.now(timezone.utc)
                }
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching feed: {feed_config.name}")
            return None
        except Exception as e:
            logger.error(f"Error fetching feed {feed_config.name}: {e}")
            return None
    
    async def fetch_all_feeds(self, feed_configs: List) -> List[Dict[str, Any]]:
        """Fetch all feeds in parallel with concurrency limit"""
        semaphore = asyncio.Semaphore(config.RSS_MAX_CONCURRENT)
        
        async def fetch_with_semaphore(feed_config):
            async with semaphore:
                return await self.fetch_feed(feed_config)
        
        tasks = [fetch_with_semaphore(fc) for fc in feed_configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        valid_results = [r for r in results if r and not isinstance(r, Exception)]
        
        logger.info(f"Fetched {len(valid_results)} of {len(feed_configs)} feeds successfully")
        return valid_results


def parse_entry_date(entry) -> datetime:
    """Parse entry published date"""
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        else:
            # Default to now if no date found
            return datetime.now(timezone.utc)
    except Exception as e:
        logger.warning(f"Error parsing entry date: {e}")
        return datetime.now(timezone.utc)


def process_feed_entry(entry, feed_result: Dict[str, Any]) -> Optional[RawArticle]:
    """Process a single feed entry into a RawArticle"""
    try:
        feed_config = feed_result['config']
        fetched_at = feed_result['fetched_at']
        
        # Extract basic fields
        title = clean_html(entry.get('title', ''))
        if not title:
            return None
        
        description = clean_html(entry.get('description', '') or entry.get('summary', ''))
        article_url = entry.get('link', '')
        
        if not article_url:
            return None
        
        # Parse published date
        published_at = parse_entry_date(entry)
        published_date = published_at.strftime('%Y-%m-%d')
        
        # Extract content
        content = None
        if hasattr(entry, 'content') and entry.content:
            content = clean_html(entry.content[0].value)
        elif description:
            content = description
        
        # Truncate content
        if content:
            content = truncate_text(content, max_length=2000)
        
        # Extract author
        author = entry.get('author', None)
        
        # Extract entities
        text_for_entities = f"{title} {description}"
        entities = extract_simple_entities(text_for_entities)
        
        # Categorize
        category = categorize_article(title, description, article_url)
        if category == 'general':
            category = feed_config.category
        
        # Generate IDs
        article_id = generate_article_id(feed_config.source_id, article_url, published_at)
        story_fingerprint = generate_story_fingerprint(title, entities)
        
        # Create RawArticle
        article = RawArticle(
            id=article_id,
            source=feed_config.source_id,
            source_url=feed_config.url,
            source_tier=feed_config.tier,
            article_url=article_url,
            title=title,
            description=description,
            published_at=published_at,
            fetched_at=fetched_at,
            published_date=published_date,
            content=content,
            author=author,
            entities=entities,
            category=category,
            tags=[],
            language='en',
            story_fingerprint=story_fingerprint,
            processed=False,
            processing_attempts=0
        )
        
        return article
        
    except Exception as e:
        logger.error(f"Error processing feed entry: {e}")
        return None


async def ingest_feeds():
    """Main ingestion logic"""
    logger.info("Starting RSS ingestion")
    
    # Connect to Cosmos DB
    cosmos_client.connect()
    
    # Get feed configurations
    feed_configs = get_initial_feeds()
    logger.info(f"Loading {len(feed_configs)} RSS feeds")
    
    # Fetch all feeds
    async with RSSFetcher() as fetcher:
        feed_results = await fetcher.fetch_all_feeds(feed_configs)
    
    # Process entries
    total_articles = 0
    new_articles = 0
    
    for feed_result in feed_results:
        feed = feed_result['feed']
        feed_config = feed_result['config']
        
        logger.info(f"Processing {len(feed.entries)} entries from {feed_config.name}")
        
        for entry in feed.entries:
            total_articles += 1
            
            article = process_feed_entry(entry, feed_result)
            if not article:
                continue
            
            # Store in Cosmos DB
            try:
                result = await cosmos_client.create_raw_article(article)
                if result:
                    new_articles += 1
            except Exception as e:
                logger.error(f"Error storing article {article.id}: {e}")
    
    logger.info(f"RSS ingestion complete: {new_articles} new articles out of {total_articles} total")
    return {
        'total_articles': total_articles,
        'new_articles': new_articles,
        'feeds_processed': len(feed_results)
    }


@app.function_name(name="RSSIngestion")
@app.schedule(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=False)
async def rss_ingestion_timer(timer: func.TimerRequest) -> None:
    """
    Timer trigger function that runs every 5 minutes
    Schedule: 0 */5 * * * * (every 5 minutes)
    """
    logger.info("RSS ingestion timer triggered")
    
    try:
        result = await ingest_feeds()
        logger.info(f"Ingestion result: {result}")
        
    except Exception as e:
        logger.error(f"RSS ingestion failed: {e}", exc_info=True)
        raise

