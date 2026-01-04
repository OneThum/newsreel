//
//  APIService.swift
//  Newsreel
//
//  Backend API communication service
//  Handles all HTTP requests to Azure Container Apps APIs
//  Supports mock data for development
//

import Foundation
import UIKit
import FirebaseAuth

/// API errors
enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case unauthorized
    case rateLimitExceeded
    case serverError(Int)
    case networkError(Error)
    case decodingError(Error)
    case mockModeEnabled
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL"
        case .invalidResponse:
            return "Invalid server response"
        case .unauthorized:
            return "Unauthorized. Please sign in again."
        case .rateLimitExceeded:
            return "Daily limit reached. Upgrade to Premium for unlimited stories!"
        case .serverError(let code):
            return "Server error (\(code)). Please try again later."
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .decodingError:
            return "Failed to parse server response"
        case .mockModeEnabled:
            return "Mock mode is enabled"
        }
    }
}

/// Azure API interaction request
struct AzureInteractionRequest: Codable {
    let interaction_type: String
    let session_id: String
    let dwell_time_seconds: Int
    let card_flipped: Bool
    let sources_clicked: [String]
    let device_info: [String: String]
}

@MainActor
class APIService: ObservableObject {
    
    // MARK: - Configuration
    
    /// Base URL for the Story API (Azure Container App)
    private let baseURL = "https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io"
    
    /// Enable mock data mode for development
    /// Set to false to use live Azure backend
    @Published var useMockData: Bool = false
    
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
    
    init(authService: AuthService, useMockData: Bool = true) {
        self.authService = authService
        self.useMockData = useMockData
        
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
    ///   - category: Optional category filter
    /// - Returns: Array of Story objects
    func getFeed(offset: Int = 0, limit: Int = 20, category: NewsCategory? = nil) async throws -> [Story] {
        log.section("GET FEED")
        log.log("Fetching feed - offset: \(offset), limit: \(limit), category: \(category?.displayName ?? "all")", category: .api)
        
        if useMockData {
            log.log("Using mock data mode", category: .api, level: .debug)
            return await mockGetFeed(offset: offset, limit: limit, category: category)
        }
        
        // Verify user is authenticated before fetching personalized feed
        guard Auth.auth().currentUser != nil else {
            log.logAuth("⚠️ No authenticated user, cannot fetch personalized feed", level: .warning)
            throw APIError.unauthorized
        }
        
        // Use the proper authenticated feed endpoint
        var endpoint = "/api/stories/feed?offset=\(offset)&limit=\(limit)"
        if let category = category {
            endpoint += "&category=\(category.rawValue)"
        }
        
        log.log("Endpoint: \(endpoint)", category: .api, level: .debug)
        
        do {
            // API returns direct array of stories
            let azureStories: [AzureStoryResponse] = try await request(endpoint: endpoint, method: "GET", requiresAuth: true)
            let stories = azureStories.map { $0.toStory() }
            log.log("✅ Feed loaded successfully: \(stories.count) stories", category: .api, level: .info)
            log.log("   Sources included: \(azureStories.first?.sources?.count ?? 0) sources in first story", category: .api, level: .debug)
            return stories
        } catch let error as APIError where error.localizedDescription.contains("Unauthorized") {
            log.log("⚠️ Authentication failed - Firebase credentials may not be configured on Azure", category: .api, level: .warning)
            log.log("💡 Falling back to breaking news (public endpoint)", category: .api, level: .info)
            // Fallback to breaking news if auth fails
            return try await getBreakingNews()
        } catch {
            log.logError(error, context: "getFeed failed")
            throw error
        }
    }
    
    /// Search stories by keywords
    /// - Parameters:
    ///   - query: Search query string
    ///   - category: Optional category filter
    ///   - limit: Maximum number of results
    /// - Returns: Array of Story objects matching the search
    func searchStories(query: String, category: NewsCategory? = nil, limit: Int = 20) async throws -> [Story] {
        guard !query.isEmpty else { return [] }
        
        var endpoint = "/api/stories/search?q=\(query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query)&limit=\(limit)"
        
        if let category = category {
            let categoryParam = category.rawValue.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? category.rawValue
            endpoint += "&category=\(categoryParam)"
        }
        
        log.log("🔍 Searching for: '\(query)' (category: \(category?.displayName ?? "all"))", category: .api, level: .info)
        
        let azureStories: [AzureStoryResponse] = try await request(endpoint: endpoint, method: "GET", requiresAuth: false)
        let stories = azureStories.map { $0.toStory() }
        
        log.log("✅ Search returned \(stories.count) results", category: .api, level: .info)
        return stories
    }
    
    /// Get story clusters (related stories grouped together)
    /// - Parameters:
    ///   - offset: Pagination offset
    ///   - limit: Number of clusters to fetch
    /// - Returns: Array of StoryCluster objects
    func getStoryClusters(offset: Int = 0, limit: Int = 10) async throws -> [StoryCluster] {
        if useMockData {
            return await mockGetClusters(offset: offset, limit: limit)
        }
        
        // TEMPORARY: Use breaking news as fallback since clusters endpoint doesn't exist yet
        log.log("⚠️ Clusters endpoint not available, using breaking news as fallback", category: .api, level: .warning)
        let stories = try await getBreakingNews()
        
        // Convert stories to clusters (simple implementation)
        let clusters = stories.prefix(limit).map { story in
            StoryCluster(
                id: story.id,
                title: story.title,
                summary: story.summary,
                category: story.category,
                imageURL: story.imageURL,
                publishedAt: story.publishedAt,
                stories: [story],
                sourceCount: story.sources.count,
                credibilityScore: 0.9,
                trendingScore: 0.8,
                perspectives: []
            )
        }
        
        return Array(clusters)
    }
    
    /// Get a single story by ID
    /// - Parameter id: Story ID
    /// - Returns: Story object
    func getStory(id: String) async throws -> Story {
        if useMockData {
            return await mockGetStory(id: id)
        }
        
        let endpoint = "/api/stories/\(id)"
        let azureStory: AzureStoryResponse = try await request(endpoint: endpoint, method: "GET")
        return azureStory.toStory()
    }
    
    /// Get breaking news stories
    /// - Returns: Array of breaking Story objects
    func getBreakingNews() async throws -> [Story] {
        log.log("Fetching breaking news (public endpoint)", category: .api)
        
        if useMockData {
            log.log("Using mock data mode", category: .api, level: .debug)
            return await mockGetBreakingNews()
        }
        
        let endpoint = "/api/stories/breaking?limit=20"
        log.log("Endpoint: \(endpoint) (no auth required)", category: .api, level: .debug)
        
        do {
            // API now returns direct array (not wrapped)
            let azureStories: [AzureStoryResponse] = try await request(endpoint: endpoint, method: "GET", requiresAuth: false)
            let stories = azureStories.map { $0.toStory() }
            log.log("✅ Breaking news loaded: \(stories.count) stories", category: .api, level: .info)
            log.log("   Sources per story: \(azureStories.first?.sources?.count ?? 0)", category: .api, level: .debug)
            return stories
        } catch {
            log.logError(error, context: "getBreakingNews failed")
            throw error
        }
    }
    
    /// Search stories
    /// - Parameters:
    ///   - query: Search query string
    ///   - offset: Pagination offset
    ///   - limit: Number of results
    /// - Returns: Array of matching stories
    func searchStories(query: String, offset: Int = 0, limit: Int = 20) async throws -> [Story] {
        if useMockData {
            return await mockSearchStories(query: query)
        }

        let encodedQuery = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query
        let endpoint = "/api/stories/search?q=\(encodedQuery)&offset=\(offset)&limit=\(limit)"
        // API returns direct array
        let azureStories: [AzureStoryResponse] = try await request(endpoint: endpoint, method: "GET")
        return azureStories.map { $0.toStory() }
    }

    /// Fetch all source articles for a story
    /// - Parameter storyId: Story ID
    /// - Returns: Array of source articles
    func fetchStorySources(storyId: String) async throws -> [SourceArticle] {
        log.log("Fetching sources for story: \(storyId)", category: .api, level: .info)

        if useMockData {
            // Return mock sources
            return []
        }

        let endpoint = "/api/stories/\(storyId)/sources"

        do {
            let response: [AzureSourceResponse] = try await request(endpoint: endpoint, method: "GET")
            let sources = response.map { azureSource in
                SourceArticle(
                    id: azureSource.id,
                    source: azureSource.source,
                    title: azureSource.title,
                    articleURL: azureSource.article_url,
                    publishedAt: azureSource.published_at
                )
            }
            log.log("✅ Loaded \(sources.count) sources for story", category: .api, level: .info)
            return sources
        } catch {
            log.logError(error, context: "fetchStorySources failed")
            throw error
        }
    }

    // MARK: - User Interactions API
    
    /// Record interaction with story
    private func recordInteraction(
        storyId: String,
        type: String,
        dwellTime: Int = 0,
        cardFlipped: Bool = false
    ) async throws {
        let endpoint = "/api/stories/\(storyId)/interact"
        
        let interaction = AzureInteractionRequest(
            interaction_type: type,
            session_id: UUID().uuidString,
            dwell_time_seconds: dwellTime,
            card_flipped: cardFlipped,
            sources_clicked: [],
            device_info: [
                "platform": "ios",
                "app_version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0.0",
                "os_version": UIDevice.current.systemVersion
            ]
        )
        
        // Try to record interaction, but don't fail if auth isn't configured yet
        do {
            let _: EmptyResponse = try await request(endpoint: endpoint, method: "POST", body: interaction)
            log.log("✅ Interaction '\(type)' recorded for story", category: .api, level: .info)
        } catch let error as APIError where error.localizedDescription.contains("Unauthorized") {
            log.log("⚠️ Interaction tracking unavailable - Firebase credentials not configured on Azure (this is OK)", category: .api, level: .debug)
            // Silently fail - interactions will work once Firebase is configured
            // For now, track locally in SwiftData
        } catch {
            log.log("⚠️ Failed to record interaction: \(error.localizedDescription)", category: .api, level: .debug)
            // Non-critical, don't throw
        }
    }
    
    /// Mark story as read
    func markAsRead(storyId: String) async throws {
        if useMockData {
            await mockMarkAsRead(storyId: storyId)
            return
        }
        
        try await recordInteraction(storyId: storyId, type: "view")
    }
    
    /// Save story for later
    func saveStory(storyId: String) async throws {
        if useMockData {
            await mockSaveStory(storyId: storyId)
            return
        }
        
        try await recordInteraction(storyId: storyId, type: "save")
    }
    
    /// Unsave story
    func unsaveStory(storyId: String) async throws {
        if useMockData {
            await mockUnsaveStory(storyId: storyId)
            return
        }
        
        try await recordInteraction(storyId: storyId, type: "unsave")
    }
    
    /// Like story
    func likeStory(storyId: String) async throws {
        if useMockData {
            await mockLikeStory(storyId: storyId)
            return
        }
        
        try await recordInteraction(storyId: storyId, type: "like")
    }
    
    /// Unlike story
    func unlikeStory(storyId: String) async throws {
        if useMockData {
            await mockUnlikeStory(storyId: storyId)
            return
        }
        
        try await recordInteraction(storyId: storyId, type: "unlike")
    }
    
    /// Get saved stories
    func getSavedStories(offset: Int = 0, limit: Int = 20) async throws -> [Story] {
        if useMockData {
            return await mockGetSavedStories()
        }
        
        // TEMPORARY: Return empty array since saved stories endpoint doesn't exist yet
        log.log("⚠️ Saved stories endpoint not available, returning empty array", category: .api, level: .warning)
        return []
    }
    
    // MARK: - User Preferences API
    
    /// Get user preferences
    func getUserPreferences() async throws -> UserPreferences {
        if useMockData {
            return authService.isAnonymous ? .anonymous : .default
        }
        
        let endpoint = "/api/user/preferences"
        return try await request(endpoint: endpoint, method: "GET")
    }
    
    /// Update user preferences
    func updateUserPreferences(_ preferences: UserPreferences) async throws {
        if useMockData {
            await mockUpdatePreferences(preferences)
            return
        }
        
        let endpoint = "/api/user/preferences"
        let _: EmptyResponse = try await request(
            endpoint: endpoint,
            method: "PUT",
            body: preferences
        )
    }
    
    // MARK: - Sources API
    
    /// Get all available news sources
    func getSources() async throws -> [Source] {
        if useMockData {
            return Source.mockArray
        }
        
        // TEMPORARY: Return mock sources since sources endpoint doesn't exist yet
        log.log("⚠️ Sources endpoint not available, returning mock sources", category: .api, level: .warning)
        return Source.mockArray
    }
    
    // MARK: - Health Check
    
    /// Check API health status
    func checkHealth() async throws -> Bool {
        if useMockData {
            return true
        }
        
        let endpoint = "/health"
        let response: HealthResponse = try await request(
            endpoint: endpoint,
            method: "GET",
            requiresAuth: false
        )
        return response.status == "healthy"
    }
    
    // MARK: - Private Request Method
    
    /// Generic request method with retry logic
    private func request<T: Decodable, B: Encodable>(
        endpoint: String,
        method: String,
        body: B? = nil as EmptyBody?,
        requiresAuth: Bool = true,
        retryCount: Int = 0
    ) async throws -> T {
        let startTime = Date()
        
        // Build URL
        guard let url = URL(string: baseURL + endpoint) else {
            log.log("❌ Invalid URL: \(baseURL + endpoint)", category: .api, level: .error)
            throw APIError.invalidURL
        }
        
        // Create request
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = method
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.setValue("ios/1.0", forHTTPHeaderField: "User-Agent")
        
        var headers: [String: String] = [
            "Content-Type": "application/json",
            "User-Agent": "ios/1.0"
        ]
        
        // Add authentication if required
        if requiresAuth {
            do {
                let token = try await authService.getIDToken(forceRefresh: retryCount > 0)
                urlRequest.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
                headers["Authorization"] = "Bearer [TOKEN]"
            } catch {
                log.logAuth("❌ Failed to get Firebase token: \(error.localizedDescription)", level: .error)
                throw APIError.unauthorized
            }
        }
        
        // Add body if provided
        var bodyData: Data? = nil
        if let body = body {
            bodyData = try encoder.encode(body)
            urlRequest.httpBody = bodyData
        }
        
        // Log request
        log.logAPIRequest(method, endpoint: endpoint, headers: headers, body: bodyData)
        
        // Execute request
        do {
            let (data, response) = try await session.data(for: urlRequest)
            let duration = Date().timeIntervalSince(startTime)
            
            // Validate response
            guard let httpResponse = response as? HTTPURLResponse else {
                log.log("❌ Invalid HTTP response", category: .network, level: .error)
                throw APIError.invalidResponse
            }
            
            // Log response
            log.logAPIResponse(httpResponse.statusCode, endpoint: endpoint, data: data, duration: duration)
            
            switch httpResponse.statusCode {
            case 200...299:
                // Success - decode response
                do {
                    let decoded = try decoder.decode(T.self, from: data)
                    log.logTiming("\(method) \(endpoint)", duration: duration)
                    return decoded
                } catch {
                    log.log("❌ Decoding error: \(error)", category: .api, level: .error)
                    if let jsonString = String(data: data, encoding: .utf8) {
                        log.log("Response data: \(jsonString.prefix(500))", category: .api, level: .debug)
                    }
                    throw APIError.decodingError(error)
                }
                
            case 401:
                // Unauthorized - retry once with token refresh
                log.logAuth("Received 401 Unauthorized, retry count: \(retryCount)", level: .warning)
                if retryCount == 0 {
                    log.logAuth("Retrying with refreshed token...", level: .info)
                    return try await request(
                        endpoint: endpoint,
                        method: method,
                        body: body,
                        requiresAuth: requiresAuth,
                        retryCount: 1
                    )
                }
                log.logAuth("❌ Authentication failed after retry", level: .error)
                throw APIError.unauthorized
                
            case 429:
                // Rate limit exceeded
                log.log("⚠️ Rate limit exceeded (429)", category: .api, level: .warning)
                throw APIError.rateLimitExceeded
                
            default:
                log.log("❌ Server error: \(httpResponse.statusCode)", category: .api, level: .error)
                throw APIError.serverError(httpResponse.statusCode)
            }
            
        } catch let error as APIError {
            log.logError(error, context: "\(method) \(endpoint)")
            throw error
        } catch {
            log.logError(error, context: "\(method) \(endpoint) - Network error")
            throw APIError.networkError(error)
        }
    }
    
    // MARK: - Admin API
    
    /// Get comprehensive admin metrics (admin-only endpoint)
    func getAdminMetrics() async throws -> AdminMetrics {
        log.log("Fetching admin metrics", category: .api)
        
        let endpoint = "/api/admin/metrics"
        
        return try await request(
            endpoint: endpoint,
            method: "GET",
            requiresAuth: true
        )
    }
}

// MARK: - Azure API Response Models

/// Azure API story response
struct AzureStoryResponse: Codable {
    let id: String
    let title: String
    let category: String
    let tags: [String]
    let status: String
    let verification_level: Int
    let summary: AzureSummaryResponse?
    let source_count: Int
    let first_seen: String
    let last_updated: String
    let importance_score: Int
    let breaking_news: Bool
    let user_liked: Bool?
    let user_saved: Bool?
    let sources: [AzureSourceResponse]?
}

struct AzureSummaryResponse: Codable {
    let text: String
    let version: Int
    let word_count: Int
    let generated_at: String
}

struct AzureSourceResponse: Codable {
    let id: String
    let source: String
    let title: String
    let article_url: String
    let published_at: String
}

struct FeedResponse: Codable {
    let stories: [AzureStoryResponse]
    let total: Int?
    let has_more: Bool?
    let next_offset: Int?
    
    enum CodingKeys: String, CodingKey {
        case stories, total
        case has_more
        case next_offset
    }
}

struct ClusterResponse: Codable {
    let clusters: [StoryCluster]
    let total: Int?
    let has_more: Bool?
}

struct SourcesResponse: Codable {
    let sources: [Source]
}

struct HealthResponse: Codable {
    let status: String
    let version: String?
    let timestamp: String?
    let cosmos_db: String?
}

/// Empty body for requests without a body
private struct EmptyBody: Encodable {}

/// Empty response for requests that don't return data
private struct EmptyResponse: Decodable {}

// MARK: - Azure Response Mapping

extension AzureStoryResponse {
    /// Convert Azure API response to app Story model
    func toStory() -> Story {
        // Parse dates - need to handle both with and without fractional seconds
        // API returns: "2026-01-04T03:09:11Z" or "2026-01-04T04:42:14.901474Z"
        let dateFormatter = ISO8601DateFormatter()
        dateFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        
        // Try with fractional seconds first, then without
        let publishedDate: Date
        if let date = dateFormatter.date(from: first_seen) {
            publishedDate = date
        } else {
            // Try without fractional seconds
            dateFormatter.formatOptions = [.withInternetDateTime]
            publishedDate = dateFormatter.date(from: first_seen) ?? Date()
        }
        
        // Map category
        let newsCategory: NewsCategory = {
            switch category.lowercased() {
            case "tech", "technology": return .technology
            case "business", "finance": return .business
            case "politics", "government": return .politics
            case "science": return .science
            case "health", "medical": return .health
            case "sports": return .sports
            case "entertainment": return .entertainment
            case "world", "international": return .world
            case "environment", "climate": return .environment
            default: return .topStories
            }
        }()
        
        // Create primary source from first article or generic
        let primarySource: Source
        if let firstSource = sources?.first {
            // API already returns properly formatted source names (e.g., "BBC News", "The Guardian")
            // Use them as-is without modification
            primarySource = Source(
                id: firstSource.source,
                name: firstSource.source, // Use the source name exactly as provided by API
                domain: "\(firstSource.source.lowercased().replacingOccurrences(of: " ", with: "")).com",
                logoURL: URL(string: "https://logo.clearbit.com/\(firstSource.source.lowercased().replacingOccurrences(of: " ", with: "")).com")
            )
        } else {
            primarySource = .mock // Fallback
        }
        
                // Convert all sources to SourceArticle objects
                let sourceArticles: [SourceArticle] = sources?.map { azureSource in
                    SourceArticle(
                        id: azureSource.id,
                        source: azureSource.source,
                        title: azureSource.title,
                        articleURL: azureSource.article_url,
                        publishedAt: azureSource.published_at
                    )
                } ?? []

                // PERFORMANCE FIX: Backend now handles deduplication correctly (Nov 2025)
                // Removed client-side deduplication that was causing CPU overhead
                let deduplicatedSources = sourceArticles
        
        // PERFORMANCE FIX: Verbose decode logging disabled by default
        // Enable via log.logVerboseDecode = true for debugging source issues
        #if DEBUG
        if log.logVerboseDecode {
            if let sources = sources {
                log.log("📦 [API DECODE] Story: \(id)", category: .api, level: .debug)
                log.log("   API returned \(sources.count) source objects", category: .api, level: .debug)
                
                // Only log duplicates (actual issues)
                let sourceNames = sources.map { $0.source }
                let uniqueNames = Set(sourceNames)
                if uniqueNames.count != sourceNames.count {
                    log.log("⚠️ [API DECODE] API RETURNED DUPLICATES!", category: .api, level: .warning)
                    let counts = Dictionary(grouping: sourceNames, by: { $0 }).mapValues { $0.count }
                    let duplicates = counts.filter { $0.value > 1 }
                    for (name, count) in duplicates {
                        log.log("   '\(name)' appears \(count) times", category: .api, level: .warning)
                    }
                }
            } else {
                log.log("⚠️ [API DECODE] Story: \(id) - sources field is nil", category: .api, level: .warning)
            }
        }
        #endif
        
        // Get article URL from first valid source
        let articleURL: URL = {
            // Try to find a valid URL from sources
            if let sources = sources {
                for source in sources {
                    if !source.article_url.isEmpty,
                       let url = URL(string: source.article_url),
                       url.scheme != nil {
                        return url
                    }
                }
            }
            // Fallback for stories without valid URLs
            return URL(string: "https://newsreel.app/article-unavailable")!
        }()
        
        // Estimate reading time from summary
        let readingTime = (summary?.word_count ?? 150) / 200 // ~200 words per minute
        
        // Map status
        let storyStatus: StoryStatus = {
            switch status.uppercased() {
            case "MONITORING": return .monitoring
            case "DEVELOPING": return .developing
            case "VERIFIED": return .verified
            case "BREAKING": return .breaking
            default: return .verified
            }
        }()
        
        // Parse last updated date - also handle both formats
        let lastUpdatedDate: Date?
        let lastUpdatedFormatter = ISO8601DateFormatter()
        lastUpdatedFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = lastUpdatedFormatter.date(from: last_updated) {
            lastUpdatedDate = date
        } else {
            lastUpdatedFormatter.formatOptions = [.withInternetDateTime]
            lastUpdatedDate = lastUpdatedFormatter.date(from: last_updated)
        }
        
        // Verbose decode logging (disabled by default)
        #if DEBUG
        if log.logVerboseDecode {
            log.log("📦 [API DECODE] Creating Story object with \(deduplicatedSources.count) sources", category: .api, level: .debug)
        }
        #endif
        
        return Story(
            id: id,
            title: title,
            summary: summary?.text ?? "No summary available",
            content: nil,
            imageURL: nil, // TODO: Extract from sources if available
            publishedAt: publishedDate,
            source: primarySource,
            sources: deduplicatedSources,  // Use deduplicated array
            category: newsCategory,
            url: articleURL,
            clusterId: nil,
            sentiment: nil,
            readingTimeMinutes: max(1, readingTime),
            status: storyStatus,
            lastUpdated: lastUpdatedDate,
            sourceCount: source_count,
            credibilityScore: Double(verification_level) / 10.0, // Convert 0-10 to 0.0-1.0
            trendingScore: breaking_news ? 0.9 : Double(importance_score) / 10.0,
            isRead: false,
            isSaved: user_saved ?? false,
            isLiked: user_liked ?? false
        )
    }
}


// MARK: - Mock Data Support

extension APIService {
    /// Simulates network delay for more realistic mock behavior
    private func mockDelay() async {
        try? await Task.sleep(nanoseconds: UInt64.random(in: 300_000_000...800_000_000)) // 0.3-0.8 seconds
    }
    
    private func mockGetFeed(offset: Int, limit: Int, category: NewsCategory?) async -> [Story] {
        await mockDelay()
        let stories = category == nil ? Story.mockArray : Story.mockArray.filter { $0.category == category }
        let start = min(offset, stories.count)
        let end = min(offset + limit, stories.count)
        return Array(stories[start..<end])
    }
    
    private func mockGetClusters(offset: Int, limit: Int) async -> [StoryCluster] {
        await mockDelay()
        let clusters = StoryCluster.mockArray
        let start = min(offset, clusters.count)
        let end = min(offset + limit, clusters.count)
        return Array(clusters[start..<end])
    }
    
    private func mockGetStory(id: String) async -> Story {
        await mockDelay()
        return Story.mockArray.first(where: { $0.id == id }) ?? Story.mock
    }
    
    private func mockGetBreakingNews() async -> [Story] {
        await mockDelay()
        return Array(Story.mockArray.prefix(2))
    }
    
    private func mockSearchStories(query: String) async -> [Story] {
        await mockDelay()
        let lowercaseQuery = query.lowercased()
        return Story.mockArray.filter {
            $0.title.lowercased().contains(lowercaseQuery) ||
            $0.summary.lowercased().contains(lowercaseQuery)
        }
    }
    
    private func mockMarkAsRead(storyId: String) async {
        await mockDelay()
        print("Mock: Marked story \(storyId) as read")
    }
    
    private func mockSaveStory(storyId: String) async {
        await mockDelay()
        print("Mock: Saved story \(storyId)")
    }
    
    private func mockUnsaveStory(storyId: String) async {
        await mockDelay()
        print("Mock: Unsaved story \(storyId)")
    }
    
    private func mockLikeStory(storyId: String) async {
        await mockDelay()
        print("Mock: Liked story \(storyId)")
    }
    
    private func mockUnlikeStory(storyId: String) async {
        await mockDelay()
        print("Mock: Unliked story \(storyId)")
    }
    
    private func mockGetSavedStories() async -> [Story] {
        await mockDelay()
        return Array(Story.mockArray.prefix(2))
    }
    
    private func mockUpdatePreferences(_ preferences: UserPreferences) async {
        await mockDelay()
        print("Mock: Updated preferences")
    }
    
    // MARK: - Device Token Registration (Push Notifications)
    
    /// Register device token for push notifications
    func registerDeviceToken(token: String) async throws {
        log.log("📱 Registering device token with backend", category: .api, level: .info)
        
        let endpoint = "\(baseURL)/api/user/device-token"
        guard let url = URL(string: endpoint) else {
            throw APIError.invalidURL
        }
        
        let body: [String: Any] = [
            "fcm_token": token,
            "platform": "ios",
            "app_version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
        ]
        
        let jsonData = try JSONSerialization.data(withJSONObject: body)
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = jsonData
        
        // Add JWT token for authentication
        if let jwt = try? await authService.getIDToken() {
            request.setValue("Bearer \(jwt)", forHTTPHeaderField: "Authorization")
        }
        
        do {
            let (_, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            
            switch httpResponse.statusCode {
            case 200...299:
                log.log("✅ Device token registered successfully", category: .api, level: .info)
            case 401:
                throw APIError.unauthorized
            default:
                throw APIError.serverError(httpResponse.statusCode)
            }
        } catch let error as APIError {
            log.logError(error, context: "Register device token")
            throw error
        } catch {
            log.logError(error, context: "Register device token network error")
            throw APIError.networkError(error)
        }
    }
    
    /// Unregister device token (e.g., on logout)
    func unregisterDeviceToken(token: String) async throws {
        log.log("📱 Unregistering device token from backend", category: .api, level: .info)
        
        let endpoint = "\(baseURL)/api/user/device-token/\(token)"
        guard let url = URL(string: endpoint) else {
            throw APIError.invalidURL
        }
        
        let body: [String: Any] = [
            "fcm_token": token
        ]
        
        let jsonData = try JSONSerialization.data(withJSONObject: body)
        
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = jsonData
        
        // Add JWT token for authentication
        if let jwt = try? await authService.getIDToken() {
            request.setValue("Bearer \(jwt)", forHTTPHeaderField: "Authorization")
        }
        
        do {
            let (_, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            
            switch httpResponse.statusCode {
            case 200...299:
                log.log("✅ Device token unregistered successfully", category: .api, level: .info)
            case 401:
                throw APIError.unauthorized
            default:
                throw APIError.serverError(httpResponse.statusCode)
            }
        } catch let error as APIError {
            log.logError(error, context: "Unregister device token")
            throw error
        } catch {
            log.logError(error, context: "Unregister device token network error")
            throw APIError.networkError(error)
        }
    }
}
