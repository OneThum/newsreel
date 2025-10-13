//
//  SourceArticle.swift
//  Newsreel
//
//  Individual source article from a news outlet
//

import Foundation

/// Represents an individual source article
struct SourceArticle: Identifiable, Codable, Hashable {
    let id: String
    let source: String  // Source name (e.g., "reuters", "bbc")
    let title: String
    let articleURL: String
    let publishedAt: String  // ISO8601 date string from backend
    
    enum CodingKeys: String, CodingKey {
        case id, source, title
        case articleURL = "article_url"
        case publishedAt = "published_at"
    }
    
    /// Get URL object
    var url: URL? {
        URL(string: articleURL)
    }
    
    /// Get parsed date
    var date: Date? {
        let formatter = ISO8601DateFormatter()
        return formatter.date(from: publishedAt)
    }
    
    /// Display name for source with proper formatting
    var displayName: String {
        SourceNameMapper.displayName(for: source)
    }
}

