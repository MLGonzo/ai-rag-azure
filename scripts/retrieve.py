"""Query Azure AI Search and print retrieved chunks for inspection."""

from __future__ import annotations

import argparse
import os
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOP_K = 5
DEFAULT_PREVIEW_CHARS = 500
SEARCH_FIELDS = [
    "id",
    "content",
    "source_blob_name",
    "source_filename",
    "chunk_number",
]


class ConfigError(RuntimeError):
    """Raised when required local configuration is missing or invalid."""


@dataclass(frozen=True)
class RetrievalConfig:
    search_endpoint: str
    search_api_key: str
    search_index_name: str
    openai_endpoint: str
    openai_api_key: str
    openai_api_version: str
    embedding_deployment: str
    mode: str
    top_k: int
    preview_chars: int


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
    default_mode = os.getenv("RETRIEVAL_MODE", "hybrid").strip().lower()
    parser = argparse.ArgumentParser(
        description="Retrieve matching chunks from Azure AI Search for a question."
    )
    parser.add_argument(
        "question",
        nargs="*",
        help="Question to retrieve context for. If omitted, the script prompts for it.",
    )
    parser.add_argument(
        "--mode",
        choices=["keyword", "vector", "hybrid"],
        default=default_mode,
        help="Retrieval mode. Defaults to RETRIEVAL_MODE or hybrid.",
    )
    parser.add_argument(
        "--top-k",
        default=os.getenv("RETRIEVAL_TOP_K", str(DEFAULT_TOP_K)),
        help="Number of chunks to return. Defaults to RETRIEVAL_TOP_K.",
    )
    parser.add_argument(
        "--preview-chars",
        default=os.getenv("RETRIEVAL_PREVIEW_CHARS", str(DEFAULT_PREVIEW_CHARS)),
        help="Maximum characters to print from each chunk.",
    )
    parser.add_argument(
        "--index-name",
        default=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        help="Search index name. Defaults to AZURE_SEARCH_INDEX_NAME.",
    )
    return parser.parse_args()


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    if "replace-with-" in value:
        raise ConfigError(f"{name} still contains a placeholder value")
    return value


def optional_env(name: str) -> str:
    return os.getenv(name, "").strip()


def parse_positive_int(value: str, name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
    if parsed <= 0:
        raise ConfigError(f"{name} must be greater than zero")
    return parsed


def load_config(args: argparse.Namespace) -> RetrievalConfig:
    index_name = (args.index_name or "").strip()
    if not index_name:
        raise ConfigError("Missing required environment variable: AZURE_SEARCH_INDEX_NAME")

    mode = str(args.mode).strip().lower()
    if mode not in {"keyword", "vector", "hybrid"}:
        raise ConfigError("RETRIEVAL_MODE must be keyword, vector, or hybrid")

    needs_embedding = mode in {"vector", "hybrid"}

    return RetrievalConfig(
        search_endpoint=require_env("AZURE_SEARCH_ENDPOINT"),
        search_api_key=require_env("AZURE_SEARCH_API_KEY"),
        search_index_name=index_name,
        openai_endpoint=(
            require_env("AZURE_OPENAI_ENDPOINT")
            if needs_embedding
            else optional_env("AZURE_OPENAI_ENDPOINT")
        ),
        openai_api_key=(
            require_env("AZURE_OPENAI_API_KEY")
            if needs_embedding
            else optional_env("AZURE_OPENAI_API_KEY")
        ),
        openai_api_version=(
            require_env("AZURE_OPENAI_API_VERSION")
            if needs_embedding
            else optional_env("AZURE_OPENAI_API_VERSION")
        ),
        embedding_deployment=(
            require_env("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
            if needs_embedding
            else optional_env("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        ),
        mode=mode,
        top_k=parse_positive_int(str(args.top_k), "RETRIEVAL_TOP_K"),
        preview_chars=parse_positive_int(
            str(args.preview_chars),
            "RETRIEVAL_PREVIEW_CHARS",
        ),
    )


def question_from_args(args: argparse.Namespace) -> str:
    question = " ".join(args.question).strip()
    if not question:
        question = input("Question: ").strip()
    if not question:
        raise ConfigError("Question cannot be empty")
    return question


def create_embedding_client(config: RetrievalConfig):
    try:
        from openai import AzureOpenAI
    except ImportError as exc:
        raise ConfigError(
            "Missing OpenAI SDK. Run: python -m pip install -r app/requirements.txt"
        ) from exc

    return AzureOpenAI(
        api_key=config.openai_api_key,
        api_version=config.openai_api_version,
        azure_endpoint=config.openai_endpoint,
    )


def create_search_client(config: RetrievalConfig):
    try:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient
    except ImportError as exc:
        raise ConfigError(
            "Missing Azure AI Search SDK. Run: python -m pip install -r app/requirements.txt"
        ) from exc

    return SearchClient(
        endpoint=config.search_endpoint,
        index_name=config.search_index_name,
        credential=AzureKeyCredential(config.search_api_key),
    )


def embed_query(config: RetrievalConfig, question: str) -> list[float]:
    embedding_client = create_embedding_client(config)
    response = embedding_client.embeddings.create(
        model=config.embedding_deployment,
        input=question,
    )
    return list(response.data[0].embedding)


def build_vector_query(vector: list[float], top_k: int):
    try:
        from azure.search.documents.models import VectorizedQuery
    except ImportError as exc:
        raise ConfigError(
            "This Azure AI Search SDK version does not support vector queries. "
            "Run: python -m pip install -r app/requirements.txt"
        ) from exc

    return VectorizedQuery(
        vector=vector,
        k_nearest_neighbors=top_k,
        fields="content_vector",
    )


def search_chunks(
    *,
    search_client: Any,
    question: str,
    config: RetrievalConfig,
    query_vector: list[float] | None,
) -> Iterable[dict[str, Any]]:
    if config.mode == "keyword":
        return search_client.search(
            search_text=question,
            top=config.top_k,
            select=SEARCH_FIELDS,
        )

    if query_vector is None:
        raise ConfigError("Vector retrieval requires a query embedding")

    vector_query = build_vector_query(
        vector=query_vector,
        top_k=config.top_k,
    )

    if config.mode == "vector":
        return search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            top=config.top_k,
            select=SEARCH_FIELDS,
        )

    return search_client.search(
        search_text=question,
        vector_queries=[vector_query],
        top=config.top_k,
        select=SEARCH_FIELDS,
    )


def metadata_value(result: dict[str, Any], name: str, default: str = "unknown") -> str:
    value = result.get(name)
    if value is None or value == "":
        return default
    return str(value)


def format_score(value: object) -> str:
    if isinstance(value, int | float):
        return f"{value:.4f}"
    if value is None:
        return "n/a"
    return str(value)


def content_preview(content: str, preview_chars: int) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= preview_chars:
        return normalized
    if preview_chars <= 3:
        return normalized[:preview_chars]
    return textwrap.shorten(normalized, width=preview_chars, placeholder="...")


def print_results(
    *,
    results: list[dict[str, Any]],
    question: str,
    config: RetrievalConfig,
) -> None:
    print(f"Question: {question}")
    print(f"Retrieval mode: {config.mode}")
    print(f"Search index: {config.search_index_name}")
    if config.mode in {"vector", "hybrid"}:
        print(f"Embedding deployment: {config.embedding_deployment}")
    print(f"Chunks returned: {len(results)}")

    if not results:
        print("No chunks matched the query.")
        return

    for rank, result in enumerate(results, start=1):
        score = result.get("@search.score")
        chunk_id = metadata_value(result, "id")
        source_filename = metadata_value(result, "source_filename")
        source_blob_name = metadata_value(result, "source_blob_name")
        chunk_number = metadata_value(result, "chunk_number")
        content = metadata_value(result, "content", default="")

        print()
        print(f"[{rank}] score={format_score(score)}")
        print(f"Source: {source_filename} ({source_blob_name})")
        print(f"Chunk: {chunk_number}  id={chunk_id}")
        print(f"Preview: {content_preview(content, config.preview_chars)}")


def main() -> int:
    try:
        if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
            parse_args()
            return 0

        load_local_dotenv()
        args = parse_args()
        question = question_from_args(args)
        config = load_config(args)

        print(f"Using Search endpoint: {config.search_endpoint}")
        if config.mode in {"vector", "hybrid"}:
            print(f"Using embedding deployment: {config.embedding_deployment}")

        query_vector = None
        if config.mode in {"vector", "hybrid"}:
            query_vector = embed_query(config, question)

        search_client = create_search_client(config)
        results = list(
            search_chunks(
                search_client=search_client,
                question=question,
                config=config,
                query_vector=query_vector,
            )
        )
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except EOFError:
        print("Configuration error: Question cannot be empty", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Retrieval failed: {exc}", file=sys.stderr)
        return 1

    print_results(results=results, question=question, config=config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
