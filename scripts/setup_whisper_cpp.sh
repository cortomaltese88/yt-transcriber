#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${YT_TRANSCRIBER_APP_WHISPER_DIR:-$HOME/.local/share/yt-transcriber/whisper.cpp}"
CHECK_ONLY=0
MODEL_NAME="base"
if [[ "${1:-}" == "--check-only" ]]; then
  CHECK_ONLY=1
  shift
fi
if [[ -n "${1:-}" ]]; then
  MODEL_NAME="$1"
fi
BIN_PATH="$APP_DIR/build/bin/whisper-cli"
MODEL_PATH="$APP_DIR/models/ggml-${MODEL_NAME}.bin"
REPO_URL="https://github.com/ggml-org/whisper.cpp.git"

echo "==> Setup whisper.cpp in home utente"
echo "    repo: $APP_DIR"
echo "    modello: $MODEL_NAME"
if [[ $CHECK_ONLY -eq 1 ]]; then
  echo "    modalita': check-only"
fi

missing=()
for cmd in git cmake make; do
  command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
done
if ! command -v g++ >/dev/null 2>&1 && ! command -v c++ >/dev/null 2>&1; then
  missing+=("g++/c++")
fi
if [[ ${#missing[@]} -gt 0 ]]; then
  echo "ERRORE: mancano dipendenze di build: ${missing[*]}" >&2
  echo "Installa le dipendenze con: sudo apt install git cmake g++ make" >&2
  exit 1
fi

if [[ $CHECK_ONLY -eq 1 ]]; then
  # CHECK_ONLY_START
  echo "==> Check-only: nessuna modifica verra' eseguita"
  echo "    Binario atteso: $BIN_PATH"
  echo "    Modello atteso: $MODEL_PATH"
  if [[ -d "$APP_DIR" ]]; then
    echo "    Stato repo dir: presente"
  else
    echo "    Stato repo dir: assente"
  fi
  if [[ -x "$BIN_PATH" ]]; then
    echo "    Stato whisper-cli: presente"
  else
    echo "    Stato whisper-cli: assente"
  fi
  if [[ -f "$MODEL_PATH" ]]; then
    echo "    Stato modello: presente"
  else
    echo "    Stato modello: assente"
  fi
  # CHECK_ONLY_END
  exit 0
fi

mkdir -p "$(dirname "$APP_DIR")"

if [[ ! -d "$APP_DIR/.git" ]]; then
  echo "==> Clono whisper.cpp"
  git clone --depth 1 "$REPO_URL" "$APP_DIR"
else
  echo "==> Aggiorno whisper.cpp"
  git -C "$APP_DIR" fetch --depth 1 origin
  git -C "$APP_DIR" pull --ff-only
fi

echo "==> Compilo whisper.cpp (CPU)"
cmake -S "$APP_DIR" -B "$APP_DIR/build"
cmake --build "$APP_DIR/build" -j "${YT_TRANSCRIBER_BUILD_JOBS:-2}"

if [[ ! -x "$BIN_PATH" ]]; then
  echo "ERRORE: whisper-cli non trovato dopo la build: $BIN_PATH" >&2
  exit 1
fi

echo "==> Scarico/verifico modello ggml: $MODEL_NAME"
bash "$APP_DIR/models/download-ggml-model.sh" "$MODEL_NAME"

if [[ ! -f "$MODEL_PATH" ]]; then
  echo "ERRORE: modello non trovato dopo il download: $MODEL_PATH" >&2
  exit 1
fi

echo "==> Verifico whisper-cli"
set +e
help_output="$("$BIN_PATH" --help 2>&1)"
help_status=$?
set -e
if [[ $help_status -ne 0 && $help_status -ne 1 ]]; then
  echo "ERRORE: whisper-cli trovato ma non eseguibile correttamente" >&2
  if [[ -n "$help_output" ]]; then
    printf '%s\n' "$help_output" >&2
  fi
  exit 1
fi

echo "==> Completato"
echo "    Binario: $BIN_PATH"
echo "    Modello: $MODEL_PATH"
