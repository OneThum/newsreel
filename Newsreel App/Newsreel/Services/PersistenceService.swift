//
//  PersistenceService.swift
//  Newsreel
//
//  Local persistence service using SwiftData
//  Handles offline storage and caching
//

import Foundation
import SwiftData

/// SwiftData model for cached stories
@Model
final class CachedStory {
    @Attribute(.unique) var id: String
    var title: String
    var summary: String
    var content: String?
    var imageURLString: String?
    var publishedAt: Date
    var sourceId: String
    var sourceName: String
    var categoryRawValue: String
    var urlString: String
    var clusterId: String?
    var sentimentRawValue: String?
    var readingTimeMinutes: Int
    var sourceCount: Int
    var credibilityScore: Double
    var trendingScore: Double
    
    // User interactions
    var isRead: Bool
    var isSaved: Bool
    var isLiked: Bool
    var savedAt: Date?
    var readAt: Date?
    
    // Sync metadata
    var lastSyncedAt: Date
    var needsSync: Bool
    
    init(from story: Story) {
        self.id = story.id
        self.title = story.title
        self.summary = story.summary
        self.content = story.content
        self.imageURLString = story.imageURL?.absoluteString
        self.publishedAt = story.publishedAt
        self.sourceId = story.source.id
        self.sourceName = story.source.name
        self.categoryRawValue = story.category.rawValue
        self.urlString = story.url.absoluteString
        self.clusterId = story.clusterId
        self.sentimentRawValue = story.sentiment?.rawValue
        self.readingTimeMinutes = story.readingTimeMinutes
        self.sourceCount = story.sourceCount
        self.credibilityScore = story.credibilityScore
        self.trendingScore = story.trendingScore
        self.isRead = story.isRead
        self.isSaved = story.isSaved
        self.isLiked = story.isLiked
        self.savedAt = story.isSaved ? Date() : nil
        self.readAt = story.isRead ? Date() : nil
        self.lastSyncedAt = Date()
        self.needsSync = false
    }
    
    /// Convert back to Story model
    func toStory() -> Story? {
        guard let url = URL(string: urlString),
              let category = NewsCategory(rawValue: categoryRawValue) else {
            return nil
        }
        
        let source = Source(
            id: sourceId,
            name: sourceName,
            domain: "",
            logoURL: nil
        )
        
        let sentiment: Sentiment? = sentimentRawValue.flatMap { Sentiment(rawValue: $0) }
        
        return Story(
            id: id,
            title: title,
            summary: summary,
            content: content,
            imageURL: imageURLString.flatMap { URL(string: $0) },
            publishedAt: publishedAt,
            source: source,
            category: category,
            url: url,
            clusterId: clusterId,
            sentiment: sentiment,
            readingTimeMinutes: readingTimeMinutes,
            sourceCount: sourceCount,
            credibilityScore: credibilityScore,
            trendingScore: trendingScore,
            isRead: isRead,
            isSaved: isSaved,
            isLiked: isLiked
        )
    }
}

// MARK: - Persistence Service

@MainActor
class PersistenceService: ObservableObject {
    static let shared = PersistenceService()
    
    let modelContainer: ModelContainer
    let modelContext: ModelContext
    
    private init() {
        do {
            let schema = Schema([CachedStory.self])
            let modelConfiguration = ModelConfiguration(
                schema: schema,
                isStoredInMemoryOnly: false,
                allowsSave: true
            )
            
            modelContainer = try ModelContainer(
                for: schema,
                configurations: [modelConfiguration]
            )
            
            modelContext = ModelContext(modelContainer)
            modelContext.autosaveEnabled = true
        } catch {
            fatalError("Could not create ModelContainer: \(error)")
        }
    }
    
    // MARK: - Story Operations
    
    /// Save or update a story in the cache
    func cacheStory(_ story: Story) throws {
        // Check if story already exists
        let predicate = #Predicate<CachedStory> { $0.id == story.id }
        let descriptor = FetchDescriptor<CachedStory>(predicate: predicate)
        
        if let existing = try modelContext.fetch(descriptor).first {
            // Update existing
            existing.title = story.title
            existing.summary = story.summary
            existing.content = story.content
            existing.isRead = story.isRead
            existing.isSaved = story.isSaved
            existing.isLiked = story.isLiked
            existing.savedAt = story.isSaved ? (existing.savedAt ?? Date()) : nil
            existing.readAt = story.isRead ? (existing.readAt ?? Date()) : nil
            existing.lastSyncedAt = Date()
        } else {
            // Create new
            let cached = CachedStory(from: story)
            modelContext.insert(cached)
        }
        
        try modelContext.save()
    }
    
    /// Get cached story by ID
    func getCachedStory(id: String) throws -> Story? {
        let predicate = #Predicate<CachedStory> { $0.id == id }
        let descriptor = FetchDescriptor<CachedStory>(predicate: predicate)
        
        if let cached = try modelContext.fetch(descriptor).first {
            return cached.toStory()
        }
        return nil
    }
    
    /// Get all saved stories
    func getSavedStories() throws -> [Story] {
        let predicate = #Predicate<CachedStory> { $0.isSaved == true }
        let descriptor = FetchDescriptor<CachedStory>(
            predicate: predicate,
            sortBy: [SortDescriptor(\CachedStory.savedAt, order: .reverse)]
        )
        
        let cached = try modelContext.fetch(descriptor)
        return cached.compactMap { $0.toStory() }
    }
    
    /// Get reading history
    func getReadingHistory(limit: Int = 50) throws -> [Story] {
        let predicate = #Predicate<CachedStory> { $0.isRead == true }
        var descriptor = FetchDescriptor<CachedStory>(
            predicate: predicate,
            sortBy: [SortDescriptor(\CachedStory.readAt, order: .reverse)]
        )
        descriptor.fetchLimit = limit
        
        let cached = try modelContext.fetch(descriptor)
        return cached.compactMap { $0.toStory() }
    }
    
    /// Mark story as read
    func markAsRead(storyId: String) throws {
        let predicate = #Predicate<CachedStory> { $0.id == storyId }
        let descriptor = FetchDescriptor<CachedStory>(predicate: predicate)
        
        if let cached = try modelContext.fetch(descriptor).first {
            cached.isRead = true
            cached.readAt = Date()
            cached.needsSync = true
            try modelContext.save()
        }
    }
    
    /// Toggle save status
    func toggleSave(storyId: String) throws {
        let predicate = #Predicate<CachedStory> { $0.id == storyId }
        let descriptor = FetchDescriptor<CachedStory>(predicate: predicate)
        
        if let cached = try modelContext.fetch(descriptor).first {
            cached.isSaved.toggle()
            cached.savedAt = cached.isSaved ? Date() : nil
            cached.needsSync = true
            try modelContext.save()
        }
    }
    
    /// Toggle like status
    func toggleLike(storyId: String) throws {
        let predicate = #Predicate<CachedStory> { $0.id == storyId }
        let descriptor = FetchDescriptor<CachedStory>(predicate: predicate)
        
        if let cached = try modelContext.fetch(descriptor).first {
            cached.isLiked.toggle()
            cached.needsSync = true
            try modelContext.save()
        }
    }
    
    /// Delete old read stories (keep last 100)
    func cleanupOldStories() throws {
        let predicate = #Predicate<CachedStory> { story in
            story.isSaved == false && story.isRead == true
        }
        let descriptor = FetchDescriptor<CachedStory>(
            predicate: predicate,
            sortBy: [SortDescriptor(\CachedStory.readAt, order: .reverse)]
        )
        
        let allRead = try modelContext.fetch(descriptor)
        
        // Keep only the 100 most recent read stories
        if allRead.count > 100 {
            let toDelete = allRead.dropFirst(100)
            for story in toDelete {
                modelContext.delete(story)
            }
            try modelContext.save()
        }
    }
    
    /// Get stories that need to be synced
    func getStoriesToSync() throws -> [CachedStory] {
        let predicate = #Predicate<CachedStory> { $0.needsSync == true }
        let descriptor = FetchDescriptor<CachedStory>(predicate: predicate)
        return try modelContext.fetch(descriptor)
    }
    
    /// Mark stories as synced
    func markAsSynced(storyIds: [String]) throws {
        for id in storyIds {
            let predicate = #Predicate<CachedStory> { $0.id == id }
            let descriptor = FetchDescriptor<CachedStory>(predicate: predicate)
            
            if let cached = try modelContext.fetch(descriptor).first {
                cached.needsSync = false
                cached.lastSyncedAt = Date()
            }
        }
        try modelContext.save()
    }
    
    /// Cache multiple stories (for feed persistence)
    func cacheStories(_ stories: [Story]) throws {
        for story in stories {
            try cacheStory(story)
        }
    }
    
    /// Get cached feed (last viewed stories)
    func getCachedFeed(limit: Int = 20) throws -> [Story] {
        var descriptor = FetchDescriptor<CachedStory>(
            sortBy: [SortDescriptor(\CachedStory.lastSyncedAt, order: .reverse)]
        )
        descriptor.fetchLimit = limit
        
        let cached = try modelContext.fetch(descriptor)
        return cached.compactMap { $0.toStory() }
    }
    
    /// Clear all cached data
    func clearAll() throws {
        try modelContext.delete(model: CachedStory.self)
        try modelContext.save()
    }
}

