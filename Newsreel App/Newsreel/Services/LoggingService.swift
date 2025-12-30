import Foundation
import OSLog

/// Centralized logging service with structured logging and performance tracking
@MainActor
class LoggingService {
    static let shared = LoggingService()
    
    // MARK: - Log Categories
    enum LogCategory: String {
        case network = "🌐 Network"
        case auth = "🔐 Auth"
        case ui = "📱 UI"
        case data = "💾 Data"
        case performance = "⚡️ Performance"
        case api = "📡 API"
        case error = "❌ Error"
        case feed = "📰 Feed"
        case clustering = "🔗 Clustering"
        case categorization = "🏷️ Category"
    }
    
    enum LogLevel {
        case debug
        case info
        case warning
        case error
        case critical
    }
    
    // MARK: - OSLog Loggers
    private let networkLogger = Logger(subsystem: Bundle.main.bundleIdentifier ?? "com.newsreel", category: "network")
    private let authLogger = Logger(subsystem: Bundle.main.bundleIdentifier ?? "com.newsreel", category: "auth")
    private let uiLogger = Logger(subsystem: Bundle.main.bundleIdentifier ?? "com.newsreel", category: "ui")
    private let dataLogger = Logger(subsystem: Bundle.main.bundleIdentifier ?? "com.newsreel", category: "data")
    private let performanceLogger = Logger(subsystem: Bundle.main.bundleIdentifier ?? "com.newsreel", category: "performance")
    
    // MARK: - Configuration
    #if DEBUG
    private let isEnabled = true
    private let minimumLevel: LogLevel = .debug
    #else
    private let isEnabled = true
    private let minimumLevel: LogLevel = .info
    #endif
    
    private var sessionId = UUID().uuidString
    private var correlationId: String?
    
    private init() {
        log("📱 Logging Service Initialized (Session: \(sessionId.prefix(8)))", category: .ui, level: .info)
    }
    
    // MARK: - Public Logging Methods
    
    func log(_ message: String, category: LogCategory = .ui, level: LogLevel = .info, 
             file: String = #file, function: String = #function, line: Int = #line) {
        guard isEnabled && shouldLog(level: level) else { return }
        
        let fileName = (file as NSString).lastPathComponent
        let timestamp = dateFormatter.string(from: Date())
        let logMessage = "\(category.rawValue) [\(timestamp)] \(message) (\(fileName):\(line))"
        
        // Console output
        print(logMessage)
        
        // OSLog output (for Instruments & Console.app)
        let logger = getLogger(for: category)
        switch level {
        case .debug:
            logger.debug("\(message, privacy: .public)")
        case .info:
            logger.info("\(message, privacy: .public)")
        case .warning:
            logger.warning("\(message, privacy: .public)")
        case .error, .critical:
            logger.error("\(message, privacy: .public)")
        }
    }
    
    func section(_ title: String, category: LogCategory = .ui) {
        let separator = String(repeating: "=", count: 60)
        log("\n\(separator)\n  \(title)\n\(separator)", category: category, level: .info)
    }
    
    // MARK: - Specialized Logging
    
    func logNetworkRequest(url: String, method: String, headers: [String: String]? = nil) {
        log("→ \(method) \(url)", category: .network, level: .debug)
    }
    
    func logNetworkResponse(url: String, statusCode: Int, duration: TimeInterval, bodySize: Int? = nil) {
        var message = "← \(statusCode) \(url) (\(Int(duration * 1000))ms"
        if let size = bodySize {
            message += ", \(size) bytes"
        }
        message += ")"
        
        let level: LogLevel = statusCode >= 400 ? .error : .debug
        log(message, category: .network, level: level)
    }
    
    func logAuth(_ message: String, level: LogLevel = .info) {
        log(message, category: .auth, level: level)
    }
    
    func logFeedOperation(_ operation: String, storyCount: Int? = nil, category: NewsCategory? = nil, duration: TimeInterval? = nil) {
        var message = operation
        if let count = storyCount {
            message += " (\(count) stories"
            if let cat = category {
                message += ", \(cat.displayName)"
            }
            if let dur = duration {
                message += ", \(Int(dur * 1000))ms"
            }
            message += ")"
        }
        log(message, category: .feed, level: .info)
    }
    
    func logCategorization(articleId: String, title: String, category: NewsCategory, confidence: Double? = nil) {
        var message = "Categorized: \(category.displayName) - \(title.prefix(50))"
        if let conf = confidence {
            message += " (confidence: \(Int(conf * 100))%)"
        }
        log(message, category: .categorization, level: .debug)
    }
    
    func logSourceDiversity(uniqueSources: Int, totalStories: Int, distribution: [String: Int]) {
        let topSources = distribution.sorted { $0.value > $1.value }.prefix(5)
        let sourcesStr = topSources.map { "\($0.key): \($0.value)" }.joined(separator: ", ")
        log("Feed Diversity: \(uniqueSources) sources, \(totalStories) stories. Top: \(sourcesStr)", 
            category: .feed, level: .info)
    }
    
    // MARK: - Performance Tracking
    
    func measureOperation<T>(_ name: String, category: LogCategory = .performance, 
                            operation: () async throws -> T) async rethrows -> T {
        let start = Date()
        log("⏱️ Starting: \(name)", category: category, level: .debug)
        
        let result = try await operation()
        
        let duration = Date().timeIntervalSince(start)
        log("✅ Completed: \(name) in \(Int(duration * 1000))ms", category: category, level: .info)
        
        return result
    }
    
    // MARK: - Error Logging
    
    func logError(_ error: Error, context: String, category: LogCategory = .error, 
                  file: String = #file, function: String = #function, line: Int = #line) {
        let errorDescription = (error as NSError).localizedDescription
        let fileName = (file as NSString).lastPathComponent
        
        log("ERROR in \(context): \(errorDescription) at \(fileName):\(line)", 
            category: category, level: .error)
    }
    
    // MARK: - Helper Methods
    
    private func shouldLog(level: LogLevel) -> Bool {
        let levels: [LogLevel] = [.debug, .info, .warning, .error, .critical]
        guard let currentIndex = levels.firstIndex(of: level),
              let minimumIndex = levels.firstIndex(of: minimumLevel) else {
            return true
        }
        return currentIndex >= minimumIndex
    }
    
    private func getLogger(for category: LogCategory) -> Logger {
        switch category {
        case .network, .api:
            return networkLogger
        case .auth:
            return authLogger
        case .ui, .feed:
            return uiLogger
        case .data:
            return dataLogger
        case .performance:
            return performanceLogger
        case .error, .clustering, .categorization:
            return uiLogger
        }
    }
    
    private lazy var dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss.SSS"
        return formatter
    }()
    
    // MARK: - Correlation ID
    
    func setCorrelationId(_ id: String) {
        correlationId = id
    }
    
    func clearCorrelationId() {
        correlationId = nil
    }
}

// MARK: - Global Convenience
let log = LoggingService.shared

