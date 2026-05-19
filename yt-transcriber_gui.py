#!/usr/bin/env python3
"""
yt-transcriber GUI v1.2.1
Pipeline Trascrizione Audio/Video — Studio GD LEX
"""

import sys, os, re, signal, subprocess, json, random, shutil
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar,
    QFileDialog, QFrame, QSizePolicy, QMessageBox, QScrollArea,
    QTabWidget, QSplashScreen, QComboBox, QListWidget, QListWidgetItem, QMenu,
    QStackedLayout, QSystemTrayIcon
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QRect, QProcess
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtGui import (QFont, QTextCursor, QPalette, QColor,
                          QPixmap, QPainter, QPen, QBrush, QLinearGradient,
                          QAction, QIcon)

# ── Versione ───────────────────────────────────────────────────────────────────
APP_VERSION = "1.2.1"
APP_AUTHOR  = "Studio GD LEX"
APP_YEAR    = "2026"

# ── Backend detection ──────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
try:
    from transcriber_backend import detect_backend as _detect_backend
    _BACKEND = _detect_backend()
except Exception:
    _BACKEND = {"type": "none", "info": "non rilevato", "fast": False}

# ── Config ─────────────────────────────────────────────────────────────────────
PIPELINE_DIR  = Path(__file__).parent
DEFAULT_OUT   = Path.home() / "Trascrizioni"
SCRIPT_SH     = PIPELINE_DIR / "yt-transcriber.sh"
SINGLE_INSTANCE_SERVER_NAME = "yt-transcriber-gdlex"
YT_TRANSCRIBER_WHISPER_BIN_ENV = "YT_TRANSCRIBER_WHISPER_BIN"
YT_TRANSCRIBER_WHISPER_MODEL_ENV = "YT_TRANSCRIBER_WHISPER_MODEL"
LEGACY_WHISPER_BIN_ENV = "WHISPER_BIN"
LEGACY_WHISPER_MODEL_ENV = "WHISPER_MODEL"
SETUP_FASTER_WHISPER_SCRIPT = PIPELINE_DIR / "scripts" / "setup_faster_whisper_venv.sh"
INSTALLED_SETUP_FASTER_WHISPER_SCRIPT = Path("/usr/lib/yt-transcriber/scripts/setup_faster_whisper_venv.sh")
SETUP_WHISPER_CPP_SCRIPT = PIPELINE_DIR / "scripts" / "setup_whisper_cpp.sh"
INSTALLED_SETUP_WHISPER_CPP_SCRIPT = Path("/usr/lib/yt-transcriber/scripts/setup_whisper_cpp.sh")
APP_WHISPER_CPP_DIR = Path.home() / ".local/share/yt-transcriber/whisper.cpp"

WHISPER_BIN_CANDIDATES = (
    Path.home() / "whisper.cpp/build-vulkan/bin/whisper-cli",
    Path.home() / "whisper.cpp/build-cuda/bin/whisper-cli",
    Path.home() / "whisper.cpp/build/bin/whisper-cli",
    APP_WHISPER_CPP_DIR / "build/bin/whisper-cli",
    Path("/usr/local/bin/whisper-cli"),
    Path("/usr/bin/whisper-cli"),
)

WHISPER_MODEL_BASE_DIRS = (
    Path.home() / "whisper.cpp/models",
    Path.home() / ".local/share/yt-transcriber/models",
    APP_WHISPER_CPP_DIR / "models",
    Path("/usr/share/yt-transcriber/models"),
    Path("/usr/local/share/whisper.cpp/models"),
)

HISTORY_FILE  = Path.home() / ".config/yt-transcriber/history.json"

AUDIO_FORMATS = (
    "Audio/Video (*.mp3 *.mp4 *.wav *.flac *.ogg *.opus *.m4a *.webm *.aac "
    "*.wma *.aiff *.mka *.mkv *.avi *.mov *.wmv *.flv *.ts *.mts *.m2ts *.vob *.3gp);;"
    "Audio (*.mp3 *.wav *.flac *.ogg *.opus *.m4a *.aac *.wma *.aiff *.mka);;"
    "Video (*.mp4 *.mkv *.avi *.mov *.wmv *.webm *.flv *.ts *.mts *.m2ts *.vob *.3gp);;"
    "Tutti i file (*)"
)

LANGUAGES = [
    ("🌐", "auto", "Rilevamento automatico"),
    ("🇮🇹", "it",  "Italiano"),
    ("🇬🇧", "en",  "English"),
    ("🇫🇷", "fr",  "Français"),
    ("🇩🇪", "de",  "Deutsch"),
    ("🇪🇸", "es",  "Español"),
    ("🇵🇹", "pt",  "Português"),
    ("🇷🇺", "ru",  "Русский"),
    ("🇨🇳", "zh",  "中文"),
    ("🇯🇵", "ja",  "日本語"),
    ("🇦🇷", "ar",  "العربية"),
    ("🇳🇱", "nl",  "Nederlands"),
    ("🇵🇱", "pl",  "Polski"),
    ("🇹🇷", "tr",  "Türkçe"),
    ("🇬🇷", "el",  "Ελληνικά"),
]

WHISPER_MODELS = [
    ("medium",   "medium   — veloce, buona qualità  (~1.5 GB)"),
    ("large-v3", "large-v3 — lento, qualità massima (~3 GB)"),
    ("small",    "small    — molto veloce, qualità base (~500 MB)"),
]

# ── Palette Matrix Slate ───────────────────────────────────────────────────────
BG         = "#0F1A0F"
BG2        = "#141F14"
BG3        = "#1A2A1A"
GREEN      = "#00FF41"
GREEN_DIM  = "#90EE90"
GREEN_DARK = "#1A3A1A"
GREEN_MID  = "#00C832"
GOLD       = "#FFD700"
RED        = "#FF6B6B"
MUTED      = "#4A6A4A"
BORDER     = "#243A24"
WHITE      = "#E0FFE0"
LIVE_TEXT  = "#D8FFD8"
FONT_MONO  = "JetBrains Mono, Fira Code, Monospace, Courier New"
ENABLE_BACKSTAGE_MATRIX_RAIN = True
ENABLE_MATRIX_EASTER_EGGS = True
ENABLE_WHITE_RABBIT_EASTER_EGGS = True
BACKSTAGE_MATRIX_IDLE_MS = 1500
BACKSTAGE_MATRIX_FRAME_MS = 120
WHITE_RABBIT_CHANCE = 0.50
WHITE_RABBIT_MIN_COOLDOWN_TICKS = 18
WHITE_RABBIT_MAX_COOLDOWN_TICKS = 35
MATRIX_ASSET_DIR = PIPELINE_DIR / "assets" / "matrix"
WHITE_RABBIT_FRAME_NAMES = tuple(
    f"white_rabbit_{idx}.png" for idx in range(4)
)
MATRIX_IDLE_MESSAGES = [
    "NEO, OPEN YOUR EYES",
    "KNOCK KNOCK...",
    "WAKE UP...",
    "FOLLOW THE WHITE RABBIT",
    "SIGNAL ACQUIRED",
    "SEARCHING THE SOURCE",
    "ACCESSING STREAM",
    "LISTENING...",
    "RED PILL ACCEPTED",
    "BLUE PILL: WAIT",
    "RED PILL: TRACE",
]

# ── Cronologia ────────────────────────────────────────────────────────────────
def load_history():
    try:
        return json.loads(HISTORY_FILE.read_text())
    except Exception:
        return []

def save_history(items):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(items[-20:], ensure_ascii=False, indent=2))


def _expand_candidate_path(value):
    try:
        return Path(value).expanduser()
    except Exception:
        return None


def _is_executable_file(path):
    return bool(path and path.is_file() and os.access(path, os.X_OK))


def _normalize_model_filename(model_name):
    raw = (model_name or "").strip()
    if raw.endswith(".bin"):
        raw = raw[:-4]
    if raw.startswith("ggml-"):
        raw = raw[5:]
    return f"ggml-{raw}.bin" if raw else "ggml-medium.bin"


def _resolve_model_candidate_paths(model_name):
    filename = _normalize_model_filename(model_name)
    return [base / filename for base in WHISPER_MODEL_BASE_DIRS], filename


def resolve_whisper_bin():
    issues = []
    env_name = None
    candidate = None
    for name in (YT_TRANSCRIBER_WHISPER_BIN_ENV, LEGACY_WHISPER_BIN_ENV):
        value = os.environ.get(name, "").strip()
        if not value:
            continue
        env_name = name
        candidate = _expand_candidate_path(value)
        if candidate is None or not candidate.exists():
            issues.append(f"{name} punta a un file inesistente")
            candidate = None
            break
        if not candidate.is_file():
            issues.append(f"{name} non punta a un file")
            candidate = None
            break
        if not os.access(candidate, os.X_OK):
            issues.append(f"{name} punta a un file non eseguibile")
            candidate = None
            break
        return candidate, issues

    which_path = shutil.which("whisper-cli")
    if which_path:
        candidate = _expand_candidate_path(which_path)
        if _is_executable_file(candidate):
            return candidate, issues

    for candidate in WHISPER_BIN_CANDIDATES:
        if _is_executable_file(candidate):
            return candidate, issues

    if env_name and not issues:
        issues.append(f"{env_name} non valida")
    return None, issues


def resolve_whisper_model(model_name):
    issues = []
    filename = _normalize_model_filename(model_name)

    for name in (YT_TRANSCRIBER_WHISPER_MODEL_ENV, LEGACY_WHISPER_MODEL_ENV):
        value = os.environ.get(name, "").strip()
        if not value:
            continue
        if "/" not in value and not value.endswith(".bin"):
            model_name = value
            filename = _normalize_model_filename(model_name)
            break
        candidate = _expand_candidate_path(value)
        if candidate is None or not candidate.exists():
            issues.append(f"{name} punta a un file inesistente")
            return None, filename, issues
        if not candidate.is_file():
            issues.append(f"{name} non punta a un file")
            return None, filename, issues
        return candidate, candidate.name, issues

    for candidate in _resolve_model_candidate_paths(model_name)[0]:
        if candidate.is_file():
            return candidate, candidate.name, issues

    return None, filename, issues


def resolve_setup_faster_whisper_script():
    for candidate in (
        SETUP_FASTER_WHISPER_SCRIPT,
        INSTALLED_SETUP_FASTER_WHISPER_SCRIPT,
    ):
        if candidate.is_file():
            return candidate
    return None


def resolve_setup_whisper_cpp_script():
    for candidate in (
        SETUP_WHISPER_CPP_SCRIPT,
        INSTALLED_SETUP_WHISPER_CPP_SCRIPT,
    ):
        if candidate.is_file():
            return candidate
    return None


# ── Worker ────────────────────────────────────────────────────────────────────
class PipelineWorker(QThread):
    log_line = pyqtSignal(str, str)
    transcript_chunk = pyqtSignal(str)
    progress = pyqtSignal(int, str, str)
    step_idx = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, url, title, output_dir,
                 lang="it", timestamps=False, burn_subs=False,
                 formats=None, model="medium", audio_normalize=False,
                 whisper_bin=None, whisper_model_path=None):
        super().__init__()
        self.url        = url
        self.title      = title
        self.output_dir = output_dir
        self.lang       = lang
        self.timestamps = timestamps
        self.burn_subs  = burn_subs
        self.formats    = formats or {"docx": True}
        self.model      = model
        self.audio_normalize = audio_normalize
        self.whisper_bin = str(whisper_bin) if whisper_bin else ""
        self.whisper_model_path = str(whisper_model_path) if whisper_model_path else ""
        self._cancelled = False
        self._proc      = None
        self._last_ytdlp_bucket = -1

    def cancel(self):
        self._cancelled = True
        if self._proc:
            try:
                if self._proc.poll() is None:
                    os.killpg(os.getpgid(self._proc.pid), signal.SIGTERM)
            except Exception:
                try:
                    self._proc.terminate()
                except Exception:
                    pass

    def _extract_transcript_payload(self, line):
        if not line or not line.startswith("TRANSCRIPT_LIVE:"):
            return None
        return line.split(":", 1)[1].strip()

    def _extract_audio_prep_status(self, line):
        if not line or not line.startswith("AUDIO_PREP_STATUS:"):
            return None
        return line.split(":", 1)[1].strip()

    def run(self):
        env = os.environ.copy()
        env["WHISPER_LANG"]       = self.lang if self.lang != "auto" else ""
        env["WHISPER_TIMESTAMPS"] = "1" if self.timestamps else "0"
        env["WHISPER_BURN_SUBS"]  = "1" if self.burn_subs  else "0"
        env["AUDIO_NORMALIZE"]    = "1" if self.audio_normalize else "0"
        env["OUT_DOCX"] = "1" if self.formats.get("docx") else "0"
        env["OUT_PDF"]  = "1" if self.formats.get("pdf")  else "0"
        env["OUT_TXT"]  = "1" if self.formats.get("txt")  else "0"
        env["OUT_SRT"]  = "1" if self.formats.get("srt")  else "0"
        env["OUT_VTT"]  = "1" if self.formats.get("vtt")  else "0"
        env["WHISPER_MODEL"] = self.whisper_model_path or self.model
        if self.whisper_bin:
            env["WHISPER_BIN"] = self.whisper_bin
            env[YT_TRANSCRIBER_WHISPER_BIN_ENV] = self.whisper_bin
        if self.whisper_model_path:
            env[YT_TRANSCRIBER_WHISPER_MODEL_ENV] = self.whisper_model_path

        if self.url.startswith("LOCAL:"):
            cmd = [str(SCRIPT_SH), "--local", self.url[6:],
                   self.title, str(self.output_dir)]
        else:
            cmd = [str(SCRIPT_SH), self.url, self.title, str(self.output_dir)]

        STEPS = ["download audio", "preparazione audio", "normalizzazione audio",
                 "trascrizione con whisper", "pulitura testo",
                 "generazione file word", "lingua italiana"]
        success = False
        msg = "Pipeline interrotta."
        try:
            self._proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, env=env, start_new_session=True)

            for line in self._proc.stdout:
                line = line.rstrip()
                if self._cancelled:
                    continue
                if not line: continue
                clean = re.sub(r"\x1b\[[0-9;]*m", "", line)

                transcript_text = self._extract_transcript_payload(clean)
                if transcript_text is not None:
                    if transcript_text:
                        self.transcript_chunk.emit(transcript_text)
                    continue

                audio_prep_status = self._extract_audio_prep_status(clean)
                if audio_prep_status is not None:
                    if audio_prep_status:
                        self.log_line.emit(f"→ {audio_prep_status}", WHITE)
                    continue

                if clean.startswith("YTDLP_PROGRESS:"):
                    parts = clean.split(":", 5)
                    pct_raw = parts[1] if len(parts) > 1 else ""
                    downloaded = parts[2] if len(parts) > 2 else ""
                    total = parts[3] if len(parts) > 3 else ""
                    speed = parts[4] if len(parts) > 4 else ""
                    eta = parts[5] if len(parts) > 5 else ""

                    def _norm_field(value, default="--"):
                        value = value.strip()
                        return default if not value or value == "NA" else value

                    pct_clean = pct_raw.strip().replace("%", "")
                    try:
                        pct = int(float(pct_clean))
                    except Exception:
                        continue

                    downloaded = _norm_field(downloaded)
                    total = _norm_field(total)
                    speed = _norm_field(speed)
                    eta = _norm_field(eta, "--:--")

                    self.progress.emit(pct, eta, "" if speed == "--" else speed)

                    bucket = 10 if pct >= 100 else max(0, pct // 10)
                    if bucket != self._last_ytdlp_bucket:
                        self._last_ytdlp_bucket = bucket
                        self.log_line.emit(
                            f"→ Download video: {pct}% - {downloaded} / {total} - {speed} - ETA {eta}",
                            WHITE
                        )
                    continue

                # Filtra righe barra ASCII
                has_blocks = any(c in "█░▓▒" for c in clean)
                if has_blocks or clean.startswith("PROGRESS:"): pass
                else:
                    color = (GREEN_DIM if "✓" in clean or "completat" in clean.lower()
                             else RED    if "✗" in clean or "error" in clean.lower()
                             else GOLD   if "⚠" in clean
                             else "#00FFFF" if "▶" in clean
                             else WHITE)
                    self.log_line.emit(clean, color)

                cl = clean.lower()
                for i, kw in enumerate(STEPS):
                    if kw in cl:
                        self.step_idx.emit(i); break

                if clean.startswith("PROGRESS:"):
                    parts = clean.split(":")
                    try:
                        pct   = int(parts[1])
                        eta   = parts[2] if len(parts) > 2 else "--:--"
                        speed = f"{parts[3]}×" if len(parts) > 3 and parts[3] else ""
                        self.progress.emit(pct, eta, speed)
                    except Exception:
                        pass
                else:
                    pm = re.search(r"(\d{1,3})%", clean)
                    em = re.search(r"ETA\s+(\d+:\d+)", clean)
                    sm = re.search(r"velocità\s+([\d.]+)x", clean)
                    if pm and not clean.startswith("["):
                        self.progress.emit(
                            int(pm.group(1)),
                            em.group(1) if em else "--:--",
                            f"{sm.group(1)}×" if sm else "")

            self._proc.wait()
            if self._cancelled:
                msg = "Annullato."
            elif self._proc.returncode == 0:
                success = True
                msg = "Pipeline completata."
            else:
                msg = f"Errore (exit {self._proc.returncode})."
        except Exception as e:
            msg = str(e)
        finally:
            self.finished.emit(success, msg)


# ── Componenti UI ─────────────────────────────────────────────────────────────
class MatrixInput(QLineEdit):
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setFont(QFont(FONT_MONO, 13))
        self._apply_style(False)

    def _apply_style(self, focused):
        border = GREEN if focused else GREEN_MID
        bg = "#0F280F" if focused else BG3
        self.setStyleSheet(f"""
            QLineEdit {{
                background: {bg}; border: 1.5px solid {border};
                border-radius: 4px; padding: 9px 14px;
                color: {WHITE}; font-family: {FONT_MONO}; font-size: 13px;
            }}
            QLineEdit::placeholder {{ color: #5A8A5A; }}
        """)

    def focusInEvent(self, e):  self._apply_style(True);  super().focusInEvent(e)
    def focusOutEvent(self, e): self._apply_style(False); super().focusOutEvent(e)


class StepBadge(QLabel):
    IDLE=0; ACTIVE=1; DONE=2

    def __init__(self, num, text):
        super().__init__()
        self._num=num; self._text=text; self._state=self.IDLE
        self._render()

    def set_state(self, s):
        self._state=s; self._render()

    def _render(self):
        if   self._state == self.DONE:   bg,fg,pre,bold = GREEN_DARK,GREEN,"✓",True
        elif self._state == self.ACTIVE: bg,fg,pre,bold = GREEN_DARK,GREEN,"●",True
        else:                            bg,fg,pre,bold = BG2,MUTED,str(self._num),False
        self.setText(f" {pre}  {self._text} ")
        self.setFont(QFont(FONT_MONO, 11,
                     QFont.Weight.Bold if bold else QFont.Weight.Normal))
        border = GREEN if self._state != self.IDLE else BORDER
        self.setStyleSheet(f"""
            QLabel {{ background: {bg}; color: {fg};
                      border: 1px solid {border}; border-radius: 3px;
                      padding: 5px 6px; }}
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class SectionHeader(QLabel):
    def __init__(self, text):
        super().__init__(f"// {text}")
        self.setFont(QFont(FONT_MONO, 11))
        self.setStyleSheet(f"color:{MUTED}; letter-spacing:2px; background:transparent;")


def make_card(title):
    f = QFrame()
    f.setStyleSheet(f"QFrame {{ background:{BG2}; border:1px solid {BORDER}; border-radius:4px; }}")
    v = QVBoxLayout(f)
    v.setContentsMargins(18,12,18,14)
    v.setSpacing(8)
    v.addWidget(SectionHeader(title))
    return f, v


def toggle_btn(label, checked=False, enabled=True):
    btn = QPushButton(label)
    btn.setCheckable(True)
    btn.setChecked(checked)
    btn.setEnabled(enabled)
    btn.setFont(QFont(FONT_MONO, 11))
    def update(b=btn):
        if b.isChecked():
            b.setStyleSheet(f"QPushButton {{ background:{GREEN_DARK}; color:{GREEN}; border:1.5px solid {GREEN_MID}; border-radius:4px; padding:6px 14px; font-family:{FONT_MONO}; }}")
        else:
            b.setStyleSheet(f"QPushButton {{ background:{BG3}; color:{MUTED}; border:1px solid {BORDER}; border-radius:4px; padding:6px 14px; font-family:{FONT_MONO}; }} QPushButton:disabled {{ color:#2A3A2A; border-color:#1A2A1A; }}")
    btn.toggled.connect(lambda _: update())
    update()
    return btn


class MatrixRainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._active = False
        self._columns = []
        self._idle_message = ""
        self._rabbit_frames = self._load_rabbit_frames()
        self._rabbit_active = False
        self._rabbit_x = -self._rabbit_sprite_width()
        self._rabbit_base_y = 0
        self._rabbit_y = 0
        self._rabbit_frame_index = 0
        self._rabbit_speed = 5
        self._rabbit_hop_phase = 0
        self._rabbit_spawn_cooldown_ticks = 0
        self.setMinimumHeight(156)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def start_animation(self):
        if self._active:
            return
        self._active = True
        self._reset_columns()
        if ENABLE_MATRIX_EASTER_EGGS and MATRIX_IDLE_MESSAGES:
            self._idle_message = random.choice(MATRIX_IDLE_MESSAGES)
        else:
            self._idle_message = ""
        self._try_spawn_rabbit()
        if not self._rabbit_active:
            self._rabbit_spawn_cooldown_ticks = random.randint(8, 12)
        self._timer.start(BACKSTAGE_MATRIX_FRAME_MS)
        self.update()

    def stop_animation(self):
        if not self._active and not self._timer.isActive():
            return
        self._active = False
        self._timer.stop()
        self._idle_message = ""
        self._rabbit_active = False
        self._rabbit_x = -self._rabbit_sprite_width()
        self._rabbit_base_y = 0
        self._rabbit_hop_phase = 0
        self._rabbit_spawn_cooldown_ticks = 0
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._active:
            self._reset_columns()

    def _reset_columns(self):
        chars = "01アイウエオカキクケコサシスセソ"
        usable_width = max(1, self.width() - 24)
        count = max(6, usable_width // 28)
        self._columns = []
        for idx in range(count):
            self._columns.append({
                "x": 14 + idx * max(18, usable_width // count),
                "y": random.randint(-120, max(10, self.height())),
                "speed": random.randint(9, 18),
                "length": random.randint(4, 8),
                "chars": [random.choice(chars) for _ in range(random.randint(4, 8))],
            })

    def _load_rabbit_frames(self):
        frames = []
        for name in WHITE_RABBIT_FRAME_NAMES:
            pixmap = QPixmap(str(MATRIX_ASSET_DIR / name))
            if pixmap.isNull():
                return []
            frames.append(pixmap)
        return frames

    def _rabbit_sprite_width(self):
        return self._rabbit_frames[0].width() if self._rabbit_frames else 64

    def _rabbit_sprite_height(self):
        return self._rabbit_frames[0].height() if self._rabbit_frames else 40

    def _top_status_height(self):
        return 30

    def _bottom_lane_height(self):
        return 58

    def _easter_egg_text_rect(self):
        return QRect(18, self.height() - 28, self.width() - 36, 22)

    def _rabbit_lane_top(self):
        return self.height() - self._bottom_lane_height()

    def _next_rabbit_spawn_cooldown(self):
        return random.randint(
            WHITE_RABBIT_MIN_COOLDOWN_TICKS,
            WHITE_RABBIT_MAX_COOLDOWN_TICKS
        )

    def _try_spawn_rabbit(self):
        if self._rabbit_active:
            return
        if not self._rabbit_frames:
            self._rabbit_frames = self._load_rabbit_frames()
        if not ENABLE_WHITE_RABBIT_EASTER_EGGS or not self._rabbit_frames:
            return
        if random.random() > WHITE_RABBIT_CHANCE:
            return
        self._rabbit_x = -self._rabbit_sprite_width()
        self._rabbit_frame_index = 0
        self._rabbit_hop_phase = 0
        self._rabbit_speed = random.randint(5, 6)
        self._rabbit_active = True
        lane_top = self._rabbit_lane_top()
        self._rabbit_base_y = max(
            self._top_status_height() + 12,
            lane_top - self._rabbit_sprite_height() - random.randint(4, 10)
        )
        self._rabbit_y = self._rabbit_base_y
        self._rabbit_spawn_cooldown_ticks = 0

    def _draw_rabbit(self, painter):
        if not self._rabbit_active or not self._rabbit_frames:
            return
        painter.setOpacity(0.90)
        painter.drawPixmap(
            int(self._rabbit_x),
            int(self._rabbit_y),
            self._rabbit_frames[self._rabbit_frame_index]
        )
        painter.setOpacity(1.0)

    def _tick(self):
        if not self._active:
            return
        chars = "01アイウエオカキクケコサシスセソ"
        bottom = self.height() + 50
        for col in self._columns:
            col["y"] += col["speed"]
            if random.random() < 0.25 and col["chars"]:
                col["chars"][-1] = random.choice(chars)
            if col["y"] > bottom:
                col["y"] = random.randint(-120, -20)
                col["speed"] = random.randint(9, 18)
                col["chars"] = [random.choice(chars) for _ in range(random.randint(4, 8))]
        if self._rabbit_active:
            self._rabbit_x += self._rabbit_speed
            self._rabbit_hop_phase = (self._rabbit_hop_phase + 1) % 8
            hop = (0, -4, -10, -14, -9, -3, 1, 0)[self._rabbit_hop_phase]
            self._rabbit_y = self._rabbit_base_y + hop
            self._rabbit_frame_index = (self._rabbit_frame_index + 1) % len(self._rabbit_frames)
            if self._rabbit_x > self.width() + self._rabbit_sprite_width():
                self._rabbit_active = False
                self._rabbit_spawn_cooldown_ticks = self._next_rabbit_spawn_cooldown()
        else:
            if self._rabbit_spawn_cooldown_ticks > 0:
                self._rabbit_spawn_cooldown_ticks -= 1
            if self._rabbit_spawn_cooldown_ticks <= 0:
                self._try_spawn_rabbit()
                if not self._rabbit_active:
                    self._rabbit_spawn_cooldown_ticks = self._next_rabbit_spawn_cooldown()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0A120A"))
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        top_status_height = self._top_status_height()
        rabbit_lane_top = self._rabbit_lane_top()
        easter_egg_rect = self._easter_egg_text_rect()

        if self._active:
            painter.setFont(QFont("Monospace", 10))
            for col in self._columns:
                for row, char in enumerate(col["chars"]):
                    y = col["y"] + row * 14
                    if y < top_status_height + 8 or y > self.height() - 8:
                        continue
                    frac = (row + 1) / max(1, len(col["chars"]))
                    alpha = int(70 + frac * 120)
                    if y >= rabbit_lane_top - 6:
                        alpha = max(38, int(alpha * 0.45))
                    if row == len(col["chars"]) - 1:
                        painter.setPen(QColor(180, 255, 180, min(220, alpha + 30)))
                    else:
                        painter.setPen(QColor(40, 170, 70, alpha))
                    painter.drawText(col["x"], int(y), char)
        text_overlay_rect = easter_egg_rect.adjusted(-14, -5, 14, 5)
        painter.setPen(QColor(70, 150, 90, 40))
        painter.setBrush(QColor(6, 14, 6, 42))
        painter.drawRoundedRect(text_overlay_rect, 6, 6)
        self._draw_rabbit(painter)

        painter.setFont(QFont(FONT_MONO, 10))
        painter.setPen(QColor("#90EE90"))
        painter.drawText(
            QRect(0, 10, self.width(), 24),
            Qt.AlignmentFlag.AlignHCenter,
            "In attesa output backend..."
        )
        if self._idle_message:
            painter.setFont(QFont(FONT_MONO, 11, QFont.Weight.Bold))
            painter.setPen(QColor(110, 220, 130, 170))
            painter.drawText(
                easter_egg_rect,
                Qt.AlignmentFlag.AlignHCenter,
                self._idle_message
            )
        painter.end()


# ── Finestra principale ───────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ── Stato ─────────────────────────────────────────────────────────────
        self.worker         = None
        self._mode          = "youtube"
        self._local_file    = ""
        self._lang          = "it"
        self._timestamps    = False
        self._burn_subs     = False
        self._audio_normalize = False
        self._formats       = {"docx":True,"pdf":False,"txt":False,"srt":True,"vtt":False}
        self._whisper_model = "medium"
        self._history       = load_history()
        self._pulse_timer   = QTimer()
        self._pulse_timer.timeout.connect(self._pulse_progress)
        self._pulse_val     = 0
        self._pulse_dir     = 1
        self._progress_mode = ""
        self._last_transcript_chunk = ""
        self._backend_idle_timer = QTimer(self)
        self._backend_idle_timer.setSingleShot(True)
        self._backend_idle_timer.timeout.connect(self._show_backend_idle_if_quiet)
        self._backend_status = {}
        self._setup_process = None
        self._setup_process_label = ""
        self._closing_during_setup = False

        self.setWindowTitle(f"yt-transcriber v{APP_VERSION} — Studio GD LEX")
        self.setMinimumSize(1000, 860)
        self.resize(1100, 1050)
        self.setAcceptDrops(True)
        self._setup_style()
        self._build_ui()
        self._setup_single_instance_server()
        self._setup_tray()
        self._check_deps()
        self._update_tray_state()

    # ── Stile globale ─────────────────────────────────────────────────────────
    def _setup_style(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background:{BG}; }}
            QScrollArea {{ background:{BG}; border:none; }}
            QScrollBar:vertical {{ background:{BG2}; width:6px; border-radius:3px; }}
            QScrollBar::handle:vertical {{ background:{GREEN_MID}; border-radius:3px; min-height:20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0px; }}
            QPushButton {{
                font-family:{FONT_MONO}; font-size:11px;
                border-radius:3px; padding:8px 16px; border:none;
            }}
            QPushButton#primary {{
                background:{GREEN_DARK}; color:{WHITE}; border:1px solid {GREEN};
                font-size:15px; font-weight:bold; min-width:200px; min-height:48px;
            }}
            QPushButton#primary:hover   {{ background:{GREEN}; color:{BG}; }}
            QPushButton#primary:disabled {{ background:{BG2}; color:{MUTED}; border-color:{BORDER}; }}
            QPushButton#secondary {{
                background:{BG2}; color:{WHITE}; border:1px solid {BORDER};
            }}
            QPushButton#secondary:hover {{ border-color:{GREEN_MID}; color:{GREEN}; }}
            QPushButton#danger {{
                background:{BG2}; color:{RED}; border:1px solid #3A0000;
            }}
            QPushButton#danger:hover   {{ background:#1A0000; border-color:{RED}; }}
            QPushButton#danger:disabled {{ color:{MUTED}; border-color:{BORDER}; }}
            QProgressBar {{
                background:{BG2}; border:1px solid {BORDER}; border-radius:3px;
                min-height:18px; max-height:18px; text-align:center;
                font-family:{FONT_MONO}; font-size:12px; color:{WHITE}; font-weight:bold;
            }}
            QProgressBar::chunk {{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #003B00, stop:0.5 {GREEN_MID}, stop:1 {GREEN});
                border-radius:3px;
            }}
            QComboBox {{
                background:{BG3}; border:1.5px solid {BORDER}; border-radius:4px;
                padding:7px 12px; color:{WHITE}; font-family:{FONT_MONO}; font-size:12px;
            }}
            QComboBox:focus {{ border-color:{GREEN_MID}; }}
            QComboBox::drop-down {{ border:none; width:24px; }}
            QComboBox QAbstractItemView {{
                background:{BG2}; color:{WHITE}; border:1px solid {BORDER};
                selection-background-color:{GREEN_DARK}; selection-color:{GREEN};
                font-family:{FONT_MONO}; font-size:12px;
            }}
        """)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0,0,0,0)
        root.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(76)
        header.setStyleSheet(f"QFrame {{ background:{BG2}; border-bottom:1px solid {GREEN_MID}; }}")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(28,0,28,0)

        logo = QLabel()
        logo.setTextFormat(Qt.TextFormat.RichText)
        logo.setText(f"<span style='color:{WHITE};font-family:{FONT_MONO};font-size:28px;font-weight:bold;'>yt-<span style='color:{GREEN};'>transcriber</span></span>")
        logo.setStyleSheet("background:transparent;")
        ver_lbl = QLabel(f"v{APP_VERSION}")
        ver_lbl.setFont(QFont(FONT_MONO, 9))
        ver_lbl.setStyleSheet(f"color:{MUTED}; background:transparent; margin-top:10px;")
        sep = QLabel("  //  ")
        sep.setStyleSheet(f"color:{MUTED}; font-family:{FONT_MONO}; font-size:15px; background:transparent;")
        subtitle = QLabel("Pipeline Trascrizione Audio/Video  ·  Studio GD LEX")
        subtitle.setFont(QFont(FONT_MONO, 12))
        subtitle.setStyleSheet(f"color:{MUTED}; background:transparent;")
        self.dep_badge = QLabel()
        self.dep_badge.setFont(QFont(FONT_MONO, 11, QFont.Weight.Bold))

        hl.addWidget(logo); hl.addWidget(ver_lbl); hl.addWidget(sep)
        hl.addWidget(subtitle); hl.addStretch(); hl.addWidget(self.dep_badge)
        root.addWidget(header)

        # Scroll body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body_w = QWidget()
        body_w.setStyleSheet(f"background:{BG};")
        body = QVBoxLayout(body_w)
        body.setContentsMargins(24,14,24,14)
        body.setSpacing(10)
        scroll.setWidget(body_w)
        root.addWidget(scroll)

        # ── SORGENTE ──────────────────────────────────────────────────────────
        c, cv = make_card("SORGENTE")

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{ border:none; background:transparent; }}
            QTabBar::tab {{
                background:{BG}; color:{MUTED}; border:1px solid {BORDER};
                border-bottom:none; padding:6px 18px;
                font-family:{FONT_MONO}; font-size:12px; margin-right:2px;
            }}
            QTabBar::tab:selected {{ background:{BG2}; color:{GREEN}; border-color:{GREEN_MID}; }}
            QTabBar::tab:hover {{ color:{GREEN_DIM}; }}
        """)

        # Tab URL video
        yt_tab = QWidget(); yt_tab.setStyleSheet("background:transparent;")
        yt_l = QVBoxLayout(yt_tab); yt_l.setContentsMargins(0,10,0,0); yt_l.setSpacing(6)
        yt_l.addWidget(QLabel("URL VIDEO", styleSheet=f"color:{MUTED};font-family:{FONT_MONO};font-size:11px;letter-spacing:1px;background:transparent;"))
        self.url_input = MatrixInput("https://www.youtube.com/...   oppure   altro URL supportato da yt-dlp")
        self.url_input.textChanged.connect(self._on_url_changed)
        self.url_input.returnPressed.connect(self._run_if_ready)
        yt_l.addWidget(self.url_input)

        # Tab File locale
        local_tab = QWidget(); local_tab.setStyleSheet("background:transparent;")
        loc_l = QVBoxLayout(local_tab); loc_l.setContentsMargins(0,10,0,0); loc_l.setSpacing(6)
        loc_l.addWidget(QLabel("FILE AUDIO / VIDEO", styleSheet=f"color:{MUTED};font-family:{FONT_MONO};font-size:11px;letter-spacing:1px;background:transparent;"))
        file_row = QHBoxLayout(); file_row.setSpacing(8)
        self.file_input = MatrixInput("Seleziona un file audio o video…")
        self.file_input.textChanged.connect(self._on_file_changed)
        self.file_input.returnPressed.connect(self._run_if_ready)
        file_btn = QPushButton("sfoglia…"); file_btn.setObjectName("secondary")
        file_btn.setFixedWidth(88); file_btn.clicked.connect(self._browse_audio)
        file_row.addWidget(self.file_input); file_row.addWidget(file_btn)
        loc_l.addLayout(file_row)
        loc_l.addWidget(QLabel(
            "audio: mp3  wav  flac  ogg  opus  m4a  aac  wma  aiff    "
            "video: mp4  mkv  avi  mov  wmv  webm  flv  ts  3gp",
            styleSheet=f"color:{MUTED};font-family:{FONT_MONO};font-size:10px;background:transparent;"))

        self.tab_widget.addTab(yt_tab,    "▶  URL video")
        self.tab_widget.addTab(local_tab, "📁  File locale")
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        cv.addWidget(self.tab_widget)

        # Titolo + Output
        row2 = QHBoxLayout(); row2.setSpacing(12)
        col_t = QVBoxLayout(); col_t.setSpacing(4)
        col_t.addWidget(QLabel("TITOLO  (opzionale)", styleSheet=f"color:{MUTED};font-family:{FONT_MONO};font-size:11px;letter-spacing:1px;background:transparent;"))
        self.title_input = MatrixInput("Rilevato automaticamente")
        self.title_input.returnPressed.connect(self._run_if_ready)
        col_t.addWidget(self.title_input)
        col_o = QVBoxLayout(); col_o.setSpacing(4)
        col_o.addWidget(QLabel("CARTELLA OUTPUT", styleSheet=f"color:{MUTED};font-family:{FONT_MONO};font-size:11px;letter-spacing:1px;background:transparent;"))
        out_row = QHBoxLayout(); out_row.setSpacing(8)
        self.out_input = MatrixInput(str(DEFAULT_OUT))
        self.out_input.returnPressed.connect(self._run_if_ready)
        browse_btn = QPushButton("browse…"); browse_btn.setObjectName("secondary")
        browse_btn.setFixedWidth(88); browse_btn.clicked.connect(self._browse)
        out_row.addWidget(self.out_input); out_row.addWidget(browse_btn)
        col_o.addLayout(out_row)
        row2.addLayout(col_t,3); row2.addLayout(col_o,2)
        cv.addLayout(row2)
        body.addWidget(c)

        # ── PIPELINE ──────────────────────────────────────────────────────────
        cf, cfv = make_card("PIPELINE")
        fr = QHBoxLayout(); fr.setSpacing(6)
        self.badges = []
        for n,t in [(1,"sorgente"),(2,"prep.audio"),(3,"whisper GPU"),
                    (4,"pulitura"),(5,"docx"),(6,"lang:it")]:
            b = StepBadge(n,t)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            fr.addWidget(b); self.badges.append(b)
        cfv.addLayout(fr)
        body.addWidget(cf)

        # ── OPZIONI ───────────────────────────────────────────────────────────
        co, cov = make_card("OPZIONI")
        self.options_card = co
        opt_row = QHBoxLayout(); opt_row.setSpacing(12)

        # Lingua
        lang_col = QVBoxLayout(); lang_col.setSpacing(4)
        lang_col.addWidget(QLabel("LINGUA", styleSheet=f"color:{MUTED};font-family:{FONT_MONO};font-size:11px;letter-spacing:1px;background:transparent;"))
        self.lang_combo = QComboBox()
        self.lang_combo.setFont(QFont(FONT_MONO, 12))
        for flag, code, name in LANGUAGES:
            self.lang_combo.addItem(f"{flag}  {name}", code)
        for _i in range(self.lang_combo.count()):
            if self.lang_combo.itemData(_i) == "it":
                self.lang_combo.setCurrentIndex(_i); break
        self.lang_combo.currentIndexChanged.connect(
            lambda i: setattr(self, "_lang", self.lang_combo.itemData(i)))
        lang_col.addWidget(self.lang_combo)
        opt_row.addLayout(lang_col, 2)

        # Modello
        model_col = QVBoxLayout(); model_col.setSpacing(4)
        model_col.addWidget(QLabel("MODELLO WHISPER", styleSheet=f"color:{MUTED};font-family:{FONT_MONO};font-size:11px;letter-spacing:1px;background:transparent;"))
        self.model_combo = QComboBox()
        self.model_combo.setFont(QFont(FONT_MONO, 12))
        for code, label in WHISPER_MODELS:
            self.model_combo.addItem(label, code)
        self.model_combo.setCurrentIndex(0)
        def _on_model_changed(i):
            setattr(self, "_whisper_model", self.model_combo.itemData(i))
            self._check_deps()
        self.model_combo.currentIndexChanged.connect(_on_model_changed)
        model_col.addWidget(self.model_combo)
        opt_row.addLayout(model_col, 3)

        # Extra
        extra_col = QVBoxLayout(); extra_col.setSpacing(6)
        extra_col.addWidget(QLabel("EXTRA", styleSheet=f"color:{MUTED};font-family:{FONT_MONO};font-size:11px;letter-spacing:1px;background:transparent;"))
        extra_row = QHBoxLayout(); extra_row.setSpacing(8)
        self.ts_btn = toggle_btn("⏱  Timestamp")
        self.ts_btn.toggled.connect(lambda v: setattr(self, "_timestamps", v))
        self.burn_btn = toggle_btn("🎬  Brucia sottotitoli", enabled=False)
        self.burn_btn.toggled.connect(lambda v: setattr(self, "_burn_subs", v))
        extra_row.addWidget(self.ts_btn); extra_row.addWidget(self.burn_btn)
        extra_row.addStretch()
        extra_col.addLayout(extra_row)
        self.audio_normalize_btn = toggle_btn("Normalizza audio", checked=False)
        self.audio_normalize_btn.setToolTip(
            "Rende più uniforme il parlato in caso di audio basso, alto o irregolare. "
            "Lasciare disattivato se l’audio è già buono."
        )
        self.audio_normalize_btn.toggled.connect(self._on_audio_normalize_toggled)
        extra_col.addWidget(self.audio_normalize_btn)
        opt_row.addLayout(extra_col, 3)
        cov.addLayout(opt_row)

        # Formati output
        cov.addWidget(QLabel("FORMATO OUTPUT", styleSheet=f"color:{MUTED};font-family:{FONT_MONO};font-size:11px;letter-spacing:1px;background:transparent;margin-top:2px;"))
        fmt_row = QHBoxLayout(); fmt_row.setSpacing(8)
        self._fmt_btns = {}
        for fmt, default, label in [
            ("docx", True,  "📄  Word"),
            ("pdf",  False, "📕  PDF"),
            ("txt",  False, "📝  Testo"),
            ("srt",  True,  "💬  SRT"),
            ("vtt",  False, "🌐  VTT"),
        ]:
            btn = toggle_btn(label, checked=default)
            btn.toggled.connect(lambda v, f=fmt: self._on_fmt_changed(f, v))
            fmt_row.addWidget(btn)
            self._fmt_btns[fmt] = btn
        fmt_row.addStretch()
        cov.addLayout(fmt_row)
        body.addWidget(co)

        # ── PROGRESSO ─────────────────────────────────────────────────────────
        cp, cpv = make_card("PROGRESSO")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("  idle")
        cpv.addWidget(self.progress_bar)
        mr = QHBoxLayout()
        self.phase_lbl = QLabel("_", styleSheet=f"color:{WHITE};font-family:{FONT_MONO};font-size:12px;background:transparent;")
        self.eta_lbl   = QLabel("eta: --:--", styleSheet=f"color:{MUTED};font-family:{FONT_MONO};font-size:12px;background:transparent;")
        self.spd_lbl   = QLabel("", styleSheet=f"color:{GOLD};font-family:{FONT_MONO};font-size:11px;font-weight:bold;background:transparent;")
        mr.addWidget(self.phase_lbl); mr.addStretch()
        mr.addWidget(self.eta_lbl); mr.addSpacing(16); mr.addWidget(self.spd_lbl)
        cpv.addLayout(mr)
        body.addWidget(cp)

        # ── TRASCRIZIONE LIVE ───────────────────────────────────────────────
        ctl, ctlv = make_card("TRASCRIZIONE LIVE")
        self.transcript_view = QTextEdit()
        self.transcript_view.setReadOnly(True)
        self.transcript_view.setMinimumHeight(160)
        self.transcript_view.setPlaceholderText("Il testo riconosciuto comparirà qui durante la trascrizione.")
        self.transcript_view.setFont(QFont(FONT_MONO, 12))
        self.transcript_view.setStyleSheet(f"""
            QTextEdit {{
                background:#0A120A; color:{LIVE_TEXT};
                border:1px solid {GREEN_DARK}; border-radius:4px; padding:12px;
            }}
        """)
        ctlv.addWidget(self.transcript_view)
        body.addWidget(ctl)

        # ── LOG ───────────────────────────────────────────────────────────────
        cl2, clv = make_card("LOG")
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(130)
        self.log_view.setFont(QFont(FONT_MONO, 12))
        self.log_view.setStyleSheet(f"""
            QTextEdit {{
                background:#0A120A; color:{GREEN_DIM};
                border:1px solid {BORDER}; border-radius:4px; padding:12px;
            }}
        """)
        self.log_idle_view = MatrixRainWidget()
        self.log_stack = QStackedLayout()
        self.log_stack.setStackingMode(QStackedLayout.StackingMode.StackOne)
        self.log_stack.addWidget(self.log_view)
        self.log_stack.addWidget(self.log_idle_view)
        self.log_stack.setCurrentWidget(self.log_view)
        clv.addLayout(self.log_stack)
        body.addWidget(cl2)

        # ── CRONOLOGIA ────────────────────────────────────────────────────────
        ch, chv = make_card("CRONOLOGIA")
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(90)
        self.history_list.setFont(QFont(FONT_MONO, 10))
        self.history_list.setStyleSheet(f"""
            QListWidget {{ background:{BG3}; border:1px solid {BORDER};
                           border-radius:4px; color:{GREEN_DIM}; }}
            QListWidget::item {{ padding:3px 8px; }}
            QListWidget::item:selected {{ background:{GREEN_DARK}; color:{GREEN}; }}
            QListWidget::item:hover {{ background:#1A2A1A; }}
        """)
        self.history_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._history_menu)
        self.history_list.itemDoubleClicked.connect(self._history_load)
        self._refresh_history()
        chv.addWidget(self.history_list)
        chv.addWidget(QLabel("  doppio click per ricaricare  ·  tasto destro per opzioni",
            styleSheet=f"color:{MUTED};font-family:{FONT_MONO};font-size:9px;background:transparent;"))
        body.addWidget(ch)

        # ── FOOTER ────────────────────────────────────────────────────────────
        footer = QFrame()
        footer.setFixedHeight(72)
        footer.setStyleSheet(f"QFrame {{ background:{BG2}; border-top:1px solid {BORDER}; }}")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(28,0,28,0); fl.setSpacing(10)

        self.about_btn  = QPushButton("about");          self.about_btn.setObjectName("secondary")
        self.clear_btn  = QPushButton("clear log");      self.clear_btn.setObjectName("secondary")
        self.open_btn   = QPushButton("open output");    self.open_btn.setObjectName("secondary")
        self.claude_btn = QPushButton("🤖  Apri in Claude"); self.claude_btn.setObjectName("secondary")
        self.setup_backend_btn = QPushButton("Configura backend Whisper"); self.setup_backend_btn.setObjectName("secondary")
        self.cancel_btn = QPushButton("[ abort ]");      self.cancel_btn.setObjectName("danger")
        self.run_btn    = QPushButton("▶  AVVIA PIPELINE"); self.run_btn.setObjectName("primary")

        self.about_btn.clicked.connect(self._show_about)
        self.clear_btn.clicked.connect(self._clear_log)
        self.open_btn.clicked.connect(self._open_output)
        self.claude_btn.clicked.connect(self._open_claude)
        self.setup_backend_btn.clicked.connect(self._setup_backend)
        self.cancel_btn.clicked.connect(self._cancel)
        self.run_btn.clicked.connect(self._run)

        self.cancel_btn.setEnabled(False)
        self.claude_btn.setEnabled(False)
        self.setup_backend_btn.setVisible(False)
        self.run_btn.setEnabled(False)

        fl.addWidget(self.about_btn); fl.addWidget(self.clear_btn)
        fl.addWidget(self.open_btn);  fl.addWidget(self.claude_btn)
        fl.addWidget(self.setup_backend_btn)
        fl.addStretch()
        fl.addWidget(self.cancel_btn); fl.addSpacing(8); fl.addWidget(self.run_btn)
        root.addWidget(footer)

    # ── Pulse (barra indeterminata) ───────────────────────────────────────────
    def _pulse_progress(self):
        self._pulse_val += self._pulse_dir * 3
        if self._pulse_val >= 95: self._pulse_dir = -1
        elif self._pulse_val <= 5: self._pulse_dir = 1
        self.progress_bar.setValue(self._pulse_val)

    def _start_pulse(self, label=""):
        self.progress_bar.setFormat(f"  {label}…")
        self._pulse_val = 5; self._pulse_dir = 1
        self._pulse_timer.start(40)

    def _stop_pulse(self):
        self._pulse_timer.stop()

    # ── Deps ──────────────────────────────────────────────────────────────────
    def _resolve_backend_status(self):
        missing = []
        details = []
        issues = []
        backend_type = _BACKEND.get("type", "none")
        backend_label = _BACKEND.get("info", "non rilevato")
        uses_python_fallback = backend_type in {"faster_whisper", "faster_whisper_venv"}

        if not SCRIPT_SH.exists():
            missing.append("yt-transcriber.sh")
            details.append("script pipeline mancante")

        whisper_bin, bin_issues = resolve_whisper_bin()
        issues.extend(bin_issues)
        if whisper_bin is None and not uses_python_fallback:
            missing.append("whisper-cli")
            details.append("backend whisper-cli non configurato")

        model_path, model_label, model_issues = resolve_whisper_model(self._whisper_model)
        issues.extend(model_issues)
        if model_path is None and not uses_python_fallback:
            missing.append(model_label)
            details.append(f"modello {model_label} non configurato")

        if uses_python_fallback:
            details.append("fallback Python faster-whisper disponibile")

        return {
            "ready": not missing,
            "missing": missing,
            "details": details,
            "issues": issues,
            "bin_path": whisper_bin,
            "model_path": model_path,
            "model_label": model_label,
            "backend_type": backend_type,
            "backend_label": backend_label,
            "uses_python_fallback": uses_python_fallback,
        }

    def _backend_warning_message(self, status):
        lines = []
        missing = status.get("missing", [])
        if status.get("uses_python_fallback"):
            lines.append(f"Fallback Python disponibile: {status.get('backend_label', 'faster-whisper')}")
            lines.append("whisper.cpp non configurato: verra' usato faster-whisper")
            return "\n".join(lines)
        if missing:
            lines.append(f"missing: {', '.join(missing)}")
        if status.get("issues"):
            lines.extend(status["issues"])
        if missing:
            lines.append("Configura whisper.cpp oppure installa faster-whisper.")
            lines.append("In alternativa imposta:")
            lines.append(YT_TRANSCRIBER_WHISPER_BIN_ENV)
            lines.append(YT_TRANSCRIBER_WHISPER_MODEL_ENV)
        return "\n".join(lines)

    def _check_deps(self):
        status = self._resolve_backend_status()
        self._backend_status = status
        if status["ready"]:
            if status.get("uses_python_fallback"):
                self.dep_badge.setText(f"<> Backend Python: {status['backend_label']}")
                self.dep_badge.setStyleSheet(f"color:{WHITE};background:{GREEN_DARK};border:1px solid {GREEN_MID};border-radius:3px;padding:4px 12px;font-family:{FONT_MONO};")
                tooltip = (
                    f"backend: {status['backend_label']}\n"
                    "whisper.cpp non configurato: verra' usato faster-whisper"
                )
            else:
                binfo  = _BACKEND.get("info","?")
                bspeed = "(GPU)" if _BACKEND.get("fast") else "(CPU)"
                self.dep_badge.setText(f"<> {binfo} {bspeed}")
                self.dep_badge.setStyleSheet(f"color:{WHITE};background:{GREEN_DARK};border:1px solid {GREEN_MID};border-radius:3px;padding:4px 12px;font-family:{FONT_MONO};")
                tooltip = (
                    f"whisper-cli: {status['bin_path']}\n"
                    f"modello: {status['model_path']}"
                )
            self.dep_badge.setToolTip(tooltip)
        else:
            warning_text = self._backend_warning_message(status)
            self.dep_badge.setText(f"⚠  missing: {', '.join(status['missing'])}")
            self.dep_badge.setStyleSheet(f"color:{GOLD};background:#1A1000;border:1px solid {GOLD};border-radius:3px;padding:4px 12px;font-family:{FONT_MONO};")
            self.dep_badge.setToolTip(warning_text)
            self._log(f"⚠  {warning_text.replace(chr(10), ' | ')}", GOLD)
        whisper_cpp_script = resolve_setup_whisper_cpp_script()
        faster_script = resolve_setup_faster_whisper_script()
        show_setup_btn = (not status["ready"]) and (whisper_cpp_script is not None or faster_script is not None)
        self.setup_backend_btn.setVisible(show_setup_btn)
        self.setup_backend_btn.setEnabled(show_setup_btn and self._setup_process is None)
        if show_setup_btn:
            self.setup_backend_btn.setToolTip(
                "Configura whisper.cpp (consigliato) oppure faster-whisper (fallback)."
            )
        self._update_run_btn()

    # ── Slot UI ───────────────────────────────────────────────────────────────
    def _set_input_validity(self, widget, is_valid, has_text):
        if has_text and not is_valid:
            style = widget.styleSheet()
            style = style.replace(f"border: 1.5px solid {GREEN_MID}", f"border: 1.5px solid {RED}")
            style = style.replace(f"border: 1.5px solid {GREEN}", f"border: 1.5px solid {RED}")
            widget.setStyleSheet(style)
        else:
            widget._apply_style(widget.hasFocus())

    def _resolve_local_file(self, value):
        candidate = value.strip()
        if not candidate:
            return ""
        if len(candidate) >= 2 and candidate[0] == candidate[-1] and candidate[0] in {"'", '"'}:
            candidate = candidate[1:-1]
            if not candidate:
                return ""
        try:
            path = Path(candidate).expanduser()
        except Exception:
            return ""
        return str(path) if path.is_file() else ""

    def _is_supported_remote_url(self, value):
        candidate = value.strip()
        if not candidate:
            return False
        try:
            parsed = urlparse(candidate)
        except Exception:
            return False
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    def _on_url_changed(self, t):
        ok = self._is_supported_remote_url(t)
        self._set_input_validity(self.url_input, ok, bool(t.strip()))
        self._update_run_btn()

    def _on_file_changed(self, t):
        self._local_file = self._resolve_local_file(t)
        self._set_input_validity(self.file_input, bool(self._local_file), bool(t.strip()))
        self._update_run_btn()

    def _on_tab_changed(self, idx):
        self._mode = "youtube" if idx == 0 else "local"
        self.burn_btn.setEnabled(self._mode == "local")
        if self._mode != "local":
            self.burn_btn.setChecked(False)
        self._update_run_btn()

    def _update_run_btn(self):
        if self.worker and self.worker.isRunning():
            self.run_btn.setEnabled(False)
            if self.setup_backend_btn.isVisible():
                self.setup_backend_btn.setEnabled(False)
            self._update_tray_state()
            return
        if self._setup_process is not None:
            self.run_btn.setEnabled(False)
            if self.setup_backend_btn.isVisible():
                self.setup_backend_btn.setEnabled(False)
            self._update_tray_state()
            return
        if self._mode == "youtube":
            t = self.url_input.text().strip()
            ok = self._is_supported_remote_url(t)
        else:
            ok = bool(self._local_file)
        backend_ready = self._backend_status.get("ready", False)
        self.run_btn.setEnabled(ok and backend_ready)
        if not backend_ready:
            self.run_btn.setToolTip(self._backend_warning_message(self._backend_status))
        elif self._mode == "youtube" and not ok:
            self.run_btn.setToolTip("Inserisci un URL http/https valido.")
        elif self._mode == "local" and not ok:
            self.run_btn.setToolTip("Seleziona un file audio o video valido.")
        else:
            self.run_btn.setToolTip("Avvia la pipeline di trascrizione.")
        if self.setup_backend_btn.isVisible():
            self.setup_backend_btn.setEnabled(True)
        self._update_tray_state()

    def _on_fmt_changed(self, fmt, v):
        self._formats[fmt] = v
        if not any(self._formats.values()):
            self._formats["docx"] = True
            self._fmt_btns["docx"].setChecked(True)

    def _on_audio_normalize_toggled(self, checked):
        self._audio_normalize = checked

    def _run_if_ready(self):
        if self.worker and self.worker.isRunning():
            return
        if self.run_btn.isEnabled():
            self._run()

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self,"Output",str(DEFAULT_OUT))
        if d: self.out_input.setText(d)

    def _browse_audio(self):
        f, _ = QFileDialog.getOpenFileName(self,"File audio/video",str(Path.home()),AUDIO_FORMATS)
        if f:
            self.file_input.setText(f)
            if not self.title_input.text().strip():
                self.title_input.setText(Path(f).stem)

    def _setup_backend(self):
        if self._setup_process is not None:
            return

        box = QMessageBox(self)
        box.setWindowTitle("Configura backend Whisper")
        box.setText(
            "Scegli come configurare il backend Whisper.\n\n"
            "whisper.cpp: backend consigliato, usa whisper-cli e modelli ggml.\n"
            "faster-whisper: alternativa Python in venv utente, più semplice se whisper.cpp non è disponibile o non si compila."
        )
        whisper_btn = box.addButton("Installa whisper.cpp", QMessageBox.ButtonRole.AcceptRole)
        faster_btn = box.addButton("Installa faster-whisper", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = box.addButton("Annulla", QMessageBox.ButtonRole.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if clicked == cancel_btn or clicked is None:
            return
        if clicked == whisper_btn:
            script_path = resolve_setup_whisper_cpp_script()
            setup_label = "whisper.cpp"
            setup_note = (
                "Vuoi installare whisper.cpp in uno spazio utente dedicato e scaricare/verificare il modello selezionato?\n\n"
                "- non serve sudo\n"
                "- non viene modificato Python di sistema\n"
                "- verra' creato ~/.local/share/yt-transcriber/whisper.cpp\n"
                "- servono git, cmake, make e g++/c++\n"
                "- serve connessione internet\n"
                "- il download del modello puo' richiedere tempo"
            )
        elif clicked == faster_btn:
            script_path = resolve_setup_faster_whisper_script()
            setup_label = "faster-whisper"
            setup_note = (
                "Vuoi installare faster-whisper e scaricare/verificare il modello selezionato?\n\n"
                "- non serve sudo\n"
                "- non viene modificato Python di sistema\n"
                "- verra' creato ~/.local/share/yt-transcriber/venv\n"
                "- serve connessione internet\n"
                "- il download del modello puo' richiedere tempo"
            )
        else:
            return

        if script_path is None:
            QMessageBox.warning(self, "Configura backend Whisper", "Script di setup non trovato.")
            return

        answer = QMessageBox.question(
            self,
            f"Installa {setup_label}",
            setup_note,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self._log(f"▶  Avvio setup {setup_label}…", "#00FFFF")
        self._log(f"   script: {script_path}", MUTED)
        self._log(f"   modello: {self._whisper_model}", MUTED)
        self.setup_backend_btn.setEnabled(False)
        self.setup_backend_btn.setText("Setup in corso…")

        proc = QProcess(self)
        proc.setProgram("bash")
        proc.setArguments([str(script_path), self._whisper_model or "medium"])
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(self._on_setup_backend_output)
        proc.finished.connect(self._on_setup_backend_finished)
        self._setup_process = proc
        self._setup_process_label = setup_label
        proc.start()
        self._update_run_btn()

    def _on_setup_backend_output(self):
        if self._setup_process is None:
            return
        raw = bytes(self._setup_process.readAllStandardOutput()).decode("utf-8", errors="replace")
        for line in raw.splitlines():
            if line.strip():
                self._log(line, GREEN_DIM)

    def _on_setup_backend_finished(self, exit_code, exit_status):
        proc = self._setup_process
        if proc is not None:
            self._on_setup_backend_output()
            proc.deleteLater()
        self._setup_process = None
        setup_label = getattr(self, "_setup_process_label", "backend Whisper")
        self._setup_process_label = ""
        if self._closing_during_setup:
            return
        self.setup_backend_btn.setText("Configura backend Whisper")
        self._check_deps()

        if exit_status == QProcess.ExitStatus.NormalExit and exit_code == 0:
            self._log(f"✓  Setup {setup_label} completato.", GREEN)
            QMessageBox.information(
                self,
                "Setup completato",
                "Setup completato. Riavvia yt-transcriber per rilevare il nuovo backend."
            )
        else:
            self._log(f"✗  Setup {setup_label} fallito.", RED)
            QMessageBox.warning(
                self,
                "Configura backend Whisper",
                f"Setup {setup_label} fallito. Controlla il log e verifica requisiti e connessione internet."
            )

    def _clear_log(self):
        self._hide_backend_idle_animation()
        self.log_view.clear()

    def _clear_transcript(self):
        self.transcript_view.clear()
        self._last_transcript_chunk = ""

    def _app_icon(self):
        for candidate in (
            PIPELINE_DIR / "yt-transcriber.png",
            PIPELINE_DIR / "yt-transcriber_512.png",
            PIPELINE_DIR / "yt-transcriber.svg",
        ):
            if candidate.exists():
                icon = QIcon(str(candidate))
                if not icon.isNull():
                    return icon
        return QIcon.fromTheme("yt-transcriber")

    def _setup_single_instance_server(self):
        self.instance_server = QLocalServer(self)
        self.instance_server.newConnection.connect(self._on_single_instance_connection)
        if self.instance_server.listen(SINGLE_INSTANCE_SERVER_NAME):
            return
        QLocalServer.removeServer(SINGLE_INSTANCE_SERVER_NAME)
        if not self.instance_server.listen(SINGLE_INSTANCE_SERVER_NAME):
            self.instance_server.deleteLater()
            self.instance_server = None

    def _on_single_instance_connection(self):
        if self.instance_server is None:
            return
        while self.instance_server.hasPendingConnections():
            socket = self.instance_server.nextPendingConnection()
            if socket is None:
                continue
            socket.waitForReadyRead(250)
            message = bytes(socket.readAll()).decode("utf-8", errors="ignore").strip()
            if not message or "SHOW" in message:
                self._show_from_single_instance_request()
            socket.disconnectFromServer()

    def _show_from_single_instance_request(self):
        if not self.isVisible():
            self.show()
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _tray_icon(self):
        for candidate in (
            PIPELINE_DIR / "assets" / "tray" / "yt-transcriber-tray.svg",
        ):
            if candidate.exists():
                icon = QIcon(str(candidate))
                if not icon.isNull():
                    return icon
        themed_icon = QIcon.fromTheme("yt-transcriber")
        if not themed_icon.isNull():
            return themed_icon
        for candidate in (
            PIPELINE_DIR / "yt-transcriber.svg",
            PIPELINE_DIR / "yt-transcriber_512.png",
            PIPELINE_DIR / "yt-transcriber.png",
        ):
            if candidate.exists():
                icon = QIcon(str(candidate))
                if not icon.isNull():
                    return icon
        return QIcon()

    def _setup_tray(self):
        self.tray_icon = None
        self.tray_menu = None
        self.tray_toggle_action = None
        self.tray_run_action = None
        self.tray_cancel_action = None
        self.tray_open_output_action = None
        self.tray_open_folder_action = None
        self.tray_about_action = None
        self.tray_exit_action = None

        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self._tray_icon())
        self.tray_icon.setToolTip("yt-transcriber — pronto")
        self.tray_icon.activated.connect(self._on_tray_activated)

        self.tray_menu = QMenu(self)
        self.tray_menu.setStyleSheet(f"""
            QMenu {{ background:{BG2}; color:{WHITE}; border:1px solid {BORDER};
                     font-family:{FONT_MONO}; font-size:11px; }}
            QMenu::item:selected {{ background:{GREEN_DARK}; color:{GREEN}; }}
        """)
        self.tray_toggle_action = QAction("Mostra/Nascondi finestra", self)
        self.tray_run_action = QAction("Avvia pipeline", self)
        self.tray_cancel_action = QAction("Annulla pipeline", self)
        self.tray_open_folder_action = QAction("Apri cartella output", self)
        self.tray_about_action = QAction("About", self)
        self.tray_exit_action = QAction("Esci", self)

        self.tray_toggle_action.triggered.connect(self._toggle_window_visibility)
        self.tray_run_action.triggered.connect(self._run_if_ready)
        self.tray_cancel_action.triggered.connect(self._cancel)
        self.tray_open_folder_action.triggered.connect(self._open_output_folder)
        self.tray_about_action.triggered.connect(self._show_about)
        self.tray_exit_action.triggered.connect(self._quit_from_tray)

        self.tray_menu.addAction(self.tray_toggle_action)
        self.tray_menu.addAction(self.tray_run_action)
        self.tray_menu.addAction(self.tray_cancel_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.tray_open_folder_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.tray_about_action)
        self.tray_menu.addAction(self.tray_exit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

    def _toggle_window_visibility(self):
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.showNormal()
            self.raise_()
            self.activateWindow()

    def _on_tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._toggle_window_visibility()

    def _show_tray_message(self, title, message, icon=None):
        if self.tray_icon is None:
            return
        try:
            self.tray_icon.showMessage(
                title,
                message,
                icon or QSystemTrayIcon.MessageIcon.Information,
                3500,
            )
        except Exception:
            pass

    def _quit_from_tray(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(
                self,
                "Pipeline in corso",
                "Pipeline in corso. Annullare la pipeline prima di uscire."
            )
            self.showNormal()
            self.raise_()
            self.activateWindow()
            return
        self.close()

    def closeEvent(self, event):
        proc = self._setup_process
        if proc is None or proc.state() == QProcess.ProcessState.NotRunning:
            event.accept()
            return

        answer = QMessageBox.question(
            self,
            "Configura backend Whisper",
            "Setup backend in corso. Vuoi interromperlo e chiudere yt-transcriber?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            event.ignore()
            return

        self._closing_during_setup = True
        try:
            proc.terminate()
            if not proc.waitForFinished(3000):
                proc.kill()
                proc.waitForFinished(1000)
        except Exception:
            pass
        event.accept()

    def _update_tray_state(self):
        if self.tray_icon is None:
            return
        running = bool(self.worker and self.worker.isRunning())
        self.tray_run_action.setEnabled((not running) and self.run_btn.isEnabled())
        self.tray_cancel_action.setEnabled(running)
        self.tray_icon.setToolTip(
            "yt-transcriber — pipeline in esecuzione" if running else "yt-transcriber — pronto"
        )

    def _open_output(self):
        p = self.out_input.text() or str(DEFAULT_OUT)
        os.makedirs(p, exist_ok=True)
        subprocess.Popen(["xdg-open", p])

    def _open_output_folder(self):
        p = self.out_input.text().strip() or str(DEFAULT_OUT)
        try:
            target = Path(p).expanduser()
        except Exception:
            self._log("⚠  Cartella output non valida.", GOLD)
            return
        try:
            target.mkdir(parents=True, exist_ok=True)
        except Exception:
            self._log("⚠  Impossibile aprire la cartella output.", GOLD)
            return
        subprocess.Popen(["xdg-open", str(target)])

    def _open_claude(self):
        import webbrowser, shutil
        from pathlib import Path

        out_dir = Path(self.out_input.text() or str(DEFAULT_OUT))
        docx_files = sorted(out_dir.glob("*.docx"), key=lambda f: f.stat().st_mtime, reverse=True)

        if docx_files:
            latest = docx_files[0]
            if shutil.which("xclip"):
                result = subprocess.run(["xclip", "-selection", "clipboard"],
                                        input=str(latest), text=True)
                if result.returncode == 0:
                    self._log(f"→  percorso copiato negli appunti: {latest.name}", GREEN_DIM)
                else:
                    subprocess.Popen(["xdg-open", str(out_dir)])
                    self._log(f"→  xclip fallito (rc={result.returncode}) — cartella output aperta", GOLD)
            else:
                subprocess.Popen(["xdg-open", str(out_dir)])
                self._log(f"→  xclip non trovato — cartella output aperta ({latest.name})", GOLD)
        else:
            self._log("→  nessun file .docx trovato nella cartella output", GOLD)

        webbrowser.open("https://claude.ai")
        self._log("→  claude.ai aperto nel browser", GREEN_DIM)

    def _cancel(self):
        self._hide_backend_idle_animation()
        self._stop_pulse()
        if self.worker:
            self.worker.cancel()
        self.cancel_btn.setEnabled(False)
        self._log("⚠  Annullamento richiesto…", GOLD)
        self._update_tray_state()

    # ── Log ───────────────────────────────────────────────────────────────────
    def _restart_backend_idle_timer(self):
        if not ENABLE_BACKSTAGE_MATRIX_RAIN:
            return
        if self.worker and self.worker.isRunning():
            self._backend_idle_timer.start(BACKSTAGE_MATRIX_IDLE_MS)

    def _show_backend_idle_if_quiet(self):
        if not ENABLE_BACKSTAGE_MATRIX_RAIN:
            return
        if self.worker and self.worker.isRunning():
            self.log_stack.setCurrentWidget(self.log_idle_view)
            self.log_idle_view.start_animation()

    def _hide_backend_idle_animation(self):
        self._backend_idle_timer.stop()
        self.log_idle_view.stop_animation()
        self.log_stack.setCurrentWidget(self.log_view)

    def _log(self, text, color=None):
        self._hide_backend_idle_animation()
        c = color or GREEN_DIM
        cursor = self.log_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_view.setTextCursor(cursor)
        safe = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        self.log_view.insertHtml(f'<span style="color:{c};font-family:monospace;">{safe}</span><br>')
        cursor = self.log_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_view.setTextCursor(cursor)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())
        self.log_view.ensureCursorVisible()
        self._restart_backend_idle_timer()

    # ── Badges ────────────────────────────────────────────────────────────────
    def _reset_badges(self):
        for b in self.badges: b.set_state(StepBadge.IDLE)

    def _on_step(self, idx):
        last = len(self.badges) - 1
        for i, b in enumerate(self.badges):
            if i < idx:        b.set_state(StepBadge.DONE)
            elif i == idx:     b.set_state(StepBadge.DONE if idx==last else StepBadge.ACTIVE)
            else:              b.set_state(StepBadge.IDLE)

    # ── Pipeline ──────────────────────────────────────────────────────────────
    def _run(self):
        if self.worker and self.worker.isRunning():
            return

        if not self._backend_status.get("ready", False):
            warning_text = self._backend_warning_message(self._backend_status)
            self._log(f"⚠  {warning_text.replace(chr(10), ' | ')}", GOLD)
            QMessageBox.warning(self, "Backend Whisper mancante", warning_text)
            self._update_run_btn()
            return

        if self._mode == "local" and not self._local_file:
            self._log("✗  Percorso file locale non valido.", RED)
            self._update_run_btn()
            return

        title = self.title_input.text().strip()
        out   = Path(self.out_input.text().strip() or str(DEFAULT_OUT))
        out.mkdir(parents=True, exist_ok=True)

        self.options_card.hide()
        self.run_btn.setEnabled(False); self.cancel_btn.setEnabled(True)
        self.claude_btn.setEnabled(False)
        self.progress_bar.setValue(0); self.progress_bar.setFormat("  init…")
        self.phase_lbl.setText("init…"); self.spd_lbl.setText("")
        self.eta_lbl.setText("eta: --:--")
        self._progress_mode = ""
        self._reset_badges()
        self._clear_transcript()

        if self._mode == "youtube":
            url = self.url_input.text().strip()
            src_label = url
        else:
            url = f"LOCAL:{self._local_file}"
            src_label = Path(self._local_file).name
            if not title: title = Path(self._local_file).stem

        self._log(f"{'─'*54}", "#00FFFF")
        self._log(f"▶  {datetime.now().strftime('%H:%M:%S')}  start", "#00FFFF")
        self._log(f"   sorgente: {src_label}", MUTED)
        self._log(f"   modello:  {self._whisper_model}", MUTED)

        # Stima durata per file locali
        if self._mode == "local" and self._local_file:
            try:
                r = subprocess.run(
                    ["ffprobe","-v","error","-show_entries","format=duration",
                     "-of","default=noprint_wrappers=1:nokey=1", self._local_file],
                    capture_output=True, text=True)
                dur = float(r.stdout.strip())
                speed = {"medium":7,"large-v3":3,"small":15}.get(self._whisper_model,7)
                est = int(dur / speed)
                self._log(
                    f"   durata:   {int(dur//60)}m{int(dur%60)}s  →  stima ~{est//60}m{est%60:02d}s",
                    "#00FFFF")
            except Exception:
                pass

        self._log(f"{'─'*54}", "#00FFFF")

        self.worker = PipelineWorker(
            url, title, out,
            self._lang, self._timestamps, self._burn_subs,
            dict(self._formats), self._whisper_model, self._audio_normalize,
            whisper_bin=self._backend_status.get("bin_path"),
            whisper_model_path=self._backend_status.get("model_path"))
        self.worker.log_line.connect(self._on_log)
        self.worker.transcript_chunk.connect(self._on_transcript_chunk)
        self.worker.progress.connect(self._on_progress)
        self.worker.step_idx.connect(self._on_step)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
        self._restart_backend_idle_timer()
        self._update_tray_state()

    def _on_log(self, text, color):
        self._log(text, color)
        cl = text.lower()
        phases = {
            "download audio":           ("⬇  recupero audio…",           "pulse"),
            "file locale":              ("📁  file locale…",              "pulse"),
            "preparazione audio":       ("🔊  prep. audio…",              "pulse"),
            "analisi file audio":       ("🔊  analisi audio...",          "pulse"),
            "conversione audio in corso": ("🔊  conversione audio...",    "pulse"),
            "boost audio in corso":     ("🔊  boost audio...",            "pulse"),
            "estrazione audio":         ("🎬  estrazione audio…",         "pulse"),
            "normalizzazione audio in corso": ("🔊  normalizzazione audio...", "pulse"),
            "normalizzazione audio":    ("🔊  prep. audio…",              "pulse"),
            "verifica audio preparato": ("🔊  verifica audio...",         "pulse"),
            "preparazione audio completata": ("✓ audio pronto",            "status"),
            "trascrizione con whisper": ("⚙   whisper GPU transcribing…", "whisper"),
            "pulitura testo":           ("🧹  cleaning text…",            "pulse"),
            "generazione file word":    ("📄  generating .docx…",         "pulse"),
            "lingua italiana":          ("🇮🇹  setting lang: it-IT…",      "pulse"),
        }
        for kw, (lbl, mode) in phases.items():
            if kw in cl:
                self._progress_mode = "download" if kw == "download audio" else "whisper" if kw == "trascrizione con whisper" else mode
                self.phase_lbl.setText(lbl)
                if mode == "pulse":
                    self._stop_pulse()
                    self._start_pulse(lbl.split("  ")[1].rstrip("…"))
                elif mode == "whisper":
                    self._stop_pulse()
                    self.progress_bar.setValue(0)
                    self.progress_bar.setFormat("  0%")
                break

    def _on_progress(self, pct, eta, speed):
        self._stop_pulse()
        self.progress_bar.setValue(pct)
        if self._progress_mode == "download":
            self.progress_bar.setFormat(f"  Download video {pct}%")
        else:
            self.progress_bar.setFormat(f"  {pct}%")
        self.eta_lbl.setText(f"eta: {eta}")
        if speed:
            self.spd_lbl.setText(f"⚡ {speed} realtime" if "×" in speed else f"⚡ {speed}")
        else:
            self.spd_lbl.setText("")

    def _on_transcript_chunk(self, text):
        chunk = text.strip()
        if not chunk or chunk == self._last_transcript_chunk:
            return
        self._last_transcript_chunk = chunk
        cursor = self.transcript_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.transcript_view.setTextCursor(cursor)
        self.transcript_view.insertPlainText(chunk + "\n")
        cursor = self.transcript_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.transcript_view.setTextCursor(cursor)
        self.transcript_view.verticalScrollBar().setValue(
            self.transcript_view.verticalScrollBar().maximum()
        )
        self.transcript_view.ensureCursorVisible()

    def _on_finished(self, success, msg):
        self._hide_backend_idle_animation()
        self._stop_pulse()
        self.options_card.show()
        self.cancel_btn.setEnabled(False)
        finished_worker = self.worker
        self.worker = None
        self._update_run_btn()
        if finished_worker:
            finished_worker.deleteLater()
        if success:
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("  ✓  done")
            self.phase_lbl.setText("✓  pipeline completata")
            for b in self.badges: b.set_state(StepBadge.DONE)
            self._log(f"✓  {msg}", GREEN)
            self.claude_btn.setEnabled(True)
            output_dir = str(Path(self.out_input.text().strip() or str(DEFAULT_OUT)).expanduser())
            # Cronologia
            url = self.url_input.text().strip() if self._mode == "youtube" else f"LOCAL:{self._local_file}"
            title = self.title_input.text().strip() or "Senza titolo"
            self._add_to_history(url, title, output_dir)
            QMessageBox.information(self,"Done",
                f"{msg}\n\nFile salvati in:\n{output_dir}")
            self._show_tray_message(
                "yt-transcriber",
                "Pipeline completata",
                QSystemTrayIcon.MessageIcon.Information,
            )
        else:
            is_cancelled = msg == "Annullato."
            self.progress_bar.setFormat("  annullato" if is_cancelled else "  ✗  error")
            self.phase_lbl.setText(f"⚠  {msg}" if is_cancelled else f"✗  {msg}")
            self._log(f"⚠  {msg}" if is_cancelled else f"✗  {msg}", GOLD if is_cancelled else RED)
            if not is_cancelled:
                QMessageBox.warning(self,"Error",msg)
            self._show_tray_message(
                "yt-transcriber",
                "Pipeline annullata" if is_cancelled else "Errore pipeline",
                QSystemTrayIcon.MessageIcon.Warning if is_cancelled else QSystemTrayIcon.MessageIcon.Critical,
            )
        self._update_tray_state()

    # ── Cronologia ────────────────────────────────────────────────────────────
    def _refresh_history(self):
        self.history_list.clear()
        for item in reversed(self._history[-10:]):
            title = item.get("title", item.get("url","?"))[:60]
            date  = item.get("date","")[:10]
            wi = QListWidgetItem(f"  {date}  {title}")
            wi.setData(256, item)
            self.history_list.addItem(wi)

    def _history_load(self, item):
        data  = item.data(256)
        url   = data.get("url","")
        title = data.get("title","")
        out   = data.get("output", str(DEFAULT_OUT))
        if url.startswith("LOCAL:"):
            fpath = url[6:]
            self.tab_widget.setCurrentIndex(1)
            self.file_input.setText(fpath)
        else:
            self.tab_widget.setCurrentIndex(0)
            self.url_input.setText(url)
        self.title_input.setText(title)
        self.out_input.setText(out)
        self._log(f"→  Ricaricato: {title}", GREEN_DIM)

    def _history_menu(self, pos):
        item = self.history_list.itemAt(pos)
        if not item: return
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background:{BG2}; color:{WHITE}; border:1px solid {BORDER};
                     font-family:{FONT_MONO}; font-size:11px; }}
            QMenu::item:selected {{ background:{GREEN_DARK}; color:{GREEN}; }}
        """)
        load_act  = menu.addAction("↩  Ricarica")
        open_act  = menu.addAction("📂  Apri cartella output")
        menu.addSeparator()
        del_act   = menu.addAction("🗑  Rimuovi")
        clear_act = menu.addAction("✕  Cancella cronologia")
        action = menu.exec(self.history_list.mapToGlobal(pos))
        data = item.data(256)
        if action == load_act:   self._history_load(item)
        elif action == open_act:
            p = data.get("output", str(DEFAULT_OUT))
            os.makedirs(p, exist_ok=True)
            subprocess.Popen(["xdg-open", p])
        elif action == del_act:
            self._history = [h for h in self._history if h.get("url") != data.get("url")]
            save_history(self._history); self._refresh_history()
        elif action == clear_act:
            self._history = []; save_history(self._history); self._refresh_history()

    def _add_to_history(self, url, title, output):
        self._history = [h for h in self._history if h.get("url") != url]
        self._history.append({
            "url": url, "title": title, "output": str(output),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        save_history(self._history)
        self._refresh_history()

    # ── Drag & drop ───────────────────────────────────────────────────────────
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            u = event.mimeData().urls()
            if u:
                p = u[0].toLocalFile()
                ext = Path(p).suffix.lower()
                audio_exts = {".mp3",".wav",".flac",".ogg",".opus",".m4a",
                              ".aac",".wma",".aiff",".mka",".mp4",".mkv",
                              ".avi",".mov",".wmv",".webm",".flv",".ts",
                              ".mts",".m2ts",".vob",".3gp"}
                u_str = u[0].toString()
                if ext in audio_exts or u_str.startswith("http"):
                    event.acceptProposedAction(); return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls: return
        p = urls[0].toLocalFile()
        u = urls[0].toString()
        if p.startswith("http") or u.startswith("http"):
            self.tab_widget.setCurrentIndex(0)
            self.url_input.setText(p if p.startswith("http") else u)
            self._log("→  URL ricevuto via drag & drop", GREEN_DIM)
        else:
            self.tab_widget.setCurrentIndex(1)
            self.file_input.setText(p)
            if not self.title_input.text().strip():
                self.title_input.setText(Path(p).stem)
            self._log(f"→  File ricevuto via drag & drop: {Path(p).name}", GREEN_DIM)
            self._update_run_btn()

    # ── About ─────────────────────────────────────────────────────────────────
    def _show_about(self):
        box = QMessageBox(self)
        box.setWindowTitle("About yt-transcriber")
        box.setIcon(QMessageBox.Icon.NoIcon)
        box.setText(
            f"<div style='font-family:monospace;color:#E0FFE0;'>"
            f"<p style='font-size:18px;font-weight:bold;color:#00FF41;'>yt-transcriber</p>"
            f"<p style='color:#90EE90;'>Pipeline Trascrizione Audio/Video</p>"
            f"<p style='margin-top:12px;'><b style='color:#FFD700;'>Versione:</b> {APP_VERSION}</p>"
            f"<p><b style='color:#FFD700;'>Backend:</b> {_BACKEND.get('info','N/A')} "
            f"{'(GPU)' if _BACKEND.get('fast') else '(CPU)'}</p>"
            f"<p><b style='color:#FFD700;'>Autore:</b> {APP_AUTHOR}</p>"
            f"<p><b style='color:#FFD700;'>Anno:</b> {APP_YEAR}</p>"
            f"<hr style='border-color:#243A24;'/>"
            f"<p style='color:#4A6A4A;font-size:11px;'>Powered by Whisper.cpp · PyQt6 · ffmpeg · yt-dlp</p>"
            f"</div>"
        )
        box.setStyleSheet(f"""
            QMessageBox {{ background:#0F1A0F; }}
            QMessageBox QLabel {{ color:#E0FFE0; font-family:monospace; }}
            QPushButton {{ background:#1A3A1A; color:#E0FFE0;
                border:1px solid #243A24; border-radius:4px;
                padding:6px 20px; font-family:monospace; }}
            QPushButton:hover {{ background:#243A24; color:#00FF41; }}
        """)
        box.exec()


# ── Splash ────────────────────────────────────────────────────────────────────
def create_splash_frame(pct, col_state, W=640, H=360):
    import random
    CHARS = "01アイウエオカキクケコサシスセソタチツテトナニヌネノ"
    panel_w, panel_h = 440, 200
    px2, py2 = (W-panel_w)//2, (H-panel_h)//2
    bar_x, bar_y, bar_w, bar_h = px2+30, py2+panel_h-35, panel_w-60, 8

    px = QPixmap(W, H)
    px.fill(QColor("#0F1A0F"))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    col_w = 18
    for ci, col in enumerate(col_state):
        x = ci * col_w + 4
        drop_len = len(col["chars"])
        col["y"] += col["speed"]
        if col["y"] > H + drop_len*14:
            col["y"] = -drop_len*14
            col["chars"] = [random.choice(CHARS) for _ in range(random.randint(4,14))]
            col["speed"] = random.uniform(6,18)
        if random.random() < 0.3:
            col["chars"][-1] = random.choice(CHARS)
        for row in range(drop_len):
            y = int(col["y"]) + row*14
            if y < 0 or y > H: continue
            frac = (row+1)/drop_len
            alpha = int(255*frac)
            if row == drop_len-1:
                color = QColor(180,255,180,min(alpha,255))
                p.setFont(QFont("Monospace",11,QFont.Weight.Bold))
            else:
                g = int(60+frac*150)
                color = QColor(20,g,20,min(alpha,200))
                p.setFont(QFont("Monospace",11))
            p.setPen(QPen(color))
            p.drawText(x, y+12, col["chars"][row])

    p.setBrush(QBrush(QColor(15,30,15,225)))
    p.setPen(QPen(QColor("#00C832"),1))
    p.drawRect(px2, py2, panel_w, panel_h)
    p.setPen(QPen(QColor("#FFD700"),1))
    p.drawLine(px2+20, py2+panel_h-50, px2+panel_w-20, py2+panel_h-50)
    p.setFont(QFont("Monospace",36,QFont.Weight.Bold))
    p.setPen(QPen(QColor("#E0FFE0")))
    p.drawText(QRect(px2, py2+20, panel_w,60), Qt.AlignmentFlag.AlignHCenter, "yt-")
    p.setPen(QPen(QColor("#00FF41")))
    p.drawText(QRect(px2, py2+60, panel_w,60), Qt.AlignmentFlag.AlignHCenter, "transcriber")
    p.setFont(QFont("Monospace",10))
    p.setPen(QPen(QColor("#90EE90")))
    p.drawText(QRect(px2, py2+118, panel_w,30), Qt.AlignmentFlag.AlignHCenter,
               "Pipeline Trascrizione Audio/Video")
    p.setFont(QFont("Monospace",9,QFont.Weight.Bold))
    p.setPen(QPen(QColor("#FFD700")))
    p.drawText(QRect(px2, py2+148, panel_w,25), Qt.AlignmentFlag.AlignHCenter,
               "Studio GD LEX")
    p.setBrush(QBrush(QColor("#0F1A0F")))
    p.setPen(QPen(QColor("#243A24"),1))
    p.drawRect(bar_x, bar_y, bar_w, bar_h)
    fill_w = int((bar_w-2)*pct)
    if fill_w > 0:
        grad = QLinearGradient(bar_x+1,0,bar_x+1+fill_w,0)
        grad.setColorAt(0.0, QColor("#1A3A1A"))
        grad.setColorAt(0.6, QColor("#00C832"))
        grad.setColorAt(1.0, QColor("#00FF41"))
        p.setBrush(QBrush(grad)); p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(bar_x+1, bar_y+1, fill_w, bar_h-2)
    p.setFont(QFont("Monospace",8))
    p.setPen(QPen(QColor("#90EE90")))
    msgs = ["init…","loading modules…","checking deps…","ready"]
    msg = msgs[min(int(pct*len(msgs)),len(msgs)-1)]
    p.drawText(QRect(bar_x, bar_y+12, bar_w,16), Qt.AlignmentFlag.AlignHCenter, msg)
    p.setFont(QFont("Monospace",8))
    p.setPen(QPen(QColor("#4A6A4A")))
    p.drawText(QRect(0, H-18, W,16), Qt.AlignmentFlag.AlignRight, f"v{APP_VERSION}  ")
    p.end()
    return px


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    import random, time
    app = QApplication(sys.argv)
    app.setApplicationName("yt-transcriber")
    app.setOrganizationName("Studio GD LEX")
    app.setDesktopFileName("yt-transcriber")
    app.setStyle("Fusion")

    show_socket = QLocalSocket()
    show_socket.connectToServer(SINGLE_INSTANCE_SERVER_NAME)
    if show_socket.waitForConnected(250):
        show_socket.write(b"SHOW")
        show_socket.flush()
        show_socket.waitForBytesWritten(250)
        show_socket.disconnectFromServer()
        return 0

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,          QColor(BG))
    pal.setColor(QPalette.ColorRole.WindowText,      QColor(GREEN))
    pal.setColor(QPalette.ColorRole.Base,            QColor(BG2))
    pal.setColor(QPalette.ColorRole.AlternateBase,   QColor(BG3))
    pal.setColor(QPalette.ColorRole.Text,            QColor(GREEN))
    pal.setColor(QPalette.ColorRole.Highlight,       QColor(GREEN_DARK))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(GREEN))
    app.setPalette(pal)

    # Splash
    W, H = 640, 360
    col_w = 18
    random.seed(None)
    col_state = [{
        "chars": [random.choice("01アイウエオカキクケコ") for _ in range(random.randint(4,14))],
        "y":     random.randint(-200, H),
        "speed": random.uniform(6,18),
    } for _ in range(W//col_w)]

    splash = QSplashScreen(create_splash_frame(0, col_state),
                           Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    steps = 50
    for i in range(steps+1):
        splash.setPixmap(create_splash_frame(i/steps, col_state))
        app.processEvents()
        time.sleep(0.033)

    w = MainWindow()
    w.show()
    splash.finish(w)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
