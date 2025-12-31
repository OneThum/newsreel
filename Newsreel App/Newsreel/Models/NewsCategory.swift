//
//  NewsCategory.swift
//  Newsreel
//
//  Data model for news categories
//

import Foundation
import SwiftUI

/// News categories/topics
enum NewsCategory: String, Codable, CaseIterable, Identifiable {
    case topStories = "top_stories"
    case world = "world"
    case politics = "politics"
    case business = "business"
    case technology = "technology"
    case science = "science"
    case health = "health"
    case sports = "sports"
    case entertainment = "entertainment"
    case lifestyle = "lifestyle"      // Product reviews, guides, how-tos
    case environment = "environment"
    
    var id: String { rawValue }
    
    var displayName: String {
        switch self {
        case .topStories: return "Top Stories"
        case .world: return "World"
        case .politics: return "Politics"
        case .business: return "Business"
        case .technology: return "Tech"
        case .science: return "Science"
        case .health: return "Health"
        case .sports: return "Sports"
        case .entertainment: return "Entertainment"
        case .lifestyle: return "Lifestyle"
        case .environment: return "Environment"
        }
    }
    
    var icon: String {
        switch self {
        case .topStories: return "flame.fill"
        case .world: return "globe.americas.fill"
        case .politics: return "building.columns.fill"
        case .business: return "chart.line.uptrend.xyaxis"
        case .technology: return "laptopcomputer"
        case .science: return "flask.fill"
        case .health: return "heart.fill"
        case .sports: return "sportscourt.fill"
        case .entertainment: return "film.fill"
        case .lifestyle: return "house.fill"
        case .environment: return "leaf.fill"
        }
    }
    
    var color: Color {
        switch self {
        case .topStories: return .orange
        case .world: return .indigo
        case .politics: return .blue
        case .business: return .green
        case .technology: return .purple
        case .science: return .cyan
        case .health: return .red
        case .sports: return .yellow
        case .entertainment: return .pink
        case .lifestyle: return .teal
        case .environment: return .mint
        }
    }
}

