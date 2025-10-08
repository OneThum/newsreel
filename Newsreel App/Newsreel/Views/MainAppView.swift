//
//  MainAppView.swift
//  Newsreel
//
//  Main authenticated app view with navigation
//

import SwiftUI

struct MainAppView: View {
    @EnvironmentObject var authService: AuthService
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            FeedView()
                .tabItem {
                    Label("Feed", systemImage: "newspaper.fill")
                }
                .tag(0)
            
            SavedStoriesView()
                .tabItem {
                    Label("Saved", systemImage: "bookmark.fill")
                }
                .tag(1)
            
            ProfileView()
                .tabItem {
                    Label("Profile", systemImage: "person.fill")
                }
                .tag(2)
        }
        .tint(.blue)
    }
}

// MARK: - Feed View (Placeholder)

struct FeedView: View {
    var body: some View {
        NavigationStack {
            ZStack {
                AppBackground()
                
                ScrollView {
                    VStack(spacing: 20) {
                        // Placeholder for story cards
                        ForEach(0..<5) { index in
                            StoryCardPlaceholder(index: index)
                        }
                    }
                    .padding()
                }
            }
            .navigationTitle("Newsreel")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

struct StoryCardPlaceholder: View {
    let index: Int
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "newspaper.fill")
                    .foregroundStyle(.blue)
                Text("Breaking News")
                    .font(.outfit(.semiBold, size: 14))
                    .foregroundStyle(.blue)
                Spacer()
                Text("\(index * 15)m ago")
                    .font(.outfit(.regular, size: 12))
                    .foregroundStyle(.secondary)
            }
            
            Text("Sample News Story \(index + 1)")
                .font(.outfit(.bold, size: 22))
            
            Text("This is a placeholder for actual news content. The full story card implementation will be added in Phase 3.")
                .font(.outfit(.regular, size: 15))
                .foregroundStyle(.secondary)
                .lineLimit(3)
            
            HStack(spacing: 16) {
                Button(action: {}) {
                    Image(systemName: "heart")
                }
                Button(action: {}) {
                    Image(systemName: "bookmark")
                }
                Button(action: {}) {
                    Image(systemName: "square.and.arrow.up")
                }
                Spacer()
                Text("\(3 + index) sources")
                    .font(.outfit(.regular, size: 13))
                    .foregroundStyle(.secondary)
            }
            .font(.system(size: 18))
            .foregroundStyle(.primary)
            .padding(.top, 8)
        }
        .padding(20)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16))
        .shadow(color: .black.opacity(0.1), radius: 10, y: 5)
    }
}

// MARK: - Saved Stories View (Placeholder)

struct SavedStoriesView: View {
    var body: some View {
        NavigationStack {
            ZStack {
                AppBackground()
                
                VStack(spacing: 16) {
                    Image(systemName: "bookmark.fill")
                        .font(.system(size: 60))
                        .foregroundStyle(.secondary)
                    
                    Text("No Saved Stories")
                        .font(.outfit(.semiBold, size: 24))
                    
                    Text("Stories you bookmark will appear here")
                        .font(.outfit(.regular, size: 16))
                        .foregroundStyle(.secondary)
                }
                .padding()
            }
            .navigationTitle("Saved")
            .navigationBarTitleDisplayMode(.large)
        }
    }
}

// MARK: - Profile View (Placeholder)

struct ProfileView: View {
    @EnvironmentObject var authService: AuthService
    @State private var showingSignOutAlert = false
    
    var body: some View {
        NavigationStack {
            ZStack {
                AppBackground()
                
                List {
                    Section {
                        if let user = authService.currentUser {
                            VStack(alignment: .leading, spacing: 8) {
                                Text(user.displayName ?? "User")
                                    .font(.outfit(.bold, size: 20))
                                
                                if let email = user.email {
                                    Text(email)
                                        .font(.outfit(.regular, size: 15))
                                        .foregroundStyle(.secondary)
                                }
                            }
                            .padding(.vertical, 8)
                        }
                    }
                    
                    Section("Account") {
                        NavigationLink(destination: Text("Subscription")) {
                            Label("Subscription", systemImage: "crown.fill")
                                .font(.outfit(.regular, size: 16))
                        }
                        
                        NavigationLink(destination: Text("Preferences")) {
                            Label("Preferences", systemImage: "slider.horizontal.3")
                                .font(.outfit(.regular, size: 16))
                        }
                        
                        NavigationLink(destination: Text("Notifications")) {
                            Label("Notifications", systemImage: "bell.fill")
                                .font(.outfit(.regular, size: 16))
                        }
                    }
                    
                    Section {
                        Button(action: { showingSignOutAlert = true }) {
                            Label("Sign Out", systemImage: "arrow.right.square")
                                .font(.outfit(.regular, size: 16))
                                .foregroundStyle(.red)
                        }
                    }
                }
                .scrollContentBackground(.hidden)
            }
            .navigationTitle("Profile")
            .navigationBarTitleDisplayMode(.large)
            .alert("Sign Out", isPresented: $showingSignOutAlert) {
                Button("Cancel", role: .cancel) {}
                Button("Sign Out", role: .destructive) {
                    try? authService.signOut()
                }
            } message: {
                Text("Are you sure you want to sign out?")
            }
        }
    }
}

#Preview("Main App") {
    MainAppView()
        .environmentObject(AuthService())
}

#Preview("Feed") {
    FeedView()
}

#Preview("Profile") {
    ProfileView()
        .environmentObject(AuthService())
}

