//
//  OnboardingView.swift
//  Newsreel
//
//  Onboarding flow for first-time users
//

import SwiftUI
import UserNotifications

struct OnboardingView: View {
    @Binding var isPresented: Bool
    @State private var currentPage = 0
    @State private var selectedCategories: Set<NewsCategory> = []
    @EnvironmentObject var notificationService: NotificationService
    @EnvironmentObject var apiService: APIService

    // Total pages in onboarding
    private let totalPages = 5

    var body: some View {
        ZStack {
            AppBackground()

            VStack(spacing: 0) {
                // Progress indicator
                HStack(spacing: 8) {
                    ForEach(0..<totalPages, id: \.self) { index in
                        Capsule()
                            .fill(index <= currentPage ? Color.blue : Color.gray.opacity(0.3))
                            .frame(height: 4)
                            .frame(maxWidth: .infinity)
                    }
                }
                .padding(.horizontal, 32)
                .padding(.top, 60)
                .padding(.bottom, 20)

                // Page content
                TabView(selection: $currentPage) {
                    // Page 1: Welcome
                    WelcomePage()
                        .tag(0)

                    // Page 2: AI-Powered Summaries
                    FeaturePage(
                        icon: "sparkles",
                        title: "AI-Powered Summaries",
                        description: "Get concise, unbiased summaries of breaking news from multiple trusted sources. Our AI combines coverage from different perspectives to give you the complete story.",
                        accentColor: .purple
                    )
                    .tag(1)

                    // Page 3: Smart Clustering
                    FeaturePage(
                        icon: "square.stack.3d.up.fill",
                        title: "Smart Story Clustering",
                        description: "See the same story from different angles. We automatically group related articles from various news sources so you can compare coverage and perspectives.",
                        accentColor: .blue
                    )
                    .tag(2)

                    // Page 4: Category Selection
                    CategorySelectionPage(selectedCategories: $selectedCategories)
                        .tag(3)

                    // Page 5: Notifications
                    NotificationPermissionPage(
                        onComplete: completeOnboarding
                    )
                    .tag(4)
                }
                .tabViewStyle(.page(indexDisplayMode: .never))
                .animation(.easeInOut, value: currentPage)

                // Navigation buttons
                HStack(spacing: 16) {
                    // Back button
                    if currentPage > 0 {
                        Button(action: {
                            withAnimation {
                                currentPage -= 1
                            }
                        }) {
                            Text("Back")
                                .font(.outfit(size: 17, weight: .medium))
                                .foregroundColor(.secondary)
                                .frame(maxWidth: .infinity)
                                .frame(height: 56)
                                .background(Color.secondary.opacity(0.1))
                                .cornerRadius(16)
                        }
                    }

                    // Next/Continue button
                    Button(action: {
                        if currentPage < totalPages - 1 {
                            withAnimation {
                                currentPage += 1
                            }
                        } else {
                            completeOnboarding()
                        }
                    }) {
                        Text(currentPage == totalPages - 1 ? "Get Started" : "Continue")
                            .font(.outfit(size: 17, weight: .semiBold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 56)
                            .background(
                                LinearGradient(
                                    colors: [.blue, .purple],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .cornerRadius(16)
                            .shadow(color: .blue.opacity(0.3), radius: 10, y: 5)
                    }
                    .disabled(currentPage == 3 && selectedCategories.isEmpty)
                    .opacity(currentPage == 3 && selectedCategories.isEmpty ? 0.5 : 1.0)
                }
                .padding(.horizontal, 32)
                .padding(.bottom, 40)
            }
        }
        .preferredColorScheme(.dark)
        .interactiveDismissDisabled()
    }

    /// Complete onboarding and save preferences
    private func completeOnboarding() {
        // Save category preferences if any selected
        if !selectedCategories.isEmpty {
            Task {
                do {
                    let preferences = UserPreferences(
                        preferredCategories: selectedCategories,
                        enableNotifications: true
                    )
                    try await apiService.updateUserPreferences(preferences)
                    log.log("✅ Saved onboarding preferences: \(selectedCategories.count) categories",
                           category: .ui, level: .info)
                } catch {
                    log.logError(error, context: "Failed to save onboarding preferences")
                }
            }
        }

        // Mark onboarding as complete
        UserDefaults.standard.set(true, forKey: "hasCompletedOnboarding")

        // Dismiss onboarding
        withAnimation(.smooth) {
            isPresented = false
        }

        log.log("🎉 Onboarding completed", category: .analytics, level: .info)
    }
}

// MARK: - Welcome Page

struct WelcomePage: View {
    @State private var isAnimating = false

    var body: some View {
        VStack(spacing: 32) {
            Spacer()

            // App Icon
            Image(systemName: "newspaper.fill")
                .font(.system(size: 100, weight: .bold))
                .foregroundStyle(
                    LinearGradient(
                        colors: [.blue, .purple],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .glowing(color: .blue, radius: 40, intensity: 0.5)
                .scaleEffect(isAnimating ? 1.0 : 0.8)
                .opacity(isAnimating ? 1.0 : 0.0)

            VStack(spacing: 16) {
                Text("Welcome to Newsreel")
                    .font(.outfit(size: 36, weight: .extraBold))
                    .multilineTextAlignment(.center)
                    .offset(y: isAnimating ? 0 : 20)
                    .opacity(isAnimating ? 1.0 : 0.0)

                Text("Your AI-powered news companion that brings you unbiased summaries from multiple trusted sources")
                    .font(.outfit(size: 17, weight: .medium))
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 32)
                    .offset(y: isAnimating ? 0 : 20)
                    .opacity(isAnimating ? 1.0 : 0.0)
            }

            Spacer()
            Spacer()
        }
        .onAppear {
            withAnimation(.spring(response: 0.8, dampingFraction: 0.7)) {
                isAnimating = true
            }
        }
    }
}

// MARK: - Feature Page

struct FeaturePage: View {
    let icon: String
    let title: String
    let description: String
    let accentColor: Color

    @State private var isAnimating = false

    var body: some View {
        VStack(spacing: 32) {
            Spacer()

            // Feature Icon
            Image(systemName: icon)
                .font(.system(size: 80, weight: .semibold))
                .foregroundStyle(
                    LinearGradient(
                        colors: [accentColor, accentColor.opacity(0.6)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .glowing(color: accentColor, radius: 30, intensity: 0.4)
                .scaleEffect(isAnimating ? 1.0 : 0.8)
                .opacity(isAnimating ? 1.0 : 0.0)

            VStack(spacing: 16) {
                Text(title)
                    .font(.outfit(size: 32, weight: .bold))
                    .multilineTextAlignment(.center)
                    .offset(y: isAnimating ? 0 : 20)
                    .opacity(isAnimating ? 1.0 : 0.0)

                Text(description)
                    .font(.outfit(size: 17, weight: .medium))
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 40)
                    .offset(y: isAnimating ? 0 : 20)
                    .opacity(isAnimating ? 1.0 : 0.0)
            }

            Spacer()
            Spacer()
        }
        .onAppear {
            withAnimation(.spring(response: 0.8, dampingFraction: 0.7).delay(0.2)) {
                isAnimating = true
            }
        }
    }
}

// MARK: - Category Selection Page

struct CategorySelectionPage: View {
    @Binding var selectedCategories: Set<NewsCategory>
    @State private var isAnimating = false

    // Default recommended categories
    private let recommendedCategories: [NewsCategory] = [
        .topStories, .technology, .business, .world
    ]

    var body: some View {
        VStack(spacing: 24) {
            VStack(spacing: 12) {
                Text("Choose Your Interests")
                    .font(.outfit(size: 32, weight: .bold))
                    .multilineTextAlignment(.center)
                    .offset(y: isAnimating ? 0 : 20)
                    .opacity(isAnimating ? 1.0 : 0.0)

                Text("Select the categories you care about. You can always change these later in settings.")
                    .font(.outfit(size: 16, weight: .medium))
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 32)
                    .offset(y: isAnimating ? 0 : 20)
                    .opacity(isAnimating ? 1.0 : 0.0)
            }
            .padding(.top, 40)

            // Category Grid
            ScrollView {
                LazyVGrid(columns: [
                    GridItem(.flexible(), spacing: 12),
                    GridItem(.flexible(), spacing: 12)
                ], spacing: 12) {
                    ForEach(Array(NewsCategory.allCases.enumerated()), id: \.element) { index, category in
                        CategoryButton(
                            category: category,
                            isSelected: selectedCategories.contains(category)
                        ) {
                            withAnimation(.spring(response: 0.3)) {
                                if selectedCategories.contains(category) {
                                    selectedCategories.remove(category)
                                } else {
                                    selectedCategories.insert(category)
                                }
                            }
                        }
                        .offset(y: isAnimating ? 0 : 20)
                        .opacity(isAnimating ? 1.0 : 0.0)
                        .animation(.spring(response: 0.5).delay(Double(index) * 0.05), value: isAnimating)
                    }
                }
                .padding(.horizontal, 32)
            }
            .frame(maxHeight: .infinity)
        }
        .onAppear {
            // Pre-select recommended categories
            if selectedCategories.isEmpty {
                selectedCategories = Set(recommendedCategories)
            }

            withAnimation(.spring(response: 0.8, dampingFraction: 0.7).delay(0.1)) {
                isAnimating = true
            }
        }
    }
}

// MARK: - Category Button

struct CategoryButton: View {
    let category: NewsCategory
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 12) {
                Image(systemName: category.icon)
                    .font(.system(size: 32, weight: .semibold))
                    .foregroundColor(isSelected ? .white : category.color)

                Text(category.displayName)
                    .font(.outfit(size: 15, weight: .semiBold))
                    .foregroundColor(isSelected ? .white : .primary)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 120)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(isSelected ? category.color : Color.secondary.opacity(0.1))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .strokeBorder(
                        isSelected ? category.color.opacity(0.5) : Color.clear,
                        lineWidth: 2
                    )
            )
            .shadow(
                color: isSelected ? category.color.opacity(0.3) : Color.clear,
                radius: 10,
                y: 5
            )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Notification Permission Page

struct NotificationPermissionPage: View {
    let onComplete: () -> Void

    @State private var isAnimating = false
    @State private var notificationStatus: UNAuthorizationStatus = .notDetermined
    @EnvironmentObject var notificationService: NotificationService

    var body: some View {
        VStack(spacing: 32) {
            Spacer()

            // Notification Icon
            Image(systemName: notificationStatus == .authorized ? "bell.badge.fill" : "bell.fill")
                .font(.system(size: 80, weight: .semibold))
                .foregroundStyle(
                    LinearGradient(
                        colors: [.blue, .cyan],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .glowing(color: .blue, radius: 30, intensity: 0.4)
                .scaleEffect(isAnimating ? 1.0 : 0.8)
                .opacity(isAnimating ? 1.0 : 0.0)

            VStack(spacing: 16) {
                Text(notificationStatus == .authorized ? "Notifications Enabled!" : "Stay Updated")
                    .font(.outfit(size: 32, weight: .bold))
                    .multilineTextAlignment(.center)
                    .offset(y: isAnimating ? 0 : 20)
                    .opacity(isAnimating ? 1.0 : 0.0)

                Text(notificationStatus == .authorized
                     ? "You'll receive alerts for breaking news stories and developing stories."
                     : "Get notified about breaking news and important developing stories as they happen.")
                    .font(.outfit(size: 17, weight: .medium))
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 40)
                    .offset(y: isAnimating ? 0 : 20)
                    .opacity(isAnimating ? 1.0 : 0.0)
            }

            // Enable Notifications Button (if not yet authorized)
            if notificationStatus == .notDetermined {
                Button(action: {
                    Task {
                        await requestNotificationPermission()
                    }
                }) {
                    HStack(spacing: 12) {
                        Image(systemName: "bell.badge.fill")
                        Text("Enable Notifications")
                    }
                    .font(.outfit(size: 17, weight: .semiBold))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .frame(height: 56)
                    .background(
                        LinearGradient(
                            colors: [.blue, .cyan],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .cornerRadius(16)
                    .shadow(color: .blue.opacity(0.3), radius: 10, y: 5)
                }
                .padding(.horizontal, 32)
                .offset(y: isAnimating ? 0 : 20)
                .opacity(isAnimating ? 1.0 : 0.0)

                Button(action: {
                    onComplete()
                }) {
                    Text("Maybe Later")
                        .font(.outfit(size: 16, weight: .medium))
                        .foregroundColor(.secondary)
                }
                .offset(y: isAnimating ? 0 : 20)
                .opacity(isAnimating ? 1.0 : 0.0)
            }

            Spacer()
            Spacer()

            // Terms and Privacy
            VStack(spacing: 8) {
                Text("By continuing, you agree to our")
                    .font(.outfit(size: 13, weight: .medium))
                    .foregroundColor(.secondary)

                HStack(spacing: 4) {
                    Link("Terms of Service", destination: URL(string: "https://www.onethum.com/terms-of-service")!)
                        .font(.outfit(size: 13, weight: .semiBold))

                    Text("and")
                        .font(.outfit(size: 13, weight: .medium))
                        .foregroundColor(.secondary)

                    Link("Privacy Policy", destination: URL(string: "https://www.onethum.com/privacy-policy")!)
                        .font(.outfit(size: 13, weight: .semiBold))
                }
            }
            .offset(y: isAnimating ? 0 : 20)
            .opacity(isAnimating ? 1.0 : 0.0)
        }
        .onAppear {
            withAnimation(.spring(response: 0.8, dampingFraction: 0.7).delay(0.2)) {
                isAnimating = true
            }
            checkNotificationStatus()
        }
    }

    /// Check current notification authorization status
    private func checkNotificationStatus() {
        UNUserNotificationCenter.current().getNotificationSettings { settings in
            DispatchQueue.main.async {
                self.notificationStatus = settings.authorizationStatus
            }
        }
    }

    /// Request notification permission
    private func requestNotificationPermission() async {
        let granted = await notificationService.requestPermission()

        DispatchQueue.main.async {
            withAnimation {
                self.notificationStatus = granted ? .authorized : .denied
            }

            if granted {
                log.log("✅ Notification permission granted during onboarding",
                       category: .analytics, level: .info)

                // Auto-complete after brief delay to show success state
                DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                    onComplete()
                }
            } else {
                log.log("⚠️ Notification permission denied during onboarding",
                       category: .analytics, level: .info)
            }
        }
    }
}

// MARK: - Preview

#Preview("Onboarding") {
    let authService = AuthService()
    OnboardingView(isPresented: .constant(true))
        .environmentObject(authService)
        .environmentObject(NotificationService.shared)
        .environmentObject(APIService(authService: authService, useMockData: false))
        .environmentObject(SubscriptionService())
        .environmentObject(PersistenceService.shared)
}