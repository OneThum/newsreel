//
//  StoryCard.swift
//  Newsreel
//
//  Rich story card component with image, metadata, and interactions
//

import SwiftUI

struct StoryCard: View {
    @EnvironmentObject var authService: AuthService
    let story: Story
    let onTap: () -> Void
    let onSave: () -> Void
    let onLike: () -> Void
    let onShare: () -> Void
    
    @State private var showFullImage = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Story Image (if available)
            if let imageURL = story.imageURL {
                AsyncImage(url: imageURL) { phase in
                    switch phase {
                    case .empty:
                        imageLoadingPlaceholder
                    case .success(let image):
                        image
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                            .frame(height: 200)
                            .clipped()
                    case .failure:
                        imageErrorPlaceholder
                    @unknown default:
                        imageLoadingPlaceholder
                    }
                }
                .frame(height: 200)
                .background(Color.gray.opacity(0.1))
            }
            
            // Story Content
            VStack(alignment: .leading, spacing: 12) {
                // Category Badge, Status, and Metadata
                HStack(spacing: 8) {
                    CategoryBadge(category: story.category, size: .small, style: .subtle)
                    
                    // Status badge (only if not verified or recently updated)
                    StatusBadge(status: story.status, isUpdated: story.isRecentlyUpdated)
                    
                    Spacer()
                    
                    // Time ago
                    Text(story.timeAgo)
                        .font(.outfit(size: 12, weight: .regular))
                        .foregroundStyle(.secondary)
                }
                
                // Title
                Text(story.title)
                    .font(.outfit(size: 20, weight: .bold))
                    .foregroundStyle(.primary)
                    .lineLimit(3)
                
                // Summary (only show if not empty and valid)
                if !story.displaySummary.isEmpty {
                    Text(.init(story.displaySummary))  // Parse markdown
                        .font(.outfit(size: 15, weight: .regular))
                        .foregroundStyle(.secondary)
                        .lineLimit(3)
                }
                
                // Source and Metadata
                HStack(spacing: 12) {
                    // Source logo and name
                    HStack(spacing: 6) {
                        if let logoURL = story.source.logoURL {
                            AsyncImage(url: logoURL) { image in
                                image
                                    .resizable()
                                    .aspectRatio(contentMode: .fit)
                            } placeholder: {
                                Image(systemName: "newspaper")
                                    .foregroundStyle(.secondary)
                            }
                            .frame(width: 16, height: 16)
                            .clipShape(Circle())
                        } else {
                            Image(systemName: "newspaper")
                                .font(.system(size: 12))
                                .foregroundStyle(.secondary)
                        }
                        
                        Text(story.source.displayName)
                            .font(.outfit(size: 13, weight: .medium))
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                    }
                    .fixedSize(horizontal: true, vertical: false)
                    
                    // Separator
                    Text("•")
                        .foregroundStyle(.quaternary)
                    
                    // Reading time
                    HStack(spacing: 4) {
                        Image(systemName: "clock")
                            .font(.system(size: 12))
                        Text(story.formattedReadingTime)
                            .font(.outfit(size: 13, weight: .regular))
                    }
                    .foregroundStyle(.secondary)
                    
                    // Separator
                    Text("•")
                        .foregroundStyle(.quaternary)
                    
                    // Source count
                    HStack(spacing: 4) {
                        Image(systemName: "doc.on.doc")
                            .font(.system(size: 12))
                        Text(story.formattedSourceCount)
                            .font(.outfit(size: 13, weight: .regular))
                    }
                    .foregroundStyle(.secondary)
                    
                    Spacer()
                }
            }
            .padding(16)
        }
        .glassCard(cornerRadius: 16)
        .scaleEffect(showFullImage ? 1.02 : 1.0)
        .animation(.spring(response: 0.3, dampingFraction: 0.7), value: showFullImage)
        .onTapGesture {
            HapticManager.selection()
            onTap()
        }
        .onLongPressGesture(minimumDuration: 0.3) {
            HapticManager.impact(style: .medium)
            showFullImage.toggle()
        }
        .onAppear {
            // Log badge display for monitoring badge accuracy
            if story.status != .verified || story.isRecentlyUpdated {
                let badgeType = story.isRecentlyUpdated ? "UPDATED" : story.status.displayName
                log.log("🏷️ Badge displayed: \(badgeType) for story '\(story.title.prefix(50))...' (sources: \(story.sourceCount))", 
                       category: .ui, level: .debug)
            }
        }
    }
    
    // MARK: - Image Placeholders
    
    private var imageLoadingPlaceholder: some View {
        ZStack {
            Rectangle()
                .fill(.quaternary)
            ProgressView()
                .tint(.primary)
        }
        .frame(height: 200)
    }
    
    private var imageErrorPlaceholder: some View {
        ZStack {
            Rectangle()
                .fill(.quaternary)
            VStack(spacing: 8) {
                Image(systemName: "photo")
                    .font(.system(size: 40))
                    .foregroundStyle(.secondary)
                Text("Image unavailable")
                    .font(.outfit(size: 12, weight: .regular))
                    .foregroundStyle(.secondary)
            }
        }
        .frame(height: 200)
    }
}

// MARK: - Haptic Manager

struct HapticManager {
    static func impact(style: UIImpactFeedbackGenerator.FeedbackStyle) {
        let generator = UIImpactFeedbackGenerator(style: style)
        generator.impactOccurred()
    }
    
    static func selection() {
        let generator = UISelectionFeedbackGenerator()
        generator.selectionChanged()
    }
    
    static func notification(type: UINotificationFeedbackGenerator.FeedbackType) {
        let generator = UINotificationFeedbackGenerator()
        generator.notificationOccurred(type)
    }
}

// MARK: - Preview

#Preview {
    ScrollView {
        VStack(spacing: 20) {
            StoryCard(
                story: Story.mock,
                onTap: { print("Tapped") },
                onSave: { print("Saved") },
                onLike: { print("Liked") },
                onShare: { print("Shared") }
            )
            .padding()
            
            StoryCard(
                story: Story.mockArray[1],
                onTap: { print("Tapped") },
                onSave: { print("Saved") },
                onLike: { print("Liked") },
                onShare: { print("Shared") }
            )
            .padding()
        }
    }
    .environmentObject(AuthService())
    .withAppBackground()
}

