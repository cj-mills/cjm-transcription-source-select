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
    from cjm_fasthtml_daisyui.utilities.semantic_colors import text_dui

    from cjm_fasthtml_tailwind.utilities.spacing import p, m
    from cjm_fasthtml_tailwind.utilities.sizing import container, max_w
    from cjm_fasthtml_tailwind.utilities.typography import font_size, font_weight, text_align
    from cjm_fasthtml_tailwind.core.base import combine_classes

    from cjm_fasthtml_app_core.components.navbar import create_navbar
    from cjm_fasthtml_app_core.core.routing import register_routes
    from cjm_fasthtml_app_core.core.htmx import handle_htmx_request
    from cjm_fasthtml_app_core.core.layout import wrap_with_layout

    from cjm_workflow_state.state_store import SQLiteWorkflowStateStore

    from cjm_plugin_system.core.manager import PluginManager

    from cjm_fasthtml_file_browser.providers.local import LocalFileSystemProvider

    from cjm_transcription_source_select.routes.core import get_step_state, get_session_id_from_sess
    from cjm_transcription_source_select.routes.init import init_source_select_routers
    from cjm_transcription_source_select.services.source_select import SourceSelectService
    from cjm_transcription_source_select.components.file_browser_panel import create_media_browser_config
    from cjm_transcription_source_select.components.step_renderer import render_source_select_step

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

    plugin_manager = PluginManager()
    plugin_manager.discover_manifests()
    if plugin_manager.discovered:
        print(f"  Discovered plugins:")
        for meta in plugin_manager.discovered:
            print(f"    - {meta.name}")
    else:
        print(f"  No plugins discovered")

    # -------------------------------------------------------------------------
    # Service layer and file system provider
    # -------------------------------------------------------------------------

    service = SourceSelectService(plugin_manager)
    service.ensure_loaded()
    print(f"  FFmpeg plugin available: {service.is_available()}")

    provider = LocalFileSystemProvider()
    home_path = provider.get_home_path()
    start_path = DEMO_MEDIA_DIR if Path(DEMO_MEDIA_DIR).exists() else home_path
    browser_config = create_media_browser_config()
    print(f"  File browser start: {start_path}")

    # -------------------------------------------------------------------------
    # Initialize routes via unified assembly
    # -------------------------------------------------------------------------

    source_select = init_source_select_routers(
        state_store=state_store,
        provider=provider,
        browser_config=browser_config,
        workflow_id=workflow_id,
        service=service,
        home_path=home_path,
        prefix="",
    )

    print(f"  Routers initialized ({len(source_select.routers)} routers)")

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

            # Eagerly restore browser state so file browser shows correct directory
            source_select.restore_state(session_id)

            step_state = get_step_state(state_store, workflow_id, session_id)

            selected_files = step_state.get("selected_files", [])
            selected_folders = step_state.get("selected_folders", [])
            extraction_results = step_state.get("extraction_results", {})
            verified = step_state.get("verified", False)

            return render_source_select_step(
                selected_files=selected_files,
                extraction_results=extraction_results,
                verified=verified,
                urls=source_select.urls,
                render_browser_panel_fn=source_select.render_panel,
                selected_folders=selected_folders,
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

    register_routes(app, router, *source_select.routers)

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
