# Newsreel Documentation Index

**Last Updated**: January 3, 2026

Welcome to the Newsreel documentation hub. All project documentation is consolidated here for easy navigation.

---

## 🎯 Start Here

| Document | Description |
|----------|-------------|
| **[APP_STORE_READINESS.md](APP_STORE_READINESS.md)** | Launch checklist and requirements |
| **[PROJECT_STATUS.md](PROJECT_STATUS.md)** | Current system status and metrics |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Commands, URLs, and quick tips |

---

## 📚 Documentation by Category

### Project Management
- **[APP_STORE_READINESS.md](APP_STORE_READINESS.md)** - Launch checklist and requirements
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current status and metrics
- **[Development_Roadmap.md](Development_Roadmap.md)** - Development phases and timeline
- **[Product_Specification.md](Product_Specification.md)** - Complete product requirements

### Setup & Configuration
- **[Azure_Setup_Guide.md](Azure_Setup_Guide.md)** - Complete Azure infrastructure deployment
- **[Firebase_Setup_Guide.md](Firebase_Setup_Guide.md)** - Authentication configuration
- **[Xcode_Configuration.md](Xcode_Configuration.md)** - iOS project setup
- **[Font_Setup_Guide.md](Font_Setup_Guide.md)** - Custom font integration (Outfit)
- **[RevenueCat_Setup_Guide.md](RevenueCat_Setup_Guide.md)** - Subscription management

### Architecture & Design
- **[Product_Specification.md](Product_Specification.md)** - Complete product requirements
- **[RSS_FEED_STRATEGY.md](RSS_FEED_STRATEGY.md)** - Feed ingestion architecture
- **[RSS_INGESTION_CONFIG.md](RSS_INGESTION_CONFIG.md)** - Polling configuration details
- **[Source_Display_Names.md](Source_Display_Names.md)** - RSS source configuration
- **[Design_System.md](Design_System.md)** - iOS UI/UX patterns and guidelines
- **[iOS18_Best_Practices.md](iOS18_Best_Practices.md)** - SwiftUI development guidelines

### Testing & Quality
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Complete testing guide (unit, integration, system tests)
- **[TESTING_POLICY_NO_MOCKS.md](TESTING_POLICY_NO_MOCKS.md)** - Why we don't use mocks
- **[TESTING_DECISION_TREE.md](TESTING_DECISION_TREE.md)** - When to use each test type
- **[POLICY_NO_FAKE_DATA.md](POLICY_NO_FAKE_DATA.md)** - Why we use realistic data

### Operations & Monitoring
- **[Cost_Management.md](Cost_Management.md)** - Azure budget optimization
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Commands and URLs

### Azure-Specific (docs/azure/)
- **[QUICK_START.md](azure/QUICK_START.md)** - Azure quick start guide
- **[DEPLOYMENT_SUMMARY.md](azure/DEPLOYMENT_SUMMARY.md)** - Infrastructure deployment details
- **[MONITORING_GUIDE.md](azure/MONITORING_GUIDE.md)** - Logging and monitoring
- **[AZURE_CLI_AUTH_REFERENCE.md](azure/AZURE_CLI_AUTH_REFERENCE.md)** - CLI authentication

### Development History
- **[DEVELOPMENT_HISTORY.md](DEVELOPMENT_HISTORY.md)** - Complete development journey and session summaries
- **[archive/](archive/)** - Historical bug fixes and session reports

---

## 🔍 Quick Find

| Looking for... | Go to |
|----------------|-------|
| What's needed for launch? | [APP_STORE_READINESS.md](APP_STORE_READINESS.md) |
| Current system status? | [PROJECT_STATUS.md](PROJECT_STATUS.md) |
| How to test? | [TESTING_GUIDE.md](TESTING_GUIDE.md) |
| How to deploy backend? | [Azure_Setup_Guide.md](Azure_Setup_Guide.md) |
| How to set up iOS app? | [Xcode_Configuration.md](Xcode_Configuration.md) |
| How RSS feeds work? | [RSS_FEED_STRATEGY.md](RSS_FEED_STRATEGY.md) |
| Design guidelines? | [Design_System.md](Design_System.md) |
| Commands and URLs? | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |
| Development history? | [DEVELOPMENT_HISTORY.md](DEVELOPMENT_HISTORY.md) |
| Bug fix history? | [archive/](archive/) folder |

---

## 📁 Folder Structure

```
docs/
├── INDEX.md                    # This file - documentation hub
├── APP_STORE_READINESS.md      # Launch checklist
├── PROJECT_STATUS.md           # Current status
├── QUICK_REFERENCE.md          # Commands & URLs
│
├── Setup Guides/
│   ├── Azure_Setup_Guide.md
│   ├── Firebase_Setup_Guide.md
│   ├── Xcode_Configuration.md
│   ├── Font_Setup_Guide.md
│   └── RevenueCat_Setup_Guide.md
│
├── Architecture/
│   ├── Product_Specification.md
│   ├── RSS_FEED_STRATEGY.md
│   ├── RSS_INGESTION_CONFIG.md
│   ├── Design_System.md
│   └── iOS18_Best_Practices.md
│
├── Testing/
│   ├── TESTING_GUIDE.md
│   ├── TESTING_POLICY_NO_MOCKS.md
│   ├── TESTING_DECISION_TREE.md
│   └── POLICY_NO_FAKE_DATA.md
│
├── azure/                      # Azure-specific docs
│   ├── QUICK_START.md
│   ├── DEPLOYMENT_SUMMARY.md
│   └── MONITORING_GUIDE.md
│
└── archive/                    # Historical records
    ├── sessions/               # Session summaries
    └── (bug fixes, status reports)
```

---

## 🗺️ Documentation by Role

### For iOS Developers
1. [Xcode_Configuration.md](Xcode_Configuration.md) - Set up Xcode project
2. [Firebase_Setup_Guide.md](Firebase_Setup_Guide.md) - Configure authentication
3. [Design_System.md](Design_System.md) - Follow design guidelines
4. [iOS18_Best_Practices.md](iOS18_Best_Practices.md) - SwiftUI best practices

### For Backend Developers
1. [Azure_Setup_Guide.md](Azure_Setup_Guide.md) - Deploy infrastructure
2. [azure/QUICK_START.md](azure/QUICK_START.md) - Get started quickly
3. [RSS_FEED_STRATEGY.md](RSS_FEED_STRATEGY.md) - Understand feed architecture
4. [azure/MONITORING_GUIDE.md](azure/MONITORING_GUIDE.md) - Monitor the system

### For DevOps / Operations
1. [azure/MONITORING_GUIDE.md](azure/MONITORING_GUIDE.md) - Set up monitoring
2. [Cost_Management.md](Cost_Management.md) - Manage Azure costs
3. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common commands

### For AI Assistants
1. [APP_STORE_READINESS.md](APP_STORE_READINESS.md) - Understand what needs to be done
2. [PROJECT_STATUS.md](PROJECT_STATUS.md) - Understand current state
3. [DEVELOPMENT_HISTORY.md](DEVELOPMENT_HISTORY.md) - Understand what's been built
4. This INDEX.md - Navigate to specific topics

---

## 📝 Documentation Standards

When creating or updating documentation:

1. **Add date** - Include "Last Updated: [Date]" at the top
2. **Use markdown** - Follow consistent formatting
3. **Link related docs** - Cross-reference relevant documents
4. **Keep current** - Update when changes are made
5. **Update this index** - Add new documents to appropriate sections

---

## 📞 Support

- **Developer**: dave@onethum.com
- **Project**: Newsreel by One Thum Software

---

**All documentation is organized in `/docs`. Start with [APP_STORE_READINESS.md](APP_STORE_READINESS.md) to see what's needed for launch.**
