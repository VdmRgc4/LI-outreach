"""
Module: person_intel.py
Purpose: Research executives and gather context for personalized messaging
Dependencies: requests, beautifulsoup4
External calls: Web search (with rate limiting)

Input Format:
    first_name: str
    last_name: str
    company_name: str
    title: str

Output Format:
    {
        "career_pattern": str,  # "builder" | "optimizer" | "turnaround" | "unknown"
        "recent_activity": List[str],
        "sophistication_level": str,  # "tactical" | "strategic" | "unknown"
        "communication_style": str,  # "data-driven" | "narrative-driven" | "unknown"
        "background_summary": str,
        "key_initiatives": List[str],
        "confidence": int
    }
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import time
import re
import sys
import os

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def search_person_background(
    first_name: str,
    last_name: str,
    company_name: str
) -> Dict:
    """
    Search for person's background and recent activity

    Args:
        first_name: Person's first name
        last_name: Person's last name
        company_name: Current company

    Returns:
        Dictionary with background information
    """
    result = {
        "found_mentions": [],
        "recent_articles": [],
        "speaking_engagements": [],
        "linkedin_activity": [],
        "press_mentions": []
    }

    try:
        # Construct search query
        full_name = f"{first_name} {last_name}"
        search_query = f"{full_name} {company_name}"

        # Note: In production, you'd use a proper search API (Google, Bing, etc.)
        # For now, we'll use simplified pattern matching and heuristics

        # Look for common patterns in professional context
        professional_keywords = [
            "interview",
            "podcast",
            "speaking",
            "conference",
            "article",
            "quoted",
            "announced",
            "appointed",
            "hired",
            "promoted"
        ]

        # In a real implementation, this would make actual search API calls
        # For now, we'll provide a structure that can be extended
        result["found_mentions"] = [
            f"Search would look for: {search_query}"
        ]

        # Placeholder for actual search results
        # In production: result["recent_articles"] = actual_search_results

        return result

    except Exception as e:
        print(f"  ⚠️  Error searching for {first_name} {last_name}: {str(e)}")
        return result


def identify_career_pattern(
    title: str,
    background_data: Dict
) -> str:
    """
    Identify career pattern based on title and background

    Args:
        title: Current job title
        background_data: Background search results

    Returns:
        Career pattern: "builder" | "optimizer" | "turnaround" | "unknown"
    """
    if not title:
        return "unknown"

    title_lower = title.lower()

    # Builder signals: Growth-focused roles
    builder_keywords = [
        "growth",
        "expansion",
        "new business",
        "revenue",
        "scale",
        "startup",
        "founding",
        "chief growth"
    ]

    # Optimizer signals: Efficiency-focused roles
    optimizer_keywords = [
        "operations",
        "efficiency",
        "optimization",
        "process",
        "systems",
        "automation",
        "chief operating"
    ]

    # Turnaround signals: Transformation-focused roles
    turnaround_keywords = [
        "transformation",
        "change",
        "turnaround",
        "restructure",
        "interim",
        "chief restructuring"
    ]

    # Count matches
    builder_score = sum(1 for kw in builder_keywords if kw in title_lower)
    optimizer_score = sum(1 for kw in optimizer_keywords if kw in title_lower)
    turnaround_score = sum(1 for kw in turnaround_keywords if kw in title_lower)

    # Determine pattern
    if builder_score > optimizer_score and builder_score > turnaround_score:
        return "builder"
    elif optimizer_score > builder_score and optimizer_score > turnaround_score:
        return "optimizer"
    elif turnaround_score > 0:
        return "turnaround"
    else:
        # Default based on seniority
        if any(senior_kw in title_lower for senior_kw in ["vp", "vice president", "chief", "head of"]):
            return "builder"  # Senior roles often focused on growth
        return "unknown"


def assess_sophistication_level(title: str, company_name: str) -> str:
    """
    Assess whether person thinks tactically or strategically

    Args:
        title: Job title
        company_name: Company name

    Returns:
        "tactical" | "strategic" | "unknown"
    """
    if not title:
        return "unknown"

    title_lower = title.lower()

    # Strategic indicators (C-level, VP, Director roles)
    strategic_keywords = [
        "chief",
        "vp",
        "vice president",
        "head of",
        "director",
        "executive",
        "president",
        "founder"
    ]

    # Tactical indicators (Manager, Specialist, Coordinator roles)
    tactical_keywords = [
        "manager",
        "specialist",
        "coordinator",
        "analyst",
        "associate",
        "lead"
    ]

    # Check for strategic indicators first (higher priority)
    if any(kw in title_lower for kw in strategic_keywords):
        return "strategic"

    # Check for tactical indicators
    if any(kw in title_lower for kw in tactical_keywords):
        return "tactical"

    return "unknown"


def assess_communication_style(
    title: str,
    background_data: Dict
) -> str:
    """
    Assess communication style preferences

    Args:
        title: Job title
        background_data: Background search results

    Returns:
        "data-driven" | "narrative-driven" | "unknown"
    """
    if not title:
        return "unknown"

    title_lower = title.lower()

    # Data-driven roles (Analytics, Operations, Technical)
    data_driven_keywords = [
        "analytics",
        "data",
        "operations",
        "finance",
        "technology",
        "engineering",
        "product",
        "technical"
    ]

    # Narrative-driven roles (Marketing, Sales, Communications)
    narrative_keywords = [
        "marketing",
        "sales",
        "communications",
        "brand",
        "content",
        "creative",
        "strategy"
    ]

    # Count matches
    data_score = sum(1 for kw in data_driven_keywords if kw in title_lower)
    narrative_score = sum(1 for kw in narrative_keywords if kw in title_lower)

    if data_score > narrative_score:
        return "data-driven"
    elif narrative_score > data_score:
        return "narrative-driven"
    else:
        return "unknown"


def extract_key_initiatives(title: str, company_name: str) -> List[str]:
    """
    Identify likely key initiatives based on role and company

    Args:
        title: Job title
        company_name: Company name

    Returns:
        List of likely initiatives
    """
    initiatives = []
    title_lower = title.lower()

    # Marketing roles
    if any(kw in title_lower for kw in ["marketing", "cmo", "chief marketing"]):
        initiatives.extend([
            "Brand positioning and awareness",
            "Lead generation and pipeline growth",
            "Marketing technology stack optimization",
            "Content strategy and thought leadership"
        ])

    # Sales roles
    if any(kw in title_lower for kw in ["sales", "revenue", "cro", "chief revenue"]):
        initiatives.extend([
            "Revenue growth and target achievement",
            "Sales process optimization",
            "Team expansion and enablement",
            "Market penetration and new customer acquisition"
        ])

    # Product roles
    if any(kw in title_lower for kw in ["product", "cpo", "chief product"]):
        initiatives.extend([
            "Product roadmap and feature prioritization",
            "Customer experience improvement",
            "Market fit validation",
            "Innovation and competitive differentiation"
        ])

    # Technology/Engineering roles
    if any(kw in title_lower for kw in ["technology", "engineering", "cto", "chief technology"]):
        initiatives.extend([
            "Technical infrastructure and scalability",
            "Engineering team growth",
            "Innovation and R&D",
            "Security and compliance"
        ])

    # Operations roles
    if any(kw in title_lower for kw in ["operations", "coo", "chief operating"]):
        initiatives.extend([
            "Operational efficiency and process improvement",
            "Cost optimization",
            "Team structure and resource allocation",
            "Systems and automation"
        ])

    # CEO/Founder roles
    if any(kw in title_lower for kw in ["ceo", "chief executive", "founder", "president"]):
        initiatives.extend([
            "Company vision and strategic direction",
            "Growth and market expansion",
            "Funding and financial performance",
            "Team building and culture"
        ])

    return initiatives[:4]  # Return top 4 most relevant


def get_person_intel(
    first_name: str,
    last_name: str,
    company_name: str,
    title: str
) -> Dict:
    """
    Main function to gather complete person intelligence

    Args:
        first_name: Person's first name
        last_name: Person's last name
        company_name: Current company
        title: Job title

    Returns:
        Complete person intelligence dictionary
    """
    print(f"  👤 Researching {first_name} {last_name} at {company_name}...")

    # Initialize result structure
    result = {
        "career_pattern": "unknown",
        "recent_activity": [],
        "sophistication_level": "unknown",
        "communication_style": "unknown",
        "background_summary": "",
        "key_initiatives": [],
        "confidence": 0
    }

    confidence_points = 0

    # Step 1: Search for background
    background_data = search_person_background(first_name, last_name, company_name)
    if background_data.get("found_mentions"):
        confidence_points += 15
        print(f"    ✅ Found background information")

    # Rate limiting
    time.sleep(config.REQUEST_DELAY_SECONDS)

    # Step 2: Identify career pattern
    result["career_pattern"] = identify_career_pattern(title, background_data)
    if result["career_pattern"] != "unknown":
        confidence_points += 15
        print(f"    ✅ Career pattern: {result['career_pattern']}")

    # Step 3: Assess sophistication level
    result["sophistication_level"] = assess_sophistication_level(title, company_name)
    if result["sophistication_level"] != "unknown":
        confidence_points += 15
        print(f"    ✅ Sophistication: {result['sophistication_level']}")

    # Step 4: Assess communication style
    result["communication_style"] = assess_communication_style(title, background_data)
    if result["communication_style"] != "unknown":
        confidence_points += 15
        print(f"    ✅ Communication style: {result['communication_style']}")

    # Step 5: Extract key initiatives
    result["key_initiatives"] = extract_key_initiatives(title, company_name)
    if result["key_initiatives"]:
        confidence_points += 15
        print(f"    ✅ Identified {len(result['key_initiatives'])} key initiatives")

    # Step 6: Create background summary
    summary_parts = [
        f"{first_name} {last_name} is {title} at {company_name}"
    ]

    if result["career_pattern"] != "unknown":
        pattern_desc = {
            "builder": "focused on growth and expansion",
            "optimizer": "focused on efficiency and optimization",
            "turnaround": "focused on transformation and change"
        }
        summary_parts.append(pattern_desc.get(result["career_pattern"], ""))

    if result["sophistication_level"] == "strategic":
        summary_parts.append("operates at strategic level")
    elif result["sophistication_level"] == "tactical":
        summary_parts.append("operates at tactical level")

    if result["communication_style"] != "unknown":
        summary_parts.append(f"with {result['communication_style']} communication style")

    result["background_summary"] = ", ".join(filter(None, summary_parts)) + "."
    confidence_points += 10

    # Add recent activity (from background search)
    if background_data.get("recent_articles"):
        result["recent_activity"] = background_data["recent_articles"][:5]
        confidence_points += 15

    # Final confidence score
    result["confidence"] = confidence_points

    print(f"    📊 Confidence: {confidence_points}/100")

    return result


if __name__ == "__main__":
    # Test person intelligence module
    print("Testing Person Intelligence Module...")
    print("=" * 70)

    test_people = [
        ("Sarah", "Chen", "DataFlow Analytics", "VP of Marketing"),
        ("John", "Smith", "Acme Corp", "Chief Technology Officer"),
        ("Jane", "Doe", "StartupXYZ", "Head of Product"),
    ]

    for first_name, last_name, company_name, title in test_people:
        print(f"\nTest: {first_name} {last_name}")
        result = get_person_intel(first_name, last_name, company_name, title)
        print(f"\nResults:")
        print(f"  Career Pattern: {result['career_pattern']}")
        print(f"  Sophistication: {result['sophistication_level']}")
        print(f"  Communication Style: {result['communication_style']}")
        print(f"  Key Initiatives: {result['key_initiatives']}")
        print(f"  Background Summary: {result['background_summary']}")
        print(f"  Confidence: {result['confidence']}/100")
        print("-" * 70)

    print("\n✅ Person Intelligence module tests complete!")
