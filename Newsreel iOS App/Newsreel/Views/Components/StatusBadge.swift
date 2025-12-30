//
//  StatusBadge.swift
//  Newsreel
//
//  Story status badge component showing verification level
//

import SwiftUI

// MARK: - StoryStatus Extension for UI
extension StoryStatus {
    var color: Color {
        switch self {
        case .monitoring: return .gray
        case .developing: return .orange
        case .verified: return .green
        case .breaking: return .red
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
    
    var body: some View {
        // Only show badge if not VERIFIED or if recently updated
        if status != .verified || isUpdated {
            HStack(spacing: 4) {
                // Status indicator
                Circle()
                    .fill(badgeColor)
                    .frame(width: 6, height: 6)
                
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
    }
    
    private var displayText: String {
        if isUpdated {
            return "UPDATED"
        }
        return status.displayName
    }
    
    private var badgeColor: Color {
        if isUpdated {
            return .blue
        }
        return status.color
    }
}

// MARK: - Preview
#Preview("Status Badges") {
    VStack(spacing: 16) {
        HStack(spacing: 12) {
            StatusBadge(status: .breaking)
            StatusBadge(status: .developing)
        }
        
        HStack(spacing: 12) {
            StatusBadge(status: .monitoring)
            StatusBadge(status: .verified, isUpdated: true)
        }
        
        HStack(spacing: 12) {
            StatusBadge(status: .verified)
            Text("← Verified doesn't show unless updated")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
    .padding()
}

