# Product Specification: Newsreel iOS App
**Version 1.0 | Date: October 8, 2025**

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Overview](#2-product-overview)
3. [System Architecture](#3-system-architecture)
4. [Database Schema](#4-database-schema)
5. [Backend Services](#5-backend-services)
6. [API Specifications](#6-api-specifications)
7. [iOS Application](#7-ios-application)
8. [Infrastructure & Deployment](#8-infrastructure--deployment)
9. [Security & Authentication](#9-security--authentication)
10. [Cost Management](#10-cost-management)
11. [Development Phases](#11-development-phases)
12. [Testing & Quality Assurance](#12-testing--quality-assurance)
13. [Monitoring & Operations](#13-monitoring--operations)
14. [Appendices](#14-appendices)

---

## 1. Executive Summary

### 1.1 Product Vision

Newsreel is an ad-free, AI-curated news aggregation platform for iOS that presents summarized news stories in a personalized feed. The app uses machine learning to understand user preferences through implicit signals (likes, saves, shares) and gradually improves content curation over time.

### 1.2 Key Differentiators

- **No advertisements** - Clean, distraction-free reading experience
- **AI-powered summarization** - Facts-based summaries using Claude Sonnet 4.1
- **Multi-source synthesis** - Combines information from multiple outlets
- **Transparent sourcing** - All sources accessible via flip-card UI
- **Personalized curation** - Learns from user behavior
- **Breaking news detection** - Real-time monitoring with verification

### 1.3 Business Model

- **Free Tier**: 20 stories per day, 30-minute delay on breaking news
- **Premium Tier**: $4.99/month - unlimited stories, real-time breaking news, unlimited saves

### 1.4 Technical Stack

| Component | Technology | Monthly Cost |
|-----------|-----------|--------------|
| Mobile App | iOS 18.0+, SwiftUI (latest) | $0 |
| Authentication | Firebase Auth | $0 (free tier) |
| Subscriptions | RevenueCat | $0 (free tier) |
| Backend APIs | Azure Container Apps, FastAPI | $40 |
| Functions | Azure Functions (Python) | $15 |
| Database | Azure Cosmos DB (Serverless) | $31 |
| AI Summarization | Anthropic Claude Sonnet 4.1 | $80 |
| Breaking News Triggers | Twitter/X Basic API | $100 |
| Push Notifications | Azure Notification Hubs | $0 (free tier) |
| Monitoring | Azure Application Insights | $10 |
| **Azure Subtotal** | | **$96/month** |
| **Total Project** | | **$276/month** |

**Budget Constraints:**
- **Maximum Azure Budget**: $150/month
- **Maximum Total Budget**: $300/month
- **Current Azure Projected**: $96/month (within budget ✅)
- **Current Total Projected**: $276/month (within budget ✅)

**Notes:**
- RevenueCat is free up to $2,500 MRR (Monthly Recurring Revenue), then 1% of tracked revenue
- At $4.99/user/month, we can have ~500 subscribers before RevenueCat charges apply
- RevenueCat handles: receipt validation, webhooks, subscriber management, analytics

### 1.5 App Identity

- **App Name**: Newsreel
- **Display Name**: Newsreel
- **Bundle Identifier**: com.onethum.newsreel
- **Version**: 1.0.0
- **Build Number**: 1
- **Repository**: https://github.com/OneThum/newsreel.git
- **Developer**: One Thum Software
- **Copyright**: © 2025 One Thum Software. All rights reserved.

---

## 2. Product Overview

### 2.1 User Experience Flow

```
1. User opens app
   ↓
2. Personalized feed loads (20 story tiles)
   ↓
3. User reads summary on tile front
   ↓
4. User flips tile to see sources (optional)
   ↓
5. User interacts: like, save, share, or tap source
   ↓
6. System learns preferences
   ↓
7. Feed improves over time
```

### 2.2 Story Tile Design

**Front of Card (Primary View)**
```
┌─────────────────────────────────────┐
│ 🌍 Breaking · 15m ago · 6 sources  │
│                                     │
│ 7.2 Magnitude Earthquake Strikes    │
│ Northern Japan                      │
│                                     │
│ A powerful earthquake struck off    │
│ the coast of Hokkaido at 2:34 PM    │
│ local time Tuesday. The US          │
│ Geological Survey recorded the      │
│ quake at 7.2 magnitude, with the    │
│ epicenter 45km east of Kushiro at   │
│ a depth of 30km. Japanese           │
│ authorities report at least 47      │
│ injuries, primarily from falling    │
│ debris and glass. Tsunami warnings  │
│ have been issued for coastal areas  │
│ of Hokkaido and northern Honshu,    │
│ with waves up to 1 meter expected.  │
│ Evacuations are underway in low-    │
│ lying areas. No deaths have been    │
│ confirmed. Power outages affecting  │
│ approximately 12,000 homes.         │
│                                     │
│ [❤️] [💾] [↗️] [ℹ️ View 6 sources] │
└─────────────────────────────────────┘
```

**Back of Card (Source Attribution)**
```
┌─────────────────────────────────────┐
│        Sources for this story       │
│                                     │
│ This summary synthesized from:      │
│                                     │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                     │
│ 📰 Reuters · 15 min ago            │
│ "Japan earthquake injures dozens,   │
│  tsunami warning issued"            │
│ [Read full article →]              │
│                                     │
│ 📰 NHK News · 12 min ago           │
│ "Magnitude 7.2 quake strikes        │
│  Hokkaido"                          │
│ [Read full article →]              │
│                                     │
│ 📰 USGS · 18 min ago               │
│ "M7.2 - 45km E of Kushiro, Japan"  │
│ [Read report →]                    │
│                                     │
│ + 3 more sources [View all]         │
│                                     │
│ [Report an issue] [Flip back]      │
└─────────────────────────────────────┘
```

### 2.3 Content Verification Levels

| Status | Sources | Display | Push Notifications |
|--------|---------|---------|-------------------|
| MONITORING | 1 | Hidden from users | No |
| DEVELOPING | 2 | Shown with "⚠️ Developing" tag | No |
| BREAKING | 3+ | Shown as "🔴 Breaking" | Yes (premium) |
| VERIFIED | 3+ after 30min | Standard display | No |

### 2.4 User Tiers

**Free Tier**
- 20 stories per day
- 30-minute delay on breaking news
- Can view all sources
- Cannot save more than 10 stories
- Standard personalization

**Premium Tier ($4.99/month)**
- Unlimited stories
- Real-time breaking news
- Unlimited saves
- Priority support
- Export reading history
- Custom notification settings

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    iOS App (SwiftUI)                     │
│              Firebase Auth JWT Tokens                    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────────┐
│            Azure API Management (Optional)               │
│         Rate Limiting • JWT Validation                   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│          Azure Container Apps (FastAPI APIs)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Story API   │  │  User API    │  │  Rec Engine  │  │
│  │  Port 8000   │  │  Port 8001   │  │  Port 8002   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│            Azure Cosmos DB (Serverless)                  │
│  • raw_articles      • story_clusters                    │
│  • user_profiles     • user_interactions                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│         Azure Functions (Python, Consumption)            │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ RSS Ingestion (Timer: every 5 min)                 │ │
│  │ • Fetch 100 RSS feeds in parallel                  │ │
│  │ • Use HTTP 304 conditional requests                │ │
│  │ • Store raw articles in Cosmos DB                  │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Story Clustering (Cosmos DB Change Feed)           │ │
│  │ • Group related articles                           │ │
│  │ • Extract entities and topics                      │ │
│  │ • Detect breaking news velocity                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Summarization (Event-driven)                       │ │
│  │ • Call Anthropic Claude API                        │ │
│  │ • Generate facts-based summaries                   │ │
│  │ • Multi-source synthesis                           │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Breaking News Monitor (Timer: every 2 min)         │ │
│  │ • Monitor Twitter for breaking news signals        │ │
│  │ • Trigger immediate RSS verification               │ │
│  │ • Queue push notifications                         │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              External Services                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Twitter API │  │ Anthropic API│  │Firebase Auth │  │
│  │  (Triggers)  │  │(Claude 4.1)  │  │   (JWT)      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

**Story Creation Flow**
```
1. RSS Feed → Raw Article (Cosmos DB)
2. Change Feed Trigger → Story Clustering Function
3. Find/Create Story Cluster (Cosmos DB)
4. If 2+ sources → Trigger Summarization Function
5. Call Claude API → Generate Summary
6. Store Summary in Story Cluster (Cosmos DB)
7. If 3+ sources → Mark as BREAKING
8. If major event → Queue Push Notification
```

**User Feed Generation Flow**
```
1. iOS App → GET /api/stories/feed
2. API checks Firebase JWT
3. API retrieves user profile (Cosmos DB)
4. API calls Recommendation Engine
5. Recommendation Engine scores all available stories
6. Apply diversity filter
7. Return top 20 personalized stories
8. iOS App renders feed
```

**Breaking News Detection Flow**
```
1. Twitter stream detects "BREAKING" from @Reuters
2. Extract entities: ["earthquake", "Japan", "7.2"]
3. Trigger immediate RSS poll for relevant feeds
4. If 2+ RSS sources confirm → Create DEVELOPING story
5. Continue monitoring for 3rd source
6. Once 3+ sources → Upgrade to BREAKING
7. Queue push notifications for premium users
```

### 3.3 Component Responsibilities

| Component | Responsibility | Scaling Strategy |
|-----------|---------------|------------------|
| RSS Ingestion | Fetch and parse RSS feeds | Horizontal (Durable Functions) |
| Story Clustering | Group related articles | Auto-scale on Cosmos change feed |
| Summarization | Generate AI summaries | Rate-limited queue processing |
| Story API | Serve stories to app | Auto-scale Container Apps (0-3 instances) |
| User API | User profiles & preferences | Auto-scale Container Apps |
| Rec Engine | Personalization algorithm | Dedicated instance with caching |
| Twitter Monitor | Breaking news detection | Single instance with reconnect logic |
| Cosmos DB | Data persistence | Serverless (auto-scales) |

---

## 4. Database Schema

### 4.1 Azure Cosmos DB Containers

**Container: `raw_articles`**
- **Partition Key**: `published_date` (YYYY-MM-DD format)
- **Time-to-Live (TTL)**: 30 days
- **Purpose**: Store raw RSS articles before clustering

```json
{
  "id": "reuters_20251008_143022_abc123",
  "source": "reuters",
  "source_url": "https://www.reuters.com",
  "source_tier": 1,
  "article_url": "https://www.reuters.com/world/asia/...",
  "title": "Earthquake strikes northern Japan",
  "description": "A 7.2 magnitude earthquake struck...",
  "published_at": "2025-10-08T14:30:22Z",
  "fetched_at": "2025-10-08T14:31:15Z",
  "published_date": "2025-10-08",
  "content": "Full article text if available...",
  "author": "John Smith",
  "entities": [
    {"text": "Japan", "type": "LOCATION"},
    {"text": "earthquake", "type": "EVENT"},
    {"text": "Hokkaido", "type": "LOCATION"}
  ],
  "category": "world",
  "tags": ["natural-disaster", "asia"],
  "language": "en",
  "story_fingerprint": "hash_japan_earthquake_hokkaido_7.2",
  "embedding": [0.123, 0.456, ...],
  "processed": false,
  "processing_attempts": 0
}
```

**Container: `story_clusters`**
- **Partition Key**: `category`
- **Time-to-Live (TTL)**: 90 days
- **Purpose**: Aggregated stories from multiple sources

```json
{
  "id": "story_20251008_earthquake_japan_001",
  "event_fingerprint": "japan_earthquake_7.2_hokkaido_20251008",
  "title": "7.2 Magnitude Earthquake Strikes Northern Japan",
  "category": "world",
  "tags": ["earthquake", "japan", "natural-disaster", "breaking"],
  "status": "BREAKING",
  "verification_level": 6,
  "first_seen": "2025-10-08T14:30:22Z",
  "last_updated": "2025-10-08T15:45:10Z",
  "source_articles": [
    "reuters_20251008_143022_abc123",
    "nhk_20251008_143145_def456",
    "ap_20251008_143322_ghi789",
    "bbc_20251008_143501_jkl012",
    "usgs_20251008_143630_mno345",
    "cnn_20251008_143820_pqr678"
  ],
  "summary": {
    "version": 2,
    "text": "A powerful earthquake struck off the coast of Hokkaido...",
    "generated_at": "2025-10-08T15:45:10Z",
    "model": "claude-sonnet-4-20250514",
    "word_count": 142,
    "generation_time_ms": 3240,
    "prompt_tokens": 1250,
    "completion_tokens": 180,
    "cached_tokens": 200,
    "cost_usd": 0.0048
  },
  "version_history": [
    {
      "version": 1,
      "timestamp": "2025-10-08T14:45:00Z",
      "summary": "Initial summary with 2 sources...",
      "source_count": 2,
      "status": "DEVELOPING"
    }
  ],
  "location": {
    "country": "Japan",
    "region": "Hokkaido",
    "coordinates": {
      "lat": 43.23,
      "lng": 145.67
    }
  },
  "importance_score": 95,
  "confidence_score": 98,
  "update_count": 3,
  "view_count": 0,
  "like_count": 0,
  "save_count": 0,
  "share_count": 0,
  "breaking_news": true,
  "breaking_detected_at": "2025-10-08T14:48:00Z",
  "push_notification_sent": true,
  "push_notification_sent_at": "2025-10-08T14:50:00Z",
  "needs_human_review": false,
  "human_reviewed": false,
  "corrections": []
}
```

**Container: `user_profiles`**
- **Partition Key**: `id` (user Firebase UID)
- **Time-to-Live (TTL)**: None (persist indefinitely)
- **Purpose**: User preferences and subscription status

```json
{
  "id": "firebase_uid_abc123xyz",
  "firebase_uid": "firebase_uid_abc123xyz",
  "email": "user@example.com",
  "created_at": "2025-09-01T12:00:00Z",
  "last_active": "2025-10-08T14:30:00Z",
  "subscription": {
    "tier": "paid",
    "started_at": "2025-09-15T10:00:00Z",
    "expires_at": "2026-09-15T10:00:00Z",
    "auto_renew": true,
    "platform": "ios",
    "original_transaction_id": "1000000123456789",
    "receipt_validated_at": "2025-10-01T08:00:00Z"
  },
  "preferences": {
    "categories": ["world", "tech", "science", "business"],
    "sources_boost": ["reuters", "bbc", "nature"],
    "sources_mute": ["tabloid_example"],
    "notification_settings": {
      "breaking_news": true,
      "threshold": "major",
      "quiet_hours": {
        "enabled": true,
        "start": "22:00",
        "end": "07:00",
        "timezone": "America/Los_Angeles"
      },
      "geographic_focus": ["US", "UK", "Japan"]
    },
    "reading_preferences": {
      "summary_length": "standard",
      "font_size": "medium",
      "theme": "auto"
    }
  },
  "location": {
    "country": "US",
    "state": "CA",
    "city": "San Francisco",
    "timezone": "America/Los_Angeles",
    "coordinates": {
      "lat": 37.7749,
      "lng": -122.4194
    },
    "last_updated": "2025-10-08T14:00:00Z"
  },
  "interaction_stats": {
    "total_stories_viewed": 1247,
    "total_stories_liked": 89,
    "total_stories_saved": 34,
    "total_stories_shared": 12,
    "total_sources_clicked": 156,
    "total_cards_flipped": 423,
    "avg_daily_views": 18,
    "engagement_score": 72
  },
  "personalization_profile": {
    "category_scores": {
      "world": 0.85,
      "tech": 0.92,
      "science": 0.78,
      "business": 0.65,
      "sports": 0.32,
      "entertainment": 0.41
    },
    "topic_scores": {
      "artificial-intelligence": 0.95,
      "climate-change": 0.82,
      "space-exploration": 0.88
    },
    "recency_preference": 0.75,
    "diversity_preference": 0.60,
    "last_updated": "2025-10-08T14:00:00Z"
  },
  "rate_limiting": {
    "daily_story_count": 8,
    "last_reset": "2025-10-08T00:00:00Z",
    "exceeded_limit": false
  },
  "device_tokens": [
    {
      "token": "apns_token_xyz789...",
      "platform": "ios",
      "added_at": "2025-09-01T12:05:00Z",
      "last_used": "2025-10-08T08:00:00Z"
    }
  ]
}
```

**Container: `user_interactions`**
- **Partition Key**: `user_id`
- **Time-to-Live (TTL)**: 180 days
- **Purpose**: Track user engagement for personalization

```json
{
  "id": "interaction_uuid_123",
  "user_id": "firebase_uid_abc123xyz",
  "story_id": "story_20251008_earthquake_japan_001",
  "interaction_type": "like",
  "timestamp": "2025-10-08T14:35:22Z",
  "session_id": "session_uuid_456",
  "dwell_time_seconds": 45,
  "card_flipped": true,
  "sources_clicked": ["reuters_20251008_143022_abc123"],
  "device_info": {
    "platform": "ios",
    "app_version": "1.0.0",
    "os_version": "17.0"
  }
}
```

**Container: `moderation_queue`**
- **Partition Key**: `status`
- **Time-to-Live (TTL)**: 30 days
- **Purpose**: Stories flagged for manual review

```json
{
  "id": "moderation_uuid_789",
  "story_id": "story_20251008_earthquake_japan_001",
  "flagged_at": "2025-10-08T14:50:00Z",
  "flagged_by": "automated_system",
  "reason": "major_casualty_event",
  "status": "pending",
  "priority": "high",
  "reviewed_by": null,
  "reviewed_at": null,
  "action_taken": null,
  "notes": null
}
```

### 4.2 Indexing Strategy

**raw_articles**
```javascript
// Composite indexes
["/published_date", "/source"]
["/published_date", "/category"]
["/story_fingerprint"]

// Single-field indexes (automatic)
/id
/processed
```

**story_clusters**
```javascript
// Composite indexes
["/category", "/last_updated"]
["/category", "/importance_score"]
["/status", "/last_updated"]
["/breaking_news", "/last_updated"]

// Single-field indexes
/id
/event_fingerprint
```

**user_profiles**
```javascript
// Single-field indexes
/id
/email
/subscription/tier
```

**user_interactions**
```javascript
// Composite indexes
["/user_id", "/timestamp"]
["/user_id", "/interaction_type"]
["/story_id", "/timestamp"]
```

### 4.3 Database Operations

**Estimated Request Units (RU) per Operation**

| Operation | RUs | Frequency | Daily RUs |
|-----------|-----|-----------|-----------|
| Insert raw article | 10 | 2,000/day | 20,000 |
| Read story by ID (point read) | 1 | 50,000/day | 50,000 |
| Query stories by category | 5 | 20,000/day | 100,000 |
| Update story cluster | 15 | 1,000/day | 15,000 |
| Insert interaction | 8 | 10,000/day | 80,000 |
| Query user profile | 1 | 50,000/day | 50,000 |
| **Total Daily** | | | **315,000 RUs** |

**Cost Calculation (Serverless)**
- 315,000 RUs/day × 30 days = 9,450,000 RUs/month
- 9.45M RUs × $0.285 per million = **$2.69/month** for requests
- Storage (10GB): **$2.50/month**
- **Total Cosmos DB: ~$5/month** (under budget estimate)

---

_[Note: This is the first section of the specification. The document continues with sections 5-14 covering Backend Services, API Specifications, iOS Application, Infrastructure, Security, Cost Management, Development Phases, Testing, Monitoring, and Appendices. The full specification would be approximately 15,000+ words. Would you like me to continue with specific sections?]_

---

## Quick Reference

### Project Identity
- **App Name**: Newsreel
- **Bundle ID**: com.onethum.newsreel
- **Developer**: One Thum Software
- **Repository**: https://github.com/OneThum/newsreel.git

### Tech Stack Summary
- **Platform**: iOS 26+ (SwiftUI)
- **Auth**: Firebase Authentication
- **Backend**: Azure Functions (Python), Azure Container Apps (FastAPI)
- **Database**: Azure Cosmos DB (Serverless)
- **AI**: Anthropic Claude Sonnet 4.1
- **Monitoring**: Azure Application Insights

### Key Features
- AI-curated news feed
- Multi-source summarization
- Flip-card UI for source attribution
- Breaking news detection
- Personalized content
- Free + Premium tiers

---

**Document Status**: Living Document  
**Last Updated**: October 8, 2025  
**Next Review**: As implementation progresses

