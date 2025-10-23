# LinkedIn Outreach Automation - Project State

## Last Updated
2025-10-23 - Phase 2 Complete

## What's Working
- ✅ .claudeignore file (prevents 60% context waste)
- ✅ Project structure (modules/, output/)
- ✅ CSV input/output handling (modules/csv_handler.py)
- ✅ Configuration management (config.py)
- ✅ Main entry point (main.py - orchestration only)
- ✅ Sample CSV generation
- ✅ Company intelligence module (modules/company_intel.py)
- ❌ Person intelligence module (not implemented yet)
- ❌ Message generation (not implemented yet)
- ❌ Full integration (not implemented yet)

## Current Phase
**Phase 1: COMPLETE** - Project Setup & CSV Handler
**Phase 2: COMPLETE** - Company Intelligence Module
**Next: Phase 3** - Person Intelligence Module

## Critical Decisions Made

### Architecture
- **Modular design**: Each module is self-contained and <300 lines
- **Clear interfaces**: Every module has interface documentation at the top
- **Type hints throughout**: Helps Claude understand without reading implementations
- **No monolithic files**: Everything is broken into focused components

### CSV Handling
- **Input format**: linkedin_url, first_name, last_name, title, company_name (required)
- **Optional columns**: notes, company_url, industry, company_size
- **Output format**: All input columns + 10 generated columns (subject_line, message_body, hook_type, etc.)
- **Duplicate handling**: Removes duplicate LinkedIn URLs automatically
- **Validation**: Checks for required columns and validates LinkedIn URL formats

### Configuration
- **Rate limiting**: 2-second delay between requests (ethical scraping)
- **Confidence threshold**: 60 minimum to generate message
- **Message length**: 150-200 words
- **Subject line length**: 6-10 words
- **Claude API model**: claude-sonnet-4-20250514

### Technical Decisions
- **Web scraping**: BeautifulSoup (not Selenium - too heavy)
- **Error handling**: Graceful degradation, continue batch processing even if individual prospects fail
- **Confidence scoring**: 0-100 based on data completeness
  - Company website found: 30 points
  - Competitive intel: 20 points
  - Technical audit: 20 points
  - Executive context: 15 points
  - Strategic signals: 15 points

## Module Interfaces

### csv_handler.py (COMPLETE)
```python
# Input: CSV file path
# Output: pandas DataFrame

# Methods:
- read_input_csv(file_path: str) -> DataFrame
- write_output_csv(data: List[Dict], file_path: str) -> None
- append_to_output_csv(row_data: Dict, file_path: str) -> None
- validate_linkedin_url(url: str) -> bool
- get_prospect_summary(df: DataFrame) -> Dict
- create_sample_input_csv(file_path: str) -> None
```

### company_intel.py (COMPLETE - Phase 2)
```python
# Input: company_name (string), optional company_url (string)
# Output: dictionary

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

# Functions:
- find_company_website(company_name: str) -> Optional[str]
  - Strategy 1: Try common domain patterns (.com, .io, with/without www)
  - Strategy 2: Fallback to search if patterns fail
  - Returns working URL or None

- scrape_homepage(url: str) -> Dict
  - Extracts value prop, trust signals, H1 headings, meta description
  - Checks for blog/resources presence
  - Handles anti-bot protection gracefully (returns empty data)

- check_robots_txt(url: str) -> List[str]
  - Checks for AI crawler blocking (GPTBot, ClaudeBot, CCBot, etc.)
  - Returns list of blocked crawlers

- calculate_geo_readiness_score(homepage_data, blocked_crawlers, url) -> int
  - Scores 0-10 based on AI crawler access, content structure, blog presence

- get_company_intel(company_name: str, company_url: Optional[str]) -> Dict
  - Main orchestration function
  - Calls all sub-functions with rate limiting
  - Returns complete intelligence package
```

### person_intel.py (NOT YET IMPLEMENTED - Phase 3)
```python
# Input: first_name, last_name, company_name, title (strings)
# Output: dictionary

{
    "career_pattern": str,  # "builder" | "optimizer" | "turnaround"
    "recent_activity": List[str],
    "sophistication_level": str,  # "tactical" | "strategic"
    "communication_style": str,  # "data-driven" | "narrative-driven"
    "confidence": int
}
```

### message_gen.py (NOT YET IMPLEMENTED - Phase 4)
```python
# Input: company_data (dict), person_data (dict), prospect_info (dict)
# Output: dictionary

{
    "subject_line": str,
    "message_body": str,
    "hook_type": str,
    "key_insights": List[str],
    "confidence_score": int
}
```

## Do Not Modify
- ✅ csv_handler.py (tested and working)
- ✅ company_intel.py (Phase 2 complete - working)
- ✅ config.py (settings locked for now)
- ✅ .claudeignore (critical for context management)
- ✅ main.py (just orchestration, will update in Phase 5)

## Next Steps (Phase 3)

1. Create modules/person_intel.py with these functions:
   - `search_person_background(first_name, last_name, company_name) -> Dict`
   - `identify_career_pattern(background_data) -> str`
   - `get_person_intel(first_name, last_name, company_name, title) -> Dict` (main function)

2. Implementation requirements:
   - Use web search to find person information
   - Look for recent activity, articles, interviews
   - Identify career pattern (builder/optimizer/turnaround)
   - Assess communication style (data-driven/narrative-driven)
   - Return structured data matching interface in CURRENT_STATE.md

3. Test with sample names

4. Commit Phase 3 when complete

## Known Issues
- Some websites (like Stripe) have anti-bot protection that blocks scraping - module handles this gracefully
- External search may be rate-limited - fallback to domain pattern matching works well
- In production, consider using a proxy service or API for more reliable scraping

## Dependencies Installed
```
pandas==2.2.0
anthropic==0.25.0
beautifulsoup4==4.12.3
requests==2.31.0
python-dotenv==1.0.0
lxml==5.1.0
urllib3==2.2.0
```

## Session Health Indicators

### Current Session: HEALTHY ✅
- Tasks completing without re-reading files
- Responses consistent
- No context compaction warnings
- Modular structure maintained

### Signs to Restart (watch for these):
- Claude wants to refactor working code
- Suggests reading "all files"
- Opens unrelated modules
- Takes 30+ seconds per response
- "compacting conversation" appears 2+ times

## Development Guidelines for Next Session

When starting Phase 2:
```
"Read CURRENT_STATE.md first.

Implement modules/company_intel.py ONLY.

DO NOT read or modify:
- csv_handler.py
- main.py
- config.py

ONLY focus on company intelligence gathering.
Use the interface defined above.
Keep under 300 lines."
```

## File Structure
```
linkedin-outreach-automation/
├── .claudeignore          ✅ Complete
├── README.md              ✅ Complete
├── CURRENT_STATE.md       ✅ Complete (this file)
├── requirements.txt       ✅ Complete
├── config.py              ✅ Complete
├── main.py                ✅ Complete (Phase 1 version)
├── modules/
│   ├── csv_handler.py     ✅ Complete & Tested (Phase 1)
│   ├── company_intel.py   ✅ Complete & Tested (Phase 2)
│   ├── person_intel.py    ⏳ Next (Phase 3)
│   └── message_gen.py     🔜 Future (Phase 4)
└── output/                ✅ Directory created
```

## Quality Metrics Target

For Phase 1 (Achieved ✅):
- ✅ .claudeignore present
- ✅ Each module <300 lines
- ✅ Clear module interfaces
- ✅ Type hints throughout
- ✅ Main.py <100 lines
- ✅ Tests work

For Phase 2-5 (Goals):
- Process 50+ prospects per hour
- Achieve 80%+ confidence scores on average
- Generate 100% unique messages
- Find company websites for 90%+ of prospects
- Complete technical audits for 75%+ of companies

## Git Workflow

Current branch: `claude/linkedin-outreach-automation-011CUQQwBAuikVZP8QwRGoNV`

After each phase:
```bash
git add .
git commit -m "Phase X: [description]"
git push -u origin claude/linkedin-outreach-automation-011CUQQwBAuikVZP8QwRGoNV
```

## Notes
- Phase 1 completed successfully (Project setup, CSV I/O)
- Phase 2 completed successfully (Company intelligence module)
- Context management strategy working well - no compaction issues
- Modular architecture proving effective for focused development
- Error handling working as designed (graceful degradation)
- Ready to proceed with Phase 3: Person Intelligence module
