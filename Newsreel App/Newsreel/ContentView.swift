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
    @State private var showLaunchScreen = true
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
            .opacity(showLaunchScreen ? 0 : 1)
            
            // Launch Screen Overlay
            if showLaunchScreen {
                LaunchScreenView(isPresented: $showLaunchScreen)
                    .transition(.opacity)
                    .zIndex(999)
            }
        }
        .onChange(of: notificationService.notificationToHandle) { _, response in
            if let response = response {
                handleNotificationTap(response)
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
    ContentView()
        .environmentObject(AuthService())
}

#Preview("Loading") {
    LoadingView()
}
