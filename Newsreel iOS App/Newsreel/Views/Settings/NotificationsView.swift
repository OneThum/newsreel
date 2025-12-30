//
//  NotificationsView.swift
//  Newsreel
//
//  Push notification preferences and settings
//

import SwiftUI
import UserNotifications

struct NotificationsView: View {
    @EnvironmentObject var authService: AuthService
    @StateObject private var viewModel = NotificationsViewModel()
    
    var body: some View {
        ZStack {
            AppBackground()
            
            List {
                // Notification Status
                Section {
                    HStack(spacing: 12) {
                        ZStack {
                            Circle()
                                .fill(viewModel.notificationsEnabled ? .green.opacity(0.2) : .red.opacity(0.2))
                                .frame(width: 44, height: 44)
                            
                            Image(systemName: viewModel.notificationsEnabled ? "bell.fill" : "bell.slash.fill")
                                .font(.system(size: 20))
                                .foregroundStyle(viewModel.notificationsEnabled ? .green : .red)
                        }
                        
                        VStack(alignment: .leading, spacing: 4) {
                            Text(viewModel.notificationsEnabled ? "Notifications Enabled" : "Notifications Disabled")
                                .font(.outfit(size: 18, weight: .semiBold))
                            
                            Text(viewModel.notificationsEnabled ? "You'll receive breaking news alerts" : "Enable to get breaking news alerts")
                                .font(.outfit(size: 14, weight: .regular))
                                .foregroundStyle(.secondary)
                        }
                        
                        Spacer()
                    }
                    .padding(.vertical, 8)
                    
                    if !viewModel.notificationsEnabled {
                        Button(action: {
                            viewModel.requestNotificationPermission()
                        }) {
                            HStack {
                                Spacer()
                                Text("Enable Notifications")
                                    .font(.outfit(size: 16, weight: .semiBold))
                                    .foregroundStyle(.white)
                                Spacer()
                            }
                        }
                        .listRowBackground(
                            RoundedRectangle(cornerRadius: 12)
                                .fill(
                                    LinearGradient(
                                        colors: [.blue, .purple],
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                        )
                    }
                }
                
                // Breaking News
                if viewModel.notificationsEnabled {
                    Section {
                        Toggle(isOn: $viewModel.breakingNewsAlerts) {
                            HStack(spacing: 12) {
                                Image(systemName: "exclamationmark.triangle.fill")
                                    .font(.system(size: 18))
                                    .foregroundStyle(.red)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text("Breaking News")
                                        .font(.outfit(size: 16, weight: .regular))
                                    Text("Urgent, time-sensitive news")
                                        .font(.outfit(size: 13, weight: .regular))
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                        .tint(.red)
                        
                        Toggle(isOn: $viewModel.majorStoriesAlerts) {
                            HStack(spacing: 12) {
                                Image(systemName: "star.fill")
                                    .font(.system(size: 18))
                                    .foregroundStyle(.orange)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text("Major Stories")
                                        .font(.outfit(size: 16, weight: .regular))
                                    Text("Important news from multiple sources")
                                        .font(.outfit(size: 13, weight: .regular))
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                        .tint(.orange)
                    } header: {
                        Text("Alert Types")
                            .font(.outfit(size: 13, weight: .semiBold))
                    }
                    
                    // Category Alerts
                    Section {
                        ForEach(NewsCategory.allCases.filter { $0 != .topStories }) { category in
                            Toggle(isOn: Binding(
                                get: { viewModel.categoryAlerts.contains(category) },
                                set: { enabled in
                                    if enabled {
                                        viewModel.categoryAlerts.insert(category)
                                    } else {
                                        viewModel.categoryAlerts.remove(category)
                                    }
                                }
                            )) {
                                HStack(spacing: 12) {
                                    Image(systemName: category.icon)
                                        .font(.system(size: 18))
                                        .foregroundStyle(category.color)
                                    Text(category.displayName)
                                        .font(.outfit(size: 16, weight: .regular))
                                }
                            }
                            .tint(category.color)
                        }
                    } header: {
                        Text("Category Alerts")
                            .font(.outfit(size: 13, weight: .semiBold))
                    } footer: {
                        Text("Get notified about breaking news in these categories")
                            .font(.outfit(size: 12, weight: .regular))
                    }
                    
                    // Timing
                    Section {
                        Toggle(isOn: $viewModel.quietHoursEnabled) {
                            HStack(spacing: 12) {
                                Image(systemName: "moon.fill")
                                    .font(.system(size: 18))
                                    .foregroundStyle(.indigo)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text("Quiet Hours")
                                        .font(.outfit(size: 16, weight: .regular))
                                    Text("Mute notifications during sleeping hours")
                                        .font(.outfit(size: 13, weight: .regular))
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                        .tint(.indigo)
                        
                        if viewModel.quietHoursEnabled {
                            DatePicker("Start", selection: $viewModel.quietHoursStart, displayedComponents: .hourAndMinute)
                                .font(.outfit(size: 16, weight: .regular))
                            
                            DatePicker("End", selection: $viewModel.quietHoursEnd, displayedComponents: .hourAndMinute)
                                .font(.outfit(size: 16, weight: .regular))
                        }
                    } header: {
                        Text("Schedule")
                            .font(.outfit(size: 13, weight: .semiBold))
                    }
                    
                    // Save Button
                    Section {
                        Button(action: {
                            Task {
                                await viewModel.saveSettings()
                            }
                        }) {
                            HStack {
                                Spacer()
                                if viewModel.isSaving {
                                    ProgressView()
                                        .tint(.white)
                                } else {
                                    Text("Save Notification Settings")
                                        .font(.outfit(size: 16, weight: .semiBold))
                                        .foregroundStyle(.white)
                                }
                                Spacer()
                            }
                        }
                        .listRowBackground(
                            RoundedRectangle(cornerRadius: 12)
                                .fill(
                                    LinearGradient(
                                        colors: [.blue, .purple],
                                        startPoint: .leading,
                                        endPoint: .trailing
                                    )
                                )
                        )
                        .disabled(viewModel.isSaving)
                    }
                }
            }
            .scrollContentBackground(.hidden)
        }
        .navigationTitle("Notifications")
        .navigationBarTitleDisplayMode(.large)
        .task {
            await viewModel.checkNotificationStatus()
        }
    }
}

// MARK: - View Model

@MainActor
class NotificationsViewModel: ObservableObject {
    @Published var notificationsEnabled: Bool = false
    @Published var breakingNewsAlerts: Bool = true
    @Published var majorStoriesAlerts: Bool = true
    @Published var categoryAlerts: Set<NewsCategory> = []
    @Published var quietHoursEnabled: Bool = false
    @Published var quietHoursStart: Date = {
        var components = DateComponents()
        components.hour = 22
        components.minute = 0
        return Calendar.current.date(from: components) ?? Date()
    }()
    @Published var quietHoursEnd: Date = {
        var components = DateComponents()
        components.hour = 7
        components.minute = 0
        return Calendar.current.date(from: components) ?? Date()
    }()
    @Published var isSaving: Bool = false
    
    init() {
        loadSettings()
    }
    
    func checkNotificationStatus() async {
        let settings = await UNUserNotificationCenter.current().notificationSettings()
        notificationsEnabled = settings.authorizationStatus == .authorized
    }
    
    func requestNotificationPermission() {
        Task {
            do {
                let granted = try await UNUserNotificationCenter.current().requestAuthorization(
                    options: [.alert, .badge, .sound]
                )
                
                if granted {
                    await MainActor.run {
                        notificationsEnabled = true
                        HapticManager.notification(type: .success)
                    }
                } else {
                    // Open settings
                    if let settingsURL = URL(string: UIApplication.openSettingsURLString) {
                        await UIApplication.shared.open(settingsURL)
                    }
                }
            } catch {
                print("Error requesting notification permission: \(error)")
            }
        }
    }
    
    func saveSettings() async {
        isSaving = true
        
        // Save to UserDefaults
        UserDefaults.standard.set(breakingNewsAlerts, forKey: "breakingNewsAlerts")
        UserDefaults.standard.set(majorStoriesAlerts, forKey: "majorStoriesAlerts")
        UserDefaults.standard.set(Array(categoryAlerts.map { $0.rawValue }), forKey: "categoryAlerts")
        UserDefaults.standard.set(quietHoursEnabled, forKey: "quietHoursEnabled")
        UserDefaults.standard.set(quietHoursStart, forKey: "quietHoursStart")
        UserDefaults.standard.set(quietHoursEnd, forKey: "quietHoursEnd")
        
        // Simulate API call
        try? await Task.sleep(nanoseconds: 500_000_000)
        
        // TODO: Sync with backend API
        // try await apiService.updateNotificationPreferences(...)
        
        isSaving = false
        
        HapticManager.notification(type: .success)
    }
    
    private func loadSettings() {
        breakingNewsAlerts = UserDefaults.standard.bool(forKey: "breakingNewsAlerts", default: true)
        majorStoriesAlerts = UserDefaults.standard.bool(forKey: "majorStoriesAlerts", default: true)
        quietHoursEnabled = UserDefaults.standard.bool(forKey: "quietHoursEnabled", default: false)
        
        if let categoriesData = UserDefaults.standard.array(forKey: "categoryAlerts") as? [String] {
            categoryAlerts = Set(categoriesData.compactMap { NewsCategory(rawValue: $0) })
        } else {
            // Default: all categories enabled
            categoryAlerts = Set(NewsCategory.allCases.filter { $0 != .topStories })
        }
        
        if let start = UserDefaults.standard.object(forKey: "quietHoursStart") as? Date {
            quietHoursStart = start
        }
        if let end = UserDefaults.standard.object(forKey: "quietHoursEnd") as? Date {
            quietHoursEnd = end
        }
    }
}

#Preview {
    NavigationStack {
        NotificationsView()
            .environmentObject(AuthService())
    }
}


