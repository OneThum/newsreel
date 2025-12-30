//
//  CategoryBadge.swift
//  Newsreel
//
//  Enhanced category badge with glass effects and animations
//

import SwiftUI

struct CategoryBadge: View {
    let category: NewsCategory
    var size: BadgeSize = .medium
    var style: BadgeStyle = .filled
    @State private var isAnimating = false
    
    var body: some View {
        HStack(spacing: size.iconSpacing) {
            Image(systemName: category.icon)
                .font(.system(size: size.iconSize))
            
            Text(category.displayName)
                .font(.outfit(size: size.textSize, weight: .semiBold))
        }
        .foregroundStyle(
            style == .filled ? .white : category.color
        )
        .padding(.horizontal, size.horizontalPadding)
        .padding(.vertical, size.verticalPadding)
        .background(
            Group {
                if style == .filled {
                    ZStack {
                        Capsule()
                            .fill(category.color.opacity(0.9))
                        
                        // Glass highlight
                        Capsule()
                            .fill(
                                LinearGradient(
                                    colors: [
                                        .white.opacity(0.3),
                                        .clear
                                    ],
                                    startPoint: .top,
                                    endPoint: .bottom
                                )
                            )
                    }
                } else {
                    Capsule()
                        .fill(category.color.opacity(0.15))
                }
            }
        )
        .overlay(
            Capsule()
                .stroke(
                    style == .outline ? category.color.opacity(0.5) : .clear,
                    lineWidth: 1.5
                )
        )
        .shadow(color: style == .filled ? category.color.opacity(0.3) : .clear, radius: 8, y: 4)
        .scaleEffect(isAnimating ? 1.0 : 0.8)
        .opacity(isAnimating ? 1.0 : 0.0)
        .onAppear {
            withAnimation(.spring(response: 0.5, dampingFraction: 0.7)) {
                isAnimating = true
            }
        }
    }
}

// MARK: - Badge Size

enum BadgeSize {
    case small
    case medium
    case large
    
    var iconSize: CGFloat {
        switch self {
        case .small: return 10
        case .medium: return 12
        case .large: return 14
        }
    }
    
    var textSize: CGFloat {
        switch self {
        case .small: return 11
        case .medium: return 12
        case .large: return 14
        }
    }
    
    var iconSpacing: CGFloat {
        switch self {
        case .small: return 3
        case .medium: return 4
        case .large: return 5
        }
    }
    
    var horizontalPadding: CGFloat {
        switch self {
        case .small: return 8
        case .medium: return 10
        case .large: return 12
        }
    }
    
    var verticalPadding: CGFloat {
        switch self {
        case .small: return 4
        case .medium: return 5
        case .large: return 6
        }
    }
}

// MARK: - Badge Style

enum BadgeStyle {
    case filled      // Solid background with white text
    case outlined    // Transparent with colored border
    case subtle      // Light background with colored text
    case outline     // Alias for outlined
}

// MARK: - Preview

#Preview {
    VStack(spacing: 20) {
        HStack(spacing: 12) {
            CategoryBadge(category: .technology, style: .filled)
            CategoryBadge(category: .politics, style: .filled)
            CategoryBadge(category: .business, style: .filled)
        }
        
        HStack(spacing: 12) {
            CategoryBadge(category: .science, style: .subtle)
            CategoryBadge(category: .health, style: .subtle)
            CategoryBadge(category: .sports, style: .subtle)
        }
        
        HStack(spacing: 12) {
            CategoryBadge(category: .environment, size: .large, style: .filled)
            CategoryBadge(category: .world, size: .large, style: .filled)
        }
    }
    .padding()
    .withAppBackground()
}

