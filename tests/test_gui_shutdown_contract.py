import ast
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "yt-transcriber_gui.py"


def _tree():
    return ast.parse(SOURCE.read_text(encoding="utf-8"))


def _main_window_class(tree):
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "MainWindow":
            return node
    raise AssertionError("MainWindow class not found")


def _method(class_node, name):
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} method not found")


def _attr_names(node):
    return {
        child.attr
        for child in ast.walk(node)
        if isinstance(child, ast.Attribute)
    }


def _method_call_names(node):
    names = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Attribute):
                names.add(func.attr)
            elif isinstance(func, ast.Name):
                names.add(func.id)
    return names


def test_tray_exit_uses_real_shutdown_path_instead_of_close():
    main_window = _main_window_class(_tree())
    quit_from_tray = _method(main_window, "_quit_from_tray")

    calls = _method_call_names(quit_from_tray)

    assert "_request_app_exit" in calls
    assert "close" not in calls


def test_close_event_distinguishes_tray_hide_from_real_exit():
    main_window = _main_window_class(_tree())
    close_event = _method(main_window, "closeEvent")

    names = _attr_names(close_event)
    calls = _method_call_names(close_event)

    assert "_real_exit_requested" in names
    assert "ignore" in calls
    assert "hide" in calls
    assert "_perform_shutdown_cleanup" in calls


def test_shutdown_cleanup_covers_timers_server_tray_and_workers():
    main_window = _main_window_class(_tree())
    cleanup = _method(main_window, "_perform_shutdown_cleanup")

    names = _attr_names(cleanup)
    calls = _method_call_names(cleanup)

    assert "_shutdown_cleanup_done" in names
    assert "_pulse_timer" in names
    assert "_backend_idle_timer" in names
    assert "instance_server" in names
    assert "tray_icon" in names
    assert "_setup_process" in names
    assert "worker" in names
    assert "stop_for_exit" in calls
    assert "removeServer" in calls
    assert "quit" not in calls
