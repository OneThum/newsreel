//
//  AuthService.swift
//  Newsreel
//
//  Firebase Authentication Service
//  Handles email/password, Google, and Apple Sign-In
//

import Foundation
import FirebaseAuth
import FirebaseCore
import AuthenticationServices
import CryptoKit

/// Authentication state for the app
enum AuthState {
    case authenticated(User)
    case unauthenticated
    case loading
}

/// Authentication errors
enum AuthError: LocalizedError {
    case userNotFound
    case invalidCredentials
    case networkError
    case unknownError(String)
    
    var errorDescription: String? {
        switch self {
        case .userNotFound:
            return "User account not found"
        case .invalidCredentials:
            return "Invalid email or password"
        case .networkError:
            return "Network connection error. Please try again."
        case .unknownError(let message):
            return message
        }
    }
}

/// User model
struct User: Identifiable {
    let id: String
    let email: String?
    let displayName: String?
    let photoURL: URL?
    
    init(from firebaseUser: FirebaseAuth.User) {
        self.id = firebaseUser.uid
        self.email = firebaseUser.email
        self.displayName = firebaseUser.displayName
        self.photoURL = firebaseUser.photoURL
    }
}

@MainActor
class AuthService: ObservableObject {
    
    @Published var authState: AuthState = .loading
    @Published var currentUser: User?
    
    private var authStateListener: AuthStateDidChangeListenerHandle?
    private var currentNonce: String?
    
    init() {
        // Configure Firebase (called from NewsreelApp.swift)
        setupAuthStateListener()
    }
    
    deinit {
        if let listener = authStateListener {
            Auth.auth().removeStateDidChangeListener(listener)
        }
    }
    
    // MARK: - Auth State Monitoring
    
    private func setupAuthStateListener() {
        authStateListener = Auth.auth().addStateDidChangeListener { [weak self] _, firebaseUser in
            guard let self = self else { return }
            
            if let firebaseUser = firebaseUser {
                let user = User(from: firebaseUser)
                self.currentUser = user
                self.authState = .authenticated(user)
            } else {
                self.currentUser = nil
                self.authState = .unauthenticated
            }
        }
    }
    
    // MARK: - Email/Password Authentication
    
    func signIn(email: String, password: String) async throws {
        do {
            let result = try await Auth.auth().signIn(withEmail: email, password: password)
            let user = User(from: result.user)
            self.currentUser = user
            self.authState = .authenticated(user)
        } catch let error as NSError {
            throw mapFirebaseError(error)
        }
    }
    
    func signUp(email: String, password: String, displayName: String?) async throws {
        do {
            let result = try await Auth.auth().createUser(withEmail: email, password: password)
            
            // Update display name if provided
            if let displayName = displayName {
                let changeRequest = result.user.createProfileChangeRequest()
                changeRequest.displayName = displayName
                try await changeRequest.commitChanges()
            }
            
            let user = User(from: result.user)
            self.currentUser = user
            self.authState = .authenticated(user)
        } catch let error as NSError {
            throw mapFirebaseError(error)
        }
    }
    
    // MARK: - Google Sign-In
    
    // TODO: Implement Google Sign-In (requires GoogleSignIn SDK)
    // This will be added in Phase 3
    
    // MARK: - Apple Sign-In
    
    func signInWithApple(authorization: ASAuthorization) async throws {
        guard let appleIDCredential = authorization.credential as? ASAuthorizationAppleIDCredential else {
            throw AuthError.unknownError("Invalid Apple ID credential")
        }
        
        guard let nonce = currentNonce else {
            throw AuthError.unknownError("Invalid state: nonce missing")
        }
        
        guard let appleIDToken = appleIDCredential.identityToken else {
            throw AuthError.unknownError("Unable to fetch identity token")
        }
        
        guard let idTokenString = String(data: appleIDToken, encoding: .utf8) else {
            throw AuthError.unknownError("Unable to serialize token string")
        }
        
        let credential = OAuthProvider.credential(
            withProviderID: "apple.com",
            idToken: idTokenString,
            rawNonce: nonce
        )
        
        do {
            let result = try await Auth.auth().signIn(with: credential)
            let user = User(from: result.user)
            self.currentUser = user
            self.authState = .authenticated(user)
        } catch let error as NSError {
            throw mapFirebaseError(error)
        }
    }
    
    func prepareAppleSignIn() -> String {
        let nonce = randomNonceString()
        currentNonce = nonce
        return sha256(nonce)
    }
    
    // MARK: - Sign Out
    
    func signOut() throws {
        do {
            try Auth.auth().signOut()
            self.currentUser = nil
            self.authState = .unauthenticated
        } catch let error as NSError {
            throw mapFirebaseError(error)
        }
    }
    
    // MARK: - Password Reset
    
    func sendPasswordReset(email: String) async throws {
        do {
            try await Auth.auth().sendPasswordReset(withEmail: email)
        } catch let error as NSError {
            throw mapFirebaseError(error)
        }
    }
    
    // MARK: - JWT Token
    
    /// Get current user's Firebase JWT token for API authentication
    func getIDToken(forceRefresh: Bool = false) async throws -> String {
        guard let firebaseUser = Auth.auth().currentUser else {
            throw AuthError.userNotFound
        }
        
        return try await firebaseUser.getIDToken(forcingRefresh: forceRefresh)
    }
    
    // MARK: - Helper Methods
    
    private func mapFirebaseError(_ error: NSError) -> AuthError {
        guard let errorCode = AuthErrorCode.Code(rawValue: error.code) else {
            return .unknownError(error.localizedDescription)
        }
        
        switch errorCode {
        case .userNotFound, .userDisabled:
            return .userNotFound
        case .wrongPassword, .invalidEmail, .invalidCredential:
            return .invalidCredentials
        case .networkError:
            return .networkError
        default:
            return .unknownError(error.localizedDescription)
        }
    }
    
    // MARK: - Apple Sign-In Helpers
    
    private func randomNonceString(length: Int = 32) -> String {
        precondition(length > 0)
        let charset: [Character] = Array("0123456789ABCDEFGHIJKLMNOPQRSTUVXYZabcdefghijklmnopqrstuvwxyz-._")
        var result = ""
        var remainingLength = length
        
        while remainingLength > 0 {
            let randoms: [UInt8] = (0 ..< 16).map { _ in
                var random: UInt8 = 0
                let errorCode = SecRandomCopyBytes(kSecRandomDefault, 1, &random)
                if errorCode != errSecSuccess {
                    fatalError("Unable to generate nonce. SecRandomCopyBytes failed with OSStatus \(errorCode)")
                }
                return random
            }
            
            randoms.forEach { random in
                if remainingLength == 0 {
                    return
                }
                
                if random < charset.count {
                    result.append(charset[Int(random)])
                    remainingLength -= 1
                }
            }
        }
        
        return result
    }
    
    private func sha256(_ input: String) -> String {
        let inputData = Data(input.utf8)
        let hashedData = SHA256.hash(data: inputData)
        let hashString = hashedData.compactMap {
            String(format: "%02x", $0)
        }.joined()
        
        return hashString
    }
}

