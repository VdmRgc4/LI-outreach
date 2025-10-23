#!/usr/bin/env python3
"""
LinkedIn Outreach Automation - Main Entry Point
Orchestrates the full workflow from CSV input to personalized message generation
"""

import argparse
import sys
from datetime import datetime
from modules.csv_handler import CSVHandler


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
        default=60,
        help="Minimum confidence score to generate message (default: 60)"
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
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
    print("PHASE 1 COMPLETE: Project Setup & CSV I/O")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Run tests: python modules/csv_handler.py")
    print("  2. Commit changes: git add . && git commit -m 'Phase 1: Setup complete'")
    print("  3. Continue with Phase 2: Company Intelligence module")
    print("\n⚠️  Full processing logic will be implemented in Phase 5")
    print("    Current status: CSV I/O validated ✅")


if __name__ == "__main__":
    main()
