"""
Event Signature Extraction - Phase 3 Clustering Overhaul

Extracts semantic event signatures from news articles to improve story clustering.
Identifies the core action, event type, and key attributes of news stories.
"""
import re
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class EventSignatureExtractor:
    """
    Extracts event signatures from news articles for better clustering.

    Event signatures capture:
    - Action verbs (announced, attacked, died, elected, etc.)
    - Event types (election, earthquake, merger, bankruptcy, etc.)
    - Scale indicators (breaking, massive, historic, unprecedented)
    - Temporal markers (just in, developing, ongoing)
    - Outcome indicators (won, lost, killed, injured)
    """

    def __init__(self):
        """Initialize the event signature extractor with predefined patterns."""
        # Action verbs that indicate events
        self.action_verbs = {
            # Political/Government
            'announced', 'declared', 'stated', 'confirmed', 'denied', 'proposed',
            'approved', 'rejected', 'passed', 'signed', 'vetoed', 'resigned',
            'appointed', 'elected', 'won', 'lost', 'defeated', 'nominated',

            # Conflict/War
            'attacked', 'bombed', 'fired', 'shot', 'killed', 'injured', 'died',
            'struck', 'hit', 'destroyed', 'damaged', 'evacuated', 'fled',

            # Business/Finance
            'acquired', 'merged', 'bought', 'sold', 'invested', 'raised', 'cut',
            'laid off', 'hired', 'fired', 'bankrupt', 'profitable', 'reported',

            # Legal/Crime
            'arrested', 'charged', 'convicted', 'sentenced', 'acquitted',
            'indicted', 'investigated', 'accused', 'pleaded', 'confessed',

            # Natural Disasters/Accidents
            'struck', 'hit', 'devastated', 'flooded', 'burned', 'collapsed',
            'crashed', 'derailed', 'exploded', 'leaked', 'spilled',

            # Health/Medical
            'diagnosed', 'treated', 'cured', 'vaccinated', 'infected',
            'recovered', 'died', 'hospitalized', 'tested',

            # Sports/Competition
            'scored', 'won', 'lost', 'beat', 'defeated', 'qualified', 'eliminated',
            'advanced', 'retired', 'injured', 'suspended',

            # General breaking news
            'happened', 'occurred', 'took place', 'broke out', 'erupted'
        }

        # Event type categories
        self.event_types = {
            # Natural Disasters
            'earthquake': ['earthquake', 'quake', 'tremor', 'aftershock'],
            'hurricane': ['hurricane', 'tropical storm', 'cyclone', 'typhoon'],
            'flood': ['flood', 'flooding', 'flash flood'],
            'fire': ['fire', 'wildfire', 'bushfire', 'forest fire'],
            'tornado': ['tornado', 'twister', 'funnel cloud'],

            # Human Conflicts
            'war': ['war', 'invasion', 'occupation', 'ceasefire'],
            'terrorism': ['terrorist', 'bombing', 'attack', 'explosion'],
            'shooting': ['shooting', 'gunfire', 'mass shooting'],
            'protest': ['protest', 'demonstration', 'riot', 'unrest'],

            # Politics
            'election': ['election', 'vote', 'ballot', 'campaign', 'candidate'],
            'government': ['government', 'parliament', 'congress', 'senate'],
            'policy': ['policy', 'law', 'bill', 'legislation', 'reform'],

            # Business
            'merger': ['merger', 'acquisition', 'takeover', 'buyout'],
            'bankruptcy': ['bankruptcy', 'insolvent', 'liquidation'],
            'earnings': ['earnings', 'profit', 'revenue', 'quarterly'],

            # Technology
            'launch': ['launch', 'release', 'unveiled', 'announced'],
            'hack': ['hack', 'breach', 'cyberattack', 'data breach'],
            'recall': ['recall', 'defect', 'safety issue'],

            # Health
            'pandemic': ['pandemic', 'epidemic', 'outbreak', 'virus'],
            'vaccine': ['vaccine', 'vaccination', 'immunization'],

            # Sports
            'championship': ['championship', 'final', 'tournament', 'league'],
            'record': ['record', 'historic', 'unprecedented', 'first']
        }

        # Scale and urgency indicators
        self.scale_indicators = {
            'breaking': ['breaking', 'urgent', 'emergency', 'crisis'],
            'massive': ['massive', 'huge', 'major', 'significant', 'substantial'],
            'historic': ['historic', 'historical', 'unprecedented', 'first time'],
            'deadly': ['deadly', 'fatal', 'killed', 'died', 'casualties'],
            'widespread': ['widespread', 'nationwide', 'global', 'international']
        }

        # Temporal indicators
        self.temporal_indicators = {
            'current': ['now', 'currently', 'ongoing', 'continuing', 'live'],
            'recent': ['just', 'recently', 'latest', 'new', 'fresh'],
            'future': ['planned', 'scheduled', 'expected', 'anticipated'],
            'past': ['previously', 'earlier', 'ago', 'yesterday']
        }

    def extract_signature(self, title: str, description: str = "", entities: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Extract event signature from article title and description.

        Args:
            title: Article title
            description: Article description/content
            entities: Extracted named entities

        Returns:
            Dictionary containing event signature components
        """
        text = f"{title} {description}".lower()

        # Extract components
        actions = self._extract_actions(text)
        event_types = self._extract_event_types(text)
        scale = self._extract_scale(text)
        temporal = self._extract_temporal(text)
        entities_involved = self._extract_key_entities(entities or [])

        # Create signature
        signature = {
            'actions': actions,
            'event_types': event_types,
            'scale': scale,
            'temporal': temporal,
            'entities': entities_involved,
            'confidence': self._calculate_confidence(actions, event_types, scale),
            'signature_hash': self._generate_signature_hash(actions, event_types, entities_involved)
        }

        return signature

    def _extract_actions(self, text: str) -> List[str]:
        """Extract action verbs from text."""
        found_actions = []
        words = re.findall(r'\b\w+\b', text.lower())

        for verb in self.action_verbs:
            if verb in words:
                # Get context around the verb
                verb_index = words.index(verb)
                context_start = max(0, verb_index - 2)
                context_end = min(len(words), verb_index + 3)
                context = ' '.join(words[context_start:context_end])

                found_actions.append({
                    'verb': verb,
                    'context': context,
                    'position': verb_index
                })

        # Return top 3 most relevant actions
        return sorted(found_actions, key=lambda x: x['position'])[:3]

    def _extract_event_types(self, text: str) -> List[str]:
        """Extract event type categories from text."""
        found_types = []

        for event_type, keywords in self.event_types.items():
            for keyword in keywords:
                if keyword in text:
                    found_types.append(event_type)
                    break  # Only add each type once

        return list(set(found_types))  # Remove duplicates

    def _extract_scale(self, text: str) -> List[str]:
        """Extract scale/urgency indicators from text."""
        found_scale = []

        for scale_type, indicators in self.scale_indicators.items():
            for indicator in indicators:
                if indicator in text:
                    found_scale.append(scale_type)
                    break

        return list(set(found_scale))

    def _extract_temporal(self, text: str) -> List[str]:
        """Extract temporal indicators from text."""
        found_temporal = []

        for temporal_type, indicators in self.temporal_indicators.items():
            for indicator in indicators:
                if indicator in text:
                    found_temporal.append(temporal_type)
                    break

        return list(set(found_temporal))

    def _extract_key_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract most relevant entities for signature."""
        if not entities:
            return []

        # Prioritize by entity type and salience
        prioritized = []
        for entity in entities:
            priority = 0
            entity_type = entity.get('type', '')

            # Person entities are often key to events
            if entity_type == 'PERSON':
                priority = 3
            elif entity_type in ['ORGANIZATION', 'LOCATION']:
                priority = 2
            elif entity_type == 'EVENT':
                priority = 1

            # Boost if mentioned in title (would need title context)
            if entity.get('salience', 0) > 0.5:
                priority += 1

            prioritized.append({
                'text': entity.get('text', ''),
                'type': entity_type,
                'priority': priority
            })

        # Return top entities by priority
        return sorted(prioritized, key=lambda x: x['priority'], reverse=True)[:5]

    def _calculate_confidence(self, actions: List[Dict], event_types: List[str], scale: List[str]) -> float:
        """Calculate confidence score for the extracted signature."""
        confidence = 0.0

        # Actions are strongest signal
        if actions:
            confidence += 0.4 * min(len(actions), 3) / 3  # Up to 0.4

        # Event types add confidence
        if event_types:
            confidence += 0.3 * min(len(event_types), 2) / 2  # Up to 0.3

        # Scale indicators boost confidence
        if scale:
            confidence += 0.2 * min(len(scale), 2) / 2  # Up to 0.2

        # Temporal context helps
        # (Already included in base scoring)

        return min(confidence, 1.0)

    def _generate_signature_hash(self, actions: List[Dict], event_types: List[str], entities: List[Dict]) -> str:
        """Generate a hash representing the event signature."""
        import hashlib

        # Create signature string
        signature_parts = []

        # Add action verbs
        action_verbs = [action['verb'] for action in actions]
        if action_verbs:
            signature_parts.append(f"actions:{','.join(sorted(action_verbs))}")

        # Add event types
        if event_types:
            signature_parts.append(f"types:{','.join(sorted(event_types))}")

        # Add key entities (top 2)
        key_entities = [e['text'].lower() for e in entities[:2] if e['priority'] >= 2]
        if key_entities:
            signature_parts.append(f"entities:{','.join(sorted(key_entities))}")

        signature_str = '|'.join(signature_parts) if signature_parts else 'none'

        # Generate hash
        return hashlib.md5(signature_str.encode()).hexdigest()[:12]

    def compare_signatures(self, sig1: Dict[str, Any], sig2: Dict[str, Any]) -> float:
        """
        Compare two event signatures for similarity.

        Args:
            sig1: First event signature
            sig2: Second event signature

        Returns:
            Similarity score (0-1)
        """
        if not sig1 or not sig2:
            return 0.0

        similarity = 0.0

        # Compare actions (most important)
        actions1 = {action['verb'] for action in sig1.get('actions', [])}
        actions2 = {action['verb'] for action in sig2.get('actions', [])}
        if actions1 or actions2:
            action_overlap = len(actions1.intersection(actions2))
            action_union = len(actions1.union(actions2))
            if action_union > 0:
                similarity += 0.4 * (action_overlap / action_union)

        # Compare event types
        types1 = set(sig1.get('event_types', []))
        types2 = set(sig2.get('event_types', []))
        if types1 or types2:
            type_overlap = len(types1.intersection(types2))
            type_union = len(types1.union(types2))
            if type_union > 0:
                similarity += 0.3 * (type_overlap / type_union)

        # Compare entities
        entities1 = {e['text'].lower() for e in sig1.get('entities', []) if e['priority'] >= 2}
        entities2 = {e['text'].lower() for e in sig2.get('entities', []) if e['priority'] >= 2}
        if entities1 or entities2:
            entity_overlap = len(entities1.intersection(entities2))
            entity_union = len(entities1.union(entities2))
            if entity_union > 0:
                similarity += 0.3 * (entity_overlap / entity_union)

        return similarity


# Global instance
_event_extractor = None


def get_event_extractor() -> EventSignatureExtractor:
    """Get global event signature extractor instance."""
    global _event_extractor
    if _event_extractor is None:
        _event_extractor = EventSignatureExtractor()
    return _event_extractor


def extract_event_signature(title: str, description: str = "", entities: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Convenience function to extract event signature from article.

    Args:
        title: Article title
        description: Article description
        entities: Extracted entities

    Returns:
        Event signature dictionary
    """
    extractor = get_event_extractor()
    return extractor.extract_signature(title, description, entities)


def compare_event_signatures(sig1: Dict[str, Any], sig2: Dict[str, Any]) -> float:
    """
    Convenience function to compare two event signatures.

    Args:
        sig1: First signature
        sig2: Second signature

    Returns:
        Similarity score (0-1)
    """
    extractor = get_event_extractor()
    return extractor.compare_signatures(sig1, sig2)
