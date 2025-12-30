//
//  Story.swift
//  Newsreel
//
//  Data model for news stories
//

import Foundation

/// Represents a single news story
struct Story: Identifiable, Codable, Hashable {
    let id: String
    let title: String
    let summary: String
    let content: String?
    let imageURL: URL?
    let publishedAt: Date
    let source: Source // Primary source
    let sources: [SourceArticle] // All source articles
    let category: NewsCategory
    let url: URL
    let clusterId: String?
    let sentiment: Sentiment?
    let readingTimeMinutes: Int
    let status: StoryStatus // Verification status from backend
    let lastUpdated: Date? // When the story was last updated with new sources
    
    // Metadata
    let sourceCount: Int // Number of sources covering this story
    let credibilityScore: Double // 0.0 to 1.0
    let trendingScore: Double // 0.0 to 1.0
    
    // User interaction
    var isRead: Bool
    var isSaved: Bool
    var isLiked: Bool
    
    enum CodingKeys: String, CodingKey {
        case id, title, summary, content, imageURL, publishedAt
        case source, sources, category, url, clusterId, sentiment
        case readingTimeMinutes, sourceCount, credibilityScore
        case trendingScore, isRead, isSaved, isLiked, status, lastUpdated
    }
    
    init(
        id: String,
        title: String,
        summary: String,
        content: String? = nil,
        imageURL: URL? = nil,
        publishedAt: Date,
        source: Source,
        sources: [SourceArticle] = [],
        category: NewsCategory,
        url: URL,
        clusterId: String? = nil,
        sentiment: Sentiment? = nil,
        readingTimeMinutes: Int = 5,
        status: StoryStatus = .verified,
        lastUpdated: Date? = nil,
        sourceCount: Int = 1,
        credibilityScore: Double = 0.8,
        trendingScore: Double = 0.5,
        isRead: Bool = false,
        isSaved: Bool = false,
        isLiked: Bool = false
    ) {
        self.id = id
        self.title = title
        self.summary = summary
        self.content = content
        self.imageURL = imageURL
        self.publishedAt = publishedAt
        self.source = source
        self.sources = sources
        self.category = category
        self.url = url
        self.clusterId = clusterId
        self.sentiment = sentiment
        self.readingTimeMinutes = readingTimeMinutes
        self.status = status
        self.lastUpdated = lastUpdated
        self.sourceCount = sourceCount
        self.credibilityScore = credibilityScore
        self.trendingScore = trendingScore
        self.isRead = isRead
        self.isSaved = isSaved
        self.isLiked = isLiked
    }
}

// MARK: - Story Status

enum StoryStatus: String, Codable {
    case monitoring = "MONITORING"  // Single source, unverified
    case developing = "DEVELOPING"  // 2 sources
    case verified = "VERIFIED"      // 3+ sources, not breaking
    case breaking = "BREAKING"      // 3+ sources, recent
    
    var displayName: String {
        switch self {
        case .monitoring: return "MONITORING"
        case .developing: return "DEVELOPING"
        case .verified: return "VERIFIED"
        case .breaking: return "BREAKING"
        }
    }
}

// MARK: - Sentiment

enum Sentiment: String, Codable {
    case positive
    case neutral
    case negative
    case mixed
}

// MARK: - Extensions

extension Story {
    /// Returns a formatted time ago string (e.g., "2h ago", "1d ago")
    /// "Just now" only appears if:
    /// - Story was published < 1 minute ago, OR
    /// - Story was updated < 1 minute ago (with UPDATED badge)
    var timeAgo: String {
        let calendar = Calendar.current
        let now = Date()
        
        // Determine which timestamp to use based on whether story was recently updated
        let referenceDate: Date
        if isRecentlyUpdated, let lastUpdated = lastUpdated {
            // Use lastUpdated for stories with UPDATED badge
            referenceDate = lastUpdated
        } else {
            // Use publishedAt for all other stories
            referenceDate = publishedAt
        }
        
        let components = calendar.dateComponents([.minute, .hour, .day], from: referenceDate, to: now)
        
        if let day = components.day, day > 0 {
            return day == 1 ? "1d ago" : "\(day)d ago"
        } else if let hour = components.hour, hour > 0 {
            return hour == 1 ? "1h ago" : "\(hour)h ago"
        } else if let minute = components.minute, minute > 0 {
            return minute == 1 ? "1m ago" : "\(minute)m ago"
        } else {
            // "Just now" only if less than 1 minute old
            return "Just now"
        }
    }
    
    /// Returns formatted reading time (e.g., "5 min")
    var formattedReadingTime: String {
        "\(readingTimeMinutes) min"
    }
    
    /// Returns formatted source count (e.g., "3 sources")
    var formattedSourceCount: String {
        sourceCount == 1 ? "1 source" : "\(sourceCount) sources"
    }
    
    /// Returns true if the story has been updated significantly after initial publication
    var isRecentlyUpdated: Bool {
        guard let lastUpdated = lastUpdated else { return false }
        let timeSincePublished = lastUpdated.timeIntervalSince(publishedAt)
        // Consider it "updated" if last update was at least 30 minutes after publication
        return timeSincePublished >= 1800 // 30 minutes
    }
    
    /// Returns the summary text if valid, otherwise returns empty string
    /// Filters out AI error messages and redundant markdown headlines
    var displaySummary: String {
        let errorIndicators = [
            "i cannot create",
            "cannot provide",
            "insufficient",
            "would need",
            "unable to",
            "based on the provided information",
            "source contains only",
            "null content",
            "no actual article",
            "guidelines specify"
        ]
        
        let summaryLower = summary.lowercased()
        
        // Check if summary contains error indicators
        if errorIndicators.contains(where: { summaryLower.contains($0) }) {
            return ""
        }
        
        // Strip redundant markdown headline and "Summary:" label from summary body
        // Backend generates summaries like: "**Headline**\n\nBody text..." or "Summary:\n\nBody text..."
        // We only want the body text since the story already has a title
        let lines = summary.components(separatedBy: .newlines)

        // If first non-empty line is a markdown bold headline or "Summary:" label, skip it
        var startIndex = 0
        for (index, line) in lines.enumerated() {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            if !trimmed.isEmpty {
                // Check if it's a markdown headline (starts with ** and contains **)
                // or if it's a "Summary:" label
                if (trimmed.hasPrefix("**") && trimmed.contains("**")) ||
                   trimmed.lowercased().starts(with: "summary:") {
                    startIndex = index + 1
                    // Skip blank lines after headline/label
                    while startIndex < lines.count && lines[startIndex].trimmingCharacters(in: .whitespaces).isEmpty {
                        startIndex += 1
                    }
                }
                break
            }
        }

        // Join remaining lines and trim whitespace
        let bodyText = lines[startIndex...].joined(separator: "\n").trimmingCharacters(in: .whitespacesAndNewlines)
        return bodyText
    }
}

// MARK: - Mock Data

extension Story {
    static let mock = Story(
        id: UUID().uuidString,
        title: "Major Breakthrough in Renewable Energy Storage",
        summary: "Scientists announce a new battery technology that could revolutionize how we store renewable energy, making it more efficient and cost-effective than ever before.",
        content: nil,
        imageURL: URL(string: "https://picsum.photos/800/600"),
        publishedAt: Date().addingTimeInterval(-3600 * 2), // 2 hours ago
        source: .mock,
        category: .technology,
        url: URL(string: "https://example.com/article")!,
        clusterId: "cluster-123",
        sentiment: .positive,
        readingTimeMinutes: 5,
        sourceCount: 7,
        credibilityScore: 0.92,
        trendingScore: 0.85
    )
    
    static let mockArray: [Story] = [
        Story(
            id: "1",
            title: "Major Breakthrough in Renewable Energy Storage",
            summary: "Scientists announce a new battery technology that could revolutionize energy storage.",
            imageURL: URL(string: "https://picsum.photos/800/600?random=1"),
            publishedAt: Date().addingTimeInterval(-3600 * 2),
            source: .mock,
            category: .technology,
            url: URL(string: "https://example.com/1")!,
            sourceCount: 7,
            trendingScore: 0.9
        ),
        Story(
            id: "2",
            title: "Global Markets Rally on Economic Recovery Signs",
            summary: "Stock markets around the world show positive momentum as economic indicators improve.",
            imageURL: URL(string: "https://picsum.photos/800/600?random=2"),
            publishedAt: Date().addingTimeInterval(-3600 * 5),
            source: .mock,
            category: .business,
            url: URL(string: "https://example.com/2")!,
            sourceCount: 12,
            trendingScore: 0.75
        ),
        Story(
            id: "3",
            title: "New Climate Agreement Reached at International Summit",
            summary: "World leaders commit to ambitious new targets for reducing carbon emissions.",
            imageURL: URL(string: "https://picsum.photos/800/600?random=3"),
            publishedAt: Date().addingTimeInterval(-3600 * 8),
            source: .mock,
            category: .politics,
            url: URL(string: "https://example.com/3")!,
            sourceCount: 15,
            trendingScore: 0.88
        ),
        Story(
            id: "4",
            title: "Groundbreaking Medical Research Shows Promise",
            summary: "New treatment approach demonstrates significant results in clinical trials.",
            imageURL: URL(string: "https://picsum.photos/800/600?random=4"),
            publishedAt: Date().addingTimeInterval(-3600 * 24),
            source: .mock,
            category: .health,
            url: URL(string: "https://example.com/4")!,
            sourceCount: 5,
            trendingScore: 0.65
        ),
        Story(
            id: "5",
            title: "Space Agency Announces Ambitious Mars Mission",
            summary: "Details revealed for upcoming mission that could change our understanding of the Red Planet.",
            imageURL: URL(string: "https://picsum.photos/800/600?random=5"),
            publishedAt: Date().addingTimeInterval(-3600 * 36),
            source: .mock,
            category: .science,
            url: URL(string: "https://example.com/5")!,
            sourceCount: 9,
            trendingScore: 0.82
        )
    ]
}
