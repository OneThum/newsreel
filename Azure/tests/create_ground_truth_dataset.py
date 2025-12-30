#!/usr/bin/env python3
"""
Create Ground Truth Dataset for Clustering Validation

This script generates a labeled dataset of article pairs for validating
the clustering overhaul. It creates various scenarios:
- Same story (positive pairs)
- Different stories (negative pairs)
- Edge cases and ambiguous cases
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import asyncio
import os
from pathlib import Path

# Sample articles covering various scenarios
SAMPLE_ARTICLES = [
    # Technology - Apple iPhone launches
    {
        "id": "apple_iphone_1",
        "title": "Apple Announces New iPhone 15 Pro Max",
        "description": "Apple Inc. unveiled its latest flagship smartphone with advanced camera features and A17 chip.",
        "source": "techcrunch",
        "category": "technology",
        "published_at": "2024-01-15T09:00:00Z"
    },
    {
        "id": "apple_iphone_2",
        "title": "Apple Launches iPhone 15 Series Globally",
        "description": "The new iPhone 15 lineup is now available in stores worldwide, featuring improved battery life.",
        "source": "cnet",
        "category": "technology",
        "published_at": "2024-01-15T10:30:00Z"
    },
    {
        "id": "apple_iphone_3",
        "title": "iPhone 15 Pro Max Review: Camera Innovation Shines",
        "description": "Our hands-on review of Apple's latest smartphone reveals impressive camera capabilities.",
        "source": "theverge",
        "category": "technology",
        "published_at": "2024-01-16T14:00:00Z"
    },
    {
        "id": "apple_watch_1",
        "title": "Apple Watch Series 9 Gets Major Update",
        "description": "Apple introduced new health features and improved performance in the latest Watch model.",
        "source": "macrumors",
        "category": "technology",
        "published_at": "2024-01-15T11:00:00Z"
    },

    # Politics - US Election
    {
        "id": "election_1",
        "title": "Biden Administration Announces New Climate Policy",
        "description": "President Biden unveiled ambitious new environmental regulations targeting carbon emissions.",
        "source": "nytimes",
        "category": "politics",
        "published_at": "2024-01-10T08:00:00Z"
    },
    {
        "id": "election_2",
        "title": "White House Climate Initiative Details Released",
        "description": "The Biden administration provided specifics on the new environmental policy framework.",
        "source": "washingtonpost",
        "category": "politics",
        "published_at": "2024-01-10T09:15:00Z"
    },
    {
        "id": "election_3",
        "title": "Congress Reacts to Biden's Climate Plan",
        "description": "Lawmakers from both parties commented on the president's new environmental initiative.",
        "source": "politico",
        "category": "politics",
        "published_at": "2024-01-10T12:00:00Z"
    },
    {
        "id": "election_4",
        "title": "Trump Campaign Criticizes Biden Climate Policy",
        "description": "Former President Trump called the new environmental regulations 'job-killing' in a campaign speech.",
        "source": "foxnews",
        "category": "politics",
        "published_at": "2024-01-10T15:00:00Z"
    },

    # Sports - NFL
    {
        "id": "nfl_1",
        "title": "Chiefs Win Super Bowl LVIII in Overtime Thriller",
        "description": "Patrick Mahomes led the Kansas City Chiefs to victory over the San Francisco 49ers in overtime.",
        "source": "espn",
        "category": "sports",
        "published_at": "2024-02-11T22:30:00Z"
    },
    {
        "id": "nfl_2",
        "title": "Mahomes MVP Performance Seals Chiefs Victory",
        "description": "Kansas City quarterback Patrick Mahomes was named Super Bowl MVP after his record-breaking performance.",
        "source": "nfl",
        "category": "sports",
        "published_at": "2024-02-12T01:00:00Z"
    },
    {
        "id": "nfl_3",
        "title": "Super Bowl Halftime Show Controversy",
        "description": "Usher's performance drew mixed reactions from viewers and social media users.",
        "source": "variety",
        "category": "sports",
        "published_at": "2024-02-12T02:00:00Z"
    },

    # Business - Tesla
    {
        "id": "tesla_1",
        "title": "Tesla Reports Record Q4 Earnings",
        "description": "Electric vehicle maker Tesla posted better-than-expected financial results for Q4 2024.",
        "source": "bloomberg",
        "category": "business",
        "published_at": "2024-01-20T16:00:00Z"
    },
    {
        "id": "tesla_2",
        "title": "Tesla Stock Surges on Earnings Beat",
        "description": "Tesla shares jumped 8% after the company reported stronger-than-expected revenue growth.",
        "source": "cnbc",
        "category": "business",
        "published_at": "2024-01-20T16:30:00Z"
    },
    {
        "id": "tesla_3",
        "title": "Musk Comments on Tesla's Future Plans",
        "description": "CEO Elon Musk discussed autonomous driving technology and new vehicle models during earnings call.",
        "source": "reuters",
        "category": "business",
        "published_at": "2024-01-20T17:00:00Z"
    },

    # World News - Middle East
    {
        "id": "middle_east_1",
        "title": "Ceasefire Agreement Reached in Gaza",
        "description": "Israel and Hamas agreed to a temporary ceasefire after weeks of negotiations.",
        "source": "bbc",
        "category": "world",
        "published_at": "2024-01-25T06:00:00Z"
    },
    {
        "id": "middle_east_2",
        "title": "Gaza Ceasefire Takes Effect",
        "description": "Fighting paused in Gaza as both sides begin implementing the ceasefire agreement.",
        "source": "aljazeera",
        "category": "world",
        "published_at": "2024-01-25T08:00:00Z"
    },
    {
        "id": "middle_east_3",
        "title": "US Welcomes Gaza Ceasefire Deal",
        "description": "Secretary of State Antony Blinken praised the ceasefire agreement as a step toward peace.",
        "source": "ap",
        "category": "world",
        "published_at": "2024-01-25T10:00:00Z"
    },

    # Edge Cases - Ambiguous
    {
        "id": "edge_paris_1",
        "title": "Paris Climate Agreement Anniversary",
        "description": "World leaders marked the 5th anniversary of the Paris climate accord.",
        "source": "guardian",
        "category": "environment",
        "published_at": "2024-01-12T12:00:00Z"
    },
    {
        "id": "edge_paris_2",
        "title": "Paris Hilton Releases New Music",
        "description": "Celebrity Paris Hilton announced her return to music with a new single.",
        "source": "billboard",
        "category": "entertainment",
        "published_at": "2024-01-12T14:00:00Z"
    },
    {
        "id": "edge_sydney_1",
        "title": "Sydney Dentist Charged with Murder",
        "description": "A Sydney dentist faces murder charges in connection with a patient's death.",
        "source": "abc_au",
        "category": "crime",
        "published_at": "2024-01-18T20:00:00Z"
    },
    {
        "id": "edge_sydney_2",
        "title": "Sydney Stabbing Leaves One Dead",
        "description": "Police are investigating a fatal stabbing incident in Sydney's CBD.",
        "source": "sydney_morning_herald",
        "category": "crime",
        "published_at": "2024-01-18T22:00:00Z"
    }
]


def create_positive_pairs() -> List[Tuple[str, str, int]]:
    """Create positive pairs (articles about the same story)"""
    positive_pairs = []

    # Group articles by story topic
    story_groups = {
        "apple_iphone": ["apple_iphone_1", "apple_iphone_2", "apple_iphone_3"],
        "biden_climate": ["election_1", "election_2", "election_3"],
        "super_bowl": ["nfl_1", "nfl_2"],
        "tesla_earnings": ["tesla_1", "tesla_2", "tesla_3"],
        "gaza_ceasefire": ["middle_east_1", "middle_east_2", "middle_east_3"]
    }

    for story, article_ids in story_groups.items():
        # Create all pairs within each story group
        for i, id1 in enumerate(article_ids):
            for id2 in article_ids[i+1:]:
                positive_pairs.append((id1, id2, 1))  # Label 1 = same story

    return positive_pairs


def create_negative_pairs() -> List[Tuple[str, str, int]]:
    """Create negative pairs (articles about different stories)"""
    negative_pairs = []

    # Different categories should never cluster together
    categories = {}
    for article in SAMPLE_ARTICLES:
        cat = article["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(article["id"])

    # Create pairs between different categories
    category_list = list(categories.keys())
    for i, cat1 in enumerate(category_list):
        for cat2 in category_list[i+1:]:
            cat1_articles = categories[cat1][:3]  # Limit to avoid too many pairs
            cat2_articles = categories[cat2][:3]

            for id1 in cat1_articles:
                for id2 in cat2_articles:
                    negative_pairs.append((id1, id2, 0))  # Label 0 = different stories

    return negative_pairs


def create_hard_negative_pairs() -> List[Tuple[str, str, int]]:
    """Create hard negative pairs (tricky cases that might be misclassified)"""
    hard_negatives = []

    # Ambiguous entity cases
    hard_negatives.extend([
        ("edge_paris_1", "edge_paris_2", 0),  # Paris city vs Paris Hilton
        ("edge_sydney_1", "edge_sydney_2", 0),  # Sydney dentist vs Sydney stabbing
    ])

    # Similar but different topics in same category
    hard_negatives.extend([
        ("apple_iphone_1", "apple_watch_1", 0),  # iPhone vs Apple Watch
        ("election_3", "election_4", 0),  # Biden climate vs Trump criticism
        ("nfl_2", "nfl_3", 0),  # Super Bowl win vs halftime show
    ])

    # Time-separated similar events
    # (These would be negative if they were from different time periods)

    return hard_negatives


def create_near_duplicate_pairs() -> List[Tuple[str, str, int]]:
    """Create near-duplicate pairs (syndicated/repeated content)"""
    near_duplicates = []

    # Simulate syndicated content (same story, different sources)
    near_duplicates.extend([
        ("apple_iphone_1", "apple_iphone_2", 1),  # Already in positive pairs
        ("election_1", "election_2", 1),  # Already in positive pairs
    ])

    # Add some artificially created near-duplicates
    near_duplicates.extend([
        # These are already in positive pairs, but we can mark them as near-duplicates too
    ])

    return near_duplicates


def generate_balanced_dataset(num_pairs: int = 1000) -> List[Tuple[Dict[str, Any], Dict[str, Any], int]]:
    """
    Generate a balanced dataset of article pairs with labels.

    Args:
        num_pairs: Total number of pairs to generate

    Returns:
        List of (article1, article2, label) tuples
    """
    # Get all possible pairs
    positive_pairs = create_positive_pairs()
    negative_pairs = create_negative_pairs()
    hard_negative_pairs = create_hard_negative_pairs()

    print(f"Generated {len(positive_pairs)} positive pairs")
    print(f"Generated {len(negative_pairs)} negative pairs")
    print(f"Generated {len(hard_negative_pairs)} hard negative pairs")

    # Balance the dataset
    target_positive = num_pairs // 3
    target_easy_negative = num_pairs // 3
    target_hard_negative = num_pairs - target_positive - target_easy_negative

    # Sample from each category
    selected_positive = random.sample(positive_pairs, min(target_positive, len(positive_pairs)))
    selected_easy_negative = random.sample(negative_pairs, min(target_easy_negative, len(negative_pairs)))
    selected_hard_negative = hard_negative_pairs[:target_hard_negative]  # Take all hard negatives

    # Combine and shuffle
    all_pairs = selected_positive + selected_easy_negative + selected_hard_negative
    random.shuffle(all_pairs)

    # Convert to full article pairs
    article_pairs = []
    article_dict = {art["id"]: art for art in SAMPLE_ARTICLES}

    for id1, id2, label in all_pairs:
        if id1 in article_dict and id2 in article_dict:
            article_pairs.append((article_dict[id1], article_dict[id2], label))

    print(f"Final dataset: {len(article_pairs)} pairs")
    print(f"Positive pairs: {sum(1 for _, _, label in article_pairs if label == 1)}")
    print(f"Negative pairs: {sum(1 for _, _, label in article_pairs if label == 0)}")

    return article_pairs


async def save_ground_truth_dataset(filepath: str = "Azure/tests/ground_truth_dataset.json"):
    """Generate and save the ground truth dataset"""
    print("Generating ground truth dataset...")

    # Generate the dataset
    dataset = generate_balanced_dataset(num_pairs=500)  # Start with 500 pairs

    # Convert to serializable format
    serializable_dataset = []
    for article1, article2, label in dataset:
        pair_data = {
            "article1": article1,
            "article2": article2,
            "label": label,
            "pair_type": "positive" if label == 1 else "negative"
        }
        serializable_dataset.append(pair_data)

    # Save to file
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump({
            "dataset": serializable_dataset,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "num_pairs": len(serializable_dataset),
                "positive_pairs": sum(1 for p in serializable_dataset if p["label"] == 1),
                "negative_pairs": sum(1 for p in serializable_dataset if p["label"] == 0),
                "description": "Ground truth dataset for clustering validation"
            }
        }, f, ensure_ascii=False, indent=2)

    print(f"Saved ground truth dataset to {filepath}")
    print(f"Dataset contains {len(serializable_dataset)} labeled pairs")


async def create_validation_scenarios():
    """Create specific validation scenarios for testing"""
    scenarios = {
        "entity_disambiguation": [
            {
                "articles": ["edge_paris_1", "edge_paris_2"],
                "expected_cluster": False,  # Should NOT cluster together
                "reason": "Paris city vs Paris Hilton - different entities"
            },
            {
                "articles": ["edge_sydney_1", "edge_sydney_2"],
                "expected_cluster": False,  # Should NOT cluster together
                "reason": "Sydney dentist vs Sydney stabbing - different events"
            }
        ],
        "temporal_clustering": [
            {
                "articles": ["apple_iphone_1", "apple_iphone_2", "apple_iphone_3"],
                "expected_cluster": True,  # Should cluster together
                "reason": "Same story about iPhone launch over time"
            }
        ],
        "source_diversity": [
            {
                "articles": ["election_1", "election_2", "election_3"],
                "expected_cluster": True,  # Should cluster together
                "reason": "Same story from different reputable sources"
            }
        ]
    }

    # Save scenarios
    with open("Azure/tests/validation_scenarios.json", 'w', encoding='utf-8') as f:
        json.dump(scenarios, f, ensure_ascii=False, indent=2)

    print("Saved validation scenarios")


if __name__ == "__main__":
    # Generate ground truth dataset
    asyncio.run(save_ground_truth_dataset())

    # Create validation scenarios
    asyncio.run(create_validation_scenarios())

    print("Ground truth dataset generation complete!")
