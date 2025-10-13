# Newsreel

**AI-Powered News Aggregation Platform**

Newsreel is a modern news aggregation app that delivers curated, multi-perspective news stories from 100+ trusted sources, enhanced with AI-powered summaries and real-time verification.

---

## 🚀 Quick Start

### Prerequisites
- **iOS**: Xcode 15+, iOS 17+, Swift 5.9+
- **Backend**: Azure subscription, Python 3.11+, Azure Functions Core Tools
- **Auth**: Firebase project with Apple Sign-In and Google Sign-In enabled

### Setup
1. **iOS App**: See `docs/Xcode_Configuration.md`
2. **Azure Backend**: See `docs/Azure_Setup_Guide.md`
3. **Firebase Auth**: See `docs/Firebase_Setup_Guide.md`

---

## 📚 Documentation

All documentation is organized in the `/docs` folder:

### Getting Started
- **[Recent Changes](docs/Recent_Changes.md)** - Latest features, bug fixes, and improvements
- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Essential commands and URLs
- **[Project Status](docs/PROJECT_STATUS.md)** - Current implementation status

### Setup Guides
- **[Azure Setup](docs/Azure_Setup_Guide.md)** - Azure infrastructure deployment
- **[Firebase Setup](docs/Firebase_Setup_Guide.md)** - Authentication configuration
- **[Xcode Configuration](docs/Xcode_Configuration.md)** - iOS project setup

### Architecture & Design
- **[RSS Feed Strategy](docs/RSS_FEED_STRATEGY.md)** - Feed ingestion architecture
- **[Clustering Improvements](docs/CLUSTERING_IMPROVEMENTS.md)** - Story clustering logic
- **[Staggered RSS Polling](docs/STAGGERED_RSS_POLLING.md)** - Polling optimization
- **[Design System](docs/Design_System.md)** - iOS UI/UX patterns
- **[iOS18 Best Practices](docs/iOS18_Best_Practices.md)** - Development guidelines

### Monitoring & Operations
- **[Badge Logging & Monitoring](docs/BADGE_LOGGING_MONITORING.md)** - Observability setup
- **[Product Improvement Roadmap](docs/PRODUCT_IMPROVEMENT_ROADMAP.md)** - Future enhancements
- **[Cost Management](docs/Cost_Management.md)** - Azure budget optimization

### Product Specification
- **[Product Specification](docs/Product_Specification.md)** - Full product requirements

---

## 🏗️ Architecture

### Backend (Azure)
- **Azure Functions**: RSS ingestion, story clustering, summarization, breaking news monitoring
- **Azure Container Apps**: FastAPI REST API
- **Cosmos DB**: Serverless NoSQL database
- **Application Insights**: Logging and monitoring
- **Anthropic API**: AI-powered summaries

### iOS App
- **SwiftUI**: Modern declarative UI
- **Firebase Authentication**: Apple Sign-In, Google Sign-In
- **SwiftData**: Local persistence and offline-first caching
- **Async/Await**: Modern concurrency patterns

---

## ✨ Key Features

### For Users
- **Multi-Source Stories**: View 100+ news sources covering the same story
- **AI Summaries**: Quick, accurate summaries powered by Claude
- **Real-Time Updates**: Twitter-style smooth feed updates
- **Category Filtering**: 10 news categories with beautiful horizontal chips
- **Full-Text Search**: Find stories by keywords with relevance ranking
- **Status Badges**: See story verification status (MONITORING, DEVELOPING, VERIFIED, BREAKING)
- **Offline Support**: Read cached stories without internet

### For Developers
- **Structured Logging**: Full observability with Application Insights
- **CLI Automation**: Shell scripts for log analysis
- **Admin Dashboard**: Mobile-accessible backend metrics
- **Modern Stack**: SwiftUI, Azure Functions, FastAPI, Cosmos DB
- **Cost Optimized**: Serverless architecture with budget controls

---

## 🔧 Tech Stack

### iOS
- Swift 5.9+
- SwiftUI & SwiftData
- Firebase (Auth & Analytics)
- URLSession with async/await
- OSLog for structured logging

### Backend
- Python 3.11
- Azure Functions (Timer triggers, Cosmos DB change feed)
- FastAPI (REST API)
- Cosmos DB (Serverless NoSQL)
- Anthropic Claude API
- Application Insights

### Infrastructure
- Azure Container Apps
- Azure Functions
- Azure Cosmos DB
- Azure Container Registry
- Azure Application Insights
- Azure Log Analytics

---

## 📱 iOS App Structure

```
Newsreel App/
├── Newsreel/
│   ├── NewsreelApp.swift          # App entry point
│   ├── Models/                     # Data models
│   ├── Services/                   # API, Auth, Persistence
│   ├── Views/                      # SwiftUI views
│   │   ├── Auth/                  # Login, registration
│   │   ├── Components/            # Reusable components
│   │   ├── Settings/              # Preferences, notifications
│   │   └── Admin/                 # Admin dashboard
│   ├── Utilities/                  # Helpers, extensions
│   └── Assets.xcassets/           # Images, colors
```

---

## 🌐 Backend Structure

```
Azure/
├── functions/                      # Azure Functions
│   ├── rss_ingestion/             # 10-second RSS polling
│   ├── story_clustering/          # Story deduplication & clustering
│   ├── summarization/             # AI summary generation
│   ├── breaking_news_monitor/     # Real-time news alerts
│   └── shared/                    # Shared utilities
├── api/                           # FastAPI REST API
│   └── app/
│       ├── routers/               # API endpoints
│       ├── services/              # Business logic
│       └── middleware/            # Auth, logging
└── scripts/                       # CLI automation tools
```

---

## 🚀 Deployment

### iOS App
```bash
# Build
cd "Newsreel App"
xcodebuild -project Newsreel.xcodeproj -scheme Newsreel build

# Run in simulator
open -a Simulator
xcodebuild -project Newsreel.xcodeproj -scheme Newsreel -destination 'platform=iOS Simulator,name=iPhone 16 Pro' run
```

### Azure Functions
```bash
cd Azure/functions
func azure functionapp publish newsreel-func-51689 --python
```

### Azure Container Apps (API)
```bash
cd Azure/api
az acr build --registry newsreelacr --image newsreel-api:latest .
az containerapp update --name newsreel-api --resource-group newsreel-rg --image newsreelacr.azurecr.io/newsreel-api:latest
```

---

## 🔗 Quick Links

- **Backend API**: https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io
- **Azure Functions**: newsreel-func-51689.azurewebsites.net
- **Application Insights**: Via Azure Portal
- **Cosmos DB**: newsreel-cosmos (serverless)

---

## 📄 License

Copyright © 2025 One Thum Software. All rights reserved.

---

## 🤝 Contributing

This is a private project. For questions or issues, contact dave@onethum.com.

---

**For detailed documentation, see the `/docs` folder.**
