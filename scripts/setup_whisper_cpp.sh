#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${YT_TRANSCRIBER_APP_WHISPER_DIR:-$HOME/.local/share/yt-transcriber/whisper.cpp}"
CHECK_ONLY=0
MODEL_NAME="base"
APT_BASE_CMD="sudo apt install -y git cmake g++ make"
APT_ALL_CMD="sudo apt install -y git cmake g++ make mesa-vulkan-drivers vulkan-tools libvulkan-dev glslc spirv-headers spirv-tools"

normalize_model_name() {
  local raw="${1:-base}"
  case "$raw" in
    tiny|base|small|medium)
      echo "$raw"
      ;;
    large|large-v3)
      echo "large-v3"
      ;;
    *)
      echo ""
      ;;
  esac
}

if [[ "${1:-}" == "--check-only" ]]; then
  CHECK_ONLY=1
  shift
fi
if [[ -n "${1:-}" ]]; then
  MODEL_NAME="$1"
fi
MODEL_NAME_NORMALIZED="$(normalize_model_name "$MODEL_NAME")"
if [[ -z "$MODEL_NAME_NORMALIZED" ]]; then
  echo "ERRORE: modello non supportato: $MODEL_NAME" >&2
  echo "Usa uno tra: tiny, base, small, medium, large" >&2
  exit 1
fi
MODEL_NAME="$MODEL_NAME_NORMALIZED"
BIN_PATH="$APP_DIR/build/bin/whisper-cli"
MODEL_PATH="$APP_DIR/models/ggml-${MODEL_NAME}.bin"
REPO_URL="https://github.com/ggml-org/whisper.cpp.git"

is_linux() {
  [[ "$(uname -s 2>/dev/null || true)" == "Linux" ]]
}

has_vulkan_runtime() {
  command -v vulkaninfo >/dev/null 2>&1 && vulkaninfo --summary >/dev/null 2>&1
}

missing_vulkan_deps() {
  local missing=()
  command -v vulkaninfo >/dev/null 2>&1 || missing+=("vulkan-tools")
  command -v glslc >/dev/null 2>&1 || missing+=("glslc")
  command -v spirv-as >/dev/null 2>&1 || missing+=("spirv-tools")
  [[ -f /usr/include/vulkan/vulkan.h ]] || missing+=("libvulkan-dev")
  if ! ldconfig -p 2>/dev/null | grep -Fq "libvulkan.so"; then
    [[ -e /usr/lib/x86_64-linux-gnu/libvulkan.so || -e /usr/lib64/libvulkan.so ]] || missing+=("libvulkan-dev")
  fi
  printf '%s\n' "${missing[@]}"
}

vulkan_build_artifact_present() {
  find "$APP_DIR/build" -name 'libggml-vulkan.so*' -print -quit 2>/dev/null | grep -q .
}

build_whisper_cpu() {
  echo "==> Compilo whisper.cpp (CPU)"
  cmake -S "$APP_DIR" -B "$APP_DIR/build"
  cmake --build "$APP_DIR/build" -j "${YT_TRANSCRIBER_BUILD_JOBS:-2}"
}

build_whisper_vulkan() {
  echo "==> Compilo whisper.cpp (GPU/Vulkan)"
  cmake -S "$APP_DIR" -B "$APP_DIR/build" -DGGML_VULKAN=ON
  cmake --build "$APP_DIR/build" -j "${YT_TRANSCRIBER_BUILD_JOBS:-2}"
}

echo "==> Setup whisper.cpp in home utente"
echo "    repo: $APP_DIR"
echo "    modello: $MODEL_NAME"
if [[ "$MODEL_NAME" == "large-v3" ]]; then
  echo "    alias richiesto: large -> large-v3"
fi
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
  echo "Installa le dipendenze con: $APT_BASE_CMD" >&2
  exit 1
fi

VULKAN_READY=0
if is_linux; then
  mapfile -t missing_vulkan < <(missing_vulkan_deps)
  if [[ ${#missing_vulkan[@]} -eq 0 ]] && has_vulkan_runtime; then
    VULKAN_READY=1
  else
    echo "==> Vulkan non pronto: verra' usata la build CPU se necessario"
    if [[ ${#missing_vulkan[@]} -gt 0 ]]; then
      echo "    Dipendenze Vulkan mancanti: ${missing_vulkan[*]}"
    else
      echo "    Runtime Vulkan non rilevato da vulkaninfo"
    fi
    echo "    Per abilitare GPU/Vulkan su Kubuntu:"
    echo "    $APT_ALL_CMD"
  fi
fi

if [[ $CHECK_ONLY -eq 1 ]]; then
  # CHECK_ONLY_START
  echo "==> Check-only: nessuna modifica verra' eseguita"
  echo "    Binario atteso: $BIN_PATH"
  echo "    Modello atteso: $MODEL_PATH"
  if [[ $VULKAN_READY -eq 1 ]]; then
    echo "    Stato Vulkan: disponibile"
  else
    echo "    Stato Vulkan: non disponibile"
  fi
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

if [[ $VULKAN_READY -eq 1 ]]; then
  set +e
  build_whisper_vulkan
  build_status=$?
  set -e
  if [[ $build_status -eq 0 ]] && vulkan_build_artifact_present; then
    echo "==> Build Vulkan completata"
  else
    echo "ATTENZIONE: build Vulkan fallita o libreria Vulkan non trovata; fallback CPU" >&2
    build_whisper_cpu
  fi
else
  build_whisper_cpu
fi

if [[ ! -x "$BIN_PATH" ]]; then
  echo "ERRORE: whisper-cli non trovato dopo la build: $BIN_PATH" >&2
  exit 1
fi

if [[ -f "$MODEL_PATH" ]]; then
  echo "==> Modello gia' presente, download saltato: $MODEL_PATH"
else
  echo "==> Scarico/verifico modello ggml: $MODEL_NAME"
  bash "$APP_DIR/models/download-ggml-model.sh" "$MODEL_NAME"
fi

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
