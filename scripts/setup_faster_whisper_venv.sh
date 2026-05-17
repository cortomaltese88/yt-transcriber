#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="${YT_TRANSCRIBER_USER_VENV:-$HOME/.local/share/yt-transcriber/venv}"
VENV_PYTHON="$VENV_DIR/bin/python"

echo "==> Setup faster-whisper in venv utente"
echo "    venv: $VENV_DIR"

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

echo "==> Completato"
echo "    Python venv: $VENV_PYTHON"
echo "    Ora yt-transcriber puo' usare il fallback faster-whisper dal venv utente."
