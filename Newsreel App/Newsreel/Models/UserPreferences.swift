//
//  UserPreferences.swift
//  Newsreel
//
//  Data model for user preferences and settings
//

import Foundation
import SwiftUI

/// User preferences and settings
struct UserPreferences: Codable {
    // Content Preferences
    var preferredCategories: Set<NewsCategory>
    var blockedSources: Set<String> // Source IDs
    var preferredSources: Set<String> // Source IDs
    var preferredLanguages: Set<String>
    var preferredCountries: Set<String>
    
    // Reading Preferences
    var textSizeMultiplier: Double // 0.8 to 1.5
    var autoPlayVideos: Bool
    var showImages: Bool
    var dataUsageMode: DataUsageMode
    
    // Notification Preferences
    var enableNotifications: Bool
    var breakingNewsAlerts: Bool
    var dailyDigest: Bool
    var dailyDigestTime: Date?
    var notificationCategories: Set<NewsCategory>
    
    // Privacy & Display
    var allowPersonalization: Bool
    var shareReadingHistory: Bool
    var useRecommendations: Bool
    
    // App Behavior
    var openLinksInApp: Bool
    var markAsReadOnScroll: Bool
    var autoRefresh: Bool
    
    // Appearance
    var preferredColorScheme: AppColorScheme
    
    init(
        preferredCategories: Set<NewsCategory> = [.topStories, .technology, .business],
        blockedSources: Set<String> = [],
        preferredSources: Set<String> = [],
        preferredLanguages: Set<String> = ["en"],
        preferredCountries: Set<String> = ["US"],
        textSizeMultiplier: Double = 1.0,
        autoPlayVideos: Bool = false,
        showImages: Bool = true,
        dataUsageMode: DataUsageMode = .standard,
        enableNotifications: Bool = true,
        breakingNewsAlerts: Bool = true,
        dailyDigest: Bool = false,
        dailyDigestTime: Date? = nil,
        notificationCategories: Set<NewsCategory> = Set(NewsCategory.allCases),
        allowPersonalization: Bool = true,
        shareReadingHistory: Bool = true,
        useRecommendations: Bool = true,
        openLinksInApp: Bool = true,
        markAsReadOnScroll: Bool = true,
        autoRefresh: Bool = true,
        preferredColorScheme: AppColorScheme = .dark
    ) {
        self.preferredCategories = preferredCategories
        self.blockedSources = blockedSources
        self.preferredSources = preferredSources
        self.preferredLanguages = preferredLanguages
        self.preferredCountries = preferredCountries
        self.textSizeMultiplier = textSizeMultiplier
        self.autoPlayVideos = autoPlayVideos
        self.showImages = showImages
        self.dataUsageMode = dataUsageMode
        self.enableNotifications = enableNotifications
        self.breakingNewsAlerts = breakingNewsAlerts
        self.dailyDigest = dailyDigest
        self.dailyDigestTime = dailyDigestTime
        self.notificationCategories = notificationCategories
        self.allowPersonalization = allowPersonalization
        self.shareReadingHistory = shareReadingHistory
        self.useRecommendations = useRecommendations
        self.openLinksInApp = openLinksInApp
        self.markAsReadOnScroll = markAsReadOnScroll
        self.autoRefresh = autoRefresh
        self.preferredColorScheme = preferredColorScheme
    }
}

// MARK: - App Color Scheme

enum AppColorScheme: String, Codable, CaseIterable {
    case light = "light"
    case dark = "dark"
    case system = "system"
    
    var displayName: String {
        switch self {
        case .light: return "Light"
        case .dark: return "Dark"
        case .system: return "System"
        }
    }
    
    var colorScheme: ColorScheme? {
        switch self {
        case .light: return .light
        case .dark: return .dark
        case .system: return nil
        }
    }
}

// MARK: - Data Usage Mode

enum DataUsageMode: String, Codable, CaseIterable {
    case low = "low"
    case standard = "standard"
    case high = "high"
    
    var displayName: String {
        switch self {
        case .low: return "Low Data"
        case .standard: return "Standard"
        case .high: return "High Quality"
        }
    }
    
    var description: String {
        switch self {
        case .low: return "Reduced image quality, no auto-loading"
        case .standard: return "Balanced quality and data usage"
        case .high: return "Best quality, higher data usage"
        }
    }
}

// MARK: - Default

extension UserPreferences {
    static let `default` = UserPreferences()
    
    /// Anonymous user preferences (limited personalization)
    static let anonymous = UserPreferences(
        allowPersonalization: false,
        shareReadingHistory: false,
        useRecommendations: false
    )
}
