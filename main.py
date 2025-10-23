#!/usr/bin/env python3
"""
LinkedIn Outreach Automation - Main Entry Point
Orchestrates the full workflow from CSV input to personalized message generation
"""

import argparse
import sys
import json
import time
from datetime import datetime
from typing import Dict, List
import os

from modules.csv_handler import CSVHandler
from modules.company_intel import get_company_intel
from modules.person_intel import get_person_intel
from modules.message_gen import generate_message
import config


def process_prospect(
    row: Dict,
    min_confidence: int,
    verbose: bool,
    error_log: List[Dict]
) -> Dict:
    """
    Process a single prospect through the full workflow

    Args:
        row: Prospect data row
        min_confidence: Minimum confidence threshold
        verbose: Show detailed logs
        error_log: List to append errors to

    Returns:
        Complete output row with results
    """
    start_time = time.time()

    # Extract prospect info
    first_name = row.get("first_name", "")
    last_name = row.get("last_name", "")
    title = row.get("title", "")
    company_name = row.get("company_name", "")
    linkedin_url = row.get("linkedin_url", "")
    company_url = row.get("company_url", "")  # Optional pre-provided URL

    print(f"\n{'='*70}")
    print(f"Processing: {first_name} {last_name} - {title} at {company_name}")
    print(f"{'='*70}")

    # Prepare output row (start with input data)
    output_row = row.copy()
    output_row.update({
        "subject_line": "",
        "message_body": "",
        "hook_type": "",
        "key_insights": "",
        "competitive_intel": "",
        "technical_gaps": "",
        "geo_readiness_score": 0,
        "confidence_score": 0,
        "audit_date": datetime.now().isoformat(),
        "processing_time_seconds": 0
    })

    try:
        # Step 1: Company Intelligence
        print("\n[1/3] Company Intelligence")
        company_data = get_company_intel(company_name, company_url if company_url else None)

        if company_data.get("confidence", 0) < 30:
            print(f"  ⚠️  Low company intelligence confidence: {company_data.get('confidence', 0)}/100")

        # Step 2: Person Intelligence
        print("\n[2/3] Person Intelligence")
        person_data = get_person_intel(first_name, last_name, company_name, title)

        if person_data.get("confidence", 0) < 30:
            print(f"  ⚠️  Low person intelligence confidence: {person_data.get('confidence', 0)}/100")

        # Step 3: Message Generation
        print("\n[3/3] Message Generation")

        prospect_info = {
            "first_name": first_name,
            "last_name": last_name,
            "title": title,
            "company_name": company_name,
            "linkedin_url": linkedin_url
        }

        message_data = generate_message(company_data, person_data, prospect_info)

        # Check confidence threshold
        confidence_score = message_data.get("confidence_score", 0)

        if confidence_score < min_confidence:
            print(f"\n❌ SKIPPED: Confidence {confidence_score}/100 below minimum {min_confidence}")
            error_log.append({
                "name": f"{first_name} {last_name}",
                "company": company_name,
                "reason": f"Low confidence ({confidence_score}/{min_confidence})",
                "timestamp": datetime.now().isoformat()
            })
            output_row["confidence_score"] = confidence_score
            output_row["processing_time_seconds"] = round(time.time() - start_time, 2)
            return output_row

        # Populate output row with results
        output_row.update({
            "company_url": company_data.get("company_url", ""),
            "industry": row.get("industry", ""),  # Keep from input if exists
            "subject_line": message_data.get("subject_line", ""),
            "message_body": message_data.get("message_body", ""),
            "hook_type": message_data.get("hook_type", ""),
            "key_insights": json.dumps(message_data.get("key_insights", [])),
            "competitive_intel": ", ".join(company_data.get("competitors", [])),
            "technical_gaps": json.dumps(company_data.get("technical_gaps", [])),
            "geo_readiness_score": company_data.get("geo_readiness_score", 0),
            "confidence_score": confidence_score,
            "processing_time_seconds": round(time.time() - start_time, 2)
        })

        print(f"\n✅ SUCCESS: Message generated with {confidence_score}/100 confidence")
        print(f"   Processing time: {output_row['processing_time_seconds']}s")

        return output_row

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        error_log.append({
            "name": f"{first_name} {last_name}",
            "company": company_name,
            "reason": str(e),
            "timestamp": datetime.now().isoformat()
        })

        output_row["processing_time_seconds"] = round(time.time() - start_time, 2)
        return output_row


def generate_summary_report(
    total_prospects: int,
    successful: int,
    skipped: int,
    errors: int,
    total_time: float,
    error_log: List[Dict]
) -> str:
    """
    Generate summary report of processing results

    Args:
        total_prospects: Total number of prospects processed
        successful: Number successfully processed
        skipped: Number skipped due to low confidence
        errors: Number with errors
        total_time: Total processing time in seconds
        error_log: List of errors

    Returns:
        Formatted summary report string
    """
    success_rate = (successful / total_prospects * 100) if total_prospects > 0 else 0
    avg_time = (total_time / total_prospects) if total_prospects > 0 else 0

    report = f"""
{'='*70}
PROCESSING COMPLETE - SUMMARY REPORT
{'='*70}

Total Prospects Processed: {total_prospects}
✅ Successful:             {successful} ({success_rate:.1f}%)
⚠️  Skipped (low conf):    {skipped}
❌ Errors:                 {errors}

Processing Time:           {total_time:.1f}s
Average per Prospect:      {avg_time:.1f}s

{'='*70}
"""

    if error_log:
        report += f"\nERRORS AND SKIPPED ({len(error_log)} total):\n"
        for idx, error in enumerate(error_log[:10], 1):  # Show first 10
            report += f"{idx}. {error['name']} ({error['company']}): {error['reason']}\n"

        if len(error_log) > 10:
            report += f"... and {len(error_log) - 10} more (see error_log.json)\n"

    return report


def main():
    """Main entry point for LinkedIn outreach automation"""

    parser = argparse.ArgumentParser(
        description="LinkedIn Outreach Automation - Generate personalized outreach messages at scale"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to input CSV file with prospect data"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Path to output CSV file for results"
    )

    parser.add_argument(
        "--min-confidence",
        type=int,
        default=config.MIN_CONFIDENCE_SCORE,
        help=f"Minimum confidence score to generate message (default: {config.MIN_CONFIDENCE_SCORE})"
    )

    parser.add_argument(
        "--max-batch",
        type=int,
        default=None,
        help="Maximum number of prospects to process (default: all)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed processing logs"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("LinkedIn Outreach Automation System")
    print("Breakspear Advisory Methodology")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check for API key
    if not config.ANTHROPIC_API_KEY:
        print("⚠️  WARNING: ANTHROPIC_API_KEY not found in environment")
        print("   Message generation will be skipped")
        print("   Set API key in .env file to enable message generation")
        print()

    # Initialize CSV handler
    csv_handler = CSVHandler()

    # Read input CSV
    print(f"Reading input file: {args.input}")
    try:
        df = csv_handler.read_input_csv(args.input)
        print(f"✅ Loaded {len(df)} prospects")
    except Exception as e:
        print(f"❌ Error reading input CSV: {str(e)}")
        sys.exit(1)

    # Show summary
    summary = csv_handler.get_prospect_summary(df)
    print("\nInput Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Limit batch if specified
    if args.max_batch:
        df = df.head(args.max_batch)
        print(f"\nLimited to {len(df)} prospects (--max-batch={args.max_batch})")

    print("\n" + "=" * 70)
    print("STARTING BATCH PROCESSING")
    print("=" * 70)

    # Process prospects
    start_time = time.time()
    output_rows = []
    error_log = []
    successful = 0
    skipped = 0
    errors_count = 0

    for idx, (_, row) in enumerate(df.iterrows(), 1):
        print(f"\n[{idx}/{len(df)}] ", end="")

        try:
            output_row = process_prospect(
                row.to_dict(),
                args.min_confidence,
                args.verbose,
                error_log
            )

            output_rows.append(output_row)

            # Track results
            if output_row.get("message_body"):
                successful += 1
            elif output_row.get("confidence_score", 0) < args.min_confidence:
                skipped += 1
            else:
                errors_count += 1

            # Progress indicator
            progress = (idx / len(df)) * 100
            print(f"Progress: {progress:.1f}% ({idx}/{len(df)})")

        except Exception as e:
            print(f"❌ CRITICAL ERROR: {str(e)}")
            errors_count += 1
            error_log.append({
                "name": f"Row {idx}",
                "company": "Unknown",
                "reason": f"Critical error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

    total_time = time.time() - start_time

    # Write output CSV
    print(f"\n{'='*70}")
    print("Writing output CSV...")
    try:
        csv_handler.write_output_csv(output_rows, args.output)
        print(f"✅ Output written to: {args.output}")
    except Exception as e:
        print(f"❌ Error writing output CSV: {str(e)}")
        sys.exit(1)

    # Write error log if there are errors
    if error_log:
        error_log_file = "error_log.json"
        try:
            with open(error_log_file, 'w') as f:
                json.dump(error_log, f, indent=2)
            print(f"⚠️  Error log written to: {error_log_file}")
        except Exception as e:
            print(f"⚠️  Could not write error log: {str(e)}")

    # Generate and display summary report
    report = generate_summary_report(
        len(df),
        successful,
        skipped,
        errors_count,
        total_time,
        error_log
    )
    print(report)

    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Exit with appropriate code
    if errors_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
