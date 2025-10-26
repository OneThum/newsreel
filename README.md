# Newsreel - News Aggregation Platform

> **Current Status**: 🟡 78% Functional (96/123 tests passing)  
> **Last Updated**: October 26, 2025  
> **Main Blocker**: Clustering pipeline needs Azure Portal investigation  
> **See**: [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed status

---

# Newsreel

**AI-Powered News Aggregation Platform**

Modern news app that delivers curated, multi-perspective stories from 100+ trusted sources, enhanced with AI-powered summaries.

---

## 🚀 Quick Links

- **[📋 App Store Readiness](docs/APP_STORE_READINESS.md)** ⭐ - What's done, what's needed for launch
- **[📊 Project Status](docs/PROJECT_STATUS.md)** - Current implementation status
- **[📚 Documentation Index](docs/INDEX.md)** - Complete documentation guide
- **[🔧 Quick Reference](docs/QUICK_REFERENCE.md)** - Commands, URLs, and quick tips

---

## 📖 Documentation

All documentation is organized in the **`/docs`** folder:

### For Project Status
- **[APP_STORE_READINESS.md](docs/APP_STORE_READINESS.md)** - Launch checklist and timeline
- **[PROJECT_STATUS.md](docs/PROJECT_STATUS.md)** - Current status and metrics
- **[Recent_Changes.md](docs/Recent_Changes.md)** - Latest features and fixes

### For Setup & Deployment
- **[Azure_Setup_Guide.md](docs/Azure_Setup_Guide.md)** - Backend infrastructure
- **[Firebase_Setup_Guide.md](docs/Firebase_Setup_Guide.md)** - Authentication setup
- **[Xcode_Configuration.md](docs/Xcode_Configuration.md)** - iOS project configuration

### For Architecture & Design
- **[Product_Specification.md](docs/Product_Specification.md)** - Complete product requirements
- **[RSS_FEED_STRATEGY.md](docs/RSS_FEED_STRATEGY.md)** - Feed ingestion architecture
- **[Design_System.md](docs/Design_System.md)** - iOS UI/UX guidelines

---

## 🎯 Current Status

**Backend**: 🟢 Fully Operational  
**iOS App**: 🟡 95% Complete (needs subscription integration)  
**Target Launch**: 4-6 weeks

### What's Working ✅
- ✅ Azure Functions: RSS ingestion, clustering, AI summarization
- ✅ REST API: FastAPI with Firebase authentication
- ✅ iOS App: Feed, search, authentication, categories, saved stories
- ✅ AI Summaries: Claude Sonnet 4 with multi-source synthesis
- ✅ 100+ RSS feeds processing ~1,900 articles/hour

### What's Needed 🔴
- ❌ Subscription system (RevenueCat + App Store Connect)
- ❌ Privacy Policy & Terms of Service
- ❌ App Store assets (icon, screenshots, description)
- ❌ Onboarding flow

See **[APP_STORE_READINESS.md](docs/APP_STORE_READINESS.md)** for complete details.

---

## 🏗️ Architecture

```
Newsreel/
├── Newsreel App/          # iOS app (SwiftUI, Swift 5.9+)
├── Azure/
│   ├── api/              # FastAPI REST API (Container Apps)
│   ├── functions/        # Azure Functions (RSS, clustering, AI)
│   └── scripts/          # CLI automation tools
├── docs/                 # 📚 All documentation (start here!)
│   ├── archive/          # Historical bug fixes and diagnostics
│   └── azure/            # Azure-specific guides
└── README.md            # ← You are here
```

---

## 🔗 Live Services

- **Backend API**: https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io
- **Azure Functions**: newsreel-func-51689.azurewebsites.net
- **Azure Portal**: [Resource Group](https://portal.azure.com)
- **Firebase Console**: [newsreel-865a5](https://console.firebase.google.com/project/newsreel-865a5)

---

## 💻 Tech Stack

- **iOS**: Swift 5.9+, SwiftUI, SwiftData, iOS 17+
- **Backend**: Python 3.11, Azure Functions, FastAPI
- **Database**: Azure Cosmos DB (Serverless NoSQL)
- **Auth**: Firebase Authentication
- **AI**: Anthropic Claude Sonnet 4
- **Infrastructure**: Azure Container Apps, Application Insights

---

## 📱 iOS App Features

- 🔐 **Authentication**: Apple Sign-In, Google Sign-In, Email/Password
- 📰 **News Feed**: Infinite scroll with real-time updates
- 🎴 **Flip Cards**: Summary on front, sources on back (3D animation)
- 🔍 **Search**: Full-text search with relevance ranking
- 📑 **Categories**: 10 news categories with filter chips
- ⭐ **Saved Stories**: Offline-first with SwiftData
- 🎨 **Design**: Liquid Glass gradients, Outfit font, iOS 18 best practices
- 🌓 **Dark Mode**: Adaptive UI with system integration

---

## 🚀 Quick Start

### For AI Assistance

**Most important docs for AI context:**
1. Read **[APP_STORE_READINESS.md](docs/APP_STORE_READINESS.md)** for what needs to be done
2. Read **[PROJECT_STATUS.md](docs/PROJECT_STATUS.md)** for current system status
3. Check **[INDEX.md](docs/INDEX.md)** for specific topic documentation

### For Developers

**iOS Development:**
```bash
cd "Newsreel App"
open Newsreel.xcodeproj
# Configure signing in Xcode, then build
```

**Backend Deployment:**
```bash
# Functions
cd Azure/functions
func azure functionapp publish newsreel-func-51689

# API
cd Azure/api
az acr build --registry newsreelacr --image newsreel-api:latest .
```

See setup guides in `/docs` for detailed instructions.

---

## 📊 Performance Metrics

- **Articles/Hour**: ~1,900 from 100+ sources
- **AI Summary Coverage**: 33.8%+
- **API Response Time**: <500ms P95
- **Uptime**: 99.9%+
- **Monthly Costs**: $176 (well under $300 budget)

---

## 📄 License & Contact

**Copyright**: © 2025 One Thum Software. All rights reserved.  
**Contact**: dave@onethum.com  
**Project**: Private - One Thum Software

---

## 🗂️ Documentation Structure

```
docs/
├── APP_STORE_READINESS.md    ⭐ Launch checklist
├── PROJECT_STATUS.md         📊 Current status
├── INDEX.md                  📚 Documentation index
├── Recent_Changes.md         🆕 Latest updates
├── QUICK_REFERENCE.md        🔧 Commands & URLs
│
├── Setup Guides/
│   ├── Azure_Setup_Guide.md
│   ├── Firebase_Setup_Guide.md
│   └── Xcode_Configuration.md
│
├── Architecture/
│   ├── Product_Specification.md
│   ├── RSS_FEED_STRATEGY.md
│   ├── RSS_INGESTION_CONFIG.md
│   └── Design_System.md
│
├── archive/                  📦 Historical records
│   └── (Bug fixes from October 2025)
│
└── azure/                    ☁️ Azure-specific docs
    ├── QUICK_START.md
    ├── DEPLOYMENT_SUMMARY.md
    └── MONITORING_GUIDE.md
```

---

**For complete documentation, see the [`/docs`](docs/) folder.**

**Ready to launch!** 🚀
