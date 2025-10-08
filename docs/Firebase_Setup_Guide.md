# Firebase Setup Guide for Newsreel

**Last Updated**: October 8, 2025

---

## Overview

Newsreel uses Firebase for user authentication. This guide covers the Firebase configuration and setup.

---

## Firebase Project Details

| Setting | Value |
|---------|-------|
| **Project ID** | newsreel-865a5 |
| **Bundle ID** | com.onethum.newsreel |
| **Google App ID** | 1:940368851541:ios:7016e27c1cd8d535c15adc |
| **Storage Bucket** | newsreel-865a5.firebasestorage.app |
| **Console URL** | https://console.firebase.google.com/project/newsreel-865a5 |

### Features Enabled

- ✅ **Authentication** - Email/password, Google Sign-In, Apple Sign-In
- ✅ **Cloud Messaging (GCM)** - Push notifications
- ✅ **App Invite** - User referrals
- ❌ **Analytics** - Disabled for privacy
- ❌ **Ads** - Disabled (ad-free app)

---

## Configuration File

The `GoogleService-Info.plist` file is already configured and located at:

```
Newsreel App/Newsreel/GoogleService-Info.plist
```

**Important**: This file contains API keys and should:
- ✅ Be included in the Xcode project
- ✅ Have target membership for Newsreel
- ❌ NOT be committed to public repositories (already in .gitignore)

---

## Xcode Configuration

### 1. Verify GoogleService-Info.plist

1. Open `Newsreel.xcodeproj` in Xcode
2. Verify `GoogleService-Info.plist` is in the Project Navigator
3. Select the file and check **Target Membership** → ✓ **Newsreel**
4. The file should be in the **Copy Bundle Resources** build phase

### 2. Add Firebase SDK

Add Firebase via Swift Package Manager:

1. In Xcode, go to **File** → **Add Package Dependencies**
2. Enter URL: `https://github.com/firebase/firebase-ios-sdk`
3. Select version: **Latest** (11.0.0+)
4. Click **Add Package**
5. Select these products:
   - ✅ **FirebaseAuth** (Authentication)
   - ✅ **FirebaseMessaging** (Push notifications)
   - ✅ **FirebaseAnalytics** (Optional, if needed later)

### 3. Initialize Firebase in App

Update `NewsreelApp.swift`:

```swift
//
//  NewsreelApp.swift
//  Newsreel
//

import SwiftUI
import FirebaseCore
import FirebaseAuth

@main
struct NewsreelApp: App {
    
    init() {
        // Configure Firebase
        FirebaseApp.configure()
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
```

---

## Authentication Setup

### Enabled Methods

The Firebase project has these authentication methods configured:

1. **Email/Password** ✅
2. **Google Sign-In** ✅
3. **Apple Sign-In** ✅

### Configure Authentication Methods

#### Email/Password

Already enabled in Firebase Console. No additional configuration needed.

#### Google Sign-In

1. Go to Firebase Console → Authentication → Sign-in method
2. Google is already enabled
3. For iOS, use Firebase Auth's Google Sign-In integration

```swift
import FirebaseAuth
import GoogleSignIn

func signInWithGoogle() async throws {
    guard let clientID = FirebaseApp.app()?.options.clientID else { return }
    
    let config = GIDConfiguration(clientID: clientID)
    GIDSignIn.sharedInstance.configuration = config
    
    guard let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
          let window = windowScene.windows.first,
          let rootViewController = window.rootViewController else {
        return
    }
    
    let result = try await GIDSignIn.sharedInstance.signIn(withPresenting: rootViewController)
    
    guard let idToken = result.user.idToken?.tokenString else { return }
    let accessToken = result.user.accessToken.tokenString
    
    let credential = GoogleAuthProvider.credential(withIDToken: idToken, accessToken: accessToken)
    try await Auth.auth().signIn(with: credential)
}
```

#### Apple Sign-In

1. Already enabled in Firebase Console
2. Add **Sign in with Apple** capability in Xcode:
   - Select Newsreel target
   - Go to **Signing & Capabilities**
   - Click **+ Capability**
   - Add **Sign in with Apple**

```swift
import FirebaseAuth
import AuthenticationServices
import CryptoKit

func signInWithApple() {
    let nonce = randomNonceString()
    currentNonce = nonce
    
    let appleIDProvider = ASAuthorizationAppleIDProvider()
    let request = appleIDProvider.createRequest()
    request.requestedScopes = [.fullName, .email]
    request.nonce = sha256(nonce)
    
    let authorizationController = ASAuthorizationController(authorizationRequests: [request])
    authorizationController.delegate = self
    authorizationController.presentationContextProvider = self
    authorizationController.performRequests()
}

// On success callback
func authorizationController(controller: ASAuthorizationController, didCompleteWithAuthorization authorization: ASAuthorization) {
    guard let appleIDCredential = authorization.credential as? ASAuthorizationAppleIDCredential,
          let nonce = currentNonce,
          let appleIDToken = appleIDCredential.identityToken,
          let idTokenString = String(data: appleIDToken, encoding: .utf8) else {
        return
    }
    
    let credential = OAuthProvider.appleCredential(withIDToken: idTokenString,
                                                   rawNonce: nonce,
                                                   fullName: appleIDCredential.fullName)
    
    Task {
        try await Auth.auth().signIn(with: credential)
    }
}

// Helper functions
private func randomNonceString(length: Int = 32) -> String {
    precondition(length > 0)
    var randomBytes = [UInt8](repeating: 0, count: length)
    let errorCode = SecRandomCopyBytes(kSecRandomDefault, randomBytes.count, &randomBytes)
    if errorCode != errSecSuccess {
        fatalError("Unable to generate nonce")
    }
    
    let charset: [Character] = Array("0123456789ABCDEFGHIJKLMNOPQRSTUVXYZabcdefghijklmnopqrstuvwxyz-._")
    let nonce = randomBytes.map { byte in
        charset[Int(byte) % charset.count]
    }
    return String(nonce)
}

private func sha256(_ input: String) -> String {
    let inputData = Data(input.utf8)
    let hashedData = SHA256.hash(data: inputData)
    let hashString = hashedData.compactMap {
        String(format: "%02x", $0)
    }.joined()
    return hashString
}
```

---

## Push Notifications (Firebase Cloud Messaging)

### Upload APNs Certificate

1. Go to Firebase Console → Project Settings → Cloud Messaging
2. Under **Apple app configuration**, upload your APNs certificate or key
3. For development: Upload Development APNs certificate
4. For production: Upload Production APNs certificate

### Configure in Xcode

1. Add **Push Notifications** capability:
   - Select Newsreel target
   - Signing & Capabilities
   - Add **Push Notifications**

2. Add **Background Modes** capability:
   - Enable **Remote notifications**

### Initialize Messaging

```swift
import FirebaseMessaging
import UserNotifications

class AppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication,
                    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey : Any]? = nil) -> Bool {
        
        // Request notification permissions
        UNUserNotificationCenter.current().delegate = self
        let authOptions: UNAuthorizationOptions = [.alert, .badge, .sound]
        UNUserNotificationCenter.current().requestAuthorization(options: authOptions) { granted, _ in
            print("Permission granted: \(granted)")
        }
        
        application.registerForRemoteNotifications()
        
        // Set FCM delegate
        Messaging.messaging().delegate = self
        
        return true
    }
    
    func application(_ application: UIApplication,
                    didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        Messaging.messaging().apnsToken = deviceToken
    }
}

extension AppDelegate: MessagingDelegate {
    func messaging(_ messaging: Messaging, didReceiveRegistrationToken fcmToken: String?) {
        print("FCM Token: \(fcmToken ?? "")")
        // Send token to your backend
        sendTokenToBackend(fcmToken)
    }
}

extension AppDelegate: UNUserNotificationCenterDelegate {
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                              willPresent notification: UNNotification,
                              withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        completionHandler([[.banner, .sound, .badge]])
    }
}
```

---

## Security Rules

### Authentication Security

Current configuration:
- Email verification: Optional (can be enabled)
- Password requirements: Firebase defaults (6+ characters)
- Account enumeration protection: Enabled

### Best Practices

1. **Enable Email Verification** (Optional):
```swift
try await user.sendEmailVerification()
```

2. **Password Reset**:
```swift
try await Auth.auth().sendPasswordReset(withEmail: email)
```

3. **Token Refresh**:
```swift
let token = try await Auth.auth().currentUser?.getIDToken()
```

---

## Backend Integration

### Verify Firebase Tokens

Backend services should verify Firebase ID tokens:

```python
# api/services/auth_service.py

from firebase_admin import auth, credentials, initialize_app
import os

# Initialize Firebase Admin SDK
cred = credentials.Certificate(os.environ["FIREBASE_CREDENTIALS_JSON"])
initialize_app(cred)

async def verify_token(id_token: str) -> dict:
    """Verify Firebase ID token and return user info"""
    try:
        decoded_token = auth.verify_id_token(id_token)
        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "email_verified": decoded_token.get("email_verified", False)
        }
    except Exception as e:
        raise ValueError(f"Invalid token: {str(e)}")
```

### Store Service Account Key

The backend needs the Firebase service account key stored in Azure Key Vault:

```bash
# Download service account key from Firebase Console
# Then store in Azure Key Vault
az keyvault secret set \
  --vault-name newsreel-prod-kv \
  --name "FirebaseServiceAccountKey" \
  --file path/to/newsreel-865a5-firebase-adminsdk.json
```

---

## Testing

### Test Authentication

1. Run the app in simulator
2. Create test account:
   - Email: `test@newsreel.app`
   - Password: `TestPassword123`
3. Verify in Firebase Console → Authentication → Users

### Test Push Notifications

Use Firebase Console to send test notification:

1. Go to Cloud Messaging
2. Click **Send your first message**
3. Enter notification details
4. Select your app
5. Click **Test on device**
6. Enter FCM token from app logs

---

## Troubleshooting

### Issue: "No Firebase App '[DEFAULT]' has been created"

**Solution**: Ensure `FirebaseApp.configure()` is called in app init before any Firebase usage.

### Issue: GoogleService-Info.plist not found

**Solution**: 
1. Verify file is in project
2. Check target membership
3. Clean build folder (Shift + Cmd + K)
4. Rebuild

### Issue: Google Sign-In not working

**Solution**:
1. Verify Google Sign-In is enabled in Firebase Console
2. Check bundle ID matches
3. Add Google Sign-In SDK via SPM
4. Configure URL schemes in Info.plist

### Issue: Apple Sign-In fails

**Solution**:
1. Enable Sign in with Apple capability in Xcode
2. Verify Apple Sign-In is enabled in Firebase Console
3. Check App ID has Sign in with Apple enabled in Apple Developer portal

---

## Firebase Console Access

- **URL**: https://console.firebase.google.com/project/newsreel-865a5
- **Authentication**: https://console.firebase.google.com/project/newsreel-865a5/authentication/users
- **Cloud Messaging**: https://console.firebase.google.com/project/newsreel-865a5/notification

---

## Privacy Considerations

Current configuration:
- ❌ **Analytics Disabled** - No user tracking
- ❌ **Ads Disabled** - Ad-free experience
- ✅ **Authentication Only** - Minimal data collection
- ✅ **Cloud Messaging** - For breaking news notifications only

This configuration aligns with our privacy-first approach.

---

## Resources

- **Firebase iOS Documentation**: https://firebase.google.com/docs/ios/setup
- **Firebase Auth Documentation**: https://firebase.google.com/docs/auth
- **Firebase Cloud Messaging**: https://firebase.google.com/docs/cloud-messaging

---

**Document Owner**: iOS Lead  
**Last Updated**: October 8, 2025  
**Next Review**: After authentication implementation

