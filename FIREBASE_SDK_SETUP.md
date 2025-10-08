# Firebase SDK Setup Instructions

**Note**: Firebase SDK packages must be added through Xcode's UI due to Swift Package Manager integration.

## Steps to Add Firebase SDK

1. **Open Xcode Project**
   ```bash
   open "Newsreel App/Newsreel.xcodeproj"
   ```

2. **Add Firebase Package**
   - Select the Newsreel project in the Project Navigator
   - Select the Newsreel target
   - Go to "Package Dependencies" tab
   - Click the "+" button at the bottom
   - Enter Firebase package URL: `https://github.com/firebase/firebase-ios-sdk`
   - Select version: `11.6.0` or "Up to Next Major Version"
   - Click "Add Package"

3. **Select Firebase Products**
   When prompted, add these products:
   - ✅ **FirebaseAuth** - Authentication
   - ✅ **FirebaseMessaging** - Push notifications (Cloud Messaging)
   - ✅ **FirebaseAnalytics** (optional, currently disabled in app)
   
   Click "Add Package"

4. **Verify Installation**
   - Build the project (Cmd+B)
   - Firebase packages should download and link automatically
   - Check for any build errors

## Required Capabilities

After adding Firebase SDK, enable these capabilities in Xcode:

1. **Push Notifications**
   - Select Newsreel target → "Signing & Capabilities"
   - Click "+ Capability"
   - Add "Push Notifications"

2. **Sign in with Apple**
   - Click "+ Capability"
   - Add "Sign in with Apple"

3. **Background Modes** (for push notifications)
   - Click "+ Capability"
   - Add "Background Modes"
   - Enable "Remote notifications"

## Code Signing

Set your Apple Developer Team:
- Select Newsreel target → "Signing & Capabilities"
- Under "Team", select your developer account
- Bundle Identifier: `com.onethum.newsreel`

## Already Configured

✅ GoogleService-Info.plist is already included in the project  
✅ Firebase initialization code is in `NewsreelApp.swift`  
✅ AuthService is implemented and ready to use  
✅ Authentication views are complete

## Next Steps

Once Firebase SDK is added:
1. Build and run the app (Cmd+R)
2. Test email/password sign-up
3. Test Apple Sign-In
4. Verify authentication state handling

## Troubleshooting

**Build errors**: Clean build folder (Shift+Cmd+K) and rebuild  
**Package resolution issues**: File → Packages → Reset Package Caches  
**Missing imports**: Make sure FirebaseAuth and FirebaseCore are selected in package products

