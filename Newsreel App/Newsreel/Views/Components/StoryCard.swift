//
//  StoryCard.swift
//  Newsreel
//
//  Story card component with metadata and interactions
//

import SwiftUI

struct StoryCard: View {
    @EnvironmentObject var authService: AuthService
    @ObservedObject private var readStateManager = ReadStateManager.shared
    let story: Story
    let onTap: () -> Void
    let onSave: () -> Void
    let onLike: () -> Void
    let onShare: () -> Void
    
    /// Whether this story has been read and not updated since
    private var isRead: Bool {
        readStateManager.isStoryRead(story)
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
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
                
                // Title - dims when read
                Text(story.title)
                    .font(.outfit(size: 20, weight: .bold))
                    .foregroundStyle(isRead ? .secondary : .primary)
                    .lineLimit(3)
                
                // Summary (only show if not empty and valid)
                if !story.displaySummary.isEmpty {
                    Text(.init(story.displaySummary))  // Parse markdown
                        .font(.outfit(size: 15, weight: .regular))
                        .foregroundStyle(isRead ? .tertiary : .secondary)
                        .lineLimit(3)
                }
                
                // Source and Metadata
                HStack(spacing: 12) {
                    // Source logo and name
                    HStack(spacing: 6) {
                        Image(systemName: "newspaper")
                            .font(.system(size: 12))
                            .foregroundStyle(.secondary)
                        
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
        // Subtle opacity reduction for read stories
        .opacity(isRead ? 0.7 : 1.0)
        .animation(.easeInOut(duration: 0.3), value: isRead)
        .onTapGesture {
            HapticManager.selection()
            onTap()
        }
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

#Preview("Story Card") {
    StoryCard(story: Story.mock, onTap: {}, onSave: {}, onLike: {}, onShare: {})
        .padding()
        .environmentObject(AuthService())
}

