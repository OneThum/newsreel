# Newsreel Azure Backend

**Backend services for the Newsreel iOS app**

---

## 📚 Documentation

All documentation has been moved to the `/docs` folder in the project root.

### For Backend Setup & Deployment
- **[/docs/Azure_Setup_Guide.md](../docs/Azure_Setup_Guide.md)** - Complete Azure infrastructure guide
- **[/docs/azure/QUICK_START.md](../docs/azure/QUICK_START.md)** - Quick start guide
- **[/docs/azure/DEPLOYMENT_SUMMARY.md](../docs/azure/DEPLOYMENT_SUMMARY.md)** - Deployment details
- **[/docs/azure/MONITORING_GUIDE.md](../docs/azure/MONITORING_GUIDE.md)** - Logging and monitoring
- **[/docs/azure/QUICK_REFERENCE.md](../docs/azure/QUICK_REFERENCE.md)** - URLs and commands

### For Current Status
- **[/docs/APP_STORE_READINESS.md](../docs/APP_STORE_READINESS.md)** - Launch checklist
- **[/docs/PROJECT_STATUS.md](../docs/PROJECT_STATUS.md)** - System status

---

## 🏗️ Structure

```
Azure/
├── api/                    # FastAPI REST API (Container Apps)
│   ├── app/
│   │   ├── routers/       # API endpoints
│   │   ├── services/      # Business logic
│   │   └── middleware/    # Auth, logging
│   ├── Dockerfile
│   └── requirements.txt
│
├── functions/              # Azure Functions (Python)
│   ├── function_app.py    # Main functions (RSS, clustering, summarization)
│   ├── shared/            # Shared utilities
│   ├── host.json
│   └── requirements.txt
│
├── scripts/                # CLI automation tools
│   ├── check-story-sources.py
│   ├── diagnose-story-sources.py
│   └── (more scripts)
│
└── README.md              # ← You are here
```

---

## 🚀 Quick Deploy

### Functions
```bash
cd functions
func azure functionapp publish newsreel-func-51689 --python
```

### API (Container Apps)
```bash
cd api
az acr build --registry newsreelacr --image newsreel-api:latest .
az containerapp update --name newsreel-api --resource-group Newsreel-RG \
  --image newsreelacr.azurecr.io/newsreel-api:latest
```

---

## 🔗 Live Services

- **API**: https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io
- **Functions**: newsreel-func-51689.azurewebsites.net
- **Azure Portal**: https://portal.azure.com (Resource Group: Newsreel-RG)

---

## 📊 Current Status

- ✅ **RSS Ingestion**: ~1,900 articles/hour from 100+ sources
- ✅ **Story Clustering**: Multi-source deduplication working
- ✅ **AI Summarization**: Claude Sonnet 4, 33.8%+ coverage
- ✅ **API**: FastAPI with Firebase auth, <500ms response time
- ✅ **Monitoring**: Application Insights with full logging
- ✅ **Costs**: $96/month (within $150 budget)

---

For complete documentation, see **[/docs](../docs/)** folder.
