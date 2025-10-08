//
//  AppBackground.swift
//  Newsreel
//
//  Apple-inspired gradient background system with Liquid Glass effect
//  Adapted from Ticka Currencies
//

import SwiftUI

struct AppBackgroundView: View {
    @Environment(\.colorScheme) var colorScheme
    
    var body: some View {
        // Beautiful cloud gradient with blur for dreamy Liquid Glass effect
        MeshGradientBackground(colorScheme: colorScheme)
            .blur(radius: 30)
            .ignoresSafeArea()
    }
}

// MARK: - Mesh Gradient Background

struct MeshGradientBackground: View {
    let colorScheme: ColorScheme
    
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
                
                // Deep blue cloud accent
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
                    .offset(x: -geometry.size.width * 0.3, y: -geometry.size.height * 0.2)
                
                // Subtle teal accent for depth
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
                    .offset(x: geometry.size.width * 0.3, y: geometry.size.height * 0.4)
                
                // Mid-tone blue for layering
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
                    .offset(y: geometry.size.height * 0.1)
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

                // More prominent light blue cloud with higher opacity
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
                    .offset(x: -geometry.size.width * 0.4, y: -geometry.size.height * 0.3)

                // Enhanced teal accent with more presence
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
                    .offset(x: geometry.size.width * 0.4, y: geometry.size.height * 0.3)

                // Enhanced central blue accent for better depth
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
                    .offset(y: geometry.size.height * 0.1)
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
}

