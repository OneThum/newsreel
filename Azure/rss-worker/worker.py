"""
RSS Worker - Always-on Container App for reliable RSS feed ingestion

Architecture:
- Pulls feed URLs from Azure Service Bus Queue
- Fetches and parses RSS feeds with retry logic
- Stores articles in Cosmos DB
- Circuit breaker prevents hammering failing feeds
- Dead letter queue for failed messages
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
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

import aiohttp
import feedparser
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
from azure.cosmos import CosmosClient
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import numpy as np

# Configuration from environment
SERVICE_BUS_CONNECTION_STRING = os.getenv('SERVICE_BUS_CONNECTION_STRING', '')
SERVICE_BUS_QUEUE_NAME = os.getenv('SERVICE_BUS_QUEUE_NAME', 'rss-feeds')
COSMOS_CONNECTION_STRING = os.getenv('COSMOS_CONNECTION_STRING', '')
COSMOS_DATABASE_NAME = os.getenv('COSMOS_DATABASE_NAME', 'newsreel-db')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Worker configuration
MAX_CONCURRENT_FEEDS = int(os.getenv('MAX_CONCURRENT_FEEDS', '10'))
FEED_TIMEOUT_SECONDS = int(os.getenv('FEED_TIMEOUT_SECONDS', '30'))
CIRCUIT_BREAKER_THRESHOLD = int(os.getenv('CIRCUIT_BREAKER_THRESHOLD', '3'))
CIRCUIT_BREAKER_TIMEOUT_MINUTES = int(os.getenv('CIRCUIT_BREAKER_TIMEOUT_MINUTES', '30'))

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('rss-worker')


# =============================================================================
# CIRCUIT BREAKER
# =============================================================================

class CircuitBreaker:
    """
    Circuit breaker pattern to prevent hammering failing feeds.
    
    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Feed is failing, requests blocked
    - HALF_OPEN: Testing if feed recovered
    """
    
    def __init__(self, threshold: int = 3, timeout_minutes: int = 30):
        self.threshold = threshold
        self.timeout = timedelta(minutes=timeout_minutes)
        # feed_id -> (failure_count, last_failure_time, is_open)
        self._states: Dict[str, tuple] = {}
        self._lock = asyncio.Lock()
    
    async def record_success(self, feed_id: str):
        """Reset circuit on success"""
        async with self._lock:
            self._states[feed_id] = (0, None, False)
            logger.debug(f'Circuit CLOSED for {feed_id}')
    
    async def record_failure(self, feed_id: str) -> bool:
        """Record failure, return True if circuit is now open"""
        async with self._lock:
            count, _, _ = self._states.get(feed_id, (0, None, False))
            count += 1
            now = datetime.now(timezone.utc)
            
            is_open = count >= self.threshold
            self._states[feed_id] = (count, now, is_open)
            
            if is_open:
                logger.warning(f'Circuit OPEN for {feed_id} after {count} failures')
            
            return is_open
    
    async def should_allow(self, feed_id: str) -> bool:
        """Check if request should be allowed"""
        async with self._lock:
            if feed_id not in self._states:
                return True
            
            count, last_failure, is_open = self._states[feed_id]
            
            if not is_open:
                return True
            
            # Check if timeout expired (half-open state)
            if last_failure and datetime.now(timezone.utc) - last_failure > self.timeout:
                logger.info(f'Circuit HALF-OPEN for {feed_id}, allowing test request')
                return True
            
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for monitoring"""
        open_circuits = [
            feed_id for feed_id, (_, _, is_open) in self._states.items() if is_open
        ]
        return {
            'total_tracked': len(self._states),
            'open_circuits': len(open_circuits),
            'open_feeds': open_circuits[:10]  # Limit for response size
        }


# =============================================================================
# RSS FETCHER
# =============================================================================

class RSSFetcher:
    """
    Async RSS feed fetcher with connection pooling and retries.
    Uses a thread pool for feedparser (which is synchronous).
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
        self.executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_FEEDS)
        self.user_agent = 'Newsreel/2.0 (+https://newsreel.app) RSS-Worker'
    
    async def start(self):
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers={'User-Agent': self.user_agent}
            )
            logger.info('HTTP session initialized')
    
    async def stop(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
        self.executor.shutdown(wait=False)
        logger.info('HTTP session closed')
    
    async def fetch_feed(self, feed_url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch and parse a single RSS feed.
        Returns parsed feed data or None on failure.
        """
        if not self.session:
            await self.start()
        
        try:
            start_time = time.time()
            
            async with self.session.get(feed_url) as response:
                if response.status == 304:
                    logger.debug(f'Feed not modified: {feed_url}')
                    return None
                
                if response.status != 200:
                    logger.warning(f'Feed returned {response.status}: {feed_url}')
                    return None
                
                content = await response.text()
                
                # Parse feed in thread pool (feedparser is sync/blocking)
                loop = asyncio.get_event_loop()
                feed = await loop.run_in_executor(
                    self.executor,
                    feedparser.parse,
                    content
                )
                
                fetch_time = time.time() - start_time
                
                return {
                    'feed': feed,
                    'url': feed_url,
                    'fetch_time_ms': int(fetch_time * 1000),
                    'entry_count': len(feed.entries)
                }
                
        except asyncio.TimeoutError:
            logger.error(f'Timeout fetching feed: {feed_url}')
            return None
        except Exception as e:
            logger.error(f'Error fetching feed {feed_url}: {e}')
            return None


# =============================================================================
# ARTICLE PROCESSOR
# =============================================================================

class ArticleProcessor:
    """
    Process RSS entries into articles and store in Cosmos DB.
    """
    
    def __init__(self, cosmos_client: CosmosClient, database_name: str):
        self.database = cosmos_client.get_database_client(database_name)
        self.articles_container = self.database.get_container_client('raw_articles')
        self.openai_client = None
        
        if OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f'OpenAI client init failed: {e}')
    
    def generate_article_id(self, source_id: str, url: str, published_at: datetime) -> str:
        """Generate unique article ID"""
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        date_str = published_at.strftime('%Y%m%d_%H%M%S')
        return f'{source_id}_{date_str}_{url_hash}'
    
    def clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        import re
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
            logger.warning(f'Embedding generation failed: {e}')
            return None
    
    def categorize(self, title: str, description: str, url: str) -> str:
        """Simple category detection"""
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
    
    async def process_entry(
        self,
        entry,
        feed_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process a single feed entry into an article"""
        try:
            title = self.clean_html(entry.get('title', ''))
            if not title:
                return None
            
            description = self.clean_html(
                entry.get('description', '') or entry.get('summary', '')
            )
            url = entry.get('link', '')
            
            if not url:
                return None
            
            if self.is_spam(title, description, url):
                logger.debug(f'Filtered spam: {title[:50]}...')
                return None
            
            published_at = self.parse_date(entry)
            
            # Generate embedding for semantic clustering
            embedding = self.generate_embedding(title, description)
            
            # Build article document
            article = {
                'id': self.generate_article_id(
                    feed_config['source_id'],
                    url,
                    published_at
                ),
                'source': feed_config['source_id'],
                'source_url': feed_config['url'],
                'source_tier': feed_config.get('tier', 2),
                'article_url': url,
                'title': title,
                'description': description,
                'published_at': published_at.isoformat(),
                'published_date': published_at.strftime('%Y-%m-%d'),
                'fetched_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'category': feed_config.get('category') or self.categorize(title, description, url),
                'embedding': embedding,
                'processed': False,
                'processing_attempts': 0
            }
            
            return article
            
        except Exception as e:
            logger.error(f'Error processing entry: {e}')
            return None
    
    async def store_article(self, article: Dict[str, Any]) -> bool:
        """Store article in Cosmos DB (upsert)"""
        try:
            self.articles_container.upsert_item(article)
            return True
        except Exception as e:
            logger.error(f'Error storing article {article.get("id")}: {e}')
            return False


# =============================================================================
# QUEUE WORKER
# =============================================================================

class QueueWorker:
    """
    Main worker that consumes feed URLs from Service Bus queue
    and processes them reliably.
    """
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            threshold=CIRCUIT_BREAKER_THRESHOLD,
            timeout_minutes=CIRCUIT_BREAKER_TIMEOUT_MINUTES
        )
        self.fetcher = RSSFetcher(timeout=FEED_TIMEOUT_SECONDS)
        self.processor: Optional[ArticleProcessor] = None
        self.servicebus_client: Optional[ServiceBusClient] = None
        self.is_running = False
        self.stats = {
            'feeds_processed': 0,
            'articles_stored': 0,
            'errors': 0,
            'circuit_breaks': 0,
            'start_time': None
        }
    
    async def start(self):
        """Initialize connections"""
        logger.info('Starting RSS Worker...')
        
        # Initialize Cosmos DB
        cosmos_client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
        self.processor = ArticleProcessor(cosmos_client, COSMOS_DATABASE_NAME)
        
        # Initialize Service Bus
        self.servicebus_client = ServiceBusClient.from_connection_string(
            SERVICE_BUS_CONNECTION_STRING
        )
        
        # Initialize HTTP session
        await self.fetcher.start()
        
        self.stats['start_time'] = datetime.now(timezone.utc).isoformat()
        self.is_running = True
        logger.info('RSS Worker started successfully')
    
    async def stop(self):
        """Clean shutdown"""
        logger.info('Stopping RSS Worker...')
        self.is_running = False
        
        await self.fetcher.stop()
        
        if self.servicebus_client:
            await self.servicebus_client.close()
        
        logger.info('RSS Worker stopped')
    
    async def process_message(self, message_body: str) -> bool:
        """
        Process a single queue message containing feed configuration.
        Returns True if processed successfully.
        """
        try:
            feed_config = json.loads(message_body)
            feed_id = feed_config.get('id', feed_config.get('url', 'unknown'))
            feed_url = feed_config.get('url')
            
            if not feed_url:
                logger.error(f'Invalid message - no URL: {message_body}')
                return False
            
            # Check circuit breaker
            if not await self.circuit_breaker.should_allow(feed_id):
                logger.debug(f'Circuit open, skipping: {feed_id}')
                self.stats['circuit_breaks'] += 1
                return True  # Don't retry, circuit is open
            
            # Fetch feed
            result = await self.fetcher.fetch_feed(feed_url)
            
            if not result:
                await self.circuit_breaker.record_failure(feed_id)
                self.stats['errors'] += 1
                return False
            
            # Process entries
            feed = result['feed']
            articles_stored = 0
            
            for entry in feed.entries:
                article = await self.processor.process_entry(entry, feed_config)
                if article:
                    if await self.processor.store_article(article):
                        articles_stored += 1
            
            # Record success
            await self.circuit_breaker.record_success(feed_id)
            self.stats['feeds_processed'] += 1
            self.stats['articles_stored'] += articles_stored
            
            logger.info(
                f'Processed {feed_config.get("name", feed_url)}: '
                f'{articles_stored}/{result["entry_count"]} articles, '
                f'{result["fetch_time_ms"]}ms'
            )
            
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f'Invalid JSON in message: {e}')
            return False
        except Exception as e:
            logger.error(f'Error processing message: {e}')
            self.stats['errors'] += 1
            return False
    
    async def run(self):
        """Main worker loop - consume messages from queue"""
        await self.start()
        
        async with self.servicebus_client:
            receiver = self.servicebus_client.get_queue_receiver(
                queue_name=SERVICE_BUS_QUEUE_NAME,
                max_wait_time=5  # Poll every 5 seconds if no messages
            )
            
            async with receiver:
                logger.info(f'Listening on queue: {SERVICE_BUS_QUEUE_NAME}')
                
                while self.is_running:
                    try:
                        # Receive batch of messages
                        messages = await receiver.receive_messages(
                            max_message_count=MAX_CONCURRENT_FEEDS,
                            max_wait_time=5
                        )
                        
                        if not messages:
                            continue
                        
                        # Process messages concurrently
                        tasks = []
                        for message in messages:
                            body = str(message)
                            tasks.append(self.process_message(body))
                        
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # Complete or dead-letter messages
                        for message, result in zip(messages, results):
                            if isinstance(result, Exception):
                                logger.error(f'Message processing exception: {result}')
                                await receiver.dead_letter_message(
                                    message,
                                    reason='ProcessingException',
                                    error_description=str(result)
                                )
                            elif result:
                                await receiver.complete_message(message)
                            else:
                                # Processing failed, will be retried
                                await receiver.abandon_message(message)
                        
                    except Exception as e:
                        logger.error(f'Error in worker loop: {e}')
                        await asyncio.sleep(1)
        
        await self.stop()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        return {
            **self.stats,
            'circuit_breaker': self.circuit_breaker.get_status(),
            'is_running': self.is_running
        }


# =============================================================================
# HEALTH API
# =============================================================================

worker = QueueWorker()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Start worker in background
    asyncio.create_task(worker.run())
    yield
    # Shutdown
    await worker.stop()

app = FastAPI(
    title='Newsreel RSS Worker',
    description='Always-on RSS feed ingestion worker',
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
    
    return HealthResponse(
        status='healthy' if worker.is_running else 'unhealthy',
        uptime_seconds=uptime,
        stats=stats
    )


@app.get('/stats')
async def get_stats():
    """Detailed statistics endpoint"""
    return worker.get_stats()


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
    logger.info(f'Received signal {signum}, shutting down...')
    worker.is_running = False


if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    
    # Validate configuration
    if not SERVICE_BUS_CONNECTION_STRING:
        logger.error('SERVICE_BUS_CONNECTION_STRING not set')
        sys.exit(1)
    
    if not COSMOS_CONNECTION_STRING:
        logger.error('COSMOS_CONNECTION_STRING not set')
        sys.exit(1)
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8080,
        log_level='info'
    )

