#!/usr/bin/env python3
"""Utility minime per path e apertura file/cartelle cross-platform."""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path


APP_NAME = "yt-transcriber"


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_macos() -> bool:
    return platform.system() == "Darwin"


def _windows_local_appdata() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata)
    return Path.home() / "AppData" / "Local"


def app_data_dir() -> Path:
    if is_windows():
        return _windows_local_appdata() / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


def config_dir() -> Path:
    if is_windows():
        return _windows_local_appdata() / APP_NAME / "config"
    return Path.home() / ".config" / APP_NAME


def cache_dir() -> Path:
    if is_windows():
        return _windows_local_appdata() / APP_NAME / "cache"
    return Path.home() / ".cache" / APP_NAME


def default_output_dir() -> Path:
    return Path.home() / "Trascrizioni"


def user_venv_dir() -> Path:
    return app_data_dir() / "venv"


def user_venv_python() -> Path:
    if is_windows():
        return user_venv_dir() / "Scripts" / "python.exe"
    return user_venv_dir() / "bin" / "python"


def app_whisper_cpp_dir() -> Path:
    return app_data_dir() / "whisper.cpp"


def app_whisper_cpp_bin() -> Path:
    if is_windows():
        return app_whisper_cpp_dir() / "build" / "bin" / "whisper-cli.exe"
    return app_whisper_cpp_dir() / "build" / "bin" / "whisper-cli"


def app_whisper_model_dir() -> Path:
    return app_whisper_cpp_dir() / "models"


def open_path(path: str | Path) -> bool:
    target = Path(path).expanduser()
    try:
        if is_windows() and hasattr(os, "startfile"):
            os.startfile(str(target))
            return True
        if is_macos():
            subprocess.Popen(["open", str(target)])
            return True
        subprocess.Popen(["xdg-open", str(target)])
        return True
    except Exception:
        return False
