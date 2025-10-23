"""
Module: csv_handler.py
Purpose: Handle CSV input/output operations for LinkedIn outreach automation
Dependencies: pandas
External calls: None (self-contained)

Input Format:
    CSV file with columns: linkedin_url, first_name, last_name, title, company_name
    Optional columns: notes, company_url, industry, company_size

Output Format:
    CSV file with all input columns plus:
    - subject_line: str
    - message_body: str
    - hook_type: str
    - key_insights: str (JSON array as string)
    - competitive_intel: str
    - technical_gaps: str (JSON array as string)
    - geo_readiness_score: int
    - confidence_score: int
    - audit_date: str (ISO format)
    - processing_time_seconds: float
"""

import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
import json
import sys
import os

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class CSVHandler:
    """Handles CSV input/output operations for LinkedIn outreach automation"""

    def __init__(self):
        self.required_columns = config.REQUIRED_INPUT_COLUMNS
        self.output_columns = config.OUTPUT_COLUMNS

    def read_input_csv(self, file_path: str) -> pd.DataFrame:
        """
        Read and validate input CSV file

        Args:
            file_path: Path to input CSV file

        Returns:
            DataFrame with validated prospect data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If required columns are missing
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input file not found: {file_path}")

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {str(e)}")

        # Validate required columns
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        # Remove duplicates based on LinkedIn URL
        initial_count = len(df)
        df = df.drop_duplicates(subset=['linkedin_url'], keep='first')
        duplicates_removed = initial_count - len(df)

        if duplicates_removed > 0:
            print(f"Removed {duplicates_removed} duplicate LinkedIn URLs")

        # Clean data
        df = df.fillna("")  # Replace NaN with empty strings
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)  # Strip whitespace

        return df

    def write_output_csv(self, data: List[Dict], file_path: str) -> None:
        """
        Write results to output CSV file

        Args:
            data: List of dictionaries containing prospect data and results
            file_path: Path to output CSV file
        """
        if not data:
            raise ValueError("No data to write to CSV")

        # Convert list of dicts to DataFrame
        df = pd.DataFrame(data)

        # Ensure all output columns are present
        for col in self.output_columns:
            if col not in df.columns:
                df[col] = ""

        # Reorder columns to match output format
        df = df[self.output_columns]

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)

        # Write to CSV
        df.to_csv(file_path, index=False, encoding='utf-8')
        print(f"Output written to: {file_path}")

    def append_to_output_csv(self, row_data: Dict, file_path: str) -> None:
        """
        Append a single row to output CSV (for streaming results)

        Args:
            row_data: Dictionary containing single prospect result
            file_path: Path to output CSV file
        """
        # Check if file exists
        file_exists = os.path.exists(file_path)

        # Convert to DataFrame
        df = pd.DataFrame([row_data])

        # Ensure all output columns are present
        for col in self.output_columns:
            if col not in df.columns:
                df[col] = ""

        # Reorder columns
        df = df[self.output_columns]

        # Append to CSV
        df.to_csv(
            file_path,
            mode='a' if file_exists else 'w',
            header=not file_exists,
            index=False,
            encoding='utf-8'
        )

    def validate_linkedin_url(self, url: str) -> bool:
        """
        Validate LinkedIn URL format

        Args:
            url: LinkedIn profile URL

        Returns:
            True if valid, False otherwise
        """
        if not url:
            return False

        valid_patterns = [
            "linkedin.com/in/",
            "linkedin.com/sales/lead/",
            "linkedin.com/sales/people/"
        ]

        return any(pattern in url.lower() for pattern in valid_patterns)

    def get_prospect_summary(self, df: pd.DataFrame) -> Dict:
        """
        Generate summary statistics from input data

        Args:
            df: Input DataFrame

        Returns:
            Dictionary with summary statistics
        """
        summary = {
            "total_prospects": len(df),
            "unique_companies": df['company_name'].nunique(),
            "prospects_with_notes": (df.get('notes', pd.Series([''])) != '').sum(),
            "prospects_with_company_url": (df.get('company_url', pd.Series([''])) != '').sum(),
            "invalid_urls": sum(not self.validate_linkedin_url(url) for url in df['linkedin_url'])
        }

        return summary


def create_sample_input_csv(file_path: str) -> None:
    """
    Create a sample input CSV file for testing

    Args:
        file_path: Path where sample CSV should be created
    """
    sample_data = [
        {
            "linkedin_url": "https://www.linkedin.com/in/sample-profile-1",
            "first_name": "John",
            "last_name": "Doe",
            "title": "VP of Marketing",
            "company_name": "Acme Corp",
            "notes": "Met at conference",
            "company_url": "",
            "industry": "B2B SaaS",
            "company_size": "500"
        },
        {
            "linkedin_url": "https://www.linkedin.com/in/sample-profile-2",
            "first_name": "Jane",
            "last_name": "Smith",
            "title": "Chief Marketing Officer",
            "company_name": "DataFlow Analytics",
            "notes": "",
            "company_url": "https://dataflowanalytics.com",
            "industry": "Data Analytics",
            "company_size": "200"
        }
    ]

    df = pd.DataFrame(sample_data)
    df.to_csv(file_path, index=False)
    print(f"Sample input CSV created: {file_path}")


if __name__ == "__main__":
    # Test CSV handler
    print("Testing CSV Handler...")

    # Create sample input
    sample_input = "sample_input.csv"
    create_sample_input_csv(sample_input)

    # Test reading
    handler = CSVHandler()
    df = handler.read_input_csv(sample_input)
    print(f"\nRead {len(df)} prospects from CSV")

    # Test summary
    summary = handler.get_prospect_summary(df)
    print(f"\nSummary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Test writing (with mock data)
    output_data = []
    for _, row in df.iterrows():
        output_row = row.to_dict()
        output_row.update({
            "subject_line": "Sample subject",
            "message_body": "Sample message",
            "hook_type": "Competitive Intelligence",
            "key_insights": json.dumps(["Insight 1", "Insight 2"]),
            "competitive_intel": "Sample competitive intel",
            "technical_gaps": json.dumps(["Gap 1", "Gap 2"]),
            "geo_readiness_score": 75,
            "confidence_score": 85,
            "audit_date": datetime.now().isoformat(),
            "processing_time_seconds": 30.5
        })
        output_data.append(output_row)

    sample_output = "output/sample_output.csv"
    handler.write_output_csv(output_data, sample_output)

    print("\n✅ CSV Handler tests passed!")
