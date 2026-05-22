#!/usr/bin/env python3
"""
transcriber_backend.py — Rilevamento e gestione backend Whisper
Studio GD LEX — yt-transcriber v1.0.5

Ordine di preferenza:
  1. whisper.cpp Vulkan  (Linux/Windows, GPU AMD/Intel)
  2. whisper.cpp CUDA    (Linux/Windows, GPU Nvidia)
  3. whisper.cpp CPU     (Linux/Windows, CPU only)
  4. whisper.cpp gestito dall'app (CPU)
  5. whisper.cpp manuale via env
  6. faster-whisper      (Python, CPU/CUDA, fallback universale)
  7. faster-whisper venv utente
  8. openai-whisper      (Python, CPU, ultimo fallback)
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
from platform_paths import (
    app_whisper_cpp_bin,
    app_whisper_cpp_dir,
    app_whisper_model_dir,
    is_windows,
    user_venv_dir,
    user_venv_python,
)

# ── Costanti ──────────────────────────────────────────────────────────────────
IS_WINDOWS = is_windows()
IS_LINUX   = platform.system() == "Linux"
HOME       = Path.home()
USER_VENV_DIR = user_venv_dir()
USER_VENV_PYTHON = user_venv_python()
APP_WHISPER_CPP_DIR = app_whisper_cpp_dir()
APP_WHISPER_CPP_BIN = app_whisper_cpp_bin()
APP_WHISPER_MODEL_DIR = app_whisper_model_dir()
YT_TRANSCRIBER_WHISPER_BIN_ENV = "YT_TRANSCRIBER_WHISPER_BIN"
YT_TRANSCRIBER_WHISPER_MODEL_ENV = "YT_TRANSCRIBER_WHISPER_MODEL"

def _normalize_whisper_model_input(model_value: str | None) -> tuple[Path, str]:
    """Ritorna il path modello risolto e il filename ggml per il modello app-managed."""
    raw = (model_value or "").strip()
    if not raw:
        raw = str(HOME / "whisper.cpp/models/ggml-base.bin")

    resolved_model_path = Path(raw).expanduser()
    if "/" in raw or "\\" in raw or raw.endswith(".bin"):
        app_model_name = resolved_model_path.name or "ggml-base.bin"
    else:
        if raw == "large":
            raw = "large-v3"
        app_model_name = f"ggml-{raw}.bin"
        resolved_model_path = HOME / "whisper.cpp/models" / app_model_name
    return resolved_model_path, app_model_name


def _requested_model_name(default: str = "base") -> str:
    """Ritorna il nome modello richiesto per backend Python."""
    for raw in (
        os.environ.get(YT_TRANSCRIBER_WHISPER_MODEL_ENV),
        os.environ.get("WHISPER_MODEL"),
    ):
        value = (raw or "").strip()
        if not value:
            continue
        name = Path(value).name if ("/" in value or "\\" in value or value.endswith(".bin")) else value
        if name.startswith("ggml-"):
            name = name[5:]
        if name.endswith(".bin"):
            name = name[:-4]
        if name == "large-v3":
            return "large"
        return name
    return default


# Percorsi whisper.cpp — personalizzabili via env
WHISPER_MODEL, APP_WHISPER_MODEL_NAME = _normalize_whisper_model_input(
    os.environ.get("WHISPER_MODEL")
)

WHISPER_BINS = {
    "vulkan": Path(os.environ.get(
        "WHISPER_BIN_VULKAN",
        str(HOME / "whisper.cpp/build-vulkan/bin/whisper-cli") +
        (".exe" if IS_WINDOWS else "")
    )),
    "cuda": Path(os.environ.get(
        "WHISPER_BIN_CUDA",
        str(HOME / "whisper.cpp/build-cuda/bin/whisper-cli") +
        (".exe" if IS_WINDOWS else "")
    )),
    "cpu": Path(os.environ.get(
        "WHISPER_BIN_CPU",
        str(HOME / "whisper.cpp/build/bin/whisper-cli") +
        (".exe" if IS_WINDOWS else "")
    )),
}
APP_WHISPER_MODEL = APP_WHISPER_CPP_DIR / "models" / APP_WHISPER_MODEL_NAME
WHISPER_MODEL_BASE_DIRS = (
    HOME / "whisper.cpp/models",
    HOME / ".local/share/yt-transcriber/models",
    APP_WHISPER_MODEL_DIR,
    Path("/usr/share/yt-transcriber/models"),
    Path("/usr/local/share/whisper.cpp/models"),
)


def _discover_available_whisper_model() -> Path | None:
    """Ritorna un modello ggml disponibile per rilevare la disponibilita' del backend."""
    if WHISPER_MODEL.exists():
        return WHISPER_MODEL

    if APP_WHISPER_MODEL.exists():
        return APP_WHISPER_MODEL

    for env_name in (YT_TRANSCRIBER_WHISPER_MODEL_ENV, "WHISPER_MODEL"):
        raw = os.environ.get(env_name, "").strip()
        if not raw:
            continue
        candidate = Path(raw).expanduser()
        if candidate.is_file():
            return candidate

    for model_name in ("base", "small", "medium", "large-v3", "tiny"):
        filename = f"ggml-{model_name}.bin"
        for base_dir in WHISPER_MODEL_BASE_DIRS:
            candidate = base_dir / filename
            if candidate.is_file():
                return candidate

    return None


def _venv_has_module(python_path: Path, module_name: str) -> bool:
    """Verifica se un interpreter Python alternativo importa un modulo."""
    if not python_path.exists():
        return False
    try:
        r = subprocess.run(
            [str(python_path), "-c", f"import {module_name}"],
            capture_output=True, timeout=8
        )
        return r.returncode == 0
    except Exception:
        return False


def _manual_whisper_backend() -> dict | None:
    bin_value = os.environ.get(YT_TRANSCRIBER_WHISPER_BIN_ENV, "").strip()
    model_value = os.environ.get(YT_TRANSCRIBER_WHISPER_MODEL_ENV, "").strip()
    if not bin_value or not model_value:
        return None

    bin_path = Path(bin_value).expanduser()
    model_path = Path(model_value).expanduser()
    if not bin_path.is_file() or not model_path.is_file():
        return None
    if model_path.suffix.lower() != ".bin":
        return None

    return {
        "type":  "whisper_manual",
        "bin":   bin_path,
        "model": model_path,
        "info":  "whisper.cpp (manuale)",
        "fast":  False,
    }


# ── Rilevamento backend ────────────────────────────────────────────────────────
def detect_backend() -> dict:
    """
    Rileva il backend migliore disponibile.
    Ritorna: {'type': str, 'bin': Path|None, 'model': Path|None, 'info': str}
    """
    available_model = _discover_available_whisper_model()

    # 1. whisper.cpp Vulkan
    if WHISPER_BINS["vulkan"].exists():
        if _test_whisper_bin(WHISPER_BINS["vulkan"]):
            return {
                "type":  "whisper_vulkan",
                "bin":   WHISPER_BINS["vulkan"],
                "model": available_model,
                "info":  "whisper.cpp (Vulkan GPU)",
                "fast":  True,
            }

    # 2. whisper.cpp CUDA
    if WHISPER_BINS["cuda"].exists():
        if _test_whisper_bin(WHISPER_BINS["cuda"]):
            return {
                "type":  "whisper_cuda",
                "bin":   WHISPER_BINS["cuda"],
                "model": available_model,
                "info":  "whisper.cpp (CUDA GPU)",
                "fast":  True,
            }

    # 3. whisper.cpp CPU
    if WHISPER_BINS["cpu"].exists():
        if _test_whisper_bin(WHISPER_BINS["cpu"]):
            return {
                "type":  "whisper_cpu",
                "bin":   WHISPER_BINS["cpu"],
                "model": available_model,
                "info":  "whisper.cpp (CPU)",
                "fast":  False,
            }

    # 4. whisper.cpp gestito dall'app
    if APP_WHISPER_CPP_BIN.exists():
        if _test_whisper_bin(APP_WHISPER_CPP_BIN):
            return {
                "type":  "whisper_app_cpu",
                "bin":   APP_WHISPER_CPP_BIN,
                "model": available_model,
                "info":  "whisper.cpp (gestito dall'app)",
                "fast":  False,
            }

    # 5. whisper.cpp manuale via env
    manual_backend = _manual_whisper_backend()
    if manual_backend is not None:
        return manual_backend

    # 6. faster-whisper
    try:
        import faster_whisper
        return {
            "type":  "faster_whisper",
            "bin":   None,
            "model": None,
            "info":  "faster-whisper (Python)",
            "fast":  False,
        }
    except ImportError:
        pass

    # 7. faster-whisper nel venv utente
    if _venv_has_module(USER_VENV_PYTHON, "faster_whisper"):
        return {
            "type":   "faster_whisper_venv",
            "bin":    None,
            "model":  None,
            "python": USER_VENV_PYTHON,
            "info":   "faster-whisper (venv utente)",
            "fast":   False,
        }

    # 8. openai-whisper
    try:
        import whisper
        return {
            "type":  "openai_whisper",
            "bin":   None,
            "model": None,
            "info":  "openai-whisper (Python)",
            "fast":  False,
        }
    except ImportError:
        pass

    return {
        "type":  "none",
        "bin":   None,
        "model": None,
        "info":  "Nessun backend disponibile",
        "fast":  False,
    }


def _test_whisper_bin(bin_path: Path) -> bool:
    """Verifica che il binario sia eseguibile e risponda."""
    try:
        r = subprocess.run(
            [str(bin_path), "--help"],
            capture_output=True, timeout=5
        )
        return r.returncode in (0, 1)  # --help può dare 1
    except Exception:
        return False


# ── Trascrizione ───────────────────────────────────────────────────────────────
def transcribe(
    audio_path: str,
    output_srt: str,
    lang: str = "it",
    threads: int = 8,
    backend: dict = None,
    progress_callback=None,   # callable(pct, eta, speed)
    log_callback=None,        # callable(line, color)
) -> bool:
    """
    Esegui la trascrizione con il backend rilevato.
    Ritorna True se successo, False altrimenti.
    """
    if backend is None:
        backend = detect_backend()

    btype = backend["type"]

    if btype in ("whisper_vulkan", "whisper_cuda", "whisper_cpu", "whisper_app_cpu", "whisper_manual"):
        if not backend.get("model"):
            if log_callback:
                log_callback("✗  Backend whisper.cpp rilevato ma nessun modello ggml disponibile.", "#FF6B6B")
            return False
        return _transcribe_whisper_cpp(
            audio_path, output_srt, lang, threads,
            backend, progress_callback, log_callback
        )
    elif btype == "faster_whisper":
        return _transcribe_faster_whisper(
            audio_path, output_srt, lang,
            progress_callback, log_callback
        )
    elif btype == "faster_whisper_venv":
        return _transcribe_faster_whisper_venv(
            audio_path, output_srt, lang,
            backend, progress_callback, log_callback
        )
    elif btype == "openai_whisper":
        return _transcribe_openai_whisper(
            audio_path, output_srt, lang,
            progress_callback, log_callback
        )
    else:
        if log_callback:
            log_callback("✗  Nessun backend disponibile.", "#FF6B6B")
        return False


def _transcribe_whisper_cpp(audio_path, output_srt, lang, threads,
                             backend, progress_cb, log_cb):
    import re, time
    srt_base = output_srt.replace(".srt", "")
    lang_arg = ["-l", lang] if lang and lang != "auto" else []

    cmd = [
        str(backend["bin"]),
        "-m", str(backend["model"]),
        *lang_arg,
        "-f", audio_path,
        "-osrt",
        "-of", srt_base,
        "--threads", str(threads),
    ]

    # Calcola durata per ETA
    total_sec = _get_duration(audio_path)
    start_time = time.time()

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )

    for line in proc.stdout:
        line = line.rstrip()
        if not line:
            continue
        if log_cb:
            log_cb(line, "#90EE90")

        # PROGRESS parsing
        m = re.search(r'^\[(\d{2}:\d{2}:\d{2})', line)
        if m and progress_cb and total_sec:
            h, mi, s = map(int, m.group(1).split(':'))
            cur = h*3600 + mi*60 + s
            pct = min(int(cur * 100 / total_sec), 99)
            elapsed = time.time() - start_time
            speed = f"{cur/elapsed:.1f}×" if elapsed > 0 and cur > 0 else ""
            remaining = int((total_sec - cur) / (cur/elapsed)) if elapsed > 0 and cur > 0 else 0
            eta = f"{remaining//60:02d}:{remaining%60:02d}" if remaining > 0 else "--:--"
            progress_cb(pct, eta, speed)

    proc.wait()
    return proc.returncode == 0 and Path(output_srt).exists()


def _transcribe_faster_whisper(audio_path, output_srt, lang,
                                progress_cb, log_cb):
    try:
        from faster_whisper import WhisperModel
        import time

        selected_model = _requested_model_name()
        if log_cb:
            log_cb(f"⚙  Modello Whisper selezionato: {selected_model}", "#90EE90")
            log_cb(f"⚙  Caricamento modello faster-whisper ({selected_model})…", "#90EE90")
        model = WhisperModel(selected_model, device="cpu", compute_type="int8")

        detect_lang = None if lang == "auto" else lang
        segments, info = model.transcribe(audio_path, language=detect_lang)

        if log_cb:
            log_cb(f"⚙  Lingua rilevata: {info.language} ({info.language_probability:.0%})", "#90EE90")

        total = info.duration
        lines = []
        for i, seg in enumerate(segments):
            start = _fmt_ts(seg.start)
            end   = _fmt_ts(seg.end)
            lines.append(f"{i+1}\n{start} --> {end}\n{seg.text.strip()}\n")
            if progress_cb and total:
                pct = min(int(seg.end * 100 / total), 99)
                progress_cb(pct, "--:--", "")

        with open(output_srt, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        if progress_cb: progress_cb(100, "00:00", "")
        return True
    except Exception as e:
        if log_cb: log_cb(f"✗  faster-whisper: {e}", "#FF6B6B")
        return False


def _transcribe_faster_whisper_venv(audio_path, output_srt, lang,
                                     backend, progress_cb, log_cb):
    python_path = Path(backend.get("python", USER_VENV_PYTHON))
    if not python_path.exists():
        if log_cb:
            log_cb("✗  faster-whisper venv: interpreter non trovato.", "#FF6B6B")
        return False

    selected_model = _requested_model_name()

    script = r"""
import sys
from faster_whisper import WhisperModel

audio_path, output_srt, lang, model_name = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
detect_lang = None if lang == "auto" else lang
model = WhisperModel(model_name, device="cpu", compute_type="int8")
segments, info = model.transcribe(audio_path, language=detect_lang)
print(f"FWINFO:language={info.language};prob={info.language_probability:.4f};duration={info.duration}", flush=True)

def fmt_ts(seconds):
    ms = int((seconds % 1) * 1000)
    s = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

lines = []
for i, seg in enumerate(segments, start=1):
    lines.append(f"{i}\n{fmt_ts(seg.start)} --> {fmt_ts(seg.end)}\n{seg.text.strip()}\n")
    print(f"FWSEG:{seg.end:.3f}:{seg.text.strip()}", flush=True)

with open(output_srt, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
"""

    try:
        proc = subprocess.Popen(
            [str(python_path), "-c", script, audio_path, output_srt, lang or "it", selected_model],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except Exception as e:
        if log_cb:
            log_cb(f"✗  faster-whisper venv: {e}", "#FF6B6B")
        return False

    total = None
    for line in proc.stdout:
        line = line.rstrip()
        if not line:
            continue
        if line.startswith("FWINFO:"):
            if log_cb:
                log_cb(f"⚙  Modello Whisper selezionato: {selected_model}", "#90EE90")
                log_cb(f"⚙  Caricamento modello faster-whisper (venv utente, {selected_model})…", "#90EE90")
            parts = dict(
                item.split("=", 1) for item in line[7:].split(";") if "=" in item
            )
            total = float(parts.get("duration", "0") or "0")
            if log_cb and parts.get("language"):
                prob = float(parts.get("prob", "0") or "0")
                log_cb(
                    f"⚙  Lingua rilevata: {parts['language']} ({prob:.0%})",
                    "#90EE90",
                )
            continue
        if line.startswith("FWSEG:"):
            _, end_raw, text = line.split(":", 2)
            if progress_cb and total:
                pct = min(int(float(end_raw) * 100 / total), 99)
                progress_cb(pct, "--:--", "")
            continue
        if log_cb:
            log_cb(line, "#90EE90")

    proc.wait()
    if proc.returncode == 0 and Path(output_srt).exists():
        if progress_cb:
            progress_cb(100, "00:00", "")
        return True
    if log_cb:
        log_cb("✗  faster-whisper venv: trascrizione fallita.", "#FF6B6B")
    return False


def _transcribe_openai_whisper(audio_path, output_srt, lang,
                                progress_cb, log_cb):
    try:
        import whisper as ow
        selected_model = _requested_model_name()
        if log_cb:
            log_cb(f"⚙  Modello Whisper selezionato: {selected_model}", "#90EE90")
            log_cb(f"⚙  Caricamento modello openai-whisper ({selected_model})…", "#90EE90")
        model = ow.load_model(selected_model)
        detect_lang = None if lang == "auto" else lang
        result = model.transcribe(audio_path, language=detect_lang)

        lines = []
        for i, seg in enumerate(result["segments"]):
            start = _fmt_ts(seg["start"])
            end   = _fmt_ts(seg["end"])
            lines.append(f"{i+1}\n{start} --> {end}\n{seg['text'].strip()}\n")

        with open(output_srt, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        if progress_cb: progress_cb(100, "00:00", "")
        return True
    except Exception as e:
        if log_cb: log_cb(f"✗  openai-whisper: {e}", "#FF6B6B")
        return False


def _fmt_ts(seconds: float) -> str:
    """Secondi → HH:MM:SS,mmm"""
    ms = int((seconds % 1) * 1000)
    s  = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _get_duration(audio_path: str) -> float:
    """Durata in secondi con ffprobe."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True
        )
        return float(r.stdout.strip())
    except Exception:
        return 0.0


# ── Install helper ────────────────────────────────────────────────────────────
def install_faster_whisper():
    """Helper legacy: indirizza al setup in venv utente."""
    script_path = Path(__file__).resolve().parent / "scripts" / "setup_faster_whisper_venv.sh"
    if script_path.exists():
        subprocess.run(["bash", str(script_path)], check=False)
    else:
        print("Setup faster-whisper non disponibile: script mancante.", file=sys.stderr)


# ── CLI diagnostica ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    backend = detect_backend()
    print(f"\n{'='*50}")
    print(f"  yt-transcriber — Backend Diagnostics")
    print(f"{'='*50}")
    print(f"  Sistema:   {platform.system()} {platform.machine()}")
    print(f"  Backend:   {backend['info']}")
    print(f"  Veloce:    {'Sì (GPU)' if backend['fast'] else 'No (CPU)'}")
    if backend['bin']:
        print(f"  Binario:   {backend['bin']}")
    if backend['model']:
        print(f"  Modello:   {backend['model']}")
    if backend.get('python'):
        print(f"  Python:    {backend['python']}")
    print(f"{'='*50}\n")

    if backend['type'] == 'none':
        print("  ⚠  Nessun backend trovato.")
