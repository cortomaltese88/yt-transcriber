# Validazione Windows da sorgente

## 1. Scopo

Validare manualmente `yt-transcriber` su Windows da sorgente, senza packaging e senza modifiche al codice.

Commit di riferimento attesi nel repository:

- `46d9c33` Document manual whisper.cpp Windows setup
- `e1b40b5` Add manual whisper.cpp backend detection via env
- `cad29f7` Refine backend setup texts for Windows
- `c54daef` Wire Windows GUI setup to faster-whisper PowerShell script
- `1b77d1c` Add Windows faster-whisper user venv setup script
- `42fb12b` Introduce cross-platform path helpers for W1 Windows prep

## 2. Prerequisiti Windows

Sistema consigliato:

- Windows 10 o Windows 11
- PowerShell classico disponibile come `powershell.exe`
- accesso internet per `npm` e `pip`, e per il download modello `faster-whisper` se si esegue il setup reale

### 2.1 Python 3.10+

Verifica in PowerShell:

```powershell
python --version
py -3 --version
```

Esito atteso:

- almeno uno dei due comandi risponde con Python 3.10 o superiore

Se manca:

- installare Python per Windows
- abilitare l'opzione per aggiungerlo al PATH, se disponibile

### 2.2 pip

Verifica:

```powershell
python -m pip --version
```

Esito atteso:

- versione `pip` visibile

Se manca:

- reinstallare o riparare Python
- provare `py -3 -m ensurepip --upgrade`

### 2.3 venv

Verifica:

```powershell
python -m venv --help
```

Esito atteso:

- help del modulo `venv`

Se manca:

- verificare che l'installazione Python includa `venv`

### 2.4 Node.js LTS

Verifica:

```powershell
node --version
npm --version
```

Esito atteso:

- `node` e `npm` disponibili

Se mancano:

- installare Node.js LTS per Windows

### 2.5 ffmpeg

Verifica:

```powershell
ffmpeg -version
ffprobe -version
```

Esito atteso:

- versioni mostrate senza errori

Se manca:

- installare `ffmpeg` e aggiungerlo al PATH

### 2.6 yt-dlp

Verifica:

```powershell
yt-dlp --version
```

Esito atteso:

- versione visibile

Se manca:

- installare `yt-dlp` nel PATH oppure via Python:

```powershell
python -m pip install yt-dlp
```

### 2.7 PowerShell classico

Verifica:

```powershell
powershell.exe -Command "$PSVersionTable.PSVersion"
```

Esito atteso:

- versione PowerShell mostrata

Se manca:

- verificare installazione Windows/PowerShell
- per questo step e' preferito `powershell.exe`, non `pwsh`

### 2.8 Git

Verifica:

```powershell
git --version
```

Esito atteso:

- versione Git visibile

Se manca:

- installare Git for Windows

### 2.9 Microsoft Visual C++ Redistributable

Verifica indiretta:

- alcuni wheel Python possono richiederlo
- se installazioni `pip` falliscono con errori runtime DLL, annotarlo

Se manca:

- installare il Microsoft Visual C++ Redistributable supportato dal sistema

### 2.10 Spazio disco

Verifica manuale:

- controllare spazio libero su disco di sistema e profilo utente

Esito atteso:

- spazio sufficiente per:
  - `.venv`
  - `node_modules`
  - eventuale modello `faster-whisper`

Consiglio prudente:

- avere almeno alcuni GB liberi

## 3. Checkout progetto su Windows

### Opzione A — Clone da GitHub

PowerShell:

```powershell
git clone git@github.com:cortomaltese88/yt-transcriber.git
cd yt-transcriber
git status --short --branch
git log --oneline --decorate -5
```

Esito atteso:

- working tree pulita
- `main` allineato a `origin/main`
- commit recenti coerenti con il checkpoint

### Opzione B — Copia cartella progetto

Operazione manuale:

- copiare la cartella del repository su Windows

Poi in PowerShell:

```powershell
cd C:\percorso\yt-transcriber
git status --short --branch
git log --oneline --decorate -5
```

## 4. Ambiente Python/Node per esecuzione da sorgente

Dipendenze deducibili dal repository:

- Python:
  - `PyQt6`
  - `fpdf2` opzionale ma utile
- Node:
  - `docx` tramite `npm ci`

PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install PyQt6 fpdf2
npm ci
```

Verifiche consigliate:

```powershell
python -m py_compile .\yt-transcriber_gui.py .\transcriber_backend.py .\platform_paths.py
```

Esito atteso:

- nessun errore di compilazione Python
- `npm ci` completa senza errori

Nota:

- `faster-whisper` non va installato qui manualmente se si vuole testare il setup Windows dedicato

## 5. Avvio GUI da sorgente

PowerShell:

```powershell
python .\yt-transcriber_gui.py
```

Checklist esito:

- la finestra GUI si apre
- la versione mostrata e' coerente con `1.2.3`
- non compaiono traceback in console
- il pulsante `Configura backend Whisper` e' visibile se il backend non e' pronto
- i testi Windows sono coerenti:
  - `faster-whisper` guidato via PowerShell
  - `whisper.cpp` guidato Windows non ancora integrato

Raccogliere in caso di errore:

- output completo console
- screenshot della GUI o del traceback
- versione Python usata

## 6. Test setup faster-whisper da script PowerShell

### 6.1 Check-only

PowerShell:

```powershell
.\scripts\setup_faster_whisper_venv.ps1 medium -CheckOnly
```

Esito atteso:

- non crea il venv
- non installa pacchetti
- non scarica modelli
- mostra il path atteso del venv in `%LOCALAPPDATA%\yt-transcriber\venv`
- mostra il Python rilevato
- indica se il venv e' assente o presente

Raccogliere:

- output completo
- exit code

Verifica exit code:

```powershell
$LASTEXITCODE
```

### 6.2 Setup reale opzionale

Solo se si vuole testare davvero il setup:

```powershell
.\scripts\setup_faster_whisper_venv.ps1 medium
```

Esito atteso:

- crea il venv utente
- aggiorna `pip`
- installa `faster-whisper`
- verifica import
- inizializza il modello scelto
- termina con exit code `0`

Raccogliere in caso di errore:

- output completo PowerShell
- exit code
- eventuali errori `pip`
- eventuali errori `WhisperModel`
- path effettivo del venv creato

## 7. Test setup faster-whisper dalla GUI

Operazioni manuali:

1. aprire la GUI
2. cliccare `Configura backend Whisper`
3. scegliere `Installa faster-whisper`
4. confermare
5. osservare il log GUI fino alla fine

Esito atteso:

- viene lanciato `powershell.exe`
- l'output compare nel log GUI
- i pulsanti restano disabilitati durante il setup
- a fine setup compare messaggio chiaro di successo o errore
- se previsto, la GUI chiede o suggerisce il riavvio

Raccogliere:

- screenshot del dialog iniziale
- screenshot/log della fase di setup
- eventuale messaggio finale
- eventuale traceback o errore console

## 8. Test detection backend faster-whisper venv

Dopo setup completato:

1. chiudere la GUI
2. riaprire la GUI
3. osservare il badge backend

Esito atteso:

- backend Python rilevato, preferibilmente `faster-whisper (venv utente)` o equivalente

Verifica da PowerShell:

```powershell
python -c "from transcriber_backend import detect_backend; print(detect_backend())"
```

Esito atteso:

- dizionario con `type` coerente con `faster_whisper_venv` oppure altro backend disponibile
- nessun crash

Raccogliere:

- output completo del comando
- screenshot badge backend nella GUI

## 9. Test whisper.cpp manuale via env

Sezione opzionale. Nessun download automatico.

Prerequisiti:

- `whisper-cli.exe` gia' disponibile
- modello `.bin` gia' disponibile, per esempio `ggml-medium.bin`

### 9.1 Impostazione env utente

PowerShell:

```powershell
[Environment]::SetEnvironmentVariable("YT_TRANSCRIBER_WHISPER_BIN", "C:\percorso\whisper-cli.exe", "User")
[Environment]::SetEnvironmentVariable("YT_TRANSCRIBER_WHISPER_MODEL", "C:\percorso\ggml-medium.bin", "User")
```

Poi:

- chiudere e riaprire PowerShell
- chiudere e riaprire la GUI

### 9.2 Verifica detection

PowerShell:

```powershell
python -c "from transcriber_backend import detect_backend; print(detect_backend())"
```

Esito atteso:

- `type: whisper_manual`
- `info: whisper.cpp (manuale)`
- `bin`: path di `whisper-cli.exe`
- `model`: path del `.bin`

Nota:

- se sul sistema Windows esistono backend whisper.cpp piu' prioritari e gia' rilevabili, il detector potrebbe scegliere quelli prima del manuale

### 9.3 Rimozione env utente

PowerShell:

```powershell
[Environment]::SetEnvironmentVariable("YT_TRANSCRIBER_WHISPER_BIN", $null, "User")
[Environment]::SetEnvironmentVariable("YT_TRANSCRIBER_WHISPER_MODEL", $null, "User")
```

Poi:

- riaprire PowerShell
- riaprire la GUI

## 10. Test pipeline reale Windows

La pipeline principale resta ancora bash/Linux-oriented.

Obiettivo del test:

- capire se oggi da Windows la GUI consente solo setup backend oppure tenta anche di lanciare `yt-transcriber.sh`

Test controllato consigliato:

1. usare un file locale molto piccolo
2. aprire la GUI
3. selezionare il file locale
4. compilare i campi minimi
5. cliccare `Avvia pipeline`
6. osservare log GUI e console

Classificazione esiti:

- `OK`: improbabile in questa fase, ma documentare se accade
- `KO atteso`: la GUI/backend e' pronto ma la pipeline bash Windows non e' ancora portata
- `KO inatteso`: crash GUI, traceback, blocco anomalo o errore non riconducibile al limite noto della pipeline

Raccogliere:

- log GUI
- output console
- eventuale messaggio su `yt-transcriber.sh`, `bash`, path mancanti o subprocess falliti

Non proporre fix durante questo test: serve solo classificare l'esito.

## 11. Modello di report risultati

Compilare al termine dei test:

```text
Windows version:
Python version:
Node version:
npm version:
ffmpeg version:
yt-dlp version:
PowerShell version:
Git version:

GUI avviata: si/no
Setup faster-whisper script diretto: OK/KO
Setup faster-whisper GUI: OK/KO
detect_backend dopo setup: output
whisper.cpp manuale env: OK/KO/non testato
Trascrizione reale: OK/KO atteso/KO inatteso/non testata

Errori console:
Screenshot/log rilevanti:
Note:
```

## 12. Criteri di valutazione finale

Esito minimo buono per procedere oltre:

- GUI avviabile su Windows da sorgente
- script `setup_faster_whisper_venv.ps1` funziona almeno in `-CheckOnly`
- setup `faster-whisper` dalla GUI parte via `powershell.exe`
- detection backend dopo setup e' coerente
- detection `whisper.cpp` manuale via env funziona oppure produce un esito chiaramente diagnosticabile

Esito che suggerisce stop prima del packaging:

- GUI non parte
- `powershell.exe` non viene lanciato dalla GUI
- script PowerShell fallisce in modo non chiaro
- detection backend Windows e' incoerente
- crash o traceback non spiegabili dal limite noto della pipeline bash

## 13. Note operative

- usare preferibilmente PowerShell per tutti i test Windows
- non dare per scontato che PATH e variabili ambiente siano aggiornati finche' non si riapre la shell
- se un test modifica env utente o installa componenti, annotare sempre:
  - comando esatto
  - output
  - exit code
  - eventuale riavvio shell/GUI eseguito
