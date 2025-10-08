//
//  ContentView.swift
//  Newsreel
//
//  Created by David McLauchlan on 10/8/25.
//
//  Root view that handles authentication state
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authService: AuthService
    
    var body: some View {
        Group {
            switch authService.authState {
            case .authenticated:
                MainAppView()
                
            case .unauthenticated:
                LoginView()
                
            case .loading:
                LoadingView()
            }
        }
        .animation(.smooth, value: authService.authState)
    }
}

// MARK: - Loading View

struct LoadingView: View {
    var body: some View {
        ZStack {
            AppBackground()
            
            VStack(spacing: 20) {
                Image(systemName: "newspaper.fill")
                    .font(.system(size: 72, weight: .bold))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.blue, .purple],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                
                Text("Newsreel")
                    .font(.outfit(.extraBold, size: 42))
                
                ProgressView()
                    .tint(.primary)
            }
        }
    }
}

#Preview("Content View") {
    ContentView()
        .environmentObject(AuthService())
}

#Preview("Loading") {
    LoadingView()
}
