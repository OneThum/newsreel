"""Utility functions for Azure Functions"""
import hashlib
import re
from datetime import datetime
from typing import List, Set, Tuple
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
    """Generate unique article ID based on source + URL only (no timestamp)
    
    This enables update-in-place: same URL from same source = same article ID
    When an article is updated, it overwrites the existing record instead of creating duplicates.
    
    Benefits:
    - 80% storage reduction (no duplicate updates)
    - Each source represented once per story (not 10x for 10 updates)
    - Faster queries (fewer records)
    - No API deduplication needed
    """
    # Use longer hash for uniqueness without timestamp
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    return f"{source}_{url_hash}"


def generate_story_fingerprint(title: str, entities: List[Entity]) -> str:
    """
    Generate story fingerprint for clustering - IMPROVED for better matching
    
    Strategy: Create fingerprints that capture the CORE story, not specific wording
    Example: "Trump announces policy" and "President Trump unveils approach" 
    should match on "trump policy"
    """
    # Normalize title
    title_normalized = title.lower().strip()
    title_normalized = re.sub(r'[^\w\s]', '', title_normalized)
    
    # Expanded stop words (more aggressive filtering)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'be',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                  'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
                  'says', 'after', 'over', 'about', 'into', 'through', 'during', 'before',
                  'under', 'between', 'out', 'against', 'among', 'throughout'}
    
    # Action words to remove (verbs that don't help identify stories)
    action_verbs = {'announces', 'unveils', 'reveals', 'confirms', 'denies', 'says', 
                    'reports', 'claims', 'stated', 'told', 'speaks', 'discusses'}
    
    # Get meaningful words - AGGRESSIVE reduction for broader matching
    words = title_normalized.split()
    
    # Focus on ONLY the most essential words (3+ chars, no stop/action words)
    key_words = [w for w in words 
                 if len(w) > 3  # Keep at 3 characters
                 and w not in stop_words 
                 and w not in action_verbs][:3]  # REDUCED from 5 to 3 - even fewer = much broader match
    
    # Extract ONLY the top entity (single most important concept)
    entity_texts = []
    for e in entities:
        if e.type in ['PERSON', 'LOCATION']:
            entity_texts.append(e.text.lower())
            break  # Take just the FIRST person/location
        elif e.type == 'ORGANIZATION' and not entity_texts:
            entity_texts.append(e.text.lower())
    entity_texts = entity_texts[:1]  # REDUCED from 2 to 1 - single entity = broadest match
    
    # Combine - focus on MINIMAL essential concepts only
    all_terms = set(key_words + entity_texts)
    
    # If we have very few terms, use just 2-3 words as fallback (not 4)
    if len(all_terms) < 2:
        all_terms = set([w for w in words if len(w) > 3 and w not in stop_words][:3])
    
    combined = '_'.join(sorted(all_terms))
    
    # Use VERY SHORT hash for extremely broad matching (6 chars instead of 8)
    # This means stories with similar core concepts will fingerprint together
    fingerprint_hash = hashlib.md5(combined.encode()).hexdigest()[:6]
    
    return fingerprint_hash


def generate_event_fingerprint(articles_fingerprints: List[str]) -> str:
    """Generate event fingerprint from article fingerprints"""
    combined = '_'.join(sorted(articles_fingerprints))
    return hashlib.md5(combined.encode()).hexdigest()[:16]


def extract_simple_entities(text: str) -> List[Entity]:
    """Simple entity extraction (placeholder for more sophisticated NER)"""
    entities = []
    
    # Simple capitalized word extraction as named entities
    words = text.split()
    capitalized = [w.strip('.,!?;:') for w in words if w and w[0].isupper() and len(w) > 2]
    
    # Common country names
    countries = {'US', 'USA', 'UK', 'China', 'Japan', 'Russia', 'France', 'Germany', 'India', 
                 'Canada', 'Australia', 'Brazil', 'Mexico', 'Italy', 'Spain'}
    
    for word in capitalized:
        if word in countries:
            entities.append(Entity(text=word, type='LOCATION'))
        elif word.endswith('land') or word.endswith('stan'):
            entities.append(Entity(text=word, type='LOCATION'))
        else:
            # Default to organization
            entities.append(Entity(text=word, type='ORGANIZATION'))
    
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
    Calculate AGGRESSIVE text similarity for news clustering
    
    Optimized for news: AP and CNN reporting same story should score 70-90%
    Uses multiple methods weighted toward keyword matching
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
    
    # Combine methods with NEWS-OPTIMIZED weights
    # - Keyword overlap: 50% (most important - same topics use same words)
    # - Entity matching: 30% (proper nouns are strong signals)
    # - Substring: 15% (catches variations)
    # - Jaccard: 5% (general similarity, but less important)
    final_score = (keyword_score * 0.50) + (entity_score * 0.30) + (substring_score * 0.15) + (jaccard * 0.05)
    
    # Boost score if there are multiple entity matches (strong signal)
    if entity_overlap >= 3:
        final_score = min(1.0, final_score * 1.2)  # 20% boost, capped at 1.0
    
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
    """Remove HTML tags from text"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
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

