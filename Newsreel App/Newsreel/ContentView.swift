//
//  ContentView.swift
//  Newsreel
//
//  Created by David McLauchlan on 10/8/25.
//
//  Root view that handles authentication state
//

import SwiftUI
import UserNotifications

struct ContentView: View {
    @EnvironmentObject var authService: AuthService
    @EnvironmentObject var notificationService: NotificationService
    @State private var showOnboarding = false
    @State private var storyIdToOpen: String? // Story to navigate to from notification

    var body: some View {
        ZStack {
            // Main App Content
            Group {
                switch authService.authState {
                case .authenticated:
                    MainAppView(notificationStoryId: $storyIdToOpen)

                case .unauthenticated:
                    LoginView()

                case .loading:
                    LoadingView()
                }
            }
            .animation(.smooth, value: authService.authState)

            // Onboarding Overlay (shown after main app loads)
            if showOnboarding {
                OnboardingView(isPresented: $showOnboarding)
                    .transition(.opacity)
                    .zIndex(999)
            }
        }
        .onChange(of: notificationService.notificationToHandle) { _, response in
            if let response = response {
                handleNotificationTap(response)
            }
        }
        .onChange(of: authService.authState) { _, newState in
            // When user authenticates, check if we should show onboarding
            if case .authenticated = newState {
                checkOnboardingStatus()
            }
        }
    }

    /// Handle notification tap - extract story ID and navigate
    private func handleNotificationTap(_ response: UNNotificationResponse) {
        if let storyId = notificationService.handleNotificationTap(response) {
            log.log("📲 Navigating to story from notification: \(storyId)",
                   category: .analytics, level: .info)
            storyIdToOpen = storyId

            // Clear the notification after handling
            notificationService.notificationToHandle = nil
        }
    }

    /// Check if user has completed onboarding
    private func checkOnboardingStatus() {
        let hasCompletedOnboarding = UserDefaults.standard.bool(forKey: "hasCompletedOnboarding")

        // Only show onboarding if user is authenticated and hasn't completed it
        if case .authenticated = authService.authState, !hasCompletedOnboarding {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                withAnimation(.smooth) {
                    showOnboarding = true
                }
                log.log("🎓 Showing onboarding for first-time user", category: .ui, level: .info)
            }
        }
    }
}

// MARK: - Loading View

struct LoadingView: View {
    @State private var isAnimating = false
    
    var body: some View {
        ZStack {
            AppBackground()
            
            VStack(spacing: 24) {
                // Animated logo
                Image(systemName: "newspaper.fill")
                    .font(.system(size: 72, weight: .bold))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.blue, .purple],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .glowing(color: .blue, radius: 30, intensity: 0.4)
                    .pulsing(duration: 2.0, min: 0.95, max: 1.05)
                    .scaleEffect(isAnimating ? 1.0 : 0.8)
                    .opacity(isAnimating ? 1.0 : 0.0)
                
                Text("Newsreel")
                    .font(.outfit(size: 42, weight: .extraBold))
                    .offset(y: isAnimating ? 0 : 20)
                    .opacity(isAnimating ? 1.0 : 0.0)
                
                ProgressView()
                    .tint(.primary)
                    .scaleEffect(1.2)
                    .offset(y: isAnimating ? 0 : 20)
                    .opacity(isAnimating ? 1.0 : 0.0)
            }
            .onAppear {
                withAnimation(.spring(response: 0.8, dampingFraction: 0.7)) {
                    isAnimating = true
                }
            }
        }
    }
}

#Preview("Content View") {
    let authService = AuthService()
    ContentView()
        .environmentObject(authService)
        .environmentObject(NotificationService.shared)
        .environmentObject(APIService(authService: authService, useMockData: false))
        .environmentObject(SubscriptionService())
        .environmentObject(PersistenceService.shared)
}

#Preview("Loading") {
    LoadingView()
}
