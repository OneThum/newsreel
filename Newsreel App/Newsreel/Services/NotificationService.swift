//
//  NotificationService.swift
//  Newsreel
//
//  Push Notification Service
//  Handles APNs registration, FCM tokens, and notification permissions
//

import Foundation
import UserNotifications
import FirebaseMessaging
import SwiftUI

/// Manages push notifications for breaking news
@MainActor
class NotificationService: NSObject, ObservableObject {
    static let shared = NotificationService()
    
    @Published var isAuthorized = false
    @Published var fcmToken: String?
    @Published var notificationToHandle: UNNotificationResponse?
    
    private let apiService: APIService?
    
    override init() {
        self.apiService = nil
        super.init()
    }
    
    /// Initialize with API service for token registration
    func configure(with apiService: APIService) {
        log.section("NOTIFICATION SERVICE")
        log.log("📢 Configuring notification service", category: .analytics, level: .info)
        
        // Set up notification center delegate
        UNUserNotificationCenter.current().delegate = self
        
        // Set up FCM delegate
        Messaging.messaging().delegate = self
        
        // Check current authorization status
        checkAuthorizationStatus()
        
        log.log("✅ Notification service configured", category: .analytics, level: .info)
    }
    
    /// Request notification permissions from user
    func requestPermission() async -> Bool {
        log.log("📢 Requesting notification permission", category: .analytics, level: .info)
        
        do {
            let granted = try await UNUserNotificationCenter.current()
                .requestAuthorization(options: [.alert, .badge, .sound, .criticalAlert])
            
            await MainActor.run {
                isAuthorized = granted
            }
            
            if granted {
                log.log("✅ Notification permission granted", category: .analytics, level: .info)
                // Register for remote notifications
                registerForRemoteNotifications()
            } else {
                log.log("⚠️ Notification permission denied", category: .analytics, level: .warning)
            }
            
            return granted
        } catch {
            log.logError(error, context: "Request notification permission")
            return false
        }
    }
    
    /// Register for remote notifications (APNs)
    private func registerForRemoteNotifications() {
        UIApplication.shared.registerForRemoteNotifications()
        log.log("📱 Registered for remote notifications", category: .analytics, level: .info)
    }
    
    /// Check current authorization status
    func checkAuthorizationStatus() {
        UNUserNotificationCenter.current().getNotificationSettings { settings in
            Task { @MainActor in
                self.isAuthorized = settings.authorizationStatus == .authorized
                log.log("📊 Notification status: \(settings.authorizationStatus.rawValue)", 
                       category: .analytics, level: .debug)
            }
        }
    }
    
    /// Register FCM token with backend
    func registerToken(with apiService: APIService) async {
        guard let token = fcmToken else {
            log.log("⚠️ No FCM token available to register", category: .analytics, level: .warning)
            return
        }
        
        log.log("📤 Registering FCM token with backend", category: .analytics, level: .info)
        
        do {
            try await apiService.registerDeviceToken(token: token)
            log.log("✅ FCM token registered successfully", category: .analytics, level: .info)
        } catch {
            log.logError(error, context: "Register FCM token")
        }
    }
    
    /// Unregister token from backend
    func unregisterToken(with apiService: APIService) async {
        guard let token = fcmToken else { return }
        
        log.log("📤 Unregistering FCM token from backend", category: .analytics, level: .info)
        
        do {
            try await apiService.unregisterDeviceToken(token: token)
            log.log("✅ FCM token unregistered", category: .analytics, level: .info)
        } catch {
            log.logError(error, context: "Unregister FCM token")
        }
    }
    
    /// Handle notification tap - extracts story ID for navigation
    func handleNotificationTap(_ response: UNNotificationResponse) -> String? {
        let userInfo = response.notification.request.content.userInfo
        
        log.log("📲 Handling notification tap", category: .analytics, level: .info)
        log.log("   User info: \(userInfo)", category: .analytics, level: .debug)
        
        // Extract story ID from notification payload
        if let storyId = userInfo["storyId"] as? String {
            log.log("   Story ID: \(storyId)", category: .analytics, level: .info)
            return storyId
        }
        
        return nil
    }
}

// MARK: - UNUserNotificationCenterDelegate

extension NotificationService: UNUserNotificationCenterDelegate {
    
    /// Handle notification when app is in foreground
    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        let userInfo = notification.request.content.userInfo
        
        Task { @MainActor in
            log.log("📢 Received notification while app in foreground", category: .analytics, level: .info)
            log.log("   Title: \(notification.request.content.title)", category: .analytics, level: .debug)
            log.log("   Body: \(notification.request.content.body)", category: .analytics, level: .debug)
        }
        
        // Show notification even when app is in foreground for breaking news
        // This ensures users always see critical breaking news alerts
        if let priority = userInfo["priority"] as? String, priority == "breaking" {
            completionHandler([.banner, .sound, .badge])
        } else {
            // For regular notifications, don't show banner (rely on in-app UI)
            completionHandler([.badge])
        }
    }
    
    /// Handle notification tap
    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        Task { @MainActor in
            log.log("📲 User tapped notification", category: .analytics, level: .info)
            
            // Store response for app to handle
            notificationToHandle = response
        }
        
        completionHandler()
    }
}

// MARK: - MessagingDelegate

extension NotificationService: MessagingDelegate {
    
    /// Handle FCM token refresh
    nonisolated func messaging(_ messaging: Messaging, didReceiveRegistrationToken fcmToken: String?) {
        Task { @MainActor in
            log.log("🔑 FCM token received: \(fcmToken?.prefix(20) ?? "nil")...", 
                   category: .analytics, level: .info)
            
            self.fcmToken = fcmToken
            
            // Auto-register if we have an API service
            // This will be called from NewsreelApp after services are initialized
        }
    }
}

// MARK: - Notification Models

/// Represents a breaking news notification payload
struct BreakingNewsNotification: Codable {
    let storyId: String
    let title: String
    let body: String
    let priority: String
    let category: String
    let sourceCount: Int
}

