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
    case politics = "politics"
    case business = "business"
    case technology = "technology"
    case science = "science"
    case health = "health"
    case sports = "sports"
    case entertainment = "entertainment"
    case world = "world"
    case environment = "environment"
    
    var id: String { rawValue }
    
    var displayName: String {
        switch self {
        case .topStories: return "Top Stories"
        case .politics: return "Politics"
        case .business: return "Business"
        case .technology: return "Technology"
        case .science: return "Science"
        case .health: return "Health"
        case .sports: return "Sports"
        case .entertainment: return "Entertainment"
        case .world: return "World"
        case .environment: return "Environment"
        }
    }
    
    var icon: String {
        switch self {
        case .topStories: return "flame.fill"
        case .politics: return "building.columns.fill"
        case .business: return "chart.line.uptrend.xyaxis"
        case .technology: return "laptopcomputer"
        case .science: return "flask.fill"
        case .health: return "heart.fill"
        case .sports: return "sportscourt.fill"
        case .entertainment: return "film.fill"
        case .world: return "globe.americas.fill"
        case .environment: return "leaf.fill"
        }
    }
    
    var color: Color {
        switch self {
        case .topStories: return .orange
        case .politics: return .blue
        case .business: return .green
        case .technology: return .purple
        case .science: return .cyan
        case .health: return .red
        case .sports: return .yellow
        case .entertainment: return .pink
        case .world: return .indigo
        case .environment: return .mint
        }
    }
}

