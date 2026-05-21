"""Create the Azure AI Search index used by the RAG sample."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EMBEDDING_DIMENSIONS = 1536
VECTOR_PROFILE_NAME = "content-vector-profile"
VECTOR_ALGORITHM_NAME = "content-hnsw"


class ConfigError(RuntimeError):
    """Raised when required local configuration is missing or invalid."""


@dataclass(frozen=True)
class SearchConfig:
    endpoint: str
    api_key: str
    index_name: str
    embedding_dimensions: int


def load_local_dotenv() -> None:
    """Load .env from the repo root."""
    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise ConfigError(
            "Missing python-dotenv. Run: python -m pip install -r app/requirements.txt"
        ) from exc

    load_dotenv(REPO_ROOT / ".env")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or update the Azure AI Search index for chunked documents."
    )
    parser.add_argument(
        "--index-name",
        default=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        help="Search index name. Defaults to AZURE_SEARCH_INDEX_NAME.",
    )
    parser.add_argument(
        "--embedding-dimensions",
        default=os.getenv(
            "AZURE_OPENAI_EMBEDDING_DIMENSIONS",
            str(DEFAULT_EMBEDDING_DIMENSIONS),
        ),
        help="Vector dimensions produced by the embedding deployment.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the existing index first. This removes indexed chunks.",
    )
    return parser.parse_args()


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    if "replace-with-" in value:
        raise ConfigError(f"{name} still contains a placeholder value")
    return value


def parse_positive_int(value: str, name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
    if parsed <= 0:
        raise ConfigError(f"{name} must be greater than zero")
    return parsed


def load_config(args: argparse.Namespace) -> SearchConfig:
    index_name = (args.index_name or "").strip()
    if not index_name:
        raise ConfigError("Missing required environment variable: AZURE_SEARCH_INDEX_NAME")

    return SearchConfig(
        endpoint=require_env("AZURE_SEARCH_ENDPOINT"),
        api_key=require_env("AZURE_SEARCH_API_KEY"),
        index_name=index_name,
        embedding_dimensions=parse_positive_int(
            str(args.embedding_dimensions),
            "AZURE_OPENAI_EMBEDDING_DIMENSIONS",
        ),
    )


def build_index(index_name: str, embedding_dimensions: int):
    try:
        from azure.search.documents.indexes.models import (
            HnswAlgorithmConfiguration,
            SearchField,
            SearchFieldDataType,
            SearchIndex,
            SearchableField,
            SimpleField,
            VectorSearch,
            VectorSearchProfile,
        )
    except ImportError as exc:
        raise ConfigError(
            "Missing Azure AI Search SDK. Run: python -m pip install -r app/requirements.txt"
        ) from exc

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=embedding_dimensions,
            vector_search_profile_name=VECTOR_PROFILE_NAME,
        ),
        SearchableField(
            name="source_blob_name",
            type=SearchFieldDataType.String,
            filterable=True,
            sortable=True,
        ),
        SearchableField(
            name="source_filename",
            type=SearchFieldDataType.String,
            filterable=True,
            sortable=True,
        ),
        SimpleField(
            name="chunk_number",
            type=SearchFieldDataType.Int32,
            filterable=True,
            sortable=True,
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name=VECTOR_ALGORITHM_NAME)],
        profiles=[
            VectorSearchProfile(
                name=VECTOR_PROFILE_NAME,
                algorithm_configuration_name=VECTOR_ALGORITHM_NAME,
            )
        ],
    )

    return SearchIndex(name=index_name, fields=fields, vector_search=vector_search)


def create_or_update_index(config: SearchConfig, reset: bool) -> None:
    try:
        from azure.core.credentials import AzureKeyCredential
        from azure.core.exceptions import ResourceNotFoundError
        from azure.search.documents.indexes import SearchIndexClient
    except ImportError as exc:
        raise ConfigError(
            "Missing Azure AI Search SDK. Run: python -m pip install -r app/requirements.txt"
        ) from exc

    client = SearchIndexClient(
        endpoint=config.endpoint,
        credential=AzureKeyCredential(config.api_key),
    )

    if reset:
        try:
            client.delete_index(config.index_name)
            print(f"Deleted existing index: {config.index_name}")
        except ResourceNotFoundError:
            print(f"No existing index to delete: {config.index_name}")

    index = build_index(config.index_name, config.embedding_dimensions)
    client.create_or_update_index(index)


def main() -> int:
    try:
        if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
            parse_args()
            return 0

        load_local_dotenv()
        args = parse_args()
        config = load_config(args)

        print(f"Using Search endpoint: {config.endpoint}")
        print(f"Using Search index: {config.index_name}")
        print(f"Using embedding dimensions: {config.embedding_dimensions}")
        if args.reset:
            print("Reset enabled: existing indexed chunks will be deleted.")

        create_or_update_index(config, reset=args.reset)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Index creation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Done. Search index is ready: {config.index_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
