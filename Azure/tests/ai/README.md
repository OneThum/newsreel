# AI-Powered Quality Testing Infrastructure

This directory contains AI-powered testing infrastructure that uses Claude (Anthropic) to evaluate the quality of the Newsreel app's content and user experience.

## Overview

Traditional testing can only check if code works correctly. AI-powered testing evaluates whether the **content and user experience** make sense to actual users. This catches issues like:

- Inaccurate summaries
- Poor article clustering
- Wrong categorization
- Feed quality issues
- UX problems

## Architecture

### Cost Control System

```python
class AITestBudget:
    """Controls AI testing costs with daily limits"""
    - $5/day default budget
    - Tracks spending per test
    - Prevents overspending
    - Daily budget reset
```

### AI Testers

#### 1. AISummaryQualityTester
**Purpose**: Validates news summaries are accurate and unbiased

**Tests**:
- Factual accuracy (0-100)
- Bias detection (0-100)
- Completeness (0-100)
- Hallucination detection
- Issue identification

**Usage**:
```python
tester = AISummaryQualityTester(budget)
result = await tester.test_summary_accuracy(story, summary_text)
assert result['factual_accuracy'] >= 80
```

#### 2. AIClusteringTester
**Purpose**: Verifies stories are correctly clustered

**Tests**:
- Article belongs to cluster validation
- Cluster coherence analysis
- Clustering error detection

**Usage**:
```python
result = await tester.test_story_belongs_to_cluster(article, cluster, other_clusters)
assert result['correct_cluster'] == True
```

#### 3. AICategorizationTester
**Purpose**: Ensures articles are in appropriate categories

**Tests**:
- Category appropriateness
- Distribution analysis
- Consistency monitoring

**Usage**:
```python
result = await tester.test_category_correctness(article)
# Warnings for subjective issues, no hard failures
```

#### 4. AIAPITester
**Purpose**: Evaluates API responses from user perspective

**Tests**:
- Feed diversity and quality
- Story detail UX
- Response consistency
- Regression monitoring

**Usage**:
```python
result = await tester.test_stories_feed_quality(stories)
assert result['overall_quality'] >= 65
```

#### 5. IOSClientDataQualityTester ⭐ **NEW**
**Purpose**: End-to-end validation that API returns iOS-ready data

**Tests**:
- **Data Structure**: All required fields present and valid
- **Source Diversity**: No unhealthy concentration from one source
- **Clustering Quality**: Stories have appropriate number of sources (2-8)
- **Content Completeness**: Summaries present, images accessible
- **Overall UX Quality**: Comprehensive quality score (0-100)

**Critical Assertions**:
- ≥95% stories structurally valid
- ≥5 diverse sources in feed
- ≤60% concentration from any single source
- ≥75 overall quality score

**Usage**:
```python
tester = IOSClientDataQualityTester(budget)
result = await tester.test_ios_client_data_quality()
assert result['overall_quality_score'] >= 75  # iOS-ready threshold
```

## Cost Management

### Budget Limits
- **Daily Budget**: $5.00 (configurable via `AI_TEST_BUDGET` env var)
- **Per Test Cost**: ~$0.01-0.05 depending on complexity
- **Monthly Estimate**: ~$150 for comprehensive testing

### Cost Optimization
- Intelligent test skipping when budget exceeded
- Response truncation for long content
- Sample size limits (max 20 items per test)
- Cached responses where possible

## Test Categories

### Unit Tests (`pytest -m ai -k "unit"`)
Fast, focused tests on individual components:
- Budget control validation
- Edge case handling
- Cost calculation accuracy

### Integration Tests (`pytest -m ai -k "integration"`)
Test component interactions:
- Sample data clustering validation
- Mock API response evaluation

### System Tests (`pytest -m ai -k "system"`)
Test production data:
- Real summary quality validation
- Production clustering analysis
- Live API feed evaluation

## Running Tests

### Prerequisites
```bash
export ANTHROPIC_API_KEY="your_key_here"
export AI_TEST_BUDGET="5.0"  # Optional, defaults to $5/day
```

### Run All AI Tests
```bash
pytest tests/ai/ -m ai -v
```

### Run Specific Test Types
```bash
# Budget control tests (no API calls)
pytest tests/ai/ -k "budget_control" -v

# Summary quality tests
pytest tests/ai/test_ai_summary_quality.py -v

# Production quality monitoring
pytest tests/ai/ -k "production" -v --tb=short
```

### CI/CD Integration
```yaml
# In GitHub Actions or similar
- name: AI Quality Tests
  run: |
    export ANTHROPIC_API_KEY=${{ secrets.ANTHROPIC_API_KEY }}
    pytest tests/ai/ -m "ai and not slow" --maxfail=3
```

## Quality Metrics

### Summary Quality
- **Accuracy**: ≥80% (stories must be factually correct)
- **Bias**: ≥70% (summaries should be neutral)
- **No Hallucinations**: 0 false information allowed

### Clustering Quality
- **Coherence**: ≥80% (clusters should be about same event)
- **Correctness**: AI validation of cluster assignments

### Feed Quality
- **Diversity**: ≥60% (variety of topics/sources)
- **Freshness**: ≥50% (recent, relevant content)
- **Overall**: ≥65% (user satisfaction score)

## Monitoring & Alerts

### Quality Degradation Detection
Tests compare against baselines and alert when quality drops:
- Summary accuracy < 75%
- Feed quality < baseline × 90%
- Clustering coherence < 70%

### Logging
All AI tests log results for trend analysis:
```
✅ AI Summary Test Passed - Accuracy: 92%, Bias: 85%, Cost: $0.023
📊 Production Quality OK - Avg Accuracy: 87%, Avg Bias: 82%
⚠️ Feed quality degraded: 72% vs 80% baseline
```

## Implementation Notes

### Error Handling
- **Budget Exceeded**: Tests skip gracefully with clear messaging
- **API Errors**: Fall back to mock/default data where possible
- **JSON Parsing**: Robust error handling for AI response parsing

### Performance
- **Async/Await**: All AI calls are properly async
- **Timeouts**: 60-second timeouts prevent hanging
- **Batching**: Multiple evaluations batched where possible

### Reliability
- **Retry Logic**: Automatic retries for transient failures
- **Fallbacks**: Tests continue with partial results
- **Validation**: Strict JSON schema validation for AI responses

## Future Enhancements

### Additional AI Testers
- **AISourceCredibilityTester**: Evaluate source trustworthiness
- **AIContentFreshnessTester**: Detect stale/outdated content
- **AIUserIntentTester**: Test if content matches user interests

### Advanced Features
- **Trend Analysis**: Historical quality tracking
- **A/B Testing**: Compare different algorithms
- **User Feedback Integration**: Correlate with real user ratings

### Cost Optimizations
- **Response Caching**: Cache AI evaluations for repeated content
- **Model Selection**: Use cheaper models for simple validations
- **Batch Processing**: Group similar evaluations

## Best Practices

### Cost Awareness
1. **Test Selectively**: Run AI tests on CI, not every commit
2. **Sample Wisely**: Test representative samples, not everything
3. **Monitor Budget**: Set up alerts for budget overruns
4. **Optimize Prompts**: Keep prompts concise for cost efficiency

### Quality Focus
1. **Set Baselines**: Establish quality baselines from good data
2. **Monitor Trends**: Watch for gradual quality degradation
3. **Act on Insights**: Use AI feedback to improve algorithms
4. **Balance Rigor**: Some subjectivity is OK (categorization ≠ science)

### Reliability
1. **Handle Failures**: AI tests should fail gracefully
2. **Provide Context**: Include reasoning in test failures
3. **Document Limits**: Be clear about what AI can/cannot detect
4. **Human Oversight**: AI flags issues, humans make final calls

This AI testing infrastructure provides unprecedented insight into content quality, catching issues that traditional testing completely misses. It's particularly valuable for news apps where accuracy, neutrality, and user experience are critical.
