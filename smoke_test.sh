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

if [[ -d node_modules/docx ]]; then
  ok "Presenza directory: node_modules/docx"
else
  ko "Presenza directory: node_modules/docx"
fi

if [[ $fail -eq 0 ]]; then
  echo "\nTutti i controlli smoke sono OK."
  exit 0
else
  echo "\nUno o più controlli smoke hanno fallito."
  exit 1
fi
