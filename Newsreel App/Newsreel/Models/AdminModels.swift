import Foundation

// MARK: - Admin Metrics

struct AdminMetrics: Codable {
    let timestamp: Date
    let systemHealth: SystemHealth
    let database: DatabaseStats
    let rssIngestion: RSSIngestionStats
    let clustering: ClusteringStats
    let summarization: SummarizationStats
    let batchProcessing: BatchProcessingStats
    let feedQuality: FeedQualityStats
    let azure: AzureResourceInfo
    
    enum CodingKeys: String, CodingKey {
        case timestamp
        case systemHealth = "system_health"
        case database
        case rssIngestion = "rss_ingestion"
        case clustering
        case summarization
        case batchProcessing = "batch_processing"
        case feedQuality = "feed_quality"
        case azure
    }
}

struct ComponentHealth: Codable {
    let status: String  // "healthy", "degraded", "down"
    let message: String
    let lastChecked: Date
    let responseTimeMs: Int?
    
    enum CodingKeys: String, CodingKey {
        case status
        case message
        case lastChecked = "last_checked"
        case responseTimeMs = "response_time_ms"
    }
}

struct SystemHealth: Codable {
    let overallStatus: String
    let apiHealth: String
    let functionsHealth: String
    let databaseHealth: String
    
    // Detailed component statuses
    let rssIngestion: ComponentHealth?
    let storyClustering: ComponentHealth?
    let summarizationChangefeed: ComponentHealth?
    let summarizationBackfill: ComponentHealth?
    let breakingNewsMonitor: ComponentHealth?
    
    enum CodingKeys: String, CodingKey {
        case overallStatus = "overall_status"
        case apiHealth = "api_health"
        case functionsHealth = "functions_health"
        case databaseHealth = "database_health"
        case rssIngestion = "rss_ingestion"
        case storyClustering = "story_clustering"
        case summarizationChangefeed = "summarization_changefeed"
        case summarizationBackfill = "summarization_backfill"
        case breakingNewsMonitor = "breaking_news_monitor"
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

struct BatchProcessingStats: Codable {
    let enabled: Bool
    let batchesSubmitted24h: Int
    let batchesCompleted24h: Int
    let batchSuccessRate: Double
    let storiesInQueue: Int
    let avgBatchSize: Int
    let batchCost24h: Double
    
    enum CodingKeys: String, CodingKey {
        case enabled
        case batchesSubmitted24h = "batches_submitted_24h"
        case batchesCompleted24h = "batches_completed_24h"
        case batchSuccessRate = "batch_success_rate"
        case storiesInQueue = "stories_in_queue"
        case avgBatchSize = "avg_batch_size"
        case batchCost24h = "batch_cost_24h"
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

