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
import GoogleSignIn

/// Authentication state for the app
enum AuthState: Equatable {
    case authenticated(User)
    case unauthenticated
    case loading
    
    static func == (lhs: AuthState, rhs: AuthState) -> Bool {
        switch (lhs, rhs) {
        case (.authenticated(let lUser), .authenticated(let rUser)):
            return lUser.id == rUser.id
        case (.unauthenticated, .unauthenticated):
            return true
        case (.loading, .loading):
            return true
        default:
            return false
        }
    }
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
    let isAnonymous: Bool
    
    init(from firebaseUser: FirebaseAuth.User) {
        self.id = firebaseUser.uid
        self.email = firebaseUser.email
        self.displayName = firebaseUser.displayName
        self.photoURL = firebaseUser.photoURL
        self.isAnonymous = firebaseUser.isAnonymous
    }
}

@MainActor
class AuthService: ObservableObject {
    
    @Published var authState: AuthState = .loading
    @Published var currentUser: User?
    @Published var isAnonymous: Bool = false
    
    private var authStateListener: AuthStateDidChangeListenerHandle?
    private var currentNonce: String?
    
    init() {
        log.separator("AUTH SERVICE INIT")
        log.logAuth("Initializing AuthService", level: .info)
        // Configure Firebase (called from NewsreelApp.swift)
        setupAuthStateListener()
        log.logAuth("AuthService initialized", level: .info)
    }
    
    deinit {
        if let listener = authStateListener {
            Auth.auth().removeStateDidChangeListener(listener)
        }
    }
    
    // MARK: - Auth State Monitoring
    
    private func setupAuthStateListener() {
        log.logAuth("Setting up auth state listener", level: .debug)
        authStateListener = Auth.auth().addStateDidChangeListener { [weak self] _, firebaseUser in
            guard let self = self else { return }
            
            if let firebaseUser = firebaseUser {
                let user = User(from: firebaseUser)
                self.currentUser = user
                self.isAnonymous = firebaseUser.isAnonymous
                self.authState = .authenticated(user)
                
                let userType = firebaseUser.isAnonymous ? "Anonymous" : "Authenticated"
                log.logAuth("🔐 Auth state changed: \(userType) user (UID: \(firebaseUser.uid.prefix(8))...)", level: .info)
                log.logAuth("   Email: \(firebaseUser.email ?? "none")", level: .debug)
                log.logAuth("   Display Name: \(firebaseUser.displayName ?? "none")", level: .debug)
                log.logAuth("   Is Anonymous: \(firebaseUser.isAnonymous)", level: .debug)
            } else {
                self.currentUser = nil
                self.isAnonymous = false
                self.authState = .unauthenticated
                log.logAuth("🔓 Auth state changed: Unauthenticated", level: .info)
            }
        }
    }
    
    // MARK: - Email/Password Authentication
    
    func signIn(email: String, password: String) async throws {
        log.logAuth("Attempting email/password sign in for: \(email)", level: .info)
        do {
            let result = try await Auth.auth().signIn(withEmail: email, password: password)
            let user = User(from: result.user)
            self.currentUser = user
            self.authState = .authenticated(user)
            log.logAuth("✅ Email/password sign in successful", level: .info)
        } catch let error as NSError {
            log.logAuth("❌ Email/password sign in failed: \(error.localizedDescription)", level: .error)
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
    
    // MARK: - Anonymous Sign-In
    
    func signInAnonymously() async throws {
        log.logAuth("Attempting anonymous sign in", level: .info)
        do {
            let result = try await Auth.auth().signInAnonymously()
            let user = User(from: result.user)
            self.currentUser = user
            self.isAnonymous = true
            self.authState = .authenticated(user)
            log.logAuth("✅ Anonymous sign in successful (UID: \(result.user.uid.prefix(8))...)", level: .info)
        } catch let error as NSError {
            log.logAuth("❌ Anonymous sign in failed: \(error.localizedDescription)", level: .error)
            throw mapFirebaseError(error)
        }
    }
    
    // MARK: - Link Anonymous Account
    
    /// Link anonymous account to permanent credentials (for future use)
    func linkAnonymousAccount(to credential: AuthCredential) async throws {
        guard let firebaseUser = Auth.auth().currentUser, firebaseUser.isAnonymous else {
            throw AuthError.unknownError("No anonymous account to link")
        }
        
        do {
            let result = try await firebaseUser.link(with: credential)
            let user = User(from: result.user)
            self.currentUser = user
            self.isAnonymous = false
            self.authState = .authenticated(user)
        } catch let error as NSError {
            throw mapFirebaseError(error)
        }
    }
    
    // MARK: - Google Sign-In
    
    func signInWithGoogle() async throws {
        log.logAuth("Attempting Google Sign In", level: .info)
        
        // Get the client ID from Firebase
        guard let clientID = Auth.auth().app?.options.clientID else {
            log.logAuth("❌ No Firebase client ID found", level: .error)
            throw AuthError.unknownError("No Firebase client ID found")
        }
        
        // Create Google Sign In configuration
        let config = GIDConfiguration(clientID: clientID)
        GIDSignIn.sharedInstance.configuration = config
        
        // Get the root view controller
        guard let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
              let rootViewController = windowScene.windows.first?.rootViewController else {
            log.logAuth("❌ No root view controller found", level: .error)
            throw AuthError.unknownError("No root view controller")
        }
        
        do {
            // Start the sign in flow
            let result = try await GIDSignIn.sharedInstance.signIn(withPresenting: rootViewController)
            
            guard let idToken = result.user.idToken?.tokenString else {
                log.logAuth("❌ No ID token from Google", level: .error)
                throw AuthError.unknownError("No ID token from Google")
            }
            
            let accessToken = result.user.accessToken.tokenString
            
            log.logAuth("Google sign in successful, creating Firebase credential", level: .debug)
            
            // Create Firebase credential
            let credential = GoogleAuthProvider.credential(withIDToken: idToken, accessToken: accessToken)
            
            // Sign in with Firebase
            let authResult = try await Auth.auth().signIn(with: credential)
            let user = User(from: authResult.user)
            self.currentUser = user
            self.authState = .authenticated(user)
            
            log.logAuth("✅ Google Sign In successful (UID: \(authResult.user.uid.prefix(8))...)", level: .info)
            log.logAuth("   Email: \(authResult.user.email ?? "none")", level: .debug)
            log.logAuth("   Display Name: \(authResult.user.displayName ?? "none")", level: .debug)
            
        } catch let error as NSError {
            log.logAuth("❌ Google Sign In failed: \(error.localizedDescription)", level: .error)
            throw mapFirebaseError(error)
        }
    }
    
    // MARK: - Apple Sign-In
    
    func signInWithApple(authorization: ASAuthorization) async throws {
        log.logAuth("Attempting Apple Sign In", level: .info)
        
        guard let appleIDCredential = authorization.credential as? ASAuthorizationAppleIDCredential else {
            log.logAuth("❌ Invalid Apple ID credential", level: .error)
            throw AuthError.unknownError("Invalid Apple ID credential")
        }
        
        guard let nonce = currentNonce else {
            log.logAuth("❌ Nonce missing", level: .error)
            throw AuthError.unknownError("Invalid state: nonce missing")
        }
        
        guard let appleIDToken = appleIDCredential.identityToken else {
            log.logAuth("❌ Unable to fetch identity token", level: .error)
            throw AuthError.unknownError("Unable to fetch identity token")
        }
        
        guard let idTokenString = String(data: appleIDToken, encoding: .utf8) else {
            log.logAuth("❌ Unable to serialize token string", level: .error)
            throw AuthError.unknownError("Unable to serialize token string")
        }
        
        log.logAuth("Apple ID token obtained, creating Firebase credential", level: .debug)
        
        let credential = OAuthProvider.appleCredential(
            withIDToken: idTokenString,
            rawNonce: nonce,
            fullName: appleIDCredential.fullName
        )
        
        do {
            let result = try await Auth.auth().signIn(with: credential)
            let user = User(from: result.user)
            self.currentUser = user
            self.authState = .authenticated(user)
            log.logAuth("✅ Apple Sign In successful (UID: \(result.user.uid.prefix(8))...)", level: .info)
            log.logAuth("   Email: \(result.user.email ?? "none")", level: .debug)
        } catch let error as NSError {
            log.logAuth("❌ Apple Sign In failed: \(error.localizedDescription)", level: .error)
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
        log.logAuth("Getting Firebase ID token (force refresh: \(forceRefresh))", level: .debug)
        
        guard let firebaseUser = Auth.auth().currentUser else {
            log.logAuth("❌ No current user, cannot get token", level: .error)
            throw AuthError.userNotFound
        }
        
        do {
            let token = try await firebaseUser.getIDToken(forcingRefresh: forceRefresh)
            log.logAuth("✅ Firebase ID token obtained (length: \(token.count) chars)", level: .debug)
            return token
        } catch {
            log.logAuth("❌ Failed to get Firebase ID token: \(error.localizedDescription)", level: .error)
            throw error
        }
    }
    
    // MARK: - Helper Methods
    
    private func mapFirebaseError(_ error: NSError) -> AuthError {
        guard let errorCode = AuthErrorCode(rawValue: error.code) else {
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

