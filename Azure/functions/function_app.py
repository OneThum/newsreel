"""
Newsreel Azure Functions
All functions in a single file for Azure Functions Python V2 model
"""
import azure.functions as func
import logging
import asyncio
import aiohttp
import feedparser
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import time
import traceback

# Import shared modules
from shared.config import config
from shared.cosmos_client import cosmos_client
from shared.models import (
    RawArticle, StoryCluster, StoryStatus, Entity,
    VersionHistory, SummaryVersion
)
from shared.rss_feeds import get_initial_feeds, get_all_feeds
from shared.utils import (
    generate_article_id, generate_story_fingerprint,
    generate_event_fingerprint, extract_simple_entities,
    categorize_article, clean_html, truncate_text,
    calculate_text_similarity, is_spam_or_promotional
)

# Try to import Anthropic
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

# Import structured logger
from shared.logger import get_logger

logger = get_logger(__name__)
app = func.FunctionApp()

# ============================================================================
# PUSH NOTIFICATION SERVICE
# ============================================================================

class FCMNotificationService:
    """Firebase Cloud Messaging service for push notifications"""
    
    def __init__(self):
        self.fcm_server_key = config.FCM_SERVER_KEY if hasattr(config, 'FCM_SERVER_KEY') else None
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
    
    async def send_breaking_news_notification(
        self,
        fcm_tokens: List[str],
        story: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send breaking news push notification via FCM
        
        Args:
            fcm_tokens: List of FCM device tokens
            story: Story cluster dictionary
            
        Returns:
            dict: Results summary
        """
        if not self.fcm_server_key:
            logger.warning("⚠️  FCM_SERVER_KEY not configured, skipping push notifications")
            return {"success": 0, "failure": 0, "error": "FCM not configured"}
        
        if not fcm_tokens:
            return {"success": 0, "failure": 0, "error": "No FCM tokens"}
        
        # Prepare notification payload
        title = "🚨 BREAKING NEWS"
        body = story.get('title', 'Breaking news story')[:150]  # Truncate for notification
        
        source_count = len(story.get('source_articles', []))
        if source_count > 1:
            body = f"{body} ({source_count} sources)"
        
        notification_data = {
            "notification": {
                "title": title,
                "body": body,
                "sound": "default",
                "badge": 1,
                "priority": "high"
            },
            "data": {
                "storyId": story['id'],
                "category": story.get('category', ''),
                "priority": "breaking",
                "sourceCount": str(source_count)
            },
            "priority": "high",
            "content_available": True
        }
        
        success_count = 0
        failure_count = 0
        
        # Send to each token
        async with aiohttp.ClientSession() as session:
            for token in fcm_tokens:
                try:
                    payload = {
                        **notification_data,
                        "to": token
                    }
                    
                    headers = {
                        "Authorization": f"Bearer {self.fcm_server_key}",
                        "Content-Type": "application/json"
                    }
                    
                    async with session.post(
                        self.fcm_url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            success_count += 1
                            logger.info(f"✅ FCM notification sent successfully to token: {token[:20]}...")
                        else:
                            failure_count += 1
                            error_text = await response.text()
                            logger.error(f"❌ FCM notification failed: {response.status} - {error_text}")
                            
                except Exception as e:
                    failure_count += 1
                    logger.error(f"❌ Failed to send FCM notification: {e}")
        
        return {
            "success": success_count,
            "failure": failure_count,
            "total_tokens": len(fcm_tokens)
        }

# Initialize FCM service
fcm_service = FCMNotificationService()


# ============================================================================
# CLUSTERING HELPER FUNCTIONS
# ============================================================================

def has_topic_conflict(title1: str, title2: str) -> bool:
    """
    Detect if two titles are about fundamentally different topics
    
    Prevents false clustering of unrelated stories that happen to share
    location words (e.g., "Sydney dentist" vs "Sydney stabbing")
    """
    # Define mutually exclusive topic keywords
    topic_groups = {
        'crime_violence': {'stabbed', 'stabbing', 'murder', 'killed', 'shooting', 'attack', 'assault', 'robbery', 'theft', 'arrested'},
        'medical_health': {'dentist', 'doctor', 'hospital', 'patient', 'disease', 'virus', 'hiv', 'covid', 'surgery', 'medical', 'health'},
        'politics': {'election', 'vote', 'parliament', 'government', 'president', 'prime minister', 'senator', 'legislation', 'policy'},
        'sports': {'game', 'match', 'team', 'player', 'scored', 'championship', 'league', 'tournament', 'olympic'},
        'business': {'stock', 'market', 'earnings', 'profit', 'ceo', 'company', 'merger', 'acquisition', 'investor'},
        'weather': {'storm', 'hurricane', 'flood', 'earthquake', 'tornado', 'weather', 'forecast', 'climate'},
        'entertainment': {'movie', 'film', 'actor', 'actress', 'concert', 'album', 'celebrity', 'award', 'premiere'},
    }
    
    t1_lower = title1.lower()
    t2_lower = title2.lower()
    
    # Find which topic groups each title belongs to
    t1_topics = set()
    t2_topics = set()
    
    for topic_name, keywords in topic_groups.items():
        if any(keyword in t1_lower for keyword in keywords):
            t1_topics.add(topic_name)
        if any(keyword in t2_lower for keyword in keywords):
            t2_topics.add(topic_name)
    
    # If both titles have topics and they don't overlap, it's a conflict
    if t1_topics and t2_topics and not t1_topics.intersection(t2_topics):
        return True
    
    return False


# ============================================================================
# HEADLINE GENERATION HELPER
# ============================================================================

async def generate_updated_headline(story: Dict[str, Any], source_articles: List[Dict[str, Any]], new_article: RawArticle) -> str:
    """
    Re-evaluate headline when a new source is added to a story cluster.
    AI determines if the new source contains material warranting a headline update.
    
    Default: Keep current headline unless new source has significant new information.
    
    Headlines evolve as breaking news develops:
    - Initial report: "Explosion reported in Tennessee"
    - New detail: "18 missing after Tennessee explosives plant blast"
    - Update: "No survivors found in Tennessee explosives factory blast"
    """
    try:
        # Initialize Anthropic client
        if not Anthropic or not config.ANTHROPIC_API_KEY:
            logger.warning("Anthropic not configured, keeping original headline")
            return story.get('title', '')
        
        anthropic_client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        
        # Get current headline
        current_headline = story.get('title', '')
        
        # Get the NEW source's headline and details
        new_source_name = new_article.source
        new_source_headline = new_article.title
        new_source_description = new_article.description or ''
        
        # Gather all source headlines for context
        all_source_headlines = []
        for art_id in source_articles[:10]:  # Limit to 10 most recent
            parts = art_id.split('_')
            if len(parts) >= 2:
                date_str = parts[1]
                partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                article = await cosmos_client.get_raw_article(art_id, partition_key)
                if article:
                    source_name = article.get('source', 'Unknown')
                    title = article.get('title', '')
                    if title:
                        all_source_headlines.append(f"- {source_name}: {title}")
        
        combined_headlines = "\n".join(all_source_headlines)
        source_count = len(source_articles)
        
        # Prompt for intelligent headline re-evaluation
        prompt = f"""A news story has {source_count} sources. A NEW source just arrived. Evaluate if the headline should be updated.

CURRENT HEADLINE: "{current_headline}"

NEW SOURCE ({new_source_name}):
Title: "{new_source_headline}"
Details: "{new_source_description[:200]}"

ALL {source_count} SOURCES (for context):
{combined_headlines}

TASK: Determine if the NEW source contains material information that warrants updating the headline.

Update headline ONLY IF the new source has:
✓ Significant new factual details (numbers, names, outcomes, locations)
✓ Breaking developments that change the story
✓ More specific or accurate information than current headline
✓ Contradicts or refines information in current headline
✓ Current headline has source-specific artifacts (e.g., "| Special Report", "| BREAKING", "- Live") that should be removed

KEEP current headline if new source:
✗ Repeats information already in current headline
✗ Adds only minor or peripheral details
✗ Provides commentary without new facts
✗ Is essentially the same story from a different angle

CRITICAL: Always remove source-specific editorial tags like:
- "| Special Report" (CBS branding)
- "| BREAKING" (editorial tags)
- "- Live" or "- Update" (time-specific tags)
- "| Analysis" or "| Opinion" (content type tags)
- Network/outlet branding suffixes

Headlines should be FACTUAL, NEUTRAL, and FREE of source-specific formatting.

RESPONSE FORMAT:
If update needed: Write the improved headline (8-15 words, specific, clear, NO editorial tags)
If no update needed: Write exactly "KEEP_CURRENT"

Your response:"""

        system_prompt = """You are a senior news editor evaluating whether new sources warrant headline updates. Your decisions are:
- CONSERVATIVE: Default to keeping current headline unless new source has material new information
- FACTUAL: Only update for concrete new facts, not opinions or commentary
- SPECIFIC: Updated headlines must include concrete details (numbers, names, outcomes, locations)
- CLEAR: Headlines must be immediately comprehensible (8-15 words)
- CURRENT: Prioritize the most recent, verified developments
- NEUTRAL: Remove ALL source-specific editorial tags (e.g., "| Special Report", "| BREAKING", "- Live", outlet branding)
- CLEAN: Headlines should be pure factual content, suitable for any news outlet

CRITICAL: If current headline has source-specific artifacts (like "| Special Report"), you MUST update to remove them, even if the factual content is accurate.

You always respond with either an improved headline OR "KEEP_CURRENT". Never explain or refuse."""

        # Call Claude API with minimal tokens
        start_time = time.time()
        response = anthropic_client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=150,  # Allow for headline or "KEEP_CURRENT"
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Extract response
        ai_response = response.content[0].text.strip()
        generation_time_ms = int((time.time() - start_time) * 1000)
        
        # Log AI cost
        usage = response.usage
        cost = (usage.input_tokens * 3.0 + usage.output_tokens * 15.0) / 1_000_000
        
        # Check if AI decided to keep current headline
        if "KEEP_CURRENT" in ai_response.upper():
            logger.info(
                f"📰 Headline unchanged for {story['id']} - new source didn't warrant update "
                f"({generation_time_ms}ms, ${cost:.4f})"
            )
            return story['title']  # Return current headline (no change)
        
        # Clean up new headline
        updated_headline = ai_response.strip('"').strip("'").strip()
        
        # Validate headline quality
        if len(updated_headline.split()) < 4 or len(updated_headline) < 20:
            # Too short, keep original
            logger.warning(f"Generated headline too short, keeping original: '{updated_headline}'")
            return story['title']
        
        if len(updated_headline) > 200:
            # Too long, truncate
            updated_headline = updated_headline[:200].rsplit(' ', 1)[0] + '...'
        
        # Log successful headline update
        logger.info(
            f"📰 Headline updated for {story['id']}: {len(updated_headline)} chars, "
            f"{generation_time_ms}ms, ${cost:.4f} - "
            f"'{current_headline}' → '{updated_headline}'"
        )
        
        return updated_headline
        
    except Exception as e:
        logger.error(f"Failed to generate updated headline: {e}")
        # Return original headline on error
        return story.get('title', '')


# ============================================================================
# RSS INGESTION FUNCTION
# ============================================================================

class RSSFetcher:
    """RSS feed fetcher with HTTP conditional requests"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.feeds_cache: Dict[str, Dict[str, str]] = {}
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=config.RSS_TIMEOUT_SECONDS)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={'User-Agent': config.RSS_USER_AGENT}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_feed(self, feed_config) -> Optional[Dict[str, Any]]:
        """Fetch a single RSS feed"""
        try:
            headers = {}
            cache_key = feed_config.id
            
            if cache_key in self.feeds_cache:
                if self.feeds_cache[cache_key].get('etag'):
                    headers['If-None-Match'] = self.feeds_cache[cache_key]['etag']
            
            async with self.session.get(feed_config.url, headers=headers) as response:
                if response.status == 304:
                    logger.info(f"Feed {feed_config.name} not modified (304)")
                    return None
                
                if response.status != 200:
                    logger.warning(f"Feed {feed_config.name} returned status {response.status}")
                    return None
                
                if cache_key not in self.feeds_cache:
                    self.feeds_cache[cache_key] = {}
                
                if 'ETag' in response.headers:
                    self.feeds_cache[cache_key]['etag'] = response.headers['ETag']
                
                content = await response.text()
                feed = feedparser.parse(content)
                
                return {
                    'config': feed_config,
                    'feed': feed,
                    'fetched_at': datetime.now(timezone.utc)
                }
                
        except Exception as e:
            logger.error(f"Error fetching feed {feed_config.name}: {e}")
            return None
    
    async def fetch_all_feeds(self, feed_configs: List) -> List[Dict[str, Any]]:
        """Fetch all feeds in parallel"""
        semaphore = asyncio.Semaphore(config.RSS_MAX_CONCURRENT)
        
        async def fetch_with_semaphore(feed_config):
            async with semaphore:
                return await self.fetch_feed(feed_config)
        
        tasks = [fetch_with_semaphore(fc) for fc in feed_configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
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
            return datetime.now(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def normalize_category(category: str) -> str:
    """Normalize category names to match iOS app expectations"""
    category_mapping = {
        'tech': 'technology',
        'entertainment': 'entertainment',
        'sports': 'sports',
        'business': 'business',
        'health': 'health',
        'science': 'science',
        'technology': 'technology',
        'general': 'general',
        'politics': 'politics',
        'world': 'world'
    }
    return category_mapping.get(category.lower(), category)


def process_feed_entry(entry, feed_result: Dict[str, Any]) -> Optional[RawArticle]:
    """Process a single feed entry into a RawArticle"""
    try:
        feed_config = feed_result['config']
        fetched_at = feed_result['fetched_at']

        title = clean_html(entry.get('title', ''))
        if not title:
            return None

        description = clean_html(entry.get('description', '') or entry.get('summary', ''))
        article_url = entry.get('link', '')

        if not article_url:
            return None

        # Filter out spam/promotional content
        if is_spam_or_promotional(title, description, article_url):
            logger.info(f"🚫 Filtered spam/promotional content: {title[:80]}...")
            return None

        # PHASE 1: SimHash near-duplicate detection (if enabled)
        if config.CLUSTERING_USE_SIMHASH:
            from urllib.parse import urlparse

            # Extract domain for duplicate detection
            try:
                domain = urlparse(article_url).netloc
            except:
                domain = feed_config.source_id  # Fallback

            article_dict = {
                'title': title,
                'description': description,
                'source_domain': domain
            }

            # TODO: Implement hash storage and lookup for recent hashes
            # For now, we only implement the SimHash computation
            is_duplicate, duplicate_type = detect_duplicates(article_dict)

            if is_duplicate:
                logger.info(f"🔄 Filtered duplicate content ({duplicate_type}): {title[:80]}...")
                return None

        published_at = parse_entry_date(entry)
        published_date = published_at.strftime('%Y-%m-%d')

        content = None
        if hasattr(entry, 'content') and entry.content:
            content = clean_html(entry.content[0].value)
        elif description:
            content = description

        if content:
            content = truncate_text(content, max_length=2000)

        author = entry.get('author', None)
        text_for_entities = f"{title} {description}"
        entities = extract_simple_entities(text_for_entities)
        category = categorize_article(title, description, article_url)

        if category == 'general':
            category = feed_config.category

        # Normalize category to match iOS app expectations (tech -> technology)
        category = normalize_category(category)
        
        article_id = generate_article_id(feed_config.source_id, article_url, published_at)
        story_fingerprint = generate_story_fingerprint(title, entities)
        
        # Note: fetched_at is immutable (when we first saw it)
        # updated_at will be updated on each upsert
        now = datetime.now(timezone.utc)
        
        article = RawArticle(
            id=article_id,
            source=feed_config.source_id,
            source_url=feed_config.url,
            source_tier=feed_config.tier,
            article_url=article_url,
            title=title,
            description=description,
            published_at=published_at,
            fetched_at=fetched_at,  # When we first saw it (immutable)
            updated_at=now,  # When we last updated it (will be upserted)
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


@app.function_name(name="RSSIngestion")
@app.schedule(schedule="*/10 * * * * *", arg_name="timer", run_on_startup=True)
async def rss_ingestion_timer(timer: func.TimerRequest) -> None:
    """RSS Ingestion - Runs every 10 seconds with staggered feed polling
    
    This ensures continuous data flow instead of batch updates:
    - With 100 feeds over 5 minutes (300 seconds)
    - Polling ~3-4 feeds every 10 seconds (30 cycles per 5 min)
    - Results in 1 feed every 3 seconds (continuous firehose!)
    - More responsive to breaking news with 3x more frequent polling
    """
    
    with logger.operation("rss_ingestion"):
        try:
            cosmos_client.connect()
            
            # Use environment variable to switch between MVP (10 feeds) and Full (100 feeds)
            use_all_feeds = config.RSS_USE_ALL_FEEDS  # Default: False for MVP
            
            if use_all_feeds:
                all_feed_configs = get_all_feeds()
                logger.info(f"Staggered polling mode: {len(all_feed_configs)} total feeds available")
            else:
                all_feed_configs = get_initial_feeds()
                logger.info(f"Staggered polling mode: {len(all_feed_configs)} total feeds (MVP)")
            
            # Get feed poll states to determine which feeds need polling
            feed_states = await cosmos_client.get_feed_poll_states()
            now = datetime.now(timezone.utc)
            
            # Determine which feeds are ready to poll
            feeds_ready = []
            for feed_config in all_feed_configs:
                last_poll = feed_states.get(feed_config.name, {}).get('last_poll')
                
                # Poll if never polled OR if 3 minutes have passed (reduced for continuous flow)
                # 3-minute cooldown ensures overlap: 100 feeds / 3 per cycle = ~33 cycles × 10s = 330s (5.5 min)
                # Feeds become eligible at 3 min, so no silence gaps!
                if not last_poll or (now - last_poll).total_seconds() >= 180:
                    feeds_ready.append(feed_config)
            
            # Smart round-robin selection across categories to ensure even distribution
            # Group ready feeds by category
            feeds_by_category = {}
            for feed in feeds_ready:
                category = getattr(feed, 'category', 'unknown')
                if category not in feeds_by_category:
                    feeds_by_category[category] = []
                feeds_by_category[category].append(feed)
            
            # Select 3 feeds using round-robin across categories
            # This ensures we never poll 30 news sources in a row - they're evenly distributed
            max_feeds_per_cycle = 3
            feed_configs = []
            categories = list(feeds_by_category.keys())
            category_idx = 0
            
            # Round-robin through categories until we have 3 feeds
            attempts = 0
            max_attempts = len(feeds_ready) + len(categories)  # Prevent infinite loop
            
            while len(feed_configs) < max_feeds_per_cycle and attempts < max_attempts:
                if not categories:
                    break
                    
                # Get next category (round-robin)
                category = categories[category_idx % len(categories)]
                
                # Get feeds from this category
                if feeds_by_category[category]:
                    feed_configs.append(feeds_by_category[category].pop(0))
                
                # Remove category if empty
                if not feeds_by_category[category]:
                    categories.remove(category)
                    if categories and category_idx >= len(categories):
                        category_idx = 0
                else:
                    category_idx = (category_idx + 1) % len(categories)
                
                attempts += 1
            
            if not feed_configs:
                logger.info("No feeds need polling this cycle")
                return
            
            logger.info(f"📰 Polling {len(feed_configs)} feeds this cycle (out of {len(feeds_ready)} ready, {len(all_feed_configs)} total)")
            
            # Log feed distribution for analysis - showing round-robin worked
            feed_categories = {}
            feed_names = []
            for feed in feed_configs:
                category = getattr(feed, 'category', 'unknown')
                feed_categories[category] = feed_categories.get(category, 0) + 1
                feed_names.append(f"{feed.name} ({category})")
            
            logger.info(f"📊 Round-robin selection: {', '.join(feed_names)}")
            logger.info(f"📊 Category distribution: {dict(feed_categories)} - evenly distributed ✓")
            
            # Log detailed polling statistics
            logger.info(f"📈 RSS Polling Statistics:")
            logger.info(f"   Total feeds configured: {len(all_feed_configs)}")
            logger.info(f"   Feeds ready this cycle: {len(feeds_ready)}")
            logger.info(f"   Categories available: {len(feeds_by_category)}")
            logger.info(f"   Feeds selected (round-robin): {len(feed_configs)}")
            logger.info(f"   Polling frequency: every 10 seconds")
            logger.info(f"   Cooldown period: 3 minutes")
            logger.info(f"   Time to poll all feeds: ~{(len(all_feed_configs) / max_feeds_per_cycle * 10) / 60:.1f} minutes")
            
            # Fetch selected feeds
            fetch_start = time.time()
            async with RSSFetcher() as fetcher:
                feed_results = await fetcher.fetch_all_feeds(feed_configs)
            fetch_duration_ms = int((time.time() - fetch_start) * 1000)
            
            total_articles = 0
            new_articles = 0
            processed_articles = 0
            skipped_articles = 0
            source_distribution = {}
            feed_performance = {}
            
            logger.info(f"📊 Processing {len(feed_results)} feed results...")
            
            for feed_result in feed_results:
                feed = feed_result['feed']
                feed_config = feed_result['config']
                
                article_count = len(feed.entries)
                feed_processed = 0
                feed_skipped = 0
                
                # Log RSS fetch with structured data
                logger.log_rss_fetch(
                    source=feed_config.name,
                    success=True,
                    article_count=article_count,
                    duration_ms=fetch_duration_ms // len(feed_results) if feed_results else 0,
                    status_code=200
                )
                
                logger.info(f"📰 Processing feed '{feed_config.name}': {article_count} articles")
                
                source_distribution[feed_config.name] = 0
                
                for entry in feed.entries:
                    total_articles += 1
                    article = process_feed_entry(entry, feed_result)
                    
                    if not article:
                        skipped_articles += 1
                        feed_skipped += 1
                        logger.debug(f"   Skipped article from {feed_config.name}: failed processing")
                        continue
                    
                    try:
                        # UPSERT: Creates new or updates existing (same source + URL)
                        # This implements update-in-place for article updates
                        result = await cosmos_client.upsert_raw_article(article)
                        if result:
                            new_articles += 1  # Note: counts both new and updated articles
                            processed_articles += 1
                            feed_processed += 1
                            source_distribution[feed_config.name] += 1
                            logger.debug(f"   Processed article: {article.id[:50]}...")
                        else:
                            logger.warning(f"   Failed to upsert article: {article.id[:50]}...")
                    except Exception as e:
                        logger.error(f"Error storing article {article.id}: {e}")
                        skipped_articles += 1
                        feed_skipped += 1
                
                # Log feed performance
                feed_performance[feed_config.name] = {
                    'total_articles': article_count,
                    'processed': feed_processed,
                    'skipped': feed_skipped,
                    'success_rate': (feed_processed / article_count * 100) if article_count > 0 else 0
                }
                
                logger.info(f"✅ Feed '{feed_config.name}' complete: {feed_processed}/{article_count} processed ({feed_performance[feed_config.name]['success_rate']:.1f}% success)")
            
            # Update feed poll states for successfully polled feeds
            poll_time = datetime.now(timezone.utc)
            for feed_config in feed_configs:
                await cosmos_client.update_feed_poll_state(
                    feed_name=feed_config.name,
                    last_poll=poll_time,
                    articles_found=source_distribution.get(feed_config.name, 0)
                )
            
            # Log source diversity
            unique_sources = len([s for s, count in source_distribution.items() if count > 0])
            active_sources = {k: v for k, v in source_distribution.items() if v > 0}
            
            logger.log_feed_diversity(
                total_stories=new_articles,
                unique_sources=unique_sources,
                source_distribution=active_sources
            )
            
            # Log comprehensive RSS ingestion summary
            logger.info(f"✅ RSS ingestion complete: {new_articles} new articles out of {total_articles} total from {unique_sources} sources (staggered polling)")
            logger.info(f"📊 RSS Ingestion Summary:")
            logger.info(f"   Total articles found: {total_articles}")
            logger.info(f"   Articles processed: {processed_articles}")
            logger.info(f"   Articles skipped: {skipped_articles}")
            logger.info(f"   New/updated articles: {new_articles}")
            logger.info(f"   Processing success rate: {(processed_articles / total_articles * 100) if total_articles > 0 else 0:.1f}%")
            logger.info(f"   Unique sources: {unique_sources}")
            logger.info(f"   Fetch duration: {fetch_duration_ms}ms")
            logger.info(f"   Feeds polled: {len(feed_configs)}")
            
            if active_sources:
                logger.info(f"📊 Active sources this cycle: {', '.join(active_sources.keys())}")
            
            # Log feed performance summary
            logger.info(f"📈 Feed Performance Summary:")
            for feed_name, perf in feed_performance.items():
                logger.info(f"   {feed_name}: {perf['processed']}/{perf['total_articles']} articles ({perf['success_rate']:.1f}% success)")
            
            # Log source distribution analysis
            if source_distribution:
                total_distributed = sum(source_distribution.values())
                logger.info(f"📊 Source Distribution Analysis:")
                logger.info(f"   Total articles distributed: {total_distributed}")
                for source, count in sorted(source_distribution.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total_distributed * 100) if total_distributed > 0 else 0
                    logger.info(f"   {source}: {count} articles ({percentage:.1f}%)")
            
        except Exception as e:
            logger.error(f"RSS ingestion failed: {e}", error=e)
            raise


# ============================================================================
# STORY CLUSTERING FUNCTION
# ============================================================================

@app.function_name(name="StoryClusteringChangeFeed")
@app.cosmos_db_trigger(
    arg_name="documents",
    database_name="%COSMOS_DATABASE_NAME%",
    container_name="raw_articles",
    connection="COSMOS_CONNECTION_STRING",
    lease_container_name="leases",
    create_lease_container_if_not_exists=True
)
async def story_clustering_changefeed(documents: func.DocumentList) -> None:
    """Story Clustering - Triggered by new articles

    Supports both legacy fingerprinting and new embedding-based clustering.
    Uses A/B testing framework for gradual rollout of Phase 2 features.
    """
    if not documents:
        return

    logger.info(f"Processing {len(documents)} documents for clustering")
    cosmos_client.connect()

    for doc in documents:
        try:
            article_data = json.loads(doc.to_json())
            logger.info(f"Processing article from raw_articles, keys: {list(article_data.keys())[:10]}")
            article = RawArticle(**article_data)

            if article.processed:
                continue

            # Phase 2: A/B Testing - Determine which clustering algorithm to use
            from .shared.ab_testing import get_clustering_config, record_clustering_metric
            clustering_config = get_clustering_config(article.id)

            logger.info(f"🎯 Clustering config for {article.id}: {clustering_config}")

            # Track clustering start time for metrics
            clustering_start_time = time.time()

            if clustering_config.get('use_embeddings', False):
                # Phase 2: Use new embedding-based clustering
                matched_story = await cluster_with_embeddings(article, clustering_config)
            else:
                # Legacy: Use original fingerprinting clustering
                matched_story = await cluster_with_fingerprints(article, clustering_config)

            # Record clustering metrics
            clustering_time_ms = int((time.time() - clustering_start_time) * 1000)
            record_clustering_metric(article.id, 'clustering_time_ms', clustering_time_ms)
            record_clustering_metric(article.id, 'matched_story', matched_story)
            record_clustering_metric(article.id, 'algorithm', clustering_config.get('algorithm', 'unknown'))

            # Process clustering result (create/update story)
            await process_clustering_result(article, matched_story, clustering_config)

        except Exception as e:
            logger.error(f"Error clustering document: {e}", exc_info=True)
            logger.error(f"Traceback: {traceback.format_exc()}")

    logger.info(f"Completed clustering {len(documents)} documents")


# ============================================================================
# CLUSTERING ALGORITHMS (Phase 2)
# ============================================================================

async def cluster_with_fingerprints(article: RawArticle, config: Dict[str, Any]) -> Optional[str]:
    """
    Legacy clustering using MD5 fingerprints + text similarity fallback

    Args:
        article: Article to cluster
        config: Clustering configuration

    Returns:
        Story ID if matched, None if new story should be created
    """
    logger.info(f"🔍 Using legacy fingerprinting clustering for {article.id}")

    # Try fingerprint matching first (fast)
    stories = await cosmos_client.query_stories_by_fingerprint(article.story_fingerprint)

    if stories:
        logger.info(f"✅ Fingerprint match found for {article.id}")
        return stories[0]['id']

    # If no match by fingerprint, try IMPROVED fuzzy title matching (fallback)
    # Query recent stories in same category for better relevance
    # Phase 1: Apply time window filtering (72 hours) if enabled
    time_window_hours = 72 if config.get('use_time_window', False) else None
    recent_stories = await cosmos_client.query_recent_stories(
        category=article.category,
        limit=500,
        time_window_hours=time_window_hours
    )

    best_match = None
    best_similarity = 0.0
    similarity_scores = []
    topic_conflicts = []
    threshold_matches = []

    logger.info(f"🔍 Fuzzy matching for article '{article.title[:80]}...' against {len(recent_stories)} recent stories in category '{article.category}'")

    # Phase 1: Calculate adaptive threshold based on article age
    from datetime import datetime
    article_age_hours = (datetime.now(timezone.utc) - article.published_at).total_seconds() / 3600
    adaptive_threshold = calculate_adaptive_threshold(article_age_hours, config.get('threshold', 0.50))

    logger.info(f"🎯 Using adaptive threshold: {adaptive_threshold:.3f} (article age: {article_age_hours:.1f}h)")

    for existing_story in recent_stories:
        title_similarity = calculate_text_similarity(article.title, existing_story.get('title', ''))
        similarity_scores.append(title_similarity)

        # Track best match for logging
        if title_similarity > best_similarity:
            best_similarity = title_similarity
            best_match = existing_story

        # Log all similarity scores above 50% for analysis
        if title_similarity > 0.50:
            logger.info(f"📊 Similarity {title_similarity:.3f}: '{article.title[:60]}...' vs '{existing_story.get('title', '')[:60]}...'")

        # Phase 1: Use adaptive threshold based on article age
        if title_similarity > adaptive_threshold:
            threshold_matches.append({
                'similarity': title_similarity,
                'story_id': existing_story.get('id', 'unknown'),
                'story_title': existing_story.get('title', '')[:80]
            })

            # Additional validation: Check for topic conflicts
            if not has_topic_conflict(article.title, existing_story.get('title', '')):
                stories = [existing_story]
                matched_story = True
                logger.info(f"✅ CLUSTERING MATCH: {title_similarity:.3f} - '{article.title[:60]}...' → '{existing_story.get('title', '')[:60]}...' (threshold: {adaptive_threshold:.3f})")
                return existing_story['id']
            else:
                topic_conflicts.append({
                    'similarity': title_similarity,
                    'story_id': existing_story.get('id', 'unknown'),
                    'story_title': existing_story.get('title', '')[:80]
                })
                logger.info(f"❌ Topic conflict prevented match: {title_similarity:.3f} - '{article.title[:60]}...' vs '{existing_story.get('title', '')[:60]}...'")

        # If still no match, try entity-based matching for near-misses (0.50-adaptive_threshold range)
        # This catches stories that are about same event but phrased differently
        if not stories and best_match and 0.50 <= best_similarity < adaptive_threshold:
            # Extract key entities from both titles
            article_entities = set(word.lower() for word in article.title.split()
                                  if len(word) > 4 and word[0].isupper())
            story_entities = set(word.lower() for word in best_match.get('title', '').split()
                                if len(word) > 4 and word[0].isupper())

            # This allows "Senate", "government shutdown" to match across different phrasings
            entity_overlap = len(article_entities.intersection(story_entities))
            if entity_overlap >= 2 and not has_topic_conflict(article.title, best_match.get('title', '')):
                logger.info(f"✓ Entity match (near-miss recovery: {entity_overlap} shared, {best_similarity:.3f} similarity): '{article.title[:60]}...' → '{best_match.get('title', '')[:60]}...'")
                return best_match['id']

    # Log comprehensive clustering analysis
    if similarity_scores:
        avg_similarity = sum(similarity_scores) / len(similarity_scores)
        max_similarity = max(similarity_scores)
        logger.info(f"📈 Clustering analysis for '{article.title[:60]}...': avg={avg_similarity:.3f}, max={max_similarity:.3f}, threshold={adaptive_threshold:.3f}")

    if threshold_matches:
        logger.info(f"🎯 Threshold matches ({len(threshold_matches)}): {[m['similarity'] for m in threshold_matches]}")

    if topic_conflicts:
        logger.info(f"⚠️ Topic conflicts ({len(topic_conflicts)}): {[c['similarity'] for c in topic_conflicts]}")

    # Log clustering decision for analysis
    logger.info(f"🎯 CLUSTERING DECISION: Creating new story (no match found)")
    logger.info(f"   Article: [{article.source}] {article.title[:80]}...")
    logger.info(f"   Best similarity: {best_similarity:.3f}")
    logger.info(f"   Threshold used: {adaptive_threshold:.3f}")

    return None  # No match found, create new story


async def cluster_with_embeddings(article: RawArticle, config: Dict[str, Any]) -> Optional[str]:
    """
    Phase 3 clustering using semantic embeddings + FAISS + BM25 + Geographic + Event features

    Multi-factor scoring system with advanced features

    Args:
        article: Article to cluster
        config: Clustering configuration

    Returns:
        Story ID if matched, None if new story should be created
    """
    logger.info(f"🚀 Using advanced embedding-based clustering for {article.id}")

    try:
        from .shared.embedding_pipeline import get_embedding_pipeline
        from .shared.clustering import assign_article_to_cluster

        # Get embedding pipeline
        pipeline = await get_embedding_pipeline()

        # Convert RawArticle to dict for processing
        article_dict = {
            'id': article.id,
            'title': article.title,
            'description': article.description,
            'published_at': article.published_at.isoformat() if article.published_at else None,
            'category': article.category,
            'entities': [{'text': e.text, 'type': e.type} for e in article.entities],
            'source': article.source,
            'story_fingerprint': article.story_fingerprint
        }

        # Generate embedding for the article
        embedding = await pipeline.embeddings_client.embed_article(
            title=article.title,
            description=article.description,
            entities=article_dict['entities']
        )

        # Get candidate clusters using hybrid search
        candidates = await pipeline.candidate_generator.find_candidates(
            article=article_dict,
            article_embedding=embedding,
            max_candidates=50  # Get more candidates for better selection
        )

        # Fetch candidate cluster details
        candidate_clusters = []
        for candidate_id in candidates[:20]:  # Limit to top 20
            try:
                cluster_data = await cosmos_client.get_story(candidate_id)
                if cluster_data:
                    candidate_clusters.append(cluster_data)
            except Exception as e:
                logger.warning(f"Failed to fetch cluster {candidate_id}: {e}")

        # Use multi-factor scoring to assign to best cluster
        assigned_cluster_id, assignment_metadata = assign_article_to_cluster(
            article=article_dict,
            candidates=candidate_clusters,
            article_embedding=embedding
        )

        if assigned_cluster_id:
            logger.info(f"✅ Advanced clustering match: {assignment_metadata.get('score', 0):.3f} "
                       f"score with cluster {assigned_cluster_id}")
            logger.info(f"   Components: {assignment_metadata.get('components', {})}")
            return assigned_cluster_id
        else:
            reason = assignment_metadata.get('reason', 'unknown')
            logger.info(f"🎯 No suitable cluster found ({reason}), creating new story")
            logger.info(f"   Best score: {assignment_metadata.get('best_score', 0):.3f}, "
                       f"Threshold: {assignment_metadata.get('threshold', 0):.3f}")
            return None

    except Exception as e:
        logger.error(f"Advanced embedding clustering failed, falling back to legacy: {e}")
        # Fallback to legacy clustering
        return await cluster_with_fingerprints(article, config)


async def process_clustering_result(article: RawArticle, matched_story_id: Optional[str], config: Dict[str, Any]):
    """
    Process the result of clustering (create new story or update existing)

    Args:
        article: The article that was clustered
        matched_story_id: ID of matched story, or None for new story
        config: Clustering configuration
    """
    try:
        if matched_story_id:
            # Update existing story
            story = await cosmos_client.get_story(matched_story_id)
            if story:
                # Update story with new article (reuse existing logic)
                await update_story_with_article(story, article)
            else:
                logger.error(f"Matched story {matched_story_id} not found, creating new story")
                matched_story_id = None

        if not matched_story_id:
            # Create new story
            story_id = await create_new_story(article, config)
            matched_story_id = story_id

        # Mark article as processed
        await cosmos_client.update_article_processed(article.id, article.published_date, matched_story_id)

    except Exception as e:
        logger.error(f"Error processing clustering result: {e}")
        # Still mark as processed to avoid infinite retries
        await cosmos_client.update_article_processed(article.id, article.published_date, None)


async def update_story_with_article(story: Dict[str, Any], article: RawArticle):
    """Update existing story with new article (extracted from original logic)"""
    # Reuse existing story update logic from original function
    source_articles = story.get('source_articles', [])

    # Check if article already in story
    if article.id in source_articles:
        logger.info(f"Article {article.id} already in story {story['id']} - skipping duplicate")
        return

    # Check for duplicate sources
    existing_sources = set()
    for existing_art in source_articles:
        if isinstance(existing_art, dict):
            existing_source = existing_art.get('source', existing_art.get('id', '').split('_')[0])
        else:
            existing_source = existing_art.split('_')[0]
        existing_sources.add(existing_source)

    new_source = article.id.split('_')[0]
    if new_source in existing_sources:
        logger.info(f"Source {new_source} already in story {story['id']} - skipping duplicate source")
        return

    # Add article to story
    source_articles.append({
        "id": article.id,
        "source": article.source,
        "title": article.title,
        "url": article.article_url,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "content": article.content or article.description
    })

    # Update story metadata
    story['last_updated'] = datetime.now(timezone.utc).isoformat()
    story['source_articles'] = source_articles

    # Update in database
    await cosmos_client.upsert_story_cluster(story)


async def create_new_story(article: RawArticle, config: Dict[str, Any]) -> str:
    """Create new story cluster (extracted from original logic)"""
    from .shared.utils import categorize_article, generate_event_fingerprint

    story_id = str(uuid.uuid4())

    # Generate story title (use article title)
    story_title = article.title

    # Categorize
    category = article.category or categorize_article(article.title, article.description or "", article.article_url)

    # Create story object
    now = datetime.now(timezone.utc)
    story = {
        'id': story_id,
        'title': story_title,
        'category': category,
        'status': 'MONITORING',  # Start as monitoring, will upgrade based on sources
        'first_seen': now.isoformat(),
        'last_updated': now.isoformat(),
        'source_articles': [{
            "id": article.id,
            "source": article.source,
            "title": article.title,
            "url": article.article_url,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "content": article.content or article.description
        }],
        'entity_histogram': {},  # Will be populated by summarization
        'embedding': None,  # Will be computed later
        'summary': None,
        'breaking_news': False,
        'event_signature': None
    }

    # Save to database
    await cosmos_client.upsert_story_cluster(story)

    logger.info(f"🆕 Created new story {story_id}: '{story_title[:80]}...'")

    return story_id


# ============================================================================
# CLUSTER MAINTENANCE FUNCTION (Phase 3)
# ============================================================================

@app.function_name(name="ClusterMaintenance")
@app.timer_trigger(schedule="0 */6 * * * *", arg_name="timer", run_on_startup=False)  # Every 6 hours
async def cluster_maintenance_timer(timer: func.TimerRequest) -> None:
    """
    Cluster Maintenance - Phase 3 Clustering Overhaul

    Automatically maintains cluster quality by:
    - Merging similar clusters
    - Splitting divergent clusters
    - Decaying/archiving old clusters

    Runs every 6 hours to ensure ongoing clustering accuracy.
    """
    if not config.CLUSTER_MAINTENANCE_ENABLED:
        logger.info("Cluster maintenance disabled, skipping")
        return

    logger.info("🛠️ Starting cluster maintenance cycle")

    try:
        cosmos_client.connect()

        # Query active clusters for maintenance
        active_clusters = await cosmos_client.query_recent_stories(
            limit=config.CLUSTER_MAINTENANCE_MAX_CLUSTERS
        )

        if not active_clusters:
            logger.info("No active clusters found for maintenance")
            return

        logger.info(f"Processing {len(active_clusters)} clusters for maintenance")

        # Perform cluster maintenance
        from .shared.cluster_maintenance import perform_cluster_maintenance

        maintenance_results = perform_cluster_maintenance(
            active_clusters,
            max_clusters=config.CLUSTER_MAINTENANCE_MAX_CLUSTERS
        )

        # Log results
        logger.info("📊 Cluster maintenance results:")
        logger.info(f"   • Merges performed: {len(maintenance_results['merges'])}")
        logger.info(f"   • Splits performed: {len(maintenance_results['splits'])}")
        logger.info(f"   • Clusters decayed: {len(maintenance_results['decayed'])}")
        logger.info(f"   • Processing time: {maintenance_results['duration_seconds']:.1f}s")

        # Process merges
        for cluster1_id, cluster2_id, merged_id in maintenance_results['merges']:
            logger.info(f"🔗 Merged clusters: {cluster1_id} + {cluster2_id} → {merged_id}")

            # Mark original clusters as merged (would need to implement this)
            # await cosmos_client.mark_cluster_merged(cluster1_id, merged_id)
            # await cosmos_client.mark_cluster_merged(cluster2_id, merged_id)

        # Process splits
        for original_id, new_ids in maintenance_results['splits']:
            logger.info(f"✂️ Split cluster: {original_id} → {new_ids}")

            # Mark original cluster as split (would need to implement this)
            # await cosmos_client.mark_cluster_split(original_id, new_ids)

        # Process decays
        for decayed_id in maintenance_results['decayed']:
            logger.info(f"🗂️ Decayed cluster: {decayed_id}")

            # Mark cluster as decayed/archived
            # await cosmos_client.mark_cluster_decayed(decayed_id)

        # Record maintenance metrics
        from .shared.ab_testing import record_clustering_metric
        record_clustering_metric('maintenance', 'merges_performed', len(maintenance_results['merges']), experiment_id='maintenance')
        record_clustering_metric('maintenance', 'splits_performed', len(maintenance_results['splits']), experiment_id='maintenance')
        record_clustering_metric('maintenance', 'clusters_decayed', len(maintenance_results['decayed']), experiment_id='maintenance')

    except Exception as e:
        logger.error(f"Cluster maintenance failed: {e}", exc_info=True)

        # Record error metric
        from .shared.ab_testing import record_clustering_metric
        record_clustering_metric('maintenance', 'errors', 1, experiment_id='maintenance')

    logger.info("✅ Cluster maintenance cycle completed")


# ============================================================================
# SUMMARIZATION FUNCTION
# ============================================================================

@app.function_name(name="SummarizationChangeFeed")
@app.cosmos_db_trigger(
    arg_name="documents",
    database_name="%COSMOS_DATABASE_NAME%",
    container_name="story_clusters",
    connection="COSMOS_CONNECTION_STRING",
    lease_container_name="leases-summarization",
    create_lease_container_if_not_exists=True
)
async def summarization_changefeed(documents: func.DocumentList) -> None:
    """Summarization - Triggered by story updates"""
    if not documents:
        return
    
    logger.info(f"Processing {len(documents)} stories for summarization")
    
    # Skip if no Anthropic key
    if not config.ANTHROPIC_API_KEY:
        logger.warning("Anthropic API key not configured, skipping summarization")
        return
    
    cosmos_client.connect()
    anthropic_client = Anthropic(api_key=config.ANTHROPIC_API_KEY) if Anthropic else None
    
    if not anthropic_client:
        logger.warning("Anthropic client not available")
        return
    
    for doc in documents:
        try:
            story_data = json.loads(doc.to_json())
            source_articles = story_data.get('source_articles', [])
            
            # Generate summaries for ALL stories (even single-source)
            # Skip only if no sources at all
            if len(source_articles) < 1:
                continue
            
            existing_summary = story_data.get('summary')
            
            # RE-EVALUATE SUMMARY on EVERY source addition (triggered by story_cluster changes)
            # AI will determine if new source warrants summary update
            # For stories without summaries, always generate
            # For stories with summaries, check if source count increased (new source added)
            prev_source_count = existing_summary.get('source_count', 0) if existing_summary else 0
            current_source_count = len(source_articles)
            
            # Only re-evaluate if:
            # 1. No summary exists yet (first-time generation), OR
            # 2. Source count increased (new source was added)
            if existing_summary and current_source_count <= prev_source_count:
                # No new sources since last summary, skip
                continue
            
            logger.info(
                f"📝 Summary re-evaluation triggered for {story_data['id']} "
                f"({prev_source_count}→{current_source_count} sources)"
            )
            
            # Fetch source articles
            articles = []
            for article_id in source_articles[:6]:  # Limit to 6 sources
                parts = article_id.split('_')
                if len(parts) >= 2:
                    date_str = parts[1]
                    partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    article = await cosmos_client.get_raw_article(article_id, partition_key)
                    if article:
                        articles.append(article)
            
            if not articles:
                continue
            
            # Note: We removed the content validation check
            # The refusal detection + fallback summary will handle content-less articles
            # This ensures we always try to provide SOME summary to users
            
            # Generate summary with Claude
            logger.info(f"Generating summary for story {story_data['id']} with {len(articles)} sources")
            
            # Build prompt
            article_texts = []
            for i, article in enumerate(articles[:6], 1):
                source = article.get('source', 'Unknown')
                title = article.get('title', '')
                content = article.get('content', article.get('description', ''))[:1000]
                
                article_text = f"Source {i}: {source}\nTitle: {title}\nContent: {content}"
                article_texts.append(article_text.strip())
            
            combined_articles = "\n\n---\n\n".join(article_texts)
            
            # PHASE 1: ENHANCED PROMPTS FOR QUALITY
            # Adjust prompt based on number of sources
            
            if len(articles) == 1:
                # Single-source: Extract maximum value from available content
                prompt = f"""You are a senior news editor creating a summary from a news report. Extract and present the key information clearly.

ESSENTIAL FACTS TO INCLUDE:
- What happened (the core event)
- Who is involved (people, organizations)
- When and where it occurred  
- Why it matters (significance, impact, context)
- What happens next (if mentioned)

QUALITY STANDARDS:
- Include ALL specific details available: numbers, dates, names, locations, quotes
- Use clear, direct language that intelligent readers can understand
- Write 80-120 words (concise but complete)
- Lead with the most important information
- Maintain neutral, factual tone

YOU MUST provide a summary based on what IS available. Never refuse or say you need more sources.

Article to summarize:

{combined_articles}

Write a clear, factual summary that gives readers confidence they understand this story:"""
            
            else:
                # Multi-source: Synthesize perspectives for comprehensive view
                prompt = f"""You are a senior news editor synthesizing {len(articles)} reports about the same event. Create a comprehensive summary that shows readers the full picture from multiple perspectives.

ESSENTIAL FACTS TO INCLUDE:
- What happened (the core event)  
- Who is involved (key people, organizations)
- When and where it occurred
- Why it matters (significance, impact, broader context)
- What happens next (if known)

SYNTHESIS REQUIREMENTS:
- Identify facts reported by MULTIPLE sources (high confidence - state these directly)
- Note facts from single sources (lower confidence - attribute: "According to [Source]...")
- Highlight any conflicting information or different framings between sources
- Show how different sources emphasize different aspects of the story

QUALITY STANDARDS:
- Include specific details: numbers, dates, direct quotes, locations
- Use clear, accessible language (write for intelligent readers, not specialists)
- Write 120-150 words (comprehensive but scannable)
- Lead with the most important information
- Present multiple perspectives fairly

Articles to summarize:

{combined_articles}

Write a comprehensive summary that gives readers confidence they understand the full story from multiple angles:"""
            
            # Enhanced system prompt emphasizing quality and trustworthiness
            system_prompt = """You are a senior news editor known for creating trustworthy, comprehensive summaries. Your summaries help readers understand complex events quickly while maintaining journalistic standards.

Core principles:
- ACCURACY: Every fact must come from the provided sources. Never speculate or add information.
- COMPLETENESS: Include all key information (who, what, when, where, why, impact)
- PERSPECTIVE: For multi-source stories, show how different sources frame the event
- CLARITY: Write for intelligent readers using clear, direct language
- TRUSTWORTHINESS: Readers rely on you to be their eyes and ears across multiple sources

You ALWAYS provide a summary based on available information, even if limited. You never refuse or say you need more sources."""
            
            # Call Claude API
            start_time = time.time()
            response = anthropic_client.messages.create(
                model=config.ANTHROPIC_MODEL,
                max_tokens=config.ANTHROPIC_MAX_TOKENS,
                system=[{
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }],
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Extract summary
            summary_text = response.content[0].text.strip()
            generation_time_ms = int((time.time() - start_time) * 1000)
            
            # CRITICAL: Validate - if Claude refused, generate fallback summary
            refusal_indicators = [
                "i cannot", "cannot create", "cannot provide", "insufficient",
                "would need", "please provide", "unable to", "not possible",
                "requires additional", "incomplete information", "lacks essential",
                "based on the provided information", "source contains only", "null content",
                "no actual article", "guidelines specify"
            ]
            
            if any(indicator in summary_text.lower() for indicator in refusal_indicators):
                logger.warning(f"Claude refused to summarize story {story_data['id']}, generating fallback")
                
                # Fallback: Generate basic summary from title and available info
                story_title = story_data.get('title', '')
                first_article = articles[0]
                description = first_article.get('description', first_article.get('content', ''))[:300]
                source = first_article.get('source', 'News sources')
                
                if len(articles) == 1:
                    summary_text = f"{story_title}. According to {source}, {description}"
                else:
                    source_names = [a.get('source', '') for a in articles[:3]]
                    sources_text = ", ".join(source_names)
                    summary_text = f"{story_title}. Multiple sources including {sources_text} are reporting on this developing story. {description}"
                
                # Clean up and truncate
                summary_text = summary_text.replace('\n', ' ').strip()
                words = summary_text.split()[:100]  # Max 100 words for fallback
                summary_text = ' '.join(words)
                
                logger.info(f"Generated fallback summary ({len(summary_text.split())} words)")
            
            word_count = len(summary_text.split())
            
            # Get token usage
            usage = response.usage
            prompt_tokens = usage.input_tokens
            completion_tokens = usage.output_tokens
            cached_tokens = getattr(usage, 'cache_read_input_tokens', 0)
            
            # Calculate cost (Claude Haiku 4.5 pricing)
            # Input: $1/MTok, Cache read: $0.10/MTok, Output: $5/MTok
            input_cost = (prompt_tokens - cached_tokens) * 1.0 / 1_000_000
            cache_cost = cached_tokens * 0.10 / 1_000_000
            output_cost = completion_tokens * 5.0 / 1_000_000
            total_cost = input_cost + cache_cost + output_cost
            
            version = 1
            if existing_summary:
                version = existing_summary.get('version', 0) + 1
            
            # Create summary object
            summary = {
                'version': version,
                'text': summary_text,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'model': config.ANTHROPIC_MODEL,
                'word_count': word_count,
                'generation_time_ms': generation_time_ms,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'cached_tokens': cached_tokens,
                'cost_usd': round(total_cost, 6),
                'source_count': current_source_count  # Track source count for re-evaluation logic
            }
            
            # Update story with summary
            # NOTE: Do NOT update last_updated - that should only change when sources are added!
            # Updating last_updated here makes old stories appear as "Just now"
            await cosmos_client.update_story_cluster(
                story_data['id'],
                story_data['category'],
                {'summary': summary}
            )
            
            # Log summary generation with structured data
            logger.log_summary_generated(
                story_id=story_data['id'],
                source_count=len(source_articles),
                word_count=word_count,
                duration_ms=generation_time_ms,
                model=config.ANTHROPIC_MODEL
            )
            logger.info(f"Generated summary v{version}: {word_count} words, {generation_time_ms}ms, ${total_cost:.4f}, cached={cached_tokens} tokens")
            
        except Exception as e:
            logger.error(f"Error summarizing story: {e}")
    
    logger.info(f"Completed summarization check for {len(documents)} stories")


# ============================================================================
# SUMMARIZATION BACKFILL (Timer-triggered)
# ============================================================================

@app.function_name(name="SummarizationBackfill")
@app.schedule(schedule="0 */10 * * * *", arg_name="timer", run_on_startup=False)
async def summarization_backfill_timer(timer: func.TimerRequest) -> None:
    """
    Summarization Backfill - Runs every 10 minutes
    Finds stories without summaries and generates them
    
    BUDGET CONTROL: Disabled by default to save costs.
    Set SUMMARIZATION_BACKFILL_ENABLED=true to enable.
    Focus on NEW stories via changefeed instead.
    """
    logger.info("Summarization backfill triggered")
    
    # Budget control: Check if backfill is enabled
    if not config.SUMMARIZATION_BACKFILL_ENABLED:
        logger.info("Backfill disabled (budget control). Set SUMMARIZATION_BACKFILL_ENABLED=true to enable.")
        return
    
    if not config.ANTHROPIC_API_KEY:
        logger.warning("Anthropic API key not configured, skipping summarization backfill")
        return
    
    try:
        cosmos_client.connect()
        anthropic_client = Anthropic(api_key=config.ANTHROPIC_API_KEY) if Anthropic else None
        
        if not anthropic_client:
            logger.warning("Anthropic client not available")
            return
        
        # Query stories without summaries (now includes single-source stories)
        # Prioritize recent stories first for better user experience
        # Only process stories from the last 48 hours to avoid wasting budget on old stories
        # TODO: Reduce back to 4 hours once backlog is cleared
        forty_eight_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat(timespec='seconds') + 'Z'
        
        query = f"""
        SELECT * FROM c 
        WHERE (NOT IS_DEFINED(c.summary) OR c.summary = null OR c.summary.text = null OR c.summary.text = '')
        AND ARRAY_LENGTH(c.source_articles) >= 1
        AND c.status != 'MONITORING'
        AND c.last_updated >= '{forty_eight_hours_ago}'
        ORDER BY c.last_updated DESC
        OFFSET 0 LIMIT 50
        """
        
        stories = list(cosmos_client.story_clusters_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        logger.info(f"Found {len(stories)} recent stories (last 48 hours) needing summaries")
        
        if not stories:
            logger.info("No recent stories need summarization at this time")
            return
        
        summaries_generated = 0
        
        for story_data in stories:
            try:
                story_id = story_data['id']
                category = story_data.get('category', 'general')
                source_articles = story_data.get('source_articles', [])
                
                # Fetch source articles (limit to 6 for efficiency)
                articles = []
                for article_id in source_articles[:6]:
                    parts = article_id.split('_')
                    if len(parts) >= 2:
                        date_str = parts[1]
                        partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                        article = await cosmos_client.get_raw_article(article_id, partition_key)
                        if article:
                            articles.append(article)
                
                if not articles:
                    logger.warning(f"Could not fetch articles for story {story_id}")
                    continue
                
                logger.info(f"Generating summary for story {story_id} with {len(articles)} sources")
                
                # Build prompt (same as change feed function)
                article_texts = []
                for i, article in enumerate(articles, 1):
                    source = article.get('source', 'Unknown')
                    title = article.get('title', '')
                    description = article.get('description', '')
                    content = article.get('content', description)
                    
                    article_text = f"""Source {i}: {source}
Title: {title}
Content: {content[:1000]}"""
                    article_texts.append(article_text.strip())
                
                combined_articles = "\n\n---\n\n".join(article_texts)
                
                # Adjust prompt based on number of sources
                if len(articles) == 1:
                    prompt = f"""You are a news summarization AI. Create a factual, neutral summary from the provided news article.

Guidelines:
1. Write in third person, present or past tense
2. Extract the key facts: what happened, who, when, where
3. Include specific numbers, dates, locations, names if available
4. Keep it concise: 80-120 words
5. Focus on the core story
6. Use ONLY the information provided - do NOT refuse or say you need more sources
7. If details are limited, summarize what IS available

Article to summarize:

{combined_articles}

Write a factual summary of the key information provided:"""
                    system_msg = "You are a professional news summarizer. You ALWAYS provide a summary based on available information, even if limited. You never refuse."
                else:
                    prompt = f"""You are a news summarization AI. Create a factual, neutral summary synthesizing information from {len(articles)} news sources.

Guidelines:
1. Write in third person, present or past tense
2. Synthesize facts from all sources
3. Include specific numbers, dates, locations, names
4. Keep it concise: 100-150 words
5. Focus on what happened, who, when, where, immediate impacts
6. Avoid speculation or opinion
7. If sources conflict, mention both perspectives

Articles to summarize:

{combined_articles}

Write a factual summary synthesizing these articles:"""
                    system_msg = "You are a professional news summarizer. You create factual, neutral summaries from news articles. You ALWAYS provide a summary based on available information."
                
                # Call Claude API
                start_time = time.time()
                response = anthropic_client.messages.create(
                    model=config.ANTHROPIC_MODEL,
                    max_tokens=300,
                    system=system_msg,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                summary_text = response.content[0].text.strip()
                
                # CRITICAL: Validate - if Claude refused, generate fallback
                refusal_indicators = [
                    "i cannot", "cannot create", "cannot provide", "insufficient",
                    "would need", "please provide", "unable to", "not possible",
                    "requires additional", "incomplete information", "lacks essential"
                ]
                
                if any(indicator in summary_text.lower() for indicator in refusal_indicators):
                    logger.warning(f"Claude refused (backfill), generating fallback for story {story_id}")
                    
                    # Fallback summary
                    story_title = story_data.get('title', '')
                    first_article = articles[0]
                    description = first_article.get('description', first_article.get('content', ''))[:300]
                    source = first_article.get('source', 'News sources')
                    
                    if len(articles) == 1:
                        summary_text = f"{story_title}. According to {source}, {description}"
                    else:
                        source_names = [a.get('source', '') for a in articles[:3]]
                        sources_text = ", ".join(source_names)
                        summary_text = f"{story_title}. Multiple sources including {sources_text} are reporting on this story. {description}"
                    
                    summary_text = summary_text.replace('\n', ' ').strip()
                    summary_text = ' '.join(summary_text.split()[:100])
                    logger.info(f"Generated fallback summary ({len(summary_text.split())} words)")
                generation_time_ms = int((time.time() - start_time) * 1000)
                word_count = len(summary_text.split())
                
                # Create summary object
                summary = {
                    'version': 1,
                    'text': summary_text,
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                    'model': config.ANTHROPIC_MODEL,
                    'word_count': word_count,
                    'generation_time_ms': generation_time_ms,
                    'source_count': len(source_articles)
                }
                
                # Update story with summary
                # NOTE: Do NOT update last_updated - that should only change when sources are added!
                # This is backfill, so these are old stories - don't make them appear fresh!
                await cosmos_client.update_story_cluster(story_id, category, {
                    'summary': summary
                })
                
                logger.info(f"✅ Generated summary for {story_id}: {word_count} words in {generation_time_ms}ms")
                summaries_generated += 1
                
            except Exception as e:
                logger.error(f"Error backfilling summary for story: {e}")
                # Continue with next story
        
        logger.info(f"🎉 Backfill complete: generated {summaries_generated} summaries out of {len(stories)} stories processed")
        
    except Exception as e:
        logger.error(f"Summarization backfill failed: {e}", exc_info=True)


# ============================================================================
# BREAKING NEWS MONITOR
# ============================================================================

@app.function_name(name="BreakingNewsMonitor")
@app.schedule(schedule="0 */2 * * * *", arg_name="timer", run_on_startup=False)
async def breaking_news_monitor_timer(timer: func.TimerRequest) -> None:
    """
    Breaking News Monitor & Status Transition Manager - Runs every 2 minutes
    
    Responsibilities:
    1. Auto-transition BREAKING → VERIFIED after 30 minutes (time-based)
    2. Send push notifications for new breaking news
    3. Monitor and log status distribution
    """
    logger.info("Breaking news monitor & status transition manager triggered")
    
    try:
        cosmos_client.connect()
        now = datetime.now(timezone.utc)
        
        # 1. HANDLE STATUS TRANSITIONS (BREAKING → VERIFIED after 30 min)
        breaking_stories = await cosmos_client.query_stories_by_status("BREAKING", limit=100)
        
        transitions_made = 0
        notifications_sent = 0
        
        for story in breaking_stories:
            first_seen = datetime.fromisoformat(story['first_seen'].replace('Z', '+00:00'))
            time_since_first = now - first_seen
            
            # UPDATED LOGIC: Transition based on last_updated, not first_seen
            # This allows actively developing stories to stay BREAKING even if created hours ago
            last_updated_str = story.get('last_updated', story['first_seen'])
            last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
            time_since_update = now - last_updated
            
            # Check if story should transition from BREAKING to VERIFIED
            # Transition if NO NEW UPDATES for 90 minutes (story has stopped developing)
            # Extended to 90 minutes for major breaking news that develops over hours
            if time_since_update >= timedelta(minutes=90):
                # Story hasn't been updated in 30 min, transition to VERIFIED
                await cosmos_client.update_story_cluster(
                    story['id'],
                    story['category'],
                    {
                        'status': StoryStatus.VERIFIED.value,
                        'last_updated': now.isoformat()
                    }
                )
                transitions_made += 1
                age_minutes = int(time_since_first.total_seconds() / 60)
                idle_minutes = int(time_since_update.total_seconds() / 60)
                logger.info(
                    f"🔄 Status transition: {story['id']} - BREAKING → VERIFIED "
                    f"(age: {age_minutes}min, idle: {idle_minutes}min, sources: {len(story.get('source_articles', []))}) "
                    f"- No updates for 90 minutes"
                )
            
            # 2. HANDLE PUSH NOTIFICATIONS for stories still BREAKING
            elif not story.get('push_notification_sent', False):
                # Story is still fresh (<30min) and needs notification
                logger.info(f"📢 Sending push notification for: {story['id']} - {story.get('title', '')[:60]}...")
                
                # Get all FCM tokens from user_preferences
                try:
                    user_container = cosmos_client.client.get_database_client(config.COSMOS_DATABASE_NAME).get_container_client("user_preferences")
                    
                    # Query for all users with notifications enabled
                    query = """
                    SELECT c.fcm_token 
                    FROM c 
                    WHERE c.notifications_enabled = true 
                    AND c.fcm_token != null
                    AND (NOT IS_DEFINED(c.notification_preferences.breaking_news) OR c.notification_preferences.breaking_news = true)
                    """
                    
                    fcm_tokens = []
                    for item in user_container.query_items(query=query, enable_cross_partition_query=True):
                        if item.get('fcm_token'):
                            fcm_tokens.append(item['fcm_token'])
                    
                    if fcm_tokens:
                        # Send push notifications
                        result = await fcm_service.send_breaking_news_notification(fcm_tokens, story)
                        logger.info(
                            f"📲 Push notification results: {result['success']} success, "
                            f"{result['failure']} failure, {result['total_tokens']} total users"
                        )
                    else:
                        logger.info("⚠️  No FCM tokens found, skipping push notifications")
                    
                    # Mark as notified regardless of whether we sent (to avoid retries)
                    await cosmos_client.update_story_cluster(
                        story['id'],
                        story['category'],
                        {
                            'push_notification_sent': True,
                            'push_notification_sent_at': now.isoformat(),
                            'push_notification_recipients': len(fcm_tokens) if fcm_tokens else 0
                        }
                    )
                    notifications_sent += 1
                    
                except Exception as e:
                    logger.error(f"❌ Failed to send push notifications for story {story['id']}: {e}", exc_info=True)
        
        # 3. LOG SUMMARY
        if transitions_made > 0 or notifications_sent > 0:
            logger.info(
                f"✅ Status monitor complete: {transitions_made} BREAKING→VERIFIED transitions, "
                f"{notifications_sent} notifications sent, {len(breaking_stories)} total BREAKING stories"
            )
        else:
            logger.info(f"✅ Status monitor complete: {len(breaking_stories)} BREAKING stories, no actions needed")
        
    except Exception as e:
        logger.error(f"Breaking news monitoring failed: {e}", exc_info=True)


# ============================================================================
# BATCH SUMMARIZATION - Submit batches and process results
# ============================================================================

@app.function_name(name="BatchSummarizationManager")
@app.schedule(schedule="0 */30 * * * *", arg_name="timer", run_on_startup=False)
async def batch_summarization_manager(timer: func.TimerRequest) -> None:
    """
    Batch Summarization Manager - Runs every 30 minutes
    
    1. Processes completed batches from previous runs
    2. Finds stories needing summaries and submits new batch
    
    This provides 50% cost savings vs real-time API for backfill work.
    Real-time summarization (via changefeed) is unaffected.
    """
    logger.info("Batch summarization manager triggered")
    
    # Check if batch processing is enabled
    if not config.BATCH_PROCESSING_ENABLED:
        logger.info("Batch processing disabled. Set BATCH_PROCESSING_ENABLED=true to enable.")
        return
    
    if not config.ANTHROPIC_API_KEY:
        logger.warning("Anthropic API key not configured")
        return
    
    try:
        cosmos_client.connect()
        anthropic_client = Anthropic(api_key=config.ANTHROPIC_API_KEY) if Anthropic else None
        
        if not anthropic_client:
            logger.warning("Anthropic client not available")
            return
        
        # STEP 1: Process completed batches
        await process_completed_batches(anthropic_client)
        
        # STEP 2: Submit new batch if there are stories needing summaries
        await submit_new_batch(anthropic_client)
        
        logger.info("Batch summarization manager completed")
        
    except Exception as e:
        logger.error(f"Batch summarization manager failed: {e}", exc_info=True)


async def process_completed_batches(anthropic_client) -> None:
    """Process results from completed batches"""
    try:
        # Get all pending batches
        pending_batches = await cosmos_client.query_pending_batches()
        
        if not pending_batches:
            logger.info("No pending batches to process")
            return
        
        logger.info(f"Checking {len(pending_batches)} pending batches")
        
        for batch_tracking in pending_batches:
            batch_id = batch_tracking['batch_id']
            
            try:
                # Check batch status with Anthropic
                message_batch = anthropic_client.messages.batches.retrieve(batch_id)
                
                logger.info(f"Batch {batch_id}: {message_batch.processing_status}, "
                           f"succeeded={message_batch.request_counts.succeeded}, "
                           f"errored={message_batch.request_counts.errored}")
                
                # Only process if batch has ended
                if message_batch.processing_status != "ended":
                    logger.info(f"Batch {batch_id} still processing, skipping")
                    continue
                
                # Process results
                logger.info(f"Processing results for batch {batch_id}")
                
                succeeded_count = 0
                errored_count = 0
                
                # Stream results (memory efficient)
                for result in anthropic_client.messages.batches.results(batch_id):
                    try:
                        story_id = result.custom_id
                        
                        if result.result.type == "succeeded":
                            # Extract summary from result
                            message = result.result.message
                            summary_text = message.content[0].text.strip()
                            
                            # Check for AI refusal
                            from shared.utils import is_ai_refusal, generate_fallback_summary
                            
                            # Get story data for fallback if needed
                            story_data = None
                            if is_ai_refusal(summary_text):
                                # Need to fetch story for fallback
                                category = batch_tracking.get('story_categories', {}).get(story_id, 'general')
                                story_data = await cosmos_client.get_story_cluster(story_id, category)
                                
                                if story_data:
                                    articles = await fetch_story_articles(story_id, story_data)
                                    summary_text = generate_fallback_summary(story_data, articles)
                                    logger.warning(f"AI refused for {story_id}, used fallback")
                            
                            # Calculate metrics
                            word_count = len(summary_text.split())
                            usage = message.usage
                            
                            # Calculate cost with batch pricing (50% discount)
                            input_tokens = usage.input_tokens
                            output_tokens = usage.output_tokens
                            cached_tokens = getattr(usage, 'cache_read_input_tokens', 0)
                            
                            # Batch pricing: 50% of regular
                            input_cost = (input_tokens - cached_tokens) * 0.50 / 1_000_000  # $0.50/MTok
                            cache_cost = cached_tokens * 0.05 / 1_000_000  # $0.05/MTok
                            output_cost = output_tokens * 2.50 / 1_000_000  # $2.50/MTok
                            total_cost = input_cost + cache_cost + output_cost
                            
                            # Get story category from tracking
                            category = batch_tracking.get('story_categories', {}).get(story_id, 'general')
                            
                            # Create summary object
                            summary = {
                                'version': 1,
                                'text': summary_text,
                                'generated_at': datetime.now(timezone.utc).isoformat(),
                                'model': config.ANTHROPIC_MODEL,
                                'word_count': word_count,
                                'generation_time_ms': 0,  # Batch processing, no timing
                                'source_count': batch_tracking.get('story_source_counts', {}).get(story_id, 1),
                                'prompt_tokens': input_tokens,
                                'completion_tokens': output_tokens,
                                'cached_tokens': cached_tokens,
                                'cost_usd': round(total_cost, 6),
                                'batch_processed': True
                            }
                            
                            # Update story with summary
                            await cosmos_client.update_story_cluster(story_id, category, {
                                'summary': summary
                            })
                            
                            succeeded_count += 1
                            logger.info(f"✅ Batch summary for {story_id}: {word_count} words, ${total_cost:.4f}")
                            
                        elif result.result.type == "errored":
                            error_type = result.result.error.type
                            logger.error(f"❌ Batch request failed for {story_id}: {error_type}")
                            errored_count += 1
                            
                        elif result.result.type == "expired":
                            logger.warning(f"⏱️ Batch request expired for {story_id}")
                            errored_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing batch result for {result.custom_id}: {e}")
                        errored_count += 1
                
                # Update batch tracking
                await cosmos_client.update_batch_tracking(batch_id, {
                    'status': 'completed',
                    'ended_at': datetime.now(timezone.utc).isoformat(),
                    'succeeded_count': succeeded_count,
                    'errored_count': errored_count
                })
                
                logger.info(f"✅ Completed batch {batch_id}: {succeeded_count} succeeded, {errored_count} errored")
                
            except Exception as e:
                logger.error(f"Error processing batch {batch_id}: {e}")
                # Mark batch as failed
                try:
                    await cosmos_client.update_batch_tracking(batch_id, {
                        'status': 'failed',
                        'error': str(e)
                    })
                except:
                    pass
        
    except Exception as e:
        logger.error(f"Error in process_completed_batches: {e}", exc_info=True)


async def submit_new_batch(anthropic_client) -> None:
    """Find stories needing summaries and submit a new batch"""
    try:
        # Query stories without summaries
        cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=config.BATCH_BACKFILL_HOURS)).isoformat(timespec='seconds') + 'Z'
        
        query = f"""
        SELECT * FROM c 
        WHERE (NOT IS_DEFINED(c.summary) OR c.summary = null OR c.summary.text = null OR c.summary.text = '')
        AND ARRAY_LENGTH(c.source_articles) >= 1
        AND c.status != 'MONITORING'
        AND c.last_updated >= '{cutoff_time}'
        ORDER BY c.last_updated DESC
        OFFSET 0 LIMIT {config.BATCH_MAX_SIZE}
        """
        
        container = cosmos_client._get_container(config.CONTAINER_STORY_CLUSTERS)
        stories = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        if not stories:
            logger.info(f"No stories needing summaries (last {config.BATCH_BACKFILL_HOURS}h)")
            return
        
        logger.info(f"Found {len(stories)} stories needing summaries, preparing batch")
        
        # Build batch requests
        batch_requests = []
        story_categories = {}  # Track category for each story
        story_source_counts = {}  # Track source count for each story
        
        for story_data in stories:
            try:
                story_id = story_data['id']
                category = story_data.get('category', 'general')
                source_articles = story_data.get('source_articles', [])
                
                # Store metadata for later use
                story_categories[story_id] = category
                story_source_counts[story_id] = len(source_articles)
                
                # Fetch articles (limit to 6 for efficiency)
                articles = await fetch_story_articles(story_id, story_data)
                
                if not articles:
                    logger.warning(f"Could not fetch articles for story {story_id}, skipping")
                    continue
                
                # Build prompt using shared helper
                from shared.utils import build_summarization_prompt
                prompt, system_msg = build_summarization_prompt(articles)
                
                # Add to batch
                batch_requests.append({
                    "custom_id": story_id,
                    "params": {
                        "model": config.ANTHROPIC_MODEL,
                        "max_tokens": 300,
                        "system": system_msg,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                })
                
            except Exception as e:
                logger.error(f"Error preparing batch request for story {story_data.get('id')}: {e}")
        
        if not batch_requests:
            logger.warning("No valid batch requests prepared")
            return
        
        # Submit batch to Anthropic
        logger.info(f"Submitting batch with {len(batch_requests)} requests")
        
        message_batch = anthropic_client.messages.batches.create(
            requests=batch_requests
        )
        
        logger.info(f"✅ Batch submitted: {message_batch.id}, {len(batch_requests)} requests")
        
        # Store batch tracking in Cosmos
        batch_tracking = {
            'id': message_batch.id,
            'batch_id': message_batch.id,  # Also use as partition key
            'status': 'in_progress',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'request_count': len(batch_requests),
            'story_ids': [req['custom_id'] for req in batch_requests],
            'story_categories': story_categories,
            'story_source_counts': story_source_counts,
            'anthropic_status': message_batch.processing_status
        }
        
        await cosmos_client.create_batch_tracking(batch_tracking)
        
        logger.info(f"Batch tracking created for {message_batch.id}")
        
    except Exception as e:
        logger.error(f"Error in submit_new_batch: {e}", exc_info=True)


async def fetch_story_articles(story_id: str, story_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fetch source articles for a story (helper function)"""
    articles = []
    source_articles = story_data.get('source_articles', [])

    for article_id in source_articles[:6]:  # Limit to 6 articles
        try:
            parts = article_id.split('_')
            if len(parts) >= 2:
                date_str = parts[1]
                partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                article = await cosmos_client.get_raw_article(article_id, partition_key)
                if article:
                    articles.append(article)
        except Exception as e:
            logger.warning(f"Could not fetch article {article_id}: {e}")

    return articles


# ============================================================================
# TEMPORARY CLEANUP FUNCTION - Remove test stories
# ============================================================================

@app.function_name(name="CleanupTestStories")
@app.schedule(schedule="0 0 * * * *", arg_name="timer", run_on_startup=False)
async def cleanup_test_stories_timer(timer: func.TimerRequest) -> None:
    """TEMPORARY: Clean up test stories from database - Runs once per hour"""
    logger.info("🧹 CLEANUP: Starting test story cleanup...")

    try:
        cosmos_client.connect()

        # Query all stories
        stories_container = cosmos_client._get_container('story_clusters')
        query = 'SELECT * FROM c'
        all_stories = list(stories_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        logger.info(f"📊 Found {len(all_stories)} total stories")

        # Identify test stories
        test_story_ids = []
        for story in all_stories:
            story_id = story.get('id', '')
            title = story.get('title', '').lower()
            source_articles = story.get('source_articles', [])

            # Check for test patterns
            is_test = False

            # Title patterns
            test_title_patterns = [
                'breaking: major event',
                'major policy announcement',
                'test article',
                'test article 0',
                'major breakthrough in renewable energy',
                'global markets rally',
                'new climate agreement reached'
            ]

            if any(pattern in title for pattern in test_title_patterns):
                is_test = True

            # Check for test sources
            test_source_count = 0
            for article in source_articles:
                if isinstance(article, dict):
                    source = article.get('source', '').lower()
                    if ('test' in source or
                        source.startswith('source ') or
                        source == 'test source' or
                        source == 'test source 1'):
                        test_source_count += 1

            # If more than half the sources are test sources, it's a test story
            if test_source_count > len(source_articles) // 2 and len(source_articles) > 0:
                is_test = True

            # Unrealistic number of sources (>100 is definitely test data)
            if len(source_articles) > 100:
                is_test = True

            # Only test sources
            if len(source_articles) > 0 and test_source_count == len(source_articles):
                is_test = True

            if is_test:
                test_story_ids.append((story_id, story.get('category', 'general')))

        logger.info(f"🗑️ Found {len(test_story_ids)} test stories to delete")

        # Delete test stories
        deleted_count = 0
        for story_id, category in test_story_ids:
            try:
                stories_container.delete_item(item=story_id, partition_key=category)
                deleted_count += 1
                logger.info(f"✅ Deleted test story: {story_id}")
            except Exception as e:
                logger.error(f"❌ Failed to delete story {story_id}: {e}")

        logger.info(f"🎉 CLEANUP COMPLETE: Deleted {deleted_count} test stories")

    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}", exc_info=True)


@app.function_name(name="train_similarity_model")
@app.route(route="admin/train-similarity-model", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
async def train_similarity_model(req: func.HttpRequest) -> func.HttpResponse:
    """
    Phase 3.5: Train the similarity scoring model on labeled data.

    POST /admin/train-similarity-model
    Body: {"num_pairs": 1000, "force_retrain": false}
    """
    try:
        req_body = req.get_json()
        num_pairs = req_body.get('num_pairs', 1000)
        force_retrain = req_body.get('force_retrain', False)

        from .shared.scoring_optimization import get_similarity_scorer
        from .shared.training_data import generate_training_data, save_training_data, load_training_data

        scorer = get_similarity_scorer()

        # Check if we already have a trained model
        if scorer.is_trained and not force_retrain:
            return func.HttpResponse(
                json.dumps({
                    "message": "Model already trained",
                    "is_trained": True,
                    "model_path": config.SCORING_MODEL_PATH
                }),
                status_code=200,
                mimetype="application/json"
            )

        # Generate or load training data
        try:
            training_pairs = await load_training_data()
            if not training_pairs or len(training_pairs) < 100:
                logger.info("Insufficient training data, generating new data...")
                training_pairs = await generate_training_data(num_pairs)
                await save_training_data(training_pairs)
        except:
            logger.info("No existing training data, generating new data...")
            training_pairs = await generate_training_data(num_pairs)
            await save_training_data(training_pairs)

        if not training_pairs:
            return func.HttpResponse(
                json.dumps({"error": "Failed to generate training data"}),
                status_code=500,
                mimetype="application/json"
            )

        # Train the model
        logger.info(f"Training similarity model on {len(training_pairs)} pairs...")
        scorer.train(training_pairs)

        # Get model performance
        performance = scorer.evaluate_on_data(training_pairs)

        return func.HttpResponse(
            json.dumps({
                "message": "Model trained successfully",
                "training_pairs": len(training_pairs),
                "performance": performance,
                "model_path": config.SCORING_MODEL_PATH,
                "is_trained": scorer.is_trained
            }),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logger.error(f"Training failed: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

