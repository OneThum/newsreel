# iOS Development Standards Guide

## Apple HIG Compliance & Modern iOS Best Practices

**Purpose**: This document provides comprehensive standards for building iOS apps that comply with Apple's Human Interface Guidelines and modern iOS design patterns from the start. Following these standards ensures your app will be accessible, performant, and feel native to iOS users.

**Target Audience**: iOS Engineers, Product Designers, Technical Leads
 **Last Updated**: November 2025
 **iOS Version**: iOS 17+

------

## 📚 Table of Contents

1. [Core Principles](https://claude.ai/chat/55c4616c-52e6-4c9d-a107-21a8764de7c4#core-principles)
2. [System Integration](https://claude.ai/chat/55c4616c-52e6-4c9d-a107-21a8764de7c4#system-integration)
3. [Visual Design Foundation](https://claude.ai/chat/55c4616c-52e6-4c9d-a107-21a8764de7c4#visual-design-foundation)
4. [Typography & Dynamic Type](https://claude.ai/chat/55c4616c-52e6-4c9d-a107-21a8764de7c4#typography--dynamic-type)
5. [Accessibility Requirements](https://claude.ai/chat/55c4616c-52e6-4c9d-a107-21a8764de7c4#accessibility-requirements)
6. [Component Architecture](https://claude.ai/chat/55c4616c-52e6-4c9d-a107-21a8764de7c4#component-architecture)
7. [Animation & Motion](https://claude.ai/chat/55c4616c-52e6-4c9d-a107-21a8764de7c4#animation--motion)
8. [Navigation Patterns](https://claude.ai/chat/55c4616c-52e6-4c9d-a107-21a8764de7c4#navigation-patterns)
9. [Forms & Input](https://claude.ai/chat/55c4616c-52e6-4c9d-a107-21a8764de7c4#forms--input)
10. [Performance Standards](https://claude.ai/chat/55c4616c-52e6-4c9d-a107-21a8764de7c4#performance-standards)
11. [Testing Requirements](https://claude.ai/chat/55c4616c-52e6-4c9d-a107-21a8764de7c4#testing-requirements)

------

## Core Principles

### Development Philosophy

**Build with these priorities in order:**

1. **Accessibility First** - Every user must be able to use your app
2. **System Integration** - Respect iOS conventions and system settings
3. **Performance** - Smooth, responsive interactions are non-negotiable
4. **Visual Polish** - Clean, consistent design that feels native
5. **Brand Identity** - Express your brand within iOS conventions

### The Three Rules

1. **Never fight the system** - Use system components and conventions
2. **Never assume ability** - Support all accessibility features
3. **Never hard-code dimensions** - Let content and settings determine layout

------

## System Integration

### ✅ REQUIRED: Navigation & Tab Bars

#### Navigation Bar Configuration

**DO THIS:**

```swift
NavigationStack {
    ContentView()
        .navigationTitle("Screen Title")
        .navigationBarTitleDisplayMode(.automatic)
        .toolbarBackground(.visible, for: .navigationBar)
        .toolbarBackground(.bar, for: .navigationBar)
        .toolbarColorScheme(.automatic, for: .navigationBar)
}
```

**NEVER THIS:**

```swift
// ❌ DON'T hide navigation bar backgrounds
.toolbarBackground(.hidden, for: .navigationBar)

// ❌ DON'T use deprecated NavigationView
NavigationView { }
```

**Why**: Navigation bars need proper material backing for:

- Readability over varied content
- System blur effects
- High contrast mode support
- Reduce Transparency setting compliance

------

#### Tab Bar Configuration

**DO THIS:**

```swift
// In your App init or TabView init
init() {
    let appearance = UITabBarAppearance()
    appearance.backgroundEffect = UIBlurEffect(style: .systemMaterial)
    UITabBar.appearance().standardAppearance = appearance
    UITabBar.appearance().scrollEdgeAppearance = appearance
}

TabView {
    ContentView()
        .tabItem {
            Label("Home", systemImage: "house.fill")
        }
}
```

**NEVER THIS:**

```swift
// ❌ DON'T make tab bars transparent
let appearance = UITabBarAppearance()
appearance.configureWithTransparentBackground()
```

**Why**: Tab bars must have system material backing for:

- Touch target clarity
- Visual hierarchy
- Accessibility
- System setting compliance

------

#### Navigation Architecture

**DO THIS:**

```swift
// Use NavigationStack (iOS 16+)
NavigationStack {
    List {
        NavigationLink("Detail View") {
            DetailView()
        }
    }
}
```

**NEVER THIS:**

```swift
// ❌ DON'T use deprecated NavigationView
NavigationView {
    List { }
}
```

**Requirements**:

- All navigation must use `NavigationStack`
- Set descriptive `navigationTitle` on every view
- Use `.inline` or `.large` display mode appropriately
- Ensure back buttons have contextual labels

------

### ✅ REQUIRED: System Settings Compliance

#### Settings You MUST Support

| Setting             | SwiftUI Environment                               | Implementation Required                     |
| ------------------- | ------------------------------------------------- | ------------------------------------------- |
| Dynamic Type        | `@Environment(\.sizeCategory)`                    | Use semantic text styles, never fixed sizes |
| Reduce Motion       | `@Environment(\.accessibilityReduceMotion)`       | Disable/minimize animations                 |
| Reduce Transparency | `@Environment(\.accessibilityReduceTransparency)` | Replace materials with solid colors         |
| Increase Contrast   | `@Environment(\.colorSchemeContrast)`             | Use higher contrast colors                  |
| Dark Mode           | `@Environment(\.colorScheme)`                     | Support both light and dark                 |
| Voice Control       | Built-in with proper labels                       | Use descriptive accessibility labels        |

#### Implementation Pattern

```swift
struct AccessibilityAwareView: View {
    @Environment(\.sizeCategory) var sizeCategory
    @Environment(\.accessibilityReduceMotion) var reduceMotion
    @Environment(\.accessibilityReduceTransparency) var reduceTransparency
    @Environment(\.colorSchemeContrast) var contrast
    
    var body: some View {
        VStack {
            Text("Content")
                .font(.body) // Scales automatically
        }
        .background(
            reduceTransparency 
                ? Color(.secondarySystemBackground)
                : .ultraThinMaterial
        )
        .animation(reduceMotion ? .none : .spring(), value: someState)
    }
}
```

------

## Visual Design Foundation

### ✅ REQUIRED: Color System

#### Use Asset Catalogs for All Colors

**DO THIS:**

1. Create `Colors.xcassets` in your project
2. Add color sets with proper variants:
   - **Appearances**: Any, Light, Dark
   - **Contrast**: Standard, High Contrast
   - **Gamut**: sRGB, Display P3
3. Reference colors semantically:

```swift
// In your DesignSystem.swift
extension Color {
    // Brand colors
    static let brandPrimary = Color("BrandPrimary")
    static let brandAccent = Color("BrandAccent")
    
    // Semantic colors
    static let success = Color("Success")
    static let error = Color("Error")
    static let warning = Color("Warning")
    static let info = Color("Info")
}
```

**NEVER THIS:**

```swift
// ❌ DON'T hard-code RGB values
Color(red: 0.2, green: 0.4, blue: 0.8)
```

**Why**: Asset catalog colors automatically support:

- Dark mode variants
- High contrast variants
- Wide color gamut (Display P3)
- Dynamic system color adaptation

------

#### Semantic Color Usage

**DO THIS:**

```swift
// Separate brand identity from semantic meaning
struct Colors {
    // Brand Colors (for logos, headers, brand moments)
    static let brandBlue = Color("BrandBlue")
    static let brandRed = Color("BrandRed")
    
    // Semantic Colors (for interactive elements)
    static let primary = Color("AccentColor") // System tint
    static let success = Color.green
    static let error = Color.red  // Different from brandRed
    static let warning = Color.orange
}

// Use appropriately
Button("Submit") { }
    .foregroundStyle(Colors.primary)

Text("Error message")
    .foregroundStyle(Colors.error)
```

**Why**: Users associate colors with meaning:

- Red = error/danger
- Green = success/go
- Orange/Yellow = warning
- Blue = primary action

Don't confuse them by using brand colors for semantic purposes.

------

#### Color Contrast Requirements

**WCAG AA Standard (Minimum)**:

- Normal text: 4.5:1 contrast ratio
- Large text (18pt+): 3:1 contrast ratio
- UI components: 3:1 contrast ratio

**DO THIS:**

```swift
// Design System with compliant opacity values
enum Opacity {
    static let minimum: CGFloat = 0.15  // WCAG AA compliant
    static let low: CGFloat = 0.2
    static let medium: CGFloat = 0.3
    static let high: CGFloat = 0.5
}

// Use in overlays
Color.blue.opacity(Opacity.minimum)  // ✅ 0.15 minimum
```

**NEVER THIS:**

```swift
// ❌ DON'T use very low opacity that fails contrast
Color.blue.opacity(0.03)  // Fails WCAG
Color.white.opacity(0.05) // Fails WCAG
Color.black.opacity(0.1)  // Fails WCAG
```

**Tools for Testing**:

- Xcode Accessibility Inspector
- Color contrast analyzers
- Test with Increase Contrast enabled

------

### ✅ REQUIRED: Material & Background System

#### System Materials (Not Custom Opacity)

**DO THIS:**

```swift
// Use system materials
RoundedRectangle(cornerRadius: 12)
    .fill(.ultraThinMaterial)

RoundedRectangle(cornerRadius: 12)
    .fill(.thinMaterial)

RoundedRectangle(cornerRadius: 12)
    .fill(.regularMaterial)
```

**With Accessibility Fallback:**

```swift
@Environment(\.accessibilityReduceTransparency) var reduceTransparency

RoundedRectangle(cornerRadius: 12)
    .fill(
        reduceTransparency 
            ? Color(.secondarySystemBackground)
            : .ultraThinMaterial
    )
```

**NEVER THIS:**

```swift
// ❌ DON'T use custom opacity instead of materials
Color.white.opacity(0.6)  // Doesn't respect Reduce Transparency
Color.black.opacity(0.3)  // Doesn't adapt to dark mode
```

**Why**: System materials automatically:

- Adapt to light/dark mode
- Respect Reduce Transparency setting
- Provide consistent vibrancy
- Blur underlying content appropriately

------

#### Background Hierarchy

**DO THIS:**

```swift
// Clear hierarchy using system colors
VStack {
    // Level 1: Base
    Color(.systemBackground)
    
    // Level 2: Grouped content
    Color(.secondarySystemBackground)
    
    // Level 3: Tertiary grouped content
    Color(.tertiarySystemBackground)
}
```

**Design Token System:**

```swift
struct DesignSystem {
    enum BackgroundLevel {
        case base      // .systemBackground
        case elevated  // .secondarySystemBackground
        case card      // .tertiarySystemBackground or .ultraThinMaterial
    }
}
```

**Avoid**: Heavy branded backgrounds that:

- Reduce content readability
- Create contrast issues
- Distract from primary content
- Don't adapt to dark mode well

------

## Typography & Dynamic Type

### ✅ REQUIRED: Semantic Text Styles

#### Use Only Semantic Styles

**DO THIS:**

```swift
Text("Title")
    .font(.title)

Text("Heading")
    .font(.title2)

Text("Body text")
    .font(.body)

Text("Caption")
    .font(.caption)
```

**NEVER THIS:**

```swift
// ❌ DON'T use fixed point sizes
Text("Title")
    .font(.system(size: 24))

Text("Body")
    .font(.system(size: 16))
```

**Complete Mapping:**

| Point Size | Semantic Style | Use Case               |
| ---------- | -------------- | ---------------------- |
| 11pt       | `.caption2`    | Fine print, legal text |
| 12pt       | `.caption`     | Secondary descriptions |
| 13pt       | `.footnote`    | Footnotes, timestamps  |
| 14pt       | `.subheadline` | Section labels         |
| 15pt       | `.callout`     | Emphasized body text   |
| 16pt       | `.body`        | Primary body text      |
| 17pt       | `.body`        | Default body text      |
| 20pt       | `.title3`      | Tertiary headings      |
| 22pt       | `.title2`      | Secondary headings     |
| 28pt       | `.title`       | Primary headings       |
| 34pt       | `.largeTitle`  | Large emphasis         |

------

#### Dynamic Type Support

**DO THIS:**

```swift
struct ProperTextView: View {
    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.md) {
            Text("Dynamic Headline")
                .font(.title2.weight(.bold))
            
            Text("Body content that scales with user preferences")
                .font(.body)
        }
        .padding()
    }
}
```

**Test With All Sizes:**

- xSmall
- Small
- Medium (default)
- Large
- xLarge
- xxLarge
- xxxLarge (Accessibility)

**Requirements**:

- Text must remain readable at all sizes
- Layout must not break at extreme sizes
- Multi-line text must wrap properly
- Truncation should use `...` or `lineLimit()`

------

#### Custom Fonts

**If using custom fonts:**

```swift
// Register custom font properly
extension Font {
    static func customFont(_ style: Font.TextStyle, weight: Font.Weight = .regular) -> Font {
        // Scale with Dynamic Type
        let size = UIFont.preferredFont(forTextStyle: style.uiFontTextStyle).pointSize
        return .custom("YourFontName", size: size)
            .weight(weight)
    }
}

// Usage
Text("Branded Text")
    .font(.customFont(.headline, weight: .bold))
```

**Requirements**:

- Must scale with Dynamic Type
- Must support all font weights
- Fallback to system font if unavailable
- Ensure legibility at all sizes

------

### ✅ REQUIRED: Interactive Element Sizing

#### Never Fix Button Heights

**DO THIS:**

```swift
// Spacing token system
enum Spacing {
    static let xs: CGFloat = 4
    static let sm: CGFloat = 8
    static let md: CGFloat = 16
    static let lg: CGFloat = 24
    static let xl: CGFloat = 32
}

// Button with padding (not fixed height)
Button("Action") {
    action()
}
.padding(.horizontal, Spacing.lg)
.padding(.vertical, Spacing.md)
.background(Color.accentColor)
.foregroundStyle(.white)
.clipShape(RoundedRectangle(cornerRadius: 12))
```

**NEVER THIS:**

```swift
// ❌ DON'T fix button heights
Button("Action") { }
    .frame(height: 44)  // Breaks with Dynamic Type

Button("Action") { }
    .frame(height: 56)  // Breaks with Dynamic Type
```

**Why**: Fixed heights:

- Don't scale with Dynamic Type
- May cut off text at larger sizes
- Violate accessibility guidelines
- Create inconsistent touch targets

------

#### Minimum Touch Target Size

**Requirements**:

- **Minimum**: 44x44 points (HIG requirement)
- **Recommended**: 48x48 points
- **Ideal**: 56x56 points for primary actions

**DO THIS:**

```swift
Button("Tap Me") {
    action()
}
.padding(.horizontal, 20)
.padding(.vertical, 12)
// This creates adequate touch target size
```

**Testing**:

```swift
// Visual debug overlay for touch targets
#if DEBUG
extension View {
    func debugTouchTarget() -> some View {
        self.overlay(
            GeometryReader { geo in
                let isValid = geo.size.width >= 44 && geo.size.height >= 44
                Rectangle()
                    .stroke(isValid ? Color.green : Color.red, lineWidth: 2)
            }
        )
    }
}
#endif
```

------

## Accessibility Requirements

### ✅ REQUIRED: Screen Reader Support

#### VoiceOver Labels

**DO THIS:**

```swift
Button {
    toggleFavorite()
} label: {
    Image(systemName: isFavorite ? "heart.fill" : "heart")
}
.accessibilityLabel(isFavorite ? "Remove from favorites" : "Add to favorites")
.accessibilityHint("Double tap to toggle")

// For decorative elements
Image("background-pattern")
    .accessibilityHidden(true)
```

**Requirements**:

- Every interactive element must have a clear label
- Labels should describe the result, not the control
- Use hints sparingly for non-obvious actions
- Hide purely decorative elements

------

#### Semantic Grouping

**DO THIS:**

```swift
// Group related elements
VStack {
    Text("Progress")
        .font(.headline)
    ProgressView(value: 0.7)
    Text("70% complete")
        .font(.caption)
}
.accessibilityElement(children: .combine)
.accessibilityLabel("Progress: 70% complete")

// Helper for convenience
extension View {
    func accessibilityGroup(label: String, hint: String? = nil) -> some View {
        self
            .accessibilityElement(children: .combine)
            .accessibilityLabel(label)
            .if(hint != nil) { view in
                view.accessibilityHint(hint!)
            }
    }
}
```

**NEVER THIS:**

```swift
// ❌ DON'T let screen readers read every sub-element separately
VStack {
    Text("Progress")  // Announced separately
    ProgressView(value: 0.7)  // Announced separately
    Text("70%")  // Announced separately
}
```

------

#### Voice Control Support

**DO THIS:**

```swift
Button("Submit Form") {
    submit()
}
.accessibilityIdentifier("Submit Form") // Natural language

Image(systemName: "plus")
    .accessibilityLabel("Add item")  // Natural language command
```

**NEVER THIS:**

```swift
// ❌ DON'T use programmatic identifiers
.accessibilityIdentifier("submit_button")
.accessibilityIdentifier("btn_add_item")
```

**Why**: Voice Control users say natural commands like:

- "Tap Submit Form"
- "Tap Add item"

Not programming variables like "tap submit underscore button".

------

#### Accessibility Actions

**DO THIS:**

```swift
List {
    ForEach(items) { item in
        ItemRow(item: item)
            .accessibilityElement(children: .combine)
            .accessibilityLabel(item.title)
            .accessibilityAction(named: "Favorite") {
                toggleFavorite(item)
            }
            .accessibilityAction(named: "Share") {
                share(item)
            }
    }
}
```

**Why**: Custom actions allow screen reader users to access all functionality without navigating complex UI.

------

### ✅ REQUIRED: Dynamic Type Testing

#### Test Matrix

Test your app at these sizes:

| Size     | User Impact   | Testing Priority |
| -------- | ------------- | ---------------- |
| xSmall   | Uncommon      | Low              |
| Small    | Uncommon      | Low              |
| Medium   | Default       | High             |
| Large    | Common        | High             |
| xLarge   | Common        | High             |
| xxLarge  | Less common   | Medium           |
| xxxLarge | Accessibility | **Critical**     |

**How to Test**:

1. Settings → Accessibility → Display & Text Size → Larger Text
2. Enable "Larger Accessibility Sizes"
3. Test at XXXL (maximum size)

------

#### Common Issues & Solutions

**Problem: Text Truncation**

```swift
// ❌ BAD
Text("Long text that might truncate...")
    .lineLimit(1)

// ✅ GOOD
Text("Long text that wraps to multiple lines")
    .lineLimit(nil) // or .lineLimit(3...5)
```

**Problem: Fixed Layouts**

```swift
// ❌ BAD
HStack {
    Text("Label")
        .frame(width: 100)
    Text("Value")
}

// ✅ GOOD
@Environment(\.sizeCategory) var sizeCategory

if sizeCategory.isAccessibilityCategory {
    VStack(alignment: .leading) {
        Text("Label")
        Text("Value")
    }
} else {
    HStack {
        Text("Label")
        Text("Value")
    }
}
```

**Problem: Overlapping Content**

```swift
// ❌ BAD
.padding(8) // Fixed padding

// ✅ GOOD
@ScaledMetric var padding: CGFloat = 8
// Scales automatically with Dynamic Type
.padding(padding)
```

------

## Component Architecture

### ✅ REQUIRED: Card Design System

#### Standardized Card Styles

**DO THIS:**

```swift
// Design System
struct CardStyle {
    let cornerRadius: CGFloat
    let padding: CGFloat
    let shadow: ShadowStyle
    let background: Background
    
    static let standard = CardStyle(
        cornerRadius: 16,
        padding: 16,
        shadow: .elevated,
        background: .material(.ultraThinMaterial)
    )
    
    static let compact = CardStyle(
        cornerRadius: 12,
        padding: 8,
        shadow: .elevated,
        background: .material(.ultraThinMaterial)
    )
    
    static let prominent = CardStyle(
        cornerRadius: 16,
        padding: 24,
        shadow: .floating,
        background: .material(.regularMaterial)
    )
}

// ViewModifier for application
extension View {
    func card(style: CardStyle = .standard) -> some View {
        self
            .padding(style.padding)
            .background(style.background)
            .clipShape(RoundedRectangle(cornerRadius: style.cornerRadius))
            .applyShadow(style.shadow)
    }
}

// Usage
VStack {
    Text("Card Content")
}
.card()  // Uses standard style
```

**Requirements**:

- Use only 2-3 card styles maximum
- Corner radius: 12pt or 16pt
- Padding: 8pt, 16pt, or 24pt
- Background: System materials with accessibility fallback
- Shadows: Simple and consistent

------

#### Shadow System

**DO THIS:**

```swift
enum ShadowStyle {
    case elevated  // For cards and raised content
    case floating  // For sheets and prominent UI
    
    var config: (color: Color, radius: CGFloat, x: CGFloat, y: CGFloat) {
        switch self {
        case .elevated:
            return (.black.opacity(0.1), 8, 0, 4)
        case .floating:
            return (.black.opacity(0.15), 16, 0, 8)
        }
    }
}

extension View {
    func applyShadow(_ style: ShadowStyle) -> some View {
        let config = style.config
        return self.shadow(
            color: config.color,
            radius: config.radius,
            x: config.x,
            y: config.y
        )
    }
}
```

**NEVER THIS:**

```swift
// ❌ DON'T create arbitrary shadow styles
.shadow(color: .black.opacity(0.3), radius: 10, x: 2, y: 5)
.shadow(color: .gray.opacity(0.5), radius: 15, x: 0, y: 10)
```

**Why**: Too many shadow styles:

- Create visual inconsistency
- Confuse information hierarchy
- Look unpolished
- Impact performance

------

### ✅ REQUIRED: Button Hierarchy

#### Visual Hierarchy System

**DO THIS:**

```swift
enum ButtonStyle {
    case primary    // Main CTA (gradient or prominent)
    case secondary  // Important actions (solid color)
    case tertiary   // Less prominent (ghost/outline)
    case quiet      // Minimal visual weight (text only)
}

struct ButtonConfig {
    static let primary = ButtonConfig(
        background: .linearGradient(
            colors: [Color.accentColor, Color.accentColor.opacity(0.8)],
            startPoint: .leading,
            endPoint: .trailing
        ),
        foregroundColor: .white,
        padding: EdgeInsets(top: 16, leading: 24, bottom: 16, trailing: 24)
    )
    
    static let secondary = ButtonConfig(
        background: .solid(Color.accentColor),
        foregroundColor: .white,
        padding: EdgeInsets(top: 12, leading: 20, bottom: 12, trailing: 20)
    )
    
    static let tertiary = ButtonConfig(
        background: .clear,
        foregroundColor: .accentColor,
        padding: EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16),
        border: BorderConfig(color: .accentColor, width: 1)
    )
    
    static let quiet = ButtonConfig(
        background: .clear,
        foregroundColor: .accentColor,
        padding: EdgeInsets(top: 8, leading: 8, bottom: 8, trailing: 8)
    )
}
```

**Usage Guidelines**:

- **Primary**: One per screen, main conversion action
- **Secondary**: 2-3 per screen, important actions
- **Tertiary**: Supporting actions, less emphasis
- **Quiet**: Cancel, back, secondary navigation

**NEVER THIS:**

```swift
// ❌ DON'T use gradients on every button
Button("Submit") { }
    .background(LinearGradient(...))  // Too prominent

Button("Cancel") { }
    .background(LinearGradient(...))  // Confusing hierarchy

Button("Learn More") { }
    .background(LinearGradient(...))  // Visual overload
```

------

### ✅ REQUIRED: Spacing System

#### Design Tokens

**DO THIS:**

```swift
enum Spacing {
    static let xs: CGFloat = 4
    static let sm: CGFloat = 8
    static let md: CGFloat = 16
    static let lg: CGFloat = 24
    static let xl: CGFloat = 32
    static let xxl: CGFloat = 48
}

// Usage
VStack(spacing: Spacing.md) {
    Text("Title")
        .padding(.bottom, Spacing.sm)
    
    Text("Body")
        .padding(.horizontal, Spacing.lg)
}
```

**NEVER THIS:**

```swift
// ❌ DON'T use arbitrary spacing values
VStack(spacing: 13) { }
.padding(.bottom, 7)
.padding(.horizontal, 19)
```

**Why**: Consistent spacing creates:

- Visual rhythm
- Predictable layouts
- Easier maintenance
- Professional appearance

------

## Animation & Motion

### ✅ REQUIRED: Respect Reduce Motion

#### Motion-Aware Animations

**DO THIS:**

```swift
@Environment(\.accessibilityReduceMotion) var reduceMotion

struct AnimatedView: View {
    @State private var isVisible = false
    
    var body: some View {
        Text("Content")
            .opacity(isVisible ? 1 : 0)
            .offset(y: isVisible ? 0 : (reduceMotion ? 0 : 20))
            .animation(
                reduceMotion ? .none : .spring(duration: 0.4),
                value: isVisible
            )
            .onAppear {
                isVisible = true
            }
    }
}
```

**Animation Guidelines**:

- **With Reduce Motion ON**: Instant or very brief transitions (< 0.1s)
- **With Reduce Motion OFF**: Smooth, spring-based animations

**NEVER THIS:**

```swift
// ❌ DON'T ignore Reduce Motion setting
.animation(.spring(duration: 0.6), value: state)  // Always animates

// ❌ DON'T use repetitive animations
.rotationEffect(.degrees(rotation))
.onAppear {
    withAnimation(.linear(duration: 2).repeatForever()) {
        rotation = 360
    }
}
```

------

#### Animation Budget

**Limits per screen:**

- **Maximum**: 2-3 concurrent animations
- **Ideal**: 1 primary animation at a time

**DO THIS:**

```swift
// One purposeful animation
Button("Tap Me") {
    withAnimation(.spring()) {
        scale = 1.1
    }
    DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
        withAnimation(.spring()) {
            scale = 1.0
        }
    }
}
.scaleEffect(scale)
```

**NEVER THIS:**

```swift
// ❌ DON'T stack multiple effects
Circle()
    .modifier(FloatingModifier())  // Animation 1
    .modifier(PulseModifier())     // Animation 2
    .modifier(ShimmerEffect())     // Animation 3
    .rotationEffect(.degrees(rotation))  // Animation 4
```

**Why**: Too many animations:

- Degrade performance
- Distract users
- Drain battery
- Trigger motion sensitivity
- Look unprofessional

------

### ✅ REQUIRED: Haptic Feedback

#### Standardized Haptic System

**DO THIS:**

```swift
enum HapticFeedback {
    case selection    // Light tap for selections
    case success      // Confirmation of completion
    case warning      // Attention needed
    case error        // Something wrong
    
    func trigger() {
        switch self {
        case .selection:
            UISelectionFeedbackGenerator().selectionChanged()
        case .success:
            UINotificationFeedbackGenerator().notificationOccurred(.success)
        case .warning:
            UINotificationFeedbackGenerator().notificationOccurred(.warning)
        case .error:
            UINotificationFeedbackGenerator().notificationOccurred(.error)
        }
    }
}

// Usage
Button("Submit") {
    submitForm()
    HapticFeedback.success.trigger()
}
```

**Haptic Guidelines**:

| Event           | Haptic Type | Use Case           |
| --------------- | ----------- | ------------------ |
| Tab switch      | Selection   | User browsing      |
| Option selected | Selection   | Picking from list  |
| Form submitted  | Success     | Completion         |
| Quiz correct    | Success     | Achievement        |
| Limit reached   | Warning     | Soft stop          |
| Form error      | Error       | Validation failure |
| Quiz wrong      | Error       | Incorrect action   |

**NEVER THIS:**

```swift
// ❌ DON'T overuse haptics
.onTapGesture {
    // Haptic on every tap - annoying!
    UIImpactFeedbackGenerator(style: .medium).impactOccurred()
}

// ❌ DON'T use wrong haptic types
Button("Delete") {
    UINotificationFeedbackGenerator().notificationOccurred(.success)  // Wrong!
}
```

------

## Navigation Patterns

### ✅ REQUIRED: Navigation Best Practices

#### Use Appropriate Presentation

**DO THIS:**

```swift
// For main flows: NavigationLink
NavigationLink("Details") {
    DetailView()
}

// For modal tasks: Sheet
.sheet(isPresented: $showSettings) {
    SettingsView()
}

// For important alerts: Alert
.alert("Delete Item?", isPresented: $showAlert) {
    Button("Delete", role: .destructive) {
        delete()
    }
    Button("Cancel", role: .cancel) { }
}

// For simple choices: ConfirmationDialog
.confirmationDialog("Select Option", isPresented: $showDialog) {
    Button("Option 1") { }
    Button("Option 2") { }
    Button("Cancel", role: .cancel) { }
}
```

**NEVER THIS:**

```swift
// ❌ DON'T use sheets for main navigation
.sheet(isPresented: $showNextScreen) {
    MainContentView()  // Should be NavigationLink
}

// ❌ DON'T use full screen for temporary tasks
.fullScreenCover(isPresented: $showSettings) {
    SettingsView()  // Should be sheet
}
```

------

#### Navigation Hierarchy

**Requirements**:

- Every screen must have a clear `navigationTitle`
- Back button labels should be contextual
- Deep linking should maintain navigation stack
- Search should integrate with navigation

**DO THIS:**

```swift
NavigationStack {
    ListView()
        .navigationTitle("Items")
        .navigationDestination(for: Item.self) { item in
            DetailView(item: item)
                .navigationTitle(item.name)
                .navigationBarTitleDisplayMode(.inline)
        }
}
```

------

### ✅ REQUIRED: Tab Navigation

#### Tab Labels

**DO THIS:**

```swift
TabView {
    HomeView()
        .tabItem {
            Label("Home", systemImage: "house.fill")
        }
    
    StudyView()
        .tabItem {
            Label("Study Progress", systemImage: "chart.bar.fill")
        }
    
    ProfileView()
        .tabItem {
            Label("My Account", systemImage: "person.fill")
        }
}
```

**NEVER THIS:**

```swift
// ❌ DON'T use generic labels
.tabItem { Label("Progress", systemImage: "chart") }  // Too vague
.tabItem { Label("Profile", systemImage: "person") }  // Generic
```

**Why**: Descriptive labels help users understand purpose at a glance.

------

## Forms & Input

### ✅ REQUIRED: Form Design

#### Grouped Sections

**DO THIS:**

```swift
Form {
    Section("Account") {
        TextField("Email", text: $email)
            .textContentType(.emailAddress)
            .keyboardType(.emailAddress)
            .textInputAutocapitalization(.never)
        
        SecureField("Password", text: $password)
            .textContentType(.password)
    }
    
    Section("Preferences") {
        Toggle("Push Notifications", isOn: $notifications)
        Toggle("Email Updates", isOn: $emailUpdates)
    }
    
    Section {
        Button("Save Changes") {
            save()
        }
    }
}
```

**Requirements**:

- Group related fields with `Section`
- Use descriptive section headers
- Set appropriate `textContentType`
- Set appropriate `keyboardType`
- Handle autocapitalization
- Support password autofill

------

#### Inline Validation

**DO THIS:**

```swift
struct ValidatedTextField: View {
    @Binding var text: String
    let validation: (String) -> Bool
    let errorMessage: String
    
    var isValid: Bool {
        text.isEmpty || validation(text)
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            TextField("Email", text: $text)
                .textFieldStyle(.roundedBorder)
            
            if !isValid {
                Label(errorMessage, systemImage: "exclamationmark.triangle")
                    .font(.caption)
                    .foregroundStyle(.red)
            }
        }
    }
}

// Usage
ValidatedTextField(
    text: $email,
    validation: { $0.contains("@") },
    errorMessage: "Please enter a valid email"
)
```

**Why**: Immediate feedback helps users correct errors before submission.

------

## Performance Standards

### ✅ REQUIRED: Target Frame Rates

**Targets**:

- **Pro devices (ProMotion)**: 120fps
- **Standard devices**: 60fps
- **During scrolling**: No dropped frames
- **During animations**: Smooth, consistent frame rate

**How to Test**:

1. Instruments → Core Animation FPS
2. Xcode → Debug → View Debugging → Rendering
3. Enable "Color Offscreen-Rendered" and "Color Hits Green and Misses Red"

------

#### Optimization Techniques

**DO THIS:**

```swift
// Use LazyVStack/LazyHStack for long lists
ScrollView {
    LazyVStack {
        ForEach(items) { item in
            ItemRow(item: item)
        }
    }
}

// Use DrawingGroup for complex graphics
Canvas { context, size in
    // Complex drawing
}
.drawingGroup()

// Throttle expensive operations
.onChange(of: searchText) {
    Task {
        try? await Task.sleep(for: .milliseconds(300))
        await performSearch(searchText)
    }
}
```

**NEVER THIS:**

```swift
// ❌ DON'T use regular VStack for long lists
ScrollView {
    VStack {  // Renders all items immediately
        ForEach(items) { item in
            ItemRow(item: item)
        }
    }
}

// ❌ DON'T perform heavy operations on every keystroke
.onChange(of: searchText) {
    performExpensiveSearch(searchText)  // Called for every letter
}
```

------

## Testing Requirements

### ✅ REQUIRED: Testing Checklist

#### Accessibility Testing

**Manual Tests**:

- [ ] VoiceOver: Navigate entire app
- [ ] Voice Control: Complete key user flows
- [ ] Dynamic Type: Test at xxxLarge
- [ ] Reduce Motion: Verify animations disabled
- [ ] Reduce Transparency: Verify solid backgrounds
- [ ] Increase Contrast: Verify colors meet WCAG AA
- [ ] Invert Colors: Verify app still usable

**Automated Tests**:

```swift
func testAccessibility() throws {
    let app = XCUIApplication()
    app.launch()
    
    // Check all buttons have labels
    let buttons = app.buttons
    for button in buttons.allElementsBoundByIndex {
        XCTAssertFalse(button.label.isEmpty, 
            "Button missing accessibility label")
    }
}
```

------

#### Visual Testing

**Device Matrix**:

- [ ] iPhone SE (smallest screen)
- [ ] iPhone 15 (standard size)
- [ ] iPhone 15 Pro Max (largest screen)
- [ ] iPad (tablet layout)

**Orientation**:

- [ ] Portrait
- [ ] Landscape (where applicable)

**Display Settings**:

- [ ] Light mode
- [ ] Dark mode
- [ ] High contrast mode

------

#### Performance Testing

**Tools**:

- [ ] Instruments: Time Profiler
- [ ] Instruments: Allocations
- [ ] Instruments: Core Animation FPS
- [ ] Xcode: Memory Graph Debugger

**Benchmarks**:

- [ ] App launch < 2 seconds
- [ ] Screen transitions < 0.3 seconds
- [ ] No memory leaks detected
- [ ] Peak memory < 200MB (on standard content)
- [ ] Battery drain < 5% per hour (typical usage)

------

## Appendix: Common Mistakes

### 🚫 Avoid These Patterns

#### 1. Fighting iOS Conventions

```swift
// ❌ BAD: Custom navigation when system works better
struct CustomBackButton: View { }

// ✅ GOOD: Use system navigation
.navigationBarBackButtonHidden(false)
```

#### 2. Ignoring System Settings

```swift
// ❌ BAD: Always showing animations
.animation(.spring())

// ✅ GOOD: Respecting user preferences
@Environment(\.accessibilityReduceMotion) var reduceMotion
.animation(reduceMotion ? .none : .spring())
```

#### 3. Hard-Coding Dimensions

```swift
// ❌ BAD: Fixed sizes everywhere
.frame(width: 375, height: 667)  // iPhone 8 size
.font(.system(size: 16))

// ✅ GOOD: Flexible, adaptive layouts
.frame(maxWidth: .infinity)
.font(.body)
```

#### 4. Poor Color Contrast

```swift
// ❌ BAD: Low opacity overlays
Text("Hard to read")
    .background(Color.blue.opacity(0.05))

// ✅ GOOD: Sufficient contrast
Text("Easy to read")
    .background(Color.blue.opacity(0.15))  // WCAG compliant
```

#### 5. Missing Accessibility Labels

```swift
// ❌ BAD: Icon button with no label
Button { action() } label: {
    Image(systemName: "plus")
}

// ✅ GOOD: Descriptive label
Button { action() } label: {
    Image(systemName: "plus")
}
.accessibilityLabel("Add new item")
```

------

## Quick Reference Card

### Before Writing Any View

**Checklist**:

- [ ] Using `NavigationStack` (not `NavigationView`)
- [ ] Using semantic text styles (not fixed sizes)
- [ ] Using system materials (not custom opacity)
- [ ] Using design tokens for spacing
- [ ] Using accessibility modifiers
- [ ] Supporting Dynamic Type
- [ ] Respecting Reduce Motion
- [ ] Testing at xxxLarge text size

### Before Committing Code

**Review**:

- [ ] No fixed point sizes in `.font()`
- [ ] No fixed heights on buttons
- [ ] No hard-coded spacing values
- [ ] All interactive elements have labels
- [ ] All decorative elements are hidden from accessibility
- [ ] All colors meet WCAG AA (4.5:1 contrast)
- [ ] All animations respect Reduce Motion

------

## Resources

### Apple Documentation

- [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [Accessibility Programming Guide](https://developer.apple.com/accessibility/)
- [SwiftUI Documentation](https://developer.apple.com/documentation/swiftui)

### Tools

- Xcode Accessibility Inspector
- Instruments Performance Tools
- Color Contrast Analyzers
- SF Symbols App

### Further Reading

- WWDC Sessions on Accessibility
- WWDC Sessions on Design
- Apple Design Resources

------

**Document Version**: 1.0
 **Last Updated**: November 2025
 **Maintained By**: iOS Development Team

------

## Feedback & Updates

This document should be updated as:

- New iOS versions release
- HIG guidelines change
- Team learns new patterns
- Common issues are discovered

Submit updates via pull request to the team repository.