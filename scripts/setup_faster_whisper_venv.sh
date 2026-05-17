#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="${YT_TRANSCRIBER_USER_VENV:-$HOME/.local/share/yt-transcriber/venv}"
VENV_PYTHON="$VENV_DIR/bin/python"
MODEL_NAME="${1:-medium}"

echo "==> Setup faster-whisper in venv utente"
echo "    venv: $VENV_DIR"
echo "    modello: $MODEL_NAME"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERRORE: python3 non trovato." >&2
  exit 1
fi

mkdir -p "$(dirname "$VENV_DIR")"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "==> Creo il venv utente"
  python3 -m venv "$VENV_DIR"
else
  echo "==> Venv gia' presente"
fi

echo "==> Aggiorno pip nel venv"
"$VENV_PYTHON" -m pip install --upgrade pip

echo "==> Installo faster-whisper nel venv"
"$VENV_PYTHON" -m pip install faster-whisper

echo "==> Verifico import faster_whisper"
"$VENV_PYTHON" -c "import faster_whisper; print('OK faster_whisper')"

echo "==> Scarico/verifico modello faster-whisper: $MODEL_NAME"
"$VENV_PYTHON" - "$MODEL_NAME" <<'PYEOF'
import sys
from faster_whisper import WhisperModel

model_name = sys.argv[1] if len(sys.argv) > 1 else "medium"
WhisperModel(model_name, device="cpu", compute_type="int8")
print("Modello pronto")
PYEOF

echo "==> Completato"
echo "    Python venv: $VENV_PYTHON"
echo "    Ora yt-transcriber puo' usare il fallback faster-whisper dal venv utente."
