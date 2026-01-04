# 🚀 Clustering Overhaul Rollout Deployment Guide

**Date:** November 12, 2025
**Status:** READY FOR EXECUTION

## 📋 Deployment Overview

This guide provides the complete rollout procedure for deploying the new semantic clustering system with A/B testing infrastructure.

### 🎯 Deployment Goals
- **Zero Downtime**: Gradual rollout with A/B testing
- **Risk Mitigation**: Feature flags enable instant rollback
- **Performance Validation**: Real-time metrics monitoring
- **Quality Assurance**: Ground truth validation throughout rollout

### 🏗️ System Architecture

#### New Components Being Deployed
1. **Semantic Embeddings Service** (ACI) - Multilingual sentence transformers
2. **ML Similarity Scorer** - Feature-engineered clustering decisions
3. **Enhanced Entity Extraction** - Wikidata linking and disambiguation
4. **Event Signatures** - Action verb and event type classification
5. **Geographic Features** - Location-aware clustering
6. **Cluster Maintenance** - Automated merge/split/decay operations
7. **A/B Testing Framework** - Traffic splitting and performance monitoring

---

## 🚀 Deployment Procedure

### Prerequisites
```bash
# Ensure you have:
# - Azure CLI installed and logged in (az login)
# - Docker installed (for ACI deployment)
# - Python dependencies (scikit-learn, pandas)
# - Access to Azure subscription with required permissions

# Set environment variables (using your actual Azure resources)
export RESOURCE_GROUP="Newsreel-RG"
export FUNCTION_APP_NAME="newsreel-func-51689"
export LOCATION="centralus"
export ACR_NAME="newsreelacr"
export COSMOS_DB_NAME="newsreel-db-1759951135"
export STORAGE_ACCOUNT="newsreelstorage51494"
```

### Step 1: Pre-Deployment Validation
```bash
# Run the deployment script with validation only
./deploy_clustering_rollout.sh validate
```

### Step 2: Deploy Embedding Service
```bash
# Deploy the multilingual embeddings service to ACI
./deploy_clustering_rollout.sh embeddings

# Expected output:
# ✅ Embedding service deployed successfully!
# 🌐 Service URL: http://newsreel-embeddings.eastus.azurecontainer.io:8080
```

### Step 3: Train Similarity Model
```bash
# Train the ML similarity scoring model
./deploy_clustering_rollout.sh model

# Expected output:
# ✅ Ground truth dataset valid: 173 pairs
# 🎯 Training completed!
#    Accuracy: 0.89
#    Precision: 0.91
#    Recall: 0.87
#    F1: 0.89
```

### Step 4: Enable A/B Testing (30% Traffic)
```bash
# Configure A/B testing with 30% traffic to new system
./deploy_clustering_rollout.sh ab-test

# This sets the following Azure Function App settings:
# - CLUSTERING_USE_EMBEDDINGS=true
# - CLUSTERING_USE_EVENT_SIGNATURES=true
# - CLUSTERING_USE_GEOGRAPHIC=true
# - CLUSTERING_USE_WIKIDATA_LINKING=true
# - SCORING_OPTIMIZATION_ENABLED=true
# - CLUSTER_MAINTENANCE_ENABLED=true
```

### Step 5: Validation Testing
```bash
# Run post-deployment validation tests
./deploy_clustering_rollout.sh test

# Expected: All core functionality tests pass
```

### Step 6: Monitoring Setup
```bash
# Start monitoring and alerting
./deploy_clustering_rollout.sh monitor
```

### Option A: Full Automated Deployment
```bash
# Run complete deployment (all steps)
./deploy_clustering_rollout.sh full
```

---

## 📊 Rollout Monitoring Plan

### Phase 1: Initial Rollout (Days 1-2)
**Traffic:** 30% to new system, 70% to control

#### Key Metrics to Monitor:
```bash
# Check clustering performance
python3 scripts/monitor_clustering_improvements.py

# Monitor API performance
az monitor metrics list --resource /subscriptions/.../functionapp --metric "Http5xx"
```

#### Success Criteria:
- ✅ API response times <200ms P95
- ✅ No increase in error rates
- ✅ A/B traffic routing working correctly
- ✅ Embedding service healthy

### Phase 2: Medium Rollout (Days 3-4)
**Traffic:** 50% to new system

```bash
# Update traffic split
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --setting CLUSTERING_TRAFFIC_SPLIT="0.5"
```

#### Success Criteria:
- ✅ Clustering accuracy >85% F1 score
- ✅ Story completeness improved
- ✅ Duplicate detection rate <5%

### Phase 3: High Rollout (Days 5-6)
**Traffic:** 80% to new system

#### Success Criteria:
- ✅ All performance targets met
- ✅ User engagement metrics stable/improved
- ✅ Ground truth validation accuracy maintained

### Phase 4: Full Rollout (Day 7+)
**Traffic:** 100% to new system

---

## 🔍 Quality Assurance

### Automated Validation
```bash
# Run comprehensive test suite
python3 -m pytest tests/clustering_overhaul_test.py -v

# Validate ground truth performance
python3 -m pytest tests/create_ground_truth_dataset.py::test_ground_truth_accuracy -v
```

### Manual Quality Checks
```bash
# Check recent stories clustering quality
python3 scripts/check-recent-stories.py

# Validate API responses
python3 scripts/check-api-sources.sh
```

---

## 🚨 Rollback Procedures

### Emergency Rollback (Immediate)
```bash
# Disable all new features instantly
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --setting CLUSTERING_USE_EMBEDDINGS=false \
  --setting CLUSTERING_USE_EVENT_SIGNATURES=false \
  --setting CLUSTERING_USE_GEOGRAPHIC=false \
  --setting CLUSTERING_USE_WIKIDATA_LINKING=false \
  --setting SCORING_OPTIMIZATION_ENABLED=false \
  --setting CLUSTER_MAINTENANCE_ENABLED=false
```

### Gradual Rollback
```bash
# Reduce traffic to new system
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --setting CLUSTERING_TRAFFIC_SPLIT="0.1"
```

---

## 📈 Success Metrics

### Technical Metrics
- **API Latency**: <200ms P95 (target: <500ms)
- **Clustering Accuracy**: >87% F1 score
- **Duplicate Rate**: <5% false positives
- **Index Search**: <10ms P95
- **Ingestion Rate**: <10s P95 per article

### Business Metrics
- **Story Creation**: 50-100 new stories/day
- **Story Completeness**: +40% more articles grouped
- **Duplicate Reduction**: -67% fewer duplicate stories
- **User Experience**: Improved story coverage and relevance

---

## 📞 Support & Monitoring

### Real-time Monitoring
```bash
# Clustering improvement monitor
python3 scripts/monitor_clustering_improvements.py

# System health checks
./scripts/status-check.sh

# RSS ingestion monitoring
python3 scripts/monitor_rss_expansion.py
```

### Alert Configuration
- API latency >300ms
- Error rate >5%
- Clustering accuracy <80%
- Embedding service unhealthy

### Contact Information
- **Engineering Team**: engineering@newsreel.app
- **On-call Engineer**: Current rotation schedule
- **Documentation**: This guide + CLUSTERING_OVERHAUL_IMPLEMENTATION.md

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] Azure CLI authenticated
- [ ] Resource group exists
- [ ] Function App deployed
- [ ] Docker available
- [ ] Python dependencies installed

### Deployment Steps
- [ ] Embedding service deployed to ACI
- [ ] Similarity model trained
- [ ] A/B testing configured (30% traffic)
- [ ] Validation tests passed
- [ ] Monitoring enabled

### Post-Deployment Validation
- [ ] Traffic routing working correctly
- [ ] Performance metrics within targets
- [ ] Error rates unchanged
- [ ] Ground truth accuracy maintained

### Rollout Phases
- [ ] Phase 1 (30%): Days 1-2 monitoring
- [ ] Phase 2 (50%): Days 3-4 validation
- [ ] Phase 3 (80%): Days 5-6 verification
- [ ] Phase 4 (100%): Day 7+ full deployment

---

## 🎯 Final Status: DEPLOYMENT READY

The Newsreel clustering overhaul rollout is **fully prepared for production deployment**. All infrastructure, testing, monitoring, and rollback procedures are in place.

**Execute deployment with confidence using the provided scripts and monitoring procedures.**

---

*Deployment Guide Version: 1.0*  
*Created: November 12, 2025*  
*Ready for Execution: ✅ YES*
