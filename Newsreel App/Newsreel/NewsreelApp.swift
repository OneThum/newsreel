//
//  NewsreelApp.swift
//  Newsreel
//
//  Created by David McLauchlan on 10/8/25.
//

import SwiftUI
import FirebaseCore
import SwiftData

@main
struct NewsreelApp: App {
    @State private var showLaunchScreen = true
    @StateObject private var authService = AuthService()
    @StateObject private var apiService: APIService
    @StateObject private var persistenceService = PersistenceService.shared
    @StateObject private var subscriptionService = SubscriptionService()
    @StateObject private var notificationService = NotificationService.shared
    
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    
    init() {
        // Force print to console to verify logging is working
        print("\n\n")
        print("═══════════════════════════════════════════════════════")
        print("🚀 NEWSREEL APP LAUNCHING - YOU SHOULD SEE THIS!")
        print("═══════════════════════════════════════════════════════")
        print("\n")

        log.section("APP LAUNCH")
        log.log("🚀 Newsreel app launching...", category: .ui, level: .info)

        // Configure Firebase
        log.log("Configuring Firebase...", category: .auth, level: .info)
        FirebaseApp.configure()
        log.log("✅ Firebase configured", category: .auth, level: .info)

        // Configure navigation bar appearance with Outfit font
        let appearance = UINavigationBarAppearance()
        appearance.configureWithDefaultBackground()

        // Large title (used in main pages)
        appearance.largeTitleTextAttributes = [
            .font: UIFont(name: "Outfit-Bold", size: 34) ?? UIFont.systemFont(ofSize: 34, weight: .bold),
            .foregroundColor: UIColor.label
        ]

        // Regular title (used in detail pages)
        appearance.titleTextAttributes = [
            .font: UIFont(name: "Outfit-SemiBold", size: 17) ?? UIFont.systemFont(ofSize: 17, weight: .semibold),
            .foregroundColor: UIColor.label
        ]

        UINavigationBar.appearance().standardAppearance = appearance
        UINavigationBar.appearance().compactAppearance = appearance
        UINavigationBar.appearance().scrollEdgeAppearance = appearance

        // Initialize APIService with AuthService
        log.log("Initializing services...", category: .ui, level: .info)
        let auth = AuthService()
        _authService = StateObject(wrappedValue: auth)
        let api = APIService(authService: auth, useMockData: false)
        _apiService = StateObject(wrappedValue: api)

        log.log("✅ App initialization complete", category: .ui, level: .info)
        log.log("   Backend: https://newsreel-api.azurewebsites.net", category: .api, level: .info)
        log.log("   Mock Mode: DISABLED (using live Azure backend)", category: .api, level: .info)
        log.separator()
    }
    
    var body: some Scene {
        WindowGroup {
            ZStack {
                // Show launch screen first, then main content
                if showLaunchScreen {
                    LaunchScreenView(isPresented: $showLaunchScreen)
                } else {
                    ContentView()
                        .environmentObject(authService)
                        .environmentObject(apiService)
                        .environmentObject(persistenceService)
                        .environmentObject(subscriptionService)
                        .environmentObject(notificationService)
                }
            }
            .preferredColorScheme(.dark) // Default to dark mode
        }
        .modelContainer(persistenceService.modelContainer)
    }
}

// MARK: - AppDelegate for APNs Registration

import FirebaseMessaging

class AppDelegate: NSObject, UIApplicationDelegate {
    
    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        log.log("📱 App launched", category: .analytics, level: .info)
        return true
    }
    
    func application(
        _ application: UIApplication,
        didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data
    ) {
        log.log("📱 APNs device token received", category: .analytics, level: .info)
        
        // Pass to FCM for token generation
        Messaging.messaging().apnsToken = deviceToken
        
        let tokenParts = deviceToken.map { data in String(format: "%02.2hhx", data) }
        let token = tokenParts.joined()
        log.log("   Token: \(token.prefix(20))...", category: .analytics, level: .debug)
    }
    
    func application(
        _ application: UIApplication,
        didFailToRegisterForRemoteNotificationsWithError error: Error
    ) {
        log.logError(error, context: "APNs registration failed")
    }
}
