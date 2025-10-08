# Newsreel Development Roadmap

**Last Updated**: October 8, 2025  
**Current Phase**: Planning & Setup

---

## Phase 1: MVP Backend (Weeks 1-2)

### Objectives
Set up core Azure infrastructure and basic RSS ingestion pipeline.

### Tasks

#### Azure Infrastructure Setup
- [ ] Create Azure Resource Group (`newsreel-prod-rg`)
- [ ] Deploy Azure Cosmos DB (Serverless)
  - [ ] Create `raw_articles` container
  - [ ] Create `story_clusters` container
  - [ ] Create `user_profiles` container
  - [ ] Create `user_interactions` container
  - [ ] Configure indexing policies
- [ ] Set up Azure Storage Account for Functions
- [ ] Deploy Azure Functions (Consumption plan)
- [ ] Set up Application Insights
- [ ] Configure Azure Key Vault for secrets

#### RSS Ingestion Function
- [ ] Create RSS ingestion function (timer-triggered, every 5 min)
- [ ] Configure initial 10 RSS feeds
  - [ ] Reuters World
  - [ ] BBC World
  - [ ] AP World
  - [ ] TechCrunch
  - [ ] The Verge
  - [ ] Science Daily
  - [ ] Bloomberg
  - [ ] ESPN
  - [ ] NPR
  - [ ] CNN
- [ ] Implement HTTP 304 conditional request caching
- [ ] Store raw articles in Cosmos DB
- [ ] Add logging and error handling

#### Story Clustering Function
- [ ] Create clustering function (Cosmos DB change feed trigger)
- [ ] Implement basic story fingerprinting algorithm
- [ ] Group related articles
- [ ] Store story clusters in Cosmos DB
- [ ] Track verification levels (1, 2, 3+ sources)

#### Basic API
- [ ] Set up Azure Container Apps environment
- [ ] Create Story API container (FastAPI)
- [ ] Implement Firebase JWT authentication
- [ ] Create endpoint: `GET /api/stories/feed` (returns mock stories initially)
- [ ] Create endpoint: `GET /health` (health check)
- [ ] Deploy to Azure Container Apps

#### Firebase Setup
- [x] Create Firebase project (`newsreel-865a5`)
- [x] Configure GoogleService-Info.plist
- [x] Enable Email/Password authentication
- [x] Enable Google Sign-In
- [x] Enable Apple Sign-In
- [x] Enable Cloud Messaging (push notifications)
- [ ] Add Firebase SDK to Xcode project
- [ ] Initialize Firebase in app
- [ ] Generate service account credentials for backend
- [ ] Store credentials in Azure Key Vault

### Success Criteria
- ✅ Azure infrastructure provisioned
- ✅ RSS feeds polling successfully every 5 minutes
- ✅ Articles stored in Cosmos DB
- ✅ Basic clustering grouping similar stories
- ✅ API returning authenticated responses
- ✅ Costs under $50/month at this stage

---

## Phase 2: AI Summarization (Weeks 3-4)

### Objectives
Integrate Claude API and implement multi-source summarization.

### Tasks

#### Anthropic API Integration
- [ ] Sign up for Anthropic API
- [ ] Store API key in Azure Key Vault
- [ ] Create summarization function (Cosmos change feed trigger)
- [ ] Implement prompt engineering for facts-based summaries
- [ ] Implement prompt caching for cost optimization
- [ ] Add cost tracking and monitoring

#### Summarization Logic
- [ ] Trigger summarization when 2+ sources available
- [ ] Fetch source articles from Cosmos DB
- [ ] Build multi-source synthesis prompt
- [ ] Call Claude API with system prompt
- [ ] Store summary in story cluster
- [ ] Track version history
- [ ] Update story status (DEVELOPING → BREAKING)

#### RSS Feed Expansion
- [ ] Add 90 more RSS feeds (total: 100)
  - [ ] World news (20 feeds)
  - [ ] Tech (20 feeds)
  - [ ] Science (15 feeds)
  - [ ] Business (15 feeds)
  - [ ] US News (15 feeds)
  - [ ] Sports (10 feeds)
  - [ ] Entertainment (5 feeds)
- [ ] Configure feed categories and priorities
- [ ] Test feed reliability

#### API Enhancements
- [ ] Update `GET /api/stories/feed` to return real stories with summaries
- [ ] Create endpoint: `GET /api/stories/{id}` (story detail)
- [ ] Create endpoint: `GET /api/stories/{id}/sources` (source articles)
- [ ] Implement in-memory caching (5-minute TTL)
- [ ] Add rate limiting preparation (enforcement in Phase 5)

### Success Criteria
- ✅ Claude API generating high-quality summaries
- ✅ Multi-source synthesis working (2-6 sources per story)
- ✅ 100 RSS feeds polling successfully
- ✅ Prompt caching reducing costs by 60%+
- ✅ Claude API costs under $80/month
- ✅ Average summary: 100-150 words, factual, neutral tone

---

## Phase 3: iOS App MVP (Weeks 5-6)

### Objectives
Build core iOS app with feed, authentication, and flip-card UI.

### Tasks

#### Project Setup
- [ ] Create Xcode project (Newsreel)
- [ ] Configure bundle ID: `com.onethum.newsreel`
- [ ] Set minimum iOS version: 17.0
- [ ] Add Firebase SDK dependencies
- [ ] Configure `GoogleService-Info.plist`
- [ ] Set up folder structure (MVVM)

#### Authentication
- [ ] Create `AuthService.swift`
- [ ] Implement Firebase email/password sign-in
- [ ] Implement Firebase Google Sign-In
- [ ] Implement Firebase Apple Sign-In
- [ ] Create `LoginView.swift`
- [ ] Create `SignUpView.swift`
- [ ] Handle JWT token refresh
- [ ] Store auth state

#### API Integration
- [ ] Create `APIService.swift`
- [ ] Implement JWT authentication header
- [ ] Create `Story` model
- [ ] Create `Source` model
- [ ] Implement `getFeed()` method
- [ ] Implement `getStory(id:)` method
- [ ] Implement `getSources(storyId:)` method
- [ ] Add error handling

#### Feed View
- [ ] Create `FeedViewModel.swift`
- [ ] Create `FeedView.swift` (main screen)
- [ ] Implement pull-to-refresh
- [ ] Implement infinite scroll pagination
- [ ] Add loading states
- [ ] Add error handling UI

#### Story Card
- [ ] Create `StoryCardView.swift`
- [ ] Design card front (summary view)
  - [ ] Category icon & name
  - [ ] Breaking/Developing badge
  - [ ] Timestamp & source count
  - [ ] Title
  - [ ] Summary text
  - [ ] Action buttons (like, save, share, flip)
- [ ] Design card back (sources view)
  - [ ] Sources list
  - [ ] Tap to open in Safari
  - [ ] Flip back button
- [ ] Implement 3D flip animation
- [ ] Add card shadows and styling

#### Interactions
- [ ] Implement like button (local state only, API in Phase 4)
- [ ] Implement save button (local state only, API in Phase 4)
- [ ] Implement share sheet
- [ ] Track flip events (analytics preparation)

### Success Criteria
- ✅ Users can sign up/login with email or Google/Apple
- ✅ Feed loads 20 stories from API
- ✅ Stories display summaries correctly
- ✅ Flip animation smooth (60fps)
- ✅ Sources view shows all source articles
- ✅ Can tap sources to open in Safari
- ✅ App feels responsive and polished

---

## Phase 4: Personalization (Weeks 7-8)

### Objectives
Implement user interaction tracking, personalization engine, and breaking news detection.

### Tasks

#### Interaction Tracking
- [ ] Create endpoint: `POST /api/stories/{id}/interact` (like, save, share)
- [ ] Store interactions in `user_interactions` container
- [ ] Update story engagement counters (like_count, save_count, share_count)
- [ ] Update user interaction stats in profile
- [ ] Track dwell time and card flips

#### Recommendation Engine
- [ ] Create Recommendation Engine container app
- [ ] Implement user preference scoring
  - [ ] Category affinity
  - [ ] Topic affinity
  - [ ] Source preference
  - [ ] Recency preference
- [ ] Implement story scoring algorithm
  - [ ] User preference match
  - [ ] Importance score
  - [ ] Freshness
  - [ ] Diversity
- [ ] Create endpoint: `POST /api/recommend/stories`
- [ ] Update Story API to call Rec Engine for personalized feeds
- [ ] Implement cache warming for active users

#### Breaking News Detection
- [ ] Sign up for Twitter/X Basic API ($100/month)
- [ ] Create Breaking News Monitor function (timer: every 2 min)
- [ ] Monitor tweets from major news accounts
- [ ] Extract entities (events, locations, magnitudes)
- [ ] Trigger immediate RSS verification
- [ ] Mark stories as BREAKING when 3+ sources confirm
- [ ] Queue push notifications (delivery in Phase 5)

#### iOS Updates
- [ ] Update `APIService` to call interact endpoint
- [ ] Connect like button to API
- [ ] Connect save button to API
- [ ] Connect share to API
- [ ] Add breaking news badge animation
- [ ] Create breaking news filter view

### Success Criteria
- ✅ User interactions tracked in real-time
- ✅ Feed becomes more personalized over time
- ✅ Breaking news detected within 2 minutes
- ✅ No false positive breaking news
- ✅ Story clustering accurate (>90%)
- ✅ Recommendation engine reduces to <100ms response time

---

## Phase 5: Premium Features & Polish (Weeks 9-10)

### Objectives
Implement subscriptions, push notifications, rate limiting, and prepare for App Store.

### Tasks

#### Subscription Management
- [ ] Set up RevenueCat
  - [ ] Create RevenueCat account (https://app.revenuecat.com)
  - [ ] Create project for Newsreel
  - [ ] Configure App Store credentials
  - [ ] Create product: "Newsreel Premium" ($4.99/month)
  - [ ] Set up entitlements (premium_access)
- [ ] Set up App Store Connect In-App Purchases
  - [ ] Create subscription: "Newsreel Premium" ($4.99/month)
  - [ ] Configure auto-renewable subscription
  - [ ] Link product ID to RevenueCat
- [ ] Add RevenueCat SDK to iOS app
  - [ ] Add RevenueCat Swift package
  - [ ] Initialize SDK with API key
  - [ ] Configure observer mode (optional)
- [ ] Implement subscription purchase flow
  - [ ] Create `SubscriptionView.swift`
  - [ ] Create `SubscriptionViewModel.swift`
  - [ ] Use RevenueCat `Purchases.shared.getOfferings()`
  - [ ] Implement purchase with RevenueCat SDK
  - [ ] Handle subscription status changes
  - [ ] Implement subscription restoration
- [ ] Backend integration
  - [ ] Set up RevenueCat webhook URL in Azure
  - [ ] Create endpoint: `POST /api/webhooks/revenuecat` (handle webhook events)
  - [ ] Validate webhook signature
  - [ ] Update user profile with subscription status
  - [ ] Handle subscription events (renewal, cancellation, billing issues)

#### Rate Limiting
- [ ] Implement free tier limits (20 stories/day)
- [ ] Implement 30-minute breaking news delay for free users
- [ ] Show "Upgrade to Premium" prompts
- [ ] Create paywall UI for exceeded limits
- [ ] Add counter badge showing remaining stories (free tier)

#### Push Notifications
- [ ] Set up Azure Notification Hubs
- [ ] Configure APNs certificates in Azure
- [ ] Create `NotificationService.swift` in iOS
- [ ] Request notification permissions
- [ ] Register device token with backend
- [ ] Create endpoint: `POST /api/user/device-token`
- [ ] Create push notification function (queue-triggered)
- [ ] Send breaking news notifications (premium only)
- [ ] Implement notification tap handling
- [ ] Create notification preferences UI

#### User Profile
- [ ] Create `ProfileView.swift`
- [ ] Create `ProfileViewModel.swift`
- [ ] Create endpoint: `GET /api/user/profile`
- [ ] Create endpoint: `PUT /api/user/preferences`
- [ ] Implement category preferences selector
- [ ] Implement notification settings
- [ ] Add quiet hours configuration
- [ ] Show subscription status
- [ ] Add logout button

#### App Polish
- [x] Implement Liquid Glass gradient background system (from Ticka Currencies)
- [x] Implement Outfit font system (FontSystem.swift with all weights)
- [x] Implement iOS 18 scroll transitions and modern SwiftUI patterns
- [x] Add enhanced materials with subtle tinting (.backgroundStyle)
- [ ] Create app icon
- [ ] Design launch screen
- [x] Add haptic feedback (sensory feedback API)
- [ ] Implement skeleton loaders
- [ ] Add empty states
- [ ] Polish animations (interactive springs)
- [ ] Add app settings screen
- [x] Implement dark mode support (via AppBackground)
- [ ] Add accessibility labels
- [ ] Test VoiceOver support
- [ ] Test Dynamic Type scaling
- [ ] Verify Reduce Motion support

#### App Store Preparation
- [x] Define app version (1.0.0) and build number (1)
- [x] Set display name (Newsreel)
- [x] Confirm bundle identifier (com.onethum.newsreel)
- [ ] Configure Xcode project settings (see Xcode_Configuration.md)
- [ ] Create App Store Connect listing
- [ ] Write app description
- [ ] Create screenshots (6.7", 6.5", 5.5")
- [ ] Create promotional text
- [ ] Write keywords
- [ ] Create privacy policy
- [ ] Create terms of service
- [ ] Prepare app preview video (optional)
- [ ] Configure In-App Purchase (Premium $4.99/month)
- [ ] Test build and archive
- [ ] Submit for App Review

### Success Criteria
- ✅ Users can subscribe to Premium
- ✅ Subscription validated with App Store
- ✅ Free tier limited to 20 stories/day
- ✅ Premium users get real-time breaking news
- ✅ Push notifications working reliably
- ✅ App feels polished and professional
- ✅ Submitted to App Store

---

## Phase 6: Launch & Monitoring (Week 11+)

### Objectives
Public launch, monitor performance, gather feedback, iterate.

### Tasks

#### Pre-Launch
- [ ] Complete App Store review
- [ ] Set up monitoring dashboards
- [ ] Configure cost alerts
- [ ] Set up PagerDuty for on-call
- [ ] Create incident response runbooks
- [ ] Prepare marketing materials
- [ ] Set up analytics (Mixpanel or similar)

#### Launch
- [ ] Soft launch to friends & family (beta)
- [ ] Gather initial feedback
- [ ] Fix critical bugs
- [ ] Public launch on App Store
- [ ] Announce on social media
- [ ] Monitor crash reports
- [ ] Monitor costs
- [ ] Monitor API performance

#### Post-Launch
- [ ] Weekly usage reports
- [ ] Monitor user retention
- [ ] Track conversion to Premium
- [ ] Gather user feedback
- [ ] Prioritize feature requests
- [ ] Optimize costs
- [ ] Improve summarization quality
- [ ] Expand RSS feed sources

### Success Criteria
- ✅ App live on App Store
- ✅ <1% crash rate
- ✅ Costs remain under $300/month
- ✅ >30% user retention after 7 days
- ✅ Positive user reviews (>4.0 stars)
- ✅ Breaking news accurate and timely
- ✅ API response time <500ms (P95)

---

## Future Enhancements (Post-Launch)

### Features
- [ ] Categories filter (World, Tech, Science, etc.)
- [ ] Search functionality
- [ ] Bookmarks/Reading List
- [ ] Reading history
- [ ] Export reading history (Premium)
- [ ] Offline mode (cache last 20 stories)
- [ ] iPad support
- [ ] macOS app (Mac Catalyst)
- [ ] Widgets (Home Screen & Lock Screen)
- [ ] Siri Shortcuts integration
- [ ] Share to Reading List
- [ ] Custom notification categories

### Backend
- [ ] Multi-language support
- [ ] Video/image extraction from articles
- [ ] Fact-checking badges
- [ ] Editorial corrections UI
- [ ] Admin dashboard for story moderation
- [ ] A/B testing framework
- [ ] User feedback system
- [ ] Story recommendations via email digest

### Infrastructure
- [ ] Multi-region deployment (Asia, Europe)
- [ ] CDN for images
- [ ] Redis cache for hot data
- [ ] GraphQL API (alternative to REST)
- [ ] Dedicated recommendation model training pipeline

---

## Risk Mitigation

### Technical Risks
- **Claude API costs exceed budget**
  - Mitigation: Aggressive prompt caching, summarize only verified stories
- **Cosmos DB throttling**
  - Mitigation: Start with serverless, monitor RU consumption, optimize queries
- **Poor summarization quality**
  - Mitigation: Extensive prompt engineering, human review queue
- **Breaking news false positives**
  - Mitigation: Require 3+ sources, implement human review for major events

### Business Risks
- **Low subscription conversion**
  - Mitigation: Optimize free tier value, clear Premium benefits, trial period
- **High churn rate**
  - Mitigation: Improve personalization, add engaging features, reduce friction
- **Content licensing issues**
  - Mitigation: Fair use (facts only), always link to sources, respect robots.txt

---

## Success Metrics

### Engagement
- **Daily Active Users (DAU)**: Track growth
- **User Retention**: >30% D7, >15% D30
- **Stories Read per Session**: Target >5
- **Flip Rate**: >30% of stories flipped to see sources
- **Time in App**: Target >3 min per session

### Quality
- **Summarization Quality**: Manual review score >4/5
- **Breaking News Accuracy**: >95% verified
- **App Crash Rate**: <1%
- **API Uptime**: >99.9%

### Business
- **Free to Premium Conversion**: Target >5%
- **Monthly Recurring Revenue (MRR)**: Track growth
- **Customer Acquisition Cost (CAC)**: Optimize
- **Lifetime Value (LTV)**: Maximize
- **App Store Rating**: >4.0 stars

---

**Document Owner**: Development Team  
**Review Cadence**: Weekly during active development  
**Next Review**: After Phase 1 completion

