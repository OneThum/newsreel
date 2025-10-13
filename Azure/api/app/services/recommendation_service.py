"""Recommendation Service"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class RecommendationService:
    """Story recommendation and personalization service"""
    
    def __init__(self):
        pass
    
    async def personalize_feed(
        self,
        stories: List[Dict[str, Any]],
        user_profile: Optional[Dict[str, Any]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Personalize story feed for user"""
        
        if not user_profile:
            # No personalization, return top stories by importance
            return self._rank_by_importance(stories, limit)
        
        # Get user preferences
        preferences = user_profile.get('preferences', {})
        personalization = user_profile.get('personalization_profile', {})
        
        # Score each story
        scored_stories = []
        for story in stories:
            score = await self._score_story(story, preferences, personalization)
            scored_stories.append((score, story))
        
        # Sort by score
        scored_stories.sort(reverse=True, key=lambda x: x[0])
        
        # Apply diversity filter
        diverse_stories = self._apply_diversity(scored_stories, limit)
        
        return diverse_stories
    
    async def _score_story(
        self,
        story: Dict[str, Any],
        preferences: Dict[str, Any],
        personalization: Dict[str, Any]
    ) -> float:
        """Score a story for personalization"""
        
        score = 50.0  # Base score
        
        # Factor 1: Importance score (0-40 points)
        importance = story.get('importance_score', 50)
        score += (importance / 100) * 40
        
        # Factor 2: Verification level (0-20 points)
        verification = story.get('verification_level', 1)
        score += min(verification * 5, 20)
        
        # Factor 3: Category preference (0-30 points)
        category = story.get('category', 'general')
        category_scores = personalization.get('category_scores', {})
        if category in category_scores:
            category_preference = category_scores[category]
            score += category_preference * 30
        else:
            # Default category score
            preferred_categories = preferences.get('categories', [])
            if category in preferred_categories:
                score += 20
        
        # Factor 4: Recency (0-10 points)
        last_updated = story.get('last_updated')
        if last_updated:
            try:
                updated_dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                age_hours = (datetime.now(updated_dt.tzinfo) - updated_dt).total_seconds() / 3600
                
                # Newer stories get higher scores
                if age_hours < 1:
                    score += 10
                elif age_hours < 6:
                    score += 7
                elif age_hours < 24:
                    score += 4
                else:
                    score += 1
            except Exception:
                pass
        
        # Factor 5: Breaking news boost
        if story.get('breaking_news'):
            score += 20
        
        # Factor 6: Source boost/mute
        # (Would need to check source articles)
        
        return score
    
    def _rank_by_importance(self, stories: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Rank stories by importance score"""
        sorted_stories = sorted(
            stories,
            key=lambda s: (
                s.get('breaking_news', False),
                s.get('importance_score', 50),
                s.get('verification_level', 1)
            ),
            reverse=True
        )
        return sorted_stories[:limit]
    
    def _apply_diversity(
        self,
        scored_stories: List[tuple],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Apply diversity filter to avoid too many stories from same category"""
        
        selected = []
        category_counts = {}
        max_per_category = max(3, limit // 4)  # At least 3, or 25% of limit
        
        for score, story in scored_stories:
            if len(selected) >= limit:
                break
            
            category = story.get('category', 'general')
            count = category_counts.get(category, 0)
            
            if count < max_per_category:
                selected.append(story)
                category_counts[category] = count + 1
        
        # If we haven't reached limit, add remaining stories
        if len(selected) < limit:
            for score, story in scored_stories:
                if story not in selected:
                    selected.append(story)
                    if len(selected) >= limit:
                        break
        
        return selected
    
    async def update_user_profile_from_interactions(
        self,
        user_profile: Dict[str, Any],
        interactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Update user personalization profile based on interactions"""
        
        # Count interactions by category
        category_interactions = {}
        total_interactions = len(interactions)
        
        for interaction in interactions:
            story_id = interaction.get('story_id')
            interaction_type = interaction.get('interaction_type')
            
            # Would need to fetch story to get category
            # For now, placeholder implementation
            
            # Weight different interaction types
            weight = 1.0
            if interaction_type == 'like':
                weight = 3.0
            elif interaction_type == 'save':
                weight = 5.0
            elif interaction_type == 'share':
                weight = 4.0
            elif interaction_type == 'view':
                weight = 1.0
        
        # Update personalization profile
        personalization = user_profile.get('personalization_profile', {})
        
        # This would include more sophisticated ML-based personalization
        # For now, simple interaction counting
        
        return personalization


# Global instance
recommendation_service = RecommendationService()

