from __future__ import annotations

from pipeline.utils.qdrant_client import get_qdrant_client


def main() -> None:
    client = get_qdrant_client()
    print(f"Connected to Qdrant at {client.url}")
    print("Indexing is not wired yet. Next step: create collection and upload vectors.")


if __name__ == "__main__":
    main()
