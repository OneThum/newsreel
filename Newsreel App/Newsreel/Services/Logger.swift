//
//  Logger.swift
//  Newsreel
//
//  Professional debug logging system following iOS best practices
//  Based on Apple's unified logging system (os.log)
//

import Foundation
import OSLog

/// Logging categories for organized debugging
enum LogCategory: String {
    case api = "API"
    case auth = "Auth"
    case persistence = "Persistence"
    case ui = "UI"
    case subscription = "Subscription"
    case network = "Network"
    case error = "Error"
    case analytics = "Analytics"
}

/// Log levels following OSLog conventions
enum LogLevel: String {
    case debug = "🔍 DEBUG"
    case info = "ℹ️ INFO"
    case warning = "⚠️ WARNING"
    case error = "❌ ERROR"
    case critical = "🚨 CRITICAL"
}

/// Professional logging service
class Logger {
    
    // MARK: - Singleton
    
    static let shared = Logger()
    
    // MARK: - Configuration
    
    /// Enable/disable logging (disable in production)
    private var isEnabled: Bool {
        #if DEBUG
        return true
        #else
        return false
        #endif
    }
    
    /// Enable detailed network logging (API request/response bodies)
    var logNetworkDetails: Bool = false
    
    /// Enable timing logs
    var logTiming: Bool = true
    
    /// Enable verbose decode logging (per-story decode details)
    /// WARNING: Very verbose - produces 80+ log lines per feed load
    var logVerboseDecode: Bool = false
    
    // MARK: - OSLog Loggers
    
    private let apiLogger = OSLog(subsystem: "com.onethum.newsreel", category: "API")
    private let authLogger = OSLog(subsystem: "com.onethum.newsreel", category: "Auth")
    private let persistenceLogger = OSLog(subsystem: "com.onethum.newsreel", category: "Persistence")
    private let uiLogger = OSLog(subsystem: "com.onethum.newsreel", category: "UI")
    private let subscriptionLogger = OSLog(subsystem: "com.onethum.newsreel", category: "Subscription")
    private let networkLogger = OSLog(subsystem: "com.onethum.newsreel", category: "Network")
    private let errorLogger = OSLog(subsystem: "com.onethum.newsreel", category: "Error")
    
    // MARK: - Private Init
    
    private init() {}
    
    // MARK: - Public Logging Methods
    
    /// Log a message with category and level
    func log(_ message: String, category: LogCategory = .ui, level: LogLevel = .info, file: String = #file, function: String = #function, line: Int = #line) {
        guard isEnabled else { return }
        
        let fileName = URL(fileURLWithPath: file).lastPathComponent
        let timestamp = dateFormatter.string(from: Date())
        let prefix = "[\(timestamp)] [\(category.rawValue)] \(level.rawValue)"
        let location = "[\(fileName):\(line) \(function)]"
        let fullMessage = "\(prefix) \(location) - \(message)"
        
        // Log to OSLog (integrates with Console.app and Xcode console)
        let osLogger = getOSLogger(for: category)
        let osLogType = getOSLogType(for: level)
        os_log("%{public}@", log: osLogger, type: osLogType, fullMessage)
    }
    
    /// Log API request
    func logAPIRequest(_ method: String, endpoint: String, headers: [String: String]? = nil, body: Data? = nil) {
        guard isEnabled else { return }
        
        var message = "🌐 API Request: \(method) \(endpoint)"
        
        if logNetworkDetails {
            if let headers = headers, !headers.isEmpty {
                message += "\n   Headers: \(headers.keys.joined(separator: ", "))"
            }
            if let body = body, let bodyString = String(data: body, encoding: .utf8) {
                let preview = bodyString.prefix(200)
                message += "\n   Body: \(preview)\(bodyString.count > 200 ? "..." : "")"
            }
        }
        
        log(message, category: .api, level: .info)
    }
    
    /// Log API response
    func logAPIResponse(_ statusCode: Int, endpoint: String, data: Data?, duration: TimeInterval? = nil) {
        guard isEnabled else { return }
        
        let statusEmoji = statusCode >= 200 && statusCode < 300 ? "✅" : "❌"
        var message = "\(statusEmoji) API Response: \(statusCode) for \(endpoint)"
        
        if let duration = duration, logTiming {
            message += " (\(String(format: "%.2f", duration * 1000))ms)"
        }
        
        if logNetworkDetails, let data = data {
            message += "\n   Size: \(ByteCountFormatter.string(fromByteCount: Int64(data.count), countStyle: .file))"
            
            if let jsonString = String(data: data, encoding: .utf8) {
                let preview = jsonString.prefix(300)
                message += "\n   Data: \(preview)\(jsonString.count > 300 ? "..." : "")"
            }
        }
        
        let level: LogLevel = statusCode >= 200 && statusCode < 300 ? .info : .error
        log(message, category: .api, level: level)
    }
    
    /// Log authentication event
    func logAuth(_ message: String, level: LogLevel = .info) {
        log(message, category: .auth, level: level)
    }
    
    /// Log error with details
    func logError(_ error: Error, context: String = "", file: String = #file, function: String = #function, line: Int = #line) {
        let errorType = String(describing: type(of: error))
        let contextText = context.isEmpty ? errorType : context
        let message = """
        
        ╔══════════════════════════════════════════════════════════
        ║ ERROR: \(contextText)
        ╟──────────────────────────────────────────────────────────
        ║ Error: \(error.localizedDescription)
        ║ Type: \(errorType)
        ╚══════════════════════════════════════════════════════════
        """
        log(message, category: .error, level: .error, file: file, function: function, line: line)
    }
    
    /// Log timing for performance tracking
    func logTiming(_ operation: String, duration: TimeInterval) {
        guard logTiming else { return }
        let ms = duration * 1000
        let emoji = ms < 100 ? "⚡" : ms < 500 ? "⏱️" : "🐌"
        log("\(emoji) \(operation) took \(String(format: "%.2f", ms))ms", category: .network, level: .info)
    }
    
    /// Log UI event
    func logUI(_ message: String) {
        log(message, category: .ui, level: .debug)
    }
    
    /// Log persistence operation
    func logPersistence(_ message: String, level: LogLevel = .info) {
        log(message, category: .persistence, level: level)
    }
    
    // MARK: - Specialized Logging (Feed Quality Metrics)
    
    /// Log feed operation with metrics
    func logFeedOperation(_ operation: String, storyCount: Int? = nil, category: String? = nil, duration: TimeInterval? = nil) {
        var message = operation
        if let count = storyCount {
            message += " (\(count) stories"
            if let cat = category {
                message += ", \(cat)"
            }
            if let dur = duration {
                message += ", \(Int(dur * 1000))ms"
            }
            message += ")"
        }
        log(message, category: .api, level: .info)
    }
    
    /// Log source diversity metrics
    func logSourceDiversity(uniqueSources: Int, totalStories: Int, distribution: [String: Int]) {
        let topSources = distribution.sorted { $0.value > $1.value }.prefix(5)
        let sourcesStr = topSources.map { "\($0.key): \($0.value)" }.joined(separator: ", ")
        let diversityScore = Double(uniqueSources) / Double(max(totalStories, 1))
        let emoji = diversityScore > 0.6 ? "✅" : diversityScore > 0.4 ? "⚠️" : "❌"
        log("\(emoji) Feed Diversity: \(uniqueSources) sources, \(totalStories) stories (score: \(String(format: "%.2f", diversityScore))). Top: \(sourcesStr)", 
            category: .api, level: .info)
    }
    
    /// Log categorization decision
    func logCategorization(articleId: String, title: String, category: String, confidence: Double? = nil) {
        var message = "Categorized: \(category) - \(title.prefix(50))"
        if let conf = confidence {
            let emoji = conf > 0.7 ? "✅" : conf > 0.5 ? "⚠️" : "❌"
            message += " \(emoji) (confidence: \(Int(conf * 100))%)"
        }
        log(message, category: .api, level: .debug)
    }
    
    /// Measure and log operation performance
    @MainActor
    func measureOperation<T>(_ name: String, operation: () async throws -> T) async rethrows -> T {
        let start = Date()
        log("⏱️ Starting: \(name)", category: .network, level: .debug)
        
        let result = try await operation()
        
        let duration = Date().timeIntervalSince(start)
        logTiming(name, duration: duration)
        
        return result
    }
    
    // MARK: - Helper Methods
    
    private func getOSLogger(for category: LogCategory) -> OSLog {
        switch category {
        case .api: return apiLogger
        case .auth: return authLogger
        case .persistence: return persistenceLogger
        case .ui: return uiLogger
        case .subscription: return subscriptionLogger
        case .network: return networkLogger
        case .error, .analytics: return errorLogger
        }
    }
    
    private func getOSLogType(for level: LogLevel) -> OSLogType {
        switch level {
        case .debug: return .debug
        case .info: return .info
        case .warning: return .default
        case .error: return .error
        case .critical: return .fault
        }
    }
    
    private let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss.SSS"
        return formatter
    }()
}

// MARK: - Convenience Methods

extension Logger {
    /// Print a nicely formatted separator
    func separator(_ title: String = "") {
        guard isEnabled else { return }
        if title.isEmpty {
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        } else {
            print("━━━━━━━━━━━━━━━━ \(title) ━━━━━━━━━━━━━━━━")
        }
    }
    
    /// Print a section header
    func section(_ title: String) {
        guard isEnabled else { return }
        print("""
        
        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        ┃  \(title.padding(toLength: 50, withPad: " ", startingAt: 0))┃
        ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
        """)
    }
}

// MARK: - Global Convenience

/// Quick access to logger
let log = Logger.shared

