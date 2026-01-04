"""
Category definitions - Single Source of Truth

All category logic should reference this file to ensure consistency
between RSS ingestion, AI summarization, API responses, and iOS client.

IMPORTANT: These values must match iOS NewsCategory.swift exactly!
"""

# Valid categories that can be assigned to stories
# These MUST match the iOS NewsCategory enum rawValues
VALID_CATEGORIES = {
    'top_stories',    # Breaking/important news (assigned by importance scoring, not content)
    'world',          # International news, conflicts, diplomacy
    'politics',       # Government, elections, legislation
    'business',       # Markets, economy, companies, finance
    'technology',     # Tech, AI, software, startups (NOT 'tech' - iOS expects 'technology')
    'science',        # Research, space, discoveries
    'health',         # Medical, diseases, healthcare
    'sports',         # Sports events, athletes, leagues
    'entertainment',  # Movies, music, celebrities, TV
    'lifestyle',      # How-to guides, product reviews, recipes, gift guides
    'environment',    # Climate, conservation, pollution
}

# Default category for unknown/unclassified content
DEFAULT_CATEGORY = 'world'

# Categories that should be EXCLUDED from "Top Stories" feed
# (These are valid categories but not "top news")
EXCLUDED_FROM_TOP_STORIES = {'lifestyle', 'entertainment'}

# Lifestyle patterns for detection - used by categorize_article()
# These patterns indicate content that should be categorized as 'lifestyle'
# regardless of what feed it came from
LIFESTYLE_PATTERNS = [
    # Product reviews & recommendations
    r'\bbest\b.*\b(?:for|of|to|in)\b',       # "best X for/of/to/in"
    r'\btop\s+\d+\b',                         # "top 10", "top 5"
    r'\b\d+\s+best\b',                        # "7 best", "10 best"
    r'\bhere\s+(?:are|is)\s+\d+\+?\b',       # "Here are 50+", "Here is 10"
    r'\breviewed?\b',                         # "review", "reviewed"
    r'\btested\b',                            # "tested"
    r'\b(?:tried|we)\s+(?:and\s+)?tested\b', # "tried and tested"
    r'\bbest\s+(?:buys?|picks?|choices?)\b', # "best buys", "best picks"
    r'\b(?:our|my)\s+(?:top\s+)?picks?\b',   # "our picks", "my top picks"
    r'\bwhat\s+to\s+(?:buy|get|wear|use)\b', # "what to buy/get/wear/use"
    r'\b(?:buyer|shopping)\s*(?:\'?s?)?\s+guide\b',  # "buyer's guide"
    
    # How-to & advice content
    r'\bguide\s+to\b',                        # "guide to"
    r'\bhow\s+to\b',                          # "how to"
    r'\btips?\s+(?:for|on|to)\b',            # "tips for/on/to"
    r'\badvice\b',                            # "advice"
    r'\bhere\'?s?\s+(?:what|how|why)\b',     # "Here's what to use", "Here's how"
    r'\byou\s+should\s+(?:too|also)\b',      # "you should too"
    r'\bwe\s+stopped\s+using\b',             # "We stopped using X"
    r'\bwhy\s+(?:i|we)\s+(?:stopped|switched|quit)\b',  # "why I stopped X"
    
    # Cooking & kitchen content
    r'\brecipes?\b',                          # "recipe", "recipes"
    r'\bcooking\s+(?:tip|hack|trick)\b',     # cooking tips
    r'\bkitchen\s+(?:tip|hack|trick)\b',     # kitchen tips
    r'\b(?:aluminum\s+)?foil\s+(?:for|in)\s+cooking\b',  # foil for cooking
    
    # Shopping & deals
    r'\bdeal[s]?\b.*\b(?:on|for)\b',         # "deals on/for"
    r'\bbargain\b',                           # "bargain"
    
    # Gift guides & holidays (NOT hard news)
    r'\bgift\s+(?:guide|ideas?)\b',          # "gift guide", "gift ideas"
    r'\b\d+\+?\s+(?:thoughtful\s+)?gifts?\b', # "50+ gifts", "10 thoughtful gifts"
    r'\bmother\'?s?\s+day\b',                # Mother's Day
    r'\bfather\'?s?\s+day\b',                # Father's Day
    r'\bvalentine\'?s?\b',                   # Valentine's
    r'\bholiday\s+(?:gift|idea|tip)\b',      # holiday gifts/ideas/tips
    r'\bshe\'?ll\s+love\b',                  # "gifts she'll love"
    r'\bhe\'?ll\s+love\b',                   # "gifts he'll love"
]


def is_valid_category(category: str) -> bool:
    """Check if a category is valid"""
    return category in VALID_CATEGORIES


def normalize_category(category: str) -> str:
    """
    Normalize category to valid value.
    
    Handles legacy/variant category names and returns the canonical form.
    """
    if not category:
        return DEFAULT_CATEGORY
    
    category = category.lower().strip()
    
    # Direct match
    if category in VALID_CATEGORIES:
        return category
    
    # Legacy/variant mappings
    legacy_mappings = {
        'tech': 'technology',           # Old shorthand
        'finance': 'business',          # Variant
        'medical': 'health',            # Variant  
        'international': 'world',       # Variant
        'climate': 'environment',       # Variant
        'government': 'politics',       # Variant
        'general': 'world',             # Catch-all -> world
        'us': 'world',                  # Regional -> world
        'uk': 'world',                  # Regional -> world
        'europe': 'world',              # Regional -> world
        'australia': 'world',           # Regional -> world
        'asia': 'world',                # Regional -> world
    }
    
    return legacy_mappings.get(category, DEFAULT_CATEGORY)

