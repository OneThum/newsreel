//
//  PaywallView.swift
//  Newsreel
//
//  Subscription paywall and pricing view
//

import SwiftUI
//import RevenueCat

struct PaywallView: View {
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject var subscriptionService: SubscriptionService
    @State private var selectedTier: SubscriptionTier = .pro
    @State private var isProcessing = false
    @State private var errorMessage: String?
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 32) {
                    // Header
                    VStack(spacing: 12) {
                        Image(systemName: "crown.fill")
                            .font(.system(size: 60))
                            .foregroundStyle(
                                LinearGradient(
                                    colors: [.yellow, .orange],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                        
                        Text("Unlock Premium")
                            .font(.outfit(size: 32, weight: .bold))
                        
                        Text("Get the most out of Newsreel")
                            .font(.outfit(size: 16, weight: .regular))
                            .foregroundStyle(.secondary)
                    }
                    .padding(.top, 20)
                    
                    // Subscription Tiers
                    VStack(spacing: 16) {
                        // Pro Tier
                        SubscriptionTierCard(
                            tier: .pro,
                            price: "$4.99/month",
                            isSelected: selectedTier == .pro,
                            onSelect: { selectedTier = .pro }
                        )
                        
                        // Premium Tier
                        SubscriptionTierCard(
                            tier: .premium,
                            price: "$9.99/month",
                            isSelected: selectedTier == .premium,
                            badge: "BEST VALUE",
                            onSelect: { selectedTier = .premium }
                        )
                    }
                    .padding(.horizontal)
                    
                    // Error Message
                    if let errorMessage = errorMessage {
                        Text(errorMessage)
                            .font(.outfit(size: 14, weight: .regular))
                            .foregroundStyle(.red)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal)
                    }
                    
                    // Subscribe Button
                    Button(action: handleSubscribe) {
                        HStack {
                            if isProcessing {
                                ProgressView()
                                    .tint(.white)
                            } else {
                                Text("Subscribe to \(selectedTier.displayName)")
                                    .font(.outfit(size: 18, weight: .semiBold))
                                    .foregroundStyle(.white)
                            }
                        }
                    }
                    .primaryGlassButtonStyle()
                    .disabled(isProcessing)
                    .padding(.horizontal)
                    
                    // Restore Purchases
                    Button(action: handleRestore) {
                        Text("Restore Purchases")
                            .font(.outfit(size: 15, weight: .medium))
                            .foregroundStyle(.secondary)
                    }
                    .disabled(isProcessing)
                    
                    // Legal
                    HStack(spacing: 16) {
                        Button("Terms") {
                            // TODO: Show terms
                        }
                        Text("•")
                        Button("Privacy") {
                            // TODO: Show privacy policy
                        }
                    }
                    .font(.outfit(size: 13, weight: .regular))
                    .foregroundStyle(.secondary)
                    
                    Spacer()
                }
            }
            .withAppBackground()
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Close") {
                        dismiss()
                    }
                }
            }
        }
    }
    
    // MARK: - Actions
    
    private func handleSubscribe() {
        errorMessage = nil
        isProcessing = true
        
        Task {
            do {
                // TODO: Implement actual purchase flow when RevenueCat is configured
                // if let offering = subscriptionService.offerings?.current {
                //     let package = offering.availablePackages.first
                //     try await subscriptionService.purchase(package: package)
                //     dismiss()
                // }
                
                // Mock error for now
                throw SubscriptionError.notConfigured
            } catch {
                errorMessage = error.localizedDescription
            }
            isProcessing = false
        }
    }
    
    private func handleRestore() {
        errorMessage = nil
        isProcessing = true
        
        Task {
            do {
                try await subscriptionService.restorePurchases()
                dismiss()
            } catch {
                errorMessage = error.localizedDescription
            }
            isProcessing = false
        }
    }
}

// MARK: - Subscription Tier Card

struct SubscriptionTierCard: View {
    let tier: SubscriptionTier
    let price: String
    let isSelected: Bool
    var badge: String?
    let onSelect: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(tier.displayName)
                        .font(.outfit(size: 24, weight: .bold))
                    
                    Text(price)
                        .font(.outfit(size: 16, weight: .semiBold))
                        .foregroundStyle(.secondary)
                }
                
                Spacer()
                
                if let badge = badge {
                    Text(badge)
                        .font(.outfit(size: 11, weight: .bold))
                        .foregroundStyle(.white)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(.orange, in: Capsule())
                }
                
                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                    .font(.system(size: 24))
                    .foregroundStyle(isSelected ? .blue : .gray.opacity(0.3))
            }
            
            // Features
            VStack(alignment: .leading, spacing: 10) {
                ForEach(tier.features, id: \.self) { feature in
                    HStack(spacing: 8) {
                        Image(systemName: "checkmark")
                            .font(.system(size: 14, weight: .bold))
                            .foregroundStyle(.green)
                        
                        Text(feature)
                            .font(.outfit(size: 15, weight: .regular))
                    }
                }
            }
        }
        .padding(20)
        .background(
            ZStack {
                RoundedRectangle(cornerRadius: 16)
                    .fill(.ultraThinMaterial)
                
                // Enhanced glow for selected state
                if isSelected {
                    RoundedRectangle(cornerRadius: 16)
                        .fill(
                            LinearGradient(
                                colors: [
                                    .blue.opacity(0.2),
                                    .purple.opacity(0.15),
                                    .clear
                                ],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                }
            }
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(
                    LinearGradient(
                        colors: isSelected ? [
                            .blue.opacity(0.8),
                            .purple.opacity(0.8)
                        ] : [
                            .white.opacity(0.2),
                            .white.opacity(0.1)
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ),
                    lineWidth: isSelected ? 2 : 1
                )
        )
        .shadow(color: isSelected ? .blue.opacity(0.3) : .black.opacity(0.05), radius: isSelected ? 20 : 10, y: isSelected ? 10 : 5)
        .shadow(color: .black.opacity(0.03), radius: 5, y: 2)
        .scaleEffect(isSelected ? 1.03 : 1.0)
        .animation(.spring(response: 0.4, dampingFraction: 0.7), value: isSelected)
        .onTapGesture {
            HapticManager.selection()
            onSelect()
        }
    }
}

// MARK: - Preview

#Preview {
    PaywallView()
        .environmentObject(SubscriptionService())
}

