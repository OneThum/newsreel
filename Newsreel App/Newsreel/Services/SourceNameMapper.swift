//
//  SourceNameMapper.swift
//  Newsreel
//
//  Centralized source name mapping utility
//  Maps backend source IDs to proper display names
//

import Foundation

/// Utility for mapping source IDs to proper display names
enum SourceNameMapper {
    
    /// Comprehensive mapping of source IDs to proper display names
    private static let sourceDisplayNames: [String: String] = [
        // Major News Agencies
        "bbc": "BBC",
        "bbc news": "BBC News",
        "bbc-news": "BBC News",
        "bbc_news": "BBC News",
        "bbc_world": "BBC World",
        "bbc_uk": "BBC UK",
        "bbc_tech": "BBC Technology",
        "bbc_business": "BBC Business",
        "reuters": "Reuters",
        "ap": "Associated Press",
        "afp": "AFP",
        
        // US Major News
        "cnn": "CNN",
        "nyt": "New York Times",
        "wapo": "Washington Post",
        "wsj": "Wall Street Journal",
        "usatoday": "USA Today",
        "latimes": "LA Times",
        
        // US Broadcast
        "abc": "ABC News",
        "nbc": "NBC News",
        "cbs": "CBS News",
        "fox": "Fox News",
        "pbs": "PBS",
        "npr": "NPR",
        
        // US Tech
        "techcrunch": "TechCrunch",
        "verge": "The Verge",
        "wired": "Wired",
        "arstechnica": "Ars Technica",
        "engadget": "Engadget",
        "theverge": "The Verge",
        
        // UK News
        "guardian": "The Guardian",
        "telegraph": "The Telegraph",
        "independent": "The Independent",
        "ft": "Financial Times",
        "mirror": "Daily Mirror",
        "dailymail": "Daily Mail",
        "thetimes": "The Times",
        "skynews": "Sky News",
        
        // Australian News
        "smh": "Sydney Morning Herald",
        "theage": "The Melbourne Age",
        "theaustralian": "The Australian",
        "abc_au": "ABC Australia",
        "sbs": "SBS",
        "newscomau": "News.com.au",
        "news.com.au": "News.com.au",
        
        // Irish News
        "irishtimes": "Irish Times",
        "rte": "RTÉ News",
        "thejournal": "TheJournal.ie",
        
        // European News (Continental)
        "elpais": "El País",
        "lemonde": "Le Monde",
        "spiegel": "Der Spiegel",
        "ansa": "ANSA",
        "dutchnews": "DutchNews.nl",
        "notesfrompoland": "Notes from Poland",
        "swissinfo": "SWI swissinfo.ch",
        "thelocal": "The Local",
        "politico": "Politico Europe",
        "euronews": "Euronews",
        
        // Middle East
        "timesofisrael": "Times of Israel",
        "middleeasteye": "Middle East Eye",
        
        // Asia & International
        "aljazeera": "Al Jazeera",
        "france24": "France 24",
        "dw": "Deutsche Welle",
        "rt": "RT",
        "scmp": "South China Morning Post",
        "xinhua": "Xinhua",
        "japantimes": "Japan Times",
        "jakartapost": "Jakarta Post",
        "cgtn": "CGTN",
        
        // Business
        "bloomberg": "Bloomberg",
        "fortune": "Fortune",
        "forbes": "Forbes",
        "businessinsider": "Business Insider",
        "cnbc": "CNBC",
        
        // Sports
        "espn": "ESPN",
        "skysports": "Sky Sports",
        "yahoosports": "Yahoo Sports",
        "cbssports": "CBS Sports",
        "foxsports": "Fox Sports",
        "bleacherreport": "Bleacher Report",
        
        // Science & Health
        "sciencedaily": "Science Daily",
        "scientificamerican": "Scientific American",
        "nature": "Nature",
        "newscientist": "New Scientist",
        
        // Entertainment
        "variety": "Variety",
        "hollywoodreporter": "Hollywood Reporter",
        "deadline": "Deadline",
        "ew": "Entertainment Weekly"
    ]
    
    /// Convert a source ID to a proper display name
    /// - Parameter sourceId: The backend source ID (e.g., "bbc", "nyt", "smh")
    /// - Returns: Properly formatted display name (e.g., "BBC", "New York Times", "SMH")
    static func displayName(for sourceId: String) -> String {
        let lowercaseId = sourceId.lowercased()

        // Check if we have a mapping
        if let mapped = sourceDisplayNames[lowercaseId] {
            #if DEBUG
            print("🔍 SourceNameMapper: '\(sourceId)' -> MAPPED '\(mapped)'")
            #endif
            return mapped
        }

        // Fallback: Smart capitalization
        let smart = smartCapitalize(lowercaseId)
        #if DEBUG
        print("🔍 SourceNameMapper: '\(sourceId)' -> SMART '\(smart)'")
        #endif
        return smart
    }
    
    /// Smart capitalization that handles multi-word source names
    private static func smartCapitalize(_ text: String) -> String {
        // Split on common separators
        let separators = CharacterSet(charactersIn: "_- ")
        let words = text.components(separatedBy: separators)

        // Capitalize each word
        let capitalizedWords = words.map { word -> String in
            guard !word.isEmpty else { return word }

            // Handle all-caps acronyms (2-4 letters)
            if word.count <= 4 && word.range(of: "[a-z]", options: .regularExpression) == nil {
                return word.uppercased()
            }

            // Regular capitalization
            return word.prefix(1).uppercased() + word.dropFirst()
        }

        return capitalizedWords.joined(separator: " ")
    }

    /// Debug function to check mapping behavior
    static func debugMapping(for sourceId: String) -> String {
        let lowercaseId = sourceId.lowercased()

        if let mapped = sourceDisplayNames[lowercaseId] {
            return "MAPPED: '\(sourceId)' -> '\(mapped)'"
        } else {
            let smart = smartCapitalize(lowercaseId)
            return "SMART: '\(sourceId)' -> '\(smart)'"
        }
    }
}

