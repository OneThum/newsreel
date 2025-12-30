//
//  StoryCluster.swift
//  Newsreel
//
//  Data model for clustered news stories
//

import Foundation

/// Represents a cluster of related news stories from different sources
struct StoryCluster: Identifiable, Codable {
    let id: String
    let title: String
    let summary: String
    let category: NewsCategory
    let imageURL: URL?
    let publishedAt: Date
    let stories: [Story]
    let sourceCount: Int
    let credibilityScore: Double
    let trendingScore: Double
    let perspectives: [Perspective]
    
    init(
        id: String,
        title: String,
        summary: String,
        category: NewsCategory,
        imageURL: URL? = nil,
        publishedAt: Date,
        stories: [Story],
        sourceCount: Int,
        credibilityScore: Double = 0.85,
        trendingScore: Double = 0.7,
        perspectives: [Perspective] = []
    ) {
        self.id = id
        self.title = title
        self.summary = summary
        self.category = category
        self.imageURL = imageURL
        self.publishedAt = publishedAt
        self.stories = stories
        self.sourceCount = sourceCount
        self.credibilityScore = credibilityScore
        self.trendingScore = trendingScore
        self.perspectives = perspectives
    }
}

// MARK: - Perspective

/// Represents a political or topical perspective on a story cluster
struct Perspective: Codable, Identifiable {
    let id: String
    let bias: PoliticalBias
    let summary: String
    let sources: [Source]
    
    var displayName: String {
        bias.displayName + " Perspective"
    }
}

// MARK: - Extensions

extension StoryCluster {
    /// Returns a formatted time ago string
    var timeAgo: String {
        let calendar = Calendar.current
        let now = Date()
        let components = calendar.dateComponents([.minute, .hour, .day], from: publishedAt, to: now)
        
        if let day = components.day, day > 0 {
            return day == 1 ? "1d ago" : "\(day)d ago"
        } else if let hour = components.hour, hour > 0 {
            return hour == 1 ? "1h ago" : "\(hour)h ago"
        } else if let minute = components.minute, minute > 0 {
            return minute == 1 ? "1m ago" : "\(minute)m ago"
        } else {
            return "Just now"
        }
    }
    
    /// Returns formatted source count
    var formattedSourceCount: String {
        "\(sourceCount) \(sourceCount == 1 ? "source" : "sources")"
    }
    
    /// Returns the main story (highest credibility)
    var mainStory: Story? {
        stories.max(by: { $0.credibilityScore < $1.credibilityScore })
    }
}

// MARK: - Mock Data

extension StoryCluster {
    static let mock = StoryCluster(
        id: "cluster-1",
        title: "Major Developments in AI Technology",
        summary: "Multiple sources report on significant breakthroughs in artificial intelligence capabilities.",
        category: .technology,
        imageURL: URL(string: "https://picsum.photos/800/600?random=10"),
        publishedAt: Date().addingTimeInterval(-3600 * 3),
        stories: Array(Story.mockArray.prefix(3)),
        sourceCount: 8,
        credibilityScore: 0.92,
        trendingScore: 0.95,
        perspectives: [
            Perspective(
                id: "p1",
                bias: .centerLeft,
                summary: "Reports focus on potential societal benefits and ethical considerations.",
                sources: Array(Source.mockArray.prefix(2))
            ),
            Perspective(
                id: "p2",
                bias: .centerRight,
                summary: "Coverage emphasizes economic opportunities and market implications.",
                sources: Array(Source.mockArray.suffix(2))
            )
        ]
    )
    
    static let mockArray: [StoryCluster] = [
        StoryCluster(
            id: "cluster-1",
            title: "Major Developments in AI Technology",
            summary: "Multiple sources report on significant breakthroughs in artificial intelligence.",
            category: .technology,
            imageURL: URL(string: "https://picsum.photos/800/600?random=10"),
            publishedAt: Date().addingTimeInterval(-3600 * 3),
            stories: Array(Story.mockArray.prefix(3)),
            sourceCount: 8,
            trendingScore: 0.95
        ),
        StoryCluster(
            id: "cluster-2",
            title: "Global Economic Summit Concludes",
            summary: "World leaders reach agreements on international trade and cooperation.",
            category: .business,
            imageURL: URL(string: "https://picsum.photos/800/600?random=11"),
            publishedAt: Date().addingTimeInterval(-3600 * 6),
            stories: Array(Story.mockArray.suffix(2)),
            sourceCount: 12,
            trendingScore: 0.88
        ),
        StoryCluster(
            id: "cluster-3",
            title: "Climate Action Takes Center Stage",
            summary: "New initiatives announced to address environmental challenges.",
            category: .environment,
            imageURL: URL(string: "https://picsum.photos/800/600?random=12"),
            publishedAt: Date().addingTimeInterval(-3600 * 12),
            stories: Array(Story.mockArray.dropFirst(1).prefix(2)),
            sourceCount: 15,
            trendingScore: 0.85
        )
    ]
}

