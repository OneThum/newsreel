# Newsreel Quick Reference Card

**Last Updated**: October 8, 2025

---

## 🚨 CRITICAL RULES

### Budget Constraints (HARD LIMITS)
```
Azure Services:   MAX $150/month  ⚠️ CANNOT EXCEED
Total Project:    MAX $300/month  ⚠️ CANNOT EXCEED
```

### Before Creating ANY Azure Resource
1. ✅ Check if resource already exists
2. ✅ Evaluate if existing resource can be repurposed
3. ✅ Verify current month's costs
4. ✅ Get approval if creating new resource
5. ✅ Document justification

---

## 📋 Project Identity

| Item | Value |
|------|-------|
| **App Name** | Newsreel |
| **Display Name** | Newsreel |
| **Bundle ID** | `com.onethum.newsreel` |
| **Version** | 1.0.0 |
| **Build** | 1 |
| **Platform** | iOS 18.0+ |
| **Developer** | One Thum Software |
| **Repository** | https://github.com/OneThum/newsreel.git |

---

## ☁️ Azure Subscription

| Item | Value |
|------|-------|
| **Name** | Newsreel Subscription |
| **ID** | `d4abcc64-9e59-4094-8d89-10b5d36b6d4c` |
| **Directory** | One Thum Software (onethum.com) |
| **Region** | West US 2 |
| **Access** | Azure CLI only |

## 🔥 Firebase Project

| Item | Value |
|------|-------|
| **Project ID** | newsreel-865a5 |
| **Google App ID** | 1:940368851541:ios:7016e27c1cd8d535c15adc |
| **Bundle ID** | com.onethum.newsreel |
| **Console URL** | https://console.firebase.google.com/project/newsreel-865a5 |
| **Features** | Auth ✅ \| Cloud Messaging ✅ \| Analytics ❌ \| Ads ❌ |

---

## 💰 Current Budget Allocation

### Azure Services ($96/month projected)
```
Cosmos DB:          $31  (Serverless)
Container Apps:     $40  (0.25 vCPU, scale-to-zero)
Functions:          $15  (Consumption plan)
Storage:            $5   (Blob + Queue)
App Insights:       $5   (Limited to 5GB/month)
────────────────────────
Azure Total:        $96  ($54 under budget ✅)
```

### External Services ($180/month projected)
```
Claude API:         $80  (with prompt caching)
Twitter API:        $100 (Basic tier)
Firebase Auth:      $0   (Free tier)
RevenueCat:         $0   (Free up to $2.5k MRR)
────────────────────────
External Total:     $180
```

### Total Project: $276/month
**Buffer**: $24 (8% under budget)

---

## 🛠️ Essential Commands

### Check Existing Resources
```bash
# Login and set subscription
az login
az account set --subscription "d4abcc64-9e59-4094-8d89-10b5d36b6d4c"

# List ALL resources
az resource list --output table

# Check specific services
az cosmosdb list --output table
az functionapp list --output table
az storage account list --output table
az containerapp list --output table

# View current costs
az consumption usage list \
  --start-date $(date -d "$(date +%Y-%m-01)" +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --output table
```

### Cost Monitoring
```bash
# Daily cost check
az consumption usage list \
  --subscription d4abcc64-9e59-4094-8d89-10b5d36b6d4c \
  --start-date $(date -d "$(date +%Y-%m-01)" +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d)

# By resource group
az consumption usage list \
  --resource-group newsreel-prod-rg \
  --output table
```

---

## 📊 Budget Alert Thresholds

| Threshold | Azure | Total | Action |
|-----------|-------|-------|--------|
| **80%** | $120 | $240 | Review & optimize |
| **90%** | $135 | $270 | **Immediate action** |
| **100%** | $150 | $300 | **🚨 HARD STOP** |

---

## 📚 Key Documents

| Document | Purpose |
|----------|---------|
| [README](../README.md) | Project overview |
| [Project Status](PROJECT_STATUS.md) | ⭐ What's done, what's next |
| [Product Spec](Product_Specification.md) | Complete technical spec |
| [Roadmap](Development_Roadmap.md) | Implementation phases |
| [Xcode Config](Xcode_Configuration.md) | Project settings & App Store prep |
| [iOS 18 Best Practices](iOS18_Best_Practices.md) | Modern SwiftUI patterns |
| [Design System](Design_System.md) | Liquid Glass UI + Outfit typography |
| [Font Setup](Font_Setup_Guide.md) | Outfit font configuration |
| [Firebase Setup](Firebase_Setup_Guide.md) | Authentication & messaging |
| [Azure Setup](Azure_Setup_Guide.md) | Infrastructure deployment |
| [RevenueCat Setup](RevenueCat_Setup_Guide.md) | Subscription management |
| [Cost Management](Cost_Management.md) | Budget tracking & optimization |
| [Index](INDEX.md) | Documentation hub |

---

## 🎯 Tech Stack Summary

### Frontend
- **Platform**: iOS 18.0+ (Xcode 16+)
- **Framework**: SwiftUI (iOS 18 features)
- **Design**: Liquid Glass + Outfit font
- **Features**: Scroll transitions, materials, haptics
- **Auth**: Firebase Auth
- **Subscriptions**: RevenueCat

### Backend
- **APIs**: Azure Container Apps (FastAPI)
- **Functions**: Azure Functions (Python 3.11)
- **Database**: Azure Cosmos DB (Serverless)
- **AI**: Anthropic Claude Sonnet 4.1
- **Monitoring**: Azure Application Insights

---

## 🔑 External Services

| Service | Purpose | Cost |
|---------|---------|------|
| **Anthropic** | AI summarization | $80/mo |
| **Twitter/X** | Breaking news detection | $100/mo |
| **Firebase** | Authentication | $0 (free tier) |
| **RevenueCat** | Subscription management | $0 (free up to $2.5k MRR) |

**Logins**:
- Firebase: https://console.firebase.google.com/project/newsreel-865a5
- Anthropic: https://console.anthropic.com/
- Twitter Dev: https://developer.twitter.com/
- RevenueCat: https://app.revenuecat.com/

---

## 📝 Development Phases

| Phase | Duration | Status |
|-------|----------|--------|
| **Phase 1**: MVP Backend | Weeks 1-2 | 📝 Planning |
| **Phase 2**: AI Summarization | Weeks 3-4 | 📝 Planned |
| **Phase 3**: iOS App MVP | Weeks 5-6 | 📝 Planned |
| **Phase 4**: Personalization | Weeks 7-8 | 📝 Planned |
| **Phase 5**: Premium Features | Weeks 9-10 | 📝 Planned |
| **Phase 6**: Launch | Week 11+ | 📝 Planned |

---

## ⚡ Quick Wins for Cost Reduction

If approaching budget:

1. **Reduce App Insights to 1GB/day** → Save $5/mo
2. **Reduce RSS polling frequency (5min → 10min)** → Save $5-10/mo
3. **Summarize only 3+ source stories** → Save $10-20/mo
4. **Reduce breaking news monitoring (2min → 5min)** → Save $2-5/mo
5. **Optimize Cosmos DB queries** → Save $5-15/mo

---

## 🆘 Emergency Contacts

| Issue | Contact |
|-------|---------|
| **Budget exceeded** | CTO |
| **Azure issues** | DevOps Team |
| **API problems** | Backend Lead |
| **iOS issues** | iOS Lead |
| **General** | Development Lead |

---

## ✅ Pre-Deployment Checklist

Before deploying ANYTHING:

- [ ] Checked for existing resources
- [ ] Verified current month's Azure costs
- [ ] Confirmed budget headroom
- [ ] Reviewed resource specifications
- [ ] Planned for scale-to-zero/serverless
- [ ] Documented resource purpose
- [ ] Tagged resources appropriately
- [ ] Set up cost alerts
- [ ] Tested in development first
- [ ] Got approval (if new resource)

---

**Print this card and keep it handy!** 📌

**Full docs**: See [Documentation Index](INDEX.md)

