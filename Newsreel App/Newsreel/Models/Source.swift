//
//  Source.swift
//  Newsreel
//
//  Data model for news sources
//

import Foundation

/// Represents a news source/publisher
struct Source: Identifiable, Codable, Hashable {
    let id: String
    let name: String
    let domain: String
    let logoURL: URL?
    let category: SourceCategory
    let credibilityScore: Double // 0.0 to 1.0
    let politicalBias: PoliticalBias
    let country: String
    let language: String
    
    init(
        id: String,
        name: String,
        domain: String,
        logoURL: URL? = nil,
        category: SourceCategory = .generalNews,
        credibilityScore: Double = 0.8,
        politicalBias: PoliticalBias = .center,
        country: String = "US",
        language: String = "en"
    ) {
        self.id = id
        self.name = name
        self.domain = domain
        self.logoURL = logoURL
        self.category = category
        self.credibilityScore = credibilityScore
        self.politicalBias = politicalBias
        self.country = country
        self.language = language
    }
    
    /// Properly formatted display name (handles backend inconsistencies)
    var displayName: String {
        // If name is already properly formatted, use it
        // Otherwise, use the mapper to fix it based on the ID
        if name.contains(" ") || name.uppercased() == name {
            // Name looks proper (has spaces or is all caps like "BBC")
            return name
        }
        // Name looks like it needs mapping (e.g., "bbc", "smh", "theage")
        return SourceNameMapper.displayName(for: name.isEmpty ? id : name)
    }
}

// MARK: - Source Category

enum SourceCategory: String, Codable, CaseIterable {
    case generalNews = "general_news"
    case technology = "technology"
    case business = "business"
    case politics = "politics"
    case science = "science"
    case health = "health"
    case sports = "sports"
    case entertainment = "entertainment"
    
    var displayName: String {
        switch self {
        case .generalNews: return "General News"
        case .technology: return "Technology"
        case .business: return "Business"
        case .politics: return "Politics"
        case .science: return "Science"
        case .health: return "Health"
        case .sports: return "Sports"
        case .entertainment: return "Entertainment"
        }
    }
}

// MARK: - Political Bias

enum PoliticalBias: String, Codable {
    case left = "left"
    case centerLeft = "center_left"
    case center = "center"
    case centerRight = "center_right"
    case right = "right"
    
    var displayName: String {
        switch self {
        case .left: return "Left"
        case .centerLeft: return "Center-Left"
        case .center: return "Center"
        case .centerRight: return "Center-Right"
        case .right: return "Right"
        }
    }
}

// MARK: - Mock Data

extension Source {
    static let mock = Source(
        id: "bbc-news",
        name: "BBC News",
        domain: "bbc.com",
        logoURL: URL(string: "https://logo.clearbit.com/bbc.com"),
        category: .generalNews,
        credibilityScore: 0.95,
        politicalBias: .center,
        country: "GB",
        language: "en"
    )
    
    static let mockArray: [Source] = [
        Source(
            id: "bbc-news",
            name: "BBC News",
            domain: "bbc.com",
            logoURL: URL(string: "https://logo.clearbit.com/bbc.com"),
            category: .generalNews,
            credibilityScore: 0.95,
            politicalBias: .center
        ),
        Source(
            id: "nyt",
            name: "The New York Times",
            domain: "nytimes.com",
            logoURL: URL(string: "https://logo.clearbit.com/nytimes.com"),
            category: .generalNews,
            credibilityScore: 0.93,
            politicalBias: .centerLeft
        ),
        Source(
            id: "wsj",
            name: "The Wall Street Journal",
            domain: "wsj.com",
            logoURL: URL(string: "https://logo.clearbit.com/wsj.com"),
            category: .business,
            credibilityScore: 0.92,
            politicalBias: .centerRight
        ),
        Source(
            id: "reuters",
            name: "Reuters",
            domain: "reuters.com",
            logoURL: URL(string: "https://logo.clearbit.com/reuters.com"),
            category: .generalNews,
            credibilityScore: 0.96,
            politicalBias: .center
        ),
        Source(
            id: "techcrunch",
            name: "TechCrunch",
            domain: "techcrunch.com",
            logoURL: URL(string: "https://logo.clearbit.com/techcrunch.com"),
            category: .technology,
            credibilityScore: 0.88,
            politicalBias: .center
        )
    ]
}

