#!/usr/bin/env python3
"""
transcriber_backend.py — Rilevamento e gestione backend Whisper
Studio GD LEX — yt-transcriber v1.0.0

Ordine di preferenza:
  1. whisper.cpp Vulkan  (Linux/Windows, GPU AMD/Intel)
  2. whisper.cpp CUDA    (Linux/Windows, GPU Nvidia)
  3. whisper.cpp CPU     (Linux/Windows, CPU only)
  4. faster-whisper      (Python, CPU/CUDA, fallback universale)
  5. openai-whisper      (Python, CPU, ultimo fallback)
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

# ── Costanti ──────────────────────────────────────────────────────────────────
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX   = platform.system() == "Linux"
HOME       = Path.home()

# Percorsi whisper.cpp — personalizzabili via env
WHISPER_MODEL = Path(os.environ.get(
    "WHISPER_MODEL",
    str(HOME / "whisper.cpp/models/ggml-medium.bin")
))

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


# ── Rilevamento backend ────────────────────────────────────────────────────────
def detect_backend() -> dict:
    """
    Rileva il backend migliore disponibile.
    Ritorna: {'type': str, 'bin': Path|None, 'model': Path|None, 'info': str}
    """
    # 1. whisper.cpp Vulkan
    if WHISPER_BINS["vulkan"].exists() and WHISPER_MODEL.exists():
        if _test_whisper_bin(WHISPER_BINS["vulkan"]):
            return {
                "type":  "whisper_vulkan",
                "bin":   WHISPER_BINS["vulkan"],
                "model": WHISPER_MODEL,
                "info":  "whisper.cpp (Vulkan GPU)",
                "fast":  True,
            }

    # 2. whisper.cpp CUDA
    if WHISPER_BINS["cuda"].exists() and WHISPER_MODEL.exists():
        if _test_whisper_bin(WHISPER_BINS["cuda"]):
            return {
                "type":  "whisper_cuda",
                "bin":   WHISPER_BINS["cuda"],
                "model": WHISPER_MODEL,
                "info":  "whisper.cpp (CUDA GPU)",
                "fast":  True,
            }

    # 3. whisper.cpp CPU
    if WHISPER_BINS["cpu"].exists() and WHISPER_MODEL.exists():
        if _test_whisper_bin(WHISPER_BINS["cpu"]):
            return {
                "type":  "whisper_cpu",
                "bin":   WHISPER_BINS["cpu"],
                "model": WHISPER_MODEL,
                "info":  "whisper.cpp (CPU)",
                "fast":  False,
            }

    # 4. faster-whisper
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

    # 5. openai-whisper
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

    if btype in ("whisper_vulkan", "whisper_cuda", "whisper_cpu"):
        return _transcribe_whisper_cpp(
            audio_path, output_srt, lang, threads,
            backend, progress_callback, log_callback
        )
    elif btype == "faster_whisper":
        return _transcribe_faster_whisper(
            audio_path, output_srt, lang,
            progress_callback, log_callback
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

        if log_cb: log_cb("⚙  Caricamento modello faster-whisper (medium)…", "#90EE90")
        model = WhisperModel("medium", device="cpu", compute_type="int8")

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


def _transcribe_openai_whisper(audio_path, output_srt, lang,
                                progress_cb, log_cb):
    try:
        import whisper as ow
        if log_cb: log_cb("⚙  Caricamento modello openai-whisper (medium)…", "#90EE90")
        model = ow.load_model("medium")
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
    """Installa faster-whisper come fallback."""
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "faster-whisper", "--break-system-packages", "-q"
    ])


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
    print(f"{'='*50}\n")

    if backend['type'] == 'none':
        print("  ⚠  Nessun backend trovato.")
        print("  Installo faster-whisper come fallback…")
        install_faster_whisper()
        print("  ✓  faster-whisper installato. Rilancio diagnostica…")
        backend = detect_backend()
        print(f"  Backend attivo: {backend['info']}")
