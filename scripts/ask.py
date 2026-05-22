"""Answer a question with retrieved chunks as grounded context."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Any

import retrieve


UNKNOWN_ANSWER = "I don't know based on the provided documents."

SYSTEM_PROMPT = f"""You answer questions using only the provided context chunks.

Rules:
- Use only the context chunks. Do not use outside knowledge.
- If the context does not contain the answer, say exactly: "{UNKNOWN_ANSWER}"
- Cite supporting context inline with bracketed source numbers, such as [1].
- Keep the answer concise and factual.
"""


@dataclass(frozen=True)
class AskConfig:
    retrieval: retrieve.RetrievalConfig
    chat_deployment: str
    show_context: bool


def parse_args() -> argparse.Namespace:
    default_mode = os.getenv("RETRIEVAL_MODE", "hybrid").strip().lower()
    parser = argparse.ArgumentParser(
        description="Retrieve context and ask the configured chat model for a grounded answer."
    )
    parser.add_argument(
        "question",
        nargs="*",
        help="Question to answer. If omitted, the script prompts for it.",
    )
    parser.add_argument(
        "--mode",
        choices=["keyword", "vector", "hybrid"],
        default=default_mode,
        help="Retrieval mode. Defaults to RETRIEVAL_MODE or hybrid.",
    )
    parser.add_argument(
        "--top-k",
        default=os.getenv("RETRIEVAL_TOP_K", str(retrieve.DEFAULT_TOP_K)),
        help="Number of chunks to retrieve. Defaults to RETRIEVAL_TOP_K.",
    )
    parser.add_argument(
        "--preview-chars",
        default=os.getenv(
            "RETRIEVAL_PREVIEW_CHARS",
            str(retrieve.DEFAULT_PREVIEW_CHARS),
        ),
        help="Maximum characters to print per chunk when --show-context is used.",
    )
    parser.add_argument(
        "--index-name",
        default=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        help="Search index name. Defaults to AZURE_SEARCH_INDEX_NAME.",
    )
    parser.add_argument(
        "--chat-deployment",
        default=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        help="Chat deployment name. Defaults to AZURE_OPENAI_CHAT_DEPLOYMENT.",
    )
    parser.add_argument(
        "--show-context",
        action="store_true",
        help="Print retrieved chunks before the answer.",
    )
    return parser.parse_args()


def load_config(args: argparse.Namespace) -> AskConfig:
    retrieval_config = retrieve.load_config(args)
    retrieval_config = retrieve.RetrievalConfig(
        search_endpoint=retrieval_config.search_endpoint,
        search_api_key=retrieval_config.search_api_key,
        search_index_name=retrieval_config.search_index_name,
        openai_endpoint=retrieve.require_env("AZURE_OPENAI_ENDPOINT"),
        openai_api_key=retrieve.require_env("AZURE_OPENAI_API_KEY"),
        openai_api_version=retrieve.require_env("AZURE_OPENAI_API_VERSION"),
        embedding_deployment=retrieval_config.embedding_deployment,
        mode=retrieval_config.mode,
        top_k=retrieval_config.top_k,
        preview_chars=retrieval_config.preview_chars,
    )
    chat_deployment = (args.chat_deployment or "").strip()
    if not chat_deployment:
        raise retrieve.ConfigError(
            "Missing required environment variable: AZURE_OPENAI_CHAT_DEPLOYMENT"
        )
    if "replace-with-" in chat_deployment:
        raise retrieve.ConfigError(
            "AZURE_OPENAI_CHAT_DEPLOYMENT still contains a placeholder value"
        )

    return AskConfig(
        retrieval=retrieval_config,
        chat_deployment=chat_deployment,
        show_context=bool(args.show_context),
    )


def create_chat_client(config: AskConfig):
    try:
        from openai import AzureOpenAI
    except ImportError as exc:
        raise retrieve.ConfigError(
            "Missing OpenAI SDK. Run: python -m pip install -r app/requirements.txt"
        ) from exc

    return AzureOpenAI(
        api_key=config.retrieval.openai_api_key,
        api_version=config.retrieval.openai_api_version,
        azure_endpoint=config.retrieval.openai_endpoint,
    )


def source_label(result: dict[str, Any], rank: int) -> str:
    filename = retrieve.metadata_value(result, "source_filename")
    blob_name = retrieve.metadata_value(result, "source_blob_name")
    chunk_number = retrieve.metadata_value(result, "chunk_number")
    return f"[{rank}] {filename} ({blob_name}), chunk {chunk_number}"


def context_block(result: dict[str, Any], rank: int) -> str:
    content = retrieve.metadata_value(result, "content", default="")
    return f"{source_label(result, rank)}\n{content}"


def build_user_prompt(question: str, results: list[dict[str, Any]]) -> str:
    context = "\n\n---\n\n".join(
        context_block(result, rank)
        for rank, result in enumerate(results, start=1)
    )
    return f"""Question:
{question}

Context chunks:
{context}

Answer using only the context chunks."""


def answer_question(config: AskConfig, question: str, results: list[dict[str, Any]]) -> str:
    client = create_chat_client(config)
    response = client.chat.completions.create(
        model=config.chat_deployment,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(question, results)},
        ],
        temperature=0,
    )
    answer = response.choices[0].message.content
    return (answer or "").strip() or UNKNOWN_ANSWER


def retrieve_context(
    config: AskConfig,
    question: str,
) -> list[dict[str, Any]]:
    query_vector = None
    if config.retrieval.mode in {"vector", "hybrid"}:
        query_vector = retrieve.embed_query(config.retrieval, question)

    search_client = retrieve.create_search_client(config.retrieval)
    return list(
        retrieve.search_chunks(
            search_client=search_client,
            question=question,
            config=config.retrieval,
            query_vector=query_vector,
        )
    )


def print_answer(answer: str, results: list[dict[str, Any]]) -> None:
    print()
    print("Answer:")
    print(answer)
    print()
    print("Sources:")
    if not results:
        print("No retrieved sources.")
        return

    for rank, result in enumerate(results, start=1):
        print(source_label(result, rank))


def main() -> int:
    try:
        if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
            parse_args()
            return 0

        retrieve.load_local_dotenv()
        args = parse_args()
        question = retrieve.question_from_args(args)
        config = load_config(args)

        print(f"Using Search endpoint: {config.retrieval.search_endpoint}")
        print(f"Using Search index: {config.retrieval.search_index_name}")
        print(f"Using retrieval mode: {config.retrieval.mode}")
        if config.retrieval.mode in {"vector", "hybrid"}:
            print(f"Using embedding deployment: {config.retrieval.embedding_deployment}")
        print(f"Using chat deployment: {config.chat_deployment}")

        results = retrieve_context(config, question)
        if config.show_context:
            print()
            retrieve.print_results(
                results=results,
                question=question,
                config=config.retrieval,
            )

        if not results:
            print_answer(UNKNOWN_ANSWER, results)
            return 0

        answer = answer_question(config, question, results)
    except retrieve.ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except EOFError:
        print("Configuration error: Question cannot be empty", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Question answering failed: {exc}", file=sys.stderr)
        return 1

    print_answer(answer, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
