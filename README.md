# Newsreel

> AI-curated news aggregation for iOS - Ad-free, transparent, personalized

## Overview

Newsreel is an iOS app that delivers AI-summarized news from multiple trusted sources. Using Claude Sonnet 4.1, we synthesize facts from various outlets into clear, concise summaries while maintaining full source transparency.

**Display Name**: Newsreel  
**Bundle ID**: `com.onethum.newsreel`  
**Version**: 1.0.0 (Build 1)  
**Repository**: https://github.com/OneThum/newsreel.git  
**Developer**: One Thum Software

## Key Features

- 🤖 **AI-Powered Summaries** - Facts-based summaries synthesized from multiple sources
- 🔄 **Flip Card UI** - Summary on front, sources on back with attribution
- 🚨 **Breaking News** - Real-time detection with 3-source verification
- 🎯 **Personalized Feed** - Learns from your reading behavior
- 🚫 **Ad-Free** - Clean, distraction-free reading experience
- 📱 **iOS 26+ Native** - Built with latest SwiftUI and modern Apple design patterns
- ✨ **Liquid Glass Design** - Beautiful gradient backgrounds with Apple-inspired aesthetics
- 🎨 **Modern iOS 26 UI** - Scroll transitions, materials, and latest HIG guidelines

## Tech Stack

### Frontend
- **Platform**: iOS 26+
- **Framework**: SwiftUI (latest iOS 26 features)
- **Architecture**: MVVM with Combine/Swift Concurrency
- **Typography**: Outfit font family (all weights)
- **Design**: Liquid Glass with iOS 26 materials and transitions
- **Authentication**: Firebase Auth
- **Subscriptions**: RevenueCat

### Backend
- **APIs**: Azure Container Apps (FastAPI)
- **Functions**: Azure Functions (Python 3.11)
- **Database**: Azure Cosmos DB (Serverless)
- **AI**: Anthropic Claude Sonnet 4.1
- **Monitoring**: Azure Application Insights

## Project Structure

```
Newsreel/
├── docs/                           # Documentation
│   └── Product_Specification.md    # Full product specification
├── Azure/                          # Azure infrastructure
│   ├── functions/                  # Azure Functions
│   └── api/                        # Container Apps APIs
├── Newsreel App/                   # iOS Application
│   └── Newsreel/                   # Main app target
└── README.md                       # This file
```

## Documentation

- **[Project Status](docs/PROJECT_STATUS.md)** - Current status, completed items, and immediate next steps
- **[Product Specification](docs/Product_Specification.md)** - Complete technical specification with architecture, database schemas, API specs, and implementation details
- **[Development Roadmap](docs/Development_Roadmap.md)** - Detailed implementation plan with phases and checkboxes
- **[Xcode Configuration](docs/Xcode_Configuration.md)** - Project settings, versioning, and App Store preparation
- **[iOS 18 Best Practices](docs/iOS18_Best_Practices.md)** - Modern iOS 18 features, scroll transitions, and Liquid Glass patterns
- **[Design System Guide](docs/Design_System.md)** - Liquid Glass gradient backgrounds, Outfit typography, and UI guidelines
- **[Font Setup Guide](docs/Font_Setup_Guide.md)** - Outfit font configuration and usage reference
- **[Firebase Setup Guide](docs/Firebase_Setup_Guide.md)** - Authentication and push notification configuration
- **[Azure Setup Guide](docs/Azure_Setup_Guide.md)** - Step-by-step infrastructure deployment guide
- **[RevenueCat Setup Guide](docs/RevenueCat_Setup_Guide.md)** - Subscription management configuration and implementation
- **[Cost Management](docs/Cost_Management.md)** - Budget tracking, optimization strategies, and alerts
- **[Documentation Index](docs/INDEX.md)** - Complete documentation hub

## Business Model

### Free Tier
- 20 stories per day
- 30-minute delay on breaking news
- Access to all sources
- Up to 10 saved stories

### Premium Tier ($4.99/month)
- Unlimited stories
- Real-time breaking news
- Unlimited saves
- Priority support
- Export reading history
- Custom notifications

## Development Status

🚧 **Status**: Planning/Initial Setup

See the [Product Specification](docs/Product_Specification.md#11-development-phases) for detailed development phases and timeline.

## Getting Started

### Prerequisites
- **iOS 26.0+** / Xcode 18+
- Azure subscription (Newsreel Subscription)
- Firebase project (Authentication)
- RevenueCat account (Subscription management)
- Anthropic API key (Claude AI)
- Twitter Developer API access (Breaking news)

### Setup Instructions

See individual setup guides:
- [Xcode Configuration](docs/Xcode_Configuration.md) - Project settings and versioning
- [Firebase Setup Guide](docs/Firebase_Setup_Guide.md) - Authentication and push notifications
- [Azure Setup Guide](docs/Azure_Setup_Guide.md) - Infrastructure deployment
- [RevenueCat Setup Guide](docs/RevenueCat_Setup_Guide.md) - Subscription management
- [Font Setup Guide](docs/Font_Setup_Guide.md) - Outfit font configuration

## Cost Management

**Hard Budget Constraints:**
- **Azure Maximum**: $150/month (CANNOT EXCEED)
- **Total Project Maximum**: $300/month (CANNOT EXCEED)

**Current Projected Costs**: ~$276/month
- Azure Services: $96/month
  - Azure Cosmos DB: $31
  - Azure Container Apps: $40
  - Azure Functions: $15
  - Storage & Monitoring: $10
- External Services: $180/month
  - Claude API: $80
  - Twitter API: $100
  - Firebase Auth: $0 (free tier)
  - RevenueCat: $0 (free tier up to $2.5k MRR)

**Buffer**: $24/month (8% under budget ✅)

**Note**: RevenueCat is free for first ~500 subscribers ($2,500 MRR at $4.99/month)

See [Cost Management Guide](docs/Cost_Management.md) for detailed tracking, optimization strategies, and alerts.

## Contributing

This is a private project by One Thum Software. Internal team guidelines to be added.

## License

Copyright © 2025 One Thum Software. All rights reserved.

---

**Contact**: One Thum Software  
**Last Updated**: October 8, 2025

