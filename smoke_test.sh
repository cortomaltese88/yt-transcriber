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

if python3 -m py_compile yt-transcriber_gui.py transcriber_backend.py set_lang_it.py >/dev/null 2>&1; then
  ok "Python py_compile: yt-transcriber_gui.py, transcriber_backend.py, set_lang_it.py"
else
  ko "Python py_compile: yt-transcriber_gui.py, transcriber_backend.py, set_lang_it.py"
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

run_check "Pipeline audio: AUDIO_NORMALIZE presente" grep -Fq 'AUDIO_NORMALIZE' yt-transcriber.sh
run_check "Pipeline audio: loudnorm presente" grep -Fq 'loudnorm' yt-transcriber.sh
run_check "Log audio: Preparazione audio" grep -Fq 'Preparazione audio' yt-transcriber.sh
run_check "Log audio: Nessun filtro audio applicato" grep -Fq 'Nessun filtro audio applicato' yt-transcriber.sh
run_check "Log audio: Normalizzazione loudnorm applicata" grep -Fq 'Normalizzazione loudnorm applicata' yt-transcriber.sh
run_check "Log audio: Boost manuale applicato" grep -Fq 'Boost manuale applicato' yt-transcriber.sh

run_check "GUI->env: AUDIO_NORMALIZE presente" grep -Fq 'env["AUDIO_NORMALIZE"]' yt-transcriber_gui.py
run_check "GUI: toggle Normalizza audio presente" grep -Fq 'Normalizza audio' yt-transcriber_gui.py
run_check "GUI download: YTDLP_PROGRESS presente" grep -Fq 'YTDLP_PROGRESS' yt-transcriber_gui.py
run_check "GUI download: split(\":\", 5) presente" grep -Fq 'split(":", 5)' yt-transcriber_gui.py
run_check "GUI download: _last_ytdlp_bucket presente" grep -Fq '_last_ytdlp_bucket' yt-transcriber_gui.py
run_check "GUI download: log Download YouTube presente" grep -Fq 'Download YouTube:' yt-transcriber_gui.py
run_check "GUI fasi: preparazione audio presente" grep -Fq 'preparazione audio' yt-transcriber_gui.py
run_check "Live transcript: TRANSCRIPT_LIVE presente in pipeline" grep -Fq 'TRANSCRIPT_LIVE' yt-transcriber.sh
run_check "Live transcript: TRANSCRIPT_LIVE presente in GUI" grep -Fq 'TRANSCRIPT_LIVE' yt-transcriber_gui.py
run_check "Live transcript: transcript_chunk presente in GUI" grep -Fq 'transcript_chunk' yt-transcriber_gui.py
run_check "Live transcript: card TRASCRIZIONE LIVE presente in GUI" grep -Fq 'TRASCRIZIONE LIVE' yt-transcriber_gui.py

run_check "Standby: systemd-inhibit presente" grep -Fq 'systemd-inhibit' yt-transcriber.sh
run_check "Standby: sentinella YT_TRANSCRIBER_INHIBIT_ACTIVE presente" grep -Fq 'YT_TRANSCRIBER_INHIBIT_ACTIVE' yt-transcriber.sh
run_check "Standby: log Protezione standby attiva presente" grep -Fq 'Protezione standby attiva' yt-transcriber.sh
run_check "Download YouTube: --newline presente" grep -Fq -- '--newline' yt-transcriber.sh
run_check "Download YouTube: --progress-template presente" grep -Fq -- '--progress-template' yt-transcriber.sh
run_check "Download YouTube: prefisso YTDLP_PROGRESS presente" grep -Fq 'YTDLP_PROGRESS' yt-transcriber.sh

if [[ $fail -eq 0 ]]; then
  printf "\nTutti i controlli smoke sono OK.\n"
  exit 0
else
  printf "\nUno o più controlli smoke hanno fallito.\n"
  exit 1
fi
