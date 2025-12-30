//
//  StorySourcesView.swift
//  Newsreel
//
//  Dedicated view for browsing all source articles for a story
//

import SwiftUI
import SafariServices

struct StorySourcesView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var viewModel: StorySourcesViewModel
    let storyTitle: String
    let categoryColor: Color

    init(storyId: String, storyTitle: String, categoryColor: Color, apiService: APIService) {
        self.storyTitle = storyTitle
        self.categoryColor = categoryColor
        _viewModel = StateObject(wrappedValue: StorySourcesViewModel(storyId: storyId, apiService: apiService))
    }

    var body: some View {
        NavigationStack {
            ZStack {
                AppBackground()

                ScrollView {
                    VStack(alignment: .leading, spacing: 24) {
                        // Header
                        VStack(alignment: .leading, spacing: 12) {
                            Text(storyTitle)
                                .font(.outfit(size: 24, weight: .bold))
                                .foregroundStyle(.primary)
                                .lineLimit(3)

                            if viewModel.isLoading {
                                HStack {
                                    ProgressView()
                                        .scaleEffect(0.8)
                                    Text("Loading sources...")
                                        .font(.outfit(size: 14, weight: .medium))
                                        .foregroundStyle(.secondary)
                                }
                            } else if let error = viewModel.error {
                                HStack(spacing: 8) {
                                    Image(systemName: "exclamationmark.triangle.fill")
                                        .foregroundStyle(.orange)
                                    Text(error)
                                        .font(.outfit(size: 14, weight: .medium))
                                        .foregroundStyle(.secondary)
                                }
                            } else {
                                HStack(spacing: 6) {
                                    Image(systemName: "newspaper.fill")
                                        .foregroundStyle(categoryColor)
                                    Text("\(viewModel.sources.count) source\(viewModel.sources.count == 1 ? "" : "s")")
                                        .font(.outfit(size: 14, weight: .semiBold))
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                        .padding(.horizontal, 20)
                        .padding(.top, 8)

                        // Sources List
                        if !viewModel.sources.isEmpty {
                            VStack(spacing: 12) {
                                ForEach(viewModel.sources) { source in
                                    SourceArticleCard(
                                        source: source,
                                        categoryColor: categoryColor,
                                        onTap: {
                                            if let url = source.url {
                                                viewModel.openSourceArticle(url)
                                            }
                                        }
                                    )
                                }
                            }
                            .padding(.horizontal, 20)
                        } else if !viewModel.isLoading && viewModel.error == nil {
                            // Empty state
                            VStack(spacing: 16) {
                                Image(systemName: "doc.text.magnifyingglass")
                                    .font(.system(size: 48))
                                    .foregroundStyle(.tertiary)

                                Text("No sources available")
                                    .font(.outfit(size: 16, weight: .semiBold))
                                    .foregroundStyle(.secondary)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.top, 60)
                        }
                    }
                    .padding(.bottom, 40)
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button(action: { dismiss() }) {
                        HStack(spacing: 4) {
                            Image(systemName: "chevron.left")
                                .font(.system(size: 14, weight: .semibold))
                            Text("Back")
                                .font(.outfit(size: 17, weight: .medium))
                        }
                        .foregroundStyle(.primary)
                    }
                }

                ToolbarItem(placement: .principal) {
                    Text("Source Articles")
                        .font(.outfit(size: 17, weight: .semiBold))
                }
            }
            .sheet(isPresented: $viewModel.showWebView) {
                if let url = viewModel.selectedURL {
                    SafariView(url: url)
                        .ignoresSafeArea()
                }
            }
        }
        .onAppear {
            viewModel.loadSources()
        }
    }
}

// MARK: - Source Article Card

struct SourceArticleCard: View {
    let source: SourceArticle
    let categoryColor: Color
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 16) {
                // Source header
                HStack(spacing: 12) {
                    // Source icon
                    ZStack {
                        Circle()
                            .fill(categoryColor.opacity(0.15))
                            .frame(width: 48, height: 48)

                        Image(systemName: "newspaper.fill")
                            .font(.system(size: 20))
                            .foregroundStyle(categoryColor)
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        Text(source.displayName)
                            .font(.outfit(size: 16, weight: .semiBold))
                            .foregroundStyle(.primary)

                        if let date = source.date {
                            Text(timeAgo(from: date))
                                .font(.outfit(size: 13, weight: .regular))
                                .foregroundStyle(.secondary)
                        }
                    }

                    Spacer()

                    Image(systemName: "arrow.up.right")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundStyle(categoryColor)
                }

                // Article title
                if !source.title.isEmpty {
                    Text(source.title)
                        .font(.outfit(size: 15, weight: .medium))
                        .foregroundStyle(.primary)
                        .lineLimit(3)
                        .multilineTextAlignment(.leading)
                }

                // Read original link
                HStack(spacing: 6) {
                    Image(systemName: "safari")
                        .font(.system(size: 12))
                    Text("Read original article")
                        .font(.outfit(size: 13, weight: .semiBold))
                }
                .foregroundStyle(categoryColor)
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(.ultraThinMaterial)
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .strokeBorder(categoryColor.opacity(0.2), lineWidth: 1)
                    )
            )
        }
        .buttonStyle(.plain)
    }

    /// Format time ago from Date
    private func timeAgo(from date: Date) -> String {
        let calendar = Calendar.current
        let now = Date()
        let components = calendar.dateComponents([.minute, .hour, .day], from: date, to: now)

        if let day = components.day, day > 0 {
            return day == 1 ? "1 day ago" : "\(day) days ago"
        } else if let hour = components.hour, hour > 0 {
            return hour == 1 ? "1 hour ago" : "\(hour) hours ago"
        } else if let minute = components.minute, minute > 0 {
            return minute == 1 ? "1 minute ago" : "\(minute) minutes ago"
        } else {
            return "Just now"
        }
    }
}

// MARK: - Safari View Wrapper

struct SafariView: UIViewControllerRepresentable {
    let url: URL

    func makeUIViewController(context: Context) -> SFSafariViewController {
        let config = SFSafariViewController.Configuration()
        config.entersReaderIfAvailable = true
        config.barCollapsingEnabled = true

        let safari = SFSafariViewController(url: url, configuration: config)
        return safari
    }

    func updateUIViewController(_ uiViewController: SFSafariViewController, context: Context) {
        // No updates needed
    }
}

// MARK: - View Model

@MainActor
class StorySourcesViewModel: ObservableObject {
    @Published var sources: [SourceArticle] = []
    @Published var isLoading = false
    @Published var error: String?
    @Published var showWebView = false
    @Published var selectedURL: URL?

    private let storyId: String
    private let apiService: APIService

    init(storyId: String, apiService: APIService) {
        self.storyId = storyId
        self.apiService = apiService
    }

    func loadSources() {
        guard !isLoading else { return }

        isLoading = true
        error = nil

        Task {
            do {
                log.log("📰 Fetching sources for story: \(storyId)", category: .api, level: .info)
                let fetchedSources = try await apiService.fetchStorySources(storyId: storyId)

                await MainActor.run {
                    self.sources = fetchedSources
                    self.isLoading = false
                    log.log("✅ Loaded \(fetchedSources.count) sources", category: .api, level: .info)
                }
            } catch {
                await MainActor.run {
                    self.error = "Failed to load sources"
                    self.isLoading = false
                    log.logError(error, context: "Failed to fetch story sources")
                }
            }
        }
    }

    func openSourceArticle(_ url: URL) {
        selectedURL = url
        showWebView = true
        log.log("🔗 Opening source article: \(url.absoluteString)", category: .ui, level: .info)
    }
}

#Preview("Story Sources") {
    let authService = AuthService()
    StorySourcesView(
        storyId: "test_story",
        storyTitle: "Major Development in Technology Sector",
        categoryColor: .purple,
        apiService: APIService(authService: authService, useMockData: false)
    )
}
