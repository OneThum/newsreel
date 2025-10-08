# Newsreel Design System

**Last Updated**: October 8, 2025

---

## Overview

Newsreel uses a beautiful "Liquid Glass" design system adapted from Ticka Currencies, featuring:
- **Outfit font family** - Modern, readable typography
- Apple-inspired gradient backgrounds
- Automatic dark mode support
- Smooth, dreamy blur effects
- Blue and teal color palette
- Clean, modern aesthetics

---

## Typography System

### Outfit Font Family

Newsreel uses the Outfit font exclusively throughout the app. Outfit is a modern, geometric sans-serif typeface that provides excellent readability and a contemporary look.

#### Available Weights

- Thin (100)
- Extra Light (200)
- Light (300)
- Regular (400)
- Medium (500)
- Semi Bold (600)
- Bold (700)
- Extra Bold (800)
- Black (900)

### Font Scale

The app uses a predefined font scale accessible via `Font` extensions:

#### Display Fonts
```swift
.font(.displayLarge)    // 34pt, Bold - Page titles
.font(.displayMedium)   // 28pt, Bold - Section headers
.font(.displaySmall)    // 22pt, SemiBold - Subsection headers
```

#### Headlines
```swift
.font(.headlineLarge)   // 28pt, Bold
.font(.headlineMedium)  // 22pt, SemiBold
.font(.headlineSmall)   // 18pt, SemiBold
```

#### Titles (Story cards, article headers)
```swift
.font(.titleLarge)      // 20pt, SemiBold
.font(.titleMedium)     // 18pt, Medium
.font(.titleSmall)      // 16pt, Medium
```

#### Body Text (Main content)
```swift
.font(.bodyLarge)       // 17pt, Regular
.font(.bodyRegular)     // 15pt, Regular (Most common)
.font(.bodySmall)       // 13pt, Regular
.font(.bodyEmphasized)  // 15pt, Medium (Emphasized)
```

#### Captions (Metadata, timestamps)
```swift
.font(.captionLarge)    // 13pt, Regular
.font(.captionRegular)  // 12pt, Regular
.font(.captionSmall)    // 11pt, Regular
.font(.captionEmphasized) // 12pt, Medium
```

#### Labels (Tags, badges)
```swift
.font(.labelLarge)      // 15pt, Medium
.font(.labelRegular)    // 13pt, Medium
.font(.labelSmall)      // 11pt, Medium
```

#### Buttons
```swift
.font(.buttonLarge)     // 17pt, SemiBold
.font(.buttonRegular)   // 15pt, SemiBold
.font(.buttonSmall)     // 13pt, SemiBold
```

### Custom Font Usage

For specific needs, use the custom outfit function:

```swift
Text("Custom Text")
    .font(.outfit(size: 24, weight: .semiBold))
```

### Typography Examples

```swift
// Story card title
Text(story.title)
    .font(.titleLarge)  // 20pt, SemiBold

// Story summary
Text(story.summary)
    .font(.bodyRegular)  // 15pt, Regular
    .foregroundColor(.secondary)

// Timestamp and source count
Text("15m ago · 6 sources")
    .font(.captionRegular)  // 12pt, Regular
    .foregroundColor(.secondary)

// Breaking news badge
Text("BREAKING")
    .font(.labelSmall)  // 11pt, Medium
    .foregroundColor(.red)

// Button text
Text("View Sources")
    .font(.buttonRegular)  // 15pt, SemiBold
```

---

## Background System

### AppBackground.swift

The app uses a mesh gradient background system with three main components:

1. **AppBackgroundView** - Main gradient with blur effect
2. **MeshGradientBackground** - Light/dark mode gradient system
3. **SheetBackgroundView** - Simplified background for modal sheets

### Color Palette

#### Light Mode
- **Base**: Light blue-gray gradient (rgb: 0.92, 0.94, 0.98 → 0.82, 0.86, 0.94)
- **Accent 1**: Saturated blue (rgb: 0.6, 0.75, 0.92)
- **Accent 2**: Vibrant teal (rgb: 0.65, 0.85, 0.85)
- **Accent 3**: Central blue for depth (rgb: 0.7, 0.8, 0.92)

#### Dark Mode
- **Base**: Rich dark blue-gray gradient (rgb: 0.05, 0.05, 0.1 → 0.08, 0.08, 0.15)
- **Accent 1**: Deep blue (rgb: 0.0, 0.3, 0.6)
- **Accent 2**: Subtle teal (rgb: 0.086, 0.4, 0.4)
- **Accent 3**: Mid-tone blue (rgb: 0.0, 0.25, 0.5)

---

## Usage

### Apply to Main Views

Use the `.withAppBackground()` modifier on your root views:

```swift
// FeedView.swift

import SwiftUI

struct FeedView: View {
    @StateObject private var viewModel = FeedViewModel()
    
    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVStack(spacing: 16) {
                    ForEach(viewModel.stories) { story in
                        StoryCardView(story: story)
                    }
                }
                .padding()
            }
            .navigationTitle("Newsreel")
        }
        .withAppBackground()  // ← Apply gradient background
    }
}
```

### Apply to Modal Sheets

Use the `.withSheetBackground()` modifier for sheets and modal views:

```swift
// StoryDetailView.swift

struct StoryDetailView: View {
    let story: Story
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Story content
                Text(story.title)
                    .font(.title)
                
                Text(story.summary)
                    .font(.body)
            }
            .padding()
        }
        .withSheetBackground()  // ← Apply sheet background
    }
}
```

### Manual Background Application

If you need more control, use the background views directly:

```swift
struct CustomView: View {
    var body: some View {
        ZStack {
            // Apply background manually
            AppBackgroundView()
                .ignoresSafeArea()
            
            // Your content
            VStack {
                Text("Content")
            }
        }
    }
}
```

---

## Content Styling Tips

### Text Colors

When using the gradient background:

```swift
// Primary text (high contrast)
Text("Heading")
    .foregroundColor(.primary)

// Secondary text (medium contrast)
Text("Subheading")
    .foregroundColor(.secondary)

// Always use semantic colors - they adapt to light/dark mode
```

### Card Backgrounds

Story cards should have translucent backgrounds to show the gradient:

```swift
struct StoryCardView: View {
    var body: some View {
        VStack {
            // Card content
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(.ultraThinMaterial)  // Translucent glass effect
        )
        .shadow(color: .black.opacity(0.1), radius: 10, y: 5)
    }
}
```

### Material Effects

Use SwiftUI materials for depth:

```swift
// Ultra thin - subtle glass effect
.background(.ultraThinMaterial)

// Thin - more visible
.background(.thinMaterial)

// Regular - standard glass
.background(.regularMaterial)

// Thick - prominent glass
.background(.thickMaterial)
```

---

## Best Practices

### 1. Always Use Semantic Colors

✅ **Good**:
```swift
.foregroundColor(.primary)
.foregroundColor(.secondary)
.background(.ultraThinMaterial)
```

❌ **Bad**:
```swift
.foregroundColor(.black)  // Won't adapt to dark mode
.foregroundColor(.white)  // Won't adapt to light mode
```

### 2. Maintain Visual Hierarchy

- **Primary content**: `.ultraThinMaterial` or `.thinMaterial`
- **Secondary content**: `.regularMaterial`
- **Emphasis**: `.thickMaterial` or solid colors with opacity

### 3. Test Both Modes

Always test your UI in both light and dark mode:

```swift
#Preview {
    FeedView()
        .withAppBackground()
        .preferredColorScheme(.light)
}

#Preview("Dark Mode") {
    FeedView()
        .withAppBackground()
        .preferredColorScheme(.dark)
}
```

### 4. Avoid Heavy Backgrounds

The gradient already has depth - keep content backgrounds simple:

```swift
// ✅ Good - lets gradient shine through
.background(.ultraThinMaterial)

// ❌ Bad - hides beautiful gradient
.background(Color.white)
.background(Color.black)
```

---

## Animation Guidelines

### Smooth Transitions

The gradient creates a dreamy atmosphere - match it with smooth animations:

```swift
// Story card appearing
.transition(.scale.combined(with: .opacity))
.animation(.spring(response: 0.6, dampingFraction: 0.8), value: isVisible)

// Flip animation (for source cards)
.rotation3DEffect(.degrees(isFlipped ? 180 : 0), axis: (x: 0, y: 1, z: 0))
.animation(.spring(response: 0.6, dampingFraction: 0.8), value: isFlipped)
```

### Haptic Feedback

Enhance interactions with haptics:

```swift
import UIKit

extension UIImpactFeedbackGenerator {
    static func light() {
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
    }
    
    static func medium() {
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
    }
    
    static func heavy() {
        UIImpactFeedbackGenerator(style: .heavy).impactOccurred()
    }
}

// Usage
Button("Like") {
    UIImpactFeedbackGenerator.light()
    viewModel.likeStory()
}
```

---

## Accessibility

### Support Dynamic Type

Always use dynamic type for text:

```swift
Text("Headline")
    .font(.title)  // ✅ Scales with user preference

Text("Headline")
    .font(.system(size: 24))  // ❌ Fixed size
```

### Maintain Contrast

Ensure sufficient contrast on the gradient background:

```swift
// Test contrast with Accessibility Inspector in Xcode
// Minimum ratios:
// - Normal text: 4.5:1
// - Large text: 3:1
```

### VoiceOver Support

Add accessibility labels to interactive elements:

```swift
Button(action: likeStory) {
    Image(systemName: isLiked ? "heart.fill" : "heart")
}
.accessibilityLabel(isLiked ? "Unlike story" : "Like story")
```

---

## Performance

### Blur Radius

The background uses `blur(radius: 30)` which is optimized for performance:

- Creates smooth, dreamy effect
- Hides any aliasing in gradients
- Minimal performance impact on modern iOS devices

### Lazy Loading

Use lazy loading for scrolling views with the background:

```swift
ScrollView {
    LazyVStack {
        // Story cards
    }
}
.withAppBackground()
```

---

## Examples

### Main Feed

```swift
struct FeedView: View {
    @StateObject private var viewModel = FeedViewModel()
    
    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVStack(spacing: 16) {
                    ForEach(viewModel.stories) { story in
                        StoryCardView(story: story)
                            .containerRelativeFrame(.horizontal, count: 1, spacing: 0)
                            .scrollTransition { content, phase in
                                content
                                    .opacity(phase.isIdentity ? 1 : 0.8)
                                    .scaleEffect(phase.isIdentity ? 1 : 0.95)
                            }
                    }
                }
                .padding()
            }
            .navigationTitle("Newsreel")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Profile") {
                        showProfile = true
                    }
                }
            }
        }
        .withAppBackground()
    }
}
```

### Story Card

```swift
struct StoryCardView: View {
    let story: Story
    @State private var isFlipped = false
    
    var body: some View {
        ZStack {
            // Card content
            VStack(alignment: .leading, spacing: 12) {
                Text(story.title)
                    .font(.title3)
                    .fontWeight(.bold)
                
                Text(story.summary)
                    .font(.body)
                    .foregroundColor(.secondary)
            }
            .padding()
        }
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(.ultraThinMaterial)
        )
        .shadow(color: .black.opacity(0.1), radius: 10, y: 5)
    }
}
```

### Profile Sheet

```swift
struct ProfileView: View {
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationStack {
            List {
                Section {
                    Text("Premium")
                }
                
                Section("Preferences") {
                    Toggle("Breaking News", isOn: .constant(true))
                    Toggle("Push Notifications", isOn: .constant(true))
                }
            }
            .scrollContentBackground(.hidden)  // Hide default list background
            .navigationTitle("Profile")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .withSheetBackground()
    }
}
```

---

## Migration Guide

If updating existing views to use the new background:

1. Add `AppBackground.swift` to your project
2. Import SwiftUI
3. Apply `.withAppBackground()` to root views
4. Apply `.withSheetBackground()` to modal sheets
5. Replace solid backgrounds with materials
6. Test in both light and dark mode
7. Verify text contrast with Accessibility Inspector

---

## Support

For questions about the design system:
- **iOS Lead**: Design implementation questions
- **Reference App**: Ticka Currencies (same background system)

---

**Document Owner**: iOS Lead  
**Last Updated**: October 8, 2025  
**Next Review**: After initial implementation

