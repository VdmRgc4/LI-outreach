"""
Module: company_intel.py
Purpose: Find and analyze company websites for discovery intelligence
Dependencies: requests, beautifulsoup4
External calls: Web scraping (with rate limiting)

Input Format:
    company_name: str

Output Format:
    {
        "company_url": str,
        "value_prop": str,
        "competitors": List[str],
        "trust_signals": List[str],
        "technical_gaps": List[str],
        "geo_readiness_score": int,
        "recent_news": List[str],
        "content_velocity": str,
        "ai_crawlers_blocked": List[str],
        "confidence": int
    }
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import time
import re
from urllib.parse import urlparse, urljoin
import sys
import os

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def find_company_website(company_name: str) -> Optional[str]:
    """
    Find company website using multiple strategies

    Args:
        company_name: Name of the company

    Returns:
        Company website URL or None if not found
    """
    if not company_name:
        return None

    headers = {"User-Agent": config.USER_AGENT}

    # Strategy 1: Try common domain patterns first (fastest)
    # Convert company name to potential domains
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', company_name.lower())
    clean_name = clean_name.replace(' ', '')

    potential_domains = [
        f"https://{clean_name}.com",
        f"https://www.{clean_name}.com",
        f"https://{clean_name}.io",
        f"https://www.{clean_name}.io",
    ]

    # Also try with dashes
    dashed_name = company_name.lower().replace(' ', '-')
    dashed_name = re.sub(r'[^a-z0-9\-]', '', dashed_name)
    if dashed_name != clean_name:
        potential_domains.extend([
            f"https://{dashed_name}.com",
            f"https://www.{dashed_name}.com",
        ])

    # Test each potential domain
    for domain in potential_domains:
        try:
            response = requests.get(
                domain,
                headers=headers,
                timeout=5,
                allow_redirects=True
            )
            if response.status_code < 400:
                # Check if it's not a parking page
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.find('title')
                if title and 'park' not in title.get_text().lower():
                    return domain
        except:
            continue

    # Strategy 2: Try search (if Strategy 1 fails)
    try:
        search_url = f"https://html.duckduckgo.com/html/?q={company_name}+official+website"
        response = requests.get(search_url, headers=headers, timeout=config.REQUEST_TIMEOUT)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('a', class_='result__a')

            for result in results[:5]:
                url = result.get('href', '')

                # Skip excluded domains
                if any(domain in url.lower() for domain in config.EXCLUDED_DOMAINS):
                    continue

                parsed = urlparse(url)
                if parsed.scheme and parsed.netloc:
                    try:
                        test_response = requests.head(
                            url,
                            headers=headers,
                            timeout=5,
                            allow_redirects=True
                        )
                        if test_response.status_code < 400:
                            return url
                    except:
                        continue

    except Exception as e:
        print(f"  ⚠️  Search fallback failed for {company_name}: {str(e)}")

    return None


def scrape_homepage(url: str) -> Dict:
    """
    Scrape and analyze company homepage

    Args:
        url: Company website URL

    Returns:
        Dictionary with homepage analysis
    """
    result = {
        "value_prop": "",
        "trust_signals": [],
        "meta_description": "",
        "h1_headings": [],
        "primary_cta": "",
        "has_blog": False,
        "page_title": ""
    }

    try:
        headers = {"User-Agent": config.USER_AGENT}
        response = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract page title
        title_tag = soup.find('title')
        if title_tag:
            result["page_title"] = title_tag.get_text(strip=True)

        # Extract meta description (often contains value prop)
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            result["meta_description"] = meta_desc.get('content', '')

        # Extract H1 headings (main value propositions)
        h1_tags = soup.find_all('h1')
        result["h1_headings"] = [h1.get_text(strip=True) for h1 in h1_tags[:3]]

        # Combine for value prop
        value_prop_parts = []
        if result["page_title"]:
            value_prop_parts.append(result["page_title"])
        if result["meta_description"]:
            value_prop_parts.append(result["meta_description"])
        if result["h1_headings"]:
            value_prop_parts.extend(result["h1_headings"])

        result["value_prop"] = " | ".join(value_prop_parts[:3])

        # Look for trust signals
        text_content = soup.get_text().lower()
        trust_keywords = [
            ('funding', 'series a', 'series b', 'series c', 'raised'),
            ('featured', 'techcrunch', 'forbes', 'inc 5000'),
            ('award', 'certified', 'certification', 'iso'),
            ('trusted by', 'clients include', 'customers include'),
            ('soc 2', 'gdpr', 'hipaa', 'compliant')
        ]

        for keyword_group in trust_keywords:
            if any(kw in text_content for kw in keyword_group):
                result["trust_signals"].append(keyword_group[0])

        # Check for blog/resources
        blog_indicators = ['blog', 'resources', 'insights', 'articles', 'news']
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '').lower()
            if any(indicator in href for indicator in blog_indicators):
                result["has_blog"] = True
                break

        # Extract primary CTA
        cta_buttons = soup.find_all(['a', 'button'], class_=re.compile(r'(cta|btn|button)', re.I))
        if cta_buttons:
            result["primary_cta"] = cta_buttons[0].get_text(strip=True)

        return result

    except Exception as e:
        print(f"  ⚠️  Error scraping homepage {url}: {str(e)}")
        return result


def check_robots_txt(url: str) -> List[str]:
    """
    Check robots.txt for AI crawler access

    Args:
        url: Company website URL

    Returns:
        List of blocked AI crawlers
    """
    blocked_crawlers = []

    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        headers = {"User-Agent": config.USER_AGENT}
        response = requests.get(robots_url, headers=headers, timeout=5)

        if response.status_code == 200:
            robots_content = response.text.lower()

            # Check each AI crawler
            for crawler in config.AI_CRAWLERS:
                # Look for "Disallow" rules for this crawler
                pattern = rf'user-agent:\s*{re.escape(crawler.lower())}[\s\S]*?disallow:\s*/\s*$'
                if re.search(pattern, robots_content, re.MULTILINE | re.IGNORECASE):
                    blocked_crawlers.append(crawler)

        return blocked_crawlers

    except:
        return []


def search_competitive_intel(company_name: str, company_url: str) -> Dict:
    """
    Search for competitive intelligence about the company

    Args:
        company_name: Name of the company
        company_url: Company website URL

    Returns:
        Dictionary with competitive insights
    """
    result = {
        "competitors": [],
        "recent_news": [],
        "market_position": ""
    }

    try:
        # Simple competitor search (looking for "vs" pages on their site)
        headers = {"User-Agent": config.USER_AGENT}

        # Check if they have a competitors or comparison page
        comparison_urls = [
            urljoin(company_url, "/competitors"),
            urljoin(company_url, "/comparison"),
            urljoin(company_url, "/vs"),
            urljoin(company_url, "/alternatives")
        ]

        for comp_url in comparison_urls:
            try:
                response = requests.get(comp_url, headers=headers, timeout=5)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Extract competitor mentions from headings
                    headings = soup.find_all(['h1', 'h2', 'h3'])
                    for heading in headings[:10]:
                        text = heading.get_text()
                        # Look for "vs [Competitor]" patterns
                        vs_match = re.search(r'vs\.?\s+([A-Z][a-zA-Z]+)', text)
                        if vs_match:
                            result["competitors"].append(vs_match.group(1))
                    break
            except:
                continue

        # Search for recent company news (simplified)
        # In production, you'd use a news API or more sophisticated search
        result["recent_news"] = ["News search requires API integration"]

        return result

    except Exception as e:
        print(f"  ⚠️  Error gathering competitive intel: {str(e)}")
        return result


def calculate_geo_readiness_score(
    homepage_data: Dict,
    blocked_crawlers: List[str],
    company_url: str
) -> int:
    """
    Calculate GEO (Generative Engine Optimization) readiness score

    Args:
        homepage_data: Homepage analysis data
        blocked_crawlers: List of blocked AI crawlers
        company_url: Company website URL

    Returns:
        Score from 0-10
    """
    score = 10

    # Penalty for blocked AI crawlers (-2 points each)
    score -= len(blocked_crawlers) * 2

    # Bonus for having structured content (+1 point)
    if homepage_data.get("meta_description"):
        score += 1

    # Penalty for no blog/content (-2 points)
    if not homepage_data.get("has_blog"):
        score -= 2

    # Ensure score is between 0 and 10
    return max(0, min(10, score))


def get_company_intel(company_name: str, company_url: Optional[str] = None) -> Dict:
    """
    Main function to gather complete company intelligence

    Args:
        company_name: Name of the company
        company_url: Optional pre-known company URL

    Returns:
        Complete company intelligence dictionary
    """
    print(f"  🔍 Analyzing {company_name}...")

    # Initialize result structure
    result = {
        "company_url": company_url or "",
        "value_prop": "",
        "competitors": [],
        "trust_signals": [],
        "technical_gaps": [],
        "geo_readiness_score": 0,
        "recent_news": [],
        "content_velocity": "unknown",
        "ai_crawlers_blocked": [],
        "confidence": 0
    }

    confidence_points = 0

    # Step 1: Find company website if not provided
    if not company_url:
        company_url = find_company_website(company_name)
        if company_url:
            result["company_url"] = company_url
            confidence_points += 30
            print(f"    ✅ Found website: {company_url}")
        else:
            print(f"    ❌ Could not find website")
            result["confidence"] = confidence_points
            return result
    else:
        confidence_points += 30

    # Rate limiting
    time.sleep(config.REQUEST_DELAY_SECONDS)

    # Step 2: Scrape homepage
    homepage_data = scrape_homepage(company_url)
    if homepage_data.get("value_prop"):
        result["value_prop"] = homepage_data["value_prop"]
        result["trust_signals"] = homepage_data["trust_signals"]
        confidence_points += 20
        print(f"    ✅ Analyzed homepage")

    # Rate limiting
    time.sleep(config.REQUEST_DELAY_SECONDS)

    # Step 3: Check robots.txt for AI crawlers
    blocked_crawlers = check_robots_txt(company_url)
    result["ai_crawlers_blocked"] = blocked_crawlers
    if blocked_crawlers:
        result["technical_gaps"].append(f"Blocking AI crawlers: {', '.join(blocked_crawlers)}")
        print(f"    ⚠️  Blocking {len(blocked_crawlers)} AI crawlers")
    confidence_points += 20

    # Step 4: Search for competitive intelligence
    time.sleep(config.REQUEST_DELAY_SECONDS)
    competitive_data = search_competitive_intel(company_name, company_url)
    if competitive_data.get("competitors"):
        result["competitors"] = competitive_data["competitors"]
        confidence_points += 20
        print(f"    ✅ Found {len(result['competitors'])} competitors")

    result["recent_news"] = competitive_data.get("recent_news", [])

    # Step 5: Calculate GEO readiness score
    result["geo_readiness_score"] = calculate_geo_readiness_score(
        homepage_data,
        blocked_crawlers,
        company_url
    )

    # Check for content velocity signals
    if homepage_data.get("has_blog"):
        result["content_velocity"] = "has blog/resources"
        confidence_points += 15
    else:
        result["content_velocity"] = "no blog detected"

    # Add technical gaps
    if not homepage_data.get("meta_description"):
        result["technical_gaps"].append("Missing meta description")

    if not homepage_data.get("h1_headings"):
        result["technical_gaps"].append("No H1 headings found")

    # Final confidence score
    result["confidence"] = confidence_points

    print(f"    📊 Confidence: {confidence_points}/100 | GEO Score: {result['geo_readiness_score']}/10")

    return result


if __name__ == "__main__":
    # Test company intelligence module
    print("Testing Company Intelligence Module...")
    print("=" * 70)

    test_companies = [
        ("Stripe", "https://stripe.com"),
        ("Acme Corp", None),  # Non-existent company
    ]

    for company_name, company_url in test_companies:
        print(f"\nTest: {company_name}")
        result = get_company_intel(company_name, company_url)
        print(f"\nResults:")
        print(f"  URL: {result['company_url']}")
        print(f"  Value Prop: {result['value_prop'][:100]}...")
        print(f"  Trust Signals: {result['trust_signals']}")
        print(f"  Competitors: {result['competitors']}")
        print(f"  Technical Gaps: {result['technical_gaps']}")
        print(f"  AI Crawlers Blocked: {result['ai_crawlers_blocked']}")
        print(f"  GEO Readiness: {result['geo_readiness_score']}/10")
        print(f"  Confidence: {result['confidence']}/100")
        print("-" * 70)

    print("\n✅ Company Intelligence module tests complete!")
