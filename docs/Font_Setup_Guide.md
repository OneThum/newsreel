# Font Setup Guide for Newsreel

**Last Updated**: October 8, 2025

---

## Overview

Newsreel uses the Outfit font family exclusively. The font files are already located in `/Newsreel App/Newsreel/Fonts/`. This guide explains how to configure them in Xcode.

---

## Font Files

The following Outfit font files are included:

- `Outfit-Thin.ttf` (100)
- `Outfit-ExtraLight.ttf` (200)
- `Outfit-Light.ttf` (300)
- `Outfit-Regular.ttf` (400)
- `Outfit-Medium.ttf` (500)
- `Outfit-SemiBold.ttf` (600)
- `Outfit-Bold.ttf` (700)
- `Outfit-ExtraBold.ttf` (800)
- `Outfit-Black.ttf` (900)

---

## Setup Steps

### 1. Verify Fonts in Xcode Project

1. Open `Newsreel.xcodeproj` in Xcode
2. In the Project Navigator, verify the `Fonts` folder is visible
3. Select each `.ttf` file
4. In the File Inspector (right panel), ensure **Target Membership** shows ✓ **Newsreel**

If fonts are not in the project:
1. Right-click the `Newsreel` folder in Project Navigator
2. Choose **Add Files to "Newsreel"...**
3. Navigate to the `Fonts` folder
4. Select all `.ttf` files
5. Make sure **"Copy items if needed"** is checked
6. Click **Add**

### 2. Add Fonts to Info.plist

The fonts must be registered in `Info.plist`:

1. In Xcode, select the `Newsreel` target
2. Go to the **Info** tab
3. Right-click in the list and choose **Add Row**
4. Add key: `Fonts provided by application` (or `UIAppFonts`)
5. Expand the array and add each font file name:

```
Fonts provided by application (Array)
  Item 0 (String): Outfit-Thin.ttf
  Item 1 (String): Outfit-ExtraLight.ttf
  Item 2 (String): Outfit-Light.ttf
  Item 3 (String): Outfit-Regular.ttf
  Item 4 (String): Outfit-Medium.ttf
  Item 5 (String): Outfit-SemiBold.ttf
  Item 6 (String): Outfit-Bold.ttf
  Item 7 (String): Outfit-ExtraBold.ttf
  Item 8 (String): Outfit-Black.ttf
```

**Alternatively, edit Info.plist as source code:**

1. Right-click `Info.plist` in Project Navigator
2. Choose **Open As** → **Source Code**
3. Add this inside the `<dict>` tag:

```xml
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
```

### 3. Verify Font Installation

After adding fonts to Info.plist, verify they're accessible:

1. **Build and run** the app (⌘R)
2. Use the Font Preview in Xcode:
   - Open `FontSystem.swift`
   - Run the preview to see all font weights
3. Or add this temporary code to print available fonts:

```swift
// In ContentView or NewsreelApp
func listFonts() {
    for family in UIFont.familyNames.sorted() {
        let names = UIFont.fontNames(forFamilyName: family)
        print("Family: \(family) Font names: \(names)")
    }
}

// Call in init() or onAppear()
init() {
    listFonts()
}
```

Look for "Outfit" in the console output.

---

## Usage

### Import FontSystem

```swift
import SwiftUI
// FontSystem.swift provides Font extensions automatically
```

### Basic Usage

```swift
Text("Welcome to Newsreel")
    .font(.displayLarge)  // Outfit Bold 34pt

Text("Story Title")
    .font(.titleLarge)  // Outfit SemiBold 20pt

Text("Body content here")
    .font(.bodyRegular)  // Outfit Regular 15pt

Text("12 min ago")
    .font(.captionRegular)  // Outfit Regular 12pt
```

### Custom Sizes

```swift
Text("Custom")
    .font(.outfit(size: 26, weight: .bold))
```

---

## Font Scale Reference

| Style | Font | Size | Use Case |
|-------|------|------|----------|
| **Display Large** | Bold | 34pt | Page titles |
| **Display Medium** | Bold | 28pt | Section headers |
| **Display Small** | SemiBold | 22pt | Subsection headers |
| **Headline Large** | Bold | 28pt | Major headlines |
| **Headline Medium** | SemiBold | 22pt | Section headlines |
| **Headline Small** | SemiBold | 18pt | Subsection headlines |
| **Title Large** | SemiBold | 20pt | Story card titles |
| **Title Medium** | Medium | 18pt | Article headers |
| **Title Small** | Medium | 16pt | Minor headers |
| **Body Large** | Regular | 17pt | Large body text |
| **Body Regular** | Regular | 15pt | Main content ⭐ |
| **Body Small** | Regular | 13pt | Secondary content |
| **Body Emphasized** | Medium | 15pt | Emphasized text |
| **Caption Large** | Regular | 13pt | Large captions |
| **Caption Regular** | Regular | 12pt | Metadata, timestamps |
| **Caption Small** | Regular | 11pt | Tiny captions |
| **Label Large** | Medium | 15pt | Large labels/tags |
| **Label Regular** | Medium | 13pt | Standard labels |
| **Label Small** | Medium | 11pt | Small badges |
| **Button Large** | SemiBold | 17pt | Primary buttons |
| **Button Regular** | SemiBold | 15pt | Standard buttons |
| **Button Small** | SemiBold | 13pt | Compact buttons |

---

## Story Card Typography Example

```swift
struct StoryCardView: View {
    let story: Story
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Metadata header
            HStack {
                Text(story.category)
                    .font(.labelSmall)  // Outfit Medium 11pt
                    .foregroundColor(.blue)
                
                Spacer()
                
                Text("\(story.publishedAt) · \(story.sourceCount) sources")
                    .font(.captionRegular)  // Outfit Regular 12pt
                    .foregroundColor(.secondary)
            }
            
            // Story title
            Text(story.title)
                .font(.titleLarge)  // Outfit SemiBold 20pt
                .lineLimit(3)
            
            // Summary
            Text(story.summary)
                .font(.bodyRegular)  // Outfit Regular 15pt
                .foregroundColor(.secondary)
                .lineSpacing(4)
            
            // Breaking badge (if applicable)
            if story.isBreaking {
                Text("BREAKING")
                    .font(.labelSmall)  // Outfit Medium 11pt
                    .foregroundColor(.white)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.red)
                    .cornerRadius(4)
            }
            
            Divider()
            
            // Action buttons
            HStack {
                Button("Like") {
                    // Action
                }
                .font(.buttonSmall)  // Outfit SemiBold 13pt
                
                Button("Save") {
                    // Action
                }
                .font(.buttonSmall)
                
                Spacer()
                
                Button("View Sources") {
                    // Action
                }
                .font(.buttonSmall)
            }
        }
        .padding()
        .background(.ultraThinMaterial)
        .cornerRadius(16)
    }
}
```

---

## Troubleshooting

### Fonts Not Appearing

**Problem**: Text shows system font instead of Outfit

**Solutions**:
1. ✅ Verify fonts are added to project with target membership
2. ✅ Confirm `UIAppFonts` in Info.plist has all font filenames
3. ✅ Verify exact filename spelling (case-sensitive!)
4. ✅ Clean build folder (Shift + Cmd + K)
5. ✅ Delete app from simulator/device
6. ✅ Rebuild project (Cmd + B)

### Wrong Font Weight

**Problem**: Text appears in wrong weight (e.g., Regular instead of Bold)

**Solutions**:
1. Check font name spelling in FontSystem.swift
2. Verify the exact PostScript name:
   ```swift
   // Temporarily print font names
   Text("Test").font(.custom("Outfit-Bold", size: 20))
   ```
3. Use Font Book app on Mac to verify PostScript names

### Preview Not Working

**Problem**: Xcode previews show system font

**Solutions**:
1. Fonts must be registered in Info.plist to work in previews
2. Clean and rebuild
3. Restart Xcode
4. Try building to simulator instead of preview

---

## Font Licensing

**Outfit Font License**: SIL Open Font License 1.1

The Outfit font is free to use in personal and commercial projects. No attribution required, but appreciated.

- **Source**: Google Fonts
- **Designer**: Rodrigo Fuenzalida
- **License**: https://scripts.sil.org/OFL

---

## Additional Resources

- **Outfit on Google Fonts**: https://fonts.google.com/specimen/Outfit
- **SwiftUI Custom Fonts**: https://developer.apple.com/documentation/swiftui/applying-custom-fonts-to-text
- **FontSystem.swift**: Complete font extension reference

---

**Document Owner**: iOS Lead  
**Last Updated**: October 8, 2025  
**Next Review**: After font implementation

