from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    queries_path = Path(__file__).with_name("queries_test.json")
    queries = json.loads(queries_path.read_text(encoding="utf-8"))
    print("Keyword baseline scaffold")
    print(f"Loaded {len(queries)} queries")


if __name__ == "__main__":
    main()
