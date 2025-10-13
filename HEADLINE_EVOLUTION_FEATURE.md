# ✨ Feature: Dynamic Headline Re-evaluation

**Deployed**: 2025-10-13 06:47 UTC  
**Status**: **ACTIVE**

---

## 🎯 Overview

Headlines now **evolve** as breaking news develops and more sources report on a story. As verification increases from 1 → 3 → 5 → 10+ sources, the AI re-evaluates and updates headlines to reflect the most current, verified information.

---

## 💡 Why This Matters

### **Breaking News is Dynamic**

Initial reports are often vague or incomplete:
- **Initial**: "Explosion reported in Tennessee"
- **3 sources**: "18 missing after Tennessee explosives plant blast"  
- **5+ sources**: "No survivors found in Tennessee explosives factory blast, sheriff confirms"

### **Headlines Should Reflect Truth**

As stories develop:
- ✅ **More specific** - Exact numbers, names, locations
- ✅ **More accurate** - Multiple sources verify facts
- ✅ **More current** - Latest developments prioritized
- ✅ **More complete** - Key details emerge

---

## 🔧 How It Works

### **Trigger Points**

Headlines are re-evaluated at key verification thresholds:

1. **3 sources** - Story becomes DEVELOPING/BREAKING
2. **5 sources** - Significant verification level
3. **10 sources** - Major story with high confidence
4. **15 sources** - Extensive coverage
5. **BREAKING promotion** - When story status changes to BREAKING

### **The Process**

```
1. Story gains sources (e.g., 2 → 3)
   ↓
2. Threshold reached (3 sources)
   ↓
3. System calls generate_updated_headline()
   ↓
4. Claude analyzes all source headlines
   ↓
5. Generates improved headline based on:
   - Most current, verified information
   - Facts multiple sources agree on
   - Latest developments (not initial reports)
   - Specific details (numbers, names, locations)
   ↓
6. Validates headline quality
   ↓
7. Updates story cluster with new headline
   ↓
8. Logs change for monitoring
```

---

## 📝 AI Prompt Strategy

### **System Prompt**

```
You are a senior news editor crafting headlines for breaking news. Your headlines are:
- ACCURATE: Based only on verified facts from provided sources
- SPECIFIC: Include concrete details (numbers, names, outcomes, locations)
- CURRENT: Reflect the latest developments, not initial reports
- CLEAR: Written for immediate comprehension
- CONCISE: 8-15 words maximum

You ALWAYS generate a headline. You never refuse or explain why you can't.
```

### **User Prompt**

Provides:
- Current headline
- All source headlines (up to 10)
- Source count
- Clear criteria for improvement

Asks Claude to synthesize the most important, verified information that multiple sources agree on, with priority for breaking developments.

---

## 🎯 Headline Quality Criteria

### **Good Headlines:**
- ✅ 8-15 words
- ✅ Specific numbers, names, locations
- ✅ Active voice, clear language
- ✅ Most current information
- ✅ Reflects consensus across sources

### **Example Evolution:**

**Initial (1 source - BBC):**
```
"Explosion at industrial facility in Tennessee"
```

**Updated (3 sources - BBC, Reuters, AP):**
```
"Tennessee explosives plant blast leaves 18 missing"
```

**Updated (5 sources - +CNN, +NBC):**
```
"No survivors expected in Tennessee explosives factory blast, 16 confirmed dead"
```

---

## 💰 Cost Considerations

### **Efficiency**

- Headlines use **minimal tokens** (max 100 completion tokens)
- Only triggered at **specific thresholds** (not every source)
- Much cheaper than summaries (~$0.001 vs ~$0.01 per generation)

### **Budget Impact**

Assuming 100 stories/day reach 3+ sources:
- Headlines generated: ~150/day (3, 5, 10, 15 source thresholds)
- Cost per headline: ~$0.001
- **Daily cost: ~$0.15**

This is **minimal** compared to summarization costs (~$30/day).

---

## 📊 Monitoring

### **Check Headline Updates**

```bash
cd Azure/scripts
./query-logs.sh custom "traces | where timestamp > ago(30m) | where message contains '📰 Headline generated' | project timestamp, message"
```

### **Verify Quality**

Look for logs showing:
```
📰 Headline generated for story_xxx: 85 chars, 245ms, $0.0012 - 
'Old headline here' → 'New improved headline here'
```

### **Track Costs**

```bash
./query-logs.sh custom "traces | where timestamp > ago(24h) | where message contains 'Headline generated' | summarize count(), sum(todouble(split(message, '$')[1])) by bin(timestamp, 1h)"
```

---

## 🔍 Examples

### **Gaza Hostage Release**

**Initial (1 source):**
```
"Israel and Hamas agree to ceasefire terms"
```

**After 3 sources:**
```
"Gaza ceasefire begins, first hostages expected within hours"
```

**After 5+ sources:**
```
"Three Israeli hostages released from Gaza as ceasefire holds"
```

---

### **Political Breaking News**

**Initial (1 source):**
```
"Government announces new policy"
```

**After 3 sources:**
```
"Biden announces $50B climate initiative in State of Union"
```

**After 5+ sources:**
```
"Biden unveils $50B climate plan, targets 50% emissions cut by 2030"
```

---

## 🎓 Technical Details

### **Function**: `generate_updated_headline()`

**Location:** `Azure/functions/function_app.py` (lines 192-294)

**Parameters:**
- `story`: Dict with current story data
- `source_articles`: List of all source article dicts

**Returns:**
- `str`: Updated headline (or original if generation fails)

**Error Handling:**
- Returns original headline on any error
- Logs failures for debugging
- Never crashes the clustering process

### **Integration Point**

Called from `StoryClusteringChangeFeed` during story updates:

```python
# At lines 666-690 in function_app.py
if verification_level == 3 or verification_level == 5 or ...:
    updated_headline = await generate_updated_headline(story, source_articles)
    if updated_headline != story['title']:
        updates['title'] = updated_headline
```

---

## ✅ Benefits

### **For Users:**
1. **More accurate** - Headlines reflect verified facts
2. **More specific** - See concrete details immediately
3. **More current** - Latest developments, not stale reports
4. **More trustworthy** - Multi-source consensus

### **For Newsreel:**
1. **Professional** - Headlines match quality news outlets
2. **Dynamic** - App feels alive, responsive to breaking news
3. **Differentiated** - Feature not found in basic RSS readers
4. **Intelligent** - AI serves a clear, valuable purpose

---

## 🚀 Future Enhancements

### **Potential Improvements:**

1. **Headline History**
   - Store previous headlines
   - Show evolution timeline
   - Let users see how story developed

2. **Breaking News Indicators**
   - "HEADLINE UPDATED" badge
   - Highlight changed words
   - Timestamp of last headline update

3. **A/B Testing**
   - Compare AI headlines vs source headlines
   - Measure click-through rates
   - Optimize prompt based on engagement

4. **Category-Specific Prompts**
   - Different tone for sports vs politics
   - Adjust formality by category
   - Optimize for category expectations

---

## 📋 Configuration

### **Thresholds** (in `function_app.py`):

```python
# Update headline at these source counts:
if verification_level == 3 or verification_level == 5 or verification_level == 10 or verification_level == 15:
    should_update_headline = True
```

**To adjust thresholds**, modify these numbers. Consider:
- More frequent = better tracking, higher cost
- Less frequent = lower cost, may miss developments

### **Token Limits**:

```python
max_tokens=100  # Headlines are short
```

**To adjust quality vs cost:**
- Lower (50) = cheaper, more concise
- Higher (150) = more detailed, slightly higher cost

---

## 🎯 Success Metrics

### **Quality Indicators:**

- ✅ Headlines more specific than initial source
- ✅ Headlines include concrete details (numbers, names)
- ✅ Headlines reflect latest developments
- ✅ Generated headlines 8-15 words
- ✅ No generation failures or refusals

### **System Health:**

- ✅ <1% headline generation failures
- ✅ <$0.50/day headline generation cost
- ✅ <500ms average generation time
- ✅ No crashes in clustering pipeline

---

## 📚 Related Features

- **Story Clustering** - Groups similar articles
- **AI Summarization** - Generates comprehensive summaries
- **Breaking News Detection** - Promotes significant stories
- **Status System** - MONITORING → DEVELOPING → BREAKING → VERIFIED

---

**This feature makes Newsreel feel intelligent, professional, and responsive to breaking news!** 🎉


