"""
Wikidata Entity Linking - Phase 3 Clustering Overhaul

Provides entity disambiguation using Wikidata knowledge base.
Resolves ambiguous entity mentions to specific Wikidata entities.
"""
import logging
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re

from .config import config

logger = logging.getLogger(__name__)


@dataclass
class WikidataEntity:
    """Represents a Wikidata entity with metadata"""
    qid: str  # Wikidata QID (e.g., "Q90")
    label: str  # Entity label (e.g., "Paris")
    description: str  # Entity description
    entity_type: str  # P31 value (instance of)
    aliases: List[str]  # Alternative names
    sitelinks: int  # Number of Wikipedia sitelinks (popularity measure)
    claims: int  # Number of claims/statements
    score: float = 0.0  # Relevance score for disambiguation


class WikidataLinker:
    """
    Links extracted entities to Wikidata for disambiguation.

    Handles ambiguous entity mentions by:
    - Searching Wikidata API for candidates
    - Ranking based on context and popularity
    - Providing structured entity information
    """

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_url = "https://www.wikidata.org/w/api.php"

        # Cache for entity lookups
        self.cache: Dict[str, List[WikidataEntity]] = {}
        self.cache_max_size = 1000

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        """Initialize HTTP session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def link_entity(
        self,
        entity_text: str,
        entity_type: str,
        context: Optional[str] = None,
        max_candidates: int = 5
    ) -> Optional[WikidataEntity]:
        """
        Link an entity mention to Wikidata.

        Args:
            entity_text: The entity text (e.g., "Paris")
            entity_type: NER type (PERSON, LOCATION, ORGANIZATION, etc.)
            context: Surrounding text for disambiguation
            max_candidates: Maximum candidates to consider

        Returns:
            Best matching Wikidata entity or None
        """
        await self.start()

        try:
            # Search for entity candidates
            candidates = await self._search_entities(entity_text, max_candidates * 2)

            if not candidates:
                return None

            # Rank candidates based on context and type
            ranked_candidates = await self._rank_candidates(
                candidates, entity_text, entity_type, context
            )

            # Return top candidate if confidence is high enough
            if ranked_candidates and ranked_candidates[0].score > 0.6:
                return ranked_candidates[0]

            return None

        except Exception as e:
            logger.warning(f"Wikidata linking failed for '{entity_text}': {e}")
            return None

    async def _search_entities(self, query: str, limit: int = 10) -> List[WikidataEntity]:
        """
        Search Wikidata for entities matching the query.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            List of WikidataEntity objects
        """
        # Check cache first
        cache_key = query.lower().strip()
        if cache_key in self.cache:
            return self.cache[cache_key][:limit]

        await self.start()

        params = {
            'action': 'wbsearchentities',
            'search': query,
            'language': 'en',
            'limit': limit,
            'format': 'json'
        }

        try:
            async with self.session.get(self.api_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                entities = []
                for item in data.get('search', []):
                    entity = await self._fetch_entity_details(item['id'])
                    if entity:
                        entities.append(entity)

                # Cache results
                self._cache_results(cache_key, entities)

                return entities

        except Exception as e:
            logger.error(f"Wikidata search failed for '{query}': {e}")
            return []

    async def _fetch_entity_details(self, qid: str) -> Optional[WikidataEntity]:
        """
        Fetch detailed information for a Wikidata entity.

        Args:
            qid: Wikidata QID

        Returns:
            WikidataEntity with full details
        """
        await self.start()

        params = {
            'action': 'wbgetentities',
            'ids': qid,
            'languages': 'en',
            'props': 'labels|descriptions|aliases|sitelinks|claims',
            'format': 'json'
        }

        try:
            async with self.session.get(self.api_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                entity_data = data.get('entities', {}).get(qid)
                if not entity_data:
                    return None

                # Extract basic information
                labels = entity_data.get('labels', {})
                descriptions = entity_data.get('descriptions', {})
                aliases = entity_data.get('aliases', {})

                label = labels.get('en', {}).get('value', qid)
                description = descriptions.get('en', {}).get('value', '')

                # Extract aliases
                alias_list = []
                if 'en' in aliases:
                    alias_list = [alias['value'] for alias in aliases['en']]

                # Extract entity type (instance of - P31)
                entity_type = self._extract_entity_type(entity_data)

                # Extract popularity metrics
                sitelinks = len(entity_data.get('sitelinks', {}))
                claims = len(entity_data.get('claims', {}))

                return WikidataEntity(
                    qid=qid,
                    label=label,
                    description=description,
                    entity_type=entity_type,
                    aliases=alias_list,
                    sitelinks=sitelinks,
                    claims=claims
                )

        except Exception as e:
            logger.error(f"Failed to fetch entity details for {qid}: {e}")
            return None

    def _extract_entity_type(self, entity_data: Dict[str, Any]) -> str:
        """Extract the primary entity type (instance of) from Wikidata claims."""
        claims = entity_data.get('claims', {})
        p31_claims = claims.get('P31', [])  # P31 = instance of

        if not p31_claims:
            return 'unknown'

        # Get the first instance-of value
        for claim in p31_claims:
            mainsnak = claim.get('mainsnak', {})
            datavalue = mainsnak.get('datavalue', {})
            if datavalue.get('type') == 'wikibase-entityid':
                qid = datavalue['value']['id']
                # Map common QIDs to readable types
                type_mapping = {
                    'Q5': 'person',      # human
                    'Q43229': 'organization',  # organization
                    'Q618123': 'geographical feature',  # geographical feature
                    'Q6256': 'country',   # country
                    'Q515': 'city',       # city
                    'Q7275': 'state',     # state
                    'Q783794': 'company', # business
                    'Q6881511': 'enterprise',  # enterprise
                    'Q4830453': 'business',    # business
                    'Q849122': 'newspaper',    # newspaper
                    'Q11032': 'newspaper',     # newspaper
                }
                return type_mapping.get(qid, 'entity')

        return 'entity'

    async def _rank_candidates(
        self,
        candidates: List[WikidataEntity],
        entity_text: str,
        entity_type: str,
        context: Optional[str] = None
    ) -> List[WikidataEntity]:
        """
        Rank entity candidates based on relevance to the context.

        Args:
            candidates: List of WikidataEntity candidates
            entity_text: Original entity text
            entity_type: NER entity type
            context: Surrounding text context

        Returns:
            Ranked list of candidates (highest score first)
        """
        for candidate in candidates:
            score = 0.0

            # Base score from Wikidata popularity
            popularity_score = min(candidate.sitelinks / 100, 1.0)  # Cap at 100 sitelinks
            score += popularity_score * 0.3

            # Exact label match bonus
            if candidate.label.lower() == entity_text.lower():
                score += 0.4
            elif entity_text.lower() in candidate.label.lower():
                score += 0.2

            # Alias match bonus
            for alias in candidate.aliases:
                if alias.lower() == entity_text.lower():
                    score += 0.3
                    break
                elif entity_text.lower() in alias.lower():
                    score += 0.15
                    break

            # Entity type consistency bonus
            type_consistency = self._calculate_type_consistency(candidate.entity_type, entity_type)
            score += type_consistency * 0.2

            # Context-based scoring
            if context:
                context_score = self._calculate_context_score(candidate, context)
                score += context_score * 0.2

            candidate.score = score

        # Sort by score (descending)
        return sorted(candidates, key=lambda x: x.score, reverse=True)

    def _calculate_type_consistency(self, wikidata_type: str, ner_type: str) -> float:
        """Calculate consistency between Wikidata type and NER type."""
        type_mapping = {
            'PERSON': ['person'],
            'LOCATION': ['city', 'state', 'country', 'geographical feature'],
            'ORGANIZATION': ['organization', 'company', 'business', 'newspaper', 'enterprise'],
            'GPE': ['city', 'state', 'country', 'geographical feature']
        }

        expected_types = type_mapping.get(ner_type.upper(), [])
        if wikidata_type in expected_types:
            return 1.0
        elif wikidata_type == 'entity':  # Generic fallback
            return 0.5
        else:
            return 0.0

    def _calculate_context_score(self, candidate: WikidataEntity, context: str) -> float:
        """Calculate relevance score based on context."""
        score = 0.0
        context_lower = context.lower()

        # Check if description keywords appear in context
        if candidate.description:
            desc_words = set(re.findall(r'\b\w+\b', candidate.description.lower()))
            context_words = set(re.findall(r'\b\w+\b', context_lower))

            overlap = len(desc_words.intersection(context_words))
            if overlap > 0:
                score += min(overlap / len(desc_words), 1.0) * 0.5

        # Check if entity label appears in context (beyond the entity itself)
        # This helps with co-reference resolution
        if candidate.label.lower() in context_lower:
            score += 0.3

        # Check for type-specific context clues
        if candidate.entity_type == 'person':
            # Look for person indicators in context
            person_indicators = ['president', 'minister', 'director', 'actor', 'author', 'scientist']
            if any(indicator in context_lower for indicator in person_indicators):
                score += 0.2

        elif candidate.entity_type in ['city', 'country', 'state']:
            # Look for location indicators
            location_indicators = ['capital', 'located', 'based', 'headquarters', 'city', 'country']
            if any(indicator in context_lower for indicator in location_indicators):
                score += 0.2

        return min(score, 1.0)

    def _cache_results(self, key: str, entities: List[WikidataEntity]):
        """Cache search results."""
        self.cache[key] = entities

        # Simple cache size management
        if len(self.cache) > self.cache_max_size:
            # Remove oldest entries (simple FIFO)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

    async def get_entity_info(self, qid: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a Wikidata entity.

        Args:
            qid: Wikidata QID

        Returns:
            Dictionary with entity information
        """
        entity = await self._fetch_entity_details(qid)
        if not entity:
            return None

        return {
            'qid': entity.qid,
            'label': entity.label,
            'description': entity.description,
            'type': entity.entity_type,
            'aliases': entity.aliases,
            'popularity_score': entity.sitelinks,
            'url': f'https://www.wikidata.org/wiki/{entity.qid}'
        }

    async def batch_link_entities(
        self,
        entities: List[Dict[str, Any]],
        context: Optional[str] = None
    ) -> Dict[str, Optional[WikidataEntity]]:
        """
        Link multiple entities in batch.

        Args:
            entities: List of entity dictionaries with 'text' and 'type' keys
            context: Shared context for all entities

        Returns:
            Dictionary mapping entity text to WikidataEntity (or None)
        """
        results = {}

        # Process in parallel with some concurrency control
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests

        async def link_single(entity_dict):
            async with semaphore:
                return await self.link_entity(
                    entity_dict['text'],
                    entity_dict['type'],
                    context
                )

        tasks = [link_single(entity) for entity in entities]
        linked_entities = await asyncio.gather(*tasks, return_exceptions=True)

        for entity, result in zip(entities, linked_entities):
            if isinstance(result, Exception):
                logger.warning(f"Failed to link entity '{entity['text']}': {result}")
                results[entity['text']] = None
            else:
                results[entity['text']] = result

        return results


# Global instance
_wikidata_linker = None


async def get_wikidata_linker() -> WikidataLinker:
    """Get global Wikidata linker instance."""
    global _wikidata_linker
    if _wikidata_linker is None:
        _wikidata_linker = WikidataLinker()
        await _wikidata_linker.start()
    return _wikidata_linker


async def link_entity_to_wikidata(
    entity_text: str,
    entity_type: str,
    context: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Convenience function to link an entity to Wikidata.

    Args:
        entity_text: Entity text
        entity_type: NER type
        context: Surrounding context

    Returns:
        Wikidata entity information or None
    """
    linker = await get_wikidata_linker()
    entity = await linker.link_entity(entity_text, entity_type, context)

    if entity:
        return await linker.get_entity_info(entity.qid)
    return None
