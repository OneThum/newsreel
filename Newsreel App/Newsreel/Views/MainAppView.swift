//
//  MainAppView.swift
//  Newsreel
//
//  Main authenticated app view with navigation
//

import SwiftUI

struct MainAppView: View {
    @EnvironmentObject var authService: AuthService
    @EnvironmentObject var apiService: APIService
    @EnvironmentObject var notificationService: NotificationService
    @State private var selectedTab = 0
    @Binding var notificationStoryId: String?
    
    // Admin check
    private var isAdmin: Bool {
        let adminEmails = ["david@mclauchlan.com", "dave@onethum.com"]
        guard let userEmail = authService.currentUser?.email else { return false }
        return adminEmails.contains(userEmail)
    }
    
    var body: some View {
        TabView(selection: $selectedTab) {
            FeedView(notificationStoryId: $notificationStoryId)
                .tabItem {
                    Label("Feed", systemImage: "newspaper.fill")
                }
                .tag(0)
            
            SavedStoriesView()
                .tabItem {
                    Label("Saved", systemImage: "bookmark.fill")
                }
                .tag(1)
            
            ProfileView()
                .tabItem {
                    Label("Profile", systemImage: "person.fill")
                }
                .tag(2)
            
            // Admin-only dashboard
            if isAdmin {
                AdminDashboardView()
                    .tabItem {
                        Label("Admin", systemImage: "chart.xyaxis.line")
                    }
                    .tag(3)
            }
        }
        .tint(.blue)
        .toolbarBackground(.visible, for: .tabBar)
        .toolbarBackground(.ultraThinMaterial, for: .tabBar)
        .onAppear {
            // Configure notification service
            notificationService.configure(with: apiService)
            
            // Request notification permission after login
            Task {
                let granted = await notificationService.requestPermission()
                if granted {
                    // Register device token with backend
                    await notificationService.registerToken(with: apiService)
                }
            }
        }
        .onChange(of: notificationStoryId) { _, storyId in
            if storyId != nil {
                // Switch to feed tab when notification is tapped
                selectedTab = 0
            }
        }
    }
}

// MARK: - Category Filter Bar

struct CategoryFilterBar: View {
    @Binding var selectedCategory: NewsCategory?
    let onCategoryChange: (NewsCategory?) -> Void
    
    private let categories: [NewsCategory?] = [
        nil, // "All" option
        .topStories,
        .world,
        .technology,
        .business,
        .politics,
        .science,
        .health,
        .sports,
        .entertainment,
        .environment
    ]
    
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(categories, id: \.self) { category in
                    CategoryChip(
                        category: category,
                        isSelected: selectedCategory == category,
                        action: {
                            HapticManager.selection()
                            onCategoryChange(category)
                        }
                    )
                }
            }
            .padding(.vertical, 8)
        }
    }
}

struct CategoryChip: View {
    let category: NewsCategory?
    let isSelected: Bool
    let action: () -> Void
    
    private var displayName: String {
        category?.displayName ?? "All"
    }
    
    private var icon: String {
        category?.icon ?? "square.grid.2x2.fill"
    }
    
    private var chipColor: Color {
        category?.color ?? .blue
    }
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 14))
                Text(displayName)
                    .font(.outfit(size: 14, weight: .semiBold))
            }
            .foregroundStyle(isSelected ? .white : .primary)
            .padding(.horizontal, 14)
            .padding(.vertical, 8)
            .background(
                Group {
                    if isSelected {
                        Capsule().fill(chipColor.gradient)
                    } else {
                        Capsule().fill(Color.gray.opacity(0.2))
                    }
                }
            )
            .overlay(
                Capsule()
                    .stroke(isSelected ? Color.clear : Color.gray.opacity(0.3), lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Feed View

struct FeedView: View {
    @Environment(\.scenePhase) var scenePhase
    @EnvironmentObject var authService: AuthService
    @EnvironmentObject var apiService: APIService
    @StateObject private var viewModel: FeedViewModel
    @State private var selectedStory: Story?
    @State private var showingSearch = false
    @State private var showImages: Bool
    @Binding var notificationStoryId: String?
    
    init(notificationStoryId: Binding<String?> = .constant(nil)) {
        _viewModel = StateObject(wrappedValue: FeedViewModel())
        _notificationStoryId = notificationStoryId
        // Initialize showImages from UserDefaults
        let savedValue = UserDefaults.standard.bool(forKey: "showImages")
        let hasValue = UserDefaults.standard.object(forKey: "showImages") != nil
        _showImages = State(initialValue: hasValue ? savedValue : true)
    }
    
    var body: some View {
        NavigationStack {
            feedContent
            .overlay(alignment: .bottomTrailing) {
                scrollToTopButton
            }
            .navigationTitle("Newsreel")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Image("AppIconDisplay")
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(width: 32, height: 32)
                        .clipShape(RoundedRectangle(cornerRadius: 7, style: .continuous))
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        HapticManager.selection()
                        showingSearch = true
                    }) {
                        Image(systemName: "magnifyingglass")
                            .font(.system(size: 18, weight: .medium))
                            .foregroundStyle(.primary)
                    }
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        ForEach(NewsCategory.allCases) { category in
                            Button(action: {
                                viewModel.selectedCategory = category == .topStories ? nil : category
                                Task {
                                    await viewModel.loadStories(apiService: apiService, refresh: true)
                                }
                            }) {
                                Label(category.displayName, systemImage: category.icon)
                            }
                        }
                    } label: {
                        Image(systemName: "line.3.horizontal.decrease.circle")
                            .font(.system(size: 20))
                    }
                }
            }
            .sheet(item: $selectedStory) { story in
                StoryDetailView(story: story, apiService: apiService, showImages: showImages)
                    .environmentObject(authService)
            }
            .sheet(isPresented: $showingSearch) {
                SearchView(apiService: apiService, showImages: showImages)
                    .environmentObject(authService)
            }
        }
        .task {
            if viewModel.stories.isEmpty {
                await viewModel.loadStories(apiService: apiService)
            }
            // REMOVED: Don't start polling here - let .onChange(of: scenePhase) handle it
            // This prevents potential double-polling which was causing heating issues
        }
        .onAppear {
            // Reload images preference from UserDefaults (in case it was changed elsewhere)
            let savedValue = UserDefaults.standard.bool(forKey: "showImages")
            let hasValue = UserDefaults.standard.object(forKey: "showImages") != nil
            showImages = hasValue ? savedValue : true
        }
        .onReceive(NotificationCenter.default.publisher(for: UserDefaults.didChangeNotification)) { _ in
            // Reload images preference when settings are changed
            let savedValue = UserDefaults.standard.bool(forKey: "showImages")
            let hasValue = UserDefaults.standard.object(forKey: "showImages") != nil
            showImages = hasValue ? savedValue : true
        }
        .onDisappear {
            // Stop polling when view disappears
            viewModel.stopPolling()
        }
        .onChange(of: scenePhase) { oldPhase, newPhase in
            // CRITICAL: Stop all timers when app goes to background to prevent battery drain and heat
            switch newPhase {
            case .active:
                // App is active - resume polling
                log.log("🟢 App active - resuming polling", category: .ui, level: .info)
                viewModel.startPolling(apiService: apiService)
            case .inactive, .background:
                // App is inactive or in background - stop all timers to save battery
                log.log("⏸️ App background - stopping polling to save battery", category: .ui, level: .info)
                viewModel.stopPolling()
            @unknown default:
                break
            }
        }
    }
    
    private var scrollToTopButton: some View {
        Group {
            if !viewModel.stories.isEmpty {
                ScrollToTopButton {
                    HapticManager.impact(style: .light)
                    viewModel.shouldScrollToTop = true
                }
                .padding(.trailing, 20)
                .padding(.bottom, 20)
            }
        }
    }
    
    private var feedContent: some View {
        ZStack {
            AppBackground()
            
            VStack(spacing: 0) {
                    // Category Filter Chips (horizontal scrolling)
                    CategoryFilterBar(
                        selectedCategory: $viewModel.selectedCategory,
                        onCategoryChange: { newCategory in
                            Task {
                                await viewModel.changeCategory(to: newCategory, apiService: apiService)
                            }
                        }
                    )
                    .padding(.horizontal)
                    .padding(.top, 8)
                    .padding(.bottom, 0) // Spacing handled by ScrollView padding
                    
                    // New stories indicator (Twitter-style, buttery smooth)
                    if viewModel.newStoriesAvailable {
                        Button(action: {
                            HapticManager.selection()
                            viewModel.loadPendingNewStories()
                        }) {
                            HStack(spacing: 8) {
                                Image(systemName: "arrow.up.circle.fill")
                                    .font(.system(size: 16))
                                if viewModel.pendingNewStoriesCount == 1 {
                                    Text("1 new story")
                                        .font(.outfit(size: 14, weight: .semiBold))
                                } else {
                                    Text("\(viewModel.pendingNewStoriesCount) new stories")
                                        .font(.outfit(size: 14, weight: .semiBold))
                                }
                            }
                            .foregroundStyle(.white)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 10)
                            .background(
                                Capsule()
                                    .fill(.blue.gradient)
                            )
                            .shadow(color: .black.opacity(0.2), radius: 8, y: 4)
                        }
                        .padding(.top, 8)
                        .transition(.move(edge: .top).combined(with: .opacity))
                        .animation(.spring(response: 0.4, dampingFraction: 0.7), value: viewModel.newStoriesAvailable)
                    }
                    
                    ScrollViewReader { proxy in
                        ScrollView {
                            LazyVStack(spacing: 16) {
                                // Anchor point for scroll-to-top (MUST be first!)
                                Color.clear
                                    .frame(height: 0)
                                    .id("top")
                                
                                // Minimal spacer at top (elastic scroll will handle the rest)
                                Color.clear
                                    .frame(height: 0)
                                
                                // REMOVED: lastTimeUpdate trigger was causing full feed re-renders every 5 minutes!
                                // This was a major performance issue causing jerkiness and heating
                                // Time displays update naturally when stories load/refresh
                                
                                if viewModel.isLoading && viewModel.stories.isEmpty {
                                    // Loading skeleton
                                    ForEach(0..<3) { _ in
                                        LoadingSkeleton()
                                    }
                                } else if let error = viewModel.error, viewModel.stories.isEmpty {
                                // Error state
                                ErrorStateView(error: error) {
                                    Task {
                                        await viewModel.loadStories(apiService: apiService)
                                    }
                                }
                            } else if viewModel.stories.isEmpty {
                                // Empty state
                                EmptyFeedView()
                            } else {
                                // Story cards
                                ForEach(viewModel.stories) { story in
                                    StoryCard(
                                        story: story,
                                        onTap: {
                                            selectedStory = story
                                        },
                                        onSave: {
                                            Task {
                                                await viewModel.toggleSave(story: story, apiService: apiService)
                                            }
                                        },
                                        onLike: {
                                            Task {
                                                await viewModel.toggleLike(story: story, apiService: apiService)
                                            }
                                        },
                                        onShare: {
                                            viewModel.shareStory(story)
                                        },
                                        showImages: showImages  // Pass preference
                                    )
                                    .id(story.id) // Important for animation
                                }
                                
                                // Loading indicator for pagination
                                if viewModel.isLoadingMore {
                                    ProgressView()
                                        .padding()
                                }
                            }
                        }
                        .padding(.horizontal)
                        .padding(.bottom)
                        .padding(.top, 0) // No top padding, let elastic scroll handle spacing
                        }
                        .refreshable {
                            await viewModel.refresh(apiService: apiService)
                        }
                        .onChange(of: viewModel.shouldScrollToTop) { _, shouldScroll in
                            if shouldScroll {
                                withAnimation(.easeOut(duration: 0.3)) {
                                    proxy.scrollTo("top", anchor: .top)
                                }
                                // Reset flag after scroll
                                DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) {
                                    viewModel.shouldScrollToTop = false
                                }
                            }
                        }
                        .onChange(of: viewModel.scrollToStoryId) { _, storyId in
                            if let storyId = storyId {
                                // Small delay to ensure story is rendered
                                DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                                    withAnimation(.easeOut(duration: 0.4)) {
                                        proxy.scrollTo(storyId, anchor: .top)
                                    }
                                    // Reset after scroll
                                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                                        viewModel.scrollToStoryId = nil
                                    }
                                }
                            }
                        }
                        .onChange(of: notificationStoryId) { _, storyId in
                            if let storyId = storyId {
                                log.log("📍 Scrolling to story from notification: \(storyId)", 
                                       category: .ui, level: .info)
                                // Scroll to the story
                                DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                                    withAnimation(.easeOut(duration: 0.5)) {
                                        proxy.scrollTo(storyId, anchor: .center)
                                    }
                                    // Reset after scroll
                                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) {
                                        notificationStoryId = nil
                                    }
                                }
                            }
                        }
                    }
            }
        }
    }
}

// MARK: - Feed View Model

@MainActor
class FeedViewModel: ObservableObject {
    @Published var stories: [Story] = []
    @Published var isLoading = false
    @Published var isLoadingMore = false
    @Published var error: Error?
    @Published var selectedCategory: NewsCategory?
    @Published var newStoriesAvailable = false
    @Published var pendingNewStoriesCount = 0
    @Published private(set) var lastTimeUpdate = Date() // Triggers UI refresh for timeAgo updates
    @Published var shouldScrollToTop = false // Triggers scroll animation
    @Published var scrollToStoryId: String? = nil // Scroll to specific story
    
    private var pendingNewStories: [Story] = []
    private var currentPage = 0
    private let pageSize = 20
    private let persistenceService = PersistenceService.shared
    private var hasLoadedCache = false
    private var pollingTimer: Task<Void, Never>?
    private var timeUpdateTimer: Task<Void, Never>?
    private var lastFetchDate: Date?
    
    func loadStories(apiService: APIService, refresh: Bool = false) async {
        // Prevent simultaneous loads - even for refresh
        // This prevents request cancellation when user pulls multiple times
        guard !isLoading else {
            log.log("Load already in progress (isLoading=true), skipping to prevent request cancellation", category: .ui, level: .debug)
            return
        }
        
        // On first launch, load cached stories immediately (offline-first)
        if !hasLoadedCache && !refresh && stories.isEmpty {
            loadFromCache()
            hasLoadedCache = true
        }
        
        log.section("FEED VIEW MODEL - LOAD STORIES")
        log.log("Refresh: \(refresh), Category: \(selectedCategory?.displayName ?? "all"), Page: \(currentPage)", category: .ui, level: .info)
        
        if refresh {
            currentPage = 0
            // Don't clear stories immediately to avoid flash of empty state
            log.log("Refreshing feed, reset to page 0", category: .ui, level: .debug)
        }
        
        // Always set loading state
        isLoading = true
        error = nil
        
        do {
            log.log("📡 Calling API with category: \(selectedCategory?.rawValue ?? "nil")", category: .api, level: .info)
            
            let newStories = try await apiService.getFeed(
                offset: currentPage * pageSize,
                limit: pageSize,
                category: selectedCategory
            )
            
            log.log("📥 Received \(newStories.count) stories from API", category: .api, level: .info)
            
            // Update feed (prepend new stories if refreshing, append if paginating)
            if refresh {
                stories = sortStories(newStories)
                log.log("✅ Refreshed feed with \(stories.count) stories for category: \(selectedCategory?.displayName ?? "all")", category: .ui, level: .info)
            } else {
                // Append for pagination, remove duplicates, then re-sort
                let existingIds = Set(stories.map { $0.id })
                let uniqueNewStories = newStories.filter { !existingIds.contains($0.id) }
                let combined = stories + uniqueNewStories
                stories = sortStories(combined)
            }
            currentPage += 1
            lastFetchDate = Date()
            log.log("✅ Stories loaded successfully: \(newStories.count) new stories, \(stories.count) total", category: .ui, level: .info)
            
            // Log status distribution for badge monitoring and accuracy verification
            let statusCounts = Dictionary(grouping: newStories, by: { $0.status })
                .mapValues { $0.count }
            let statusSummary = statusCounts.map { "\($0.key.displayName): \($0.value)" }.joined(separator: ", ")
            log.log("📊 Status distribution: \(statusSummary)", category: .ui, level: .info)
            
            // Log recently updated stories
            let updatedCount = newStories.filter { $0.isRecentlyUpdated }.count
            if updatedCount > 0 {
                log.log("🔄 Recently updated stories: \(updatedCount)", category: .ui, level: .info)
            }
            
            // Cache stories in background
            Task.detached(priority: .background) { [weak self] in
                guard let self = self else { return }
                try? await self.persistenceService.cacheStories(newStories)
                log.log("📱 Cached \(newStories.count) stories", category: .ui, level: .debug)
            }
        } catch {
            self.error = error
            log.logError(error, context: "FeedViewModel.loadStories")
            log.log("Error type: \(type(of: error))", category: .error, level: .debug)
            
            // If network fails and we have no stories, try loading from cache
            if stories.isEmpty {
                loadFromCache()
            }
        }
        
        isLoading = false
    }
    
    /// Load stories from local cache (Twitter-style persistence)
    private func loadFromCache() {
        do {
            let cachedStories = try persistenceService.getCachedFeed(limit: pageSize)
            if !cachedStories.isEmpty {
                self.stories = sortStories(cachedStories)
                log.log("📱 Loaded \(cachedStories.count) stories from cache", category: .ui, level: .info)
            }
        } catch {
            log.log("❌ Failed to load cached stories: \(error.localizedDescription)", category: .error, level: .error)
        }
    }
    
    /// Sort stories: BREAKING first, then by recency
    private func sortStories(_ stories: [Story]) -> [Story] {
        let sorted = stories.sorted { story1, story2 in
            // BREAKING news always comes first
            if story1.status == .breaking && story2.status != .breaking {
                return true
            }
            if story2.status == .breaking && story1.status != .breaking {
                return false
            }
            
            // Within same status level, sort by recency
            // Use lastUpdated for recently updated stories, otherwise publishedAt
            let date1 = story1.isRecentlyUpdated ? (story1.lastUpdated ?? story1.publishedAt) : story1.publishedAt
            let date2 = story2.isRecentlyUpdated ? (story2.lastUpdated ?? story2.publishedAt) : story2.publishedAt
            
            return date1 > date2
        }
        
        // Log first 3 stories after sorting for debugging
        if sorted.count >= 3 {
            log.log("🔝 Top 3 stories after sort:", category: .ui, level: .debug)
            for (index, story) in sorted.prefix(3).enumerated() {
                log.log("   \(index + 1). [\(story.status.displayName)] \(story.title.prefix(50))...", category: .ui, level: .debug)
            }
        }
        
        return sorted
    }
    
    /// Start polling for new stories (Twitter-style real-time updates)
    func startPolling(apiService: APIService) {
        stopPolling() // Stop any existing polling
        
        // Start story polling (every 5 minutes - optimized for battery and heat)
        pollingTimer = Task {
            while !Task.isCancelled {
                // Wait 5 minutes between polls (reduced frequency for battery/heat optimization)
                try? await Task.sleep(nanoseconds: 300_000_000_000)
                
                guard !Task.isCancelled else { break }
                
                // Check for new stories
                await checkForNewStories(apiService: apiService)
            }
        }
        
        // REMOVED: Time update timer - was causing unnecessary CPU usage
        // Time displays ("2h ago", etc.) update naturally when stories load/refresh
        // No need for a separate timer that triggers UI re-renders
    }
    
    /// Stop polling for new stories
    func stopPolling() {
        pollingTimer?.cancel()
        pollingTimer = nil
        // Time update timer removed for performance
    }
    
    /// Start timer to refresh timeAgo displays every minute
    private func startTimeUpdateTimer() {
        stopTimeUpdateTimer() // Stop any existing timer
        
        timeUpdateTimer = Task {
            while !Task.isCancelled {
                // Wait 5 minutes (same as polling to reduce concurrent operations)
                try? await Task.sleep(nanoseconds: 300_000_000_000)
                
                guard !Task.isCancelled else { break }
                
                // Trigger UI update by changing published property
                lastTimeUpdate = Date()
                log.log("⏰ Updated time displays", category: .ui, level: .debug)
            }
        }
    }
    
    /// Stop time update timer
    private func stopTimeUpdateTimer() {
        timeUpdateTimer?.cancel()
        timeUpdateTimer = nil
    }
    
    /// Check for new stories WITHOUT disrupting the feed (smooth, buttery UX)
    private func checkForNewStories(apiService: APIService) async {
        // Don't check if we're already loading or have an error
        guard !isLoading, error == nil else { return }
        
        do {
            // Fetch latest stories
            let latestStories = try await apiService.getFeed(
                offset: 0,
                limit: 10,
                category: selectedCategory
            )
            
            let now = Date()
            let tenMinutesAgo = now.addingTimeInterval(-10 * 60) // 10 minutes ago
            
            // Find stories we don't have yet (including pending ones)
            let existingIds = Set(stories.map { $0.id })
            let pendingIds = Set(pendingNewStories.map { $0.id })
            
            // CRITICAL FIX: Only consider stories as "new" if they're:
            // 1. Not already in our feed
            // 2. Actually recent (published or updated in the last 10 minutes)
            let newStories = latestStories.filter { story in
                let isNewId = !existingIds.contains(story.id) && !pendingIds.contains(story.id)
                
                // Check if story is actually recent
                let relevantDate = story.isRecentlyUpdated ? (story.lastUpdated ?? story.publishedAt) : story.publishedAt
                let isActuallyRecent = relevantDate > tenMinutesAgo
                
                return isNewId && isActuallyRecent
            }
            
            if !newStories.isEmpty {
                // Log details of new stories for debugging
                let storyAges = newStories.map { story -> String in
                    let relevantDate = story.isRecentlyUpdated ? (story.lastUpdated ?? story.publishedAt) : story.publishedAt
                    let age = now.timeIntervalSince(relevantDate) / 60 // minutes
                    return "\(Int(age))m"
                }.joined(separator: ", ")
                
                log.log("🆕 Found \(newStories.count) truly new stories (ages: \(storyAges))", category: .ui, level: .info)
                
                // Log first new story details
                if let firstNew = newStories.first {
                    let relevantDate = firstNew.isRecentlyUpdated ? (firstNew.lastUpdated ?? firstNew.publishedAt) : firstNew.publishedAt
                    let minutesAgo = Int(now.timeIntervalSince(relevantDate) / 60)
                    log.log("First new story: '\(firstNew.title.prefix(50))...' from \(minutesAgo)m ago", category: .ui, level: .debug)
                }
                
                // Add to pending list (NO DISRUPTION - user must tap to see them)
                pendingNewStories.append(contentsOf: newStories)
                pendingNewStoriesCount = pendingNewStories.count
                newStoriesAvailable = true
                
                // Cache new stories in background
                Task.detached(priority: .background) { [weak self] in
                    guard let self = self else { return }
                    try? await self.persistenceService.cacheStories(newStories)
                }
            }
        } catch {
            // Silently fail - don't disrupt the user experience
            log.log("Polling error: \(error.localizedDescription)", category: .error, level: .debug)
        }
    }
    
    /// Load pending new stories smoothly (called when user taps notification pill)
    func loadPendingNewStories() {
        guard !pendingNewStories.isEmpty else { return }
        
        // Remember the first new story ID to scroll to it
        let firstNewStoryId = pendingNewStories.first?.id
        
        log.log("⬆️ Loading \(pendingNewStories.count) pending stories", category: .ui, level: .info)
        
        // Smoothly merge pending stories
        withAnimation(.spring(response: 0.5, dampingFraction: 0.75)) {
            stories = sortStories(pendingNewStories + stories)
        }
        
        // Clear pending state
        pendingNewStories.removeAll()
        pendingNewStoriesCount = 0
        newStoriesAvailable = false
        
        // Trigger scroll to the new story (wherever it ended up in the sorted feed)
        if let storyId = firstNewStoryId {
            scrollToStoryId = storyId
        }
    }
    
    func refresh(apiService: APIService) async {
        // CRITICAL: Preserve the currently selected category during refresh
        let categoryToRefresh = selectedCategory
        
        log.log("🔄 Refreshing feed with category: \(categoryToRefresh?.displayName ?? "all")", category: .ui, level: .info)
        log.log("   selectedCategory before refresh: \(selectedCategory?.displayName ?? "nil")", category: .ui, level: .debug)
        
        // Reset pagination state explicitly
        currentPage = 0
        
        // Clear pending stories when doing full refresh
        pendingNewStories.removeAll()
        pendingNewStoriesCount = 0
        newStoriesAvailable = false
        
        // CRITICAL: Ensure selectedCategory hasn't been changed
        if selectedCategory != categoryToRefresh {
            log.log("⚠️ Category changed during refresh! Restoring: \(categoryToRefresh?.displayName ?? "all")", category: .ui, level: .warning)
            selectedCategory = categoryToRefresh
        }
        
        // Load stories for current category
        await loadStories(apiService: apiService, refresh: true)
        
        log.log("   selectedCategory after refresh: \(selectedCategory?.displayName ?? "nil")", category: .ui, level: .debug)
    }
    
    func changeCategory(to category: NewsCategory?, apiService: APIService) async {
        // Clear current state
        stories.removeAll()
        pendingNewStories.removeAll()
        pendingNewStoriesCount = 0
        newStoriesAvailable = false
        currentPage = 0
        selectedCategory = category
        
        // Load stories for new category
        await loadStories(apiService: apiService, refresh: true)
        
        log.log("📂 Category changed to: \(category?.displayName ?? "All")", category: .ui, level: .info)
    }
    
    func toggleSave(story: Story, apiService: APIService) async {
        guard let index = stories.firstIndex(where: { $0.id == story.id }) else { return }
        
        do {
            if stories[index].isSaved {
                try await apiService.unsaveStory(storyId: story.id)
                stories[index].isSaved = false
            } else {
                try await apiService.saveStory(storyId: story.id)
                stories[index].isSaved = true
            }
        } catch {
            print("Failed to toggle save: \(error)")
        }
    }
    
    func toggleLike(story: Story, apiService: APIService) async {
        guard let index = stories.firstIndex(where: { $0.id == story.id }) else { return }
        
        do {
            if stories[index].isLiked {
                try await apiService.unlikeStory(storyId: story.id)
                stories[index].isLiked = false
            } else {
                try await apiService.likeStory(storyId: story.id)
                stories[index].isLiked = true
            }
        } catch {
            print("Failed to toggle like: \(error)")
        }
    }
    
    func shareStory(_ story: Story) {
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

// MARK: - Loading Skeleton

struct LoadingSkeleton: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Image placeholder
            Rectangle()
                .fill(.quaternary)
                .frame(height: 200)
                .clipShape(RoundedRectangle(cornerRadius: 12))
            
            // Category badge
            Capsule()
                .fill(.quaternary)
                .frame(width: 100, height: 24)
            
            // Title
            VStack(alignment: .leading, spacing: 8) {
                Rectangle()
                    .fill(.quaternary)
                    .frame(height: 20)
                Rectangle()
                    .fill(.quaternary)
                    .frame(width: 200, height: 20)
            }
            
            // Summary
            VStack(alignment: .leading, spacing: 6) {
                Rectangle()
                    .fill(.quaternary)
                    .frame(height: 16)
                Rectangle()
                    .fill(.quaternary)
                    .frame(height: 16)
                Rectangle()
                    .fill(.quaternary)
                    .frame(width: 150, height: 16)
            }
        }
        .padding(16)
        .glassCard(cornerRadius: 16)
        .redacted(reason: .placeholder)
        .shimmering()
    }
}

// MARK: - Empty Feed View

struct EmptyFeedView: View {
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "newspaper")
                .font(.system(size: 60))
                .foregroundStyle(.secondary)
            
            Text("No Stories Available")
                .font(.outfit(size: 24, weight: .semiBold))
            
            Text("Check back later for new stories")
                .font(.outfit(size: 16, weight: .regular))
                .foregroundStyle(.secondary)
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Error State View

struct ErrorStateView: View {
    let error: Error
    let onRetry: () -> Void
    
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 60))
                .foregroundStyle(.orange)
            
            Text("Something Went Wrong")
                .font(.outfit(size: 24, weight: .semiBold))
            
            Text(error.localizedDescription)
                .font(.outfit(size: 15, weight: .regular))
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
            
            Button(action: onRetry) {
                Text("Try Again")
                    .font(.outfit(size: 16, weight: .semiBold))
                    .foregroundStyle(.white)
                    .padding(.horizontal, 32)
            }
            .primaryGlassButtonStyle()
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Shimmering Effect

extension View {
    func shimmering() -> some View {
        self.modifier(ShimmerModifier())
    }
}

struct ShimmerModifier: ViewModifier {
    @State private var phase: CGFloat = 0
    @Environment(\.colorScheme) var colorScheme
    
    func body(content: Content) -> some View {
        content
            .overlay(
                LinearGradient(
                    gradient: Gradient(colors: [
                        .clear,
                        colorScheme == .dark ? .white.opacity(0.15) : .white.opacity(0.4),
                        .clear
                    ]),
                    startPoint: .leading,
                    endPoint: .trailing
                )
                .rotationEffect(.degrees(30))
                .offset(x: phase)
                .onAppear {
                    withAnimation(
                        .linear(duration: 2)
                        .repeatForever(autoreverses: false)
                    ) {
                        phase = 500
                    }
                }
            )
            .mask(
                RoundedRectangle(cornerRadius: 16)
                    .fill(
                        LinearGradient(
                            colors: [.black, .black.opacity(0.8), .black],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
            )
    }
}

// MARK: - Saved Stories View

struct SavedStoriesView: View {
    @EnvironmentObject var authService: AuthService
    @EnvironmentObject var apiService: APIService
    @StateObject private var viewModel = SavedStoriesViewModel()
    @State private var selectedStory: Story?
    @State private var showImages: Bool
    
    init() {
        _viewModel = StateObject(wrappedValue: SavedStoriesViewModel())
        // Initialize showImages from UserDefaults
        let savedValue = UserDefaults.standard.bool(forKey: "showImages")
        let hasValue = UserDefaults.standard.object(forKey: "showImages") != nil
        _showImages = State(initialValue: hasValue ? savedValue : true)
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                AppBackground()
                
                if authService.isAnonymous {
                    // Sign-in required for anonymous users
                    VStack(spacing: 16) {
                        Image(systemName: "lock.fill")
                            .font(.system(size: 60))
                            .foregroundStyle(.secondary)
                        
                        Text("Sign In Required")
                            .font(.outfit(size: 24, weight: .semiBold))
                        
                        Text("Create an account to save stories and access them later")
                            .font(.outfit(size: 16, weight: .regular))
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 32)
                    }
                    .padding()
                } else {
                    // Authenticated user - show saved stories
                    if viewModel.isLoading && viewModel.savedStories.isEmpty {
                        VStack(spacing: 16) {
                            ProgressView()
                            Text("Loading saved stories...")
                                .font(.outfit(size: 15, weight: .regular))
                                .foregroundStyle(.secondary)
                        }
                    } else if viewModel.savedStories.isEmpty {
                        // Empty state
                        VStack(spacing: 16) {
                            Image(systemName: "bookmark.fill")
                                .font(.system(size: 60))
                                .foregroundStyle(.secondary)
                            
                            Text("No Saved Stories")
                                .font(.outfit(size: 24, weight: .semiBold))
                            
                            Text("Stories you bookmark will appear here")
                                .font(.outfit(size: 16, weight: .regular))
                                .foregroundStyle(.secondary)
                                .multilineTextAlignment(.center)
                                .padding(.horizontal, 32)
                        }
                        .padding()
                    } else {
                        // Saved stories list
                        ScrollView {
                            LazyVStack(spacing: 16) {
                                ForEach(viewModel.savedStories) { story in
                                    StoryCard(
                                        story: story,
                                        onTap: {
                                            selectedStory = story
                                        },
                                        onSave: {
                                            Task {
                                                await viewModel.toggleSave(story: story, apiService: apiService)
                                            }
                                        },
                                        onLike: {
                                            Task {
                                                await viewModel.toggleLike(story: story, apiService: apiService)
                                            }
                                        },
                                        onShare: {
                                            viewModel.shareStory(story)
                                        },
                                        showImages: showImages // Pass preference
                                    )
                                }
                            }
                            .padding()
                        }
                        .refreshable {
                            await viewModel.loadSavedStories(apiService: apiService)
                        }
                    }
                }
            }
            .navigationTitle("Saved")
            .navigationBarTitleDisplayMode(.large)
            .sheet(item: $selectedStory) { story in
                StoryDetailView(story: story, apiService: apiService, showImages: showImages)
                    .environmentObject(authService)
            }
        }
        .task {
            if !authService.isAnonymous && viewModel.savedStories.isEmpty {
                await viewModel.loadSavedStories(apiService: apiService)
            }
        }
    }
}

// MARK: - Saved Stories View Model

@MainActor
class SavedStoriesViewModel: ObservableObject {
    @Published var savedStories: [Story] = []
    @Published var isLoading = false
    @Published var error: Error?
    
    func loadSavedStories(apiService: APIService) async {
        guard !isLoading else { return }
        
        isLoading = true
        error = nil
        
        do {
            savedStories = try await apiService.getSavedStories()
        } catch {
            self.error = error
            print("Failed to load saved stories: \(error)")
        }
        
        isLoading = false
    }
    
    func toggleSave(story: Story, apiService: APIService) async {
        guard let index = savedStories.firstIndex(where: { $0.id == story.id }) else { return }
        
        do {
            // Unsave the story (it's already saved since it's in this list)
            try await apiService.unsaveStory(storyId: story.id)
            savedStories.remove(at: index)
        } catch {
            print("Failed to unsave story: \(error)")
        }
    }
    
    func toggleLike(story: Story, apiService: APIService) async {
        guard let index = savedStories.firstIndex(where: { $0.id == story.id }) else { return }
        
        do {
            if savedStories[index].isLiked {
                try await apiService.unlikeStory(storyId: story.id)
                savedStories[index].isLiked = false
            } else {
                try await apiService.likeStory(storyId: story.id)
                savedStories[index].isLiked = true
            }
        } catch {
            print("Failed to toggle like: \(error)")
        }
    }
    
    func shareStory(_ story: Story) {
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

// MARK: - Profile View (Placeholder)

struct ProfileView: View {
    @EnvironmentObject var authService: AuthService
    @EnvironmentObject var subscriptionService: SubscriptionService
    @State private var showingSignOutAlert = false
    @State private var showingPaywall = false
    @State private var showingClearCacheAlert = false
    @State private var cacheStats: (storyCount: Int, totalSize: String) = (0, "0 KB")
    
    var body: some View {
        NavigationStack {
            ZStack {
                AppBackground()
                
                ScrollView {
                    VStack(spacing: 16) {
                        // Guest User Upgrade Banner
                        if authService.isAnonymous {
                            VStack(spacing: 12) {
                                HStack {
                                    Image(systemName: "person.fill.questionmark")
                                        .font(.system(size: 40))
                                        .foregroundStyle(.secondary)
                                    Spacer()
                                }
                                
                                Text("You're using Newsreel as a Guest")
                                    .font(.outfit(size: 18, weight: .semiBold))
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                
                                Text("Sign in to unlock personalization, saved stories, and more features.")
                                    .font(.outfit(size: 14, weight: .regular))
                                    .foregroundStyle(.secondary)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                
                                Button(action: { showingSignOutAlert = true }) {
                                    Text("Sign In to Upgrade")
                                        .font(.outfit(size: 16, weight: .semiBold))
                                        .foregroundStyle(.white)
                                        .frame(maxWidth: .infinity)
                                        .padding(.vertical, 12)
                                }
                                .primaryGlassButtonStyle()
                                .padding(.top, 4)
                            }
                            .padding(20)
                            .background(
                                RoundedRectangle(cornerRadius: 16)
                                    .fill(.ultraThinMaterial)
                                    .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 4)
                            )
                            .glowing(color: .blue.opacity(0.3), radius: 16, intensity: 0.2)
                        } else {
                            // Authenticated User Info
                            if let user = authService.currentUser {
                                VStack(alignment: .leading, spacing: 8) {
                                    Text(user.displayName ?? "User")
                                        .font(.outfit(size: 24, weight: .bold))
                                    
                                    if let email = user.email {
                                        Text(email)
                                            .font(.outfit(size: 15, weight: .regular))
                                            .foregroundStyle(.secondary)
                                    }
                                }
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(20)
                                .background(
                                    RoundedRectangle(cornerRadius: 16)
                                        .fill(.ultraThinMaterial)
                                        .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 4)
                                )
                            }
                        }
                        
                        // Account section
                        VStack(spacing: 0) {
                            Text("Account")
                                .font(.outfit(size: 13, weight: .semiBold))
                                .foregroundStyle(.secondary)
                                .textCase(.uppercase)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.bottom, 8)
                                .padding(.horizontal, 4)
                            
                            VStack(spacing: 0) {
                                // Subscription
                                Button(action: { 
                                    HapticManager.selection()
                                    showingPaywall = true 
                                }) {
                                    HStack {
                                        Label("Subscription", systemImage: "crown.fill")
                                            .font(.outfit(size: 16, weight: .regular))
                                        Spacer()
                                        Text(subscriptionService.currentTier.displayName)
                                            .font(.outfit(size: 14, weight: .medium))
                                            .foregroundStyle(.secondary)
                                        Image(systemName: "chevron.right")
                                            .font(.system(size: 14))
                                            .foregroundStyle(.quaternary)
                                    }
                                    .contentShape(Rectangle())
                                }
                                .foregroundStyle(.primary)
                                .padding(16)
                                
                                Divider()
                                    .padding(.horizontal, 16)
                                
                                // Preferences
                                NavigationLink(destination: PreferencesView()) {
                                    HStack {
                                        Label("Preferences", systemImage: "slider.horizontal.3")
                                            .font(.outfit(size: 16, weight: .regular))
                                        Spacer()
                                        Image(systemName: "chevron.right")
                                            .font(.system(size: 14))
                                            .foregroundStyle(.quaternary)
                                    }
                                    .contentShape(Rectangle())
                                }
                                .disabled(authService.isAnonymous)
                                .opacity(authService.isAnonymous ? 0.5 : 1.0)
                                .padding(16)
                                
                                Divider()
                                    .padding(.horizontal, 16)
                                
                                // Notifications
                                NavigationLink(destination: NotificationsView()) {
                                    HStack {
                                        Label("Notifications", systemImage: "bell.fill")
                                            .font(.outfit(size: 16, weight: .regular))
                                        Spacer()
                                        Image(systemName: "chevron.right")
                                            .font(.system(size: 14))
                                            .foregroundStyle(.quaternary)
                                    }
                                    .contentShape(Rectangle())
                                }
                                .disabled(authService.isAnonymous)
                                .opacity(authService.isAnonymous ? 0.5 : 1.0)
                                .padding(16)
                            }
                            .background(
                                RoundedRectangle(cornerRadius: 16)
                                    .fill(.ultraThinMaterial)
                                    .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 4)
                            )
                        }
                        
                        // Developer section
                        VStack(spacing: 0) {
                            Text("Developer")
                                .font(.outfit(size: 13, weight: .semiBold))
                                .foregroundStyle(.secondary)
                                .textCase(.uppercase)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.bottom, 8)
                                .padding(.horizontal, 4)
                            
                            VStack(spacing: 0) {
                                // Clear Cache
                                Button(action: { 
                                    HapticManager.selection()
                                    showingClearCacheAlert = true
                                }) {
                                    HStack {
                                        Label("Clear Cache", systemImage: "trash")
                                            .font(.outfit(size: 16, weight: .regular))
                                        Spacer()
                                        Text("\(cacheStats.storyCount) stories")
                                            .font(.outfit(size: 14, weight: .medium))
                                            .foregroundStyle(.secondary)
                                        Image(systemName: "chevron.right")
                                            .font(.system(size: 14))
                                            .foregroundStyle(.quaternary)
                                    }
                                    .contentShape(Rectangle())
                                }
                                .foregroundStyle(.primary)
                                .padding(16)
                            }
                            .background(
                                RoundedRectangle(cornerRadius: 16)
                                    .fill(.ultraThinMaterial)
                                    .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 4)
                            )
                        }
                        
                        // Sign Out section
                        Button(action: { showingSignOutAlert = true }) {
                            HStack {
                                Label("Sign Out", systemImage: "arrow.right.square")
                                    .font(.outfit(size: 16, weight: .regular))
                                Spacer()
                            }
                            .contentShape(Rectangle())
                        }
                        .foregroundStyle(.red)
                        .padding(16)
                        .background(
                            RoundedRectangle(cornerRadius: 16)
                                .fill(.ultraThinMaterial)
                                .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 4)
                        )
                    }
                    .padding()
                }
            }
            .navigationTitle("Profile")
            .navigationBarTitleDisplayMode(.large)
            .alert(authService.isAnonymous ? "Sign In" : "Sign Out", isPresented: $showingSignOutAlert) {
                Button("Cancel", role: .cancel) {}
                if authService.isAnonymous {
                    Button("Sign Out & Return to Login") {
                        try? authService.signOut()
                    }
                } else {
                    Button("Sign Out", role: .destructive) {
                        try? authService.signOut()
                    }
                }
            } message: {
                if authService.isAnonymous {
                    Text("Sign out to access the login screen and create a permanent account.")
                } else {
                    Text("Are you sure you want to sign out?")
                }
            }
            .sheet(isPresented: $showingPaywall) {
                PaywallView()
                    .environmentObject(subscriptionService)
            }
            .alert("Clear Cache?", isPresented: $showingClearCacheAlert) {
                Button("Cancel", role: .cancel) {}
                Button("Clear", role: .destructive) {
                    Task {
                        do {
                            try PersistenceService.shared.clearAll()
                            // Refresh stats
                            cacheStats = try PersistenceService.shared.getCacheStats()
                            HapticManager.notification(type: .success)
                        } catch {
                            log.logError(error, context: "Clear cache failed")
                            HapticManager.notification(type: .error)
                        }
                    }
                }
            } message: {
                Text("This will clear \(cacheStats.storyCount) cached stories (\(cacheStats.totalSize)). Your saved stories will not be affected.")
            }
            .task {
                // Load cache stats
                do {
                    cacheStats = try PersistenceService.shared.getCacheStats()
                } catch {
                    log.logError(error, context: "Failed to get cache stats")
                }
            }
        }
    }
}

// MARK: - Search View

struct SearchView: View {
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject var authService: AuthService
    let apiService: APIService
    let showImages: Bool  // Add preference parameter
    
    @State private var searchText = ""
    @State private var results: [Story] = []
    @State private var isSearching = false
    @State private var selectedStory: Story?
    @State private var searchCategory: NewsCategory?
    @FocusState private var isSearchFieldFocused: Bool
    @State private var localShowImages: Bool
    
    init(apiService: APIService, showImages: Bool) {
        self.apiService = apiService
        self.showImages = showImages
        // Initialize localShowImages from UserDefaults
        let savedValue = UserDefaults.standard.bool(forKey: "showImages")
        let hasValue = UserDefaults.standard.object(forKey: "showImages") != nil
        _localShowImages = State(initialValue: hasValue ? savedValue : true)
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                AppBackground()
                
                VStack(spacing: 0) {
                    // Search bar
                    HStack(spacing: 12) {
                        HStack(spacing: 8) {
                            Image(systemName: "magnifyingglass")
                                .font(.system(size: 16))
                                .foregroundStyle(.secondary)
                            
                            TextField("Search news...", text: $searchText)
                                .font(.outfit(size: 16, weight: .regular))
                                .focused($isSearchFieldFocused)
                                .submitLabel(.search)
                                .onSubmit {
                                    performSearch()
                                }
                        }
                        .padding(12)
                        .background(
                            RoundedRectangle(cornerRadius: 12)
                                .fill(Color.gray.opacity(0.15))
                        )
                        
                        if !searchText.isEmpty {
                            Button("Clear") {
                                searchText = ""
                                results.removeAll()
                            }
                            .font(.outfit(size: 14, weight: .medium))
                            .foregroundStyle(.blue)
                        }
                    }
                    .padding()
                    
                    // Results
                    if isSearching {
                        ProgressView()
                            .padding()
                        Spacer()
                    } else if results.isEmpty && !searchText.isEmpty {
                        VStack(spacing: 16) {
                            Image(systemName: "magnifyingglass")
                                .font(.system(size: 50))
                                .foregroundStyle(.secondary)
                            Text("No results found")
                                .font(.outfit(size: 20, weight: .semiBold))
                            Text("Try different keywords")
                                .font(.outfit(size: 15, weight: .regular))
                                .foregroundStyle(.secondary)
                        }
                        .padding()
                        Spacer()
                    } else if results.isEmpty {
                        VStack(spacing: 16) {
                            Image(systemName: "magnifyingglass")
                                .font(.system(size: 50))
                                .foregroundStyle(.secondary)
                            Text("Search News")
                                .font(.outfit(size: 20, weight: .semiBold))
                            Text("Enter keywords to find stories")
                                .font(.outfit(size: 15, weight: .regular))
                                .foregroundStyle(.secondary)
                        }
                        .padding()
                        Spacer()
                    } else {
                        ScrollView {
                            LazyVStack(spacing: 16) {
                                ForEach(results) { story in
                                    StoryCard(
                                        story: story,
                                        onTap: {
                                            selectedStory = story
                                        },
                                        onSave: {
                                            Task {
                                                try? await apiService.saveStory(storyId: story.id)
                                            }
                                        },
                                        onLike: {
                                            Task {
                                                try? await apiService.likeStory(storyId: story.id)
                                            }
                                        },
                                        onShare: {
                                            // Share logic
                                        },
                                        showImages: localShowImages // Pass preference
                                    )
                                }
                            }
                            .padding()
                        }
                    }
                }
            }
            .navigationTitle("Search")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
            .sheet(item: $selectedStory) { story in
                StoryDetailView(story: story, apiService: apiService, showImages: localShowImages)
                    .environmentObject(authService)
            }
            .onAppear {
                isSearchFieldFocused = true
            }
            .onChange(of: searchText) { oldValue, newValue in
                if newValue.count >= 2 {
                    performSearch()
                }
            }
            .onReceive(NotificationCenter.default.publisher(for: UserDefaults.didChangeNotification)) { _ in
                // Reload images preference when settings are changed
                let savedValue = UserDefaults.standard.bool(forKey: "showImages")
                let hasValue = UserDefaults.standard.object(forKey: "showImages") != nil
                localShowImages = hasValue ? savedValue : true
            }
        }
    }
    
    private func performSearch() {
        guard !searchText.isEmpty else {
            results.removeAll()
            return
        }
        
        Task {
            isSearching = true
            do {
                results = try await apiService.searchStories(query: searchText, category: searchCategory)
            } catch {
                log.logError(error, context: "Search failed")
                results.removeAll()
            }
            isSearching = false
        }
    }
}

// MARK: - Scroll to Top Button

struct ScrollToTopButton: View {
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            ZStack {
                // Liquid Glass background
                Circle()
                    .fill(.ultraThinMaterial)
                    .frame(width: 48, height: 48)
                
                // Subtle blue tint overlay
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [
                                Color.blue.opacity(0.15),
                                Color.blue.opacity(0.05)
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 48, height: 48)
                
                // Arrow icon
                Image(systemName: "arrow.up")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.white, .white.opacity(0.9)],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
            }
            .shadow(color: .black.opacity(0.2), radius: 12, x: 0, y: 6)
            .shadow(color: .blue.opacity(0.1), radius: 20, x: 0, y: 10)
        }
    }
}

// MARK: - Previews

#Preview("Main App") {
    MainAppView(notificationStoryId: .constant(nil))
        .environmentObject(AuthService())
        .environmentObject(APIService(authService: AuthService(), useMockData: true))
        .environmentObject(NotificationService.shared)
}

#Preview("Feed") {
    FeedView()
}

#Preview("Profile") {
    ProfileView()
        .environmentObject(AuthService())
}

