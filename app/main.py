"""Small Streamlit UI for asking grounded questions over indexed documents."""

from __future__ import annotations

import os
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import ask  # noqa: E402
import retrieve  # noqa: E402


SAMPLE_QUESTION = "How long can a member borrow a starter repair kit?"
DEFAULT_HISTORY_TURNS = 3
MAX_MEMORY_QUESTION_CHARS = 300
MAX_MEMORY_ANSWER_CHARS = 700
DOC_SUMMARIES = [
    (
        "Workshop overview",
        "Hours, membership options, workshop areas, and boundaries for the fictional Harbor Hill Community Workshop.",
    ),
    (
        "Repair kit lending",
        "What starter repair kits include, how long members can borrow them, and how returns work.",
    ),
    (
        "Rainwater planters",
        "Field notes for three neighborhood planters, including labels, locations, and maintenance actions.",
    ),
    (
        "Safety orientation",
        "Orientation requirements, extra approvals, youth visitor rules, and reset-the-bench cleanup guidance.",
    ),
]

CHAT_SYSTEM_PROMPT = f"""You answer questions using only the provided context chunks.

Rules:
- Use the recent conversation only to understand follow-up questions.
- Do not treat conversation history as source material.
- Use only the retrieved context chunks for factual claims.
- If the context does not contain the answer, say exactly: "{ask.UNKNOWN_ANSWER}"
- Cite supporting context inline with bracketed source numbers, such as [1].
- Keep the answer concise and factual.
"""


@dataclass(frozen=True)
class ChatTurn:
    question: str
    answer: str


def is_streamlit_session() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except ImportError:
        return False

    return get_script_run_ctx() is not None


def load_streamlit():
    try:
        import streamlit as st
    except ImportError:
        print(
            "Missing Streamlit. Install it with: "
            "python -m pip install -r app/requirements.txt"
        )
        print("Then run: python -m streamlit run app/main.py")
        return None

    if not is_streamlit_session():
        print("Run this app with: python -m streamlit run app/main.py")
        return None

    return st


def ask_config(
    *,
    mode: str,
    top_k: int,
    preview_chars: int,
    index_name: str,
    chat_deployment: str,
) -> ask.AskConfig:
    args = SimpleNamespace(
        mode=mode,
        top_k=str(top_k),
        preview_chars=str(preview_chars),
        index_name=index_name,
        chat_deployment=chat_deployment,
        show_context=False,
    )
    return ask.load_config(args)


def result_source(result: dict[str, Any], rank: int) -> str:
    return ask.source_label(result, rank)


def default_mode() -> str:
    mode = os.getenv("RETRIEVAL_MODE", "hybrid").strip().lower()
    if mode in {"hybrid", "keyword", "vector"}:
        return mode
    return "hybrid"


def default_positive_int(name: str, fallback: int) -> int:
    try:
        return retrieve.parse_positive_int(os.getenv(name, str(fallback)), name)
    except retrieve.ConfigError:
        return fallback


def normalize_for_prompt(value: str, max_chars: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_chars:
        return normalized
    return textwrap.shorten(normalized, width=max_chars, placeholder="...")


def format_history(history: list[ChatTurn], history_turns: int) -> str:
    recent_history = history[-history_turns:]
    if not recent_history:
        return "No previous turns."

    lines: list[str] = []
    for index, turn in enumerate(recent_history, start=1):
        question = normalize_for_prompt(turn.question, MAX_MEMORY_QUESTION_CHARS)
        answer = normalize_for_prompt(turn.answer, MAX_MEMORY_ANSWER_CHARS)
        lines.append(f"Turn {index} user: {question}")
        lines.append(f"Turn {index} assistant: {answer}")
    return "\n".join(lines)


def build_retrieval_query(
    question: str,
    history: list[ChatTurn],
    history_turns: int,
) -> str:
    recent_questions = [
        normalize_for_prompt(turn.question, MAX_MEMORY_QUESTION_CHARS)
        for turn in history[-history_turns:]
    ]
    if not recent_questions:
        return question

    previous_questions = "\n".join(f"- {item}" for item in recent_questions)
    return f"""Recent user questions:
{previous_questions}

Current question:
{question}"""


def build_chat_prompt(
    *,
    question: str,
    results: list[dict[str, Any]],
    history: list[ChatTurn],
    history_turns: int,
) -> str:
    context = "\n\n---\n\n".join(
        ask.context_block(result, rank)
        for rank, result in enumerate(results, start=1)
    )
    return f"""Recent conversation:
{format_history(history, history_turns)}

Current question:
{question}

Retrieved context chunks:
{context}

Answer the current question using only the retrieved context chunks."""


def answer_chat_turn(
    *,
    config: ask.AskConfig,
    question: str,
    results: list[dict[str, Any]],
    history: list[ChatTurn],
    history_turns: int,
) -> str:
    client = ask.create_chat_client(config)
    response = client.chat.completions.create(
        model=config.chat_deployment,
        messages=[
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_chat_prompt(
                    question=question,
                    results=results,
                    history=history,
                    history_turns=history_turns,
                ),
            },
        ],
        temperature=0,
    )
    answer = response.choices[0].message.content
    return (answer or "").strip() or ask.UNKNOWN_ANSWER


def display_intro(st: Any) -> None:
    st.title("Harbor Hill Assistant")
    st.caption(
        "Ask questions about the fictional Harbor Hill Community Workshop. "
        "The assistant answers only from retrieved document chunks."
    )

    with st.expander("Documents in this demo", expanded=False):
        for title, description in DOC_SUMMARIES:
            st.markdown(f"**{title}**")
            st.caption(description)


def ensure_session_state(st: Any) -> None:
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("last_results", [])
    st.session_state.setdefault("last_retrieval_query", "")


def display_chunks(st: Any, results: list[dict[str, Any]]) -> None:
    st.subheader(f"Latest retrieved chunks ({len(results)})")

    if not results:
        st.info("No chunks were returned from Azure AI Search.")
        return

    for rank, result in enumerate(results, start=1):
        score = retrieve.format_score(result.get("@search.score"))
        chunk_id = retrieve.metadata_value(result, "id")
        content = retrieve.metadata_value(result, "content", default="")
        title = f"{result_source(result, rank)} | score {score}"

        with st.expander(title, expanded=True):
            st.caption(f"id={chunk_id}")
            if content:
                st.markdown(content)
            else:
                st.caption("This chunk did not include content.")


def display_chat_history(st: Any) -> None:
    history = st.session_state["chat_history"]
    if not history:
        return

    st.subheader("Conversation")
    for turn in history:
        with st.chat_message("user"):
            st.markdown(turn.question)
        with st.chat_message("assistant"):
            st.markdown(turn.answer)


def display_config_error(st: Any, error: Exception) -> None:
    st.error(f"Configuration error: {error}")
    st.info(
        "Check `.env`, confirm the index has been created, and install dependencies with "
        "`python -m pip install -r app/requirements.txt`."
    )


def run_question(
    st: Any,
    question: str,
    config: ask.AskConfig,
    history_turns: int,
) -> None:
    history = st.session_state["chat_history"]
    retrieval_query = build_retrieval_query(question, history, history_turns)

    with st.spinner("Retrieving chunks from Azure AI Search..."):
        results = ask.retrieve_context(config, retrieval_query)

    if not results:
        answer = ask.UNKNOWN_ANSWER
        history.append(ChatTurn(question=question, answer=answer))
        st.session_state["last_results"] = results
        st.session_state["last_retrieval_query"] = retrieval_query
        return

    with st.spinner("Generating grounded answer..."):
        answer = answer_chat_turn(
            config=config,
            question=question,
            results=results,
            history=history,
            history_turns=history_turns,
        )

    history.append(ChatTurn(question=question, answer=answer))
    st.session_state["last_results"] = results
    st.session_state["last_retrieval_query"] = retrieval_query


def run_app(st: Any) -> None:
    st.set_page_config(page_title="Harbor Hill Assistant")
    retrieve.load_local_dotenv()
    ensure_session_state(st)
    display_intro(st)

    with st.sidebar:
        st.header("Retrieval settings")
        modes = ["hybrid", "keyword", "vector"]
        mode = st.selectbox(
            "Mode",
            options=modes,
            index=modes.index(default_mode()),
        )
        top_k = st.number_input(
            "Top K",
            min_value=1,
            max_value=10,
            value=min(
                default_positive_int("RETRIEVAL_TOP_K", retrieve.DEFAULT_TOP_K),
                10,
            ),
            step=1,
        )
        index_name = st.text_input(
            "Search index",
            value=os.getenv("AZURE_SEARCH_INDEX_NAME", ""),
        )
        chat_deployment = st.text_input(
            "Chat deployment",
            value=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", ""),
        )
        history_turns = st.number_input(
            "Memory turns",
            min_value=1,
            max_value=8,
            value=min(
                default_positive_int("CHAT_HISTORY_TURNS", DEFAULT_HISTORY_TURNS),
                8,
            ),
            step=1,
        )
        if st.button("Clear conversation", use_container_width=True):
            st.session_state["chat_history"] = []
            st.session_state["last_results"] = []
            st.session_state["last_retrieval_query"] = ""
            st.rerun()

    display_chat_history(st)

    question = st.chat_input(SAMPLE_QUESTION)
    if question:
        normalized_question = question.strip()

        if not normalized_question:
            st.warning("Enter a question before running retrieval.")
        else:
            try:
                config = ask_config(
                    mode=mode,
                    top_k=top_k,
                    preview_chars=default_positive_int(
                        "RETRIEVAL_PREVIEW_CHARS",
                        retrieve.DEFAULT_PREVIEW_CHARS,
                    ),
                    index_name=index_name,
                    chat_deployment=chat_deployment,
                )
                run_question(
                    st=st,
                    question=normalized_question,
                    config=config,
                    history_turns=history_turns,
                )
                st.rerun()
            except retrieve.ConfigError as exc:
                display_config_error(st, exc)
            except Exception as exc:
                st.error(f"RAG flow failed: {exc}")

    results = st.session_state["last_results"]
    if not st.session_state["chat_history"]:
        return

    st.divider()
    if st.session_state["last_retrieval_query"]:
        with st.expander("Retrieval query sent to Azure AI Search", expanded=False):
            st.code(st.session_state["last_retrieval_query"])
    display_chunks(st, results)


def main() -> None:
    st = load_streamlit()
    if st is None:
        return

    try:
        run_app(st)
    except retrieve.ConfigError as exc:
        display_config_error(st, exc)


if __name__ == "__main__":
    main()
