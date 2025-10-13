"""Stories API Router"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
import uuid

from ..models.requests import InteractionRequest
from ..models.responses import (
    StoryResponse, StoryDetailResponse, FeedResponse,
    SourceArticle, SummaryResponse, ErrorResponse
)
from ..services.cosmos_service import cosmos_service
from ..services.recommendation_service import recommendation_service
from ..middleware.auth import get_current_user, get_optional_user, check_rate_limit
from ..utils.source_names import get_source_display_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stories", tags=["stories"])


async def map_story_to_response(
    story: Dict[str, Any], 
    user: Optional[Dict[str, Any]] = None,
    include_sources: bool = False
):
    """Map Cosmos DB story to API response"""
    
    # Check if user has interacted with story
    user_liked = False
    user_saved = False
    
    if user:
        # Would query user interactions here
        # For now, placeholder
        pass
    
    # Handle summary - always include for all users (no paywall for now)
    summary_data = story.get('summary')
    summary = None
    
    if summary_data and summary_data.get('text'):
        # All users get AI summaries
        summary = SummaryResponse(
            text=summary_data.get('text', ''),
            version=summary_data.get('version', 1),
            word_count=summary_data.get('word_count', 0),
            generated_at=datetime.fromisoformat(
                summary_data.get('generated_at', '').replace('Z', '+00:00')
            ),
            status="available"
        )
    else:
        # Story exists but no summary yet
        # Check if story is recent (< 3 minutes old) - summary might be generating
        story_age_minutes = (datetime.now(timezone.utc) - datetime.fromisoformat(
            story.get('first_seen', '').replace('Z', '+00:00')
        )).total_seconds() / 60
        
        if story_age_minutes < 3:
            # Story is fresh, summary is likely generating
            summary = SummaryResponse(
                text="",  # Empty text
                version=0,
                word_count=0,
                generated_at=datetime.now(timezone.utc),
                status="generating"
            )
        # else: story is old without summary, status would be "none" (no summary object returned)
    
    # Get source count (get_story_sources returns ALREADY DEDUPLICATED sources)
    source_ids = story.get('source_articles', [])
    unique_source_count = len(source_ids)  # Default to raw count if query fails
    source_docs = []
    
    if source_ids:
        # get_story_sources now returns deduplicated sources (one per unique source name)
        source_docs = await cosmos_service.get_story_sources(source_ids)
        unique_source_count = len(source_docs)  # Already deduplicated!
    
    # Get sources if requested
    sources = []
    if include_sources and source_docs:
        # Convert already-deduplicated sources to SourceArticle responses
        sources = [
            SourceArticle(
                id=source['id'],
                source=get_source_display_name(source.get('source', '')),  # Use display name
                title=source.get('title', ''),
                article_url=source.get('article_url', ''),
                published_at=datetime.fromisoformat(
                    source.get('published_at', '').replace('Z', '+00:00')
                )
            )
            for source in source_docs
        ]
    
    if include_sources:
        # DEBUG: Add visible marker to confirm new code is running
        response_title = story.get('title', '')
        if unique_source_count != len(source_ids):
            response_title = f"[DEDUP: {len(source_ids)}→{unique_source_count}] {response_title}"
        
        return StoryDetailResponse(
            id=story['id'],
            title=response_title,
            category=story.get('category', 'general'),
            tags=story.get('tags', []),
            status=story.get('status', 'VERIFIED'),
            verification_level=story.get('verification_level', 1),
            summary=summary,
            source_count=unique_source_count,  # Use DEDUPLICATED count
            first_seen=datetime.fromisoformat(
                story.get('first_seen', '').replace('Z', '+00:00')
            ),
            last_updated=datetime.fromisoformat(
                story.get('last_updated', '').replace('Z', '+00:00')
            ),
            importance_score=story.get('importance_score', 50),
            breaking_news=story.get('breaking_news', False),
            user_liked=user_liked,
            user_saved=user_saved,
            sources=sources
        )
    else:
        return StoryResponse(
            id=story['id'],
            title=story.get('title', ''),
            category=story.get('category', 'general'),
            tags=story.get('tags', []),
            status=story.get('status', 'VERIFIED'),
            verification_level=story.get('verification_level', 1),
            summary=summary,
            source_count=unique_source_count,  # Use DEDUPLICATED count
            first_seen=datetime.fromisoformat(
                story.get('first_seen', '').replace('Z', '+00:00')
            ),
            last_updated=datetime.fromisoformat(
                story.get('last_updated', '').replace('Z', '+00:00')
            ),
            importance_score=story.get('importance_score', 50),
            breaking_news=story.get('breaking_news', False),
            user_liked=user_liked,
            user_saved=user_saved
        )


@router.get("/feed", response_model=List[StoryDetailResponse])
async def get_personalized_feed(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=50, description="Number of stories to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get personalized story feed for authenticated user
    
    Returns a personalized feed based on user preferences and interaction history.
    """
    
    # NEW MODEL: Free users get unlimited stories, but summaries are premium-only
    # No rate limiting on feed access - everyone can see stories
    # Premium feature is the AI summary, not the feed itself
    
    # Initialize Cosmos DB connection
    cosmos_service.connect()
    
    # Query stories
    stories = await cosmos_service.query_recent_stories(
        category=category,
        limit=limit * 2,  # Get extra for personalization filtering
        offset=offset
    )
    
    # Personalize feed
    personalized_stories = await recommendation_service.personalize_feed(
        stories=stories,
        user_profile=user,
        limit=limit
    )
    
    # Map to response WITH sources included
    # Performance: Fetch sources in parallel batches
    story_responses = []
    for story in personalized_stories:
        story_response = await map_story_to_response(story, user, include_sources=True)
        story_responses.append(story_response)
    
    # No more rate limiting on feed access!
    # Premium feature is summaries, not feed access
    # (Rate limiting code removed - unlimited feed for all users)
    
    # Return stories directly with sources included
    return story_responses


@router.get("/breaking", response_model=List[StoryDetailResponse])
async def get_breaking_news(
    limit: int = Query(10, ge=1, le=20, description="Number of stories to return"),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Get breaking news stories
    
    Returns recent breaking news. Premium users get real-time access,
    free users get 30-minute delayed access.
    """
    
    # Initialize Cosmos DB connection
    cosmos_service.connect()
    
    # Query breaking news - no delays or filtering for any users
    stories = await cosmos_service.query_breaking_news(limit=limit)
    
    # Map to response with sources included
    story_responses = []
    for story in stories:
        story_response = await map_story_to_response(story, user, include_sources=True)
        story_responses.append(story_response)
    
    return story_responses


@router.get("/search", response_model=List[StoryDetailResponse])
async def search_stories(
    q: str = Query(..., min_length=2, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=50, description="Number of results to return"),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Search stories by keywords in title, summary, or tags
    
    Searches across:
    - Story titles (highest weight)
    - AI summaries (medium weight)
    - Tags (medium weight)
    - Source headlines (lower weight)
    """
    
    # Initialize Cosmos DB connection
    cosmos_service.connect()
    
    # Build search query
    search_query = q.lower().strip()
    
    # Query Cosmos DB with text search
    # Note: Cosmos DB doesn't have full-text search, so we use CONTAINS
    query = """
    SELECT * FROM c
    WHERE (
        CONTAINS(LOWER(c.title), @search_term)
        OR (IS_DEFINED(c.summary.text) AND CONTAINS(LOWER(c.summary.text), @search_term))
        OR ARRAY_CONTAINS(c.tags, @search_term, true)
    )
    """
    
    parameters = [{"name": "@search_term", "value": search_query}]
    
    # Add category filter if provided
    if category:
        query += " AND c.category = @category"
        parameters.append({"name": "@category", "value": category})
    
    # Get story clusters container
    container = cosmos_service._get_container("story_clusters")
    
    # Execute query
    items = list(container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))
    
    # Sort by relevance (title matches first, then by recency)
    def relevance_score(story):
        score = 0
        title_lower = story.get('title', '').lower()
        summary_text = story.get('summary', {}).get('text', '').lower() if story.get('summary') else ''
        
        # Title exact match: highest score
        if search_query in title_lower:
            score += 100
        # Title word match
        if any(word in title_lower for word in search_query.split()):
            score += 50
        # Summary match
        if search_query in summary_text:
            score += 25
        # Recency bonus (newer = better)
        if story.get('last_updated'):
            from datetime import datetime, timezone
            try:
                last_updated = datetime.fromisoformat(story['last_updated'].replace('Z', '+00:00'))
                hours_old = (datetime.now(timezone.utc) - last_updated).total_seconds() / 3600
                score += max(0, 20 - hours_old)  # Up to 20 point bonus for recent stories
            except:
                pass
        
        return score
    
    # Sort by relevance
    items_sorted = sorted(items, key=relevance_score, reverse=True)
    
    # Apply limit
    items_limited = items_sorted[:limit]
    
    # Map to response with sources included
    story_responses = []
    for story in items_limited:
        story_response = await map_story_to_response(story, user, include_sources=True)
        story_responses.append(story_response)
    
    return story_responses


@router.get("/{story_id}", response_model=StoryDetailResponse)
async def get_story_detail(
    story_id: str,
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Get detailed story information including sources
    """
    
    # Initialize Cosmos DB connection
    cosmos_service.connect()
    
    # We need the category to query by partition key
    # For now, we'll query across partitions (less efficient but works)
    # In production, would include category in the request
    
    # Try common categories
    story = None
    for category in ['world', 'tech', 'science', 'business', 'general', 'sports', 'health']:
        story = await cosmos_service.get_story(story_id, category)
        if story:
            break
    
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found"
        )
    
    # Map story to response with sources
    return await map_story_to_response(story, user, include_sources=True)


@router.post("/{story_id}/interact", status_code=status.HTTP_201_CREATED)
async def record_interaction(
    story_id: str,
    interaction: InteractionRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Record user interaction with a story
    
    Tracks user interactions (view, like, save, share, etc.) for personalization.
    """
    
    # Initialize Cosmos DB connection
    cosmos_service.connect()
    
    # Create interaction record
    interaction_data = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'story_id': story_id,
        'interaction_type': interaction.interaction_type,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'session_id': interaction.session_id,
        'dwell_time_seconds': interaction.dwell_time_seconds,
        'card_flipped': interaction.card_flipped,
        'sources_clicked': interaction.sources_clicked,
        'device_info': interaction.device_info
    }
    
    # Store interaction
    await cosmos_service.create_interaction(interaction_data)
    
    # Update user interaction stats
    stats = user.get('interaction_stats', {})
    
    if interaction.interaction_type == 'view':
        stats['total_stories_viewed'] = stats.get('total_stories_viewed', 0) + 1
    elif interaction.interaction_type == 'like':
        stats['total_stories_liked'] = stats.get('total_stories_liked', 0) + 1
    elif interaction.interaction_type == 'save':
        stats['total_stories_saved'] = stats.get('total_stories_saved', 0) + 1
    elif interaction.interaction_type == 'share':
        stats['total_stories_shared'] = stats.get('total_stories_shared', 0) + 1
    
    if interaction.card_flipped:
        stats['total_cards_flipped'] = stats.get('total_cards_flipped', 0) + 1
    
    if interaction.sources_clicked:
        stats['total_sources_clicked'] = stats.get('total_sources_clicked', 0) + len(interaction.sources_clicked)
    
    await cosmos_service.update_user_profile(user['id'], {
        'interaction_stats': stats
    })
    
    logger.info(f"Recorded {interaction.interaction_type} interaction for user {user['id']} on story {story_id}")
    
    return {"status": "success", "message": "Interaction recorded"}


@router.get("/{story_id}/sources", response_model=List[SourceArticle])
async def get_story_sources(
    story_id: str,
    user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    Get source articles for a story
    """
    
    # Initialize Cosmos DB connection
    cosmos_service.connect()
    
    # Get story
    story = None
    for category in ['world', 'tech', 'science', 'business', 'general', 'sports', 'health']:
        story = await cosmos_service.get_story(story_id, category)
        if story:
            break
    
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found"
        )
    
    # Get sources
    source_ids = story.get('source_articles', [])
    sources = await cosmos_service.get_story_sources(source_ids)
    
    # Map to response
    source_responses = [
        SourceArticle(
            id=source['id'],
            source=get_source_display_name(source.get('source', '')),  # Use display name
            title=source.get('title', ''),
            article_url=source.get('article_url', ''),
            published_at=datetime.fromisoformat(
                source.get('published_at', '').replace('Z', '+00:00')
            )
        )
        for source in sources
    ]
    
    return source_responses

