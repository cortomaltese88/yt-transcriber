# yt-transcriber

**Pipeline Trascrizione Audio/Video — Studio GD LEX**  
Versione 1.0.7 · 2026 · Licenza: Proprietaria

---

## 1. Cos'è e a cosa serve

`yt-transcriber` è un programma con interfaccia grafica che permette di **trascrivere automaticamente** video YouTube e file audio/video locali.

Dato un URL di YouTube o un file sul proprio computer, il programma:

1. scarica (o legge) l'audio;
2. può normalizzarlo opzionalmente per migliorare la qualità della trascrizione;
3. lo trascrive usando **Whisper** (motore AI di riconoscimento vocale);
4. pulisce e formatta il testo risultante;
5. salva la trascrizione nei formati scelti: Word (.docx), PDF, testo semplice (.txt), sottotitoli (.srt / .vtt).

È pensato per uso interno a **Studio GD LEX** e ottimizzato per la lingua italiana.

Per impostazione predefinita il comportamento resta conservativo: non viene applicata alcuna normalizzazione automatica e `VOLUME_BOOST=1.0` non aggiunge alcun filtro audio. Se serve, è possibile attivare opzionalmente `AUDIO_NORMALIZE=1` per usare `ffmpeg loudnorm` su audio troppo basso, troppo alto o irregolare. `VOLUME_BOOST` resta disponibile come opzione manuale e viene usato solo quando `AUDIO_NORMALIZE=0`.

La normalizzazione audio è ora disponibile anche dalla GUI tramite toggle Matrix `Normalizza audio`, disattivato di default. Quando il toggle è attivo la GUI passa `AUDIO_NORMALIZE=1` alla pipeline; quando è disattivo passa `AUDIO_NORMALIZE=0`.

---

## 2. Requisiti

### Obbligatori

| Componente | Versione minima | Note |
|---|---|---|
| Python | 3.10+ | Incluso nella maggior parte delle distribuzioni Linux |
| PyQt6 | qualsiasi | Libreria Python per l'interfaccia grafica |
| ffmpeg | qualsiasi | Elaborazione audio/video |
| Node.js | 16+ | Generazione documenti Word |
| yt-dlp | qualsiasi | Download da YouTube |
| bc | qualsiasi | Calcolo avanzamento nella shell |
| whisper.cpp | compilato | Motore di trascrizione (vedi sezione installazione) |
| Modello Whisper | — | File `.bin` da scaricare separatamente |

### Opzionali

| Componente | A cosa serve |
|---|---|
| faster-whisper (Python) | Fallback se whisper.cpp non è disponibile |
| openai-whisper (Python) | Secondo fallback |
| pandoc o fpdf2 | Generazione PDF |
| xclip | Copia percorso file negli appunti |

### Ambiente

- Sistema operativo: **Linux** (pacchetto `.deb` per Debian/Ubuntu/derivate)
- È necessario un **ambiente grafico** (desktop) per avviare l'interfaccia
- GPU AMD, Intel o NVIDIA consigliata per trascrizioni veloci (ma non obbligatoria)

---

## 3. Installazione

### Opzione A — Pacchetto .deb (consigliata)

Un pacchetto già pronto è incluso nella cartella del progetto:

```bash
sudo dpkg -i yt-transcriber_1.0.7_amd64.deb
sudo apt-get install -f   # risolve eventuali dipendenze mancanti
```

Il programma verrà installato in `/usr/lib/yt-transcriber/` e sarà disponibile come comando `yt-transcriber`.

### Opzione B — Esecuzione diretta dalla cartella sorgente

Installare manualmente le dipendenze Python e Node.js, poi avviare direttamente gli script (vedi sezione 4).

```bash
# Dipendenze Python
pip install PyQt6 --break-system-packages

# Dipendenze Node.js (già presenti in node_modules/)
# Se la cartella node_modules mancasse:
npm install
```

### Installazione di whisper.cpp

Questo è il passaggio più complesso. whisper.cpp deve essere compilato manualmente e posizionato in `~/whisper.cpp/`.

Il programma cerca i binari nei seguenti percorsi (in ordine di preferenza):

| Backend | Percorso binario |
|---|---|
| GPU Vulkan (AMD/Intel) | `~/whisper.cpp/build-vulkan/bin/whisper-cli` |
| GPU CUDA (NVIDIA) | `~/whisper.cpp/build-cuda/bin/whisper-cli` |
| Solo CPU | `~/whisper.cpp/build/bin/whisper-cli` |

I percorsi possono essere sovrascritti con variabili d'ambiente (`WHISPER_BIN_VULKAN`, `WHISPER_BIN_CUDA`, ecc.).

### Download dei modelli Whisper

I modelli vanno scaricati nella cartella `~/whisper.cpp/models/`. Tre opzioni disponibili:

| Modello | Dimensione | Qualità | Velocità |
|---|---|---|---|
| `ggml-small.bin` | ~500 MB | base | molto veloce |
| `ggml-medium.bin` | ~1.5 GB | buona | veloce |
| `ggml-large-v3.bin` | ~3 GB | massima | lento |

```bash
# Esempio: scarica il modello medium
cd ~/whisper.cpp/models/
bash download-ggml-model.sh medium
```

---

## 4. Come avviare il programma

### Con il pacchetto .deb installato

```bash
yt-transcriber
```

### Direttamente dalla cartella sorgente

```bash
python3 yt-transcriber_gui.py
```

### Dalla riga di comando (senza interfaccia grafica)

```bash
# Video YouTube
bash yt-transcriber.sh "https://www.youtube.com/watch?v=..." "Titolo opzionale" ~/Trascrizioni

# File locale
bash yt-transcriber.sh --local /percorso/al/file.mp3 "Titolo opzionale" ~/Trascrizioni
```

### Diagnostica del backend

```bash
python3 transcriber_backend.py
```

Mostra quale motore di trascrizione è attivo (GPU Vulkan, CUDA, CPU, o fallback Python).

---

## 5. Struttura dei file principali

```
studio-tools/
│
├── yt-transcriber_gui.py     # Interfaccia grafica (PyQt6)
│                             # Avvia la pipeline, mostra log e progresso
│
├── transcriber_backend.py    # Rilevamento automatico del backend Whisper
│                             # Gestisce whisper.cpp, faster-whisper, openai-whisper
│
├── yt-transcriber.sh         # Script bash che esegue la pipeline completa:
│                             # download → audio → trascrizione → output
│
├── make_docx_styled.js       # Genera il documento Word (.docx) formattato
│                             # Usa la libreria Node.js "docx"
│
├── set_lang_it.py            # Imposta la lingua italiana nei file .docx prodotti
│
├── build_deb.sh              # Costruisce il pacchetto .deb installabile
│
├── yt-transcriber_1.0.7_amd64.deb   # Pacchetto installabile già pronto
│
├── package.json              # Dipendenze Node.js (libreria docx)
└── node_modules/             # Librerie Node.js (generate da npm install)
```

**Cartella output predefinita:** `~/Trascrizioni/`  
**Cronologia trascrizioni:** `~/.config/yt-transcriber/history.json`

---

## 6. Problemi noti e limitazioni

- **Compilazione whisper.cpp richiesta:** non è installabile tramite `apt` o `pip`; va compilato manualmente dal sorgente. Questa è la parte più tecnica dell'installazione.
- **Modelli da scaricare manualmente:** i file `.bin` sono di grandi dimensioni (da 500 MB a 3 GB) e non sono inclusi nel pacchetto.
- **Burn-in sottotitoli solo su file locali:** la funzione "brucia sottotitoli nel video" non è disponibile per i video YouTube (solo per file già presenti sul disco).
- **PDF opzionale:** la generazione PDF richiede `pandoc` (consigliato) o la libreria Python `fpdf2`. Senza di essi, il formato PDF non viene prodotto.
- **Richiede ambiente grafico:** l'interfaccia non funziona in modalità headless (es. server senza desktop). In quel caso usare `yt-transcriber.sh` da riga di comando.
- **xclip per gli appunti:** il pulsante "Apri in Claude" copia il percorso del file negli appunti solo se `xclip` è installato (`sudo apt install xclip`).

---

## 7. Autore e licenza

**Autore:** Studio GD LEX  
**Contatto:** info@studiogdlex.it  
**Licenza:** Proprietaria — tutti i diritti riservati.  
Questo software è riservato all'uso interno di Studio GD LEX.
