"""
Structured logging utility for Newsreel Azure Functions
Provides consistent logging with correlation IDs, performance metrics, and categorization
"""
import logging
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from contextlib import contextmanager
import uuid

class StructuredLogger:
    """Enhanced logger with structured output for Azure Application Insights"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.correlation_id: Optional[str] = None
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for tracking requests across services"""
        self.correlation_id = correlation_id
    
    def _log(self, level: str, message: str, **kwargs):
        """Internal logging with structured data"""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "correlation_id": self.correlation_id or str(uuid.uuid4()),
            **kwargs
        }
        
        # Embed structured data in message for Application Insights parsing
        # Format: message | JSON for easy querying
        log_method = getattr(self.logger, level.lower())
        if kwargs:
            structured_msg = f"{message} | {json.dumps(kwargs)}"
        else:
            structured_msg = message
        log_method(structured_msg)
    
    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log("DEBUG", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)
        self._log("ERROR", message, **kwargs)
    
    # Specialized logging for key events
    
    def log_rss_fetch(self, source: str, success: bool, article_count: int = 0, 
                      duration_ms: int = 0, status_code: Optional[int] = None):
        """Log RSS feed fetch operation"""
        self.info(
            f"RSS Fetch: {source}",
            event_type="rss_fetch",
            source=source,
            success=success,
            article_count=article_count,
            duration_ms=duration_ms,
            status_code=status_code
        )
    
    def log_article_processed(self, article_id: str, source: str, category: str, 
                              fingerprint: str, matched_story: bool):
        """Log article processing"""
        self.info(
            f"Article Processed: {article_id}",
            event_type="article_processed",
            article_id=article_id,
            source=source,
            category=category,
            fingerprint=fingerprint,
            matched_story=matched_story
        )
    
    def log_story_cluster(self, story_id: str, action: str, source_count: int, 
                          category: str, fingerprint: str, title: str, status: str = None):
        """Log story clustering operation with status for monitoring badge accuracy"""
        self.info(
            f"Story Cluster: {action} - {story_id} [{status or 'unknown'}]",
            event_type="story_cluster",
            story_id=story_id,
            action=action,  # 'created', 'updated', 'merged'
            source_count=source_count,
            status=status,  # MONITORING, DEVELOPING, VERIFIED, BREAKING
            category=category,
            fingerprint=fingerprint,
            title=title[:100]
        )
    
    def log_summary_generated(self, story_id: str, source_count: int, word_count: int, 
                             duration_ms: int, model: str):
        """Log AI summary generation"""
        self.info(
            f"Summary Generated: {story_id}",
            event_type="summary_generated",
            story_id=story_id,
            source_count=source_count,
            word_count=word_count,
            duration_ms=duration_ms,
            model=model
        )
    
    def log_categorization(self, article_id: str, title: str, url: str, 
                          category: str, score: Optional[float] = None, 
                          method: str = "keyword"):
        """Log article categorization"""
        self.debug(
            f"Categorized: {category} - {title[:50]}",
            event_type="categorization",
            article_id=article_id,
            category=category,
            score=score,
            method=method,  # 'keyword', 'url', 'ml'
            url=url
        )
    
    def log_feed_diversity(self, total_stories: int, unique_sources: int, 
                          source_distribution: Dict[str, int]):
        """Log feed diversity metrics"""
        self.info(
            f"Feed Diversity: {unique_sources} sources across {total_stories} stories",
            event_type="feed_diversity",
            total_stories=total_stories,
            unique_sources=unique_sources,
            source_distribution=source_distribution
        )
    
    @contextmanager
    def operation(self, operation_name: str, **kwargs):
        """Context manager for timing operations"""
        start_time = time.time()
        operation_id = str(uuid.uuid4())[:8]
        
        self.debug(
            f"Operation Started: {operation_name}",
            operation_name=operation_name,
            operation_id=operation_id,
            **kwargs
        )
        
        try:
            yield operation_id
            duration_ms = int((time.time() - start_time) * 1000)
            self.info(
                f"Operation Completed: {operation_name}",
                operation_name=operation_name,
                operation_id=operation_id,
                duration_ms=duration_ms,
                status="success",
                **kwargs
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.error(
                f"Operation Failed: {operation_name}",
                error=e,
                operation_name=operation_name,
                operation_id=operation_id,
                duration_ms=duration_ms,
                status="failed",
                **kwargs
            )
            raise


# Global logger instance
def get_logger(name: str) -> StructuredLogger:
    """Get or create a structured logger"""
    return StructuredLogger(name)

