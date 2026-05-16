# Third-Party Components

Questo file riassume, in modo prudente, i componenti di terze parti che `yt-transcriber`
include, dichiara, importa opzionalmente o invoca come strumenti esterni. Le rispettive
licenze restano dei relativi autori e titolari.

## 1. Componenti dichiarati o inclusi nel repository

### `docx` e dipendenze Node distribuite con il progetto

- `docx` (Node.js) è dichiarato in `package.json`, bloccato in `package-lock.json` e presente
  in `node_modules/`; il build script copia `node_modules/` nel pacchetto `.deb` se presenti.
- Licenza `docx`: `MIT`, verificata localmente in `package-lock.json`.
- Il pacchetto radice del progetto usa `GPL-3.0-or-later`; questo dato è distinto dalle
  licenze dei pacchetti terzi presenti in `node_modules/`.

### Dipendenze transitive Node

- Le dipendenze transitive risultano tracciate in `package-lock.json`.
- Dalla verifica locale emergono licenze terze come `MIT`, `ISC`, `BlueOak-1.0.0`,
  `(MIT OR GPL-3.0-or-later)` e `(MIT AND Zlib)`.
- Le occorrenze residue di `ISC` in `package-lock.json` riguardano esclusivamente pacchetti
  terzi transitivi, non la licenza del progetto `yt-transcriber`.

## 2. Librerie Python usate o importate dal progetto

| Componente | Ruolo nel progetto | Stato d'uso | Licenza | Base di verifica |
|---|---|---|---|---|
| Python | runtime generale del progetto | dipendenza runtime esterna, non inclusa nel repository | PSF License / stack di licenze open source | fonte ufficiale indicata; nel repository non è inclusa una copia del runtime |
| PyQt6 | GUI desktop (`QtWidgets`, `QtCore`, `QtNetwork`, `QtGui`) | dipendenza runtime dichiarata nel `.deb` e importata dal codice | GPL v3 oppure Riverbank Commercial License | fonte ufficiale indicata; metadata Debian locale `python3-pyqt6`; metadata Python installati senza campo `License` |
| Qt | framework sottostante a PyQt6 | runtime esterno richiesto indirettamente da PyQt6 | commerciale oppure open source `LGPLv3` / `GPLv3`; alcuni moduli possono essere `GPL-only` | fonte ufficiale indicata |
| `faster-whisper` | backend Python di fallback | import opzionale a runtime, non dichiarato in `package.json` e non installato localmente qui | MIT, secondo il repository ufficiale; da riverificare se in futuro incluso materialmente nel pacchetto | nel repository è solo import opzionale; nessun metadata locale disponibile |
| `openai-whisper` | ultimo backend Python di fallback | import opzionale a runtime, non installato localmente qui | MIT | fonte ufficiale indicata; nessun metadata locale disponibile |
| `fpdf2` | fallback opzionale per output PDF | opzionale; citato nel README e nel codice shell come alternativa a `pandoc`; non installato localmente qui | LGPL-3.0 | fonte ufficiale indicata; nessun metadata locale disponibile |

### Nota su PyQt6 e Qt

- Nel contesto di questo progetto, distribuito come `GPL-3.0-or-later`, l'uso di PyQt6 è
  coerente con il ramo `GPL v3` della dual license di PyQt6.
- I moduli Qt oggi importati sono moduli base della GUI. Se in futuro verranno aggiunti moduli
  Qt ulteriori, sarà opportuno verificare se qualcuno di essi sia disponibile solo in regime GPL.

## 3. Strumenti esterni invocati o installati dall'utente

| Componente | Ruolo nel progetto | Stato d'uso | Licenza | Base di verifica |
|---|---|---|---|---|
| `yt-dlp` | download da sorgenti online supportate | strumento esterno invocato da `yt-transcriber.sh`; dipendenza runtime del `.deb` | Unlicense per repository, sdist e wheel; il binario Unix zipimport può contenere anche componenti `ISC` / `MIT` | fonte ufficiale indicata; presenza locale rilevata |
| FFmpeg / `ffprobe` | elaborazione audio/video e probing | strumenti esterni invocati da `yt-transcriber.sh`; `ffmpeg` è dipendenza runtime del `.deb` | `LGPL-2.1-or-later`, oppure `GPL-2-or-later` se la build usa componenti/opzioni GPL | fonte ufficiale indicata; metadata Debian locale confermano che la build Debian usa parti GPL e produce binari sotto GPL |
| `whisper.cpp` / `whisper-cli` | backend di trascrizione principale | strumento esterno cercato e invocato a runtime; non incluso nel repository e non incluso nel `.deb` | MIT | fonte ufficiale indicata; il repository contiene solo riferimenti ai percorsi e alla configurazione |
| `pandoc` | output PDF opzionale | strumento esterno opzionale invocato se disponibile | GPL-2.0 | fonte ufficiale indicata; non installato localmente qui |
| `xclip` | copia negli appunti opzionale dalla GUI | strumento esterno opzionale invocato se disponibile | GPL-2.0 / GPL-2.0-or-later secondo repository e metadata di distribuzione; verificare la build installata | repository ufficiale `xclip` / metadata di distribuzione |
| `xdg-open` / `xdg-utils` | apertura file/cartelle dalla GUI | strumento esterno opzionale invocato dalla GUI | MIT secondo metadata di distribuzione; verificare la build installata | `xdg-utils` / metadata di distribuzione |
| `bc` | calcolo di supporto nella pipeline shell | dipendenza runtime del `.deb` e comando invocato dallo script | GPL-3.0-or-later | fonte ufficiale GNU bc; verificare comunque eventuale pacchetto installato dalla distribuzione |

## 4. Modelli Whisper

- I modelli Whisper / `ggml` non sono inclusi nel repository.
- I modelli Whisper / `ggml` non sono inclusi nel pacchetto `.deb`, salvo diversa scelta futura.
- Le licenze dei modelli devono essere valutate separatamente dal codice applicativo prima di
  qualunque futura distribuzione che li includa materialmente.

## 5. Nota di compatibilità e distribuzione

- `yt-transcriber` è distribuito come `GPL-3.0-or-later`.
- L'uso di PyQt6 è coerente con la distribuzione `GPLv3` del progetto.
- Gli strumenti esterni invocati a riga di comando mantengono le rispettive licenze.
- Le librerie opzionali importate solo a runtime come fallback o feature accessorie non cambiano,
  da sole, la licenza del progetto; restano comunque da documentare correttamente se incluse in
  una distribuzione futura.
- Prima di distribuire pacchetti che includano materialmente componenti terzi o binari esterni,
  occorrerà includere le relative licenze, notices e ogni eventuale adempimento specifico della
  forma di distribuzione scelta.
