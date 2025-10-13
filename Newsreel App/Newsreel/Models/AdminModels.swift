import Foundation

// MARK: - Admin Metrics

struct AdminMetrics: Codable {
    let timestamp: Date
    let systemHealth: SystemHealth
    let database: DatabaseStats
    let rssIngestion: RSSIngestionStats
    let clustering: ClusteringStats
    let summarization: SummarizationStats
    let feedQuality: FeedQualityStats
    let azure: AzureResourceInfo
    
    enum CodingKeys: String, CodingKey {
        case timestamp
        case systemHealth = "system_health"
        case database
        case rssIngestion = "rss_ingestion"
        case clustering
        case summarization
        case feedQuality = "feed_quality"
        case azure
    }
}

struct SystemHealth: Codable {
    let overallStatus: String
    let apiHealth: String
    let functionsHealth: String
    let databaseHealth: String
    
    enum CodingKeys: String, CodingKey {
        case overallStatus = "overall_status"
        case apiHealth = "api_health"
        case functionsHealth = "functions_health"
        case databaseHealth = "database_health"
    }
}

struct DatabaseStats: Codable {
    let totalArticles: Int
    let totalStories: Int
    let storiesWithSummaries: Int
    let uniqueSources: Int
    let storiesByStatus: [StoryStatusCount]
    
    enum CodingKeys: String, CodingKey {
        case totalArticles = "total_articles"
        case totalStories = "total_stories"
        case storiesWithSummaries = "stories_with_summaries"
        case uniqueSources = "unique_sources"
        case storiesByStatus = "stories_by_status"
    }
}

struct StoryStatusCount: Codable {
    let status: String
    let count: Int
}

struct RSSIngestionStats: Codable {
    let totalFeeds: Int
    let lastRun: Date
    let articlesPerHour: Int
    let successRate: Double
    let topSources: [SourceCount]
    
    enum CodingKeys: String, CodingKey {
        case totalFeeds = "total_feeds"
        case lastRun = "last_run"
        case articlesPerHour = "articles_per_hour"
        case successRate = "success_rate"
        case topSources = "top_sources"
    }
}

struct SourceCount: Codable {
    let source: String
    let count: Int
}

struct ClusteringStats: Codable {
    let matchRate: Double
    let avgSourcesPerStory: Double
    let storiesCreated24h: Int
    let storiesUpdated24h: Int
    
    enum CodingKeys: String, CodingKey {
        case matchRate = "match_rate"
        case avgSourcesPerStory = "avg_sources_per_story"
        case storiesCreated24h = "stories_created_24h"
        case storiesUpdated24h = "stories_updated_24h"
    }
}

struct SummarizationStats: Codable {
    let coverage: Double
    let avgGenerationTime: Double
    let summariesGenerated24h: Int
    let avgWordCount: Int
    let cost24h: Double
    
    enum CodingKeys: String, CodingKey {
        case coverage
        case avgGenerationTime = "avg_generation_time"
        case summariesGenerated24h = "summaries_generated_24h"
        case avgWordCount = "avg_word_count"
        case cost24h = "cost_24h"
    }
}

struct FeedQualityStats: Codable {
    let rating: String
    let sourceDiversity: Double
    let uniqueSources: Int
    let categorizationConfidence: Double
    
    enum CodingKeys: String, CodingKey {
        case rating
        case sourceDiversity = "source_diversity"
        case uniqueSources = "unique_sources"
        case categorizationConfidence = "categorization_confidence"
    }
}

struct AzureResourceInfo: Codable {
    let resourceGroup: String
    let location: String
    let subscriptionName: String
    let containerAppStatus: String
    let functionsStatus: String
    let cosmosDbStatus: String
    
    enum CodingKeys: String, CodingKey {
        case resourceGroup = "resource_group"
        case location
        case subscriptionName = "subscription_name"
        case containerAppStatus = "container_app_status"
        case functionsStatus = "functions_status"
        case cosmosDbStatus = "cosmos_db_status"
    }
}

