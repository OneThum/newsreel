"""Utility functions for Azure Functions"""
import hashlib
import re
from datetime import datetime
from typing import List, Set, Tuple, Dict, Any, Optional
from .models import Entity


def is_spam_or_promotional(title: str, description: str, url: str) -> bool:
    """
    Detect promotional/spam content that shouldn't appear in news feed
    
    Returns True if content is spam/promotional, False if legitimate news
    """
    text = f"{title} {description}".lower()
    title_lower = title.lower()
    
    # CRITICAL: Explicit sponsored/promotional content indicators
    # These are highest priority and should never appear in feed
    explicit_spam_indicators = [
        'sponsored content',
        'sponsored post',
        'paid content',
        'paid partnership',
        'advertisement',
        'brought to you by',
        'in partnership with',
        'presented by',
        'promotional content',
        'advertorial',
        'native advertising',
    ]
    
    for indicator in explicit_spam_indicators:
        if indicator in title_lower or indicator in text:
            return True
    
    # Promotional keywords (deals, shopping, listicles for products)
    spam_patterns = [
        # Shopping/deals
        r'\d+\s+best.*(?:deals|products|buys|items)',
        r'(?:best|top)\s+\d+.*(?:deals|to shop|to buy)',
        r'amazon\s+deals',
        r'shop\s+(?:these|this|now)',
        r'(?:on sale|discounts?|save \$)',
        r'price drop',
        r'limited time offer',
        
        # Affiliate marketing indicators
        r'buy now',
        r'check out these',
        r'you need to (?:buy|shop)',
        r'must-have products',
        
        # Listicle spam (products) - ENHANCED patterns
        # Only flag "things" if it's clearly about products to buy/shop
        r'\d+\s+(?:products|items).*(?:you can|to).*(?:buy|shop|get)',
        r'\d+\s+(?:of the|the)?.*products.*(?:you can|to).*(?:buy|shop|get)',
        r'\d+\s+.*products.*(?:buy|shop).*(?:amazon|walmart|target)',
        r'products worth buying',
        r'items on sale',
        r'things to (?:buy|shop)',
        r'\d+\s+.*(?:useful|essential|must-have).*products',
        r'\d+.*travel products.*(?:buy|amazon)',
        
        # Gift guides (usually promotional)
        r'gift guide',
        r'best gifts for',
        
        # Generic clickbait + shopping
        r'you won\'t believe.*(?:deal|price)',
        r'products you can buy',
    ]
    
    # Check for spam patterns
    for pattern in spam_patterns:
        if re.search(pattern, text):
            return True
    
    # URL-based filtering (affiliate/shopping sections)
    spam_url_patterns = [
        r'/deals/',
        r'/shopping/',
        r'/products/',
        r'/coupons/',
        r'/reviews/best-',
        r'/affiliate',
    ]
    
    url_lower = url.lower()
    for pattern in spam_url_patterns:
        if re.search(pattern, url_lower):
            return True
    
    # Specific title patterns that are almost always spam
    if 'amazon deals' in title.lower():
        return True
    
    if re.match(r'^the \d+ best .* to (?:shop|buy)', title.lower()):
        return True
    
    # CRITICAL: Restaurant/dining/lifestyle content (not hard news)
    # Pattern: Short proper-noun-only titles (1-4 words, mostly capitalized)
    # with lifestyle context in description
    lifestyle_dining_keywords = [
        'restaurant', 'dining', 'menu', 'cafe', 'bistro', 'bar', 'pub',
        'eatery', 'upscale', 'fine dining', 'michelin', 'chef', 'culinary',
        'wine list', 'tasting menu', 'reservation', 'dine', 'brunch',
        'scenic', 'luxur', 'exquisite', 'perfect for', 'ideal for',
        'nestled', 'charm', 'atmosphere', 'ambiance', 'intimate',
        'cozy', 'elegant', 'sophisticated', 'award-winning',
        'food guide', 'where to eat', 'best restaurants'
    ]
    
    # Check if title is short and mostly capitalized (proper noun pattern)
    title_words = title.strip().split()
    if len(title_words) <= 4:  # 1-4 words
        capitalized_words = sum(1 for w in title_words if w and w[0].isupper())
        if capitalized_words >= len(title_words) * 0.7:  # 70%+ capitalized
            # Check if description/URL contains lifestyle/dining indicators
            if any(keyword in text for keyword in lifestyle_dining_keywords):
                return True
            # Check URL for lifestyle/dining sections
            if any(section in url_lower for section in ['/lifestyle/', '/food/', '/dining/', 
                                                         '/restaurants/', '/travel/', '/good-food/']):
                return True
            
            # CRITICAL: Even WITHOUT description, if URL pattern suggests restaurant guide
            # Examples: "/good-food/", "/food-drink/", "/best-restaurants/"
            restaurant_url_patterns = [
                '/good-food',
                '/best-restaurant',
                '/food-drink',
                '/venue',
                '/eating-out'
            ]
            if any(pattern in url_lower for pattern in restaurant_url_patterns):
                # And title is JUST a proper noun (restaurant name)
                # Block if no common news verbs/indicators
                news_indicators = ['says', 'announces', 'reports', 'confirms', 'claims', 
                                  'accuses', 'reveals', 'attack', 'fire', 'death', 'killed',
                                  'injured', 'arrested', 'charged', 'verdict', 'found']
                if not any(indicator in title.lower() for indicator in news_indicators):
                    return True
    
    return False


def generate_article_id(source: str, url: str, published_at: datetime) -> str:
    """Generate unique article ID including date for partitioning
    
    Format: {source}_{date}_{hash}
    Example: reuters_20251026_a1b2c3d4
    
    Includes date for efficient partition key usage in Cosmos DB.
    """
    # Include date for partitioning
    date_str = published_at.strftime('%Y%m%d')
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{source}_{date_str}_{url_hash}"


def generate_story_fingerprint(title: str, entities: List[Entity]) -> str:
    """
    Generate story fingerprint for clustering - IMPROVED for BETTER matching
    
    Strategy: Create fingerprints that capture the CORE story semantically
    
    CRITICAL FIX: Previous logic was TOO AGGRESSIVE
    - Only took 3 key words (reduced false positives but missed true matches)
    - Only took 1 entity (too restrictive)
    - Result: Articles about same event got DIFFERENT fingerprints
    
    New approach: Balance between specificity and breadth
    - Take more words (5-6) to capture full context while avoiding generic phrases
    - Take 2-3 entities (persons, orgs, locations)
    - Use full MD5 hash (not truncated) for precision
    """
    # Normalize title
    title_normalized = title.lower().strip()
    title_normalized = re.sub(r'[^\w\s]', '', title_normalized)
    
    # Essential stop words (only ultra-common ones)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'be',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                  'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
                  'says', 'after', 'over', 'about', 'into', 'through', 'during', 'before',
                  'under', 'between', 'out', 'against', 'among', 'throughout', 'up', 'down'}
    
    # Action words to remove (verbs that don't help identify stories)
    # Reduced set - only remove the most generic action verbs
    action_verbs = {'announces', 'unveils', 'reveals', 'confirms', 'denies', 
                    'reports', 'claims', 'stated', 'tells', 'speaks', 'discusses',
                    'says', 'told'}
    
    # Get meaningful words - BALANCED approach
    words = title_normalized.split()
    
    # Keep 5-6 core words (was 3) to capture full context while avoiding generic phrases
    key_words = [w for w in words 
                 if len(w) > 3  # 3+ characters  
                 and w not in stop_words 
                 and w not in action_verbs][:6]  # INCREASED from 3 to 6
    
    # Extract named entities (PERSONS, ORGS, LOCATIONS) - up to 3
    # These are CRUCIAL for story identification
    entity_texts = []
    entity_priority = []  # Track type for sorting (person/org > location)
    
    for e in entities:
        # Handle both Entity objects and dict format for compatibility
        entity_type = e.get('type') if isinstance(e, dict) else (e.type if hasattr(e, 'type') else None)
        entity_text = e.get('text') if isinstance(e, dict) else (e.text if hasattr(e, 'text') else None)
        
        if entity_text and entity_type in ['PERSON', 'ORGANIZATION', 'LOCATION']:
            entity_texts.append(entity_text.lower())
            # Prioritize persons and orgs over locations
            if entity_type in ['PERSON', 'ORGANIZATION']:
                entity_priority.insert(0, entity_text.lower())
            else:
                entity_priority.append(entity_text.lower())
    
    # Take top 2-3 entities (was 1) for better specificity
    entity_texts = (entity_priority + entity_texts)[:3]  # INCREASED from 1 to 3
    
    # Combine keywords and entities
    all_terms = set(key_words + entity_texts)
    
    # If we have very few terms, add more words as fallback
    if len(all_terms) < 3:
        fallback_words = [w for w in words if len(w) > 3 and w not in stop_words][:5]
        all_terms = set(fallback_words + entity_texts)
    
    combined = '_'.join(sorted(all_terms))
    
    # Use FULL MD5 hash (was truncated to 6 chars) for precision
    # Full hash ensures even slightly different combinations produce different fingerprints
    fingerprint_hash = hashlib.md5(combined.encode()).hexdigest()[:8]  # Use 8 chars for good balance
    
    return fingerprint_hash


def generate_event_fingerprint(articles_fingerprints: List[str]) -> str:
    """Generate event fingerprint from article fingerprints"""
    combined = '_'.join(sorted(articles_fingerprints))
    return hashlib.md5(combined.encode()).hexdigest()[:16]


async def extract_simple_entities_with_wikidata(text: str) -> List[Entity]:
    """
    Extract entities with Wikidata linking for disambiguation (Phase 3).

    Enhanced entity extraction with Wikidata knowledge base for better disambiguation.
    Links ambiguous entities to specific Wikidata entities.
    """
    entities = extract_simple_entities(text)

    if not config.WIKIDATA_LINKING_ENABLED or not entities:
        return entities

    try:
        from .wikidata_linking import get_wikidata_linker

        linker = await get_wikidata_linker()

        # Prepare entities for batch linking
        entity_dicts = [{'text': e.text, 'type': e.type} for e in entities]

        # Link entities to Wikidata
        linked_entities = await linker.batch_link_entities(entity_dicts, text)

        # Update entities with Wikidata information
        for entity in entities:
            wikidata_entity = linked_entities.get(entity.text)
            if wikidata_entity:
                entity.wikidata = {
                    'qid': wikidata_entity.qid,
                    'label': wikidata_entity.label,
                    'description': wikidata_entity.description,
                    'type': wikidata_entity.entity_type,
                    'url': f'https://www.wikidata.org/wiki/{wikidata_entity.qid}',
                    'popularity_score': wikidata_entity.sitelinks,
                    'confidence': wikidata_entity.score
                }
                entity.linked_name = wikidata_entity.label  # Override with canonical name

        logger.debug(f"Linked {sum(1 for e in entities if e.wikidata)} entities to Wikidata")

    except Exception as e:
        logger.warning(f"Wikidata linking failed: {e}")

    return entities


def extract_simple_entities(text: str) -> List[Entity]:
    """Enhanced entity extraction with basic string matching linking (Phase 1)"""
    entities = []

    # Simple capitalized word extraction as named entities
    words = text.split()
    capitalized = [w.strip('.,!?;:') for w in words if w and w[0].isupper() and len(w) > 2]

    # Known entity databases for basic linking
    countries = {
        'US': 'United States', 'USA': 'United States', 'UK': 'United Kingdom',
        'China': 'China', 'Japan': 'Japan', 'Russia': 'Russia', 'France': 'France',
        'Germany': 'Germany', 'India': 'India', 'Canada': 'Canada', 'Australia': 'Australia',
        'Brazil': 'Brazil', 'Mexico': 'Mexico', 'Italy': 'Italy', 'Spain': 'Spain'
    }

    organizations = {
        'CNN': 'Cable News Network', 'BBC': 'British Broadcasting Corporation',
        'Reuters': 'Reuters News Agency', 'AP': 'Associated Press',
        'NYT': 'The New York Times', 'WSJ': 'The Wall Street Journal',
        'Fox': 'Fox News', 'NBC': 'National Broadcasting Company',
        'CBS': 'CBS Broadcasting', 'ABC': 'American Broadcasting Company',
        'NATO': 'North Atlantic Treaty Organization', 'UN': 'United Nations',
        'WHO': 'World Health Organization', 'NASA': 'National Aeronautics and Space Administration',
        'FBI': 'Federal Bureau of Investigation', 'CIA': 'Central Intelligence Agency'
    }

    people_indicators = {'President', 'Prime', 'Minister', 'CEO', 'Director', 'Chairman',
                        'Senator', 'Governor', 'Mayor', 'Chief', 'Dr.', 'Professor'}

    for word in capitalized:
        # Phase 1: Basic string matching for entity linking
        if word in countries:
            entities.append(Entity(text=word, type='LOCATION', linked_name=countries[word]))
        elif word in organizations:
            entities.append(Entity(text=word, type='ORGANIZATION', linked_name=organizations[word]))
        elif word.endswith('land') or word.endswith('stan'):
            entities.append(Entity(text=word, type='LOCATION'))
        elif any(indicator in word for indicator in people_indicators):
            entities.append(Entity(text=word, type='PERSON'))
        else:
            # Default to organization for other capitalized words
            entities.append(Entity(text=word, type='ORGANIZATION'))

    # Phase 1: Enhanced entity linking - check for multi-word entities
    text_lower = text.lower()

    # Check for known multi-word organizations
    multi_word_orgs = {
        'white house': ('White House', 'United States Government'),
        'supreme court': ('Supreme Court', 'United States Judiciary'),
        'federal reserve': ('Federal Reserve', 'United States Central Bank'),
        'world health organization': ('World Health Organization', 'WHO'),
        'united nations': ('United Nations', 'UN'),
        'north atlantic treaty organization': ('NATO', 'North Atlantic Treaty Organization')
    }

    for phrase, (entity_text, linked_name) in multi_word_orgs.items():
        if phrase in text_lower:
            entities.append(Entity(text=entity_text, type='ORGANIZATION', linked_name=linked_name))

    # Remove duplicates
    seen = set()
    unique_entities = []
    for e in entities:
        key = (e.text, e.type)
        if key not in seen:
            seen.add(key)
            unique_entities.append(e)

    return unique_entities[:20]  # Limit to 20 entities


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate CONSERVATIVE text similarity for news clustering
    
    Optimized to prevent false clustering: Only truly related stories should score 85%+
    Uses balanced methods to avoid grouping unrelated topics
    """
    # Normalize
    t1_lower = text1.lower()
    t2_lower = text2.lower()
    
    # Expanded stop words (more aggressive filtering)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'be',
                  'have', 'has', 'had', 'says', 'said', 'reports', 'after'}
    
    # Method 1: Jaccard similarity (set-based) - reduced weight
    words1 = set(t1_lower.split())
    words2 = set(t2_lower.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    jaccard = len(intersection) / len(union) if union else 0.0
    
    # Method 2: ENHANCED keyword overlap (most important for news)
    # Extract significant keywords (3+ chars, no stop words)
    key_words1 = [w for w in t1_lower.split() if len(w) > 3 and w not in stop_words]
    key_words2 = [w for w in t2_lower.split() if len(w) > 3 and w not in stop_words]
    
    if not key_words1 or not key_words2:
        return jaccard  # Fall back to Jaccard only
    
    # Count matching keywords (bidirectional)
    keyword_matches = sum(1 for w in key_words1 if w in key_words2)
    keyword_score = keyword_matches / min(len(key_words1), len(key_words2))  # Changed to MIN for more generous scoring
    
    # Method 3: ENHANCED entity matching (proper nouns)
    # News stories about same event will share proper nouns (names, places)
    entities1 = set(w for w in text1.split() if len(w) > 3 and w[0].isupper())
    entities2 = set(w for w in text2.split() if len(w) > 3 and w[0].isupper())
    
    entity_overlap = len(entities1.intersection(entities2))
    entity_score = entity_overlap / min(len(entities1), len(entities2)) if entities1 and entities2 else 0
    
    # Method 4: Substring matching (catches partial/fuzzy matches)
    substring_matches = 0
    for w in key_words1:
        if len(w) > 4 and w in t2_lower:
            substring_matches += 1
    for w in key_words2:
        if len(w) > 4 and w in t1_lower:
            substring_matches += 1
    
    substring_score = substring_matches / (len(key_words1) + len(key_words2)) if (key_words1 or key_words2) else 0
    
    # Combine methods with CONSERVATIVE weights to prevent false clustering
    # - Keyword overlap: 40% (important but not dominant)
    # - Entity matching: 40% (proper nouns are strong signals)
    # - Substring: 15% (catches variations)
    # - Jaccard: 5% (general similarity, but less important)
    final_score = (keyword_score * 0.40) + (entity_score * 0.40) + (substring_score * 0.15) + (jaccard * 0.05)
    
    # NO BOOST - let the score stand on its own to prevent false positives
    
    return final_score


def categorize_article(title: str, description: str, url: str) -> str:
    """Categorize article based on content"""
    text = f"{title} {description}".lower()
    
    # Category keywords with weighted importance
    categories = {
        'politics': {
            'high': ['president', 'prime minister', 'parliament', 'congress', 'senate', 'white house', 
                     'government', 'minister', 'ministry', 'election', 'vote', 'campaign', 'legislation',
                     'supreme court', 'federal', 'state department', 'defense department', 'defence'],
            'medium': ['political', 'politician', 'policy', 'law', 'bill', 'regulation', 'governor',
                      'mayor', 'senator', 'representative', 'diplomat', 'cabinet', 'administration'],
            'low': ['voter', 'ballot', 'partisan', 'bipartisan']
        },
        'sports': {
            'high': ['f1', 'formula 1', 'nba', 'nfl', 'mlb', 'nhl', 'soccer', 'football', 'basketball', 
                     'baseball', 'hockey', 'tennis', 'golf', 'cricket', 'olympics', 'world cup'],
            'medium': ['sport', 'game', 'team', 'player', 'coach', 'championship', 'league', 
                      'match', 'tournament', 'season', 'playoff'],
            'low': ['score', 'goal', 'point', 'defeat', 'victory']  # Removed 'win' - too generic
        },
        'tech': {
            'high': ['apple', 'microsoft', 'google', 'facebook', 'amazon', 'netflix', 'tesla', 
                     'startup', 'silicon valley', 'artificial intelligence', 'machine learning',
                     'openai', 'chatgpt', 'iphone', 'android'],
            'medium': ['tech', 'software', 'app', 'digital', 'cyber', 'ai', 'computer', 'data',
                      'internet', 'online', 'website', 'platform'],
            'low': ['algorithm', 'code', 'programming', 'update']
        },
        'science': {
            'high': ['nasa', 'nobel', 'research paper', 'scientific study', 'climate change'],
            'medium': ['science', 'research', 'study', 'scientist', 'discovery', 'experiment', 
                      'physics', 'chemistry', 'biology', 'space', 'astronomy'],
            'low': ['theory', 'hypothesis', 'laboratory']
        },
        'business': {
            'high': ['wall street', 'stock market', 'nasdaq', 'dow jones', 'federal reserve',
                     'real estate', 'property market'],
            'medium': ['business', 'economy', 'market', 'stock', 'finance', 'company', 'ceo', 
                      'revenue', 'profit', 'trade', 'investment', 'property', 'housing', 'mortgage'],
            'low': ['earnings', 'quarter', 'sales']
        },
        'world': {
            'high': ['united nations', 'nato', 'european union', 'g7', 'g20', 'war', 'conflict',
                     'israel', 'gaza', 'ukraine', 'russia', 'china', 'immigration', 'refugee'],
            'medium': ['international', 'global', 'country', 'nation', 'foreign', 'embassy', 'border',
                      'peace deal', 'ceasefire', 'invasion', 'asylum', 'deportation', 'migrant'],
            'low': ['diplomatic', 'treaty', 'ambassador', 'visa']
        },
        'health': {
            'high': ['covid', 'pandemic', 'fda', 'cdc', 'who', 'coronavirus', 'cancer', 'tumor', 'tumour'],
            'medium': ['health', 'medical', 'doctor', 'hospital', 'disease', 'vaccine', 'patient', 
                      'treatment', 'drug', 'medicine', 'epidemic', 'surgery', 'care'],
            'low': ['symptom', 'diagnosis', 'healthcare', 'clinic']
        },
        'entertainment': {
            'high': ['oscar', 'grammy', 'emmy', 'tony award', 'golden globe', 'cannes', 'sundance',
                     'hollywood', 'broadway', 'box office'],
            'medium': ['actor', 'actress', 'film', 'movie', 'director', 'celebrity', 'star', 
                      'album', 'concert', 'music', 'band', 'singer', 'artist', 'show', 'series',
                      'netflix', 'disney', 'streaming', 'premiere', 'festival'],
            'low': ['entertainment', 'celebrity', 'performance', 'role', 'cast']
        }
    }
    
    # URL-based categorization (highest priority)
    # Only use URL for categorization if it's clearly in a dedicated section
    url_lower = url.lower()
    
    # Check for entertainment sections (stricter patterns)
    if any(pattern in url_lower for pattern in ['/entertainment/', '/movies/', '/music/', '/celebrity/', '/film/', '/showbiz/']):
        return 'entertainment'
    
    # Check for sports sections (stricter patterns - must be in path, not just anywhere)
    if any(pattern in url_lower for pattern in ['/sports/', '/sport/', 'espn.com', '/nba/', '/nfl/', '/mlb/', '/cricket/', '/football/', '/soccer/']):
        return 'sports'
    
    # Check for politics sections
    if any(pattern in url_lower for pattern in ['/politics/', '/political/', '/elections/', '/government/']):
        return 'politics'
    
    # Check for tech sections
    if any(pattern in url_lower for pattern in ['/tech/', '/technology/', 'techcrunch.com', 'wired.com', '/gadgets/']):
        return 'tech'
    
    # Check for business sections
    if any(pattern in url_lower for pattern in ['/business/', '/markets/', '/finance/', '/economy/', 'bloomberg.com', 'wsj.com']):
        return 'business'
    
    # Check for world/international sections
    if any(pattern in url_lower for pattern in ['/world/', '/international/', '/global/']):
        return 'world'
    
    # Weighted keyword-based categorization
    scores = {}
    for category, keyword_tiers in categories.items():
        score = 0
        score += sum(3 for keyword in keyword_tiers.get('high', []) if keyword in text)
        score += sum(2 for keyword in keyword_tiers.get('medium', []) if keyword in text)
        score += sum(1 for keyword in keyword_tiers.get('low', []) if keyword in text)
        
        if score > 0:
            scores[category] = score
    
    if scores:
        return max(scores, key=scores.get)
    
    return 'general'


def clean_html(text: str) -> str:
    """Remove HTML tags and decode HTML entities"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities (&amp; -> &, &#8220; -> ", etc.)
    import html
    text = html.unescape(text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to maximum length"""
    if not text:
        return ""
    
    text = clean_html(text)
    if len(text) <= max_length:
        return text
    
    # Truncate at word boundary
    truncated = text[:max_length].rsplit(' ', 1)[0]
    return truncated + '...'


# ============================================================================
# BATCH PROCESSING HELPERS
# ============================================================================

def build_summarization_prompt(articles: List[Dict[str, Any]]) -> tuple[str, str]:
    """Build prompt for summarization (used in both real-time and batch)
    
    Returns:
        tuple: (prompt, system_message)
    """
    # Build article texts
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
    
    return prompt, system_msg


def generate_fallback_summary(story_data: Dict[str, Any], articles: List[Dict[str, Any]]) -> str:
    """Generate a fallback summary when AI refuses or fails
    
    Args:
        story_data: Story cluster data
        articles: List of article dictionaries
        
    Returns:
        str: Fallback summary text
    """
    story_title = story_data.get('title', '')
    
    if not articles:
        return f"{story_title}. Details are being gathered from multiple sources."
    
    first_article = articles[0]
    description = first_article.get('description', first_article.get('content', ''))[:300]
    source = first_article.get('source', 'News sources')
    
    if len(articles) == 1:
        summary_text = f"{story_title}. According to {source}, {description}"
    else:
        source_names = [a.get('source', '') for a in articles[:3]]
        sources_text = ", ".join(source_names)
        summary_text = f"{story_title}. Multiple sources including {sources_text} are reporting on this story. {description}"
    
    # Clean up
    summary_text = summary_text.replace('\n', ' ').strip()
    summary_text = ' '.join(summary_text.split()[:100])
    
    return summary_text


def is_ai_refusal(summary_text: str) -> bool:
    """Check if AI response is a refusal to summarize

    Args:
        summary_text: The generated summary text

    Returns:
        bool: True if text appears to be a refusal
    """
    refusal_indicators = [
        "i cannot", "cannot create", "cannot provide", "insufficient",
        "would need", "please provide", "unable to", "not possible",
        "requires additional", "incomplete information", "lacks essential"
    ]

    return any(indicator in summary_text.lower() for indicator in refusal_indicators)


# ============================================================================
# SIMHASH DEDUPLICATION FUNCTIONS (Phase 1 Clustering Overhaul)
# ============================================================================

def detect_duplicates(article: Dict[str, Any], recent_hashes: Set[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Two-stage deduplication for news articles

    Stage 1: Exact match via SHA1 hash
    Stage 2: Near-duplicate via SimHash (Hamming distance <= 3)

    Args:
        article: RawArticle dict with title, description, source_domain
        recent_hashes: Set of recent exact hashes (SHA1) for fast lookup

    Returns:
        (is_duplicate, duplicate_type)
        duplicate_type: 'exact_duplicate' | 'syndication_duplicate' | None
    """
    from .config import config

    # Stage 1: Exact match via SHA1 hash
    exact_hash = hashlib.sha1(
        normalize_text(article.get('title', '')).encode() +
        article.get('source_domain', '').encode()
    ).hexdigest()

    if recent_hashes and exact_hash in recent_hashes:
        return True, 'exact_duplicate'

    # Stage 2: SimHash for near-duplicates
    combined_text = f"{article.get('title', '')} {article.get('description', '')}"
    simhash = compute_simhash(combined_text, config.SIMHASH_SHINGLE_SIZE, config.SIMHASH_BITS)

    # In a real implementation, we'd check against a database/cache of recent simhashes
    # For now, return False (this will be implemented when we add the hash storage)
    # TODO: Implement hash storage and lookup

    return False, None


def create_shingles(text: str, n: int = 3) -> List[str]:
    """Create n-grams (shingles) from text for SimHash computation

    Args:
        text: Input text
        n: Number of words per shingle (default: 3)

    Returns:
        List of shingle strings
    """
    # Normalize text: lowercase, remove punctuation, split into words
    normalized = normalize_text(text)
    words = normalized.split()

    # Create shingles (n-grams)
    shingles = []
    for i in range(len(words) - n + 1):
        shingle = ' '.join(words[i:i+n])
        shingles.append(shingle)

    return shingles


def compute_simhash(text: str, shingle_size: int = 3, bits: int = 64) -> int:
    """Compute SimHash fingerprint from text

    Args:
        text: Input text
        shingle_size: Number of words per shingle
        bits: Fingerprint size in bits (default: 64)

    Returns:
        64-bit integer SimHash fingerprint
    """
    # Create shingles
    shingles = create_shingles(text, shingle_size)

    if not shingles:
        # Fallback for very short texts
        shingles = [text.lower().strip()]

    # Initialize vector for each bit
    v = [0] * bits

    # Process each shingle
    for shingle in shingles:
        # Hash the shingle to get a 64-bit number
        h = int(hashlib.md5(shingle.encode()).hexdigest(), 16)

        # For each bit, increment/decrement based on bit value
        for i in range(bits):
            if h & (1 << i):
                v[i] += 1
            else:
                v[i] -= 1

    # Create fingerprint: 1 if v[i] > 0, else 0
    fingerprint = 0
    for i in range(bits):
        if v[i] > 0:
            fingerprint |= (1 << i)

    return fingerprint


def hamming_distance(hash1: int, hash2: int) -> int:
    """Calculate Hamming distance between two SimHash fingerprints

    Args:
        hash1: First SimHash fingerprint
        hash2: Second SimHash fingerprint

    Returns:
        Number of differing bits
    """
    x = hash1 ^ hash2  # XOR to find differing bits
    return bin(x).count('1')  # Count the 1s in binary representation


def normalize_text(text: str) -> str:
    """Normalize text for duplicate detection

    Args:
        text: Input text

    Returns:
        Normalized text (lowercase, punctuation removed)
    """
    if not text:
        return ""

    # Convert to lowercase
    normalized = text.lower()

    # Remove punctuation and extra whitespace
    import re
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)

    return normalized.strip()


# ============================================================================
# ADAPTIVE THRESHOLD FUNCTIONS (Phase 1 Clustering Overhaul)
# ============================================================================

def calculate_adaptive_threshold(article_age_hours: float, base_threshold: float = 0.50) -> float:
    """
    Calculate adaptive similarity threshold based on article age

    Strategy: Breaking news gets stricter threshold (higher), older stories get more lenient (lower)

    Args:
        article_age_hours: How many hours old the article is
        base_threshold: The default threshold to adapt from

    Returns:
        Adaptive threshold between 0.3 and 0.7
    """
    from .config import config

    if not config.CLUSTERING_USE_ADAPTIVE_THRESHOLD:
        return base_threshold

    # Adaptive threshold logic:
    # - Breaking news (< 12 hours): Stricter threshold (+0.1 to base)
    # - Recent news (12-72 hours): Standard threshold (base)
    # - Older news (> 72 hours): More lenient threshold (-0.1 to base)

    if article_age_hours < 12:
        # Breaking news - higher threshold (stricter)
        adaptive_threshold = min(base_threshold + 0.1, 0.7)
    elif article_age_hours < 72:
        # Recent news - standard threshold
        adaptive_threshold = base_threshold
    else:
        # Older news - lower threshold (more lenient)
        adaptive_threshold = max(base_threshold - 0.1, 0.3)

    return adaptive_threshold

