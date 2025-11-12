"""Source name mappings for display"""

# Maps source_id to display name
SOURCE_DISPLAY_NAMES = {
    # Australian Sources
    "abc": "ABC News",
    "smh": "Sydney Morning Herald",
    "theage": "The Age",
    "theaustralian": "The Australian",
    "news_com_au": "News.com.au",
    "9news": "9News",
    "7news": "7News",
    
    # UK Sources
    "bbc": "BBC News",
    "guardian": "The Guardian",
    "telegraph": "The Telegraph",
    "independent": "The Independent",
    "dailymail": "Daily Mail",
    "times": "The Times",
    "sky": "Sky News",
    "mirror": "The Mirror",
    
    # US Sources
    "nyt": "New York Times",
    "wapo": "Washington Post",
    "wsj": "Wall Street Journal",
    "cnn": "CNN",
    "fox": "Fox News",
    "msnbc": "MSNBC",
    "nbc": "NBC News",
    "cbs": "CBS News",
    "npr": "NPR",
    "ap": "Associated Press",
    "reuters": "Reuters",
    "bloomberg": "Bloomberg",
    "usatoday": "USA Today",
    "latimes": "LA Times",
    "chicagotribune": "Chicago Tribune",
    "bostonglobe": "Boston Globe",
    "sfchronicle": "SF Chronicle",
    
    # Tech Sources
    "techcrunch": "TechCrunch",
    "verge": "The Verge",
    "wired": "Wired",
    "arstechnica": "Ars Technica",
    "engadget": "Engadget",
    "theverge": "The Verge",
    "cnet": "CNET",
    "zdnet": "ZDNet",
    "techradar": "TechRadar",
    
    # Sports Sources
    "espn": "ESPN",
    "si": "Sports Illustrated",
    "bleacherreport": "Bleacher Report",
    "sbnation": "SB Nation",
    "skysports": "Sky Sports",
    "bbc_sport": "BBC Sport",
    "nfl": "NFL",
    "nba": "NBA",
    "mlb": "MLB",
    
    # Science Sources
    "scientificamerican": "Scientific American",
    "newscientist": "New Scientist",
    "nature": "Nature",
    "sciencedaily": "Science Daily",
    "space": "Space.com",
    
    # Business Sources
    "ft": "Financial Times",
    "economist": "The Economist",
    "forbes": "Forbes",
    "fortune": "Fortune",
    "businessinsider": "Business Insider",
    "cnbc": "CNBC",
    
    # International
    "aljazeera": "Al Jazeera",
    "dw": "Deutsche Welle",
    "france24": "France 24",
    "rfi": "RFI",
    "scmp": "South China Morning Post",
    "straitstimes": "The Straits Times",
    "japantimes": "Japan Times",
    "toi": "Times of India",
    "haaretz": "Haaretz",
    
    # Health
    "webmd": "WebMD",
    "healthline": "Healthline",
    "medicalnewstoday": "Medical News Today",
    "mayoclinic": "Mayo Clinic",
    
    # Middle East
    "middleeasteye": "Middle East Eye",
    "middleeastmonitor": "Middle East Monitor",
    "albawaba": "Al Bawaba",
}


def get_source_display_name(source_id: str) -> str:
    """
    Get display name for a source ID
    
    Args:
        source_id: Source identifier (e.g., 'smh', 'bbc', 'nyt')
    
    Returns:
        Display name (e.g., 'Sydney Morning Herald', 'BBC News', 'New York Times')
        Falls back to title-cased source_id if not found
    """
    # Return mapped name if exists
    if source_id in SOURCE_DISPLAY_NAMES:
        return SOURCE_DISPLAY_NAMES[source_id]
    
    # Otherwise, return title-cased version of source_id
    # Convert underscores to spaces and title case
    return source_id.replace('_', ' ').title()

