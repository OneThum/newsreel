//
//  PreferencesView.swift
//  Newsreel
//
//  User preferences and personalization settings
//

import SwiftUI

struct PreferencesView: View {
    @EnvironmentObject var authService: AuthService
    @StateObject private var viewModel = PreferencesViewModel()
    
    var body: some View {
        ZStack {
            AppBackground()
            
            List {
                // Category Preferences
                Section {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Choose the topics you're interested in")
                            .font(.outfit(size: 15, weight: .regular))
                            .foregroundStyle(.secondary)
                        
                        LazyVGrid(columns: [GridItem(.adaptive(minimum: 150))], spacing: 12) {
                            ForEach(NewsCategory.allCases.filter { $0 != .topStories }) { category in
                                CategoryPreferenceButton(
                                    category: category,
                                    isSelected: viewModel.selectedCategories.contains(category),
                                    action: {
                                        viewModel.toggleCategory(category)
                                    }
                                )
                            }
                        }
                    }
                    .padding(.vertical, 8)
                } header: {
                    Text("Interests")
                        .font(.outfit(size: 13, weight: .semiBold))
                }
                
                // Content Preferences
                Section {
                    Toggle(isOn: $viewModel.showImages) {
                        HStack(spacing: 12) {
                            Image(systemName: "photo.fill")
                                .font(.system(size: 18))
                                .foregroundStyle(.blue)
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Show Images")
                                    .font(.outfit(size: 16, weight: .regular))
                                Text("Display story images in feed")
                                    .font(.outfit(size: 13, weight: .regular))
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    .tint(.blue)
                    
                    Toggle(isOn: $viewModel.autoPlayVideos) {
                        HStack(spacing: 12) {
                            Image(systemName: "play.circle.fill")
                                .font(.system(size: 18))
                                .foregroundStyle(.purple)
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Auto-Play Videos")
                                    .font(.outfit(size: 16, weight: .regular))
                                Text("Videos play automatically in feed")
                                    .font(.outfit(size: 13, weight: .regular))
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    .tint(.purple)
                    
                    Picker("Reading Time Filter", selection: $viewModel.maxReadingTime) {
                        Text("Any length").tag(0)
                        Text("5 min or less").tag(5)
                        Text("10 min or less").tag(10)
                        Text("15 min or less").tag(15)
                    }
                    .pickerStyle(.navigationLink)
                } header: {
                    Text("Content Display")
                        .font(.outfit(size: 13, weight: .semiBold))
                }
                
                // Privacy & Data
                Section {
                    Toggle(isOn: $viewModel.personalizedFeed) {
                        HStack(spacing: 12) {
                            Image(systemName: "sparkles")
                                .font(.system(size: 18))
                                .foregroundStyle(.yellow)
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Personalized Feed")
                                    .font(.outfit(size: 16, weight: .regular))
                                Text("Use reading history to personalize")
                                    .font(.outfit(size: 13, weight: .regular))
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    .tint(.yellow)
                    
                    Toggle(isOn: $viewModel.trackingEnabled) {
                        HStack(spacing: 12) {
                            Image(systemName: "chart.line.uptrend.xyaxis")
                                .font(.system(size: 18))
                                .foregroundStyle(.green)
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Analytics")
                                    .font(.outfit(size: 16, weight: .regular))
                                Text("Help improve Newsreel")
                                    .font(.outfit(size: 13, weight: .regular))
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    .tint(.green)
                    
                    NavigationLink(destination: Text("Privacy Policy")) {
                        HStack(spacing: 12) {
                            Image(systemName: "lock.shield.fill")
                                .font(.system(size: 18))
                                .foregroundStyle(.cyan)
                            Text("Privacy Policy")
                                .font(.outfit(size: 16, weight: .regular))
                        }
                    }
                } header: {
                    Text("Privacy & Data")
                        .font(.outfit(size: 13, weight: .semiBold))
                }
                
                // Save Button
                Section {
                    Button(action: {
                        Task {
                            await viewModel.savePreferences()
                        }
                    }) {
                        HStack {
                            Spacer()
                            if viewModel.isSaving {
                                ProgressView()
                                    .tint(.white)
                            } else {
                                Text("Save Preferences")
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
            .scrollContentBackground(.hidden)
        }
        .navigationTitle("Preferences")
        .navigationBarTitleDisplayMode(.large)
    }
}

// MARK: - Category Preference Button

struct CategoryPreferenceButton: View {
    let category: NewsCategory
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: {
            HapticManager.selection()
            action()
        }) {
            HStack(spacing: 8) {
                Image(systemName: category.icon)
                    .font(.system(size: 16))
                    .foregroundStyle(isSelected ? .white : category.color)
                
                Text(category.displayName)
                    .font(.outfit(size: 14, weight: .semiBold))
                    .foregroundStyle(isSelected ? .white : .primary)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(
                RoundedRectangle(cornerRadius: 10)
                    .fill(isSelected ? category.color : .clear)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(category.color, lineWidth: isSelected ? 0 : 1.5)
                    )
            )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - View Model

@MainActor
class PreferencesViewModel: ObservableObject {
    @Published var selectedCategories: Set<NewsCategory> = []
    @Published var showImages: Bool = true
    @Published var autoPlayVideos: Bool = false
    @Published var maxReadingTime: Int = 0
    @Published var personalizedFeed: Bool = true
    @Published var trackingEnabled: Bool = true
    @Published var isSaving: Bool = false
    
    init() {
        // Load saved preferences
        loadPreferences()
    }
    
    func toggleCategory(_ category: NewsCategory) {
        if selectedCategories.contains(category) {
            selectedCategories.remove(category)
        } else {
            selectedCategories.insert(category)
        }
    }
    
    func savePreferences() async {
        isSaving = true
        
        // Save to UserDefaults
        UserDefaults.standard.set(Array(selectedCategories.map { $0.rawValue }), forKey: "selectedCategories")
        UserDefaults.standard.set(showImages, forKey: "showImages")
        UserDefaults.standard.set(autoPlayVideos, forKey: "autoPlayVideos")
        UserDefaults.standard.set(maxReadingTime, forKey: "maxReadingTime")
        UserDefaults.standard.set(personalizedFeed, forKey: "personalizedFeed")
        UserDefaults.standard.set(trackingEnabled, forKey: "trackingEnabled")
        
        // Simulate API call
        try? await Task.sleep(nanoseconds: 500_000_000)
        
        // TODO: Sync with backend API
        // try await apiService.updateUserPreferences(...)
        
        isSaving = false
        
        HapticManager.notification(type: .success)
    }
    
    private func loadPreferences() {
        // Load from UserDefaults
        if let categoriesData = UserDefaults.standard.array(forKey: "selectedCategories") as? [String] {
            selectedCategories = Set(categoriesData.compactMap { NewsCategory(rawValue: $0) })
        } else {
            // Default: all categories selected
            selectedCategories = Set(NewsCategory.allCases.filter { $0 != .topStories })
        }
        
        showImages = UserDefaults.standard.bool(forKey: "showImages", default: true)
        autoPlayVideos = UserDefaults.standard.bool(forKey: "autoPlayVideos", default: false)
        maxReadingTime = UserDefaults.standard.integer(forKey: "maxReadingTime")
        personalizedFeed = UserDefaults.standard.bool(forKey: "personalizedFeed", default: true)
        trackingEnabled = UserDefaults.standard.bool(forKey: "trackingEnabled", default: true)
    }
}

// UserDefaults extension for convenience
extension UserDefaults {
    func bool(forKey key: String, default defaultValue: Bool) -> Bool {
        if object(forKey: key) == nil {
            return defaultValue
        }
        return bool(forKey: key)
    }
}

#Preview {
    NavigationStack {
        PreferencesView()
            .environmentObject(AuthService())
    }
}


