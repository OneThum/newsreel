//
//  VisualEffects.swift
//  Newsreel
//
//  Advanced visual effects and animations for iOS 26 showcase
//

import SwiftUI

// MARK: - Semantic Colors

extension Color {
    /// App-specific semantic colors that adapt to light/dark mode
    static let cardBackground = Color("CardBackground", bundle: nil)
    static let cardBorder = Color("CardBorder", bundle: nil)
    static let glassHighlight = Color.white.opacity(0.3)
    static let glassShadow = Color.black.opacity(0.1)
}

// MARK: - Advanced Material Effects

struct GlassMorphismModifier: ViewModifier {
    @Environment(\.colorScheme) var colorScheme
    var cornerRadius: CGFloat = 16
    var showBorder: Bool = true
    var shadowIntensity: Double = 1.0
    
    func body(content: Content) -> some View {
        content
            .background(
                ZStack {
                    // Base material
                    RoundedRectangle(cornerRadius: cornerRadius)
                        .fill(.ultraThinMaterial)
                    
                    // Subtle gradient overlay
                    RoundedRectangle(cornerRadius: cornerRadius)
                        .fill(
                            LinearGradient(
                                colors: [
                                    colorScheme == .dark ? .white.opacity(0.03) : .white.opacity(0.2),
                                    .clear
                                ],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                }
            )
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius)
                    .stroke(
                        LinearGradient(
                            colors: [
                                .white.opacity(colorScheme == .dark ? 0.15 : 0.3),
                                .white.opacity(colorScheme == .dark ? 0.05 : 0.1),
                                .clear
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        lineWidth: showBorder ? 1 : 0
                    )
            )
            .shadow(color: .black.opacity(0.06 * shadowIntensity), radius: 16, y: 8)
            .shadow(color: .black.opacity(0.03 * shadowIntensity), radius: 4, y: 2)
    }
}

// MARK: - Hover Effect

struct HoverEffectModifier: ViewModifier {
    @State private var isHovered = false
    var scaleAmount: CGFloat = 1.02
    
    func body(content: Content) -> some View {
        content
            .scaleEffect(isHovered ? scaleAmount : 1.0)
            .animation(.spring(response: 0.3, dampingFraction: 0.7), value: isHovered)
            .onLongPressGesture(minimumDuration: 0.1) {
                // Trigger on press
            } onPressingChanged: { pressing in
                isHovered = pressing
            }
    }
}

// MARK: - Pulse Animation

struct PulseModifier: ViewModifier {
    @State private var isPulsing = false
    var duration: Double = 2.0
    var minScale: CGFloat = 0.95
    var maxScale: CGFloat = 1.05
    
    func body(content: Content) -> some View {
        content
            .scaleEffect(isPulsing ? maxScale : minScale)
            .onAppear {
                withAnimation(
                    .easeInOut(duration: duration)
                    .repeatForever(autoreverses: true)
                ) {
                    isPulsing = true
                }
            }
    }
}

// MARK: - Floating Animation

struct FloatingModifier: ViewModifier {
    @State private var isFloating = false
    var range: CGFloat = 10
    var duration: Double = 3.0
    
    func body(content: Content) -> some View {
        content
            .offset(y: isFloating ? -range : range)
            .onAppear {
                withAnimation(
                    .easeInOut(duration: duration)
                    .repeatForever(autoreverses: true)
                ) {
                    isFloating = true
                }
            }
    }
}

// MARK: - Glow Effect

struct GlowModifier: ViewModifier {
    var color: Color = .blue
    var radius: CGFloat = 20
    var intensity: Double = 0.6
    
    func body(content: Content) -> some View {
        content
            .shadow(color: color.opacity(intensity), radius: radius, y: 0)
            .shadow(color: color.opacity(intensity * 0.5), radius: radius / 2, y: 0)
    }
}

// MARK: - Bounce Animation

struct BounceModifier: ViewModifier {
    @State private var isBouncing = false
    var trigger: Bool
    
    func body(content: Content) -> some View {
        content
            .scaleEffect(isBouncing ? 1.1 : 1.0)
            .onChange(of: trigger) { oldValue, newValue in
                withAnimation(.spring(response: 0.3, dampingFraction: 0.4)) {
                    isBouncing = true
                }
                
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                    withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) {
                        isBouncing = false
                    }
                }
            }
    }
}

// MARK: - Rotate Animation

struct RotateModifier: ViewModifier {
    @State private var rotation: Double = 0
    var duration: Double = 20.0
    
    func body(content: Content) -> some View {
        content
            .rotationEffect(.degrees(rotation))
            .onAppear {
                withAnimation(
                    .linear(duration: duration)
                    .repeatForever(autoreverses: false)
                ) {
                    rotation = 360
                }
            }
    }
}

// MARK: - Parallax Effect

struct ParallaxModifier: ViewModifier {
    @State private var offset: CGFloat = 0
    var magnitude: CGFloat = 20
    
    func body(content: Content) -> some View {
        GeometryReader { geometry in
            content
                .offset(y: offset)
                .onAppear {
                    // Calculate parallax based on position
                    let frame = geometry.frame(in: .global)
                    let screenHeight = geometry.size.height * 2 // Approximate screen height
                    offset = (frame.minY / screenHeight - 0.5) * magnitude
                }
        }
    }
}

// MARK: - View Extensions

extension View {
    /// Apply glass morphism effect with customization
    func glassMorphism(
        cornerRadius: CGFloat = 16,
        showBorder: Bool = true,
        shadowIntensity: Double = 1.0
    ) -> some View {
        self.modifier(GlassMorphismModifier(
            cornerRadius: cornerRadius,
            showBorder: showBorder,
            shadowIntensity: shadowIntensity
        ))
    }
    
    /// Add hover/press effect
    func hoverEffect(scale: CGFloat = 1.02) -> some View {
        self.modifier(HoverEffectModifier(scaleAmount: scale))
    }
    
    /// Add pulsing animation
    func pulsing(duration: Double = 2.0, min: CGFloat = 0.95, max: CGFloat = 1.05) -> some View {
        self.modifier(PulseModifier(duration: duration, minScale: min, maxScale: max))
    }
    
    /// Add floating animation
    func floating(range: CGFloat = 10, duration: Double = 3.0) -> some View {
        self.modifier(FloatingModifier(range: range, duration: duration))
    }
    
    /// Add glow effect
    func glowing(color: Color = .blue, radius: CGFloat = 20, intensity: Double = 0.6) -> some View {
        self.modifier(GlowModifier(color: color, radius: radius, intensity: intensity))
    }
    
    /// Add bounce animation on trigger
    func bouncing(trigger: Bool) -> some View {
        self.modifier(BounceModifier(trigger: trigger))
    }
    
    /// Add rotation animation
    func rotating(duration: Double = 20.0) -> some View {
        self.modifier(RotateModifier(duration: duration))
    }
    
    /// Add parallax scrolling effect
    func parallax(magnitude: CGFloat = 20) -> some View {
        self.modifier(ParallaxModifier(magnitude: magnitude))
    }
}

// MARK: - Advanced Transition Effects

extension AnyTransition {
    /// Glass slide transition
    static var glassSlide: AnyTransition {
        .asymmetric(
            insertion: .move(edge: .trailing).combined(with: .opacity).combined(with: .scale(scale: 0.8)),
            removal: .move(edge: .leading).combined(with: .opacity).combined(with: .scale(scale: 1.2))
        )
    }
    
    /// Liquid expansion
    static var liquidExpand: AnyTransition {
        .scale(scale: 0.8).combined(with: .opacity)
    }
    
    /// Ripple effect
    static var ripple: AnyTransition {
        .scale(scale: 0.5, anchor: .center).combined(with: .opacity)
    }
}

// MARK: - Advanced Shape Styles

struct GlassShapeStyle: ShapeStyle {
    @Environment(\.colorScheme) var colorScheme
    
    func resolve(in environment: EnvironmentValues) -> some ShapeStyle {
        if colorScheme == .dark {
            return AnyShapeStyle(.ultraThinMaterial.opacity(0.9))
        } else {
            return AnyShapeStyle(.ultraThinMaterial)
        }
    }
}

// MARK: - Interactive Particle System (for special moments)

struct ParticleEffect: View {
    let count: Int
    @State private var particles: [Particle] = []
    
    struct Particle: Identifiable {
        let id = UUID()
        var x: CGFloat
        var y: CGFloat
        var size: CGFloat
        var opacity: Double
        var velocity: CGPoint
    }
    
    var body: some View {
        TimelineView(.animation) { timeline in
            Canvas { context, size in
                for particle in particles {
                    let path = Circle().path(in: CGRect(
                        x: particle.x,
                        y: particle.y,
                        width: particle.size,
                        height: particle.size
                    ))
                    
                    context.fill(path, with: .color(.blue.opacity(particle.opacity)))
                }
            }
        }
        .onAppear {
            generateParticles()
        }
    }
    
    private func generateParticles() {
        particles = (0..<count).map { _ in
            Particle(
                x: CGFloat.random(in: 0...400),
                y: CGFloat.random(in: 0...800),
                size: CGFloat.random(in: 2...6),
                opacity: Double.random(in: 0.2...0.6),
                velocity: CGPoint(
                    x: CGFloat.random(in: -1...1),
                    y: CGFloat.random(in: -2...0)
                )
            )
        }
    }
}

