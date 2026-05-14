#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# yt-transcriber — Pipeline trascrizione video online → .docx
#
# USAGE:
#   yt-transcriber.sh <URL_video> [titolo] [cartella_output]
#
# DIPENDENZE:
#   yt-dlp, ffmpeg, whisper.cpp (build-vulkan), node + docx, python3
#
# CONFIGURAZIONE (modifica le variabili qui sotto):
#   WHISPER_BIN   percorso binario whisper-cli (build Vulkan)
#   WHISPER_MODEL percorso modello ggml
#   WORK_DIR      cartella di lavoro temporanea
#   OUTPUT_DIR    cartella output finale (default: ~/Trascrizioni)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Configurazione ────────────────────────────────────────────────────────────
WHISPER_BIN="${WHISPER_BIN:-$HOME/whisper.cpp/build-vulkan/bin/whisper-cli}"
WHISPER_MODEL="${WHISPER_MODEL:-$HOME/whisper.cpp/models/ggml-medium.bin}"
PIPELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="${WORK_DIR:-/tmp/yt-transcriber_work}"
OUTPUT_DIR="${3:-$HOME/Trascrizioni}"
LANG="${WHISPER_LANG:-it}"
VOLUME_BOOST="${VOLUME_BOOST:-1.0}"
AUDIO_NORMALIZE="${AUDIO_NORMALIZE:-0}"
LOUDNORM_I="${LOUDNORM_I:--20}"
LOUDNORM_TP="${LOUDNORM_TP:--2}"
LOUDNORM_LRA="${LOUDNORM_LRA:-11}"

resolve_model_bin() {
  local model_input="${1:-}"
  if [[ -z "$model_input" ]]; then
    model_input="medium"
  fi
  if [[ "$model_input" == */* || "$model_input" == *.bin ]]; then
    echo "$model_input"
  else
    echo "$HOME/whisper.cpp/models/ggml-${model_input}.bin"
  fi
}

resolve_model_name() {
  local model_input="${1:-}"
  if [[ -z "$model_input" ]]; then
    echo "medium"
    return
  fi
  if [[ "$model_input" == */* || "$model_input" == *.bin ]]; then
    local base
    base="$(basename "$model_input")"
    base="${base#ggml-}"
    echo "${base%.bin}"
  else
    echo "$model_input"
  fi
}

# ── Colori ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

# ── Funzioni UI ───────────────────────────────────────────────────────────────
banner() {
  echo -e "\n${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BOLD}${BLUE}  yt-transcriber — Pipeline Trascrizione Video${NC}"
  echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

step() { echo -e "\n${BOLD}${CYAN}▶ $1${NC}"; }
ok()   { echo -e "${GREEN}  ✓ $1${NC}"; }
warn() { echo -e "${YELLOW}  ⚠ $1${NC}"; }
err()  { echo -e "${RED}  ✗ $1${NC}" >&2; exit 1; }

show_help() {
  cat << EOF
yt-transcriber.sh — Pipeline trascrizione

USO:
  yt-transcriber.sh <URL_video> [titolo] [output_dir]
  yt-transcriber.sh --local <file_audio_video> [titolo] [output_dir]
  yt-transcriber.sh --help

VARIABILI D'AMBIENTE:
  OUTPUT_DIR      Cartella output (default: ~/Trascrizioni)
  AUDIO_NORMALIZE Abilita loudnorm con ffmpeg se =1 (default: 0)
  VOLUME_BOOST    Amplificazione manuale (default: 1.0, usata solo se AUDIO_NORMALIZE=0)
  LOUDNORM_I      Parametro avanzato loudnorm (default: -20)
  LOUDNORM_TP     Parametro avanzato loudnorm (default: -2)
  LOUDNORM_LRA    Parametro avanzato loudnorm (default: 11)
  WHISPER_LANG    Lingua Whisper (default: it)
  WHISPER_BIN     Percorso whisper-cli
  WHISPER_MODEL   Modello (small/medium/large-v3) o path .bin (default: medium)
EOF
}

# ── Barra progresso whisper ───────────────────────────────────────────────────
# whisper.cpp scrive righe tipo: [00:01:23 --> 00:01:27] testo
# usiamo questo per calcolare percentuale ed ETA
watch_progress() {
  local logfile="$1"
  local total_sec="$2"
  local start_ts
  start_ts=$(date +%s)
  local last_pct=0

  while true; do
    if [[ ! -f "$logfile" ]]; then sleep 1; continue; fi

    # leggi l'ultimo timestamp dal log
    local last_ts
    last_ts=$(grep -oP '^\[\d{2}:\d{2}:\d{2}' "$logfile" 2>/dev/null | tail -1 | tr -d '[' || true)

    if [[ -n "$last_ts" ]]; then
      IFS=':' read -r hh mm ss <<< "$last_ts"
      local cur_sec=$(( 10#$hh * 3600 + 10#$mm * 60 + 10#$ss ))
      local pct=$(( cur_sec * 100 / total_sec ))
      [[ $pct -gt 100 ]] && pct=100

      local elapsed=$(( $(date +%s) - start_ts ))
      local eta="--:--"
      if [[ $pct -gt 2 ]]; then
        local remaining=$(( elapsed * (100 - pct) / pct ))
        local em=$(( remaining / 60 ))
        local es=$(( remaining % 60 ))
        eta=$(printf "%02d:%02d" $em $es)
      fi

      # barra visuale 40 caratteri
      local filled=$(( pct * 40 / 100 ))
      local bar=""
      for ((i=0; i<filled; i++)); do bar+="█"; done
      for ((i=filled; i<40; i++)); do bar+="░"; done

      local speed="--"
      if [[ $elapsed -gt 0 && $cur_sec -gt 0 ]]; then
        speed=$(echo "scale=1; $cur_sec / $elapsed" | bc 2>/dev/null || echo "--")
      fi

      printf "\r  ${CYAN}[%s]${NC} ${BOLD}%3d%%${NC}  ETA ${YELLOW}%s${NC}  velocità ${GREEN}%sx${NC}   " \
        "$bar" "$pct" "$eta" "$speed"
      # Riga strutturata per la GUI (parsed dal worker Python)
      echo "PROGRESS:${pct}:${eta}:${speed}"
    fi

    # controlla se whisper è terminato
    if ! kill -0 "$WHISPER_PID" 2>/dev/null; then
      printf "\r  ${GREEN}[████████████████████████████████████████]${NC} ${BOLD}100%%${NC}  ${GREEN}✓ Completato${NC}              \n"
      break
    fi

    sleep 2
  done
}

# ── Verifica dipendenze ───────────────────────────────────────────────────────
check_deps() {
  step "Verifica dipendenze"
  local ok=1
  for cmd in yt-dlp ffmpeg ffprobe node python3 bc; do
    if command -v "$cmd" &>/dev/null; then ok "$cmd"; else warn "$cmd non trovato"; ok=0; fi
  done
  if [[ ! -x "$WHISPER_BIN" ]]; then
    warn "whisper-cli non trovato: $WHISPER_BIN"
    ok=0
  else
    ok "whisper-cli (Vulkan)"
  fi
  local model_input
  model_input="${WHISPER_MODEL:-medium}"
  local check_model
  check_model="$(resolve_model_bin "$model_input")"
  if [[ ! -f "$check_model" ]]; then
    if [[ "$model_input" == */* || "$model_input" == *.bin ]]; then
      warn "modello .bin esplicito non trovato: $check_model"
      ok=0
    else
      warn "modello non trovato: $check_model (verrà scaricato automaticamente)"
    fi
  else
    ok "modello $(basename $check_model)"
  fi
  if [[ $ok -eq 0 ]]; then
    err "Dipendenze mancanti. Controlla la configurazione."
  fi
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
  if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    show_help
    exit 0
  fi

  if [[ "${YT_TRANSCRIBER_INHIBIT_ACTIVE:-0}" != "1" ]]; then
    if command -v systemd-inhibit &>/dev/null; then
      if systemd-inhibit \
        --what=sleep:idle \
        --who="yt-transcriber" \
        --why="yt-transcriber sta trascrivendo un audio/video" \
        --mode=block \
        true >/dev/null 2>&1; then
        echo "▶ Protezione standby attiva: systemd-inhibit (sleep:idle)"
        exec env YT_TRANSCRIBER_INHIBIT_ACTIVE=1 \
          systemd-inhibit \
            --what=sleep:idle \
            --who="yt-transcriber" \
            --why="yt-transcriber sta trascrivendo un audio/video" \
            --mode=block \
            bash "$0" "$@"
      else
        warn "Protezione standby non disponibile: systemd-inhibit presente ma non utilizzabile"
      fi
    else
      warn "Protezione standby non disponibile: systemd-inhibit non trovato"
    fi
  fi

  banner

  # ── Parsing argomenti ────────────────────────────────────────────────────
  local is_local=0
  local local_file=""
  local url=""
  local title=""

  if [[ "${1:-}" == "--local" ]]; then
    is_local=1
    local_file="${2:-}"
    title="${3:-}"
    OUTPUT_DIR="${4:-$HOME/Trascrizioni}"
    [[ -z "$local_file" ]] && err "Uso: yt-transcriber.sh --local <file> [titolo] [output_dir]"
    [[ ! -f "$local_file" ]] && err "File non trovato: $local_file"
  else
    url="${1:-}"
    title="${2:-}"
    [[ -z "$url" ]] && err "Uso: yt-transcriber.sh <URL_video> [titolo] [output_dir]"
  fi

  # Cartelle (pulisce la work dir per evitare residui di run precedenti)
  rm -rf "$WORK_DIR"
  mkdir -p "$WORK_DIR" "$OUTPUT_DIR"
  local today
  today=$(date +%Y%m%d)

  check_deps

  # ── Step 1: Sorgente audio ────────────────────────────────────────────────
  local raw_audio="$WORK_DIR/audio_raw.mp3"

  if [[ $is_local -eq 1 ]]; then
    step "File locale"
    [[ -z "$title" ]] && title="$(basename "${local_file%.*}")"
    raw_audio="$local_file"
    ok "File: $(du -sh "$raw_audio" | cut -f1)"
  else
    step "Download audio da sorgente online"
    local ytdlp_status=0
    set +e
    yt-dlp -x --audio-format mp3 --audio-quality 0 \
      --newline \
      --progress-template "download:YTDLP_PROGRESS:%(progress._percent_str)s:%(progress._downloaded_bytes_str)s:%(progress._total_bytes_str)s:%(progress._speed_str)s:%(progress._eta_str)s" \
      --output "$WORK_DIR/audio_raw.%(ext)s" \
      --print-to-file title "$WORK_DIR/video_title.txt" \
      "$url" 2>&1 | while IFS= read -r line; do
        case "$line" in
          YTDLP_PROGRESS:*|\[download\]*|\[ExtractAudio\]*|ERROR:*|WARNING:*|\[error\]*|\[warning\]*|*" ERROR:"*|*" WARNING:"*)
            printf '%s\n' "$line"
            ;;
        esac
      done
    ytdlp_status=${PIPESTATUS[0]}
    set -e
    [[ $ytdlp_status -eq 0 ]] || err "Download sorgente online fallito (yt-dlp exit $ytdlp_status)"

    # Recupera titolo dal video se non fornito
    if [[ -z "$title" && -f "$WORK_DIR/video_title.txt" ]]; then
      title=$(head -1 "$WORK_DIR/video_title.txt" | tr -d '\n')
    fi
    [[ -z "$title" ]] && title="Video_$(date +%Y%m%d_%H%M%S)"

    # Trova il file mp3 scaricato (yt-dlp può variare il nome)
    if [[ ! -f "$raw_audio" ]]; then
      raw_audio=$(find "$WORK_DIR" -name "*.mp3" | head -1)
    fi
    [[ ! -f "$raw_audio" ]] && err "Download audio fallito"
    ok "Audio scaricato: $(du -sh "$raw_audio" | cut -f1)"
  fi

  # ── Step 2: Preparazione audio ─────────────────────────────────────────────
  step "Preparazione audio"
  printf 'AUDIO_PREP_STATUS:%s\n' "Analisi file audio..."
  local loud_audio="$WORK_DIR/audio_loud.mp3"
  if [[ "$AUDIO_NORMALIZE" == "1" ]]; then
    printf 'AUDIO_PREP_STATUS:%s\n' "Normalizzazione audio in corso..."
    ffmpeg -y -i "$raw_audio" \
      -filter:a "loudnorm=I=${LOUDNORM_I}:TP=${LOUDNORM_TP}:LRA=${LOUDNORM_LRA}" \
      "$loud_audio" -loglevel warning
    ok "Normalizzazione loudnorm applicata"
  elif [[ "$VOLUME_BOOST" != "1.0" ]]; then
    printf 'AUDIO_PREP_STATUS:%s\n' "Boost audio in corso..."
    ffmpeg -y -i "$raw_audio" -filter:a "volume=${VOLUME_BOOST}" \
      "$loud_audio" -loglevel warning
    ok "Boost manuale applicato: volume=${VOLUME_BOOST}"
  else
    printf 'AUDIO_PREP_STATUS:%s\n' "Conversione audio in corso..."
    ffmpeg -y -i "$raw_audio" "$loud_audio" -loglevel warning
    ok "Nessun filtro audio applicato"
  fi

  # Calcola durata in secondi per la barra progresso
  printf 'AUDIO_PREP_STATUS:%s\n' "Verifica audio preparato..."
  local total_sec
  total_sec=$(ffprobe -v error -show_entries format=duration \
    -of default=noprint_wrappers=1:nokey=1 "$loud_audio" 2>/dev/null | cut -d. -f1)
  local total_min=$(( total_sec / 60 ))
  local total_s=$(( total_sec % 60 ))
  ok "Durata audio: ${total_min}m${total_s}s"
  printf 'AUDIO_PREP_STATUS:%s\n' "Preparazione audio completata"

  # ── Step 3: Trascrizione Whisper ───────────────────────────────────────────
  local LANG="${WHISPER_LANG:-it}"
  local MODEL_INPUT
  MODEL_INPUT="${WHISPER_MODEL:-medium}"
  local MODEL_NAME
  MODEL_NAME="$(resolve_model_name "$MODEL_INPUT")"
  local WITH_TS="${WHISPER_TIMESTAMPS:-0}"
  local BURN_SUBS="${WHISPER_BURN_SUBS:-0}"

  local lang_label="$LANG"
  [[ -z "$LANG" ]] && lang_label="auto"
  step "Trascrizione con Whisper.cpp (Vulkan GPU, lingua: ${lang_label})"

  local srt_base="$WORK_DIR/transcript"
  local srt_file="${srt_base}.srt"
  local whisper_log="$WORK_DIR/whisper.log"

  # Verifica modello:
  # - nome modello (es. medium): path standard + download automatico se assente
  # - path .bin avanzato: deve esistere, nessun download automatico
  local MODEL_BIN
  MODEL_BIN="$(resolve_model_bin "$MODEL_INPUT")"
  if [[ "$MODEL_INPUT" == */* || "$MODEL_INPUT" == *.bin ]]; then
    [[ -f "$MODEL_BIN" ]] || err "WHISPER_MODEL punta a un file .bin inesistente: $MODEL_BIN"
  else
    if [[ ! -f "$MODEL_BIN" ]]; then
      step "Download modello Whisper: ${MODEL_NAME}"
      bash "$HOME/whisper.cpp/models/download-ggml-model.sh" "$MODEL_NAME" || \
        err "Download modello ${MODEL_NAME} fallito"
    fi
  fi
  WHISPER_MODEL="$MODEL_BIN"

  # Rileva backend migliore disponibile
  local BACKEND_INFO
  BACKEND_INFO=$(python3 "$PIPELINE_DIR/transcriber_backend.py" 2>/dev/null | grep "Backend:" | awk -F': ' '{print $2}')
  ok "Backend: ${BACKEND_INFO:-rilevamento in corso…}"

  # Controlla se usare whisper.cpp o python backend
  local USE_WHISPER_CPP=0
  for bin_path in     "${WHISPER_BIN:-}"     "$HOME/whisper.cpp/build-vulkan/bin/whisper-cli"     "$HOME/whisper.cpp/build-cuda/bin/whisper-cli"     "$HOME/whisper.cpp/build/bin/whisper-cli"; do
    if [[ -n "$bin_path" && -x "$bin_path" && -f "$WHISPER_MODEL" ]]; then
      WHISPER_BIN_ACTIVE="$bin_path"
      USE_WHISPER_CPP=1
      break
    fi
  done

  if [[ $USE_WHISPER_CPP -eq 1 ]]; then
    # ── whisper.cpp ──────────────────────────────────────────────────────────
    local lang_arg=""
    [[ -n "$LANG" ]] && lang_arg="-l $LANG"

    : > "$whisper_log"
    (
      if command -v stdbuf &>/dev/null; then
        stdbuf -oL -eL \
          "$WHISPER_BIN_ACTIVE" \
          -m "$MODEL_BIN" \
          $lang_arg \
          -f "$loud_audio" \
          -osrt \
          -of "$srt_base" \
          --threads 8
      else
        "$WHISPER_BIN_ACTIVE" \
          -m "$MODEL_BIN" \
          $lang_arg \
          -f "$loud_audio" \
          -osrt \
          -of "$srt_base" \
          --threads 8
      fi
    ) 2>&1 | tee "$whisper_log" | while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      if [[ "$line" =~ ^\[[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{3})?[[:space:]]+--\>[[:space:]]+[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{3})?\][[:space:]]+(.+)$ ]]; then
        transcript_text="${BASH_REMATCH[3]}"
        transcript_text="${transcript_text#"${transcript_text%%[![:space:]]*}"}"
        transcript_text="${transcript_text%"${transcript_text##*[![:space:]]}"}"
        [[ -z "$transcript_text" ]] && continue
        [[ "$transcript_text" =~ ^\[[^]]+\]$ ]] && continue
        printf 'TRANSCRIPT_LIVE:%s\n' "$transcript_text"
      fi
    done &
    WHISPER_PID=$!
    watch_progress "$whisper_log" "$total_sec"
    wait $WHISPER_PID
    local exit_code=$?
    [[ $exit_code -ne 0 ]] && err "Whisper terminato con errore (exit $exit_code). Log: $whisper_log"
  else
    # ── Python backend (faster-whisper / openai-whisper) ─────────────────────
    warn "whisper.cpp non trovato — uso backend Python (più lento)"
    PIPELINE_DIR_PY="$PIPELINE_DIR" python3 - "$loud_audio" "$srt_file" "$LANG" << 'PYEOF'
import sys
import os
sys.path.insert(0, os.environ["PIPELINE_DIR_PY"])
try:
    from transcriber_backend import transcribe, detect_backend
    backend = detect_backend()
    print(f"Backend: {backend['info']}", flush=True)
    ok = transcribe(
        sys.argv[1], sys.argv[2],
        lang=sys.argv[3] if sys.argv[3] else "it",
        backend=backend,
        log_callback=lambda l,c: print(l, flush=True)
    )
    sys.exit(0 if ok else 1)
except ImportError:
    import subprocess, sys as _sys
    subprocess.run([_sys.executable, "-m", "pip", "install",
                    "faster-whisper", "--break-system-packages", "-q"])
    from faster_whisper import WhisperModel
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    lang = sys.argv[3] if sys.argv[3] else None
    segments, info = model.transcribe(sys.argv[1], language=lang)
    lines = []
    for i, seg in enumerate(segments):
        ms = lambda t: f"{int(t//3600):02d}:{int((t%3600)//60):02d}:{int(t%60):02d},{int((t%1)*1000):03d}"
        lines.append(f"{i+1}\n{ms(seg.start)} --> {ms(seg.end)}\n{seg.text.strip()}\n")
        print(f"[{int(seg.end//3600):02d}:{int((seg.end%3600)//60):02d}:{int(seg.end%60):02d}] {seg.text.strip()}", flush=True)
    open(sys.argv[2], 'w').write("\n".join(lines))
PYEOF
    [[ $? -ne 0 ]] && err "Trascrizione Python fallita"
  fi

  [[ ! -f "$srt_file" ]] && err "File SRT non generato: $srt_file"
  ok "Trascrizione completata: $srt_file"

  # Titolo sicuro per nomi file (necessario anche per BURN_SUBS prima di riga output)
  local safe_title
  safe_title=$(echo "$title" | sed 's/[^a-zA-Z0-9àèéìòùÀÈÉÌÒÙ _-]//g' | \
    sed 's/ \+/_/g' | cut -c1-50)

  # ── Sottotitoli: burn-in nel video (solo modalità locale) ─────────────────
  if [[ "${BURN_SUBS}" == "1" && $is_local -eq 1 ]]; then
    step "Burn-in sottotitoli nel video"
    local ext="${local_file##*.}"
    local burned_out="$OUTPUT_DIR/${today}_${safe_title}_sottotitolato.${ext}"
    ffmpeg -y -i "$local_file" \
      -vf "subtitles=${srt_file}:force_style='FontName=Arial,FontSize=18,PrimaryColour=&HFFFFFF,BackColour=&H80000000,Bold=1'" \
      -c:a copy \
      "$burned_out" -loglevel warning && \
      ok "Video con sottotitoli: $burned_out" || \
      warn "Burn-in fallito — il file video originale è invariato"
  fi

  # ── Step 4: Estrai testo dal SRT ──────────────────────────────────────────
  step "Pulitura testo"
  local raw_txt="$WORK_DIR/transcript_raw.txt"
  python3 - "$srt_file" "$raw_txt" "${WITH_TS}" << 'PYEOF'
import re, sys

with open(sys.argv[1], encoding='utf-8') as f:
    content = f.read()

with_ts = sys.argv[3] == '1' if len(sys.argv) > 3 else False

lines = content.split('\n')
text_lines = []
i = 0
while i < len(lines):
    line = lines[i].strip()
    if not line or re.match(r'^\d+$', line):
        i += 1
        continue
    if 'Amara.org' in line or 'Sottotitoli creati' in line:
        i += 1
        continue
    # Timestamp
    ts_match = re.match(r'^(\d{2}:\d{2}:\d{2}),\d+ --> \d{2}:\d{2}:\d{2},\d+', line)
    if ts_match:
        ts = ts_match.group(1)
        if with_ts and text_lines:
            text_lines.append(f'\n[{ts}]')
        elif with_ts and not text_lines:
            text_lines.append(f'[{ts}]')
        i += 1
        continue
    line = re.sub(r'<[^>]+>', '', line).strip()
    if line:
        text_lines.append(line)
    i += 1

if with_ts:
    raw = ' '.join(text_lines)
else:
    raw = ' '.join(text_lines)

# Normalizzazioni comuni
fixes = {
    'Thyssenkrupp': 'ThyssenKrupp', 'thyssenkrupp': 'ThyssenKrupp',
    'D.Lgs 231': 'D.Lgs. 231/2001', 'd.lgs 231': 'D.Lgs. 231/2001',
    'decreto 231': 'D.Lgs. 231/2001', 'Decreto 231': 'D.Lgs. 231/2001',
}
for wrong, right in fixes.items():
    raw = raw.replace(wrong, right)

with open(sys.argv[2], 'w', encoding='utf-8') as f:
    f.write(raw)

print(f"Parole: {len(raw.split())}")
PYEOF
  local word_count
  word_count=$(wc -w < "$raw_txt")
  ok "Testo estratto: ${word_count} parole"

  # ── Step 5: Genera output nei formati selezionati ─────────────────────────
  step "Generazione file di output"

  local OUT_DOCX="${OUT_DOCX:-1}"
  local OUT_PDF="${OUT_PDF:-0}"
  local OUT_TXT="${OUT_TXT:-0}"
  local OUT_SRT="${OUT_SRT:-0}"
  local OUT_VTT="${OUT_VTT:-0}"

  local out_transcript="$OUTPUT_DIR/${today}_${safe_title}_trascrizione.docx"

  # Il riassunto viene prodotto da Claude — non generiamo un placeholder inutile

  # Crea trascrizione txt formattata
  {
    echo "$title"
    [[ -n "$url" ]] && echo "$url"
    echo ""
    cat "$raw_txt"
  } > "$WORK_DIR/transcript.txt"

  # .docx
  if [[ "$OUT_DOCX" == "1" ]]; then
    local node_out node_exit=0
    node_out=$(NODE_PATH="$PIPELINE_DIR/node_modules" \
      node "$PIPELINE_DIR/make_docx_styled.js" \
        "$WORK_DIR/transcript.txt" \
        "$OUTPUT_DIR/" 2>&1) || node_exit=$?
    [[ -n "$node_out" ]] && echo "$node_out" | grep -v "^$" || true
    [[ $node_exit -eq 0 ]] || err "make_docx_styled.js fallito (exit $node_exit)"
    local generated_t
    generated_t=$(find "$OUTPUT_DIR" -name "${today}_*_trascrizione.docx" -newer "$loud_audio" | head -1)
    if [[ -n "$generated_t" && "$generated_t" != "$out_transcript" ]]; then
      mv "$generated_t" "$out_transcript" 2>/dev/null || true
    fi
    ok ".docx generato"
  fi

  # .txt
  if [[ "$OUT_TXT" == "1" ]]; then
    local out_txt="$OUTPUT_DIR/${today}_${safe_title}_trascrizione.txt"
    cp "$raw_txt" "$out_txt"
    ok ".txt generato"
  fi

  # .srt
  if [[ "$OUT_SRT" == "1" ]]; then
    local out_srt="$OUTPUT_DIR/${today}_${safe_title}.srt"
    cp "$srt_file" "$out_srt"
    ok ".srt copiato"
  fi

  # .vtt (conversione da srt)
  if [[ "$OUT_VTT" == "1" ]]; then
    local out_vtt="$OUTPUT_DIR/${today}_${safe_title}.vtt"
    python3 - "$srt_file" "$out_vtt" << 'VTTEOF'
import re, sys
with open(sys.argv[1]) as f:
    content = f.read()
# Converti timestamp SRT (00:00:00,000) in VTT (00:00:00.000)
vtt = "WEBVTT

" + re.sub(r"(\d{2}:\d{2}:\d{2}),(\d{3})", r"\1.\2", content)
# Rimuovi indici numerici
vtt = re.sub(r"^\d+
", "", vtt, flags=re.MULTILINE)
with open(sys.argv[2], 'w') as f:
    f.write(vtt)
VTTEOF
    ok ".vtt generato"
  fi

  # .pdf (da txt con pandoc o python-fpdf)
  if [[ "$OUT_PDF" == "1" ]]; then
    local out_pdf="$OUTPUT_DIR/${today}_${safe_title}_trascrizione.pdf"
    if command -v pandoc &>/dev/null; then
      pandoc "$WORK_DIR/transcript.txt" -o "$out_pdf"         --pdf-engine=xelatex 2>/dev/null || \
      pandoc "$WORK_DIR/transcript.txt" -o "$out_pdf" 2>/dev/null || true
    else
      python3 - "$WORK_DIR/transcript.txt" "$out_pdf" "$title" << 'PDFEOF'
import sys
try:
    from fpdf import FPDF
    pdf = FPDF()
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, sys.argv[3][:80], ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.ln(4)
    with open(sys.argv[1]) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    pdf.multi_cell(0, 6, line)
                except:
                    pdf.multi_cell(0, 6, line.encode('latin-1','replace').decode('latin-1'))
    pdf.output(sys.argv[2])
except ImportError:
    print("fpdf2 non installato — installa con: pip install fpdf2 --break-system-packages")
PDFEOF
    fi
    [[ -f "$out_pdf" ]] && ok ".pdf generato" || warn ".pdf: installa pandoc o fpdf2"
  fi

  # ── Step 6: Forza lingua italiana ─────────────────────────────────────────
  step "Impostazione lingua italiana nei documenti Word"
  # Trova tutti i .docx generati oggi in output
  local docx_files
  mapfile -t docx_files < <(find "$OUTPUT_DIR" -name "${today}_*.docx" -newer "$loud_audio" 2>/dev/null)
  if [[ ${#docx_files[@]} -gt 0 ]]; then
    python3 "$PIPELINE_DIR/set_lang_it.py" "${docx_files[@]}" 2>/dev/null || true
    ok "Lingua it-IT impostata su ${#docx_files[@]} file"
  else
    warn "Nessun .docx trovato per impostare la lingua"
  fi

  # ── Riepilogo finale ───────────────────────────────────────────────────────
  echo -e "\n${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BOLD}${GREEN}  ✓ Pipeline completata${NC}"
  echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "  ${BOLD}Titolo:${NC}      $title"
  echo -e "  ${BOLD}Parole:${NC}      $word_count"
  echo -e "  ${BOLD}SRT grezzo:${NC}  $srt_file"
  [[ "${WITH_TS}" == "1" ]] && echo -e "  ${BOLD}Timestamp:${NC}   inclusi nel testo"
  [[ "${BURN_SUBS}" == "1" && $is_local -eq 1 ]] && echo -e "  ${BOLD}Sottotitoli:${NC} bruciati nel video"
  echo -e "  ${BOLD}Trascrizione:${NC} $out_transcript"
  echo -e "\n  ${CYAN}→ Carica il file .docx in Claude per il riassunto strutturato${NC}\n"

  # Pulizia work dir (opzionale — commenta per debug)
  # rm -rf "$WORK_DIR"
}

main "$@"
