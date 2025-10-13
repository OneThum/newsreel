//
//  GoogleSignInButton.swift
//  Newsreel
//
//  Google Sign-In button compliant with Google's branding guidelines
//  https://developers.google.com/identity/branding-guidelines
//

import SwiftUI

struct GoogleSignInButton: View {
    let action: () -> Void
    let isLoading: Bool
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                // Google "G" logo
                GoogleGLogo()
                    .frame(width: 20, height: 20)
                
                Text("Continue with Google")
                    .font(.outfit(size: 17, weight: .semiBold))
                    .foregroundColor(.primary)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 50)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(.white.opacity(0.1))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(.white.opacity(0.2), lineWidth: 1)
                    )
            )
        }
        .disabled(isLoading)
    }
}

/// Google's official "G" logo as an SVG
/// Colors match Google's brand guidelines exactly
struct GoogleGLogo: View {
    var body: some View {
        ZStack {
            // Background white circle for contrast
            Circle()
                .fill(.white)
            
            // The Google "G" logo
            GeometryReader { geometry in
                let size = geometry.size.width
                
                Path { path in
                    // Blue section (right side)
                    path.move(to: CGPoint(x: size * 0.9, y: size * 0.5))
                    path.addLine(to: CGPoint(x: size * 0.55, y: size * 0.5))
                    path.addLine(to: CGPoint(x: size * 0.55, y: size * 0.37))
                    path.addLine(to: CGPoint(x: size * 0.9, y: size * 0.37))
                    path.addArc(center: CGPoint(x: size * 0.5, y: size * 0.5),
                               radius: size * 0.4,
                               startAngle: .degrees(270),
                               endAngle: .degrees(0),
                               clockwise: false)
                }
                .fill(Color(red: 66/255, green: 133/255, blue: 244/255)) // Google Blue
                
                Path { path in
                    // Green section (bottom right)
                    path.addArc(center: CGPoint(x: size * 0.5, y: size * 0.5),
                               radius: size * 0.4,
                               startAngle: .degrees(0),
                               endAngle: .degrees(90),
                               clockwise: false)
                    path.addArc(center: CGPoint(x: size * 0.5, y: size * 0.5),
                               radius: size * 0.25,
                               startAngle: .degrees(90),
                               endAngle: .degrees(0),
                               clockwise: true)
                }
                .fill(Color(red: 52/255, green: 168/255, blue: 83/255)) // Google Green
                
                Path { path in
                    // Yellow section (bottom left)
                    path.addArc(center: CGPoint(x: size * 0.5, y: size * 0.5),
                               radius: size * 0.4,
                               startAngle: .degrees(90),
                               endAngle: .degrees(180),
                               clockwise: false)
                    path.addArc(center: CGPoint(x: size * 0.5, y: size * 0.5),
                               radius: size * 0.25,
                               startAngle: .degrees(180),
                               endAngle: .degrees(90),
                               clockwise: true)
                }
                .fill(Color(red: 251/255, green: 188/255, blue: 5/255)) // Google Yellow
                
                Path { path in
                    // Red section (top left)
                    path.addArc(center: CGPoint(x: size * 0.5, y: size * 0.5),
                               radius: size * 0.4,
                               startAngle: .degrees(180),
                               endAngle: .degrees(270),
                               clockwise: false)
                    path.addArc(center: CGPoint(x: size * 0.5, y: size * 0.5),
                               radius: size * 0.25,
                               startAngle: .degrees(270),
                               endAngle: .degrees(180),
                               clockwise: true)
                }
                .fill(Color(red: 234/255, green: 67/255, blue: 53/255)) // Google Red
            }
            .padding(2)
        }
    }
}

#Preview {
    VStack(spacing: 20) {
        GoogleSignInButton(action: {}, isLoading: false)
            .padding()
        
        GoogleSignInButton(action: {}, isLoading: true)
            .padding()
        
        GoogleGLogo()
            .frame(width: 48, height: 48)
    }
    .background(Color.black)
}

