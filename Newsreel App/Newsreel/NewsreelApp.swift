//
//  NewsreelApp.swift
//  Newsreel
//
//  Created by David McLauchlan on 10/8/25.
//

import SwiftUI
import FirebaseCore

@main
struct NewsreelApp: App {
    @StateObject private var authService = AuthService()
    
    init() {
        // Configure Firebase
        FirebaseApp.configure()
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authService)
        }
    }
}
