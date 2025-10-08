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
    @State private var email = ""
    @State private var password = ""
    @State private var isSignUp = false
    @State private var displayName = ""
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showingForgotPassword = false
    @FocusState private var focusedField: Field?
    
    enum Field: Hashable {
        case email, password, displayName
    }
    
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
                        
                        Text("AI-curated news, personalized for you")
                            .font(.outfit(.regular, size: 16))
                            .foregroundStyle(.secondary)
                    }
                    .padding(.bottom, 20)
                    
                    // Auth Form
                    VStack(spacing: 16) {
                        if isSignUp {
                            // Display Name Field
                            TextField("Display Name", text: $displayName)
                                .textContentType(.name)
                                .autocapitalization(.words)
                                .focused($focusedField, equals: .displayName)
                                .padding()
                                .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
                        }
                        
                        // Email Field
                        TextField("Email", text: $email)
                            .textContentType(.emailAddress)
                            .autocapitalization(.none)
                            .keyboardType(.emailAddress)
                            .focused($focusedField, equals: .email)
                            .padding()
                            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
                        
                        // Password Field
                        SecureField("Password", text: $password)
                            .textContentType(isSignUp ? .newPassword : .password)
                            .focused($focusedField, equals: .password)
                            .padding()
                            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
                        
                        // Error Message
                        if let errorMessage = errorMessage {
                            Text(errorMessage)
                                .font(.outfit(.regular, size: 14))
                                .foregroundStyle(.red)
                                .multilineTextAlignment(.center)
                        }
                        
                        // Sign In/Up Button
                        Button(action: handleEmailAuth) {
                            HStack {
                                if isLoading {
                                    ProgressView()
                                        .tint(.white)
                                } else {
                                    Text(isSignUp ? "Create Account" : "Sign In")
                                        .font(.outfit(.semiBold, size: 18))
                                }
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(
                                LinearGradient(
                                    colors: [.blue, .purple],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .foregroundStyle(.white)
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                        }
                        .disabled(isLoading || !isFormValid)
                        .opacity((isLoading || !isFormValid) ? 0.6 : 1.0)
                        
                        // Toggle Sign In/Up
                        Button(action: {
                            withAnimation(.smooth) {
                                isSignUp.toggle()
                                errorMessage = nil
                            }
                        }) {
                            Text(isSignUp ? "Already have an account? **Sign In**" : "Don't have an account? **Sign Up**")
                                .font(.outfit(.regular, size: 15))
                                .foregroundStyle(.primary)
                        }
                        
                        // Forgot Password
                        if !isSignUp {
                            Button(action: { showingForgotPassword = true }) {
                                Text("Forgot Password?")
                                    .font(.outfit(.regular, size: 14))
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    .padding(.horizontal, 32)
                    
                    // Divider
                    HStack {
                        Rectangle()
                            .frame(height: 1)
                            .foregroundStyle(.quaternary)
                        
                        Text("OR")
                            .font(.outfit(.medium, size: 13))
                            .foregroundStyle(.secondary)
                            .padding(.horizontal, 12)
                        
                        Rectangle()
                            .frame(height: 1)
                            .foregroundStyle(.quaternary)
                    }
                    .padding(.horizontal, 32)
                    
                    // Social Sign-In Buttons
                    VStack(spacing: 12) {
                        // Apple Sign-In
                        SignInWithAppleButton(.signIn) { request in
                            let nonce = authService.prepareAppleSignIn()
                            request.requestedScopes = [.email, .fullName]
                            request.nonce = nonce
                        } onCompletion: { result in
                            Task {
                                await handleAppleSignIn(result)
                            }
                        }
                        .signInWithAppleButtonStyle(.black)
                        .frame(height: 50)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                        
                        // Google Sign-In (Coming Soon)
                        Button(action: {}) {
                            HStack {
                                Image(systemName: "globe")
                                Text("Continue with Google")
                                    .font(.outfit(.semiBold, size: 16))
                            }
                            .frame(maxWidth: .infinity)
                            .frame(height: 50)
                            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
                        }
                        .disabled(true)
                        .opacity(0.5)
                    }
                    .padding(.horizontal, 32)
                    
                    Spacer()
                }
            }
            .scrollDismissesKeyboard(.interactively)
        }
        .alert("Reset Password", isPresented: $showingForgotPassword) {
            TextField("Email", text: $email)
            Button("Cancel", role: .cancel) {}
            Button("Send Reset Link") {
                Task {
                    await handlePasswordReset()
                }
            }
        } message: {
            Text("Enter your email address to receive a password reset link.")
        }
    }
    
    // MARK: - Computed Properties
    
    private var isFormValid: Bool {
        if isSignUp {
            return !email.isEmpty && !password.isEmpty && password.count >= 6 && !displayName.isEmpty
        } else {
            return !email.isEmpty && !password.isEmpty
        }
    }
    
    // MARK: - Actions
    
    private func handleEmailAuth() {
        errorMessage = nil
        isLoading = true
        focusedField = nil
        
        Task {
            do {
                if isSignUp {
                    try await authService.signUp(email: email, password: password, displayName: displayName)
                } else {
                    try await authService.signIn(email: email, password: password)
                }
            } catch {
                errorMessage = error.localizedDescription
            }
            isLoading = false
        }
    }
    
    private func handleAppleSignIn(_ result: Result<ASAuthorization, Error>) {
        switch result {
        case .success(let authorization):
            errorMessage = nil
            isLoading = true
            
            Task {
                do {
                    try await authService.signInWithApple(authorization: authorization)
                } catch {
                    errorMessage = error.localizedDescription
                }
                isLoading = false
            }
            
        case .failure(let error):
            errorMessage = error.localizedDescription
        }
    }
    
    private func handlePasswordReset() async {
        guard !email.isEmpty else { return }
        
        do {
            try await authService.sendPasswordReset(email: email)
            errorMessage = "Password reset link sent to \(email)"
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    LoginView()
        .environmentObject(AuthService())
}

