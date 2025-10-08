//
//  FontSystem.swift
//  Newsreel
//
//  Typography system using Outfit font family
//

import SwiftUI

extension Font {
    // MARK: - Display Fonts (Large Titles)
    
    /// Extra large display text (34pt, Bold)
    static let displayLarge = Font.custom("Outfit-Bold", size: 34)
    
    /// Large display text (28pt, Bold)
    static let displayMedium = Font.custom("Outfit-Bold", size: 28)
    
    /// Small display text (22pt, SemiBold)
    static let displaySmall = Font.custom("Outfit-SemiBold", size: 22)
    
    // MARK: - Headline Fonts
    
    /// Large headline (28pt, Bold)
    static let headlineLarge = Font.custom("Outfit-Bold", size: 28)
    
    /// Medium headline (22pt, SemiBold)
    static let headlineMedium = Font.custom("Outfit-SemiBold", size: 22)
    
    /// Small headline (18pt, SemiBold)
    static let headlineSmall = Font.custom("Outfit-SemiBold", size: 18)
    
    // MARK: - Title Fonts
    
    /// Large title (20pt, SemiBold)
    static let titleLarge = Font.custom("Outfit-SemiBold", size: 20)
    
    /// Medium title (18pt, Medium)
    static let titleMedium = Font.custom("Outfit-Medium", size: 18)
    
    /// Small title (16pt, Medium)
    static let titleSmall = Font.custom("Outfit-Medium", size: 16)
    
    // MARK: - Body Fonts
    
    /// Large body text (17pt, Regular)
    static let bodyLarge = Font.custom("Outfit-Regular", size: 17)
    
    /// Regular body text (15pt, Regular)
    static let bodyRegular = Font.custom("Outfit-Regular", size: 15)
    
    /// Small body text (13pt, Regular)
    static let bodySmall = Font.custom("Outfit-Regular", size: 13)
    
    /// Body emphasized (17pt, Medium)
    static let bodyLargeEmphasized = Font.custom("Outfit-Medium", size: 17)
    
    /// Body emphasized (15pt, Medium)
    static let bodyEmphasized = Font.custom("Outfit-Medium", size: 15)
    
    // MARK: - Caption Fonts
    
    /// Large caption (13pt, Regular)
    static let captionLarge = Font.custom("Outfit-Regular", size: 13)
    
    /// Regular caption (12pt, Regular)
    static let captionRegular = Font.custom("Outfit-Regular", size: 12)
    
    /// Small caption (11pt, Regular)
    static let captionSmall = Font.custom("Outfit-Regular", size: 11)
    
    /// Emphasized caption (12pt, Medium)
    static let captionEmphasized = Font.custom("Outfit-Medium", size: 12)
    
    // MARK: - Label Fonts
    
    /// Large label (15pt, Medium)
    static let labelLarge = Font.custom("Outfit-Medium", size: 15)
    
    /// Regular label (13pt, Medium)
    static let labelRegular = Font.custom("Outfit-Medium", size: 13)
    
    /// Small label (11pt, Medium)
    static let labelSmall = Font.custom("Outfit-Medium", size: 11)
    
    // MARK: - Button Fonts
    
    /// Large button (17pt, SemiBold)
    static let buttonLarge = Font.custom("Outfit-SemiBold", size: 17)
    
    /// Regular button (15pt, SemiBold)
    static let buttonRegular = Font.custom("Outfit-SemiBold", size: 15)
    
    /// Small button (13pt, SemiBold)
    static let buttonSmall = Font.custom("Outfit-SemiBold", size: 13)
    
    // MARK: - Custom Weight Access
    
    /// Get Outfit font with custom size and weight
    static func outfit(size: CGFloat, weight: OutfitWeight = .regular) -> Font {
        Font.custom(weight.fontName, size: size)
    }
}

// MARK: - Outfit Font Weights

enum OutfitWeight {
    case thin
    case extraLight
    case light
    case regular
    case medium
    case semiBold
    case bold
    case extraBold
    case black
    
    var fontName: String {
        switch self {
        case .thin: return "Outfit-Thin"
        case .extraLight: return "Outfit-ExtraLight"
        case .light: return "Outfit-Light"
        case .regular: return "Outfit-Regular"
        case .medium: return "Outfit-Medium"
        case .semiBold: return "Outfit-SemiBold"
        case .bold: return "Outfit-Bold"
        case .extraBold: return "Outfit-ExtraBold"
        case .black: return "Outfit-Black"
        }
    }
}

// MARK: - View Extension for Typography

extension View {
    /// Apply Outfit display large style
    func displayLargeStyle() -> some View {
        self.font(.displayLarge)
    }
    
    /// Apply Outfit headline style
    func headlineStyle() -> some View {
        self.font(.headlineMedium)
    }
    
    /// Apply Outfit title style
    func titleStyle() -> some View {
        self.font(.titleMedium)
    }
    
    /// Apply Outfit body style
    func bodyStyle() -> some View {
        self.font(.bodyRegular)
    }
    
    /// Apply Outfit caption style
    func captionStyle() -> some View {
        self.font(.captionRegular)
    }
}

// MARK: - Preview Helper

#if DEBUG
struct FontPreview: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                Group {
                    Text("Display Large")
                        .font(.displayLarge)
                    
                    Text("Display Medium")
                        .font(.displayMedium)
                    
                    Text("Display Small")
                        .font(.displaySmall)
                }
                .padding(.horizontal)
                
                Divider()
                
                Group {
                    Text("Headline Large")
                        .font(.headlineLarge)
                    
                    Text("Headline Medium")
                        .font(.headlineMedium)
                    
                    Text("Headline Small")
                        .font(.headlineSmall)
                }
                .padding(.horizontal)
                
                Divider()
                
                Group {
                    Text("Title Large")
                        .font(.titleLarge)
                    
                    Text("Title Medium")
                        .font(.titleMedium)
                    
                    Text("Title Small")
                        .font(.titleSmall)
                }
                .padding(.horizontal)
                
                Divider()
                
                Group {
                    Text("Body Large - This is how body text will appear in the app. It should be comfortable to read and well-spaced.")
                        .font(.bodyLarge)
                    
                    Text("Body Regular - This is how body text will appear in the app. It should be comfortable to read and well-spaced.")
                        .font(.bodyRegular)
                    
                    Text("Body Small - This is how body text will appear in the app. It should be comfortable to read and well-spaced.")
                        .font(.bodySmall)
                }
                .padding(.horizontal)
                
                Divider()
                
                Group {
                    Text("Caption Large")
                        .font(.captionLarge)
                    
                    Text("Caption Regular")
                        .font(.captionRegular)
                    
                    Text("Caption Small")
                        .font(.captionSmall)
                }
                .padding(.horizontal)
                
                Divider()
                
                Group {
                    Text("Button Large")
                        .font(.buttonLarge)
                    
                    Text("Button Regular")
                        .font(.buttonRegular)
                    
                    Text("Button Small")
                        .font(.buttonSmall)
                }
                .padding(.horizontal)
            }
            .padding(.vertical)
        }
        .withAppBackground()
    }
}

#Preview {
    FontPreview()
}

#Preview("Dark Mode") {
    FontPreview()
        .preferredColorScheme(.dark)
}
#endif

