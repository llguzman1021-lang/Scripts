"""
app.py — Scripts Dashboard (entry point)
=========================================
Run with:  streamlit run app.py

UI architecture
---------------
  Sidebar  — stats + mode toggle
  Tab 1    — Uso Rápido   (search, filter, copy-to-clipboard)
  Tab 2    — Panel de Control  (full CRUD: categories + scripts)

Session-state keys
------------------
  data               : dict   — live copy of the JSON data
  filter_cat         : str    — active category filter ID (__all__ = no filter)
  confirm_del_cat    : str|None  — cat_id pending delete confirmation
  confirm_del_script : tuple|None — (cat_id, scr_id) pending deletion
  editing_cat        : str|None  — cat_id being edited inline
  editing_script     : tuple|None — (cat_id, scr_id) being edited inline
  adding_cat         : bool  — show "new category" form
  adding_script_to   : str|None — cat_id for "new script" form
"""

import copy
import streamlit as st

from config import APP_ICON, APP_NAME, APP_VERSION, CATEGORY_COLORS, CATEGORY_ICONS
from data_manager import JSONDataManager

# ─── Page config (must be the very first Streamlit call) ──────────────────────
st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
# All selectors use the "sd-" prefix to avoid Streamlit CSS collisions.
st.markdown(
    """
<style>
/* ── Global ─────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0d1117;
    border-right: 1px solid #21262d;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] label { color: #8b949e; }

/* ── Script card (user mode) ─────────────────────────── */
.sd-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 16px 18px 12px;
    margin-bottom: 14px;
    transition: border-color 0.18s, box-shadow 0.18s;
}
.sd-card:hover {
    border-color: #e05252;
    box-shadow: 0 0 0 1px #e05252;
}
.sd-card-title {
    font-size: 15px;
    font-weight: 600;
    color: #e6edf3;
    margin: 0 0 6px;
    line-height: 1.4;
}
.sd-card-preview {
    font-size: 13px;
    color: #8b949e;
    margin: 0 0 10px;
    line-height: 1.6;
}
.sd-card-footer {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}

/* ── Tags ────────────────────────────────────────────── */
.sd-tag {
    display: inline-block;
    background: #1c2b1e;
    color: #7ee787;
    border: 1px solid #2ea043;
    border-radius: 12px;
    padding: 1px 9px;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.02em;
}

/* ── Category heading ────────────────────────────────── */
.sd-cat-header {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #8b949e;
    padding: 4px 0;
    border-bottom: 1px solid #21262d;
    margin: 22px 0 14px;
}

/* ── Page section title ──────────────────────────────── */
.sd-page-title {
    font-size: 24px;
    font-weight: 700;
    color: #e6edf3;
    margin: 0 0 2px;
}
.sd-page-sub {
    font-size: 13px;
    color: #8b949e;
    margin: 0 0 22px;
}

/* ── Sidebar stat pill ───────────────────────────────── */
.sd-stat {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: center;
}
.sd-stat-num   { font-size: 26px; font-weight: 700; color: #e6edf3; line-height: 1.1; }
.sd-stat-label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.08em; }

/* ── Admin list item ─────────────────────────────────── */
.sd-admin-item {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 8px;
}

/* ── Search result badge ─────────────────────────────── */
.sd-result-badge {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    color: #4f85e0;
    background: #1c2434;
    border: 1px solid #4f85e0;
    border-radius: 4px;
    padding: 1px 7px;
    margin-bottom: 6px;
}

/* ── Tabs ────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    border-bottom: 1px solid #21262d;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #8b949e;
    font-size: 14px;
    padding: 8px 18px;
    border-radius: 6px 6px 0 0;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    color: #e6edf3 !important;
    border-bottom: 2px solid #e05252 !important;
    background: transparent !important;
}

/* ── Streamlit button overrides ──────────────────────── */
.stButton > button {
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    transition: opacity 0.15s;
}

/* ── Responsive ──────────────────────────────────────── */
@media (max-width: 768px) {
    .sd-card     { padding: 12px 14px 10px; }
    .sd-page-title { font-size: 20px; }
}
</style>
""",
    unsafe_allow_html=True,
)

# ─── Manager singleton ────────────────────────────────────────────────────────
_manager = JSONDataManager()


# ─── Session-state bootstrap ──────────────────────────────────────────────────
def _init() -> None:
    """Called once per session (skipped on subsequent reruns)."""
    defaults: dict = {
        "data":               _manager.load(),
        "filter_cat":         "__all__",
        "confirm_del_cat":    None,
        "confirm_del_script": None,
        "editing_cat":        None,
        "editing_script":     None,
        "adding_cat":         False,
        "adding_script_to":   None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init()


# ─── Shared helpers ───────────────────────────────────────────────────────────

def _save(new_data: dict) -> bool:
    """Persist data and refresh session state."""
    ok = _manager.save(new_data)
    if ok:
        st.session_state.data = new_data
    return ok


def _dcopy() -> dict:
    """Return a deep copy of current session data for mutation."""
    return copy.deepcopy(st.session_state.data)


def _tags_html(tags: list) -> str:
    return "".join(f'<span class="sd-tag">{t}</span>' for t in tags)


def _script_card(script: dict, key_prefix: str, show_cat_badge: bool = False) -> None:
    """
    Render a single script card with preview and expandable full-text copy block.
    Uses st.code(language=None) which ships with a built-in copy icon.
    """
    preview = script["content"][:130] + ("…" if len(script["content"]) > 130 else "")
    tags_block = _tags_html(script.get("tags", []))
    cat_badge  = (
        f'<span class="sd-result-badge">{script.get("cat_icon","")}&nbsp;'
        f'{script.get("cat_name","")}</span><br>'
        if show_cat_badge else ""
    )

    st.markdown(
        f"""
        <div class="sd-card">
            {cat_badge}
            <div class="sd-card-title">{script["title"]}</div>
            <div class="sd-card-preview">{preview}</div>
            <div class="sd-card-footer">{tags_block}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("📋 Ver texto completo y copiar"):
        st.code(script["content"], language=None)


# ═════════════════════════════════════════════════════════════════════════════
# USER MODE
# ═════════════════════════════════════════════════════════════════════════════

def _render_user_mode() -> None:
    data       = st.session_state.data
    categories = _manager.get_categories(data)

    st.markdown('<div class="sd-page-title">📋 Uso Rápido</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sd-page-sub">Busca, consulta y copia tus scripts al instante.</div>',
        unsafe_allow_html=True,
    )

    # ── Search ─────────────────────────────────────────────────────────────
    query = st.text_input(
        "Buscar",
        placeholder="🔍  Escribe título, contenido o etiqueta…",
        key="user_search",
        label_visibility="collapsed",
    )

    # ── Category filter ────────────────────────────────────────────────────
    cat_map   = {"__all__": "🗂️ Todas las categorías"}
    cat_map.update({c["id"]: f"{c['icon']}  {c['name']}" for c in categories})
    selected_filter = st.selectbox(
        "Filtrar categoría",
        options=list(cat_map.keys()),
        format_func=lambda k: cat_map[k],
        key="user_cat_filter",
        label_visibility="collapsed",
    )
    st.session_state.filter_cat = selected_filter

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Search results ─────────────────────────────────────────────────────
    if query.strip():
        results = _manager.search_scripts(data, query)
        if not results:
            st.info("Sin resultados. Intenta con otro término.")
        else:
            st.caption(f"**{len(results)}** resultado(s) encontrado(s)")
            cols = st.columns(2)
            for idx, scr in enumerate(results):
                with cols[idx % 2]:
                    _script_card(scr, f"sr_{scr['id']}", show_cat_badge=True)
        return

    # ── Browse by category ─────────────────────────────────────────────────
    active = (
        categories
        if selected_filter == "__all__"
        else [c for c in categories if c["id"] == selected_filter]
    )

    if not active:
        st.info("No hay categorías creadas. Ve al **Panel de Control** para agregar una.")
        return

    for cat in active:
        scripts = cat.get("scripts", [])
        count   = f"({len(scripts)} script{'s' if len(scripts) != 1 else ''})"
        st.markdown(
            f'<div class="sd-cat-header">{cat["icon"]}  {cat["name"]}  {count}</div>',
            unsafe_allow_html=True,
        )
        if not scripts:
            st.caption("Esta categoría no tiene scripts aún.")
            continue

        cols = st.columns(2)
        for idx, scr in enumerate(scripts):
            with cols[idx % 2]:
                _script_card(scr, f"{cat['id']}_{scr['id']}")


# ═════════════════════════════════════════════════════════════════════════════
# ADMIN MODE — FORMS
# ═════════════════════════════════════════════════════════════════════════════

def _form_add_category() -> None:
    """Inline form: create a new category."""
    st.markdown("**Nueva categoría**")
    with st.form("form_add_cat", clear_on_submit=True):
        name  = st.text_input("Nombre *", placeholder="ej. Procedimientos")
        icon  = st.selectbox("Ícono", CATEGORY_ICONS)
        color = st.selectbox("Color de acento", CATEGORY_COLORS)
        col_s, col_c = st.columns(2)
        submitted = col_s.form_submit_button("✓ Crear", type="primary", use_container_width=True)
        cancelled = col_c.form_submit_button("✗ Cancelar", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("El nombre es obligatorio.")
        else:
            try:
                new_data, _ = _manager.add_category(_dcopy(), name, icon, color)
                if _save(new_data):
                    st.session_state.adding_cat = False
                    st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    if cancelled:
        st.session_state.adding_cat = False
        st.rerun()


def _form_edit_category(cat: dict) -> None:
    """Inline form: update an existing category."""
    st.markdown(f"**Editando: {cat['name']}**")
    icon_idx  = CATEGORY_ICONS.index(cat["icon"]) if cat["icon"] in CATEGORY_ICONS else 0
    color_idx = CATEGORY_COLORS.index(cat["color"]) if cat["color"] in CATEGORY_COLORS else 0

    with st.form(f"form_edit_cat_{cat['id']}", clear_on_submit=False):
        name  = st.text_input("Nombre *", value=cat["name"])
        icon  = st.selectbox("Ícono", CATEGORY_ICONS, index=icon_idx)
        color = st.selectbox("Color de acento", CATEGORY_COLORS, index=color_idx)
        col_s, col_c = st.columns(2)
        submitted = col_s.form_submit_button("✓ Guardar", type="primary", use_container_width=True)
        cancelled = col_c.form_submit_button("✗ Cancelar", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("El nombre es obligatorio.")
        else:
            try:
                new_data = _manager.update_category(_dcopy(), cat["id"], name, icon, color)
                if _save(new_data):
                    st.session_state.editing_cat = None
                    st.rerun()
            except (ValueError, KeyError) as exc:
                st.error(str(exc))

    if cancelled:
        st.session_state.editing_cat = None
        st.rerun()


def _form_add_script(cat_id: str) -> None:
    """Inline form: create a new script in cat_id."""
    st.markdown("**Nuevo script**")
    with st.form("form_add_scr", clear_on_submit=True):
        title    = st.text_input("Título *", placeholder="ej. Respuesta inicial")
        content  = st.text_area("Contenido *", height=130,
                                placeholder="Escribe la respuesta aquí…")
        tags_raw = st.text_input("Etiquetas",
                                 placeholder="info, inicial, urgente  (separadas por coma)")
        col_s, col_c = st.columns(2)
        submitted = col_s.form_submit_button("✓ Guardar", type="primary", use_container_width=True)
        cancelled = col_c.form_submit_button("✗ Cancelar", use_container_width=True)

    if submitted:
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        if not title.strip():
            st.error("El título es obligatorio.")
        elif not content.strip():
            st.error("El contenido es obligatorio.")
        else:
            try:
                new_data, _ = _manager.add_script(_dcopy(), cat_id, title, content, tags)
                if _save(new_data):
                    st.session_state.adding_script_to = None
                    st.rerun()
            except (ValueError, KeyError) as exc:
                st.error(str(exc))

    if cancelled:
        st.session_state.adding_script_to = None
        st.rerun()


def _form_edit_script(cat_id: str, script: dict) -> None:
    """Inline form: update an existing script."""
    st.markdown(f"**Editando: {script['title']}**")
    tags_str = ", ".join(script.get("tags", []))

    with st.form(f"form_edit_scr_{script['id']}", clear_on_submit=False):
        title    = st.text_input("Título *", value=script["title"])
        content  = st.text_area("Contenido *", value=script["content"], height=150)
        tags_raw = st.text_input("Etiquetas", value=tags_str,
                                 placeholder="info, inicial, urgente")
        col_s, col_c = st.columns(2)
        submitted = col_s.form_submit_button("✓ Guardar", type="primary", use_container_width=True)
        cancelled = col_c.form_submit_button("✗ Cancelar", use_container_width=True)

    if submitted:
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        if not title.strip():
            st.error("El título es obligatorio.")
        elif not content.strip():
            st.error("El contenido es obligatorio.")
        else:
            try:
                new_data = _manager.update_script(
                    _dcopy(), cat_id, script["id"], title, content, tags
                )
                if _save(new_data):
                    st.session_state.editing_script = None
                    st.rerun()
            except (ValueError, KeyError) as exc:
                st.error(str(exc))

    if cancelled:
        st.session_state.editing_script = None
        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# ADMIN MODE — MAIN PANELS
# ═════════════════════════════════════════════════════════════════════════════

def _panel_categories(data: dict) -> None:
    """Left panel: list + CRUD for categories."""
    st.markdown("#### 🗂️ Categorías")
    categories = _manager.get_categories(data)

    for cat in categories:
        is_editing = st.session_state.editing_cat == cat["id"]

        if is_editing:
            _form_edit_category(cat)
            st.divider()
            continue

        # ── Category row ─────────────────────────────────────────────────
        col_a, col_b, col_c = st.columns([5, 1, 1])
        col_a.markdown(f"**{cat['icon']}  {cat['name']}**")
        col_a.caption(f"{len(cat['scripts'])} script(s)")

        if col_b.button("✏️", key=f"btn_edit_cat_{cat['id']}", help="Editar categoría"):
            st.session_state.editing_cat = cat["id"]
            st.session_state.adding_cat  = False
            st.rerun()

        # ── Delete with inline confirmation ──────────────────────────────
        if st.session_state.confirm_del_cat == cat["id"]:
            st.warning(
                f"¿Eliminar **{cat['name']}** y sus {len(cat['scripts'])} script(s)?",
                icon="⚠️",
            )
            dc1, dc2 = st.columns(2)
            if dc1.button("Sí, eliminar", key=f"yes_del_cat_{cat['id']}", type="primary",
                          use_container_width=True):
                try:
                    new_data = _manager.delete_category(_dcopy(), cat["id"])
                    if _save(new_data):
                        st.session_state.confirm_del_cat = None
                        st.rerun()
                except KeyError as exc:
                    st.error(str(exc))
            if dc2.button("Cancelar", key=f"no_del_cat_{cat['id']}", use_container_width=True):
                st.session_state.confirm_del_cat = None
                st.rerun()
        else:
            if col_c.button("🗑️", key=f"btn_del_cat_{cat['id']}", help="Eliminar categoría"):
                st.session_state.confirm_del_cat = cat["id"]
                st.rerun()

        st.divider()

    # ── Add category ──────────────────────────────────────────────────────
    if st.session_state.adding_cat:
        _form_add_category()
    else:
        if st.button("➕  Nueva categoría", use_container_width=True):
            st.session_state.adding_cat   = True
            st.session_state.editing_cat  = None
            st.rerun()


def _panel_scripts(data: dict) -> None:
    """Right panel: category selector + CRUD for scripts."""
    st.markdown("#### 📝 Scripts")
    categories = _manager.get_categories(data)

    if not categories:
        st.info("Crea al menos una categoría en el panel izquierdo.")
        return

    # ── Category selector ────────────────────────────────────────────────
    cat_map   = {c["id"]: f"{c['icon']}  {c['name']}" for c in categories}
    sel_cat_id = st.selectbox(
        "Categoría activa:",
        options=list(cat_map.keys()),
        format_func=lambda k: cat_map[k],
        key="admin_cat_sel",
    )
    sel_cat = next((c for c in categories if c["id"] == sel_cat_id), None)
    if sel_cat is None:
        return

    scripts = sel_cat.get("scripts", [])
    st.caption(f"{len(scripts)} script(s) en esta categoría")

    # ── Add script ───────────────────────────────────────────────────────
    if st.session_state.adding_script_to == sel_cat_id:
        st.divider()
        _form_add_script(sel_cat_id)
        st.divider()
    else:
        if st.button("➕  Agregar script", key="btn_add_scr", use_container_width=True):
            st.session_state.adding_script_to = sel_cat_id
            st.session_state.editing_script   = None
            st.rerun()

    if not scripts:
        st.info("Esta categoría no tiene scripts. Agrega uno con el botón de arriba.")
        return

    st.divider()

    # ── Script list ──────────────────────────────────────────────────────
    for scr in scripts:
        is_editing = st.session_state.editing_script == (sel_cat_id, scr["id"])

        if is_editing:
            _form_edit_script(sel_cat_id, scr)
            st.divider()
            continue

        with st.expander(f"📝  {scr['title']}", expanded=False):
            if scr.get("tags"):
                st.markdown("  ".join([f"`{t}`" for t in scr["tags"]]))
            st.code(scr["content"], language=None)
            st.caption(f"Actualizado: {scr.get('updated_at', '—')[:10]}")

            col_e, col_d = st.columns(2)

            if col_e.button("✏️  Editar", key=f"btn_edit_scr_{scr['id']}", use_container_width=True):
                st.session_state.editing_script   = (sel_cat_id, scr["id"])
                st.session_state.adding_script_to = None
                st.rerun()

            del_key = (sel_cat_id, scr["id"])
            if st.session_state.confirm_del_script == del_key:
                st.warning("¿Eliminar este script permanentemente?", icon="⚠️")
                dc1, dc2 = st.columns(2)
                if dc1.button("Sí, eliminar", key=f"yes_del_scr_{scr['id']}", type="primary",
                              use_container_width=True):
                    try:
                        new_data = _manager.delete_script(_dcopy(), sel_cat_id, scr["id"])
                        if _save(new_data):
                            st.session_state.confirm_del_script = None
                            st.rerun()
                    except KeyError as exc:
                        st.error(str(exc))
                if dc2.button("Cancelar", key=f"no_del_scr_{scr['id']}", use_container_width=True):
                    st.session_state.confirm_del_script = None
                    st.rerun()
            else:
                if col_d.button("🗑️  Eliminar", key=f"btn_del_scr_{scr['id']}", use_container_width=True):
                    st.session_state.confirm_del_script = (sel_cat_id, scr["id"])
                    st.rerun()


def _render_admin_mode() -> None:
    data = st.session_state.data

    st.markdown('<div class="sd-page-title">⚙️ Panel de Control</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sd-page-sub">Gestiona categorías y scripts con control total.</div>',
        unsafe_allow_html=True,
    )

    col_left, col_sep, col_right = st.columns([2.2, 0.05, 4])

    with col_left:
        _panel_categories(data)

    with col_sep:
        # Visual divider via CSS
        st.markdown(
            "<div style='height:100%;border-left:1px solid #21262d;margin:0 auto;'></div>",
            unsafe_allow_html=True,
        )

    with col_right:
        _panel_scripts(data)


# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(f"## {APP_ICON} {APP_NAME}")
    st.caption(f"v{APP_VERSION}")
    st.divider()

    stats = _manager.get_stats(st.session_state.data)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f'<div class="sd-stat">'
            f'<div class="sd-stat-num">{stats["total_categories"]}</div>'
            f'<div class="sd-stat-label">Categorías</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="sd-stat">'
            f'<div class="sd-stat-num">{stats["total_scripts"]}</div>'
            f'<div class="sd-stat-label">Scripts</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    if stats["breakdown"]:
        st.caption("📊 Distribución:")
        for item in stats["breakdown"]:
            st.markdown(f"{item['icon']} **{item['name']}** — {item['count']}")

    st.divider()
    st.caption(f"💾 Archivo: `{_manager.filepath.name}`")

    if st.button("🔄 Recargar datos", use_container_width=True, help="Fuerza una lectura del archivo"):
        st.session_state.data = _manager.load()
        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# MAIN TABS
# ═════════════════════════════════════════════════════════════════════════════

tab_user, tab_admin = st.tabs(["📋  Uso Rápido", "⚙️  Panel de Control"])

with tab_user:
    _render_user_mode()

with tab_admin:
    _render_admin_mode()
