//
//  LoginView.swift
//  Newsreel
//
//  Main authentication screen with email/password and social login
//

import SwiftUI
import AuthenticationServices

struct LoginView: View {
    @EnvironmentObject var authService: AuthService
    @State private var isLoading = false
    @State private var errorMessage: String?
    
    var body: some View {
        ZStack {
            // Liquid Glass Background
            AppBackground()
            
            ScrollView {
                VStack(spacing: 32) {
                    Spacer()
                        .frame(height: 40)
                    
                    // App Logo & Title
                    VStack(spacing: 12) {
                        Image("AppIconDisplay")
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .frame(width: 100, height: 100)
                            .clipShape(RoundedRectangle(cornerRadius: 22.37, style: .continuous))
                            .shadow(color: .black.opacity(0.2), radius: 10, x: 0, y: 5)
                        
                        Text("Newsreel")
                            .font(.outfit(size: 42, weight: .extraBold))
                        
                        Text("AI-curated news, personalized for you")
                            .font(.outfit(size: 16, weight: .regular))
                            .foregroundStyle(.secondary)
                    }
                    .padding(.bottom, 40)
                    
                    // Error Message
                    if let errorMessage = errorMessage {
                        Text(errorMessage)
                            .font(.outfit(size: 14, weight: .regular))
                            .foregroundStyle(.red)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 32)
                            .padding(.bottom, 16)
                    }
                    
                    // Sign-In Options
                    VStack(spacing: 16) {
                        // Apple Sign-In
                        SignInWithAppleButton(.signIn) { request in
                            isLoading = true
                            let nonce = authService.prepareAppleSignIn()
                            request.requestedScopes = [.email, .fullName]
                            request.nonce = nonce
                        } onCompletion: { result in
                            handleAppleSignIn(result)
                        }
                        .signInWithAppleButtonStyle(.black)
                        .frame(height: 50)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                        .disabled(isLoading)
                        
                        // Google Sign-In (Google branding guidelines compliant)
                        GoogleSignInButton(
                            action: handleGoogleSignIn,
                            isLoading: isLoading
                        )
                        .padding(.horizontal, 0)
                        
                        // Divider
                        HStack {
                            Rectangle()
                                .frame(height: 1)
                                .foregroundStyle(.quaternary)
                            
                            Text("OR")
                                .font(.outfit(size: 13, weight: .medium))
                                .foregroundStyle(.secondary)
                                .padding(.horizontal, 12)
                            
                            Rectangle()
                                .frame(height: 1)
                                .foregroundStyle(.quaternary)
                        }
                        .padding(.vertical, 8)
                        
                        // Guest Sign-In
                        VStack(spacing: 8) {
                            Button(action: handleGuestSignIn) {
                                HStack(spacing: 12) {
                                    if isLoading {
                                        ProgressView()
                                            .tint(.primary)
                                    } else {
                                        Image(systemName: "person.fill.questionmark")
                                            .font(.system(size: 20))
                                        Text("Continue as Guest")
                                            .font(.outfit(size: 17, weight: .medium))
                                    }
                                }
                            }
                            .secondaryGlassButtonStyle()
                            .disabled(isLoading)
                            
                            Text("Limited features • No personalization")
                                .font(.outfit(size: 13, weight: .regular))
                                .foregroundStyle(.secondary)
                        }
                    }
                    .padding(.horizontal, 32)
                    
                    Spacer()
                }
            }
        }
    }
    
    // MARK: - Actions
    
    private func handleAppleSignIn(_ result: Result<ASAuthorization, Error>) {
        switch result {
        case .success(let authorization):
            errorMessage = nil
            
            Task {
                do {
                    try await authService.signInWithApple(authorization: authorization)
                } catch {
                    errorMessage = error.localizedDescription
                    isLoading = false
                }
            }
            
        case .failure(let error):
            errorMessage = error.localizedDescription
            isLoading = false
        }
    }
    
    private func handleGoogleSignIn() {
        errorMessage = nil
        isLoading = true
        
        Task {
            do {
                try await authService.signInWithGoogle()
            } catch {
                errorMessage = error.localizedDescription
                isLoading = false
            }
        }
    }
    
    private func handleGuestSignIn() {
        errorMessage = nil
        isLoading = true
        
        Task {
            do {
                try await authService.signInAnonymously()
            } catch {
                errorMessage = error.localizedDescription
                isLoading = false
            }
        }
    }
}

#Preview {
    LoginView()
        .environmentObject(AuthService())
}

