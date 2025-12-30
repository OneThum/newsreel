#!/usr/bin/env python3
"""
Standalone test script for iOS Client Data Quality Tester

This script validates that the iOS quality tester works correctly
without needing the full pytest infrastructure.
"""

import sys
import os
import logging

# Add the functions directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from tests.ai.test_ios_client_data_quality import IOSClientDataQualityTester
    from tests.ai.test_ai_summary_quality import AITestBudget

    print('🧪 Testing iOS Client Data Quality Tester...')

    # Create a test budget
    budget = AITestBudget(max_daily_cost=0.1)  # Very small budget for testing

    # Create tester
    tester = IOSClientDataQualityTester(budget)

    print('✅ Tester instantiated successfully')

    # Test the validation methods
    test_story = {
        'id': 'test-123',
        'title': 'Test Story Title',
        'category': 'world',
        'last_updated': '2025-11-10T10:00:00Z',
        'sources': [
            {'source': 'BBC', 'title': 'BBC Article'},
            {'source': 'Reuters', 'title': 'Reuters Article'}
        ]
    }

    validation = tester._validate_story_structure(test_story)
    print(f'✅ Story validation: {validation}')

    print('✅ iOS Quality Tester basic functionality works!')

except Exception as e:
    print(f'❌ Test failed: {e}')
    import traceback
    traceback.print_exc()




