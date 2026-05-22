#!/usr/bin/env bash
set -u

fail=0

ok() {
  echo "✅ $1"
}

ko() {
  echo "❌ $1"
  fail=1
}

run_check() {
  local label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    ok "$label"
  else
    ko "$label"
  fi
}

run_check "Sintassi bash: yt-transcriber.sh" bash -n yt-transcriber.sh
run_check "Sintassi bash: yt-transcriber" bash -n yt-transcriber
run_check "Sintassi bash: build_deb.sh" bash -n build_deb.sh

if [[ ! -e make_docx_styled.js ]]; then
  ko "Permessi DOCX: make_docx_styled.js non esiste"
elif [[ ! -r make_docx_styled.js ]]; then
  ko "Permessi DOCX: make_docx_styled.js non e leggibile"
else
  docx_mode=$(stat -c '%a' make_docx_styled.js 2>/dev/null || true)
  if [[ -z "$docx_mode" ]]; then
    ko "Permessi DOCX: impossibile leggere i permessi di make_docx_styled.js"
  elif (( (10#$docx_mode % 10) < 4 )); then
    ko "Permessi DOCX: make_docx_styled.js deve essere almeno world-readable (permessi attuali: $docx_mode)"
  else
    ok "Permessi DOCX: make_docx_styled.js presente, leggibile e world-readable ($docx_mode)"
  fi
fi

if python3 -m py_compile yt-transcriber_gui.py transcriber_backend.py platform_paths.py set_lang_it.py >/dev/null 2>&1; then
  ok "Python py_compile: yt-transcriber_gui.py, transcriber_backend.py, platform_paths.py, set_lang_it.py"
else
  ko "Python py_compile: yt-transcriber_gui.py, transcriber_backend.py, platform_paths.py, set_lang_it.py"
fi

run_check "Sintassi JavaScript: make_docx_styled.js" node --check make_docx_styled.js
run_check "Help wrapper: ./yt-transcriber --help" ./yt-transcriber --help
run_check "Help pipeline: bash yt-transcriber.sh --help" bash yt-transcriber.sh --help

if [[ -f package.json ]]; then
  ok "Presenza file: package.json"
else
  ko "Presenza file: package.json"
fi

app_version=$(sed -n 's/^APP_VERSION = "\([^"]*\)"$/\1/p' yt-transcriber_gui.py)
build_version=$(sed -n 's/^VERSION="\([^"]*\)"$/\1/p' build_deb.sh)
package_version=$(sed -n 's/^[[:space:]]*"version": "\([^"]*\)",$/\1/p' package.json | head -n1)
package_lock_version=$(sed -n 's/^[[:space:]]*"version": "\([^"]*\)",$/\1/p' package-lock.json | head -n1)

if [[ -n "$app_version" ]]; then
  ok "Lettura APP_VERSION: yt-transcriber_gui.py ($app_version)"
else
  ko "Lettura APP_VERSION: yt-transcriber_gui.py"
fi

if [[ -n "$app_version" && "$build_version" == "$app_version" ]]; then
  ok "Versione coerente: build_deb.sh == APP_VERSION ($app_version)"
else
  ko "Versione coerente: build_deb.sh == APP_VERSION"
fi

if [[ -n "$app_version" && "$package_version" == "$app_version" ]]; then
  ok "Versione coerente: package.json == APP_VERSION ($app_version)"
else
  ko "Versione coerente: package.json == APP_VERSION"
fi

if [[ -n "$app_version" && "$package_lock_version" == "$app_version" ]]; then
  ok "Versione coerente: package-lock.json == APP_VERSION ($app_version)"
else
  ko "Versione coerente: package-lock.json == APP_VERSION"
fi

if grep -qx 'Exec=yt-transcriber' yt-transcriber.desktop; then
  ok "Desktop entry: Exec=yt-transcriber"
else
  ko "Desktop entry: Exec=yt-transcriber"
fi

if grep -qx 'Icon=yt-transcriber' yt-transcriber.desktop; then
  ok "Desktop entry: Icon=yt-transcriber"
else
  ko "Desktop entry: Icon=yt-transcriber"
fi

if [[ -d node_modules/docx ]]; then
  ok "Presenza directory: node_modules/docx"
else
  ko "Presenza directory: node_modules/docx"
fi

for rabbit_frame in assets/matrix/white_rabbit_0.png \
                    assets/matrix/white_rabbit_1.png \
                    assets/matrix/white_rabbit_2.png \
                    assets/matrix/white_rabbit_3.png; do
  if [[ -f "$rabbit_frame" ]]; then
    ok "Presenza asset: $rabbit_frame"
  else
    ko "Presenza asset: $rabbit_frame"
  fi
done

if [[ -f assets/tray/yt-transcriber-tray.svg ]]; then
  ok "Presenza asset: assets/tray/yt-transcriber-tray.svg"
else
  ko "Presenza asset: assets/tray/yt-transcriber-tray.svg"
fi

run_check "Pipeline audio: AUDIO_NORMALIZE presente" grep -Fq 'AUDIO_NORMALIZE' yt-transcriber.sh
run_check "Pipeline audio: loudnorm presente" grep -Fq 'loudnorm' yt-transcriber.sh
run_check "Pipeline audio: AUDIO_PREP_STATUS presente" grep -Fq 'AUDIO_PREP_STATUS' yt-transcriber.sh
run_check "Pipeline Whisper: resolve_whisper_bin presente" grep -Fq 'resolve_whisper_bin()' yt-transcriber.sh
run_check "Pipeline Whisper: resolve_whisper_model_path presente" grep -Fq 'resolve_whisper_model_path()' yt-transcriber.sh
run_check "Pipeline Whisper: detect_python_backend presente" grep -Fq 'detect_python_backend()' yt-transcriber.sh
run_check "Pipeline Whisper: env YT_TRANSCRIBER_WHISPER_BIN presente" grep -Fq 'YT_TRANSCRIBER_WHISPER_BIN' yt-transcriber.sh
run_check "Pipeline Whisper: env YT_TRANSCRIBER_WHISPER_MODEL presente" grep -Fq 'YT_TRANSCRIBER_WHISPER_MODEL' yt-transcriber.sh
run_check "Pipeline Whisper: venv utente presente" grep -Fq '.local/share/yt-transcriber/venv' yt-transcriber.sh
run_check "Pipeline Whisper: whisper.cpp gestito dall'app presente" grep -Fq '.local/share/yt-transcriber/whisper.cpp' yt-transcriber.sh
run_check "Log audio: Preparazione audio" grep -Fq 'Preparazione audio' yt-transcriber.sh
run_check "Log audio: Analisi file audio" grep -Fq 'Analisi file audio' yt-transcriber.sh
run_check "Log audio: Nessun filtro audio applicato" grep -Fq 'Nessun filtro audio applicato' yt-transcriber.sh
run_check "Log audio: stato audio intermedio presente" grep -Eq 'Normalizzazione audio in corso|Conversione audio in corso|Boost audio in corso' yt-transcriber.sh
run_check "Log audio: Preparazione audio completata" grep -Fq 'Preparazione audio completata' yt-transcriber.sh
run_check "Log audio: Normalizzazione loudnorm applicata" grep -Fq 'Normalizzazione loudnorm applicata' yt-transcriber.sh
run_check "Log audio: Boost manuale applicato" grep -Fq 'Boost manuale applicato' yt-transcriber.sh

run_check "GUI->env: AUDIO_NORMALIZE presente" grep -Fq 'env["AUDIO_NORMALIZE"]' yt-transcriber_gui.py
run_check "GUI->env: WHISPER_BIN presente" grep -Fq 'env["WHISPER_BIN"]' yt-transcriber_gui.py
run_check "GUI->env: WHISPER_MODEL presente" grep -Fq 'env["WHISPER_MODEL"]' yt-transcriber_gui.py
run_check "GUI->env: YT_TRANSCRIBER_WHISPER_BIN presente" grep -Fq 'YT_TRANSCRIBER_WHISPER_BIN' yt-transcriber_gui.py
run_check "GUI->env: YT_TRANSCRIBER_WHISPER_MODEL presente" grep -Fq 'YT_TRANSCRIBER_WHISPER_MODEL' yt-transcriber_gui.py
run_check "GUI: AUDIO_PREP_STATUS presente" grep -Fq 'AUDIO_PREP_STATUS' yt-transcriber_gui.py
run_check "GUI Whisper: resolve_whisper_bin presente" grep -Fq 'def resolve_whisper_bin' yt-transcriber_gui.py
run_check "GUI Whisper: resolve_whisper_model presente" grep -Fq 'def resolve_whisper_model' yt-transcriber_gui.py
run_check "GUI Whisper: modello tiny presente" grep -Fq '("tiny",' yt-transcriber_gui.py
run_check "GUI Whisper: modello base presente" grep -Fq '("base",' yt-transcriber_gui.py
run_check "GUI Whisper: modello small presente" grep -Fq '("small",' yt-transcriber_gui.py
run_check "GUI Whisper: modello medium presente" grep -Fq '("medium",' yt-transcriber_gui.py
run_check "GUI Whisper: modello large presente" grep -Fq '("large",' yt-transcriber_gui.py
run_check "GUI Whisper: warning modello mancante presente" grep -Fq 'Modello whisper.cpp mancante:' yt-transcriber_gui.py
run_check "GUI Whisper: suggerimento installa modello presente" grep -Fq 'Installa il modello' yt-transcriber_gui.py
run_check "GUI Whisper: fallback faster-whisper presente" grep -Fq 'Fallback Python disponibile:' yt-transcriber_gui.py
run_check "GUI Whisper: warning backend mancante presente" grep -Fq 'Configura whisper.cpp oppure installa faster-whisper.' yt-transcriber_gui.py
run_check "GUI Whisper: pulsante setup presente" grep -Fq 'Configura backend Whisper' yt-transcriber_gui.py
run_check "GUI Whisper: resolve setup script presente" grep -Fq 'def resolve_setup_faster_whisper_script' yt-transcriber_gui.py
run_check "GUI Whisper: resolve whisper.cpp script presente" grep -Fq 'def resolve_setup_whisper_cpp_script' yt-transcriber_gui.py
run_check "GUI Whisper: scelta whisper.cpp presente" grep -Fq 'Installa whisper.cpp' yt-transcriber_gui.py
run_check "GUI Whisper: scelta faster-whisper presente" grep -Fq 'Installa faster-whisper' yt-transcriber_gui.py
run_check "GUI Whisper: dialog backend presente" grep -Fq 'Configura backend Whisper' yt-transcriber_gui.py
run_check "GUI Whisper: run button bloccato senza backend" grep -Fq 'self.run_btn.setEnabled(ok and backend_ready)' yt-transcriber_gui.py
run_check "GUI Whisper: closeEvent protegge setup attivo" grep -Fq 'Setup backend in corso. Vuoi interromperlo e chiudere yt-transcriber?' yt-transcriber_gui.py
run_check "Backend: whisper.cpp gestito dall'app presente" grep -Fq 'whisper.cpp (gestito dall'"'"'app)' transcriber_backend.py
run_check "Backend: helper normalizzazione modello presente" grep -Fq 'def _normalize_whisper_model_input' transcriber_backend.py
run_check "Backend: helper modello richiesto presente" grep -Fq 'def _requested_model_name' transcriber_backend.py
run_check "Backend: logica ggml app-managed presente" grep -Fq 'APP_WHISPER_MODEL = APP_WHISPER_CPP_DIR / "models" / APP_WHISPER_MODEL_NAME' transcriber_backend.py
run_check "Backend: faster-whisper venv utente presente" grep -Fq 'faster-whisper (venv utente)' transcriber_backend.py
run_check "Platform paths: file presente" test -f platform_paths.py
run_check "Platform paths: import in GUI presente" grep -Fq 'from platform_paths import (' yt-transcriber_gui.py
run_check "Platform paths: import in backend presente" grep -Fq 'from platform_paths import (' transcriber_backend.py
run_check "Backend Python: niente medium hardcoded in faster-whisper" bash -lc '! grep -Fq '\''WhisperModel("medium"'\'' transcriber_backend.py'
run_check "Backend Python: niente medium hardcoded in openai-whisper" bash -lc '! grep -Fq '\''load_model("medium")'\'' transcriber_backend.py'
run_check "Pipeline Whisper: preserva modello per backend Python" grep -Fq 'WHISPER_MODEL="$MODEL_NAME"' yt-transcriber.sh
run_check "Pipeline Whisper: log modello selezionato presente" grep -Fq 'Modello Whisper selezionato:' yt-transcriber.sh
if python3 - <<'PY' >/dev/null 2>&1
import re
from pathlib import Path

source = Path("yt-transcriber_gui.py").read_text(encoding="utf-8")
match = re.search(
    r"def _normalize_model_filename\(model_name\):\n(?P<body>(?:    .*\n)+)",
    source,
)
if not match:
    raise SystemExit(1)
namespace = {}
exec("def _normalize_model_filename(model_name):\n" + match.group("body"), namespace)
fn = namespace["_normalize_model_filename"]
expected = {
    "tiny": "ggml-tiny.bin",
    "base": "ggml-base.bin",
    "small": "ggml-small.bin",
    "medium": "ggml-medium.bin",
    "large": "ggml-large-v3.bin",
}
for model, filename in expected.items():
    if fn(model) != filename:
        raise SystemExit(1)
PY
then
  ok "Mapping ggml: tiny/base/small/medium/large"
else
  ko "Mapping ggml: tiny/base/small/medium/large"
fi
run_check "Setup whisper.cpp: script presente" test -f scripts/setup_whisper_cpp.sh
run_check "Setup whisper.cpp: normalizzazione modello presente" grep -Fq 'normalize_model_name()' scripts/setup_whisper_cpp.sh
run_check "Setup whisper.cpp: supporta tiny/base/small/medium" grep -Fq 'tiny|base|small|medium' scripts/setup_whisper_cpp.sh
run_check "Setup whisper.cpp: supporta large/large-v3" grep -Fq 'large|large-v3' scripts/setup_whisper_cpp.sh
run_check "Setup whisper.cpp: build path presente" grep -Fq '.local/share/yt-transcriber/whisper.cpp' scripts/setup_whisper_cpp.sh
run_check "Setup whisper.cpp: launcher presente" grep -Fq -- '--setup-whisper-cpp' build_deb.sh
run_check "Setup whisper.cpp: check-only presente" grep -Fq -- '--check-only' scripts/setup_whisper_cpp.sh
run_check "Setup whisper.cpp: check-only senza git clone" bash -lc '! awk '"'"'/CHECK_ONLY_START/,/CHECK_ONLY_END/'"'"' scripts/setup_whisper_cpp.sh | grep -Fq "git clone"'
run_check "Setup whisper.cpp: check-only senza cmake" bash -lc '! awk '"'"'/CHECK_ONLY_START/,/CHECK_ONLY_END/'"'"' scripts/setup_whisper_cpp.sh | grep -Fq "cmake"'
run_check "Setup whisper.cpp: niente sudo automatico" bash -lc '! grep -Eq "^[[:space:]]*sudo[[:space:]]" scripts/setup_whisper_cpp.sh'
run_check "Setup whisper.cpp: verifica runtime senza || true" bash -lc '! grep -Fq "\"$BIN_PATH\" --help >/dev/null 2>&1 || true" scripts/setup_whisper_cpp.sh'
run_check "Setup faster-whisper venv: script presente" test -f scripts/setup_faster_whisper_venv.sh
run_check "Setup faster-whisper venv: riferimento percorso presente" grep -Fq '.local/share/yt-transcriber/venv' scripts/setup_faster_whisper_venv.sh
run_check "Setup faster-whisper venv: MODEL_NAME presente" grep -Fq 'MODEL_NAME=' scripts/setup_faster_whisper_venv.sh
run_check "Setup faster-whisper venv: WhisperModel presente" grep -Fq 'WhisperModel' scripts/setup_faster_whisper_venv.sh
run_check "Setup faster-whisper venv: check-only presente" grep -Fq -- '--check-only' scripts/setup_faster_whisper_venv.sh
run_check "Setup faster-whisper venv: check-only senza pip install" bash -lc '! awk '"'"'/CHECK_ONLY_START/,/CHECK_ONLY_END/'"'"' scripts/setup_faster_whisper_venv.sh | grep -Fq "pip install"'
run_check "Setup faster-whisper venv: niente break-system-packages" bash -lc '! grep -RIn -- "--break-system-packages" transcriber_backend.py yt-transcriber.sh scripts/setup_faster_whisper_venv.sh'
run_check "Packaging: python3-venv presente in build_deb.sh" grep -Fq 'python3-venv' build_deb.sh
run_check "Packaging: platform_paths.py incluso nel .deb" grep -Fq 'cp "$SOURCE_DIR/platform_paths.py"' build_deb.sh
run_check "Packaging: setup whisper.cpp inoltra argomenti" grep -Fq 'exec bash "$APP_DIR/scripts/setup_whisper_cpp.sh" "$@"' build_deb.sh
run_check "Packaging: setup faster-whisper inoltra argomenti" grep -Fq 'exec bash "$APP_DIR/scripts/setup_faster_whisper_venv.sh" "$@"' build_deb.sh
run_check "README: setup whisper.cpp presente" grep -Fq 'yt-transcriber --setup-whisper-cpp' README.md
run_check "README: setup faster-whisper presente" grep -Fq 'yt-transcriber --setup-faster-whisper' README.md
run_check "README: check-only setup whisper.cpp presente" grep -Fq 'yt-transcriber --setup-whisper-cpp --check-only' README.md
run_check "README: check-only setup faster-whisper presente" grep -Fq 'yt-transcriber --setup-faster-whisper --check-only' README.md
run_check "GUI: toggle Normalizza audio presente" grep -Fq 'Normalizza audio' yt-transcriber_gui.py
run_check "GUI file locale: campo editabile/incollabile" grep -Fq 'self.file_input = MatrixInput("Seleziona un file audio o video…")' yt-transcriber_gui.py
run_check "GUI file locale: validazione is_file presente" grep -Fq 'path.is_file()' yt-transcriber_gui.py
run_check "GUI URL: validazione http/https presente" grep -Fq 'parsed.scheme in {"http", "https"}' yt-transcriber_gui.py
run_check "GUI download: YTDLP_PROGRESS presente" grep -Fq 'YTDLP_PROGRESS' yt-transcriber_gui.py
run_check "GUI download: split(\":\", 5) presente" grep -Fq 'split(":", 5)' yt-transcriber_gui.py
run_check "GUI download: _last_ytdlp_bucket presente" grep -Fq '_last_ytdlp_bucket' yt-transcriber_gui.py
run_check "GUI download: log Download video presente" grep -Fq 'Download video:' yt-transcriber_gui.py
run_check "GUI fasi: preparazione audio presente" grep -Fq 'preparazione audio' yt-transcriber_gui.py
run_check "GUI Matrix: WHITE_RABBIT presente" grep -Fq 'WHITE_RABBIT' yt-transcriber_gui.py
run_check "GUI Matrix: assets/matrix presente" grep -Fq 'assets" / "matrix"' yt-transcriber_gui.py
run_check "GUI Tray: yt-transcriber-tray.svg presente" grep -Fq 'yt-transcriber-tray.svg' yt-transcriber_gui.py
run_check "GUI single instance: QLocalServer presente" grep -Fq 'QLocalServer' yt-transcriber_gui.py
run_check "GUI single instance: QLocalSocket presente" grep -Fq 'QLocalSocket' yt-transcriber_gui.py
run_check "GUI single instance: SINGLE_INSTANCE_SERVER_NAME presente" grep -Fq 'SINGLE_INSTANCE_SERVER_NAME' yt-transcriber_gui.py
run_check "Live transcript: TRANSCRIPT_LIVE presente in pipeline" grep -Fq 'TRANSCRIPT_LIVE' yt-transcriber.sh
run_check "Live transcript: TRANSCRIPT_LIVE presente in GUI" grep -Fq 'TRANSCRIPT_LIVE' yt-transcriber_gui.py
run_check "Live transcript: transcript_chunk presente in GUI" grep -Fq 'transcript_chunk' yt-transcriber_gui.py
run_check "Live transcript: card TRASCRIZIONE LIVE presente in GUI" grep -Fq 'TRASCRIZIONE LIVE' yt-transcriber_gui.py

run_check "Standby: systemd-inhibit presente" grep -Fq 'systemd-inhibit' yt-transcriber.sh
run_check "Standby: sentinella YT_TRANSCRIBER_INHIBIT_ACTIVE presente" grep -Fq 'YT_TRANSCRIBER_INHIBIT_ACTIVE' yt-transcriber.sh
run_check "Standby: log Protezione standby attiva presente" grep -Fq 'Protezione standby attiva' yt-transcriber.sh
run_check "Download sorgente online: testo presente" grep -Fq 'Download audio da sorgente online' yt-transcriber.sh
run_check "Download video: --newline presente" grep -Fq -- '--newline' yt-transcriber.sh
run_check "Download video: --progress-template presente" grep -Fq -- '--progress-template' yt-transcriber.sh
run_check "Download video: prefisso YTDLP_PROGRESS presente" grep -Fq 'YTDLP_PROGRESS' yt-transcriber.sh
run_check "Packaging assets Matrix presenti" grep -Fq 'cp -r "$SOURCE_DIR/assets" "$BUILD_DIR/usr/lib/${PACKAGE}/"' build_deb.sh

if [[ $fail -eq 0 ]]; then
  printf "\nTutti i controlli smoke sono OK.\n"
  exit 0
else
  printf "\nUno o più controlli smoke hanno fallito.\n"
  exit 1
fi
