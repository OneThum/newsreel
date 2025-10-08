//
//  APIService.swift
//  Newsreel
//
//  Backend API communication service
//  Handles all HTTP requests to Azure Container Apps APIs
//

import Foundation

/// API errors
enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case unauthorized
    case serverError(Int)
    case networkError(Error)
    case decodingError(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL"
        case .invalidResponse:
            return "Invalid server response"
        case .unauthorized:
            return "Unauthorized. Please sign in again."
        case .serverError(let code):
            return "Server error (\(code)). Please try again later."
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .decodingError:
            return "Failed to parse server response"
        }
    }
}

/// Story model (from API)
struct Story: Identifiable, Codable {
    let id: String
    let title: String
    let summary: String
    let category: String
    let status: StoryStatus
    let verificationLevel: Int
    let firstSeen: Date
    let lastUpdated: Date
    let sourceCount: Int
    let importanceScore: Int
    let breakingNews: Bool
    let tags: [String]
    
    enum CodingKeys: String, CodingKey {
        case id, title, summary, category, status, tags
        case verificationLevel = "verification_level"
        case firstSeen = "first_seen"
        case lastUpdated = "last_updated"
        case sourceCount = "source_count"
        case importanceScore = "importance_score"
        case breakingNews = "breaking_news"
    }
}

enum StoryStatus: String, Codable {
    case monitoring = "MONITORING"
    case developing = "DEVELOPING"
    case breaking = "BREAKING"
    case verified = "VERIFIED"
}

/// Source article model
struct SourceArticle: Identifiable, Codable {
    let id: String
    let source: String
    let title: String
    let articleURL: String
    let publishedAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id, source, title
        case articleURL = "article_url"
        case publishedAt = "published_at"
    }
}

/// Feed response model
struct FeedResponse: Codable {
    let stories: [Story]
    let totalCount: Int
    let hasMore: Bool
    
    enum CodingKeys: String, CodingKey {
        case stories
        case totalCount = "total_count"
        case hasMore = "has_more"
    }
}

/// User interaction request
struct InteractionRequest: Codable {
    let storyId: String
    let interactionType: InteractionType
    let dwellTime: Int?
    let cardFlipped: Bool?
    
    enum CodingKeys: String, CodingKey {
        case storyId = "story_id"
        case interactionType = "interaction_type"
        case dwellTime = "dwell_time"
        case cardFlipped = "card_flipped"
    }
}

enum InteractionType: String, Codable {
    case view
    case like
    case save
    case share
}

@MainActor
class APIService: ObservableObject {
    
    // MARK: - Configuration
    
    /// Base URL for the Story API (Azure Container Apps)
    /// TODO: Replace with actual Azure Container App URL after deployment
    private let baseURL = "https://story-api.newsreel-prod.azurecontainerapps.io"
    
    /// URLSession for all network requests
    private let session: URLSession
    
    /// JSON decoder with custom date decoding
    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()
    
    /// JSON encoder with custom date encoding
    private let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }()
    
    /// Reference to AuthService for JWT tokens
    private let authService: AuthService
    
    // MARK: - Initialization
    
    init(authService: AuthService) {
        self.authService = authService
        
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 30
        configuration.timeoutIntervalForResource = 60
        self.session = URLSession(configuration: configuration)
    }
    
    // MARK: - Stories API
    
    /// Get personalized feed for current user
    /// - Parameters:
    ///   - offset: Pagination offset (default: 0)
    ///   - limit: Number of stories to fetch (default: 20)
    /// - Returns: Array of Story objects
    func getFeed(offset: Int = 0, limit: Int = 20) async throws -> [Story] {
        let endpoint = "/api/stories/feed?offset=\(offset)&limit=\(limit)"
        let response: FeedResponse = try await request(endpoint: endpoint, method: "GET")
        return response.stories
    }
    
    /// Get a single story by ID
    /// - Parameter id: Story ID
    /// - Returns: Story object
    func getStory(id: String) async throws -> Story {
        let endpoint = "/api/stories/\(id)"
        return try await request(endpoint: endpoint, method: "GET")
    }
    
    /// Get source articles for a story
    /// - Parameter storyId: Story ID
    /// - Returns: Array of SourceArticle objects
    func getSources(storyId: String) async throws -> [SourceArticle] {
        let endpoint = "/api/stories/\(storyId)/sources"
        let response: [String: [SourceArticle]] = try await request(endpoint: endpoint, method: "GET")
        return response["sources"] ?? []
    }
    
    /// Get breaking news stories
    /// - Returns: Array of breaking Story objects
    func getBreakingNews() async throws -> [Story] {
        let endpoint = "/api/stories/breaking"
        let response: FeedResponse = try await request(endpoint: endpoint, method: "GET")
        return response.stories
    }
    
    // MARK: - Interactions API
    
    /// Record user interaction with a story
    /// - Parameters:
    ///   - storyId: Story ID
    ///   - type: Type of interaction
    ///   - dwellTime: Optional time spent viewing (seconds)
    ///   - cardFlipped: Whether user flipped the card
    func recordInteraction(
        storyId: String,
        type: InteractionType,
        dwellTime: Int? = nil,
        cardFlipped: Bool? = nil
    ) async throws {
        let endpoint = "/api/stories/\(storyId)/interact"
        let body = InteractionRequest(
            storyId: storyId,
            interactionType: type,
            dwellTime: dwellTime,
            cardFlipped: cardFlipped
        )
        
        let _: EmptyResponse = try await request(
            endpoint: endpoint,
            method: "POST",
            body: body
        )
    }
    
    // MARK: - User API
    
    /// Get current user profile
    /// - Returns: UserProfile object
    func getUserProfile() async throws -> UserProfile {
        let endpoint = "/api/user/profile"
        return try await request(endpoint: endpoint, method: "GET")
    }
    
    /// Update user preferences
    /// - Parameter preferences: UserPreferences object
    func updatePreferences(_ preferences: UserPreferences) async throws {
        let endpoint = "/api/user/preferences"
        let _: EmptyResponse = try await request(
            endpoint: endpoint,
            method: "PUT",
            body: preferences
        )
    }
    
    /// Register device token for push notifications
    /// - Parameter token: APNs device token
    func registerDeviceToken(_ token: String) async throws {
        let endpoint = "/api/user/device-token"
        let body = ["token": token, "platform": "ios"]
        let _: EmptyResponse = try await request(
            endpoint: endpoint,
            method: "POST",
            body: body
        )
    }
    
    // MARK: - Health Check
    
    /// Check API health status
    /// - Returns: True if API is healthy
    func checkHealth() async throws -> Bool {
        let endpoint = "/health"
        let response: [String: String] = try await request(
            endpoint: endpoint,
            method: "GET",
            requiresAuth: false
        )
        return response["status"] == "healthy"
    }
    
    // MARK: - Private Request Method
    
    /// Generic request method
    private func request<T: Decodable, B: Encodable>(
        endpoint: String,
        method: String,
        body: B? = nil as EmptyBody?,
        requiresAuth: Bool = true
    ) async throws -> T {
        // Build URL
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }
        
        // Create request
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Add authentication if required
        if requiresAuth {
            do {
                let token = try await authService.getIDToken(forceRefresh: false)
                request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            } catch {
                throw APIError.unauthorized
            }
        }
        
        // Add body if provided
        if let body = body {
            request.httpBody = try encoder.encode(body)
        }
        
        // Execute request
        do {
            let (data, response) = try await session.data(for: request)
            
            // Validate response
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            
            switch httpResponse.statusCode {
            case 200...299:
                // Success - decode response
                do {
                    return try decoder.decode(T.self, from: data)
                } catch {
                    throw APIError.decodingError(error)
                }
                
            case 401:
                throw APIError.unauthorized
                
            default:
                throw APIError.serverError(httpResponse.statusCode)
            }
            
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.networkError(error)
        }
    }
}

// MARK: - Supporting Types

struct UserProfile: Codable {
    let id: String
    let email: String?
    let subscriptionTier: String
    let preferences: UserPreferences
    
    enum CodingKeys: String, CodingKey {
        case id, email, preferences
        case subscriptionTier = "subscription_tier"
    }
}

struct UserPreferences: Codable {
    var categories: [String]
    var notificationSettings: NotificationSettings
    
    enum CodingKeys: String, CodingKey {
        case categories
        case notificationSettings = "notification_settings"
    }
}

struct NotificationSettings: Codable {
    var breakingNews: Bool
    var quietHours: QuietHours?
    
    enum CodingKeys: String, CodingKey {
        case breakingNews = "breaking_news"
        case quietHours = "quiet_hours"
    }
}

struct QuietHours: Codable {
    var enabled: Bool
    var start: String  // HH:mm format
    var end: String    // HH:mm format
}

/// Empty body for requests without a body
private struct EmptyBody: Encodable {}

/// Empty response for requests that don't return data
private struct EmptyResponse: Decodable {}

