"""Upload local sample documents to the configured Azure Blob container."""

from __future__ import annotations

import argparse
import mimetypes
import os
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCS_DIR = "data/sample-docs"
SKIPPED_FILENAMES = {"README.md"}


class ConfigError(RuntimeError):
    """Raised when required local configuration is missing or invalid."""


@dataclass(frozen=True)
class UploadItem:
    path: Path
    relative_path: str
    blob_name: str
    size_bytes: int


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
        description="Upload local sample documents to Azure Blob Storage."
    )
    parser.add_argument(
        "--docs-dir",
        default=os.getenv("SAMPLE_DOCS_DIR", DEFAULT_DOCS_DIR),
        help="Directory containing local documents. Defaults to SAMPLE_DOCS_DIR.",
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
        "--dry-run",
        action="store_true",
        help="Print the upload plan without connecting to Azure.",
    )
    return parser.parse_args()


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    if "replace-with-" in value:
        raise ConfigError(f"{name} still contains a placeholder value")
    return value


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def normalize_prefix(prefix: str) -> str:
    return prefix.strip().strip("/")


def build_blob_name(relative_path: str, prefix: str) -> str:
    if prefix:
        return f"{prefix}/{relative_path}"
    return relative_path


def should_skip(path: Path, docs_dir: Path) -> bool:
    relative_parts = path.relative_to(docs_dir).parts
    if path.name in SKIPPED_FILENAMES:
        return True
    return any(part.startswith(".") for part in relative_parts)


def find_upload_items(docs_dir: Path, prefix: str) -> list[UploadItem]:
    if not docs_dir.exists():
        raise ConfigError(f"Document directory does not exist: {display_path(docs_dir)}")
    if not docs_dir.is_dir():
        raise ConfigError(f"Document path is not a directory: {display_path(docs_dir)}")

    items: list[UploadItem] = []
    for path in sorted(docs_dir.rglob("*")):
        if not path.is_file() or should_skip(path, docs_dir):
            continue

        relative_path = path.relative_to(docs_dir).as_posix()
        items.append(
            UploadItem(
                path=path,
                relative_path=relative_path,
                blob_name=build_blob_name(relative_path, prefix),
                size_bytes=path.stat().st_size,
            )
        )

    if not items:
        raise ConfigError(f"No uploadable documents found in {display_path(docs_dir)}")

    return items


def content_type_for(path: Path) -> str:
    if path.suffix.lower() == ".md":
        return "text/markdown; charset=utf-8"
    if path.suffix.lower() in {".csv", ".json", ".txt"}:
        guessed_type, _ = mimetypes.guess_type(path.name)
        return f"{guessed_type or 'text/plain'}; charset=utf-8"

    guessed_type, _ = mimetypes.guess_type(path.name)
    return guessed_type or "application/octet-stream"


def upload_items(
    *,
    account_url: str,
    account_key: str,
    container_name: str,
    items: list[UploadItem],
) -> int:
    try:
        from azure.core.exceptions import ResourceExistsError
        from azure.storage.blob import BlobServiceClient, ContentSettings
    except ImportError as exc:
        raise ConfigError(
            "Missing Azure Blob Storage SDK. Run: python -m pip install -r app/requirements.txt"
        ) from exc

    service_client = BlobServiceClient(account_url=account_url, credential=account_key)
    container_client = service_client.get_container_client(container_name)

    try:
        container_client.create_container()
        container_state = "created"
    except ResourceExistsError:
        container_state = "already exists"

    print(f"Container ready: {container_name} ({container_state}).")

    uploaded_bytes = 0
    for item in items:
        with item.path.open("rb") as document:
            container_client.upload_blob(
                name=item.blob_name,
                data=document,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type_for(item.path)),
                metadata={
                    "source": "sample-docs",
                    "relative_path": item.relative_path,
                },
            )
        uploaded_bytes += item.size_bytes
        print(
            f"Uploaded {item.relative_path} -> {item.blob_name} "
            f"({item.size_bytes} bytes)"
        )

    return uploaded_bytes


def main() -> int:
    try:
        load_local_dotenv()
        args = parse_args()

        docs_dir = resolve_path(args.docs_dir)
        prefix = normalize_prefix(args.prefix)
        container_name = (args.container_name or "").strip()

        items = find_upload_items(docs_dir, prefix)

        print(f"Using docs directory: {display_path(docs_dir)}")
        print(f"Found {len(items)} document(s) to upload.")
        if prefix:
            print(f"Using blob prefix: {prefix}")

        if args.dry_run:
            for item in items:
                print(
                    f"Would upload {item.relative_path} -> {item.blob_name} "
                    f"({item.size_bytes} bytes)"
                )
            print("Dry run complete. No blobs were uploaded.")
            return 0

        if not container_name:
            raise ConfigError(
                "Missing required environment variable: AZURE_STORAGE_CONTAINER_NAME"
            )

        account_url = require_env("AZURE_STORAGE_ACCOUNT_URL")
        account_key = require_env("AZURE_STORAGE_ACCOUNT_KEY")
        account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "").strip()

        if account_name:
            print(f"Using storage account: {account_name}")
        print(f"Using storage account URL: {account_url}")
        print(f"Using storage container: {container_name}")
        print("Overwrite enabled: existing blobs with the same names will be replaced.")

        uploaded_bytes = upload_items(
            account_url=account_url,
            account_key=account_key,
            container_name=container_name,
            items=items,
        )
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Upload failed: {exc}", file=sys.stderr)
        return 1

    print(f"Done. Uploaded {len(items)} document(s), {uploaded_bytes} bytes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
