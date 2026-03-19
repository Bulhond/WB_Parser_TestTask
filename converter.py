import argparse
import json
from pathlib import Path

from wb_parser.xlsx_export import export_xlsx_files


def load_items(json_path: Path) -> list:
    with json_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("JSON file must contain a list of items")

    return data


def find_latest_json(data_dir: Path) -> Path:
    json_files = sorted(data_dir.glob("products_*.json"))
    if not json_files:
        raise FileNotFoundError("No JSON files found in data directory")

    return json_files[-1]


def main():
    parser = argparse.ArgumentParser(
        description="Convert scraped WB JSON into XLSX files"
    )
    parser.add_argument(
        "json_file",
        nargs="?",
        help="Path to JSON file created by Scrapy FEEDS",
    )
    args = parser.parse_args()

    if args.json_file:
        json_path = Path(args.json_file)
    else:
        json_path = find_latest_json(Path("data"))

    items = load_items(json_path)

    output_dir = Path("output")
    catalog_path, filtered_path, filtered_count = export_xlsx_files(items, output_dir)

    print(f"Loaded {len(items)} items from {json_path}")
    print(f"Catalog saved to {catalog_path}")
    print(f"Filtered file saved to {filtered_path} ({filtered_count} items)")


if __name__ == "__main__":
    main()
