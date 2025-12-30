//
//  AppBackground.swift
//  Newsreel
//
//  iOS 26 Liquid Glass background system
//  Showcase implementation of Apple's latest design language
//

import SwiftUI

// Convenient typealias
typealias AppBackground = AppBackgroundView

struct AppBackgroundView: View {
    @Environment(\.colorScheme) var colorScheme

    var body: some View {
        // PERFORMANCE FIX: Replaced 60 FPS TimelineView animation with static gradient
        // This eliminates the primary cause of iPhone heating (60-70% of GPU usage)
        ZStack {
            if colorScheme == .dark {
                // Dark mode static gradient
                LinearGradient(
                    colors: [
                        Color(red: 0.05, green: 0.05, blue: 0.1),
                        Color(red: 0.08, green: 0.08, blue: 0.15)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            } else {
                // Light mode static gradient
                LinearGradient(
                    colors: [
                        Color(red: 0.92, green: 0.94, blue: 0.98),
                        Color(red: 0.82, green: 0.86, blue: 0.94)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            }
        }
        .ignoresSafeArea()
    }
}

// MARK: - Mesh Gradient Background

struct MeshGradientBackground: View {
    let colorScheme: ColorScheme
    let time: TimeInterval
    
    var body: some View {
        if colorScheme == .dark {
            darkGradient
        } else {
            lightGradient
        }
    }
    
    private var darkGradient: some View {
        GeometryReader { geometry in
            ZStack {
                // Rich dark base gradient
                LinearGradient(
                    colors: [
                        Color(red: 0.05, green: 0.05, blue: 0.1),
                        Color(red: 0.08, green: 0.08, blue: 0.15)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
                
                // Deep blue cloud accent (animated)
                Ellipse()
                    .fill(
                        RadialGradient(
                            colors: [
                                Color(red: 0.0, green: 0.3, blue: 0.6).opacity(0.6),
                                Color(red: 0.0, green: 0.25, blue: 0.5).opacity(0.4),
                                Color.clear
                            ],
                            center: .topLeading,
                            startRadius: 0,
                            endRadius: 600
                        )
                    )
                    .frame(width: geometry.size.width * 2, height: geometry.size.height * 0.8)
                    .offset(
                        x: -geometry.size.width * 0.3 + sin(time * 0.1) * 20,
                        y: -geometry.size.height * 0.2 + cos(time * 0.15) * 15
                    )
                
                // Subtle teal accent for depth (animated)
                Ellipse()
                    .fill(
                        RadialGradient(
                            colors: [
                                Color(red: 0.086, green: 0.4, blue: 0.4).opacity(0.4),
                                Color(red: 0.1, green: 0.35, blue: 0.35).opacity(0.25),
                                Color.clear
                            ],
                            center: .bottomTrailing,
                            startRadius: 0,
                            endRadius: 600
                        )
                    )
                    .frame(width: geometry.size.width * 2, height: geometry.size.height * 0.8)
                    .offset(
                        x: geometry.size.width * 0.3 + cos(time * 0.12) * 25,
                        y: geometry.size.height * 0.4 + sin(time * 0.08) * 20
                    )
                
                // Mid-tone blue for layering (animated)
                Ellipse()
                    .fill(
                        RadialGradient(
                            colors: [
                                Color(red: 0.0, green: 0.25, blue: 0.5).opacity(0.5),
                                Color(red: 0.1, green: 0.2, blue: 0.45).opacity(0.3),
                                Color.clear
                            ],
                            center: .center,
                            startRadius: 0,
                            endRadius: 500
                        )
                    )
                    .frame(width: geometry.size.width * 1.5, height: geometry.size.height * 0.7)
                    .offset(
                        x: sin(time * 0.09) * 15,
                        y: geometry.size.height * 0.1 + cos(time * 0.11) * 18
                    )
            }
        }
    }
    
    private var lightGradient: some View {
        GeometryReader { geometry in
            ZStack {
                // Enhanced light base gradient with more vibrant blue tones
                LinearGradient(
                    colors: [
                        Color(red: 0.92, green: 0.94, blue: 0.98), // Light blue-gray with more blue
                        Color(red: 0.88, green: 0.91, blue: 0.96), // Medium blue-gray
                        Color(red: 0.82, green: 0.86, blue: 0.94)  // Deeper blue-gray for contrast
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()

                // More prominent light blue cloud with higher opacity (animated)
                Ellipse()
                    .fill(
                        RadialGradient(
                            colors: [
                                Color(red: 0.6, green: 0.75, blue: 0.92).opacity(0.6), // More saturated blue
                                Color(red: 0.65, green: 0.8, blue: 0.95).opacity(0.4),  // Medium blue
                                Color.clear
                            ],
                            center: .topLeading,
                            startRadius: 0,
                            endRadius: 650
                        )
                    )
                    .frame(width: geometry.size.width * 2.2, height: geometry.size.height * 0.9)
                    .offset(
                        x: -geometry.size.width * 0.4 + sin(time * 0.08) * 30,
                        y: -geometry.size.height * 0.3 + cos(time * 0.12) * 25
                    )

                // Enhanced teal accent with more presence (animated)
                Ellipse()
                    .fill(
                        RadialGradient(
                            colors: [
                                Color(red: 0.65, green: 0.85, blue: 0.85).opacity(0.5), // More vibrant teal
                                Color(red: 0.7, green: 0.88, blue: 0.88).opacity(0.3),   // Medium teal
                                Color.clear
                            ],
                            center: .bottomTrailing,
                            startRadius: 0,
                            endRadius: 650
                        )
                    )
                    .frame(width: geometry.size.width * 2.2, height: geometry.size.height * 0.9)
                    .offset(
                        x: geometry.size.width * 0.4 + cos(time * 0.1) * 28,
                        y: geometry.size.height * 0.3 + sin(time * 0.13) * 22
                    )

                // Enhanced central blue accent for better depth (animated)
                Ellipse()
                    .fill(
                        RadialGradient(
                            colors: [
                                Color(red: 0.7, green: 0.8, blue: 0.92).opacity(0.45), // More saturated blue
                                Color(red: 0.75, green: 0.83, blue: 0.94).opacity(0.25), // Medium blue
                                Color.clear
                            ],
                            center: .center,
                            startRadius: 0,
                            endRadius: 500
                        )
                    )
                    .frame(width: geometry.size.width * 1.8, height: geometry.size.height * 0.8)
                    .offset(
                        x: sin(time * 0.07) * 20,
                        y: geometry.size.height * 0.1 + cos(time * 0.09) * 15
                    )
            }
        }
    }
}

// MARK: - Simplified Background for Sheets

struct SheetBackgroundView: View {
    @Environment(\.colorScheme) var colorScheme
    
    var body: some View {
        ZStack {
            Color.clear  // Transparent to let main gradient show through
            
            // Subtle top accent
            LinearGradient(
                colors: [
                    Color.blue.opacity(colorScheme == .dark ? 0.08 : 0.04),
                    Color.clear
                ],
                startPoint: .top,
                endPoint: .bottom
            )
            .frame(height: 200)
            .frame(maxHeight: .infinity, alignment: .top)
        }
        .ignoresSafeArea()
    }
}

// MARK: - Glass Overlay Effect

struct GlassOverlay: View {
    let time: TimeInterval
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Subtle glass refraction effect
                ForEach(0..<3) { index in
                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [
                                    .white.opacity(0.15),
                                    .white.opacity(0.05),
                                    .clear
                                ],
                                center: .center,
                                startRadius: 0,
                                endRadius: 300
                            )
                        )
                        .frame(width: 400, height: 400)
                        .offset(
                            x: geometry.size.width * CGFloat(index) * 0.3 + sin(time * 0.3 + Double(index)) * 50,
                            y: geometry.size.height * 0.5 + cos(time * 0.25 + Double(index)) * 40
                        )
                        .blur(radius: 40)
                }
            }
        }
    }
}

// MARK: - Noise Texture

struct NoiseTexture: View {
    var body: some View {
        Canvas { context, size in
            // Create subtle noise pattern for glass texture
            let rect = CGRect(origin: .zero, size: size)
            context.fill(Path(rect), with: .color(.white.opacity(0.05)))
            
            // Add random noise dots
            for _ in 0..<200 {
                let x = CGFloat.random(in: 0...size.width)
                let y = CGFloat.random(in: 0...size.height)
                let dotSize = CGFloat.random(in: 0.5...1.5)
                let opacity = Double.random(in: 0.1...0.3)
                
                let path = Path(ellipseIn: CGRect(x: x, y: y, width: dotSize, height: dotSize))
                context.fill(path, with: .color(.white.opacity(opacity)))
            }
        }
    }
}

// MARK: - View Extension

extension View {
    /// Apply the app's gradient background - extends to full screen
    func withAppBackground() -> some View {
        ZStack {
            AppBackgroundView()
                .ignoresSafeArea()
            
            self
        }
    }
    
    /// Apply same beautiful gradient to sheets
    func withSheetBackground() -> some View {
        ZStack {
            AppBackgroundView()
                .ignoresSafeArea()
            
            self
        }
    }
    
    /// Apply advanced glass morphism effect to any view
    func glassCard(cornerRadius: CGFloat = 16) -> some View {
        self
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: cornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius)
                    .stroke(
                        LinearGradient(
                            colors: [
                                .white.opacity(0.3),
                                .white.opacity(0.1),
                                .clear
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        lineWidth: 1
                    )
            )
            .shadow(color: .black.opacity(0.08), radius: 20, y: 10)
            .shadow(color: .black.opacity(0.04), radius: 5, y: 2)
    }
}

