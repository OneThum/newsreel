//
//  StoryDetailView.swift
//  Newsreel
//
//  Full story detail view with content, sources, and interactions
//

import SwiftUI
import SafariServices

struct StoryDetailView: View {
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject var authService: AuthService
    @StateObject private var viewModel: StoryDetailViewModel
    @State private var showAllSources = false
    let showImages: Bool  // Add preference parameter

    init(story: Story, apiService: APIService, showImages: Bool = true) {
        _viewModel = StateObject(wrappedValue: StoryDetailViewModel(story: story, apiService: apiService))
        self.showImages = showImages
        
        // 🔍 DEDUPLICATION DIAGNOSTIC LOGGING
        log.log("🔍 [STORY DETAIL INIT] Opening story: \(story.id)", category: .ui, level: .info)
        log.log("   sourceCount field: \(story.sourceCount)", category: .ui, level: .info)
        log.log("   sources.count: \(story.sources.count)", category: .ui, level: .info)
        
        if story.sources.isEmpty {
            log.log("⚠️ [STORY DETAIL INIT] sources array is EMPTY!", category: .ui, level: .warning)
        } else {
            let sourceNames = story.sources.map { $0.displayName }
            log.log("   sources: \(sourceNames.joined(separator: ", "))", category: .ui, level: .info)
            
            // Check for duplicates
            let uniqueNames = Set(sourceNames)
            if uniqueNames.count != sourceNames.count {
                log.log("⚠️ [STORY DETAIL INIT] DUPLICATES in sources array!", category: .ui, level: .warning)
                log.log("   Unique: \(uniqueNames.count), Total: \(sourceNames.count)", category: .ui, level: .warning)
            }
        }
    }
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Story Image - respect showImages preference
                    if showImages, let imageURL = viewModel.story.imageURL {
                        AsyncImage(url: imageURL) { phase in
                            switch phase {
                            case .success(let image):
                                image
                                    .resizable()
                                    .aspectRatio(contentMode: .fill)
                                    .frame(height: 300)
                                    .clipped()
                            case .empty:
                                Rectangle()
                                    .fill(.quaternary)
                                    .frame(height: 300)
                                    .overlay(ProgressView())
                            case .failure:
                                Rectangle()
                                    .fill(.quaternary)
                                    .frame(height: 300)
                                    .overlay(
                                        Image(systemName: "photo")
                                            .font(.system(size: 40))
                                            .foregroundStyle(.secondary)
                                    )
                            @unknown default:
                                EmptyView()
                            }
                        }
                    }
                    
                    VStack(alignment: .leading, spacing: 16) {
                        // Category and Status Badges
                        HStack(spacing: 8) {
                            CategoryBadge(category: viewModel.story.category, size: .medium, style: .filled)
                            StatusBadge(status: viewModel.story.status, isUpdated: viewModel.story.isRecentlyUpdated)
                        }
                        
                        // Title
                        Text(viewModel.story.title)
                            .font(.outfit(size: 28, weight: .bold))
                            .foregroundStyle(.primary)
                        
                        // Metadata
                        HStack(spacing: 12) {
                            // Source (always show icon)
                            HStack(spacing: 6) {
                                if let logoURL = viewModel.story.source.logoURL {
                                    AsyncImage(url: logoURL) { image in
                                        image.resizable().aspectRatio(contentMode: .fit)
                                    } placeholder: {
                                        Image(systemName: "newspaper")
                                            .foregroundStyle(.secondary)
                                    }
                                    .frame(width: 20, height: 20)
                                    .clipShape(Circle())
                                } else {
                                    // Always show newspaper icon as fallback
                                    Image(systemName: "newspaper")
                                        .font(.system(size: 14))
                                        .foregroundStyle(.secondary)
                                        .frame(width: 20, height: 20)
                                }
                                Text(viewModel.story.source.displayName)
                                    .font(.outfit(size: 14, weight: .semiBold))
                                    .lineLimit(1)
                            }
                            .fixedSize(horizontal: true, vertical: false)
                            
                            Text("•")
                                .foregroundStyle(.quaternary)
                            
                            Text(viewModel.story.timeAgo)
                                .font(.outfit(size: 14, weight: .regular))
                                .foregroundStyle(.secondary)
                            
                            Text("•")
                                .foregroundStyle(.quaternary)
                            
                            Text(viewModel.story.formattedReadingTime)
                                .font(.outfit(size: 14, weight: .regular))
                                .foregroundStyle(.secondary)
                        }
                        
                        // Action Buttons
                        HStack(spacing: 24) {
                            // Like
                            Button(action: {
                                HapticManager.impact(style: .light)
                                viewModel.toggleLike()
                            }) {
                                VStack(spacing: 4) {
                                    Image(systemName: viewModel.story.isLiked ? "heart.fill" : "heart")
                                        .font(.system(size: 24))
                                        .foregroundStyle(viewModel.story.isLiked ? .red : .primary)
                                    Text("Like")
                                        .font(.outfit(size: 11, weight: .medium))
                                        .foregroundStyle(.secondary)
                                }
                            }
                            .disabled(authService.isAnonymous)
                            .opacity(authService.isAnonymous ? 0.4 : 1.0)
                            
                            // Save
                            Button(action: {
                                HapticManager.impact(style: .light)
                                viewModel.toggleSave()
                            }) {
                                VStack(spacing: 4) {
                                    Image(systemName: authService.isAnonymous ? "lock.fill" : (viewModel.story.isSaved ? "bookmark.fill" : "bookmark"))
                                        .font(.system(size: 24))
                                        .foregroundStyle(viewModel.story.isSaved ? .blue : .primary)
                                    Text("Save")
                                        .font(.outfit(size: 11, weight: .medium))
                                        .foregroundStyle(.secondary)
                                }
                            }
                            .disabled(authService.isAnonymous)
                            .opacity(authService.isAnonymous ? 0.4 : 1.0)
                            
                            // Share
                            Button(action: {
                                HapticManager.selection()
                                viewModel.shareStory()
                            }) {
                                VStack(spacing: 4) {
                                    Image(systemName: "square.and.arrow.up")
                                        .font(.system(size: 24))
                                        .foregroundStyle(.primary)
                                    Text("Share")
                                        .font(.outfit(size: 11, weight: .medium))
                                        .foregroundStyle(.secondary)
                                }
                            }
                            
                            Spacer()
                        }
                        .padding(.vertical, 8)
                        
                        Divider()
                        
                        // Summary Section
                        VStack(alignment: .leading, spacing: 12) {
                            HStack(spacing: 8) {
                                Image(systemName: "sparkles")
                                    .font(.system(size: 16))
                                    .foregroundStyle(viewModel.story.category.color)
                                Text("AI Summary")
                                    .font(.outfit(size: 15, weight: .semiBold))
                                    .foregroundStyle(.secondary)
                            }
                            
                            if !viewModel.story.displaySummary.isEmpty {
                                Text(.init(viewModel.story.displaySummary))  // Parse markdown
                                    .font(.outfit(size: 17, weight: .regular))
                                    .foregroundStyle(.primary)
                                    .lineSpacing(6)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                            } else {
                                Text("No summary available.")
                                    .font(.outfit(size: 17, weight: .regular))
                                    .foregroundStyle(.tertiary)
                                    .italic()
                                    .frame(maxWidth: .infinity, alignment: .leading)
                            }
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(16)
                        .background(
                            RoundedRectangle(cornerRadius: 14)
                                .fill(.ultraThinMaterial)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 14)
                                        .stroke(viewModel.story.category.color.opacity(0.2), lineWidth: 1)
                                )
                        )
                        
                        // Read Full Article Button
                        Button(action: {
                            viewModel.selectedSourceURL = viewModel.story.url
                            viewModel.showWebView = true
                        }) {
                            HStack {
                                Image(systemName: "safari")
                                Text("Read Full Article")
                                    .font(.outfit(size: 16, weight: .semiBold))
                                Spacer()
                                Image(systemName: "arrow.right")
                            }
                            .foregroundStyle(.white)
                            .padding(.horizontal, 20)
                        }
                        .primaryGlassButtonStyle()
                        
                        // Multiple Sources Section
                        if !viewModel.story.sources.isEmpty {
                            Divider()
                                .padding(.vertical, 8)
                            
                            VStack(alignment: .leading, spacing: 16) {
                                // Header
                                HStack(alignment: .center, spacing: 8) {
                                    Image(systemName: "doc.on.doc.fill")
                                        .font(.system(size: 20))
                                        .foregroundStyle(viewModel.story.category.color)
                                    
                                    Text("Multiple Perspectives")
                                        .font(.outfit(size: 20, weight: .bold))
                                        .foregroundStyle(.primary)
                                }
                                
                                Text("This story has been covered by \(viewModel.uniqueSourceCount) news sources")
                                    .font(.outfit(size: 14, weight: .regular))
                                    .foregroundStyle(.secondary)
                                    .onAppear {
                                        // 🔍 DEDUPLICATION DIAGNOSTIC LOGGING
                                        log.log("📋 [DEDUPLICATION DEBUG] Story: \(viewModel.story.id)", category: .ui, level: .info)
                                        log.log("   Total source articles from API: \(viewModel.story.sources.count)", category: .ui, level: .info)
                                        log.log("   Unique source count: \(viewModel.uniqueSourceCount)", category: .ui, level: .info)
                                        
                                        // Log all source names
                                        let sourceNames = viewModel.story.sources.map { $0.displayName }
                                        log.log("   Source names: \(sourceNames.joined(separator: ", "))", category: .ui, level: .info)
                                        
                                        // Check for duplicates
                                        let uniqueNames = Set(sourceNames)
                                        if uniqueNames.count != sourceNames.count {
                                            log.log("⚠️ [DEDUPLICATION] DUPLICATES DETECTED!", category: .ui, level: .warning)
                                            log.log("   Unique names: \(uniqueNames.count), Total: \(sourceNames.count)", category: .ui, level: .warning)
                                            
                                            // Log duplicate counts
                                            let counts = Dictionary(grouping: sourceNames, by: { $0 }).mapValues { $0.count }
                                            let duplicates = counts.filter { $0.value > 1 }
                                            for (name, count) in duplicates {
                                                log.log("   '\(name)' appears \(count) times", category: .ui, level: .warning)
                                            }
                                        } else {
                                            log.log("✅ [DEDUPLICATION] All sources unique", category: .ui, level: .info)
                                        }
                                        
                                        // Log first 5 article IDs and URLs for inspection
                                        for (index, source) in viewModel.story.sources.prefix(5).enumerated() {
                                            log.log("   [\(index+1)] \(source.displayName) - ID: \(source.id)", category: .ui, level: .debug)
                                            if let url = source.url {
                                                log.log("       URL: \(url.absoluteString)", category: .ui, level: .debug)
                                            }
                                        }
                                    }
                                
                                // Source Cards
                                VStack(spacing: 12) {
                                    ForEach(viewModel.allSourcesToDisplay) { sourceArticle in
                                        Button(action: {
                                            if let url = sourceArticle.url {
                                                HapticManager.selection()
                                                viewModel.selectedSourceURL = url
                                                viewModel.showWebView = true
                                            }
                                        }) {
                                            HStack(spacing: 14) {
                                                // Source icon in colored circle
                                                ZStack {
                                                    Circle()
                                                        .fill(viewModel.story.category.color.opacity(0.15))
                                                        .frame(width: 42, height: 42)
                                                    
                                                    Image(systemName: "newspaper.fill")
                                                        .font(.system(size: 18))
                                                        .foregroundStyle(viewModel.story.category.color)
                                                }
                                                
                                                VStack(alignment: .leading, spacing: 6) {
                                                    // Source name
                                                    Text(sourceArticle.displayName)
                                                        .font(.outfit(size: 16, weight: .semiBold))
                                                        .foregroundStyle(.primary)
                                                    
                                                    // Source headline (if different from main)
                                                    if sourceArticle.title != viewModel.story.title {
                                                        Text(sourceArticle.title)
                                                            .font(.outfit(size: 13, weight: .regular))
                                                            .foregroundStyle(.secondary)
                                                            .lineLimit(2)
                                                    } else {
                                                        Text("Read this perspective")
                                                            .font(.outfit(size: 13, weight: .regular))
                                                            .foregroundStyle(.tertiary)
                                                    }
                                                }
                                                
                                                Spacer()
                                                
                                                // External link indicator
                                                Image(systemName: "arrow.up.right.circle.fill")
                                                    .font(.system(size: 24))
                                                    .foregroundStyle(.quaternary)
                                                    .symbolRenderingMode(.hierarchical)
                                            }
                                            .padding(16)
                                            .background(
                                                RoundedRectangle(cornerRadius: 14)
                                                    .fill(.ultraThinMaterial)
                                                    .overlay(
                                                        RoundedRectangle(cornerRadius: 14)
                                                            .stroke(.white.opacity(0.1), lineWidth: 1)
                                                    )
                                            )
                                        }
                                        .buttonStyle(.plain)
                                    }
                                }

                                // View All Sources Button
                                if viewModel.story.sourceCount > 3 {
                                    Button(action: {
                                        HapticManager.selection()
                                        showAllSources = true
                                    }) {
                                        HStack {
                                            Image(systemName: "newspaper.fill")
                                            Text("View All \(viewModel.story.sourceCount) Sources")
                                                .font(.outfit(size: 16, weight: .semiBold))
                                            Spacer()
                                            Image(systemName: "arrow.right")
                                        }
                                        .foregroundStyle(viewModel.story.category.color)
                                        .padding(.horizontal, 20)
                                        .padding(.vertical, 14)
                                        .background(
                                            RoundedRectangle(cornerRadius: 14)
                                                .fill(viewModel.story.category.color.opacity(0.1))
                                                .overlay(
                                                    RoundedRectangle(cornerRadius: 14)
                                                        .stroke(viewModel.story.category.color.opacity(0.3), lineWidth: 1)
                                                )
                                        )
                                    }
                                    .padding(.top, 8)
                                }
                            }
                        }
                    }
                    .padding()
                }
            }
            .withAppBackground()
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button(action: { dismiss() }) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 28))
                            .foregroundStyle(.secondary)
                            .symbolRenderingMode(.hierarchical)
                    }
                }
            }
            .sheet(isPresented: $viewModel.showWebView) {
                SafariView(url: viewModel.selectedSourceURL ?? viewModel.story.url)
                    .ignoresSafeArea()
            }
            .sheet(isPresented: $showAllSources) {
                StorySourcesView(
                    storyId: viewModel.story.id,
                    storyTitle: viewModel.story.title,
                    categoryColor: viewModel.story.category.color,
                    apiService: viewModel.apiService
                )
            }
        }
        .task {
            await viewModel.markAsRead()
        }
    }
}

// MARK: - View Model

@MainActor
class StoryDetailViewModel: ObservableObject {
    @Published var story: Story
    @Published var showWebView = false
    @Published var selectedSourceURL: URL?
    @Published var isLoadingSources = false

    let apiService: APIService

    init(story: Story, apiService: APIService) {
        self.story = story
        self.apiService = apiService

        // If story doesn't have sources (e.g., from cache), fetch full details
        if story.sources.isEmpty && story.sourceCount > 0 {
            Task {
                await loadFullStoryDetails()
            }
        }
    }

    private func loadFullStoryDetails() async {
        isLoadingSources = true
        defer { isLoadingSources = false }

        do {
            log.log("📡 Fetching full story details for \(story.id)", category: .api, level: .info)
            let fullStory = try await apiService.getStory(id: story.id)
            self.story = fullStory
            log.log("✅ Loaded full story with \(fullStory.sources.count) sources", category: .api, level: .info)
        } catch {
            log.log("❌ Failed to load full story details: \(error.localizedDescription)", category: .api, level: .error)
        }
    }
    
    /// Computed property for unique source count (including the primary source)
    var uniqueSourceCount: Int {
        // Get all unique source names
        var uniqueSources = Set<String>()
        uniqueSources.insert(story.source.displayName) // Primary source
        story.sources.forEach { uniqueSources.insert($0.displayName) }
        return uniqueSources.count
    }
    
    /// All sources to display in the Multiple Perspectives section (deduplicated)
    var allSourcesToDisplay: [SourceArticle] {
        var displayedSources = story.sources
        
        // Check if primary source is already in the sources array
        let primaryName = story.source.displayName.lowercased()
        let alreadyIncluded = story.sources.contains { $0.displayName.lowercased() == primaryName }
        
        // If primary source isn't in sources array, add it as a SourceArticle
        if !alreadyIncluded {
            let primaryArticle = SourceArticle(
                id: story.source.id,
                source: story.source.name,
                title: story.title,
                articleURL: story.url.absoluteString,
                publishedAt: ISO8601DateFormatter().string(from: story.publishedAt)
            )
            displayedSources.insert(primaryArticle, at: 0)
        }
        
        return displayedSources
    }
    
    func markAsRead() async {
        guard !story.isRead else { return }
        
        do {
            try await apiService.markAsRead(storyId: story.id)
            story.isRead = true
        } catch {
            print("Failed to mark as read: \(error)")
        }
    }
    
    func toggleLike() {
        Task {
            do {
                if story.isLiked {
                    try await apiService.unlikeStory(storyId: story.id)
                    story.isLiked = false
                } else {
                    try await apiService.likeStory(storyId: story.id)
                    story.isLiked = true
                }
            } catch {
                print("Failed to toggle like: \(error)")
            }
        }
    }
    
    func toggleSave() {
        Task {
            do {
                if story.isSaved {
                    try await apiService.unsaveStory(storyId: story.id)
                    story.isSaved = false
                } else {
                    try await apiService.saveStory(storyId: story.id)
                    story.isSaved = true
                }
            } catch {
                print("Failed to toggle save: \(error)")
            }
        }
    }
    
    func shareStory() {
        let activityVC = UIActivityViewController(
            activityItems: [story.title, story.url],
            applicationActivities: nil
        )
        
        if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
           let window = windowScene.windows.first,
           let rootVC = window.rootViewController {
            rootVC.present(activityVC, animated: true)
        }
    }
}

// MARK: - Preview

#Preview {
    let authService = AuthService()
    StoryDetailView(
        story: Story.mock,
        apiService: APIService(authService: authService, useMockData: true)
    )
    .environmentObject(authService)
}

