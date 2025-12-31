//
//  ReadStateManager.swift
//  Newsreel
//
//  Manages read state for stories with timestamp tracking
//  Stories that were read will dim, but "light up" again if updated with new content
//

import Foundation
import SwiftUI

/// Manages persistent read state for stories
/// Tracks both whether a story was read AND when it was read
/// This allows us to show unread indicators when a story gets updated
class ReadStateManager: ObservableObject {
    static let shared = ReadStateManager()
    
    /// Dictionary of storyId -> timestamp when read
    @Published private(set) var readStates: [String: Date] = [:]
    
    private let userDefaultsKey = "newsreel_read_stories"
    private let maxStoredStories = 500 // Limit to prevent unbounded growth
    
    private init() {
        loadFromDisk()
    }
    
    // MARK: - Public API
    
    /// Check if a story should appear as "read" (dimmed)
    /// Returns false if the story has been updated since it was read
    func isStoryRead(_ story: Story) -> Bool {
        guard let readAt = readStates[story.id] else {
            return false // Never read
        }
        
        // If the story has been updated since we read it, show as unread
        if let lastUpdated = story.lastUpdated, lastUpdated > readAt {
            return false // New content available!
        }
        
        return true // Story is read and hasn't been updated
    }
    
    /// Mark a story as read at the current time
    func markAsRead(_ story: Story) {
        readStates[story.id] = Date()
        saveToDisk()
    }
    
    /// Mark a story as read with a specific timestamp
    func markAsRead(_ storyId: String, at date: Date = Date()) {
        readStates[storyId] = date
        saveToDisk()
    }
    
    /// Clear read state for a story (mark as unread)
    func markAsUnread(_ storyId: String) {
        readStates.removeValue(forKey: storyId)
        saveToDisk()
    }
    
    /// Clear all read states
    func clearAll() {
        readStates.removeAll()
        saveToDisk()
    }
    
    // MARK: - Persistence
    
    private func loadFromDisk() {
        guard let data = UserDefaults.standard.data(forKey: userDefaultsKey),
              let decoded = try? JSONDecoder().decode([String: Date].self, from: data) else {
            return
        }
        readStates = decoded
    }
    
    private func saveToDisk() {
        // Prune old entries if we exceed the limit
        if readStates.count > maxStoredStories {
            let sortedByDate = readStates.sorted { $0.value > $1.value }
            readStates = Dictionary(uniqueKeysWithValues: sortedByDate.prefix(maxStoredStories).map { ($0.key, $0.value) })
        }
        
        if let encoded = try? JSONEncoder().encode(readStates) {
            UserDefaults.standard.set(encoded, forKey: userDefaultsKey)
        }
    }
}

// MARK: - Environment Key

struct ReadStateManagerKey: EnvironmentKey {
    static let defaultValue = ReadStateManager.shared
}

extension EnvironmentValues {
    var readStateManager: ReadStateManager {
        get { self[ReadStateManagerKey.self] }
        set { self[ReadStateManagerKey.self] = newValue }
    }
}

