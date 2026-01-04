# Newsreel

**AI-Powered News Aggregation Platform**

Modern news app that delivers curated, multi-perspective stories from 100+ trusted sources, enhanced with AI-powered summaries.

---

## 📚 Documentation

**All documentation is in the [`/docs`](docs/) folder.**

### Quick Links

| Document | Description |
|----------|-------------|
| **[📋 Documentation Index](docs/INDEX.md)** | Start here - complete documentation hub |
| **[🚀 App Store Readiness](docs/APP_STORE_READINESS.md)** | Launch checklist and requirements |
| **[📊 Project Status](docs/PROJECT_STATUS.md)** | Current system status and metrics |
| **[🔧 Quick Reference](docs/QUICK_REFERENCE.md)** | Commands, URLs, and quick tips |

### By Topic

- **Setup**: [Azure](docs/Azure_Setup_Guide.md) · [Firebase](docs/Firebase_Setup_Guide.md) · [Xcode](docs/Xcode_Configuration.md)
- **Architecture**: [Product Spec](docs/Product_Specification.md) · [RSS Strategy](docs/RSS_FEED_STRATEGY.md) · [Design System](docs/Design_System.md)
- **Testing**: [Testing Guide](docs/TESTING_GUIDE.md) · [No Mocks Policy](docs/TESTING_POLICY_NO_MOCKS.md)

---

## 🏗️ Project Structure

```
Newsreel/
├── Newsreel App/          # iOS app (SwiftUI, Swift 5.9+)
├── Azure/
│   ├── api/              # FastAPI REST API (Container Apps)
│   ├── functions/        # Azure Functions (RSS, clustering, AI)
│   └── tests/            # Backend test suite
├── docs/                 # 📚 All documentation (start here!)
│   ├── INDEX.md          # Documentation hub
│   ├── archive/          # Historical records
│   └── azure/            # Azure-specific guides
└── README.md            # ← You are here
```

---

## 🔗 Live Services

- **Backend API**: https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io
- **Azure Portal**: [Newsreel-RG](https://portal.azure.com)
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

## 🚀 Quick Start

**iOS Development:**
```bash
cd "Newsreel App"
open Newsreel.xcodeproj
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

See **[docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** for all commands.

---

## 📄 License & Contact

**Copyright**: © 2025-2026 One Thum Software. All rights reserved.  
**Contact**: dave@onethum.com

---

**→ Start with the [Documentation Index](docs/INDEX.md)**
