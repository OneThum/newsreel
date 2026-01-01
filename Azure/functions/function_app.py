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
    is_spam_or_promotional
)
# New semantic clustering (2025 best practices - replaces keyword matching)
from shared.semantic_clustering import (
    generate_article_embedding, find_matching_story,
    cosine_similarity, compute_story_embedding, generate_legacy_fingerprint,
    CLUSTER_MATCH_THRESHOLD, is_semantic_clustering_enabled
)

# Try to import Anthropic
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

# Import structured logger
from shared.logger import get_logger
import re

logger = get_logger(__name__)
app = func.FunctionApp()


# ============================================================================
# AI OUTPUT CLEANUP UTILITIES
# ============================================================================

def clean_ai_summary(text: str) -> str:
    """
    Remove common AI artifacts from summaries:
    - Preambles like "Here's a concise summary:"
    - Headers like "COMPREHENSIVE NEWS SUMMARY:"
    - Meta-commentary about the summary itself
    - Trailing explanations about the summary
    """
    if not text:
        return text
    
    # Patterns to remove from the START of the summary
    start_patterns = [
        r'^Here\'?s?\s+(?:a\s+)?(?:concise|comprehensive|authoritative|brief|factual|neutral)[\s,]+(?:authoritative\s+)?summary[:\s]*',
        r'^(?:COMPREHENSIVE\s+)?NEWS\s+SUMMARY[:\s]*(?:[A-Za-z\s]+[:\s]*)?',
        r'^Summary[:\s]*',
        r'^(?:Here\s+is\s+)?(?:The\s+)?(?:a\s+)?(?:news\s+)?summary[:\s]*',
        r'^Based\s+on\s+(?:the\s+)?(?:provided\s+)?(?:articles?|sources?|information)[,:\s]*',
        r'^(?:According\s+to\s+)?(?:the\s+)?(?:multiple\s+)?sources?[,:\s]*here\'?s?\s+(?:what\s+we\s+know|a\s+summary)[:\s]*',
    ]
    
    # Patterns to remove from the END of the summary
    end_patterns = [
        r'[\.\s]+The\s+summary\s+(?:provides|offers|gives|presents)[\s\S]*$',
        r'[\.\s]+This\s+(?:summary|overview)\s+(?:provides|offers|gives|presents|maintains|covers)[\s\S]*$',
        r'[\.\s]+(?:I\'?ve\s+)?(?:maintained|ensured|kept)\s+(?:a\s+)?neutral\s+tone[\s\S]*$',
        r'[\.\s]+(?:The\s+)?(?:above\s+)?summary\s+is\s+(?:factual|neutral|comprehensive)[\s\S]*$',
    ]
    
    result = text.strip()
    
    # Remove start patterns (case-insensitive)
    for pattern in start_patterns:
        result = re.sub(pattern, '', result, flags=re.IGNORECASE).strip()
    
    # Remove end patterns (case-insensitive)
    for pattern in end_patterns:
        result = re.sub(pattern, '', result, flags=re.IGNORECASE).strip()
    
    return result


def clean_ai_headline(text: str) -> str:
    """
    Remove common AI artifacts from headlines:
    - Rationale explanations
    - Surrounding quotes
    - "Updated headline:" prefixes
    - Source-specific tags
    """
    if not text:
        return text
    
    result = text.strip()
    
    # If the response contains "Rationale:" or "Reason:", only keep the part before it
    rationale_markers = ['Rationale:', 'Reason:', 'Explanation:', 'Note:', 'Update reason:']
    for marker in rationale_markers:
        if marker in result:
            result = result.split(marker)[0].strip()
        if marker.lower() in result.lower():
            idx = result.lower().find(marker.lower())
            result = result[:idx].strip()
    
    # Remove newlines and everything after
    if '\n' in result:
        result = result.split('\n')[0].strip()
    
    # Remove "Updated headline:" or similar prefixes
    prefix_patterns = [
        r'^Updated\s+headline[:\s]*',
        r'^New\s+headline[:\s]*',
        r'^Headline[:\s]*',
        r'^Suggested[:\s]*',
    ]
    for pattern in prefix_patterns:
        result = re.sub(pattern, '', result, flags=re.IGNORECASE).strip()
    
    # Strip surrounding quotes (but preserve internal quotes)
    if (result.startswith('"') and result.endswith('"')) or \
       (result.startswith("'") and result.endswith("'")):
        result = result[1:-1].strip()
    
    # Remove trailing quote if orphaned
    result = result.rstrip('"').rstrip("'").strip()
    
    # Remove source-specific tags that might have slipped through
    tag_patterns = [
        r'\s*\|\s*(?:Special\s+Report|BREAKING|Live|Update|Analysis|Opinion|Exclusive)$',
        r'\s*-\s*(?:Live|Update|Breaking)$',
    ]
    for pattern in tag_patterns:
        result = re.sub(pattern, '', result, flags=re.IGNORECASE).strip()
    
    return result

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
        # source_articles can be dicts (new format) or string IDs (old format)
        all_source_headlines = []
        for art_data in source_articles[:10]:  # Limit to 10 most recent
            if isinstance(art_data, dict):
                # New format: article data is already embedded
                source_name = art_data.get('source', 'Unknown')
                title = art_data.get('title', '')
                if title:
                    all_source_headlines.append(f"- {source_name}: {title}")
            elif isinstance(art_data, str):
                # Old format: article_id string, need to fetch from Cosmos
                parts = art_data.split('_')
                if len(parts) >= 2:
                    date_str = parts[1]
                    partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    article = await cosmos_client.get_raw_article(art_data, partition_key)
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
If update needed: Write ONLY the headline text (8-15 words, specific, clear, NO editorial tags)
If no update needed: Write exactly "KEEP_CURRENT"

CRITICAL: Output ONLY the headline or "KEEP_CURRENT". NO explanations, NO rationale, NO quotes around the headline.

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

OUTPUT RULES:
- Respond with ONLY the headline text or "KEEP_CURRENT"
- NO explanations, rationale, or reasoning
- NO quotes around the headline
- NO line breaks or additional text"""

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
        
        # Clean up new headline using comprehensive artifact removal
        updated_headline = clean_ai_headline(ai_response)
        
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
        
        article_id = generate_article_id(feed_config.source_id, article_url, published_at)
        
        # Generate semantic embedding for clustering (2025 best practices)
        # This replaces the old fingerprint-based approach with true semantic understanding
        embedding = generate_article_embedding(title, description)
        
        # Legacy fingerprint for backward compatibility (will be phased out)
        story_fingerprint = generate_legacy_fingerprint(title)
        
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
            embedding=embedding,  # Semantic embedding for clustering
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
# QUEUE-BASED RSS INGESTION (Reliable Alternative)
# ============================================================================

@app.function_name(name="RSSIngestionQueue")
@app.schedule(schedule="*/10 * * * * *", arg_name="timer", run_on_startup=False)
async def rss_ingestion_queue_timer(timer: func.TimerRequest) -> None:
    """
    Queue-Based RSS Ingestion - Runs every 10 seconds
    
    This is a lightweight alternative to direct RSS fetching.
    Instead of fetching feeds directly (flaky), this function:
    1. Determines which feeds need polling
    2. Pushes feed URLs to Azure Service Bus queue
    3. Container App worker handles actual fetching (reliable)
    
    Enable with: USE_QUEUE_BASED_RSS=true
    
    Benefits:
    - No cold start impact on feed fetching
    - Automatic retry with dead-letter queue
    - Circuit breaker in worker prevents hammering failing feeds
    - Always-on worker = bulletproof reliability
    """
    # Check if queue-based ingestion is enabled
    if not config.USE_QUEUE_BASED_RSS:
        return  # Disabled, use traditional RSS ingestion
    
    if not config.SERVICE_BUS_CONNECTION_STRING:
        logger.warning("SERVICE_BUS_CONNECTION_STRING not configured, skipping queue-based ingestion")
        return
    
    with logger.operation("rss_ingestion_queue"):
        try:
            cosmos_client.connect()
            
            # Import queue producer
            from shared.queue_producer import get_queue_producer
            
            producer = get_queue_producer(cosmos_client)
            
            # Determine feeds to poll and push to queue
            result = await producer.push_and_track(
                use_all_feeds=config.RSS_USE_ALL_FEEDS,
                max_feeds=10,  # 10 feeds per cycle for smooth distribution
                cooldown_seconds=180  # 3 minute cooldown per feed
            )
            
            if result['feeds_queued'] > 0:
                logger.info(f"📤 Queued {result['feeds_queued']} feeds for processing")
                logger.info(f"📊 Category distribution: {result.get('categories', {})}")
            else:
                logger.debug("No feeds ready for polling this cycle")
                
        except Exception as e:
            logger.error(f"Queue-based RSS ingestion failed: {e}", error=e)
            # Don't raise - this is a lightweight producer, let it retry next cycle


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
    """Story Clustering - Triggered by new articles"""
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
            
            # =================================================================
            # SEMANTIC CLUSTERING (2025 Best Practices)
            # Uses OpenAI embeddings for true semantic understanding
            # Replaces old keyword-based fingerprint matching
            # =================================================================
            
            stories = []
            matched_story = False
            best_similarity = 0.0
            
            # Check if article has embedding (new articles should)
            article_embedding = article.embedding
            
            if not article_embedding:
                # Generate embedding if missing (handles articles created before semantic clustering)
                logger.info(f"⚠️ Article missing embedding, generating now: {article.id}")
                article_embedding = generate_article_embedding(article.title, article.description)
                if article_embedding:
                    # Update article with embedding for future use
                    await cosmos_client.update_article_embedding(article.id, article.published_date, article_embedding)
            
            if article_embedding:
                # Query recent stories across ALL categories for cross-category clustering
                # This ensures the same story isn't duplicated across world/tech/politics etc.
                recent_stories = await cosmos_client.query_recent_stories(category=None, limit=200)
                
                logger.info(f"🧠 SEMANTIC CLUSTERING: '{article.title[:60]}...' vs {len(recent_stories)} stories")
                
                # Use semantic similarity to find matching story
                matching_story, best_similarity = find_matching_story(
                    article_embedding=article_embedding,
                    article_title=article.title,
                    candidate_stories=recent_stories,
                    threshold=CLUSTER_MATCH_THRESHOLD
                )
                
                if matching_story:
                    stories = [matching_story]
                    matched_story = True
                    logger.info(f"✅ SEMANTIC MATCH: {best_similarity:.3f} - '{article.title[:50]}...' → '{matching_story.get('title', '')[:50]}...'")
                else:
                    logger.info(f"🆕 NO SEMANTIC MATCH: Creating new story (best: {best_similarity:.3f})")
            else:
                # Fallback: No embedding available, query recent stories and create new story
                logger.warning(f"⚠️ No embedding available for article {article.id}, creating new story")
                recent_stories = await cosmos_client.query_recent_stories(category=None, limit=50)
            
            # Log article processing
            logger.log_article_processed(
                article_id=article.id,
                source=article.source,
                category=article.category,
                fingerprint=article.story_fingerprint,
                matched_story=matched_story
            )
            
            if stories:
                # Update existing story
                story = stories[0]
                source_articles = story.get('source_articles', [])
                
                # CRITICAL: Calculate prev_source_count BEFORE modifying the list
                # (source_articles is a reference to the list in story, not a copy)
                prev_source_count = len(source_articles)
                
                # Check if THIS SPECIFIC ARTICLE is already in the cluster (by ID)
                if article.id in source_articles:
                    # This exact article is already in the cluster, skip
                    logger.info(f"Article {article.id} already in story {story['id']} - skipping duplicate")
                    await cosmos_client.update_article_processed(article.id, article.published_date, story['id'])
                    continue  # Skip to next article - DON'T update last_updated!
                
                # Check if we already have an article from this source in the cluster
                # This prevents duplicate sources from being added to the same story
                existing_sources = set()
                source_details = {}
                for existing_art in source_articles:
                    if isinstance(existing_art, dict):
                        existing_source = existing_art.get('source', existing_art.get('id', '').split('_')[0])
                    else:
                        existing_source = existing_art.split('_')[0]  # Fallback for old format
                    existing_sources.add(existing_source)
                    source_details[existing_source] = source_details.get(existing_source, 0) + 1
                
                new_source = article.id.split('_')[0]
                
                # Log detailed source analysis
                logger.info(f"🔍 Source analysis for story {story['id']}:")
                logger.info(f"   Existing sources: {dict(source_details)}")
                logger.info(f"   New article source: {new_source}")
                logger.info(f"   Article ID: {article.id}")
                
                if new_source in existing_sources:
                    # We already have an article from this source, skip to prevent duplicates
                    logger.info(f"❌ DUPLICATE SOURCE PREVENTION: Source {new_source} already in story {story['id']} - skipping duplicate source")
                    logger.info(f"   Existing sources: {list(existing_sources)}")
                    logger.info(f"   Source counts: {dict(source_details)}")
                    await cosmos_client.update_article_processed(article.id, article.published_date, story['id'])
                    continue  # Skip to next article - DON'T update last_updated!
                
                # Article not in cluster yet and source is unique - ADD IT
                # Store embedded article dictionary (new format)
                embedded_article = {
                    'id': article.id,
                    'source': article.source,
                    'title': article.title,
                    'url': article.article_url,
                    'published_at': article.published_at.isoformat() if isinstance(article.published_at, datetime) else str(article.published_at),
                    'content': article.description or '',
                    'embedding': article_embedding  # Store embedding for clustering
                }
                source_articles.append(embedded_article)
                
                # Recompute story embedding (centroid of all article embeddings)
                story_embedding = compute_story_embedding(source_articles)
                
                # 🔍 ENHANCED SOURCE TRACKING LOGGING
                # Calculate source diversity BEFORE updating
                from collections import Counter
                existing_sources = []
                for art in source_articles[:-1]:  # All except the one we just added
                    if isinstance(art, dict):
                        source_part = art.get('source', art.get('id', '').split('_')[0])
                    else:
                        source_part = art.split('_')[0]  # Fallback for old format
                    existing_sources.append(source_part)
                
                source_counts = Counter(existing_sources)
                unique_sources = len(source_counts)
                duplicate_sources = {k: v for k, v in source_counts.items() if v > 1}
                
                logger.info(
                    f"📰 Added [{article.source}] to story {story['id']}: "
                    f"{prev_source_count}→{len(source_articles)} articles, "
                    f"{unique_sources} unique sources"
                )
                
                if duplicate_sources:
                    logger.warning(
                        f"⚠️  Story {story['id']} has DUPLICATE SOURCES: "
                        f"{dict(duplicate_sources)}"
                    )
                    # Log the new article's source
                    logger.warning(f"   Just added: {article.source} (ID: {article.id})")
                    # Check if this new article is creating a duplicate
                    if article.source.split('_')[0] in duplicate_sources:
                        logger.warning(f"   ⚠️  This is a DUPLICATE of existing {article.source} articles!")
                
                # Log source diversity details
                logger.log_story_cluster(
                    story_id=story['id'],
                    action="updated",
                    source_count=len(source_articles),
                    category=story.get('category', 'unknown'),
                    fingerprint=article.story_fingerprint,
                    title=story.get('title', 'unknown'),
                    status=story.get('status', 'unknown')
                )
                
                verification_level = len(source_articles)
                now = datetime.now(timezone.utc)
                first_seen = datetime.fromisoformat(story['first_seen'].replace('Z', '+00:00'))
                time_since_first = now - first_seen
                
                # SIMPLIFIED STATUS SYSTEM (based purely on source count)
                # Status indicates verification confidence level, not urgency
                # - NEW: 1 source (unverified)
                # - DEVELOPING: 2 sources (gaining traction)
                # - VERIFIED: 3+ sources (confirmed by multiple outlets)
                # 
                # Note: Push notifications for breaking news are handled separately
                # by BreakingNewsMonitor based on recency + source count
                
                if verification_level >= 3:
                    status = StoryStatus.VERIFIED.value
                    logger.info(f"   → VERIFIED ({verification_level} sources)")
                elif verification_level == 2:
                    status = StoryStatus.DEVELOPING.value
                    logger.info(f"   → DEVELOPING ({verification_level} sources)")
                else:
                    status = StoryStatus.NEW.value
                    logger.info(f"   → NEW ({verification_level} source)")
                
                # Determine breaking news status based on:
                # 1. Already flagged as breaking, OR
                # 2. New tier 1 source added, OR  
                # 3. 3+ sources (verified story = potential breaking)
                is_breaking = (
                    story.get('breaking_news', False) or 
                    article.source_tier == 1 or
                    verification_level >= 3
                )
                
                updates = {
                    'source_articles': source_articles,
                    'source_count': verification_level,  # Track source count explicitly
                    'verification_level': verification_level,
                    'status': status,
                    'last_updated': datetime.now(timezone.utc).isoformat(),
                    'update_count': story.get('update_count', 0) + 1,
                    'embedding': story_embedding,  # Updated story centroid embedding
                    'breaking_news': is_breaking  # Update breaking news flag
                }
                
                # RE-EVALUATE HEADLINE on EVERY source addition
                # Headlines should evolve as breaking news develops and more details emerge
                # AI will decide if new source warrants headline update (default: KEEP_CURRENT)
                should_update_headline = False
                
                # ALWAYS re-evaluate when a new source is added (verification_level increased)
                if verification_level > prev_source_count:
                    should_update_headline = True
                    logger.info(f"📰 Headline re-evaluation triggered for {story['id']} ({prev_source_count}→{verification_level} sources)")
                
                if should_update_headline:
                    try:
                        # Generate updated headline based on all sources
                        updated_headline = await generate_updated_headline(story, source_articles, article)
                        if updated_headline and updated_headline != story['title']:
                            updates['title'] = updated_headline
                            logger.info(f"✏️ Updated headline: '{story['title']}' → '{updated_headline}'")
                    except Exception as e:
                        logger.error(f"Failed to update headline for {story['id']}: {e}")
                        # Continue without headline update if it fails
                
                await cosmos_client.update_story_cluster(story['id'], story['category'], updates)
                story_id = story['id']
                
                # Log story cluster update with status for monitoring
                logger.log_story_cluster(
                    story_id=story_id,
                    action="updated",
                    source_count=verification_level,
                    category=story['category'],
                    fingerprint=article.story_fingerprint,
                    title=story['title'],
                    status=status  # Log the status for badge monitoring
                )
            else:
                # Create new story
                story_id = f"story_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{article.story_fingerprint}"
                
                # Create embedded article dictionary (new format)
                # Include embedding for future clustering comparisons
                embedded_article = {
                    'id': article.id,
                    'source': article.source,
                    'title': article.title,
                    'url': article.article_url,
                    'published_at': article.published_at.isoformat() if isinstance(article.published_at, datetime) else str(article.published_at),
                    'content': article.description or '',
                    'embedding': article_embedding  # Store embedding for clustering
                }
                
                # Determine if this is breaking news based on tier and recency
                # Tier 1 sources (wire services) are more likely to be breaking news
                is_breaking = article.source_tier == 1
                
                story = StoryCluster(
                    id=story_id,
                    event_fingerprint=article.story_fingerprint,
                    title=article.title,
                    category=article.category,
                    tags=article.tags,
                    status=StoryStatus.NEW,  # New stories start as NEW (1 source)
                    verification_level=1,
                    first_seen=article.published_at,
                    last_updated=datetime.now(timezone.utc),
                    source_articles=[embedded_article],
                    source_count=1,  # Track source count explicitly for API queries
                    embedding=article_embedding,  # Story embedding = first article's embedding
                    importance_score=50 + (20 if article.source_tier == 1 else 0),
                    confidence_score=40,
                    breaking_news=is_breaking  # Flag as breaking if from tier 1 source
                )
                
                await cosmos_client.create_story_cluster(story)
                
                # Log story cluster creation with initial NEW status
                logger.log_story_cluster(
                    story_id=story_id,
                    action="created",
                    source_count=1,
                    status=StoryStatus.NEW.value,
                    category=article.category,
                    fingerprint=article.story_fingerprint,
                    title=article.title
                )
            
            # Mark article as processed
            await cosmos_client.update_article_processed(article.id, article.published_date, story_id)
            
        except Exception as e:
            logger.error(f"Error clustering document: {e}", exc_info=True)
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    logger.info(f"Completed clustering {len(documents)} documents")


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
            # source_articles can be dicts (new format) or string IDs (old format)
            articles = []
            for art_data in source_articles[:6]:  # Limit to 6 sources
                if isinstance(art_data, dict):
                    # New format: article data is already embedded
                    articles.append(art_data)
                elif isinstance(art_data, str):
                    # Old format: article_id string, need to fetch from Cosmos
                    parts = art_data.split('_')
                    if len(parts) >= 2:
                        date_str = parts[1]
                        partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                        article = await cosmos_client.get_raw_article(art_data, partition_key)
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
                story_title = story_data.get('title', '')
                prompt = f"""You are a senior news editor creating a summary from a news report. Extract and present the key information clearly.

HEADLINE (already shown to readers): "{story_title}"

ESSENTIAL FACTS TO INCLUDE:
- What happened (the core event)
- Who is involved (people, organizations)
- When and where it occurred  
- Why it matters (significance, impact, context)
- What happens next (if mentioned)

QUALITY STANDARDS:
- Do NOT repeat the headline - readers already see it. Start with NEW details.
- Include ALL specific details available: numbers, dates, names, locations, quotes
- Use clear, direct language that intelligent readers can understand
- Write 80-120 words (concise but complete)
- Lead with the most important NEW information not in the headline
- Maintain neutral, factual tone

YOU MUST provide a summary based on what IS available. Never refuse or say you need more sources.

Article to summarize:

{combined_articles}

Write the summary now (start directly with new details, don't repeat the headline):"""
            
            else:
                # Multi-source: Synthesize perspectives for comprehensive view
                story_title = story_data.get('title', '')
                prompt = f"""You are a senior news editor synthesizing {len(articles)} reports about the same event. Create a comprehensive summary that shows readers the full picture from multiple perspectives.

HEADLINE (already shown to readers): "{story_title}"

ESSENTIAL FACTS TO INCLUDE:
- What happened (the core event)  
- Who is involved (key people, organizations)
- When and where it occurred
- Why it matters (significance, impact, broader context)
- What happens next (if known)

SYNTHESIS REQUIREMENTS:
- Do NOT repeat the headline - readers already see it. Start with NEW details.
- Identify facts reported by MULTIPLE sources (high confidence - state these directly)
- Note facts from single sources (lower confidence - attribute: "According to [Source]...")
- Highlight any conflicting information or different framings between sources
- Show how different sources emphasize different aspects of the story

QUALITY STANDARDS:
- Include specific details: numbers, dates, direct quotes, locations
- Use clear, accessible language (write for intelligent readers, not specialists)
- Write 120-150 words (comprehensive but scannable)
- Lead with the most important NEW information not in the headline
- Present multiple perspectives fairly

Articles to summarize:

{combined_articles}

Write the summary now (start directly with new details, don't repeat the headline):"""
            
            # Enhanced system prompt emphasizing quality and trustworthiness
            system_prompt = """You are a senior news editor known for creating trustworthy, comprehensive summaries. Your summaries help readers understand complex events quickly while maintaining journalistic standards.

Core principles:
- ACCURACY: Every fact must come from the provided sources. Never speculate or add information.
- COMPLETENESS: Include all key information (who, what, when, where, why, impact)
- PERSPECTIVE: For multi-source stories, show how different sources frame the event
- CLARITY: Write for intelligent readers using clear, direct language
- TRUSTWORTHINESS: Readers rely on you to be their eyes and ears across multiple sources

CRITICAL FORMAT RULES:
- Start IMMEDIATELY with the news content. NO introductions like "Here's a summary:" or "COMPREHENSIVE NEWS SUMMARY:"
- Do NOT repeat or paraphrase the headline in your opening sentence - readers already see the headline, so add NEW information
- End with the last fact. NO meta-commentary like "This summary provides..." or "The above maintains neutral tone..."
- Write ONLY the summary itself - nothing else before or after

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
            
            # Extract summary and clean AI artifacts
            summary_text = clean_ai_summary(response.content[0].text.strip())
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
                # source_articles can be dicts (new format) or string IDs (old format)
                articles = []
                for art_data in source_articles[:6]:
                    if isinstance(art_data, dict):
                        # New format: article data is already embedded
                        articles.append(art_data)
                    elif isinstance(art_data, str):
                        # Old format: article_id string, need to fetch from Cosmos
                        parts = art_data.split('_')
                        if len(parts) >= 2:
                            date_str = parts[1]
                            partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                            article = await cosmos_client.get_raw_article(art_data, partition_key)
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

Write the summary now (start directly with the news, no preamble or header):"""
                    system_msg = "You are a professional news summarizer. You ALWAYS provide a summary based on available information, even if limited. You never refuse. Start IMMEDIATELY with the news content - NO introductions like 'Here is a summary' or headers."
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

Write the summary now (start directly with the news, no preamble or header):"""
                    system_msg = "You are a professional news summarizer. You create factual, neutral summaries from news articles. You ALWAYS provide a summary based on available information. Start IMMEDIATELY with the news content - NO introductions or headers."
                
                # Call Claude API
                start_time = time.time()
                response = anthropic_client.messages.create(
                    model=config.ANTHROPIC_MODEL,
                    max_tokens=300,
                    system=system_msg,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # Clean AI artifacts from summary
                summary_text = clean_ai_summary(response.content[0].text.strip())
                
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
# BREAKING NEWS PUSH NOTIFICATION MONITOR
# ============================================================================

@app.function_name(name="BreakingNewsMonitor")
@app.schedule(schedule="0 */2 * * * *", arg_name="timer", run_on_startup=False)
async def breaking_news_monitor_timer(timer: func.TimerRequest) -> None:
    """
    Breaking News Push Notification Monitor - Runs every 2 minutes
    
    Sends push notifications for VERIFIED stories (3+ sources) that:
    1. Were created or became VERIFIED in the last 30 minutes
    2. Haven't already received a push notification
    
    Note: Status system is now simplified to NEW/DEVELOPING/VERIFIED
    Push notifications are an EVENT, not a status.
    """
    logger.info("Breaking news push notification monitor triggered")
    
    try:
        cosmos_client.connect()
        now = datetime.now(timezone.utc)
        thirty_minutes_ago = now - timedelta(minutes=30)
        
        # Find VERIFIED stories (3+ sources) created in last 30 min that need notifications
        verified_stories = await cosmos_client.query_stories_by_status("VERIFIED", limit=100)
        
        notifications_sent = 0
        eligible_count = 0
        
        for story in verified_stories:
            # Check if story is recent enough for breaking news notification
            first_seen = datetime.fromisoformat(story['first_seen'].replace('Z', '+00:00'))
            
            # Only notify for stories created in the last 30 minutes
            if first_seen < thirty_minutes_ago:
                continue
                
            eligible_count += 1
            
            # Skip if already notified
            if story.get('push_notification_sent', False):
                continue
            
            source_count = len(story.get('source_articles', []))
            logger.info(f"📢 Sending push notification for VERIFIED story: {story['id']} - {story.get('title', '')[:60]}... ({source_count} sources)")
            
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
        
        logger.info(f"✅ Breaking news monitor complete: {notifications_sent} notifications sent, {eligible_count} eligible stories (VERIFIED, <30min old)")
        
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
    """Fetch source articles for a story (helper function)
    
    source_articles can be dicts (new format) or string IDs (old format)
    """
    articles = []
    source_articles = story_data.get('source_articles', [])
    
    for art_data in source_articles[:6]:  # Limit to 6 articles
        try:
            if isinstance(art_data, dict):
                # New format: article data is already embedded
                articles.append(art_data)
            elif isinstance(art_data, str):
                # Old format: article_id string, need to fetch from Cosmos
                parts = art_data.split('_')
                if len(parts) >= 2:
                    date_str = parts[1]
                    partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    article = await cosmos_client.get_raw_article(art_data, partition_key)
                    if article:
                        articles.append(article)
        except Exception as e:
            logger.warning(f"Could not fetch article {art_data}: {e}")
    
    return articles

