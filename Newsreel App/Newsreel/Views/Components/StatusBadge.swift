//
//  StatusBadge.swift
//  Newsreel
//
//  Story status badge component showing verification level
//  Simplified system: NEW (1 source) → DEVELOPING (2) → VERIFIED (3+)
//

import SwiftUI

// MARK: - StoryStatus Extension for UI
extension StoryStatus {
    var color: Color {
        switch self.normalized {
        case .new: return .blue         // Fresh/unverified - blue dot
        case .developing: return .orange // Gaining traction - orange
        case .verified: return .green    // Confirmed - green
        case .topStory: return .purple   // Major story - purple star
        default: return .gray
        }
    }
    
    /// Icon for the status
    var icon: String {
        switch self.normalized {
        case .new: return "circle.fill"
        case .developing: return "circle.fill"
        case .verified: return "checkmark.circle.fill"
        case .topStory: return "star.circle.fill"
        default: return "circle.fill"
        }
    }
}

struct StatusBadge: View {
    let status: StoryStatus
    let isUpdated: Bool
    
    init(status: StoryStatus, isUpdated: Bool = false) {
        self.status = status
        self.isUpdated = isUpdated
    }
    
    /// Use normalized status for display
    private var normalizedStatus: StoryStatus {
        status.normalized
    }
    
    var body: some View {
        // Show all status badges (not just non-verified)
        // Users want to know verification level at a glance
        HStack(spacing: 4) {
            // Status indicator
            if normalizedStatus == .topStory {
                Image(systemName: "star.circle.fill")
                    .font(.system(size: 10))
                    .foregroundStyle(badgeColor)
            } else if normalizedStatus == .verified {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 10))
                    .foregroundStyle(badgeColor)
            } else {
                Circle()
                    .fill(badgeColor)
                    .frame(width: 6, height: 6)
            }
            
            Text(displayText)
                .font(.outfit(size: 11, weight: .bold))
                .foregroundStyle(badgeColor)
                .textCase(.uppercase)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(
            RoundedRectangle(cornerRadius: 6)
                .fill(badgeColor.opacity(0.15))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 6)
                .stroke(badgeColor.opacity(0.3), lineWidth: 1)
        )
    }
    
    private var displayText: String {
        if isUpdated {
            return "UPDATED"
        }
        return normalizedStatus.displayName
    }
    
    private var badgeColor: Color {
        if isUpdated {
            return .blue
        }
        return normalizedStatus.color
    }
}

// MARK: - Preview
#Preview("Status Badges") {
    VStack(spacing: 16) {
        Text("New Simplified Status System")
            .font(.headline)
        
        HStack(spacing: 12) {
            StatusBadge(status: .new)
            Text("1 source")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        
        HStack(spacing: 12) {
            StatusBadge(status: .developing)
            Text("2 sources")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        
        HStack(spacing: 12) {
            StatusBadge(status: .verified)
            Text("3+ sources")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        
        Divider()
        
        Text("Legacy Status Mapping")
            .font(.headline)
        
        HStack(spacing: 12) {
            StatusBadge(status: .monitoring)
            Text("→ maps to NEW")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        
        HStack(spacing: 12) {
            StatusBadge(status: .breaking)
            Text("→ maps to VERIFIED")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        
        HStack(spacing: 12) {
            StatusBadge(status: .verified, isUpdated: true)
            Text("Updated badge")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
    .padding()
}

