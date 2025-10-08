//
//  ContentView.swift
//  Newsreel
//
//  Created by David McLauchlan on 10/8/25.
//
//  iOS 18+ with latest SwiftUI best practices
//

import SwiftUI

struct ContentView: View {
    @State private var selectedCard = 0
    @Environment(\.accessibilityReduceMotion) var reduceMotion
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    // Hero section
                    VStack(spacing: 16) {
                        Image(systemName: "newspaper.fill")
                            .font(.system(size: 60))
                            .foregroundStyle(.blue)
                            .symbolEffect(.bounce, value: selectedCard)
                        
                        Text("Welcome to Newsreel")
                            .font(.displayLarge)  // Outfit Bold 34pt
                        
                        Text("AI-curated news from multiple sources")
                            .font(.bodyRegular)  // Outfit Regular 15pt
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding(.top, 40)
                    .padding(.horizontal)
                    
                    // iOS 18: Modern feature cards with scroll transitions
                    VStack(spacing: 20) {
                        featureCard(
                            icon: "sparkles",
                            title: "AI Summarization",
                            description: "Facts-based summaries from multiple trusted sources"
                        )
                        
                        featureCard(
                            icon: "arrow.triangle.2.circlepath",
                            title: "Flip Cards",
                            description: "See full source attribution with beautiful animations"
                        )
                        
                        featureCard(
                            icon: "bolt.fill",
                            title: "Breaking News",
                            description: "Real-time detection with 3-source verification"
                        )
                    }
                    .padding(.horizontal)
                    
                    // iOS 18 showcase
                    VStack(spacing: 8) {
                        Text("Built for iOS 18")
                            .font(.captionEmphasized)
                            .foregroundStyle(.secondary)
                        
                        HStack(spacing: 16) {
                            featureBadge("Liquid Glass")
                            featureBadge("Materials")
                            featureBadge("Scroll FX")
                        }
                    }
                    .padding(.top, 20)
                    .padding(.bottom, 40)
                }
            }
            .scrollTargetBehavior(.paging)
            .navigationTitle("Newsreel")
        }
        .withAppBackground()  // Apply beautiful Liquid Glass gradient
    }
    
    private func featureCard(icon: String, title: String, description: String) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundStyle(.blue)
                
                Text(title)
                    .font(.titleLarge)  // Outfit SemiBold 20pt
            }
            
            Text(description)
                .font(.bodyRegular)  // Outfit Regular 15pt
                .foregroundStyle(.secondary)
                .lineSpacing(4)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(.ultraThinMaterial)  // iOS 18: Enhanced translucency
        .backgroundStyle(.blue.opacity(0.05))  // Subtle tint
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        .shadow(color: .black.opacity(0.1), radius: 20, x: 0, y: 10)
        // iOS 18: Scroll transition effects
        .scrollTransition { content, phase in
            content
                .opacity(phase.isIdentity ? 1 : 0.7)
                .scaleEffect(phase.isIdentity ? 1 : 0.95)
                .blur(radius: phase.isIdentity ? 0 : 2)
        }
    }
    
    private func featureBadge(_ text: String) -> some View {
        Text(text)
            .font(.labelSmall)
            .foregroundStyle(.blue)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(.blue.opacity(0.1))
            .clipShape(Capsule())
    }
}

#Preview {
    ContentView()
        .preferredColorScheme(.light)
}

#Preview("Dark Mode") {
    ContentView()
        .preferredColorScheme(.dark)
}

#Preview {
    ContentView()
        .preferredColorScheme(.light)
}

#Preview("Dark Mode") {
    ContentView()
        .preferredColorScheme(.dark)
}
