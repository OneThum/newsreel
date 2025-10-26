# Database Cleanup Scripts

**⚠️ DESTRUCTIVE OPERATIONS - READ CAREFULLY**

---

## Overview

These scripts permanently delete articles from Cosmos DB. Use them with extreme caution!

---

## Scripts

### 1. `cleanup_old_articles.py`

**Purpose**: Delete old articles, keep recent ones  
**Keeps**: Articles ingested in the last hour  
**Deletes**: Everything older than 1 hour  
**Use Case**: Maintain a small test dataset, reduce database size

**Usage**:
```bash
cd Azure/tests
python3 scripts/cleanup_old_articles.py
```

**Safety**:
- ✅ Keeps recent data (last hour)
- ⚠️  Requires confirmation before deletion
- 📊 Shows count before deletion

**Example Output**:
```
⏰ Cutoff time: 2025-10-26 00:15:00 UTC
   (Keeping articles ingested after this time)

Found 145,000 articles to delete (older than 1 hour)
Found 1,479 recent articles to keep (last hour)

Delete 145,000 old articles? (y/N):
```

---

### 2. `cleanup_all_articles.py`

**Purpose**: DELETE ALL ARTICLES from database  
**Keeps**: NOTHING  
**Deletes**: EVERYTHING  
**Use Case**: Complete system reset, start fresh

**Usage**:
```bash
cd Azure/tests
python3 scripts/cleanup_all_articles.py
```

**Safety**:
- ⚠️  **EXTREME CAUTION**
- 🔒 **THREE confirmations required**:
  1. Type "DELETE ALL ARTICLES"
  2. Type "YES I AM SURE"
  3. Type "CONFIRM DELETE"
- ⚠️  **CANNOT BE UNDONE**

**Confirmations Required**:
```
⚠️  WARNING: DESTRUCTIVE OPERATION ⚠️

This script will DELETE ALL ARTICLES from Cosmos DB!
This operation is PERMANENT and CANNOT BE UNDONE!

Type 'DELETE ALL ARTICLES' to continue: DELETE ALL ARTICLES

⚠️  Are you absolutely sure?
Type 'YES I AM SURE' to proceed: YES I AM SURE

⚠️  FINAL WARNING
Type 'CONFIRM DELETE' to proceed: CONFIRM DELETE
```

---

## From Health Report Dashboard

Both scripts can be triggered from the health report:

```
file:///Users/.../Newsreel/Azure/tests/reports/health_report.html
```

**Buttons**:
1. **🧹 Delete Old Articles** (orange) - Runs `cleanup_old_articles.py`
2. **⚠️ DELETE ALL ARTICLES** (red) - Runs `cleanup_all_articles.py`

**How it works**:
1. Click button
2. Read warning in popup
3. Click OK to copy command
4. Paste in terminal
5. Follow prompts carefully

---

## Safety Features

### Multiple Confirmations
- Scripts require explicit typed confirmations
- Cannot accidentally delete by hitting Enter
- Must type exact phrases

### Progress Tracking
```
🗑️  Deleting articles...
  Deleted 100/145,000 articles (0.1%)
  Deleted 200/145,000 articles (0.1%)
  ...
```

### Summary Report
```
================================================================================
DELETION COMPLETE
================================================================================
✓ Successfully deleted: 145,000 articles
⚠️  Failed to delete: 0 articles

Timestamp: 2025-10-26 01:20:00 UTC
```

---

## When to Use

### `cleanup_old_articles.py` ✅
**Good for**:
- Testing with fresh data
- Reducing database costs
- Maintaining a small test dataset
- Keeping last hour of data for debugging

**Example scenarios**:
- "I want to test RSS ingestion with a clean slate but keep recent articles"
- "Database is too large, trim it down to recent data"
- "Need to free up space but not lose everything"

### `cleanup_all_articles.py` ⚠️
**Good for**:
- Complete system reset
- Starting from scratch
- Clearing test data entirely
- Troubleshooting database corruption

**Example scenarios**:
- "I want to completely reset the system"
- "Need to clear all test data before going live"
- "Database has corrupt data, need fresh start"

### When NOT to use ❌
**DON'T USE IN PRODUCTION** unless you know exactly what you're doing!

These scripts are designed for **testing/development** environments.

---

## Troubleshooting

### "No articles to delete"
- Database is already empty
- Check connection string in `.env`

### "Failed to delete X articles"
- Network issues
- Permission issues
- First 5 errors are shown

### "Connection failed"
- Check `COSMOS_CONNECTION_STRING` in `.env`
- Verify Cosmos DB is accessible
- Check network connection

---

## Recovery

### If you deleted by accident:
1. **Stop immediately** (Ctrl+C)
2. Articles deleted so far are **gone forever**
3. Remaining articles are **still in database**
4. Check what's left:
   ```bash
   cd Azure/tests
   python3 diagnostics/check_rss_ingestion.py
   ```

### No backup/restore:
⚠️  These scripts **do not create backups**  
⚠️  Deletion is **permanent and immediate**  
⚠️  No "undo" or "restore" functionality

**Prevention is the only solution** - read prompts carefully!

---

## Best Practices

### Before Running
1. ✅ Read all warnings
2. ✅ Verify you're in correct environment
3. ✅ Check `.env` points to correct database
4. ✅ Consider if you really need to delete
5. ✅ Announce to team if shared database

### During Running
1. ✅ Read each prompt carefully
2. ✅ Type confirmations exactly as shown
3. ✅ Don't run if uncertain
4. ✅ Watch progress output
5. ✅ Can abort with Ctrl+C

### After Running
1. ✅ Verify results in summary
2. ✅ Check health report dashboard
3. ✅ Run diagnostics to verify state
4. ✅ Restart RSS ingestion if needed

---

## Technical Details

### What Gets Deleted

**Articles Container** (`raw_articles`):
- ✅ All raw article documents
- ✅ All ingestion metadata
- ✅ All processing flags

**Stories Container** (`story_clusters`):
- ❌ NOT deleted (kept intact)
- Stories remain but may have broken source links

### Deletion Method
- Uses Cosmos DB `delete_item()` API
- Requires both `id` and `partition_key`
- Processes one article at a time
- No batch deletion (safer)

### Performance
- **Speed**: ~100-500 articles/second
- **145,000 articles**: ~5-10 minutes
- **Progress updates**: Every 100 articles

---

## Support

**Problems?**
- Check `Azure/tests/diagnostics/system_health_report.py`
- Review Cosmos DB logs in Azure Portal
- Contact: dave@onethum.com

**Documentation**:
- Main README: `Azure/tests/README.md`
- Health Report Features: `Azure/tests/HEALTH_REPORT_FEATURES.md`

---

**Last Updated**: October 26, 2025  
**Status**: ✅ Production Ready (for dev/test environments)

