# Newsreel Documentation Index

Welcome to the Newsreel documentation. This index helps you find the right document for your needs.

---

## Quick Start

New to the project? Start here:
1. Read the [README](../README.md) for an overview
2. Check [Project Status](PROJECT_STATUS.md) - see what's complete and what's next
3. **IMPORTANT**: Review [Cost Management Guide](Cost_Management.md) - understand budget limits
4. Review the [Product Specification](Product_Specification.md) to understand the architecture
5. Check the [Development Roadmap](Development_Roadmap.md) to see detailed tasks
6. **BEFORE deploying**: Check for existing Azure resources in the subscription
7. Follow setup guides as needed (Xcode, Firebase, Azure, etc.)

---

## Core Documentation

### 📊 [Project Status](PROJECT_STATUS.md)
**Audience**: All team members, stakeholders  
**Purpose**: Current project status, completed items, and next steps

**Contents**:
- Completed deliverables (Documentation ✅, Firebase ✅, Design System ✅)
- In-progress items (iOS app 5%)
- Next steps by priority
- Progress summary by category
- Current focus areas
- Blockers and dependencies
- Key decisions log
- Team checklist

**When to use**:
- Starting your day (see current focus)
- Planning next sprint
- Status updates to stakeholders
- Identifying what to work on next
- Quick project overview

---

### 📋 [Product Specification](Product_Specification.md)
**Audience**: All team members, stakeholders  
**Purpose**: Complete technical specification for Newsreel

**Contents**:
- Executive summary and product vision
- System architecture diagrams
- Complete database schemas with examples
- Backend services (Azure Functions, APIs)
- API specifications with request/response examples
- iOS application structure and code examples
- Infrastructure as Code (Terraform)
- Security and authentication
- Cost management and optimization
- Testing strategies
- Monitoring and operations

**When to use**: 
- Understanding the full system design
- Making architectural decisions
- Onboarding new developers
- Reference during implementation

---

### 🗺️ [Development Roadmap](Development_Roadmap.md)
**Audience**: Development team, project managers  
**Purpose**: Track implementation progress and plan work

**Contents**:
- Phase 1: MVP Backend (Weeks 1-2)
- Phase 2: AI Summarization (Weeks 3-4)
- Phase 3: iOS App MVP (Weeks 5-6)
- Phase 4: Personalization (Weeks 7-8)
- Phase 5: Premium Features (Weeks 9-10)
- Phase 6: Launch & Monitoring (Week 11+)
- Future enhancements
- Risk mitigation strategies
- Success metrics

**When to use**:
- Planning sprints
- Tracking progress
- Identifying blockers
- Prioritizing features

---

### ☁️ [Azure Setup Guide](Azure_Setup_Guide.md)
**Audience**: DevOps, backend developers  
**Purpose**: Step-by-step infrastructure deployment

**Contents**:
- **CRITICAL**: Budget constraints and resource reuse policy
- Prerequisites and tool setup
- Check existing resources FIRST
- Azure CLI configuration
- Terraform backend setup
- Resource deployment steps
- Secrets management with Key Vault
- Monitoring configuration
- Testing and verification
- Troubleshooting common issues
- Cost monitoring
- Useful command reference

**When to use**:
- Setting up development environment
- Deploying to production
- Troubleshooting infrastructure issues
- Adding new Azure resources

---

### 💰 [Cost Management Guide](Cost_Management.md)
**Audience**: All team members, finance  
**Purpose**: Track and optimize project costs

**Contents**:
- Hard budget limits ($150 Azure, $300 total)
- Current cost breakdown
- Azure subscription details
- Check existing resources first (before creating)
- Daily cost monitoring commands
- Budget alert configuration
- Cost optimization strategies
- Emergency cost reduction plan
- Weekly cost reporting template
- Resource tagging strategy

**When to use**:
- Before creating any new Azure resource
- Weekly cost reviews
- When approaching budget limits
- Planning new features
- Optimizing existing infrastructure

---

## Additional Guides

### 🎨 [Design System Guide](Design_System.md)
**Audience**: iOS developers, designers  
**Purpose**: Liquid Glass gradient background system and design guidelines

**Contents**:
- **Typography system** - Outfit font scale and usage
- AppBackground.swift overview
- Color palette (light & dark mode)
- Usage examples with code
- Content styling tips (materials, cards, text)
- Animation guidelines
- Accessibility best practices
- Performance considerations
- Migration guide

**When to use**:
- Implementing new views
- Styling content
- Testing light/dark mode
- Ensuring accessibility
- Understanding the app's visual language

---

### 🔤 [Font Setup Guide](Font_Setup_Guide.md)
**Audience**: iOS developers  
**Purpose**: Configure Outfit font family in Xcode

**Contents**:
- Font files and weights
- Xcode project setup
- Info.plist configuration
- Font verification steps
- Usage examples
- Font scale reference table
- Story card typography example
- Troubleshooting guide

**When to use**:
- Initial project setup
- Font not displaying correctly
- Adding app to new machine
- Reference for font sizes and weights

---

### 📱 [iOS 18 Best Practices](iOS18_Best_Practices.md)
**Audience**: iOS developers  
**Purpose**: Leverage latest iOS 18 features and design patterns

**Contents**:
- iOS 18 feature overview
- Enhanced materials and vibrancy
- Scroll transitions (`.scrollTransition`)
- Container relative sizing
- Advanced animations and spring physics
- Sensory feedback (haptics)
- Liquid Glass implementation
- Performance optimizations
- Accessibility enhancements
- Dark mode excellence
- Modern navigation patterns
- State management with Observation
- Complete code examples

**When to use**:
- Implementing new views
- Adding animations
- Optimizing performance
- Ensuring iOS 18 compatibility
- Reference for modern SwiftUI patterns

---

### ⚙️ [Xcode Configuration](Xcode_Configuration.md)
**Audience**: iOS developers, DevOps  
**Purpose**: Configure Xcode project settings and prepare for App Store

**Contents**:
- App identity settings (version, build, bundle ID)
- Xcode project configuration
- Info.plist setup
- Signing & capabilities
- Build settings
- Asset catalog configuration
- Privacy manifest
- Version incrementing guide
- App Store Connect setup
- Build for release checklist
- Archive and upload process
- Troubleshooting

**When to use**:
- Initial project setup
- Preparing for App Store submission
- Configuring certificates and profiles
- Version updates
- Build issues

---

### 💰 [RevenueCat Setup Guide](RevenueCat_Setup_Guide.md)
**Audience**: iOS developers, backend developers  
**Purpose**: Configure subscription management with RevenueCat

**Contents**:
- RevenueCat account setup
- App Store Connect integration
- Product and entitlement configuration
- iOS SDK integration with code examples
- Backend webhook handler implementation
- Testing sandbox purchases
- Production checklist
- Monitoring and analytics

**When to use**:
- Setting up subscription management
- Implementing in-app purchases
- Testing subscription flows
- Troubleshooting purchase issues

---

## Additional Guides

### 🔥 [Firebase Setup Guide](Firebase_Setup_Guide.md)
**Audience**: iOS developers, backend developers  
**Purpose**: Configure Firebase Authentication and Cloud Messaging

**Contents**:
- Firebase project details (newsreel-865a5)
- GoogleService-Info.plist configuration
- Firebase SDK setup
- Authentication methods (Email, Google, Apple)
- Push notifications (FCM) setup
- Backend token verification
- Security best practices
- Testing procedures
- Troubleshooting

**When to use**:
- Initial authentication setup
- Configuring sign-in methods
- Push notification implementation
- Backend Firebase integration
- Authentication issues

---

## Additional Guides (To Be Created)

---

### 📰 RSS Configuration Guide
**Status**: 📝 Planned  
**Purpose**: Configure and manage RSS feeds

**Will include**:
- Feed source selection criteria
- Adding new feeds
- Feed reliability testing
- Category mapping
- Source tier system

---

### 🧪 Testing Guide
**Status**: 📝 Planned  
**Purpose**: Testing strategies and tools

**Will include**:
- Unit testing (backend & iOS)
- Integration testing
- End-to-end testing
- Load testing
- Test coverage goals

---

### 📱 iOS Development Guide
**Status**: 🔄 Partial (Design System ✅)  
**Purpose**: iOS app development standards

**Available**:
- ✅ Design System Guide (Liquid Glass backgrounds)

**Still to create**:
- Project structure conventions
- Coding conventions
- SwiftUI best practices
- State management patterns
- API integration patterns

---

### 🤖 AI Prompt Engineering
**Status**: 📝 Planned  
**Purpose**: Claude API prompt optimization

**Will include**:
- System prompt design
- Facts-based summarization techniques
- Multi-source synthesis strategies
- Cost optimization with caching
- Quality evaluation criteria

---

### 🚀 Deployment Guide
**Status**: 📝 Planned  
**Purpose**: CI/CD and release process

**Will include**:
- GitHub Actions workflows
- Container build and push
- Function app deployment
- iOS app submission
- Rollback procedures

---

### 📊 Monitoring & Alerting
**Status**: 📝 Planned  
**Purpose**: Operations and incident response

**Will include**:
- Application Insights dashboards
- Alert configuration
- On-call runbooks
- Incident response procedures
- Performance optimization

---

### 💰 Cost Optimization
**Status**: 📝 Planned  
**Purpose**: Managing operational costs

**Will include**:
- Cost breakdown by service
- Optimization strategies
- Budget alerts
- Cost-saving alternatives
- Scaling considerations

---

## Reference Documentation

### API Documentation
- **Base URL**: `https://api.newsreel.app` (production)
- **Authentication**: Firebase JWT tokens
- **Full spec**: See [Product Specification § 6](Product_Specification.md#6-api-specifications)

**Key Endpoints**:
- `GET /api/stories/feed` - Get personalized feed
- `GET /api/stories/{id}` - Get story detail
- `GET /api/stories/{id}/sources` - Get story sources
- `POST /api/stories/{id}/interact` - Like/save/share
- `GET /api/stories/breaking` - Get breaking news
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/preferences` - Update preferences

### Database Schemas
See [Product Specification § 4](Product_Specification.md#4-database-schema)

**Cosmos DB Containers**:
- `raw_articles` - Raw RSS feed articles
- `story_clusters` - Aggregated stories with summaries
- `user_profiles` - User accounts and preferences
- `user_interactions` - Engagement tracking
- `moderation_queue` - Content review queue

---

## Code Examples

### iOS (Swift)
```swift
// See Product Specification § 7.6
let stories = try await APIService.shared.getFeed(limit: 20)
```

### Backend (Python)
```python
# See Product Specification § 5.1
@app.timer_trigger(schedule="0 */5 * * * *")
async def rss_ingestion_timer(timer: func.TimerRequest):
    # Fetch RSS feeds
```

### API (FastAPI)
```python
# See Product Specification § 5.2
@app.get("/api/stories/feed")
async def get_personalized_feed(user = Depends(verify_token)):
    # Return stories
```

---

## Project Resources

### Repository
- **URL**: https://github.com/OneThum/newsreel.git
- **Branches**: 
  - `main` - Production
  - `develop` - Development
  - `feature/*` - Feature branches

### Azure Subscription
- **Subscription Name**: Newsreel Subscription
- **Subscription ID**: `d4abcc64-9e59-4094-8d89-10b5d36b6d4c`
- **Directory**: One Thum Software (onethum.com)
- **Budget**: $150/month maximum (Azure services only)

### External Services
- **Firebase Console**: https://console.firebase.google.com/project/newsreel-865a5
- **Azure Portal**: https://portal.azure.com/
- **Anthropic Console**: https://console.anthropic.com/
- **Twitter Developer**: https://developer.twitter.com/
- **RevenueCat Dashboard**: https://app.revenuecat.com/

### App Identity
- **Name**: Newsreel
- **Display Name**: Newsreel
- **Bundle ID**: `com.onethum.newsreel`
- **Version**: 1.0.0
- **Build**: 1
- **Developer**: One Thum Software
- **Platform**: iOS 18.0+
- **Copyright**: © 2025 One Thum Software

---

## Getting Help

### Internal Team
- Backend questions → Check Product Specification § 5
- iOS questions → Check Product Specification § 7
- Infrastructure questions → Check Azure Setup Guide
- API questions → Check Product Specification § 6

### External Resources
- **Azure Docs**: https://docs.microsoft.com/azure/
- **Firebase Docs**: https://firebase.google.com/docs
- **Swift Docs**: https://developer.apple.com/documentation/swift
- **Anthropic Docs**: https://docs.anthropic.com/

---

## Document Maintenance

### How to Update Documentation
1. Edit the relevant markdown file
2. Update the "Last Updated" date
3. Commit with descriptive message
4. Notify team of significant changes

### Documentation Review
- **Frequency**: After each development phase
- **Owner**: Development Lead
- **Process**: Review for accuracy, completeness, clarity

---

## Glossary

| Term | Definition |
|------|------------|
| **Story Cluster** | Group of related articles from multiple sources |
| **Story Fingerprint** | Hash used to identify similar stories |
| **Verification Level** | Number of unique sources (1-6+) |
| **Breaking News** | Story with 3+ sources and high importance |
| **Facts-Based Summary** | AI summary focusing only on facts |
| **Multi-Source Synthesis** | Combining info from multiple articles |
| **Flip Card** | UI showing summary (front) and sources (back) |
| **Rate Limiting** | Free tier restriction (20 stories/day) |
| **Personalization** | Feed customization based on behavior |
| **RU (Request Unit)** | Cosmos DB throughput measure |
| **TTL (Time-to-Live)** | Auto-delete old data after X days |

---

**Index Last Updated**: October 8, 2025  
**Total Documents**: 12 core + 1 planned  
**Documentation Coverage**: Architecture ✅ | Implementation 🔄 | Operations ✅ | Cost Management ✅ | Subscriptions ✅ | Design ✅ | Typography ✅ | iOS 18 ✅ | Xcode Config ✅ | Firebase ✅ | Status ✅

