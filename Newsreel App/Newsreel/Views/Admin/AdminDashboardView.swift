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
    @Environment(\.scenePhase) var scenePhase
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
                            
                            // System Health (Overall)
                            systemHealthSection(metrics: metrics)
                            
                            // Component Status (Detailed)
                            componentStatusSection(metrics: metrics)
                            
                            // Database Stats
                            databaseStatsSection(metrics: metrics)
                            
                            // RSS Ingestion
                            rssIngestionSection(metrics: metrics)
                            
                            // Story Clustering
                            storyClusteringSection(metrics: metrics)
                            
                            // AI Summarization
                            summarizationSection(metrics: metrics)
                            
                            // Batch Processing
                            batchProcessingSection(metrics: metrics)
                            
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
        .onChange(of: scenePhase) { oldPhase, newPhase in
            // Stop auto-refresh when app goes to background to save battery
            switch newPhase {
            case .active:
                viewModel.startAutoRefresh(apiService: apiService)
            case .inactive, .background:
                viewModel.stopAutoRefresh()
            @unknown default:
                break
            }
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
    
    // MARK: - Component Status (Detailed)
    
    private func componentStatusSection(metrics: AdminMetrics) -> some View {
        DashboardCard(
            title: "Component Health",
            icon: "checkmark.seal.fill",
            color: overallComponentColor(metrics: metrics)
        ) {
            VStack(spacing: 12) {
                // RSS Ingestion
                if let rssHealth = metrics.systemHealth.rssIngestion {
                    ComponentStatusRow(
                        label: "RSS Ingestion",
                        icon: "antenna.radiowaves.left.and.right",
                        health: rssHealth
                    )
                }
                
                // Story Clustering
                if let clusteringHealth = metrics.systemHealth.storyClustering {
                    ComponentStatusRow(
                        label: "Story Clustering",
                        icon: "link.circle.fill",
                        health: clusteringHealth
                    )
                }
                
                // Summarization Change Feed
                if let changefeedHealth = metrics.systemHealth.summarizationChangefeed {
                    ComponentStatusRow(
                        label: "AI Summarization (Live)",
                        icon: "sparkles",
                        health: changefeedHealth
                    )
                }
                
                // Summarization Backfill
                if let backfillHealth = metrics.systemHealth.summarizationBackfill {
                    ComponentStatusRow(
                        label: "AI Summarization (Backfill)",
                        icon: "arrow.circlepath",
                        health: backfillHealth
                    )
                }
                
                // Breaking News Monitor
                if let monitorHealth = metrics.systemHealth.breakingNewsMonitor {
                    ComponentStatusRow(
                        label: "Breaking News Monitor",
                        icon: "bell.badge.fill",
                        health: monitorHealth
                    )
                }
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
        DashboardCard(title: "Story Clustering", icon: "link.circle.fill", color: clusteringHealthColor(metrics.clustering.clusteringHealth)) {
            VStack(spacing: 12) {
                // Pipeline Health Status
                HStack {
                    Text("Pipeline Status")
                        .font(.outfit(size: 13, weight: .medium))
                        .foregroundColor(.secondary)
                    Spacer()
                    HStack(spacing: 4) {
                        Circle()
                            .fill(clusteringHealthColor(metrics.clustering.clusteringHealth))
                            .frame(width: 8, height: 8)
                        Text(metrics.clustering.clusteringHealth.capitalized)
                            .font(.outfit(size: 13, weight: .semiBold))
                            .foregroundColor(clusteringHealthColor(metrics.clustering.clusteringHealth))
                    }
                }
                
                Divider()
                
                // Article Processing Stats
                MetricRow(label: "Unprocessed Articles", value: metrics.clustering.unprocessedArticles.formatted)
                MetricRow(label: "Processed Articles", value: metrics.clustering.processedArticles.formatted)
                MetricRow(label: "Processing Rate", value: "\(metrics.clustering.processingRatePerHour)/hour")
                
                if metrics.clustering.oldestUnprocessedAgeMinutes > 0 {
                    MetricRow(label: "Oldest Backlog Age", value: "\(metrics.clustering.oldestUnprocessedAgeMinutes) min")
                }
                
                Divider()
                
                // Clustering Quality Stats
                MetricRow(label: "Match Rate", value: String(format: "%.1f%%", metrics.clustering.matchRate * 100))
                MetricRow(label: "Avg Sources/Story", value: String(format: "%.1f", metrics.clustering.avgSourcesPerStory))
                MetricRow(label: "Created (24h)", value: metrics.clustering.storiesCreated24h.formatted)
                MetricRow(label: "Updated (24h)", value: metrics.clustering.storiesUpdated24h.formatted)
            }
        }
    }
    
    private func clusteringHealthColor(_ health: String) -> Color {
        switch health.lowercased() {
        case "healthy": return .green
        case "degraded": return .orange
        case "stalled": return .red
        case "error": return .red
        default: return .gray
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
    
    // MARK: - Batch Processing
    
    private func batchProcessingSection(metrics: AdminMetrics) -> some View {
        DashboardCard(title: "Batch Processing", icon: "square.stack.3d.up.fill", color: .purple) {
            VStack(spacing: 12) {
                StatusRow(
                    label: "Status",
                    value: metrics.batchProcessing.enabled ? "Enabled" : "Disabled",
                    status: metrics.batchProcessing.enabled ? .healthy : .warning
                )
                
                if metrics.batchProcessing.enabled {
                    MetricRow(label: "Success Rate", value: String(format: "%.1f%%", metrics.batchProcessing.batchSuccessRate * 100))
                    MetricRow(label: "Batches Completed (24h)", value: "\(metrics.batchProcessing.batchesCompleted24h)/\(metrics.batchProcessing.batchesSubmitted24h)")
                    MetricRow(label: "Avg Batch Size", value: metrics.batchProcessing.avgBatchSize.formatted)
                    MetricRow(label: "Stories in Queue", value: metrics.batchProcessing.storiesInQueue.formatted)
                    MetricRow(label: "Batch Cost (24h)", value: String(format: "$%.4f", metrics.batchProcessing.batchCost24h))
                }
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
    
    private func overallComponentColor(metrics: AdminMetrics) -> Color {
        // Check if any component is down
        let components = [
            metrics.systemHealth.rssIngestion,
            metrics.systemHealth.storyClustering,
            metrics.systemHealth.summarizationChangefeed,
            metrics.systemHealth.summarizationBackfill,
            metrics.systemHealth.breakingNewsMonitor
        ]
        
        let hasDown = components.compactMap { $0 }.contains { $0.status == "down" }
        let hasDegraded = components.compactMap { $0 }.contains { $0.status == "degraded" }
        
        if hasDown {
            return .red
        } else if hasDegraded {
            return .orange
        } else {
            return .green
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

struct ComponentStatusRow: View {
    let label: String
    let icon: String
    let health: ComponentHealth
    
    var statusColor: Color {
        switch health.status {
        case "healthy": return .green
        case "degraded": return .orange
        case "down": return .red
        default: return .gray
        }
    }
    
    var statusIcon: String {
        switch health.status {
        case "healthy": return "checkmark.circle.fill"
        case "degraded": return "exclamationmark.triangle.fill"
        case "down": return "xmark.circle.fill"
        default: return "questionmark.circle.fill"
        }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 14))
                    .foregroundStyle(.secondary)
                
                Text(label)
                    .font(.outfit(size: 14, weight: .medium))
                
                Spacer()
                
                HStack(spacing: 4) {
                    Image(systemName: statusIcon)
                        .font(.system(size: 12))
                        .foregroundStyle(statusColor)
                    
                    Text(health.status.capitalized)
                        .font(.outfit(size: 13, weight: .semiBold))
                        .foregroundStyle(statusColor)
                }
            }
            
            // Status message
            Text(health.message)
                .font(.outfit(size: 12, weight: .regular))
                .foregroundStyle(.secondary)
                .lineLimit(2)
        }
        .padding(.vertical, 4)
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
                // Refresh every 5 minutes (was 60 seconds - way too aggressive, causes heat/battery drain)
                try? await Task.sleep(nanoseconds: 300_000_000_000) // 300 seconds = 5 minutes
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

