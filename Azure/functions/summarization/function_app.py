"""
Summarization Function
Triggered by Cosmos DB change feed on story_clusters
Generates AI summaries using Claude API when 2+ sources available
"""
import azure.functions as func
import logging
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import sys
import os
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import config
from shared.cosmos_client import cosmos_client
from shared.models import StoryStatus, SummaryVersion, VersionHistory

# Import Anthropic SDK
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None
    logging.warning("Anthropic SDK not installed")

logger = logging.getLogger(__name__)
app = func.FunctionApp()


class SummarizationService:
    """AI summarization service using Claude"""
    
    def __init__(self):
        self.client = None
        if Anthropic and config.ANTHROPIC_API_KEY:
            self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    
    def build_prompt(self, articles: List[Dict[str, Any]]) -> str:
        """Build prompt for Claude API"""
        
        # Sort articles by tier (tier 1 sources first)
        articles_sorted = sorted(articles, key=lambda a: a.get('source_tier', 3))
        
        # Build article summaries
        article_texts = []
        for i, article in enumerate(articles_sorted, 1):
            source = article.get('source', 'Unknown')
            title = article.get('title', '')
            description = article.get('description', '')
            content = article.get('content', description)
            
            article_text = f"""
Source {i}: {source}
Title: {title}
Content: {content[:1000]}
"""
            article_texts.append(article_text.strip())
        
        combined_articles = "\n\n---\n\n".join(article_texts)
        
        prompt = f"""You are a news summarization AI. Your task is to create a factual, neutral summary synthesizing information from multiple news sources about the same event.

Guidelines:
1. Write in third person, present or past tense as appropriate
2. Include only verified facts that appear in multiple sources
3. Cite specific numbers, dates, locations, and names
4. Keep it concise: 100-150 words
5. Focus on what happened, who was involved, when, where, and immediate impacts
6. Avoid speculation, opinion, or analysis
7. If sources conflict, mention both perspectives
8. Use clear, accessible language

Articles to summarize:

{combined_articles}

Write a factual summary synthesizing these articles:"""
        
        return prompt
    
    async def generate_summary(
        self,
        articles: List[Dict[str, Any]],
        existing_summary: Optional[Dict[str, Any]] = None
    ) -> Optional[SummaryVersion]:
        """Generate summary using Claude API"""
        
        if not self.client:
            logger.error("Anthropic client not initialized")
            return None
        
        if len(articles) < config.MIN_SOURCES_FOR_DEVELOPING:
            logger.info(f"Not enough sources for summarization: {len(articles)}")
            return None
        
        try:
            start_time = time.time()
            
            # Build prompt
            prompt = self.build_prompt(articles)
            
            # System prompt for consistent behavior
            system_prompt = """You are a professional news summarizer. You create factual, neutral summaries 
that synthesize information from multiple sources. You never add speculation or opinion."""
            
            # Call Claude API with prompt caching
            response = self.client.messages.create(
                model=config.ANTHROPIC_MODEL,
                max_tokens=config.ANTHROPIC_MAX_TOKENS,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract summary text
            summary_text = response.content[0].text.strip()
            
            # Calculate metrics
            generation_time_ms = int((time.time() - start_time) * 1000)
            word_count = len(summary_text.split())
            
            # Get token usage
            usage = response.usage
            prompt_tokens = usage.input_tokens
            completion_tokens = usage.output_tokens
            cached_tokens = getattr(usage, 'cache_read_input_tokens', 0)
            
            # Calculate cost (approximate)
            # Claude Sonnet 4: $3/MTok input, $15/MTok output, 90% cache discount
            input_cost = (prompt_tokens - cached_tokens) * 3.0 / 1_000_000
            cache_cost = cached_tokens * 0.30 / 1_000_000  # 90% discount
            output_cost = completion_tokens * 15.0 / 1_000_000
            total_cost = input_cost + cache_cost + output_cost
            
            # Determine version number
            version = 1
            if existing_summary:
                version = existing_summary.get('version', 0) + 1
            
            # Create SummaryVersion
            summary = SummaryVersion(
                version=version,
                text=summary_text,
                generated_at=datetime.now(timezone.utc),
                model=config.ANTHROPIC_MODEL,
                word_count=word_count,
                generation_time_ms=generation_time_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cached_tokens=cached_tokens,
                cost_usd=round(total_cost, 6)
            )
            
            logger.info(f"Generated summary v{version}: {word_count} words, "
                       f"{generation_time_ms}ms, ${total_cost:.4f}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}", exc_info=True)
            return None
    
    async def process_story(self, story_data: Dict[str, Any]):
        """Process a story for summarization"""
        try:
            story_id = story_data.get('id')
            category = story_data.get('category')
            status = story_data.get('status')
            source_articles = story_data.get('source_articles', [])
            existing_summary = story_data.get('summary')
            
            # Skip if not enough sources
            if len(source_articles) < config.MIN_SOURCES_FOR_DEVELOPING:
                logger.debug(f"Story {story_id} has only {len(source_articles)} sources, skipping")
                return
            
            # Skip if status is MONITORING
            if status == StoryStatus.MONITORING.value:
                logger.debug(f"Story {story_id} is MONITORING status, skipping")
                return
            
            # Check if we need to regenerate summary
            needs_summary = False
            
            if not existing_summary:
                needs_summary = True
                logger.info(f"Story {story_id} needs initial summary")
            elif len(source_articles) > existing_summary.get('source_count', 0):
                # New sources added, regenerate
                needs_summary = True
                logger.info(f"Story {story_id} has new sources, regenerating summary")
            
            if not needs_summary:
                logger.debug(f"Story {story_id} summary is up to date")
                return
            
            # Fetch source articles
            articles = []
            for article_id in source_articles:
                # Extract partition key from article ID
                # Format: source_YYYYMMDD_HHMMSS_hash
                parts = article_id.split('_')
                if len(parts) >= 2:
                    date_str = parts[1]  # YYYYMMDD
                    partition_key = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    
                    article = await cosmos_client.get_raw_article(article_id, partition_key)
                    if article:
                        articles.append(article)
            
            if not articles:
                logger.warning(f"Could not fetch articles for story {story_id}")
                return
            
            # Generate summary
            summary = await self.generate_summary(articles, existing_summary)
            
            if not summary:
                logger.error(f"Failed to generate summary for story {story_id}")
                return
            
            # Create version history entry if updating
            version_history = story_data.get('version_history', [])
            if existing_summary:
                history_entry = VersionHistory(
                    version=existing_summary.get('version', 1),
                    timestamp=datetime.fromisoformat(
                        existing_summary.get('generated_at', '').replace('Z', '+00:00')
                    ),
                    summary=existing_summary.get('text', ''),
                    source_count=len(source_articles) - 1,  # Previous count
                    status=StoryStatus(status)
                )
                version_history.append(history_entry.model_dump(mode='json'))
            
            # Update story with summary
            updates = {
                'summary': summary.model_dump(mode='json'),
                'version_history': version_history,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            await cosmos_client.update_story_cluster(story_id, category, updates)
            
            logger.info(f"Updated story {story_id} with summary version {summary.version}")
            
        except Exception as e:
            logger.error(f"Error processing story for summarization: {e}", exc_info=True)
            raise


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
    """
    Cosmos DB Change Feed trigger on story_clusters
    Generates AI summaries when stories are updated
    """
    
    if not documents:
        return
    
    logger.info(f"Processing {len(documents)} story updates for summarization")
    
    # Connect to Cosmos DB
    cosmos_client.connect()
    
    # Create summarization service
    summarizer = SummarizationService()
    
    # Process each document
    for doc in documents:
        try:
            story_data = json.loads(doc.to_json())
            await summarizer.process_story(story_data)
        except Exception as e:
            logger.error(f"Error processing story document: {e}")
            # Continue with next document
    
    logger.info(f"Completed summarization for {len(documents)} stories")

