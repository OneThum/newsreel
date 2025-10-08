# Xcode Project Configuration for Newsreel

**Last Updated**: October 8, 2025

---

## App Identity

| Setting | Value |
|---------|-------|
| **Product Name** | Newsreel |
| **Display Name** | Newsreel |
| **Bundle Identifier** | com.onethum.newsreel |
| **Version** | 1.0.0 |
| **Build** | 1 |
| **Developer** | One Thum Software |
| **Copyright** | © 2025 One Thum Software. All rights reserved. |

---

## Xcode Project Settings

### General Tab

1. Open `Newsreel.xcodeproj` in Xcode
2. Select the **Newsreel** target
3. In the **General** tab, configure:

| Setting | Value |
|---------|-------|
| **Display Name** | `Newsreel` |
| **Bundle Identifier** | `com.onethum.newsreel` |
| **Version** | `1.0.0` |
| **Build** | `1` |
| **Minimum Deployments** | iOS 18.0 |

### Identity Section

```
Display Name: Newsreel
Bundle Identifier: com.onethum.newsreel
Version: 1.0.0
Build: 1
```

### Deployment Info

```
iPhone Deployment Target: iOS 18.0
iPad Deployment Target: iOS 18.0
Supported Destinations: iPhone, iPad
Status Bar Style: Default
Requires Full Screen: No
Supported Interface Orientations:
  - Portrait
  - Landscape Left (optional)
  - Landscape Right (optional)
```

### Frameworks & Libraries

Add these via Swift Package Manager:

1. **Firebase iOS SDK**
   - URL: `https://github.com/firebase/firebase-ios-sdk`
   - Products: FirebaseAuth, FirebaseMessaging
   
2. **RevenueCat**
   - URL: `https://github.com/RevenueCat/purchases-ios`
   - Products: RevenueCat

---

## Build Settings

### Signing & Capabilities

**Signing**:
- **Automatically manage signing**: Enabled (for development)
- **Team**: One Thum Software
- **Provisioning Profile**: Xcode Managed Profile

**Capabilities** (add these):
- ✅ Push Notifications
- ✅ In-App Purchase
- ✅ Sign in with Apple (optional)

### Build Settings Tab

Key settings to configure:

| Setting | Value |
|---------|-------|
| **Swift Language Version** | Swift 5 |
| **iOS Deployment Target** | 18.0 |
| **Targeted Device Families** | iPhone, iPad |
| **Supports Mac Designed for iPad** | No (initially) |
| **Build Active Architecture Only** | Yes (Debug), No (Release) |

---

## Info.plist Configuration

### Required Keys

Add these keys to `Info.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- App Identity -->
    <key>CFBundleName</key>
    <string>$(PRODUCT_NAME)</string>
    
    <key>CFBundleDisplayName</key>
    <string>Newsreel</string>
    
    <key>CFBundleIdentifier</key>
    <string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
    
    <key>CFBundleVersion</key>
    <string>1</string>
    
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    
    <!-- Copyright -->
    <key>NSHumanReadableCopyright</key>
    <string>© 2025 One Thum Software. All rights reserved.</string>
    
    <!-- Fonts -->
    <key>UIAppFonts</key>
    <array>
        <string>Outfit-Thin.ttf</string>
        <string>Outfit-ExtraLight.ttf</string>
        <string>Outfit-Light.ttf</string>
        <string>Outfit-Regular.ttf</string>
        <string>Outfit-Medium.ttf</string>
        <string>Outfit-SemiBold.ttf</string>
        <string>Outfit-Bold.ttf</string>
        <string>Outfit-ExtraBold.ttf</string>
        <string>Outfit-Black.ttf</string>
    </array>
    
    <!-- App Configuration -->
    <key>UIApplicationSceneManifest</key>
    <dict>
        <key>UIApplicationSupportsMultipleScenes</key>
        <false/>
        <key>UISceneConfigurations</key>
        <dict>
            <key>UIWindowSceneSessionRoleApplication</key>
            <array>
                <dict>
                    <key>UISceneConfigurationName</key>
                    <string>Default Configuration</string>
                    <key>UISceneDelegateClassName</key>
                    <string>$(PRODUCT_MODULE_NAME).SceneDelegate</string>
                </dict>
            </array>
        </dict>
    </dict>
    
    <!-- Supported Interface Orientations -->
    <key>UISupportedInterfaceOrientations</key>
    <array>
        <string>UIInterfaceOrientationPortrait</string>
        <string>UIInterfaceOrientationLandscapeLeft</string>
        <string>UIInterfaceOrientationLandscapeRight</string>
    </array>
    
    <key>UISupportedInterfaceOrientations~ipad</key>
    <array>
        <string>UIInterfaceOrientationPortrait</string>
        <string>UIInterfaceOrientationPortraitUpsideDown</string>
        <string>UIInterfaceOrientationLandscapeLeft</string>
        <string>UIInterfaceOrientationLandscapeRight</string>
    </array>
    
    <!-- App Transport Security -->
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <false/>
    </dict>
    
    <!-- Privacy Descriptions -->
    <key>NSUserTrackingUsageDescription</key>
    <string>We use tracking to provide personalized news recommendations.</string>
    
    <key>NSPhotoLibraryUsageDescription</key>
    <string>We need access to save story images to your photo library.</string>
</dict>
</plist>
```

---

## Schemes

### Debug Scheme

- **Build Configuration**: Debug
- **Executable**: Newsreel.app
- **Launch automatically**: Yes
- **Environment Variables**:
  - `API_BASE_URL`: `http://localhost:8000` (for local testing)

### Release Scheme

- **Build Configuration**: Release
- **Executable**: Newsreel.app
- **Environment Variables**:
  - `API_BASE_URL`: `https://api.newsreel.app`

---

## Build Phases

Ensure these build phases are configured:

### 1. Dependencies
- Target Dependencies (if any)

### 2. Compile Sources
- All `.swift` files

### 3. Copy Bundle Resources
- Assets.xcassets
- All `.ttf` font files
- GoogleService-Info.plist (Firebase)

### 4. Link Binary With Libraries
- RevenueCat framework
- Firebase frameworks
- System frameworks (automatically linked)

### 5. Embed Frameworks
- RevenueCat (if not using SPM)

---

## Asset Catalog Configuration

### AppIcon.appiconset

Required sizes for iOS 18:

| Size | Usage |
|------|-------|
| 1024x1024 | App Store |
| 180x180 | iPhone 3x |
| 120x120 | iPhone 2x |
| 167x167 | iPad Pro 2x |
| 152x152 | iPad 2x |
| 76x76 | iPad 1x |

**Design Guidelines**:
- No transparency
- No rounded corners (iOS adds them)
- Solid background
- Simple, recognizable icon
- Works at small sizes

### AccentColor

Configure in Assets.xcassets:
- **Light Appearance**: Blue (RGB: 0, 122, 255)
- **Dark Appearance**: Blue (RGB: 10, 132, 255)

---

## Privacy Manifest (Privacy.xcprivacy)

iOS 17+ requires privacy manifest for certain APIs.

Create `Privacy.xcprivacy`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSPrivacyTracking</key>
    <false/>
    
    <key>NSPrivacyCollectedDataTypes</key>
    <array>
        <dict>
            <key>NSPrivacyCollectedDataType</key>
            <string>NSPrivacyCollectedDataTypeEmailAddress</string>
            <key>NSPrivacyCollectedDataTypeLinked</key>
            <true/>
            <key>NSPrivacyCollectedDataTypePurposes</key>
            <array>
                <string>NSPrivacyCollectedDataTypePurposeAppFunctionality</string>
            </array>
        </dict>
    </array>
    
    <key>NSPrivacyAccessedAPITypes</key>
    <array>
        <!-- Declare any required APIs here -->
    </array>
</dict>
</plist>
```

---

## Version Incrementing

### For Bug Fixes (1.0.1, 1.0.2, etc.)
1. Increment **Build** number: 1 → 2
2. Increment patch **Version**: 1.0.0 → 1.0.1

### For Minor Updates (1.1.0, 1.2.0, etc.)
1. Reset **Build** to 1
2. Increment minor **Version**: 1.0.0 → 1.1.0

### For Major Updates (2.0.0, 3.0.0, etc.)
1. Reset **Build** to 1
2. Increment major **Version**: 1.0.0 → 2.0.0

### Automated Version Bumping

Add a build script to automate version bumping:

```bash
#!/bin/bash
# scripts/bump-build.sh

# Increment build number
buildNumber=$(/usr/libexec/PlistBuddy -c "Print CFBundleVersion" "${INFOPLIST_FILE}")
buildNumber=$((buildNumber + 1))
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $buildNumber" "${INFOPLIST_FILE}"

echo "Build number incremented to $buildNumber"
```

---

## App Store Connect Configuration

### App Information

| Field | Value |
|-------|-------|
| **Name** | Newsreel |
| **Subtitle** | AI-Curated News |
| **Primary Language** | English (U.S.) |
| **Category** | News |
| **Secondary Category** | (none) |
| **Content Rights** | Does not contain third-party content |

### Pricing

- **Price**: Free
- **In-App Purchases**: Newsreel Premium ($4.99/month)

### App Privacy

See RevenueCat Setup Guide for privacy declarations.

---

## Testing Configuration

### Unit Tests Target

- Target Name: `NewsreelTests`
- Host Application: Newsreel
- Bundle Identifier: `com.onethum.newsreel.tests`

### UI Tests Target

- Target Name: `NewsreelUITests`
- Target Application: Newsreel
- Bundle Identifier: `com.onethum.newsreel.uitests`

---

## Build for Release Checklist

Before building for App Store submission:

- [ ] Version and build numbers updated
- [ ] All required capabilities enabled
- [ ] Provisioning profile valid
- [ ] App icon added (all sizes)
- [ ] Launch screen configured
- [ ] Privacy manifest included
- [ ] Info.plist complete
- [ ] Fonts registered in Info.plist
- [ ] Firebase configuration file added
- [ ] RevenueCat API keys configured
- [ ] Release scheme selected
- [ ] Code signing identity valid
- [ ] Archive builds successfully
- [ ] No compiler warnings
- [ ] All tests passing

---

## Archive & Upload

### Create Archive

1. Product → Archive
2. Wait for build to complete
3. Organizer window opens

### Validate Archive

1. Select archive
2. Click "Validate App"
3. Choose distribution method: App Store Connect
4. Sign with appropriate certificate
5. Wait for validation

### Upload to App Store Connect

1. Click "Distribute App"
2. Choose App Store Connect
3. Upload
4. Wait for processing

---

## Common Issues

### Issue: Fonts not appearing

**Solution**: Verify all `.ttf` files are:
1. Added to target membership
2. Listed in Info.plist under `UIAppFonts`
3. Spelled exactly correct (case-sensitive)

### Issue: Build number already used

**Solution**: Increment build number in Xcode and re-archive

### Issue: Missing entitlements

**Solution**: Add required capabilities in Signing & Capabilities tab

### Issue: Provisioning profile doesn't match

**Solution**: 
1. Go to Signing & Capabilities
2. Enable "Automatically manage signing"
3. Or download correct profile from Apple Developer

---

## Resources

- **Apple Developer**: https://developer.apple.com/
- **App Store Connect**: https://appstoreconnect.apple.com/
- **Xcode Documentation**: https://developer.apple.com/documentation/xcode

---

**Document Owner**: iOS Lead  
**Last Updated**: October 8, 2025  
**Next Review**: Before first App Store submission

