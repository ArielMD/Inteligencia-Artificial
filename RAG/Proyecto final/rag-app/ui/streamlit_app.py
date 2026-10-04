from __future__ import annotations

import html
import os
from urllib.parse import quote

import httpx
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(
    page_title="RAG — Chat",
    layout="wide",
    initial_sidebar_state="expanded",
)

MODEL_ERROR_UI = "hubo un error con el modelo de ia configurado"


def inject_light_theme() -> None:
    st.markdown(
        """
        <style>
          :root {
            --rag-bg: #ffffff;
            --rag-bg-soft: #f7f7f8;
            --rag-text: #0d0d0d;
            --rag-muted: #6e6e80;
            --rag-border: #d1d5db;
            --rag-accent: #10a37f;
          }
          .stApp {
            background-color: var(--rag-bg);
            color: var(--rag-text);
          }
          [data-testid="stAppViewContainer"],
          [data-testid="stMain"],
          [data-testid="block-container"],
          [data-testid="stBottomBlockContainer"],
          [data-testid="stBottom"] {
            background-color: var(--rag-bg) !important;
          }
          [data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.95) !important;
          }
          [data-testid="stSidebar"] {
            background-color: var(--rag-bg-soft) !important;
            border-right: 1px solid #e5e5e5;
          }
          [data-testid="stSidebar"] label,
          [data-testid="stSidebar"] p,
          [data-testid="stSidebar"] span,
          [data-testid="stSidebar"] h1,
          [data-testid="stSidebar"] h2,
          [data-testid="stSidebar"] h3 {
            color: var(--rag-text) !important;
          }

          /* Inputs: fondo claro y texto visible */
          .stTextInput input,
          .stTextArea textarea,
          [data-testid="stChatInput"] textarea,
          input[type="text"],
          textarea {
            background-color: #ffffff !important;
            color: var(--rag-text) !important;
            -webkit-text-fill-color: var(--rag-text) !important;
            caret-color: var(--rag-text) !important;
            border: 1px solid var(--rag-border) !important;
          }
          div[data-baseweb="select"] > div,
          div[data-baseweb="input"] > div,
          div[data-baseweb="base-input"] {
            background-color: #ffffff !important;
            color: var(--rag-text) !important;
            border-color: var(--rag-border) !important;
          }
          div[data-baseweb="select"] span,
          div[data-baseweb="input"] input {
            color: var(--rag-text) !important;
            -webkit-text-fill-color: var(--rag-text) !important;
          }
          /* Menú desplegable del select (popover) */
          div[data-baseweb="popover"],
          div[data-baseweb="popover"] > div,
          ul[data-baseweb="menu"],
          li[data-baseweb="option"],
          [data-baseweb="menu"] li,
          [role="listbox"],
          [role="option"] {
            background-color: #ffffff !important;
            color: #0d0d0d !important;
          }
          li[data-baseweb="option"]:hover,
          [role="option"]:hover {
            background-color: #f3f4f6 !important;
            color: #0d0d0d !important;
          }
          li[aria-selected="true"][data-baseweb="option"],
          [role="option"][aria-selected="true"] {
            background-color: #e6f4ef !important;
            color: #0d0d0d !important;
          }

          /* Alertas Streamlit (error, warning, info, success) */
          [data-testid="stAlert"],
          [data-testid="stAlertContainer"],
          div[data-testid="stAlert"] > div {
            border-radius: 10px !important;
          }
          [data-testid="stAlert"] p,
          [data-testid="stAlert"] span,
          [data-testid="stAlert"] div,
          [data-testid="stAlertContainer"] p,
          [data-testid="stAlertContainer"] span,
          [data-testid="stAlertContainer"] div {
            color: inherit !important;
          }
          div[data-testid="stAlert"]:has([data-testid="stAlertContentError"]),
          [data-baseweb="notification"][kind="error"] {
            background-color: #fef2f2 !important;
            color: #991b1b !important;
            border: 1px solid #fecaca !important;
          }
          div[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]),
          [data-baseweb="notification"][kind="warning"] {
            background-color: #fffbeb !important;
            color: #92400e !important;
            border: 1px solid #fde68a !important;
          }
          div[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) {
            background-color: #eff6ff !important;
            color: #1e40af !important;
            border: 1px solid #bfdbfe !important;
          }
          div[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) {
            background-color: #ecfdf5 !important;
            color: #065f46 !important;
            border: 1px solid #a7f3d0 !important;
          }

          .rag-alert-error {
            background: #fef2f2;
            color: #991b1b;
            border: 1px solid #fecaca;
            padding: 0.75rem 1rem;
            border-radius: 10px;
            margin: 0.75rem 0;
            font-size: 0.95rem;
            line-height: 1.45;
          }
          .rag-alert-warning {
            background: #fffbeb;
            color: #92400e;
            border: 1px solid #fde68a;
            padding: 0.75rem 1rem;
            border-radius: 10px;
            margin: 0.75rem 0;
            font-size: 0.95rem;
            line-height: 1.45;
          }

          /* Botones secundarios legibles */
          .stButton > button {
            background-color: #ffffff !important;
            color: var(--rag-text) !important;
            border: 1px solid var(--rag-border) !important;
          }
          .stButton > button[kind="primary"],
          .stButton > button[data-testid="baseButton-primary"] {
            background-color: var(--rag-accent) !important;
            color: #ffffff !important;
            border: 1px solid var(--rag-accent) !important;
          }

          .rag-hero {
            text-align: center;
            color: var(--rag-muted);
            font-size: 1.75rem;
            font-weight: 500;
            margin: 2rem 0 1.5rem 0;
          }
          div[data-testid="stChatMessage"] {
            background-color: var(--rag-bg-soft) !important;
            border: 1px solid #ececec;
            border-radius: 12px;
          }
          div[data-testid="stChatMessage"] p,
          div[data-testid="stChatMessage"] li {
            color: var(--rag-text) !important;
          }
          [data-testid="stChatInput"],
          .stChatInputContainer,
          [data-testid="stChatInputContainer"] {
            background-color: var(--rag-bg) !important;
            border-top: 1px solid #ececec;
          }
          [data-testid="stChatInput"] > div {
            background-color: #ffffff !important;
            border: 1px solid var(--rag-border) !important;
            border-radius: 24px !important;
          }

          /* Tabs estilo pestaña (sin apariencia de botón) */
          .stTabs [data-baseweb="tab-list"] {
            gap: 1.5rem;
            background-color: transparent !important;
            border-bottom: 1px solid #e5e7eb !important;
            min-height: 2.75rem;
          }
          .stTabs [data-baseweb="tab"] {
            height: auto !important;
            min-height: 2.5rem !important;
            padding: 0.5rem 0.25rem 0.75rem !important;
            line-height: 1.5 !important;
            background-color: transparent !important;
            color: var(--rag-muted) !important;
            border: none !important;
            border-radius: 0 !important;
            border-bottom: 2px solid transparent !important;
            box-shadow: none !important;
          }
          .stTabs [data-baseweb="tab"] p,
          .stTabs [data-baseweb="tab"] div,
          .stTabs button p {
            color: inherit !important;
            font-size: 0.95rem !important;
            line-height: 1.5 !important;
            margin: 0 !important;
            padding: 0 !important;
          }
          .stTabs [aria-selected="true"] {
            background-color: transparent !important;
            color: var(--rag-text) !important;
            border-bottom: 2px solid var(--rag-accent) !important;
            font-weight: 600;
          }
          .stTabs [data-baseweb="tab-panel"] {
            padding-top: 1.25rem;
          }
          .chat-row-active {
            background: #ececec;
            border-radius: 8px;
            padding: 0.15rem 0.35rem;
          }
          .stTabs [data-baseweb="tab-highlight"] {
            background-color: var(--rag-accent) !important;
          }

          /* Stepper numérico */
          [data-testid="stNumberInput"] {
            background: #f7f7f8;
            border: 1px solid var(--rag-border);
            border-radius: 10px;
            padding: 0.35rem 0.5rem;
          }
          [data-testid="stNumberInput"] input {
            background-color: #ffffff !important;
            color: var(--rag-text) !important;
            font-weight: 600;
            font-size: 1.1rem !important;
            text-align: center;
          }
          [data-testid="stNumberInput"] button {
            background-color: #ffffff !important;
            color: var(--rag-text) !important;
            border: 1px solid var(--rag-border) !important;
          }

          /* File uploader claro (Indexar / Gestión) */
          [data-testid="stFileUploader"],
          [data-testid="stFileUploader"] > section,
          [data-testid="stFileUploadDropzone"],
          [data-testid="stFileUploaderDropzoneInstructions"] {
            background-color: #f7f7f8 !important;
            color: var(--rag-text) !important;
          }
          [data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"] {
            border: 1px dashed #c5c5d2 !important;
            border-radius: 12px !important;
          }
          [data-testid="stFileUploader"] span,
          [data-testid="stFileUploader"] small,
          [data-testid="stFileUploader"] label,
          [data-testid="stFileUploader"] p {
            color: var(--rag-muted) !important;
          }
          [data-testid="stFileUploader"] button {
            background-color: #ffffff !important;
            color: var(--rag-text) !important;
            border: 1px solid var(--rag-border) !important;
          }

          /* Listados de archivos (sin bloque oscuro) */
          .rag-file-list {
            background: #f7f7f8;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 0.75rem 1rem;
            color: #0d0d0d;
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: 0.9rem;
          }
          pre, code, [data-testid="stCode"] {
            background-color: #f7f7f8 !important;
            color: #0d0d0d !important;
            border: 1px solid #e5e7eb !important;
          }

          /* Historial: una sola línea + botón eliminar compacto */
          [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
            align-items: center !important;
            gap: 0.25rem !important;
          }
          [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton > button {
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            line-height: 1.25 !important;
            min-height: 2.25rem !important;
            max-height: 2.25rem !important;
          }
          [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="column"]:last-child .stButton > button {
            min-width: 2.25rem !important;
            padding: 0 !important;
            font-size: 1.15rem !important;
            font-weight: 400 !important;
            color: var(--rag-muted) !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_error_banner(message: str) -> None:
    st.markdown(
        f'<div class="rag-alert-error">{html.escape(message)}</div>',
        unsafe_allow_html=True,
    )


def show_warning_banner(message: str) -> None:
    st.markdown(
        f'<div class="rag-alert-warning">{html.escape(message)}</div>',
        unsafe_allow_html=True,
    )


def show_api_error(message: str | None) -> None:
    if not message:
        return
    lower = message.lower()
    if MODEL_ERROR_UI in lower or "internal server error" in lower:
        show_warning_banner(
            "No se pudo completar la operación: hubo un error con el modelo configurado. "
            "Revisa la configuración e inténtalo de nuevo."
        )
        return
    show_error_banner(message)


def api_get(path: str) -> tuple[dict | list | None, str | None]:
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.get(f"{API_BASE}{path}")
            if r.status_code >= 400:
                return None, r.text
            return r.json(), None
    except httpx.RequestError as exc:
        return None, str(exc)


def api_post_json(path: str, payload: dict) -> tuple[dict | None, str | None]:
    try:
        with httpx.Client(timeout=120.0) as client:
            r = client.post(f"{API_BASE}{path}", json=payload)
            if r.status_code >= 400:
                try:
                    detail = r.json().get("detail", r.text)
                except Exception:
                    detail = r.text
                return None, str(detail)
            return r.json(), None
    except httpx.RequestError as exc:
        return None, str(exc)


def api_post_ingest_files(files: list[tuple[str, bytes]]) -> tuple[dict | None, str | None]:
    try:
        multipart = [("files", (name, data)) for name, data in files]
        with httpx.Client(timeout=300.0) as client:
            r = client.post(f"{API_BASE}/ingest", files=multipart)
            if r.status_code >= 400:
                try:
                    detail = r.json().get("detail", r.text)
                except Exception:
                    detail = r.text
                return None, str(detail)
            return r.json(), None
    except httpx.RequestError as exc:
        return None, str(exc)


def api_post_ingest_data_dir() -> tuple[dict | None, str | None]:
    try:
        with httpx.Client(timeout=300.0) as client:
            r = client.post(f"{API_BASE}/ingest", data={"index_data_dir": "true"})
            if r.status_code >= 400:
                try:
                    detail = r.json().get("detail", r.text)
                except Exception:
                    detail = r.text
                return None, str(detail)
            return r.json(), None
    except httpx.RequestError as exc:
        return None, str(exc)


def api_delete(path: str) -> tuple[dict | None, str | None]:
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.delete(f"{API_BASE}{path}")
            if r.status_code >= 400:
                try:
                    detail = r.json().get("detail", r.text)
                except Exception:
                    detail = r.text
                return None, str(detail)
            return r.json(), None
    except httpx.RequestError as exc:
        return None, str(exc)


def api_delete_source(source: str) -> tuple[dict | None, str | None]:
    return api_delete(f"/sources/{quote(source, safe='')}")


def api_reindex(source: str, filename: str, data: bytes) -> tuple[dict | None, str | None]:
    try:
        with httpx.Client(timeout=300.0) as client:
            r = client.post(
                f"{API_BASE}/sources/{quote(source, safe='')}/reindex",
                files={"file": (filename, data)},
            )
            if r.status_code >= 400:
                try:
                    detail = r.json().get("detail", r.text)
                except Exception:
                    detail = r.text
                return None, str(detail)
            return r.json(), None
    except httpx.RequestError as exc:
        return None, str(exc)


def render_citations(citations: list[dict]) -> None:
    if not citations:
        return
    st.markdown("**Fuentes recuperadas**")
    for c in citations:
        page = c.get("page")
        page_txt = f" · pág. {page}" if page is not None else ""
        block = c.get("block_type") or "prose"
        score = c.get("score", 0)
        title = f"[{c.get('index')}] {c.get('source')}{page_txt} · {block} · score {score:.3f}"
        snippet = (c.get("text") or "")[:1200]
        with st.expander(title, expanded=False):
            st.markdown(f"```\n{snippet}\n```")


def render_usage(turn: dict) -> None:
    usage = turn.get("usage") or {}
    prompt = int(usage.get("prompt_tokens") or 0)
    out = int(usage.get("candidates_tokens") or 0)
    st.markdown(
        f'<span style="font-size:0.75rem;color:#6e6e80;">'
        f"Tokens: {prompt} entrada · {out} salida"
        f"</span>",
        unsafe_allow_html=True,
    )


def sidebar_chat_title(title: str, max_len: int = 32) -> str:
    text = " ".join((title or "Sin título").split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def turns_to_messages(turns: list[dict]) -> list[dict]:
    messages: list[dict] = []
    for turn in turns:
        messages.append({"role": "user", "content": turn.get("question", "")})
        messages.append(
            {
                "role": "assistant",
                "content": turn.get("answer", ""),
                "citations": turn.get("citations") or [],
                "abstained": turn.get("abstained", False),
                "usage": turn.get("usage") or {},
                "cost_usd": turn.get("cost_usd", 0.0),
                "model": turn.get("model", ""),
                "embedding_calls": turn.get("embedding_calls", 0),
                "error": turn.get("error", False),
            }
        )
    return messages


inject_light_theme()

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

health = None
health_err = None

with st.sidebar:
    st.markdown("### RAG MIA")

    st.markdown("**Estado del servidor**")
    health, health_err = api_get("/health")
    if health_err:
        show_error_banner("Servidor no disponible. Levanta la API (puerto 8000).")
    elif health:
        st.success("Servidor en línea.")
        chunks = health.get("chunk_count", 0)
        st.info(f"{chunks} fragmento(s) indexado(s) en el corpus.")

    st.divider()
    if st.button("＋ Nueva conversación", use_container_width=True):
        st.session_state.active_chat_id = None
        st.session_state.pending_question = None
        st.rerun()

    st.markdown("**Recientes**")
    chats, chats_err = api_get("/chats")
    if chats_err:
        st.caption("No se pudieron cargar las conversaciones.")
    chat_items = [c for c in (chats or []) if (c.get("turn_count") or 0) > 0]
    if not chat_items:
        st.caption("Aún no hay conversaciones guardadas.")
    for item in chat_items:
        chat_id = item["id"]
        title = sidebar_chat_title(item.get("title") or "Sin título")
        is_active = chat_id == st.session_state.active_chat_id
        row = st.container()
        with row:
            col_title, col_menu = st.columns([6, 1], gap="small")
            with col_title:
                if st.button(
                    title,
                    key=f"open_{chat_id}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    help=item.get("title") or "Sin título",
                ):
                    st.session_state.active_chat_id = chat_id
                    st.session_state.pending_question = None
                    st.rerun()
            with col_menu:
                if st.button(
                    "×",
                    key=f"del_chat_{chat_id}",
                    help="Eliminar",
                    use_container_width=True,
                ):
                    _, del_err = api_delete(f"/chats/{chat_id}")
                    if del_err:
                        show_api_error(del_err)
                    else:
                        if st.session_state.active_chat_id == chat_id:
                            st.session_state.active_chat_id = None
                        st.rerun()

    st.divider()
    st.markdown("**Configuración de recuperación (RAG)**")
    sources, _ = api_get("/sources")
    source_names = ["Todas las fuentes"] + [s["source"] for s in (sources or [])]
    selected = st.selectbox("Filtrar por documento", source_names)
    st.markdown("**Fragmentos de contexto**")
    top_k = st.number_input(
        "Fragmentos de contexto",
        min_value=1,
        max_value=10,
        value=4,
        step=1,
        label_visibility="collapsed",
    )
    st.caption("Rango 1–10 · incremento por paso")

# —— Vista principal: chat primero ——
tab_chat, tab_index, tab_manage = st.tabs(["Chat", "Indexar", "Gestión"])

active_chat = None
if st.session_state.active_chat_id:
    active_chat, _ = api_get(f"/chats/{st.session_state.active_chat_id}")
messages = turns_to_messages((active_chat or {}).get("turns") or [])

with tab_chat:
    pending = (st.session_state.pending_question or "").strip()
    if not messages and not pending:
        st.markdown(
            '<p class="rag-hero">¿Qué quieres saber de tus documentos?</p>',
            unsafe_allow_html=True,
        )

    if health and health.get("chunk_count", 0) == 0:
        st.info("Aún no hay documentos indexados. Usa la pestaña **Indexar**.")

    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("abstained"):
                st.caption("Respuesta con abstención: no hubo evidencia suficiente en el corpus.")
            if msg.get("citations"):
                render_citations(msg["citations"])
            if msg["role"] == "assistant" and msg.get("usage"):
                render_usage(msg)

    wait_box = None
    if pending:
        with st.chat_message("user"):
            st.markdown(pending)
        with st.chat_message("assistant"):
            wait_box = st.empty()
            wait_box.markdown("Buscando evidencia…")

    question = st.chat_input("Pregunta a RAG MIA", disabled=bool(pending))
    if question and question.strip() and not pending:
        if health_err:
            show_error_banner("API no disponible.")
        elif health and health.get("chunk_count", 0) == 0:
            show_warning_banner("Indexa documentos antes de consultar.")
        else:
            st.session_state.pending_question = question.strip()
            st.rerun()

    if pending and wait_box is not None:
        if health_err:
            wait_box.markdown("API no disponible.")
            st.session_state.pending_question = None
        elif health and health.get("chunk_count", 0) == 0:
            wait_box.markdown("Indexa documentos antes de consultar.")
            st.session_state.pending_question = None
        else:
            body = {"question": pending, "top_k": int(top_k)}
            if selected != "Todas las fuentes":
                body["source"] = selected
            if st.session_state.active_chat_id:
                body["chat_id"] = st.session_state.active_chat_id
            result, q_err = api_post_json("/query", body)
            if q_err:
                wait_box.markdown(q_err)
                st.session_state.pending_question = None
            elif result:
                st.session_state.active_chat_id = result.get("chat_id")
                st.session_state.pending_question = None
                st.rerun()

with tab_index:
    st.markdown("#### Subir archivos")
    uploads = st.file_uploader(
        "Arrastra archivos aquí (PDF, TXT, MD, HTML, JSON)",
        accept_multiple_files=True,
        type=["pdf", "txt", "md", "html", "htm", "json"],
    )
    if st.button("Indexar archivos", type="primary"):
        if not uploads:
            st.warning("Selecciona al menos un archivo.")
        elif health_err:
            st.error("API no disponible.")
        else:
            payload = [(u.name, u.getvalue()) for u in uploads]
            with st.spinner("Indexando…"):
                result, ingest_err = api_post_ingest_files(payload)
            if ingest_err:
                show_api_error(ingest_err)
            elif result:
                st.success(
                    f"Listo: {result.get('documents_indexed')} documento(s), "
                    f"{result.get('chunks_indexed')} chunk(s)."
                )

    st.divider()
    st.markdown("#### Carpeta local `data/`")
    data_list, _ = api_get("/data/list")
    file_count = (data_list or {}).get("count", 0)
    if file_count == 0:
        st.info("La carpeta `data/` está vacía. Copia tus archivos ahí o súbelos arriba.")
    else:
        files = (data_list or {}).get("files") or []
        st.write(f"**{file_count}** archivo(s) detectado(s):")
        file_lines = "<br>".join(f"• {f}" for f in files)
        st.markdown(
            f'<div class="rag-file-list">{file_lines}</div>',
            unsafe_allow_html=True,
        )

    if st.button("Indexar todo en data/"):
        if health_err:
            st.error("API no disponible.")
        elif file_count == 0:
            st.warning("No hay archivos en data/.")
        else:
            with st.spinner("Indexando…"):
                result, ingest_err = api_post_ingest_data_dir()
            if ingest_err:
                show_api_error(ingest_err)
            elif result:
                st.success(
                    f"Listo: {result.get('documents_indexed')} documento(s), "
                    f"{result.get('chunks_indexed')} chunk(s)."
                )

with tab_manage:
    st.markdown("#### Documentos en el índice")
    sources, _ = api_get("/sources")
    if not sources:
        st.info("No hay fuentes indexadas.")
    for item in sources or []:
        src = item["source"]
        with st.container(border=True):
            st.write(f"**{src}** — {item.get('chunk_count', 0)} chunks")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Eliminar", key=f"del_{src}", use_container_width=True):
                    _, del_err = api_delete_source(src)
                    if del_err:
                        st.error(del_err)
                    else:
                        st.success(f"Eliminado: {src}")
                        st.rerun()
            with col2:
                new_file = st.file_uploader(
                    "Archivo de reemplazo",
                    key=f"re_{src}",
                    type=["pdf", "txt", "md", "html", "htm", "json"],
                )
                if new_file and st.button("Reindexar", key=f"rebtn_{src}", use_container_width=True):
                    with st.spinner("Reindexando…"):
                        res, r_err = api_reindex(src, new_file.name, new_file.getvalue())
                    if r_err:
                        show_api_error(r_err)
                    elif res:
                        st.success(f"Chunks: {res.get('chunks_indexed')}")
                        st.rerun()
