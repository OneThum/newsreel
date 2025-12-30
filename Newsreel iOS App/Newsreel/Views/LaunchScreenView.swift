//
//  LaunchScreenView.swift
//  Newsreel
//
//  iOS 26 Liquid Glass Launch Screen
//  Following Apple's best practices for launch screens
//

import SwiftUI

/// Beautiful launch screen with iOS 26 Liquid Glass aesthetics
/// Shows while the app initializes, then smoothly transitions to main content
struct LaunchScreenView: View {
    @State private var isAnimating = false
    @State private var showContent = false
    @Binding var isPresented: Bool
    
    var body: some View {
        ZStack {
            // Liquid Glass Background
            liquidGlassBackground
            
            // Main Content
            VStack(spacing: 32) {
                Spacer()
                
                // App Icon with Liquid Glass effect
                appIconView
                
                // App Name
                Text("Newsreel")
                    .font(.outfit(size: 48, weight: .extraBold))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.white, .white.opacity(0.9)],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
                    .offset(y: isAnimating ? 0 : 20)
                    .opacity(isAnimating ? 1.0 : 0.0)
                
                // Tagline
                Text("Your World, Curated")
                    .font(.outfit(size: 17, weight: .medium))
                    .foregroundStyle(.white.opacity(0.8))
                    .offset(y: isAnimating ? 0 : 20)
                    .opacity(isAnimating ? 1.0 : 0.0)
                
                Spacer()
                
                // Loading indicator with liquid animation
                liquidLoadingIndicator
                    .offset(y: isAnimating ? 0 : 20)
                    .opacity(isAnimating ? 1.0 : 0.0)
                
                Spacer()
                    .frame(height: 80)
            }
        }
        .onAppear {
            // Smooth entrance animation - immediate since we're the first view
            withAnimation(.spring(response: 0.8, dampingFraction: 0.7)) {
                isAnimating = true
            }
            
            // Auto-dismiss after initialization
            DispatchQueue.main.asyncAfter(deadline: .now() + 2.5) {
                withAnimation(.smooth(duration: 0.5)) {
                    showContent = true
                }
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                    isPresented = false
                }
            }
        }
    }
    
    // MARK: - Components
    
    /// Liquid Glass background with depth and layering
    private var liquidGlassBackground: some View {
        ZStack {
            // Deep background gradient
            LinearGradient(
                colors: [
                    Color(red: 0.05, green: 0.1, blue: 0.2),
                    Color(red: 0.1, green: 0.15, blue: 0.25),
                    Color(red: 0.15, green: 0.2, blue: 0.3)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            // Animated liquid glass orbs
            GeometryReader { geometry in
                ForEach(0..<3) { index in
                    liquidGlassOrb(
                        size: CGFloat(200 + index * 100),
                        offset: CGPoint(
                            x: geometry.size.width * CGFloat(0.3 + Double(index) * 0.2),
                            y: geometry.size.height * CGFloat(0.2 + Double(index) * 0.3)
                        ),
                        delay: Double(index) * 0.3
                    )
                }
            }
            .blur(radius: 60)
            .opacity(isAnimating ? 0.6 : 0.0)
        }
    }
    
    /// Floating liquid glass orb
    private func liquidGlassOrb(size: CGFloat, offset: CGPoint, delay: Double) -> some View {
        Circle()
            .fill(
                RadialGradient(
                    colors: [
                        Color.blue.opacity(0.8),
                        Color.purple.opacity(0.6),
                        Color.blue.opacity(0.4)
                    ],
                    center: .center,
                    startRadius: 0,
                    endRadius: size / 2
                )
            )
            .frame(width: size, height: size)
            .offset(x: offset.x - size / 2, y: offset.y - size / 2)
            .scaleEffect(isAnimating ? 1.0 : 0.5)
            .animation(
                .easeInOut(duration: 3.0)
                .repeatForever(autoreverses: true)
                .delay(delay),
                value: isAnimating
            )
    }
    
    /// App icon with frosted glass container
    private var appIconView: some View {
        ZStack {
            // Glass container
            RoundedRectangle(cornerRadius: 32, style: .continuous)
                .fill(.ultraThinMaterial)
                .frame(width: 140, height: 140)
                .overlay(
                    RoundedRectangle(cornerRadius: 32, style: .continuous)
                        .stroke(
                            LinearGradient(
                                colors: [
                                    .white.opacity(0.5),
                                    .white.opacity(0.1)
                                ],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            lineWidth: 1
                        )
                )
                .shadow(color: .black.opacity(0.3), radius: 30, y: 15)
            
            // App Icon
            Image("AppIconDisplay")
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(width: 100, height: 100)
                .clipShape(RoundedRectangle(cornerRadius: 22.37, style: .continuous))
                .shadow(color: .blue.opacity(0.5), radius: 20, y: 10)
        }
        .scaleEffect(isAnimating ? 1.0 : 0.7)
        .opacity(isAnimating ? 1.0 : 0.0)
        .rotation3DEffect(
            .degrees(isAnimating ? 0 : -15),
            axis: (x: 1, y: 0, z: 0)
        )
    }
    
    /// Liquid-style loading indicator
    private var liquidLoadingIndicator: some View {
        HStack(spacing: 8) {
            ForEach(0..<3) { index in
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [.blue, .purple],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
                    .frame(width: 10, height: 10)
                    .scaleEffect(isAnimating ? 1.0 : 0.5)
                    .animation(
                        .easeInOut(duration: 0.8)
                        .repeatForever(autoreverses: true)
                        .delay(Double(index) * 0.2),
                        value: isAnimating
                    )
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(
            Capsule()
                .fill(.ultraThinMaterial)
                .overlay(
                    Capsule()
                        .stroke(.white.opacity(0.2), lineWidth: 1)
                )
        )
    }
}

// MARK: - Preview

#Preview {
    @Previewable @State var isPresented = true
    
    LaunchScreenView(isPresented: $isPresented)
}

