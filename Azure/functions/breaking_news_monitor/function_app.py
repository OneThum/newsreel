"""
Breaking News Monitor Function
Timer-triggered function that monitors Twitter for breaking news signals
Runs every 2 minutes
"""
import azure.functions as func
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import config
from shared.cosmos_client import cosmos_client

logger = logging.getLogger(__name__)
app = func.FunctionApp()


class BreakingNewsMonitor:
    """Monitor for breaking news signals"""
    
    def __init__(self):
        self.twitter_bearer_token = config.TWITTER_BEARER_TOKEN
    
    async def check_breaking_stories(self) -> List[Dict[str, Any]]:
        """Check for breaking news stories in Cosmos DB"""
        try:
            # Query stories marked as breaking that haven't sent notifications
            breaking_stories = await cosmos_client.query_breaking_news(limit=20)
            
            # Filter to only those that haven't sent notifications
            stories_to_notify = [
                story for story in breaking_stories
                if not story.get('push_notification_sent', False)
            ]
            
            return stories_to_notify
            
        except Exception as e:
            logger.error(f"Error checking breaking stories: {e}")
            return []
    
    async def queue_push_notification(self, story: Dict[str, Any]):
        """Queue a push notification for breaking news"""
        try:
            story_id = story.get('id')
            category = story.get('category')
            
            # In a full implementation, this would:
            # 1. Query user profiles for users who have notifications enabled
            # 2. Filter by user preferences (categories, quiet hours, etc.)
            # 3. Queue messages to Azure Notification Hubs
            # 4. Track notification delivery
            
            # For now, just mark as sent
            logger.info(f"Would send push notification for story: {story_id}")
            
            # Update story to mark notification as sent
            updates = {
                'push_notification_sent': True,
                'push_notification_sent_at': datetime.now(timezone.utc).isoformat()
            }
            
            await cosmos_client.update_story_cluster(story_id, category, updates)
            
            logger.info(f"Marked notification as sent for story {story_id}")
            
        except Exception as e:
            logger.error(f"Error queueing push notification: {e}")
    
    async def monitor_twitter(self) -> List[Dict[str, Any]]:
        """Monitor Twitter for breaking news signals"""
        
        # Note: This is a placeholder implementation
        # A full implementation would:
        # 1. Connect to Twitter API v2 with bearer token
        # 2. Monitor tweets from verified news accounts
        # 3. Look for "BREAKING" keywords
        # 4. Extract entities and topics
        # 5. Trigger immediate RSS refresh for relevant feeds
        # 6. Cross-reference with existing stories
        
        if not self.twitter_bearer_token:
            logger.warning("Twitter bearer token not configured")
            return []
        
        logger.info("Twitter monitoring not yet implemented (placeholder)")
        
        # Placeholder: return empty list
        # In production, would return list of breaking news signals
        return []
    
    async def process_breaking_news(self):
        """Main processing logic"""
        logger.info("Starting breaking news monitoring")
        
        # Check for breaking stories in database
        breaking_stories = await self.check_breaking_stories()
        
        if breaking_stories:
            logger.info(f"Found {len(breaking_stories)} breaking stories to notify")
            
            for story in breaking_stories:
                await self.queue_push_notification(story)
        else:
            logger.info("No breaking stories requiring notifications")
        
        # Monitor Twitter for signals (Phase 2 feature)
        # twitter_signals = await self.monitor_twitter()
        
        logger.info("Breaking news monitoring complete")


@app.function_name(name="BreakingNewsMonitor")
@app.schedule(schedule="0 */2 * * * *", arg_name="timer", run_on_startup=False)
async def breaking_news_monitor_timer(timer: func.TimerRequest) -> None:
    """
    Timer trigger function that runs every 2 minutes
    Schedule: 0 */2 * * * * (every 2 minutes)
    """
    logger.info("Breaking news monitor timer triggered")
    
    try:
        # Connect to Cosmos DB
        cosmos_client.connect()
        
        # Create monitor
        monitor = BreakingNewsMonitor()
        
        # Process breaking news
        await monitor.process_breaking_news()
        
    except Exception as e:
        logger.error(f"Breaking news monitoring failed: {e}", exc_info=True)
        raise

