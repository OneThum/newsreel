# Newsreel API Test Harness - Quick Start

**Get your Newsreel API tested in 5 minutes**

---

## Prerequisites

- Python 3.11+
- Access to Azure Cosmos DB (connection string)
- Access to Newsreel API (URL)

---

## Step 1: Install Dependencies

```bash
cd Azure/tests
pip install -r requirements.txt
```

---

## Step 2: Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your favorite editor
```

Required variables:
```bash
COSMOS_CONNECTION_STRING="AccountEndpoint=https://..."
API_URL="https://newsreel-api.thankfulpebble-0dde6120.centralus.azurecontainerapps.io"
```

---

## Step 3: Run Diagnostics

### Option A: Run All Diagnostics (Recommended)

```bash
chmod +x run_all_diagnostics.sh
./run_all_diagnostics.sh
```

This will:
1. Check RSS ingestion health
2. Check clustering quality
3. Generate comprehensive HTML report

### Option B: Run Individual Checks

```bash
# Check RSS ingestion
python diagnostics/check_rss_ingestion.py

# Check clustering quality
python diagnostics/check_clustering_quality.py

# Generate full report
python diagnostics/system_health_report.py
```

---

## Step 4: View Results

### Console Output
All diagnostic scripts output colored results to the console:
- 🟢 Green = Healthy
- 🟡 Yellow = Warning
- 🔴 Red = Critical Issue

### HTML Report
```bash
# Open the comprehensive HTML report
open reports/health_report.html
```

### Bug Report
```bash
# Read the detailed bug analysis
cat reports/BUGS_DISCOVERED.md
```

---

## Step 5: Run Unit Tests (Optional)

```bash
# Run all unit tests
pytest unit/ -v

# Run specific test file
pytest unit/test_rss_parsing.py -v

# Run with coverage
pytest --cov=../functions --cov-report=html
```

---

## Understanding the Results

### RSS Ingestion Check

**What it checks:**
- ✓ Are feeds being polled every 10 seconds?
- ✓ Are we polling 3 feeds per cycle?
- ✓ Are articles being stored correctly?
- ✓ What's the success rate per feed?

**Expected Results:**
- Articles per minute: 10-15
- Unique sources: 10+
- Processing lag: < 1 minute

**Red Flags:**
- ✗ No articles in last 10 minutes = RSS ingestion stopped
- ✗ Only 1-2 sources = Feed diversity problem
- ✗ Processing lag > 5 minutes = Clustering bottleneck

### Clustering Quality Check

**What it checks:**
- ✓ Are articles clustering correctly?
- ✓ Are duplicate sources being prevented?
- ✓ What's the multi-source rate?
- ✓ Are status transitions working?

**Expected Results:**
- Multi-source rate: 20-40%
- Average sources per story: 1.5-2.5
- No duplicate sources in stories
- Status distribution: mostly VERIFIED/DEVELOPING

**Red Flags:**
- ✗ High duplicate rate (>10%) = Deduplication broken
- ✗ Low multi-source rate (<15%) = Clustering threshold too high
- ✗ High MONITORING rate (>50%) = Too many single-source stories

### System Health Report

**What it shows:**
- Overall system status
- Component health (database, RSS, clustering, summarization)
- Performance metrics
- Cost analysis

**Key Metrics:**
- Summary coverage: Should be >30% (target 50%)
- Multi-source rate: Should be >20% (target 30%)
- Articles per hour: Should be 1000-2000
- API response time: Should be <500ms

---

## Common Issues & Solutions

### Issue: Connection to Cosmos DB failed

**Solution:**
```bash
# Check connection string
echo $COSMOS_CONNECTION_STRING

# Verify it's in .env
cat .env | grep COSMOS

# Test connection
python -c "from azure.cosmos import CosmosClient; client = CosmosClient.from_connection_string('$COSMOS_CONNECTION_STRING'); print('✓ Connected')"
```

### Issue: No recent articles found

**Possible causes:**
1. RSS ingestion function not running
2. Azure Functions not deployed
3. Network/firewall blocking RSS feeds

**Solution:**
```bash
# Check Azure Functions status
az functionapp list --resource-group Newsreel-RG

# Check function logs
az functionapp logs tail --name newsreel-func-51689 --resource-group Newsreel-RG
```

### Issue: High clustering errors

**Possible causes:**
1. Clustering threshold too high/low
2. Fingerprint collisions
3. Topic conflict detection overly aggressive

**Solution:**
- Review `reports/BUGS_DISCOVERED.md` for specific issues
- Run clustering quality check with verbose output
- Adjust threshold in `config.py` if needed

### Issue: Low summarization coverage

**Possible causes:**
1. Backfill disabled (cost saving measure)
2. Batch processing not running
3. Hitting daily summary limit

**Solution:**
```bash
# Check if backfill is enabled
grep SUMMARIZATION_BACKFILL_ENABLED ../functions/shared/config.py

# Check batch processing status
python -c "from shared.config import config; print(f'Batch enabled: {config.BATCH_PROCESSING_ENABLED}')"
```

---

## Next Steps

### Immediate Actions

1. **Review Bug Report**: Read `reports/BUGS_DISCOVERED.md` for detailed analysis
2. **Fix Critical Issues**: Address P0 bugs first (duplicate sources, missing sources)
3. **Monitor Continuously**: Set up daily automated health checks

### Run Specific Queries

```sql
-- In Azure Portal > Cosmos DB > Data Explorer

-- Check for stories with no sources (Bug #2)
SELECT * FROM c 
WHERE NOT IS_DEFINED(c.source_articles) 
   OR ARRAY_LENGTH(c.source_articles) = 0
LIMIT 100

-- Check for duplicate sources (Bug #1)
SELECT c.id, c.title, c.source_articles
FROM c
WHERE ARRAY_LENGTH(c.source_articles) >= 2
LIMIT 100
```

### Set Up Continuous Monitoring

```bash
# Add to crontab for hourly checks
0 * * * * cd /path/to/Newsreel/Azure/tests && ./run_all_diagnostics.sh >> logs/diagnostics.log 2>&1
```

---

## Getting Help

### Documentation
- **Full Test Harness README**: `README.md`
- **Bug Report**: `reports/BUGS_DISCOVERED.md`
- **Project Status**: `../../docs/PROJECT_STATUS.md`

### Logs
- **Application Insights**: Azure Portal > Application Insights
- **Function Logs**: `az functionapp logs tail`
- **Test Logs**: `reports/*.log`

### Contact
- **Developer**: dave@onethum.com
- **Azure Portal**: https://portal.azure.com
- **GitHub**: [Repository URL]

---

## FAQ

**Q: How often should I run diagnostics?**

A: 
- **During development**: After every major code change
- **In production**: Daily automated checks
- **When issues arise**: Immediately

**Q: What's a "good" multi-source rate?**

A: 
- **Excellent**: >40%
- **Good**: 30-40%
- **Acceptable**: 20-30%
- **Poor**: <20%

**Q: Why is my summarization coverage so low?**

A:
- Backfill may be disabled (cost control)
- Batch processing may not be running
- Check `BATCH_PROCESSING_ENABLED` in config

**Q: How do I know if RSS ingestion is working?**

A:
Run `check_rss_ingestion.py` and look for:
- Articles in last 10 minutes > 50
- Articles per minute: 10-15
- Most recent article: < 30 seconds ago

**Q: Can I run tests in CI/CD?**

A:
Yes! See `README.md` section "CI/CD Integration" for GitHub Actions example.

---

**Quick Start Complete!** 🎉

You now have a comprehensive view of your Newsreel API health.

Next: Review `reports/BUGS_DISCOVERED.md` for detailed findings and recommendations.

