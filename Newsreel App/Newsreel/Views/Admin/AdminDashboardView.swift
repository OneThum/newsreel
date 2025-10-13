import SwiftUI

// MARK: - Number Formatting Extension
extension Int {
    var formatted: String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.groupingSeparator = ","
        return formatter.string(from: NSNumber(value: self)) ?? "\(self)"
    }
}

extension Double {
    var formatted: String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.groupingSeparator = ","
        formatter.maximumFractionDigits = 0
        return formatter.string(from: NSNumber(value: self)) ?? "\(self)"
    }
}

/// Admin-only dashboard showing Azure backend health and stats
/// Only visible to david@mclauchlan.com
struct AdminDashboardView: View {
    @EnvironmentObject private var authService: AuthService
    @EnvironmentObject private var apiService: APIService
    @StateObject private var viewModel = AdminDashboardViewModel()
    
    var body: some View {
        NavigationStack {
            ZStack {
                AppBackground()
                
                ScrollView {
                    VStack(spacing: 20) {
                        if viewModel.isLoading && viewModel.metrics == nil {
                            ProgressView()
                                .controlSize(.large)
                                .padding(.top, 100)
                        } else if let metrics = viewModel.metrics {
                            // Header
                            headerSection
                            
                            // System Health
                            systemHealthSection(metrics: metrics)
                            
                            // Database Stats
                            databaseStatsSection(metrics: metrics)
                            
                            // RSS Ingestion
                            rssIngestionSection(metrics: metrics)
                            
                            // Story Clustering
                            storyClusteringSection(metrics: metrics)
                            
                            // AI Summarization
                            summarizationSection(metrics: metrics)
                            
                            // Feed Quality
                            feedQualitySection(metrics: metrics)
                            
                            // Azure Resources
                            azureResourcesSection(metrics: metrics)
                            
                            // Actions
                            adminActionsSection
                        } else if let error = viewModel.error {
                            errorView(error: error)
                        }
                    }
                    .padding()
                }
                .refreshable {
                    await viewModel.refresh(apiService: apiService)
                }
            }
            .navigationTitle("Admin Dashboard")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { Task { await viewModel.refresh(apiService: apiService) } }) {
                        Image(systemName: "arrow.clockwise")
                            .foregroundStyle(.blue)
                    }
                    .disabled(viewModel.isLoading)
                }
            }
        }
        .task {
            await viewModel.loadMetrics(apiService: apiService)
            viewModel.startAutoRefresh(apiService: apiService)
        }
        .onDisappear {
            viewModel.stopAutoRefresh()
        }
    }
    
    // MARK: - Header
    
    private var headerSection: some View {
        VStack(spacing: 8) {
            Image(systemName: "chart.xyaxis.line")
                .font(.system(size: 50))
                .foregroundStyle(.blue.gradient)
            
            Text("Newsreel Backend")
                .font(.outfit(size: 24, weight: .bold))
            
            if let lastUpdated = viewModel.lastUpdated {
                HStack(spacing: 4) {
                    Text("Last Updated: \(lastUpdated.formatted(date: .omitted, time: .shortened))")
                        .font(.outfit(size: 14, weight: .regular))
                        .foregroundStyle(.secondary)
                    
                    Text("• Auto-refreshing")
                        .font(.outfit(size: 12, weight: .regular))
                        .foregroundStyle(.green)
                }
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 20)
    }
    
    // MARK: - System Health
    
    private func systemHealthSection(metrics: AdminMetrics) -> some View {
        DashboardCard(
            title: "System Health",
            icon: "heart.fill",
            color: metrics.systemHealth.overallStatus == "healthy" ? .green : .orange
        ) {
            VStack(spacing: 12) {
                StatusRow(
                    label: "Overall Status",
                    value: metrics.systemHealth.overallStatus.capitalized,
                    status: metrics.systemHealth.overallStatus == "healthy" ? .healthy : .warning
                )
                
                StatusRow(
                    label: "API Health",
                    value: metrics.systemHealth.apiHealth,
                    status: metrics.systemHealth.apiHealth == "healthy" ? .healthy : .error
                )
                
                StatusRow(
                    label: "Functions Health",
                    value: metrics.systemHealth.functionsHealth,
                    status: metrics.systemHealth.functionsHealth == "healthy" ? .healthy : .error
                )
                
                StatusRow(
                    label: "Database Health",
                    value: metrics.systemHealth.databaseHealth,
                    status: metrics.systemHealth.databaseHealth == "healthy" ? .healthy : .error
                )
            }
        }
    }
    
    // MARK: - Database Stats
    
    private func databaseStatsSection(metrics: AdminMetrics) -> some View {
        DashboardCard(title: "Cosmos DB", icon: "cylinder.fill", color: .purple) {
            VStack(spacing: 12) {
                MetricRow(label: "Total Articles", value: metrics.database.totalArticles.formatted)
                MetricRow(label: "Total Stories", value: metrics.database.totalStories.formatted)
                MetricRow(label: "With Summaries", value: metrics.database.storiesWithSummaries.formatted)
                MetricRow(label: "Unique Sources", value: metrics.database.uniqueSources.formatted)
                
                Divider()
                    .padding(.vertical, 4)
                
                Text("Stories by Status")
                    .font(.outfit(size: 14, weight: .semiBold))
                    .frame(maxWidth: .infinity, alignment: .leading)
                
                ForEach(metrics.database.storiesByStatus, id: \.status) { item in
                    HStack {
                        Text(item.status.capitalized)
                            .font(.outfit(size: 13, weight: .regular))
                        Spacer()
                        Text(item.count.formatted)
                            .font(.outfit(size: 13, weight: .semiBold))
                    }
                }
            }
        }
    }
    
    // MARK: - RSS Ingestion
    
    private func rssIngestionSection(metrics: AdminMetrics) -> some View {
        DashboardCard(title: "RSS Ingestion", icon: "antenna.radiowaves.left.and.right", color: .orange) {
            VStack(spacing: 12) {
                MetricRow(label: "Total Feeds", value: metrics.rssIngestion.totalFeeds.formatted)
                MetricRow(label: "Last Run", value: metrics.rssIngestion.lastRun.formatted(.relative(presentation: .named)))
                MetricRow(label: "Articles/Hour", value: metrics.rssIngestion.articlesPerHour.formatted)
                MetricRow(label: "Success Rate", value: String(format: "%.1f%%", metrics.rssIngestion.successRate * 100))
                
                if !metrics.rssIngestion.topSources.isEmpty {
                    Divider()
                        .padding(.vertical, 4)
                    
                    Text("Top Sources (24h)")
                        .font(.outfit(size: 14, weight: .semiBold))
                        .frame(maxWidth: .infinity, alignment: .leading)
                    
                    ForEach(metrics.rssIngestion.topSources.prefix(5), id: \.source) { item in
                        HStack {
                            Text(item.source)
                                .font(.outfit(size: 13, weight: .regular))
                            Spacer()
                            Text(item.count.formatted)
                                .font(.outfit(size: 13, weight: .semiBold))
                        }
                    }
                }
            }
        }
    }
    
    // MARK: - Story Clustering
    
    private func storyClusteringSection(metrics: AdminMetrics) -> some View {
        DashboardCard(title: "Story Clustering", icon: "link.circle.fill", color: .blue) {
            VStack(spacing: 12) {
                MetricRow(label: "Match Rate", value: String(format: "%.1f%%", metrics.clustering.matchRate * 100))
                MetricRow(label: "Avg Sources/Story", value: String(format: "%.1f", metrics.clustering.avgSourcesPerStory))
                MetricRow(label: "Created (24h)", value: metrics.clustering.storiesCreated24h.formatted)
                MetricRow(label: "Updated (24h)", value: metrics.clustering.storiesUpdated24h.formatted)
            }
        }
    }
    
    // MARK: - Summarization
    
    private func summarizationSection(metrics: AdminMetrics) -> some View {
        DashboardCard(title: "AI Summarization", icon: "sparkles", color: .pink) {
            VStack(spacing: 12) {
                MetricRow(label: "Coverage", value: String(format: "%.1f%%", metrics.summarization.coverage * 100))
                MetricRow(label: "Avg Generation Time", value: String(format: "%.1fs", metrics.summarization.avgGenerationTime))
                MetricRow(label: "Generated (24h)", value: metrics.summarization.summariesGenerated24h.formatted)
                MetricRow(label: "Avg Word Count", value: metrics.summarization.avgWordCount.formatted)
                MetricRow(label: "Cost (24h)", value: String(format: "$%.4f", metrics.summarization.cost24h))
            }
        }
    }
    
    // MARK: - Feed Quality
    
    private func feedQualitySection(metrics: AdminMetrics) -> some View {
        DashboardCard(title: "Feed Quality", icon: "star.fill", color: .yellow) {
            VStack(spacing: 12) {
                StatusRow(
                    label: "Quality Rating",
                    value: metrics.feedQuality.rating,
                    status: qualityStatus(metrics.feedQuality.rating)
                )
                
                MetricRow(label: "Source Diversity", value: String(format: "%.1f%%", metrics.feedQuality.sourceDiversity * 100))
                MetricRow(label: "Unique Sources", value: metrics.feedQuality.uniqueSources.formatted)
                MetricRow(label: "Categorization Confidence", value: String(format: "%.1f%%", metrics.feedQuality.categorizationConfidence * 100))
            }
        }
    }
    
    // MARK: - Azure Resources
    
    private func azureResourcesSection(metrics: AdminMetrics) -> some View {
        DashboardCard(title: "Azure Resources", icon: "cloud.fill", color: .cyan) {
            VStack(spacing: 12) {
                MetricRow(label: "Resource Group", value: metrics.azure.resourceGroup)
                MetricRow(label: "Location", value: metrics.azure.location)
                MetricRow(label: "Subscription", value: metrics.azure.subscriptionName)
                
                Divider()
                    .padding(.vertical, 4)
                
                Text("Services")
                    .font(.outfit(size: 14, weight: .semiBold))
                    .frame(maxWidth: .infinity, alignment: .leading)
                
                ServiceRow(name: "Container App", status: metrics.azure.containerAppStatus)
                ServiceRow(name: "Functions", status: metrics.azure.functionsStatus)
                ServiceRow(name: "Cosmos DB", status: metrics.azure.cosmosDbStatus)
            }
        }
    }
    
    // MARK: - Admin Actions
    
    private var adminActionsSection: some View {
        VStack(spacing: 12) {
            Text("Admin Actions")
                .font(.outfit(size: 18, weight: .bold))
                .frame(maxWidth: .infinity, alignment: .leading)
            
            Button(action: { /* TODO: Trigger RSS ingestion */ }) {
                HStack {
                    Image(systemName: "play.circle.fill")
                    Text("Trigger RSS Ingestion")
                    Spacer()
                }
                .padding()
                .background(.ultraThinMaterial)
                .clipShape(RoundedRectangle(cornerRadius: 12))
            }
            .disabled(true) // Enable when endpoint is ready
            
            Button(action: { /* TODO: Clear cache */ }) {
                HStack {
                    Image(systemName: "trash.circle.fill")
                    Text("Clear Cache")
                    Spacer()
                }
                .padding()
                .background(.ultraThinMaterial)
                .clipShape(RoundedRectangle(cornerRadius: 12))
            }
            .disabled(true)
            
            Button(action: { /* TODO: View logs */ }) {
                HStack {
                    Image(systemName: "doc.text.magnifyingglass")
                    Text("View Recent Logs")
                    Spacer()
                }
                .padding()
                .background(.ultraThinMaterial)
                .clipShape(RoundedRectangle(cornerRadius: 12))
            }
            .disabled(true)
        }
        .padding(.top, 20)
    }
    
    // MARK: - Error View
    
    private func errorView(error: Error) -> some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 50))
                .foregroundStyle(.red)
            
            Text("Failed to Load Metrics")
                .font(.outfit(size: 20, weight: .bold))
            
            Text(error.localizedDescription)
                .font(.outfit(size: 14, weight: .regular))
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
            
            Button("Retry") {
                Task { await viewModel.loadMetrics(apiService: apiService) }
            }
            .buttonStyle(.bordered)
        }
        .padding()
    }
    
    // MARK: - Helpers
    
    private func qualityStatus(_ rating: String) -> StatusIndicator {
        switch rating.lowercased() {
        case "excellent": return .healthy
        case "good": return .healthy
        case "fair": return .warning
        default: return .error
        }
    }
}

// MARK: - Supporting Views

struct DashboardCard<Content: View>: View {
    let title: String
    let icon: String
    let color: Color
    @ViewBuilder let content: Content
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .foregroundStyle(color)
                Text(title)
                    .font(.outfit(size: 18, weight: .bold))
                Spacer()
            }
            
            content
        }
        .padding()
        .background(.ultraThinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .shadow(color: .black.opacity(0.1), radius: 8, y: 4)
    }
}

struct MetricRow: View {
    let label: String
    let value: String
    
    var body: some View {
        HStack {
            Text(label)
                .font(.outfit(size: 14, weight: .regular))
                .foregroundStyle(.secondary)
            Spacer()
            Text(value)
                .font(.outfit(size: 14, weight: .semiBold))
        }
    }
}

enum StatusIndicator {
    case healthy, warning, error
    
    var color: Color {
        switch self {
        case .healthy: return .green
        case .warning: return .orange
        case .error: return .red
        }
    }
    
    var icon: String {
        switch self {
        case .healthy: return "checkmark.circle.fill"
        case .warning: return "exclamationmark.triangle.fill"
        case .error: return "xmark.circle.fill"
        }
    }
}

struct StatusRow: View {
    let label: String
    let value: String
    let status: StatusIndicator
    
    var body: some View {
        HStack {
            Text(label)
                .font(.outfit(size: 14, weight: .regular))
                .foregroundStyle(.secondary)
            Spacer()
            HStack(spacing: 6) {
                Image(systemName: status.icon)
                    .foregroundStyle(status.color)
                Text(value)
                    .font(.outfit(size: 14, weight: .semiBold))
            }
        }
    }
}

struct ServiceRow: View {
    let name: String
    let status: String
    
    var body: some View {
        HStack {
            Text(name)
                .font(.outfit(size: 13, weight: .regular))
            Spacer()
            Text(status.capitalized)
                .font(.outfit(size: 13, weight: .semiBold))
                .foregroundStyle(status == "running" ? .green : .orange)
        }
    }
}

// MARK: - View Model

@MainActor
class AdminDashboardViewModel: ObservableObject {
    @Published var metrics: AdminMetrics?
    @Published var isLoading = false
    @Published var error: Error?
    @Published var lastUpdated: Date?
    
    private var autoRefreshTask: Task<Void, Never>?
    
    func loadMetrics(apiService: APIService) async {
        // Allow refresh even if already loading
        isLoading = true
        error = nil
        
        do {
            // Call admin API endpoint
            metrics = try await apiService.getAdminMetrics()
            lastUpdated = Date()
            log.log("Admin metrics loaded successfully", category: .api, level: .info)
        } catch {
            self.error = error
            log.logError(error, context: "loadAdminMetrics")
        }
        
        isLoading = false
    }
    
    func refresh(apiService: APIService) async {
        await loadMetrics(apiService: apiService)
    }
    
    func startAutoRefresh(apiService: APIService) {
        stopAutoRefresh()
        
        autoRefreshTask = Task { @MainActor in
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 60_000_000_000) // 60 seconds
                if !Task.isCancelled {
                    await loadMetrics(apiService: apiService)
                }
            }
        }
    }
    
    func stopAutoRefresh() {
        autoRefreshTask?.cancel()
        autoRefreshTask = nil
    }
}

// MARK: - Data Models
// (Defined in Models/AdminModels.swift)

