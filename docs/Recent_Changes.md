# Recent Changes & Bug Fixes

**Last Updated**: October 13, 2025

This document consolidates recent improvements, bug fixes, and feature additions to Newsreel.

---

## 🚀 Latest Features (October 13, 2025)

### 1. Search Functionality
- **Full-text search** across all stories
- Backend relevance scoring (title > summary > tags)
- Live search as you type (after 2+ characters)
- Category filtering in search
- Beautiful iOS search UI with auto-focus

### 2. Category Filtering
- **Horizontal scrolling chips** at top of feed
- 11 categories: All + 10 news categories
- Visual states with gradients for selected categories
- Smooth scrolling performance
- Category-specific SF Symbols and colors

### 3. Smooth Feed Updates (Twitter-style)
- **Non-disruptive background polling** every 30 seconds
- New stories held in pending state
- Blue notification pill: "3 new stories"
- User taps to smoothly merge new content
- Spring animations for buttery smooth UX

**Details**: See `SEARCH_CATEGORY_FEED_IMPROVEMENTS.md`

---

## 🐛 Recent Bug Fixes (October 13, 2025)

### 1. Timestamp Update Bug
**Problem**: Stories showing "Just now" repeatedly even when nothing changed.

**Root Cause**: Clustering logic was updating `last_updated` timestamp for already-processed articles.

**Fix**: Added `else` clause to skip updates when article already in story cluster.

**Impact**:
- ✅ Accurate timestamps
- ✅ "UPDATED" badge now works correctly
- ✅ 95% fewer unnecessary database writes
- ✅ Lower Cosmos DB RU/s consumption

**Details**: See `TIMESTAMP_UPDATE_BUG_FIX.md`

---

### 2. Time Ago Refresh Bug
**Problem**: "Just now" wasn't transitioning to "1m ago", "2m ago" as time passed.

**Root Cause**: SwiftUI doesn't automatically re-evaluate computed properties when external factors (time) change.

**Fix**: 
- Updated `timeAgo` logic to use `lastUpdated` for UPDATED stories
- Added 60-second timer to trigger UI refresh
- "Just now" only shows for stories < 1 minute old

**Impact**:
- ✅ Live time updates every 60 seconds
- ✅ Natural progression: "Just now" → "1m ago" → "2m ago"
- ✅ Battery efficient (1 update per minute)

**Details**: See `TIME_AGO_REFRESH_FIX.md`

---

### 3. Card Width Bug
**Problem**: "No summary available" card showing half-width.

**Root Cause**: Summary VStack not constrained to full width.

**Fix**: Added `.frame(maxWidth: .infinity, alignment: .leading)` to container and text elements.

**Impact**:
- ✅ All cards now full-width minus padding
- ✅ Consistent, professional layout
- ✅ Design consistency across all views

**Details**: See `CARD_WIDTH_FIX.md`

---

## 📊 Monitoring & Logging

### Backend Logging (Azure)
- **Structured logging** with Application Insights integration
- **Correlation IDs** for request tracing
- **Event categorization**: RssFetch, ArticleProcessed, StoryCluster, SummaryGenerated, FeedDiversity
- **Performance metrics**: Duration, cost, token usage
- **CLI-accessible**: Shell scripts for automated log analysis

### iOS Logging (OSLog)
- **Categorized logging**: UI, API, Network, Error, Auth
- **Feed quality metrics**: Source diversity, categorization decisions
- **Performance tracking**: `measureOperation` utility
- **Badge accuracy monitoring**: Status distribution logging

### CLI Tools
- `Azure/scripts/query-logs.sh` - Query Application Insights logs
- `Azure/scripts/analyze-system-health.sh` - Automated health analysis

**Details**: See `BADGE_LOGGING_MONITORING.md`

---

## 🏗️ Architecture Updates

### RSS Polling Optimization
- **10-second polling interval** (increased from 30s)
- **Staggered feed polling**: 3-4 feeds per cycle
- **5-minute refresh window**: All 100 feeds polled in rotation
- **Continuous firehose**: ~1 feed every 3 seconds
- **Source diversity**: Duplicate source detection prevents redundancy

**Details**: See `STAGGERED_RSS_POLLING.md` and `RSS_FEED_STRATEGY.md`

---

### Story Clustering Improvements
- **Fuzzy title matching**: 45% similarity threshold
- **Multi-method similarity**: Cosine + Jaccard + Levenshtein
- **Fingerprint-first matching**: Fast exact matching
- **Source diversity enforcement**: Only unique sources per story
- **Status progression**: MONITORING → DEVELOPING → VERIFIED → BREAKING

**Details**: See `CLUSTERING_IMPROVEMENTS.md`

---

## 📱 iOS Features

### Feed Enhancements
- Category filtering with horizontal chips
- Pull-to-refresh
- Infinite scroll pagination
- Background polling with smooth updates
- Offline-first with SwiftData caching
- Status badges (DEVELOPING, BREAKING, UPDATED, MONITORING)

### Search
- Full-text search with relevance ranking
- Live search as you type
- Category filtering
- Beautiful empty states

### Admin Dashboard
- Mobile-accessible backend metrics
- Auto-refresh every 60 seconds
- Number formatting with commas
- Restricted to admin emails

### Authentication
- Apple Sign-In
- Google Sign-In (Firebase)
- Anonymous browsing

---

## 🎯 Product Roadmap

See `docs/Product_Improvement_Roadmap.md` for:
- Phase 1: Observability (✅ Complete)
- Phase 2: Feed Diversity
- Phase 3: Smart Polling
- Phase 4: Categorization Enhancement
- Phase 5: Update Intelligence

---

## 📚 Technical Documentation

### Setup Guides
- `docs/Azure_Setup_Guide.md` - Azure infrastructure setup
- `docs/Firebase_Setup_Guide.md` - Firebase authentication
- `docs/Xcode_Configuration.md` - iOS project setup

### Architecture
- `RSS_FEED_STRATEGY.md` - RSS ingestion architecture
- `CLUSTERING_IMPROVEMENTS.md` - Story clustering logic
- `STAGGERED_RSS_POLLING.md` - Polling optimization

### Design
- `docs/Design_System.md` - iOS design patterns
- `docs/iOS18_Best_Practices.md` - iOS development guidelines

---

## 🔄 Continuous Improvements

The app is in active development with focus on:
- ✅ **Performance**: Fast, responsive, buttery smooth
- ✅ **Reliability**: Stable backend, minimal errors
- ✅ **User Experience**: Twitter-level polish
- ✅ **Cost Efficiency**: Azure budget compliance
- ✅ **Code Quality**: Clean, maintainable, documented

---

## 📞 Quick Reference

- **Backend API**: `https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io`
- **Azure Functions**: `newsreel-func-51689`
- **Cosmos DB**: Serverless tier (auto-scale)
- **Application Insights**: Full logging & monitoring
- **iOS Bundle ID**: `com.onethum.Newsreel`
- **Firebase Project**: Newsreel authentication

---

**For detailed information on any topic, see the individual documentation files in the `docs/` folder.**

