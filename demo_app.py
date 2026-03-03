"""Demo application for cjm-transcription-source-select library.

Showcases the source selection component with local file browsing,
audio/video preview, selection ordering, and audio extraction from video.

Run with: python demo_app.py
"""

from pathlib import Path


# =============================================================================
# Configuration
# =============================================================================

DEMO_PORT = 5035
DEMO_MEDIA_DIR = str(Path.home() / "Music")  # Default starting directory


# =============================================================================
# Demo Application
# =============================================================================

def main():
    """Initialize source selection demo and start the server."""
    from fasthtml.common import fast_app, Div, H1, H2, P, Span, A, Script, APIRouter

    from cjm_fasthtml_daisyui.core.resources import get_daisyui_headers
    from cjm_fasthtml_daisyui.core.testing import create_theme_persistence_script
    from cjm_fasthtml_daisyui.components.actions.button import btn, btn_colors, btn_sizes
    from cjm_fasthtml_daisyui.utilities.semantic_colors import text_dui, border_dui

    from cjm_fasthtml_tailwind.utilities.spacing import p, m
    from cjm_fasthtml_tailwind.utilities.sizing import container, max_w, w, h
    from cjm_fasthtml_tailwind.utilities.typography import font_size, font_weight, text_align
    from cjm_fasthtml_tailwind.utilities.flexbox_and_grid import grid_display, grid_cols, gap
    from cjm_fasthtml_tailwind.utilities.borders import rounded, border
    from cjm_fasthtml_tailwind.core.base import combine_classes

    from cjm_fasthtml_app_core.components.navbar import create_navbar
    from cjm_fasthtml_app_core.core.routing import register_routes
    from cjm_fasthtml_app_core.core.htmx import handle_htmx_request
    from cjm_fasthtml_app_core.core.layout import wrap_with_layout

    from cjm_workflow_state.state_store import SQLiteWorkflowStateStore

    from cjm_plugin_system.core.manager import PluginManager

    from cjm_fasthtml_file_browser.providers.local import LocalFileSystemProvider

    from cjm_transcription_source_select.models import SourceSelectUrls
    from cjm_transcription_source_select.routes.core import get_step_state, get_session_id_from_sess
    from cjm_transcription_source_select.routes.browser import init_browser_router
    from cjm_transcription_source_select.routes.selection import init_selection_router
    from cjm_transcription_source_select.components.file_browser_panel import (
        create_media_browser_config, get_browser_state, sync_browser_selection,
        render_browser_panel,
    )
    from cjm_transcription_source_select.components.selection_panel import render_selection_panel
    from cjm_transcription_source_select.components.helpers import generate_sortable_init_script

    print("\n" + "=" * 70)
    print("Initializing cjm-transcription-source-select Demo")
    print("=" * 70)

    # Create FastHTML app
    app, rt = fast_app(
        pico=False,
        hdrs=[*get_daisyui_headers(), create_theme_persistence_script()],
        title="Transcription Source Selection Demo",
        htmlkw={'data-theme': 'light'},
        secret_key="demo-secret-key"
    )

    router = APIRouter(prefix="")

    print("  FastHTML app created")

    # -------------------------------------------------------------------------
    # Set up state store and plugin manager
    # -------------------------------------------------------------------------

    import tempfile
    temp_db = Path(tempfile.gettempdir()) / "cjm_tss_demo_state.db"
    state_store = SQLiteWorkflowStateStore(temp_db)
    workflow_id = "demo-transcription-source-select"
    print(f"  State store: {temp_db}")

    # Create plugin manager with manifest discovery
    plugin_manager = PluginManager()
    plugin_manager.discover_manifests()
    if plugin_manager.discovered:
        print(f"  Discovered plugins:")
        for meta in plugin_manager.discovered:
            print(f"    - {meta.name}")
    else:
        print(f"  No plugins discovered")

    # -------------------------------------------------------------------------
    # File system provider and browser config
    # -------------------------------------------------------------------------

    provider = LocalFileSystemProvider()
    home_path = provider.get_home_path()
    start_path = DEMO_MEDIA_DIR if Path(DEMO_MEDIA_DIR).exists() else home_path
    browser_config = create_media_browser_config()
    print(f"  File browser start: {start_path}")

    # -------------------------------------------------------------------------
    # Initialize routes
    # -------------------------------------------------------------------------

    urls = SourceSelectUrls()

    browser_router, browser_routes = init_browser_router(
        state_store=state_store,
        provider=provider,
        config=browser_config,
        workflow_id=workflow_id,
        urls=urls,
        home_path=home_path,
        prefix="/browser",
    )

    selection_router, selection_routes = init_selection_router(
        state_store=state_store,
        provider=provider,
        config=browser_config,
        workflow_id=workflow_id,
        urls=urls,
        home_path=home_path,
        prefix="/selection",
    )

    # Populate URL bundle
    urls.navigate = browser_routes["navigate"].to()
    urls.select = browser_routes["select"].to()
    urls.remove = selection_routes["remove"].to()
    urls.reorder = selection_routes["reorder"].to()
    urls.clear = selection_routes["clear"].to()

    print(f"  Routes initialized")
    for name, url in [("navigate", urls.navigate), ("select", urls.select),
                      ("remove", urls.remove), ("reorder", urls.reorder), ("clear", urls.clear)]:
        print(f"    {name}: {url}")

    # -------------------------------------------------------------------------
    # Page routes
    # -------------------------------------------------------------------------

    @router
    def index(request):
        """Homepage with demo overview."""

        def home_content():
            return Div(
                H1("Transcription Source Selection Demo",
                   cls=combine_classes(font_size._4xl, font_weight.bold, m.b(4))),

                P("Browse and select local audio/video files for transcription.",
                  cls=combine_classes(font_size.lg, text_dui.base_content, m.b(6))),

                Div(
                    H2("Features", cls=combine_classes(font_size._2xl, font_weight.bold, m.b(4))),
                    Div(
                        P("Local file system browsing with breadcrumb navigation", cls=m.b(2)),
                        P("Audio/video file filtering and preview", cls=m.b(2)),
                        P("Drag-and-drop selection ordering via SortableJS", cls=m.b(2)),
                        P("Audio extraction from video files via FFmpeg plugin", cls=m.b(2)),
                        P("Selection verification before proceeding", cls=m.b(2)),
                        cls=combine_classes(text_align.left, max_w.md, m.x.auto, m.b(8))
                    ),
                ),

                A(
                    "Open Source Selection Demo",
                    href=demo_selection.to(),
                    cls=combine_classes(btn, btn_colors.primary, btn_sizes.lg)
                ),

                cls=combine_classes(
                    container, max_w._4xl, m.x.auto, p(8), text_align.center
                )
            )

        return handle_htmx_request(
            request, home_content,
            wrap_fn=lambda content: wrap_with_layout(content, navbar=navbar)
        )

    @router
    def demo_selection(request, sess):
        """Source selection step demo page."""

        def selection_content():
            session_id = get_session_id_from_sess(sess)
            step_state = get_step_state(state_store, workflow_id, session_id)

            # Get or create browser state
            browser_state = get_browser_state(step_state, start_path)

            # Sync selection highlights with selected_files
            selected_files = step_state.get("selected_files", [])
            sync_browser_selection(browser_state, selected_files)

            # Render panels
            browser_panel = render_browser_panel(
                browser_state=browser_state,
                config=browser_config,
                provider=provider,
                navigate_url=urls.navigate,
                select_url=urls.select,
                home_path=home_path,
            )

            selection_panel = render_selection_panel(selected_files, urls)

            return Div(
                H1("Source Selection",
                   cls=combine_classes(font_size._2xl, font_weight.bold, m.b(4))),

                # Two-column layout (browser left, selection right)
                Div(
                    Div(browser_panel, cls=w.full),
                    Div(selection_panel, cls=w.full),
                    cls=combine_classes(str(grid_display), grid_cols(1), grid_cols(2).lg, gap(4))
                ),

                # SortableJS library + initialization (must be in body, not head)
                Script(src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"),
                Script(generate_sortable_init_script()),

                cls=combine_classes(p(4))
            )

        return handle_htmx_request(
            request, selection_content,
            wrap_fn=lambda content: wrap_with_layout(content, navbar=navbar)
        )

    # -------------------------------------------------------------------------
    # Navbar and route registration
    # -------------------------------------------------------------------------

    navbar = create_navbar(
        title="Source Selection Demo",
        nav_items=[
            ("Home", index),
            ("Selection", demo_selection),
        ],
        home_route=index,
        theme_selector=True
    )

    register_routes(app, router, browser_router, selection_router)

    # Debug output
    print("\n" + "=" * 70)
    print("Registered Routes:")
    print("=" * 70)
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  {route.path}")
    print("=" * 70)
    print("Demo App Ready!")
    print("=" * 70 + "\n")

    return app


if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading

    app = main()

    port = DEMO_PORT
    host = "0.0.0.0"
    display_host = 'localhost' if host in ['0.0.0.0', '127.0.0.1'] else host

    print(f"Server: http://{display_host}:{port}")
    print(f"\n  http://{display_host}:{port}/                — Homepage")
    print(f"  http://{display_host}:{port}/demo_selection   — Selection demo")
    print()

    timer = threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{port}"))
    timer.daemon = True
    timer.start()

    uvicorn.run(app, host=host, port=port)
