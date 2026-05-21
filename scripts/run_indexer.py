"""Read text blobs, chunk them, embed them, and upload chunks to Azure AI Search."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_TEXT_SUFFIXES = {".csv", ".json", ".md", ".txt"}
DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 120
DEFAULT_BATCH_SIZE = 16


class ConfigError(RuntimeError):
    """Raised when required local configuration is missing or invalid."""


@dataclass(frozen=True)
class IndexerConfig:
    storage_account_url: str
    storage_account_key: str
    container_name: str
    blob_prefix: str
    search_endpoint: str
    search_api_key: str
    search_index_name: str
    openai_endpoint: str
    openai_api_key: str
    openai_api_version: str
    embedding_deployment: str
    chunk_size: int
    chunk_overlap: int
    batch_size: int


@dataclass(frozen=True)
class SourceDocument:
    blob_name: str
    filename: str
    text: str


@dataclass(frozen=True)
class ChunkRecord:
    id: str
    content: str
    source_blob_name: str
    source_filename: str
    chunk_number: int


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
        description="Index text documents from Azure Blob Storage into Azure AI Search."
    )
    parser.add_argument(
        "--container-name",
        default=os.getenv("AZURE_STORAGE_CONTAINER_NAME"),
        help="Blob container name. Defaults to AZURE_STORAGE_CONTAINER_NAME.",
    )
    parser.add_argument(
        "--prefix",
        default=os.getenv("AZURE_STORAGE_BLOB_PREFIX", ""),
        help="Optional blob name prefix, for example 'sample-docs'.",
    )
    parser.add_argument(
        "--index-name",
        default=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        help="Search index name. Defaults to AZURE_SEARCH_INDEX_NAME.",
    )
    parser.add_argument(
        "--chunk-size",
        default=os.getenv("CHUNK_SIZE", str(DEFAULT_CHUNK_SIZE)),
        help="Maximum characters per chunk. Defaults to CHUNK_SIZE.",
    )
    parser.add_argument(
        "--chunk-overlap",
        default=os.getenv("CHUNK_OVERLAP", str(DEFAULT_CHUNK_OVERLAP)),
        help="Characters repeated from the previous chunk. Defaults to CHUNK_OVERLAP.",
    )
    parser.add_argument(
        "--batch-size",
        default=os.getenv("INDEXER_BATCH_SIZE", str(DEFAULT_BATCH_SIZE)),
        help="Chunks to embed and upload per batch.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read and chunk blobs without calling embeddings or Search.",
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


def parse_non_negative_int(value: str, name: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
    if parsed < 0:
        raise ConfigError(f"{name} must be zero or greater")
    return parsed


def normalize_prefix(prefix: str) -> str:
    return prefix.strip().strip("/")


def load_config(args: argparse.Namespace) -> IndexerConfig:
    container_name = (args.container_name or "").strip()
    if not container_name:
        raise ConfigError(
            "Missing required environment variable: AZURE_STORAGE_CONTAINER_NAME"
        )

    index_name = (args.index_name or "").strip()
    if not index_name and not args.dry_run:
        raise ConfigError("Missing required environment variable: AZURE_SEARCH_INDEX_NAME")

    chunk_size = parse_positive_int(str(args.chunk_size), "CHUNK_SIZE")
    chunk_overlap = parse_non_negative_int(str(args.chunk_overlap), "CHUNK_OVERLAP")
    if chunk_overlap >= chunk_size:
        raise ConfigError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")

    return IndexerConfig(
        storage_account_url=require_env("AZURE_STORAGE_ACCOUNT_URL"),
        storage_account_key=require_env("AZURE_STORAGE_ACCOUNT_KEY"),
        container_name=container_name,
        blob_prefix=normalize_prefix(args.prefix or ""),
        search_endpoint=(
            optional_env("AZURE_SEARCH_ENDPOINT")
            if args.dry_run
            else require_env("AZURE_SEARCH_ENDPOINT")
        ),
        search_api_key=(
            optional_env("AZURE_SEARCH_API_KEY")
            if args.dry_run
            else require_env("AZURE_SEARCH_API_KEY")
        ),
        search_index_name=index_name,
        openai_endpoint=(
            optional_env("AZURE_OPENAI_ENDPOINT")
            if args.dry_run
            else require_env("AZURE_OPENAI_ENDPOINT")
        ),
        openai_api_key=(
            optional_env("AZURE_OPENAI_API_KEY")
            if args.dry_run
            else require_env("AZURE_OPENAI_API_KEY")
        ),
        openai_api_version=(
            optional_env("AZURE_OPENAI_API_VERSION")
            if args.dry_run
            else require_env("AZURE_OPENAI_API_VERSION")
        ),
        embedding_deployment=(
            optional_env("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
            if args.dry_run
            else require_env("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        ),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        batch_size=parse_positive_int(str(args.batch_size), "INDEXER_BATCH_SIZE"),
    )


def blob_list_prefix(prefix: str) -> str | None:
    if not prefix:
        return None
    return f"{prefix}/"


def is_supported_text_blob(blob_name: str) -> bool:
    return Path(blob_name).suffix.lower() in SUPPORTED_TEXT_SUFFIXES


def read_source_documents(config: IndexerConfig) -> tuple[list[SourceDocument], int]:
    try:
        from azure.storage.blob import BlobServiceClient
    except ImportError as exc:
        raise ConfigError(
            "Missing Azure Blob Storage SDK. Run: python -m pip install -r app/requirements.txt"
        ) from exc

    service_client = BlobServiceClient(
        account_url=config.storage_account_url,
        credential=config.storage_account_key,
    )
    container_client = service_client.get_container_client(config.container_name)

    documents: list[SourceDocument] = []
    skipped_count = 0
    for blob in container_client.list_blobs(
        name_starts_with=blob_list_prefix(config.blob_prefix)
    ):
        if blob.name.endswith("/") or not is_supported_text_blob(blob.name):
            skipped_count += 1
            continue

        blob_client = container_client.get_blob_client(blob.name)
        raw_content = blob_client.download_blob().readall()
        try:
            text = raw_content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ConfigError(
                f"Blob is not UTF-8 text and cannot be indexed by this script: {blob.name}"
            ) from exc

        documents.append(
            SourceDocument(
                blob_name=blob.name,
                filename=Path(blob.name).name,
                text=text,
            )
        )

    return documents, skipped_count


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(normalized):
            break
        start = end - chunk_overlap

    return chunks


def stable_chunk_id(blob_name: str, chunk_number: int) -> str:
    raw_id = f"{blob_name}#{chunk_number}".encode("utf-8")
    return hashlib.sha256(raw_id).hexdigest()


def build_chunks(
    documents: Iterable[SourceDocument],
    chunk_size: int,
    chunk_overlap: int,
) -> list[ChunkRecord]:
    records: list[ChunkRecord] = []
    for document in documents:
        for chunk_number, content in enumerate(
            chunk_text(document.text, chunk_size, chunk_overlap),
            start=1,
        ):
            records.append(
                ChunkRecord(
                    id=stable_chunk_id(document.blob_name, chunk_number),
                    content=content,
                    source_blob_name=document.blob_name,
                    source_filename=document.filename,
                    chunk_number=chunk_number,
                )
            )
    return records


def batched(records: list[ChunkRecord], batch_size: int) -> Iterable[list[ChunkRecord]]:
    for start in range(0, len(records), batch_size):
        yield records[start : start + batch_size]


def create_embedding_client(config: IndexerConfig):
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


def create_search_client(config: IndexerConfig):
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


def embed_texts(client, deployment_name: str, texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(model=deployment_name, input=texts)
    ordered_items = sorted(response.data, key=lambda item: item.index)
    return [item.embedding for item in ordered_items]


def to_search_document(record: ChunkRecord, embedding: list[float]) -> dict[str, object]:
    return {
        "id": record.id,
        "content": record.content,
        "content_vector": embedding,
        "source_blob_name": record.source_blob_name,
        "source_filename": record.source_filename,
        "chunk_number": record.chunk_number,
    }


def indexing_result_succeeded(result) -> bool:
    if isinstance(result, dict):
        return bool(result.get("succeeded"))
    return bool(result.succeeded)


def indexing_result_key(result) -> str:
    if isinstance(result, dict):
        return str(result.get("key", "unknown key"))
    return str(getattr(result, "key", "unknown key"))


def indexing_result_error(result) -> str:
    if isinstance(result, dict):
        return str(
            result.get("errorMessage")
            or result.get("error_message")
            or "unknown indexing error"
        )
    return str(getattr(result, "error_message", "unknown indexing error"))


def upload_chunks(config: IndexerConfig, chunks: list[ChunkRecord]) -> int:
    embedding_client = create_embedding_client(config)
    search_client = create_search_client(config)

    indexed_count = 0
    for batch_number, batch in enumerate(batched(chunks, config.batch_size), start=1):
        embeddings = embed_texts(
            embedding_client,
            config.embedding_deployment,
            [record.content for record in batch],
        )
        documents = [
            to_search_document(record, embedding)
            for record, embedding in zip(batch, embeddings, strict=True)
        ]
        results = search_client.upload_documents(documents=documents)
        failed = [result for result in results if not indexing_result_succeeded(result)]
        if failed:
            first_failure = failed[0]
            raise RuntimeError(
                "Search indexing failed for "
                f"{indexing_result_key(first_failure)}: "
                f"{indexing_result_error(first_failure)}"
            )

        indexed_count += len(results)
        print(f"Indexed batch {batch_number}: {len(results)} chunk(s)")

    return indexed_count


def main() -> int:
    try:
        if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
            parse_args()
            return 0

        load_local_dotenv()
        args = parse_args()
        config = load_config(args)

        print(f"Using storage account URL: {config.storage_account_url}")
        print(f"Using storage container: {config.container_name}")
        if config.blob_prefix:
            print(f"Using blob prefix: {config.blob_prefix}")
        if config.search_index_name:
            print(f"Using Search index: {config.search_index_name}")
        if config.embedding_deployment:
            print(f"Using embedding deployment: {config.embedding_deployment}")
        print(
            "Chunking: "
            f"{config.chunk_size} characters with {config.chunk_overlap} character overlap."
        )

        documents, skipped_count = read_source_documents(config)
        chunks = build_chunks(documents, config.chunk_size, config.chunk_overlap)

        print(f"Blobs read: {len(documents)}")
        if skipped_count:
            print(f"Skipped non-text blobs: {skipped_count}")
        print(f"Chunks created: {len(chunks)}")

        if args.dry_run:
            print("Dry run complete. No embeddings were created and no chunks were indexed.")
            print(
                f"Done. Blobs read: {len(documents)}. "
                f"Chunks created: {len(chunks)}. Chunks indexed: 0."
            )
            return 0

        if not chunks:
            print("No chunks to index.")
            print(
                f"Done. Blobs read: {len(documents)}. "
                "Chunks created: 0. Chunks indexed: 0."
            )
            return 0

        indexed_count = upload_chunks(config, chunks)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Indexing failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"Done. Blobs read: {len(documents)}. "
        f"Chunks created: {len(chunks)}. Chunks indexed: {indexed_count}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
