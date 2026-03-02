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
    from fasthtml.common import fast_app, Div, H1, H2, P, Span, A, APIRouter

    from cjm_fasthtml_daisyui.core.resources import get_daisyui_headers
    from cjm_fasthtml_daisyui.core.testing import create_theme_persistence_script
    from cjm_fasthtml_daisyui.components.data_display.badge import badge, badge_colors
    from cjm_fasthtml_daisyui.utilities.semantic_colors import bg_dui, text_dui

    from cjm_fasthtml_tailwind.utilities.spacing import p, m
    from cjm_fasthtml_tailwind.utilities.sizing import container, max_w, w, h
    from cjm_fasthtml_tailwind.utilities.typography import font_size, font_weight, text_align
    from cjm_fasthtml_tailwind.core.base import combine_classes

    from cjm_fasthtml_app_core.components.navbar import create_navbar
    from cjm_fasthtml_app_core.core.routing import register_routes
    from cjm_fasthtml_app_core.core.htmx import handle_htmx_request
    from cjm_fasthtml_app_core.core.layout import wrap_with_layout

    from cjm_workflow_state.state_store import SQLiteWorkflowStateStore

    from cjm_plugin_system.core.manager import PluginManager

    from cjm_transcription_source_select.models import SourceSelectUrls, SourceSelectState

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
    # Helper to get state
    # -------------------------------------------------------------------------

    def get_step_state(sess) -> SourceSelectState:
        """Get current source selection step state."""
        from cjm_fasthtml_interactions.core.state_store import get_session_id
        session_id = get_session_id(sess)

        state = state_store.get_state(workflow_id, session_id)

        if not state:
            state = {"step_states": {"source_select": {}}}
            state_store.update_state(workflow_id, session_id, state)

        return state.get("step_states", {}).get("source_select", {})

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
                    cls="btn btn-primary btn-lg"
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
            step_state = get_step_state(sess)
            selected_files = step_state.get("selected_files", [])
            verified = step_state.get("verified", False)

            # Placeholder UI until full step renderer is built
            return Div(
                H1("Source Selection",
                   cls=combine_classes(font_size._2xl, font_weight.bold, m.b(4))),
                P(f"Selected files: {len(selected_files)}",
                  cls=combine_classes(font_size.lg, m.b(2))),
                P(f"Verified: {verified}",
                  cls=combine_classes(font_size.lg, m.b(4))),
                P("Full UI will be built in subsequent phases.",
                  cls=combine_classes(text_dui.base_content, font_size.sm)),
                cls=combine_classes(p(8))
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

    register_routes(app, router)

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
