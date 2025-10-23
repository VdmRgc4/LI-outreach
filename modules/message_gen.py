"""
Module: message_gen.py
Purpose: Generate personalized outreach messages using Claude API
Dependencies: anthropic
External calls: Anthropic Claude API

Input Format:
    company_data: Dict (from company_intel.py)
    person_data: Dict (from person_intel.py)
    prospect_info: Dict (first_name, last_name, title, company_name, linkedin_url)

Output Format:
    {
        "subject_line": str,
        "message_body": str,
        "hook_type": str,
        "key_insights": List[str],
        "confidence_score": int
    }
"""

import anthropic
from typing import Dict, List, Optional
import json
import sys
import os
import re

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def select_hook_type(company_data: Dict, person_data: Dict) -> str:
    """
    Select optimal hook type based on audit findings

    Hook Types:
    1. Competitive Intelligence - Strong competitor movement detected
    2. Market Shift Observation - Industry-wide change detected
    3. Strategic Question - About recent company announcement
    4. Technical Gap Revelation - Significant SEO/GEO technical issue
    5. Peer Intelligence - Similar company made relevant move

    Args:
        company_data: Company intelligence data
        person_data: Person intelligence data

    Returns:
        Hook type string
    """
    # Priority 1: Technical Gap (if AI crawlers blocked or major gaps)
    if company_data.get("ai_crawlers_blocked") and len(company_data.get("ai_crawlers_blocked", [])) > 0:
        return "Technical Gap Revelation"

    # Priority 2: Competitive Intelligence (if competitors identified)
    if company_data.get("competitors") and len(company_data.get("competitors", [])) > 0:
        return "Competitive Intelligence"

    # Priority 3: Strategic Question (if person is strategic level)
    if person_data.get("sophistication_level") == "strategic":
        return "Strategic Question"

    # Priority 4: Market Shift (default for strategic thinkers)
    if person_data.get("career_pattern") == "builder":
        return "Market Shift Observation"

    # Default: Peer Intelligence
    return "Peer Intelligence"


def build_message_prompt(
    company_data: Dict,
    person_data: Dict,
    prospect_info: Dict,
    hook_type: str
) -> str:
    """
    Build detailed prompt for Claude API

    Args:
        company_data: Company intelligence
        person_data: Person intelligence
        prospect_info: Prospect basic info
        hook_type: Selected hook type

    Returns:
        Formatted prompt string
    """
    first_name = prospect_info.get("first_name", "")
    last_name = prospect_info.get("last_name", "")
    title = prospect_info.get("title", "")
    company_name = prospect_info.get("company_name", "")

    prompt = f"""You are an expert B2B outreach strategist using the Breakspear advisory methodology. Generate a highly personalized LinkedIn InMail message.

PROSPECT CONTEXT:
- Name: {first_name} {last_name}
- Title: {title}
- Company: {company_name}

COMPANY INTELLIGENCE:
- Website: {company_data.get('company_url', 'not found')}
- Value Prop: {company_data.get('value_prop', 'not available')}
- Trust Signals: {', '.join(company_data.get('trust_signals', [])) or 'none detected'}
- Competitors: {', '.join(company_data.get('competitors', [])) or 'not identified'}
- Technical Gaps: {', '.join(company_data.get('technical_gaps', [])) or 'none identified'}
- AI Crawlers Blocked: {', '.join(company_data.get('ai_crawlers_blocked', [])) or 'none'}
- GEO Readiness Score: {company_data.get('geo_readiness_score', 0)}/10
- Content Velocity: {company_data.get('content_velocity', 'unknown')}

PERSON INTELLIGENCE:
- Career Pattern: {person_data.get('career_pattern', 'unknown')}
- Sophistication Level: {person_data.get('sophistication_level', 'unknown')}
- Communication Style: {person_data.get('communication_style', 'unknown')}
- Background: {person_data.get('background_summary', '')}
- Key Initiatives: {', '.join(person_data.get('key_initiatives', [])[:3])}

SELECTED HOOK TYPE: {hook_type}

REQUIREMENTS:
1. Create subject line (6-10 words) that creates curiosity
2. Write message body (150-200 words total)
3. Use impossibly specific observations that demonstrate deep market understanding
4. Create genuine curiosity gap without over-explaining
5. Position as peer advisor, not vendor
6. Include 3 key insights that would be valuable to this prospect
7. End with soft invitation (not aggressive CTA)

MESSAGE STRUCTURE:
- Opening Hook (1-2 sentences): Impossibly specific observation related to {hook_type}
- Strategic Insight (2-3 sentences): Share intelligence they likely don't have
- Curiosity Gap (2-3 sentences): Hint at deeper understanding without revealing full methodology
- Soft Invitation (1 sentence): Frame as them learning something valuable

TONE GUIDELINES:
- Confident but not arrogant
- Specific, never generic
- Intelligence-driven, not pitch-driven
- Peer-to-peer positioning
- Curiosity-creating, not solution-pushing

CRITICAL RULES:
- Use {first_name} (first name only) once in the message
- Reference specific company details (not generic observations)
- Quantify insights when possible (percentages, timeframes, specific numbers)
- Do NOT use phrases like "I noticed" - use more sophisticated framing
- Do NOT be salesy or use marketing jargon
- Do NOT explain who you are or what your company does

OUTPUT FORMAT - Return ONLY valid JSON:
{{
  "subject_line": "6-10 word subject line",
  "message_body": "150-200 word message following structure above",
  "hook_type": "{hook_type}",
  "key_insights": ["insight 1", "insight 2", "insight 3"],
  "reasoning": "brief explanation of why this approach"
}}

Generate the message now:"""

    return prompt


def generate_message_with_claude(prompt: str) -> Optional[Dict]:
    """
    Generate message using Claude API

    Args:
        prompt: Formatted prompt string

    Returns:
        Dictionary with generated message data or None if error
    """
    try:
        # Check for API key
        api_key = config.ANTHROPIC_API_KEY
        if not api_key:
            print("  ❌ ANTHROPIC_API_KEY not found in environment")
            return None

        # Initialize Claude client
        client = anthropic.Anthropic(api_key=api_key)

        # Call Claude API
        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=2000,
            temperature=0.7,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract response
        response_text = message.content[0].text

        # Parse JSON response
        # Try to extract JSON if wrapped in markdown code blocks
        json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        else:
            # Try to find JSON object in response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)

        result = json.loads(response_text)
        return result

    except json.JSONDecodeError as e:
        print(f"  ❌ Error parsing Claude response as JSON: {str(e)}")
        print(f"  Response: {response_text[:200]}...")
        return None
    except Exception as e:
        print(f"  ❌ Error calling Claude API: {str(e)}")
        return None


def validate_message_quality(message_data: Dict, prospect_info: Dict) -> bool:
    """
    Validate generated message meets quality standards

    Args:
        message_data: Generated message data
        prospect_info: Prospect info for validation

    Returns:
        True if message passes validation, False otherwise
    """
    if not message_data:
        return False

    # Check required fields
    required_fields = ["subject_line", "message_body", "hook_type", "key_insights"]
    for field in required_fields:
        if field not in message_data:
            print(f"  ⚠️  Missing required field: {field}")
            return False

    # Validate subject line length
    subject_words = len(message_data["subject_line"].split())
    if subject_words < config.MIN_SUBJECT_WORDS or subject_words > config.MAX_SUBJECT_WORDS:
        print(f"  ⚠️  Subject line length invalid: {subject_words} words (expected {config.MIN_SUBJECT_WORDS}-{config.MAX_SUBJECT_WORDS})")
        return False

    # Validate message body length
    message_words = len(message_data["message_body"].split())
    if message_words < config.MIN_MESSAGE_WORDS or message_words > config.MAX_MESSAGE_WORDS:
        print(f"  ⚠️  Message length invalid: {message_words} words (expected {config.MIN_MESSAGE_WORDS}-{config.MAX_MESSAGE_WORDS})")
        return False

    # Check for first name usage
    first_name = prospect_info.get("first_name", "")
    if first_name and first_name not in message_data["message_body"]:
        print(f"  ⚠️  Message doesn't use prospect's first name")
        return False

    # Check key insights
    if len(message_data.get("key_insights", [])) < 3:
        print(f"  ⚠️  Insufficient key insights: {len(message_data.get('key_insights', []))}")
        return False

    return True


def calculate_message_confidence(
    company_confidence: int,
    person_confidence: int,
    message_valid: bool
) -> int:
    """
    Calculate overall confidence score for message

    Args:
        company_confidence: Confidence from company intel (0-100)
        person_confidence: Confidence from person intel (0-100)
        message_valid: Whether message passed validation

    Returns:
        Overall confidence score (0-100)
    """
    # Weighted average: company 40%, person 30%, message validation 30%
    base_score = (company_confidence * 0.4) + (person_confidence * 0.3)

    if message_valid:
        base_score += 30
    else:
        base_score -= 20  # Penalty for invalid message

    return max(0, min(100, int(base_score)))


def generate_message(
    company_data: Dict,
    person_data: Dict,
    prospect_info: Dict
) -> Dict:
    """
    Main function to generate personalized message

    Args:
        company_data: Company intelligence from company_intel.py
        person_data: Person intelligence from person_intel.py
        prospect_info: Basic prospect info (first_name, last_name, title, company_name)

    Returns:
        Complete message generation result
    """
    first_name = prospect_info.get("first_name", "Unknown")
    last_name = prospect_info.get("last_name", "")
    company_name = prospect_info.get("company_name", "Unknown")

    print(f"  ✍️  Generating message for {first_name} {last_name} at {company_name}...")

    # Initialize result structure
    result = {
        "subject_line": "",
        "message_body": "",
        "hook_type": "",
        "key_insights": [],
        "confidence_score": 0
    }

    # Step 1: Select hook type
    hook_type = select_hook_type(company_data, person_data)
    result["hook_type"] = hook_type
    print(f"    ✅ Selected hook: {hook_type}")

    # Step 2: Build prompt
    prompt = build_message_prompt(company_data, person_data, prospect_info, hook_type)

    # Step 3: Generate message with Claude
    message_data = generate_message_with_claude(prompt)
    if not message_data:
        print(f"    ❌ Failed to generate message")
        return result

    print(f"    ✅ Message generated")

    # Step 4: Validate message quality
    is_valid = validate_message_quality(message_data, prospect_info)

    if is_valid:
        print(f"    ✅ Message passed validation")
        # Update result with generated content
        result["subject_line"] = message_data.get("subject_line", "")
        result["message_body"] = message_data.get("message_body", "")
        result["key_insights"] = message_data.get("key_insights", [])
    else:
        print(f"    ⚠️  Message failed validation (using anyway with lower confidence)")
        # Still use the message but mark with lower confidence
        result["subject_line"] = message_data.get("subject_line", "")
        result["message_body"] = message_data.get("message_body", "")
        result["key_insights"] = message_data.get("key_insights", [])

    # Step 5: Calculate confidence score
    company_confidence = company_data.get("confidence", 0)
    person_confidence = person_data.get("confidence", 0)
    result["confidence_score"] = calculate_message_confidence(
        company_confidence,
        person_confidence,
        is_valid
    )

    print(f"    📊 Confidence: {result['confidence_score']}/100")

    return result


if __name__ == "__main__":
    # Test message generation module
    print("Testing Message Generation Module...")
    print("=" * 70)

    # Mock data for testing
    mock_company_data = {
        "company_url": "https://dataflowanalytics.com",
        "value_prop": "Real-time data analytics platform for enterprise",
        "trust_signals": ["funding", "featured"],
        "competitors": ["Tableau", "PowerBI"],
        "technical_gaps": ["Blocking ClaudeBot, GPTBot"],
        "ai_crawlers_blocked": ["ClaudeBot", "GPTBot"],
        "geo_readiness_score": 4,
        "content_velocity": "has blog",
        "confidence": 80
    }

    mock_person_data = {
        "career_pattern": "builder",
        "sophistication_level": "strategic",
        "communication_style": "narrative-driven",
        "background_summary": "Sarah Chen is VP of Marketing at DataFlow Analytics, focused on growth and expansion",
        "key_initiatives": ["Brand positioning", "Lead generation", "Marketing technology stack"],
        "confidence": 85
    }

    mock_prospect_info = {
        "first_name": "Sarah",
        "last_name": "Chen",
        "title": "VP of Marketing",
        "company_name": "DataFlow Analytics",
        "linkedin_url": "https://linkedin.com/in/sarah-chen"
    }

    print("\nTest: Message Generation")
    result = generate_message(mock_company_data, mock_person_data, mock_prospect_info)

    print(f"\n{'='*70}")
    print("RESULTS:")
    print(f"{'='*70}")
    print(f"\nHook Type: {result['hook_type']}")
    print(f"\nSubject Line: {result['subject_line']}")
    print(f"\nMessage Body:\n{result['message_body']}")
    print(f"\nKey Insights:")
    for idx, insight in enumerate(result['key_insights'], 1):
        print(f"  {idx}. {insight}")
    print(f"\nConfidence Score: {result['confidence_score']}/100")
    print(f"\n{'='*70}")

    if result['subject_line'] and result['message_body']:
        print("\n✅ Message Generation module tests complete!")
    else:
        print("\n⚠️  Message generation incomplete (check API key)")
