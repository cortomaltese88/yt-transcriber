# Troubleshooting

Questa nota raccoglie problemi frequenti emersi dalla struttura attuale del progetto.

## `make_docx_styled.js` non leggibile

Sintomo: export DOCX o smoke test falliscono con warning sui permessi.

Verifiche utili:

```bash
ls -l make_docx_styled.js
stat -c '%a %n' make_docx_styled.js
```

Il file deve essere almeno leggibile; la build Debian normalizza il file a `644`.

## `node_modules/docx` mancante

Sintomo: `build_deb.sh` interrompe la build con errore su `node_modules/docx`.

Rimedio:

```bash
npm ci
```

## `yt-dlp` non installato o fallisce

Sintomi comuni:

- download da URL non disponibile
- errore comando non trovato
- extractor non aggiornato o sorgente non supportata
- `HTTP Error 403: Forbidden` durante il download YouTube, spesso insieme al
  warning `Your yt-dlp version (...) is older than 90 days!`

Verifiche utili:

```bash
yt-dlp --version
which -a yt-dlp   # verifica quale eseguibile viene usato per primo nel PATH
```

### Il pacchetto `yt-dlp` di apt e' quasi sempre troppo vecchio

Su Ubuntu 24.04 il pacchetto apt `yt-dlp` (`/usr/bin/yt-dlp`) resta fermo a
versioni molto datate (es. `2024.04.09-1`) perche' non viene aggiornato al
ritmo delle release upstream. YouTube modifica spesso il proprio player e gli
extractor di yt-dlp devono essere aggiornati di conseguenza: un `yt-dlp`
vecchio di mesi produce quasi sempre `HTTP Error 403: Forbidden` su YouTube,
anche se il resto della pipeline funziona correttamente.

**Non e' un bug di `yt-transcriber`**: e' una conseguenza dell'obsolescenza
dell'extractor. La correzione e' aggiornare `yt-dlp`, non aggiungere opzioni
alla riga di comando.

### Aggiornamento corretto su Ubuntu 24.04 (PEP 668)

Da Ubuntu 23.04 in poi, `pip install --user -U yt-dlp` fallisce con
`error: externally-managed-environment` (PEP 668). **Non usare
`--break-system-packages`**: rischia di corrompere i pacchetti Python di
sistema. Il metodo consigliato e supportato e' `pipx`, gia' presente su
Ubuntu 24.04 (`apt install pipx` se mancante):

```bash
pipx install yt-dlp        # prima installazione isolata in ~/.local/share/pipx
pipx upgrade yt-dlp        # aggiornamenti successivi
```

`pipx` crea un venv dedicato e pubblica lo shim eseguibile in
`~/.local/bin/yt-dlp`. Se `~/.local/bin` precede `/usr/bin` nel `PATH` (caso
comune), questo yt-dlp aggiornato ha priorita' sul pacchetto apt datato senza
bisogno di `sudo` ne' di rimuovere il pacchetto di sistema.

Se `~/.local/bin/yt-dlp` esiste gia' come installazione `pip --user` (non
`pipx`), `pipx install yt-dlp` puo' segnalare un conflitto sul file: in tal
caso usare `pipx install --force yt-dlp` per sostituirlo con lo shim gestito
da pipx.

Verifica dopo l'aggiornamento:

```bash
yt-dlp --version   # deve corrispondere a pipx list
```

Se la sorgente online continua a fallire dopo l'aggiornamento, provare a
scaricare il file esternamente e usare la modalita' file locale.

## `ffmpeg` mancante

Sintomo: falliscono preparazione audio, conversioni o probing.

Verifica:

```bash
ffmpeg -version
ffprobe -version
```

## Backend Whisper o faster-whisper non disponibile

Sintomi comuni:

- la GUI si avvia ma blocca `Avvia pipeline`
- la pipeline non trova `whisper-cli`
- fallback Python non disponibile

Verifiche utili:

```bash
python3 transcriber_backend.py
```

Controllare anche le variabili ambiente `YT_TRANSCRIBER_WHISPER_BIN` e `YT_TRANSCRIBER_WHISPER_MODEL`, oppure la presenza di un backend Python compatibile.

Su Windows, se si usa `whisper.cpp` manuale:

- `YT_TRANSCRIBER_WHISPER_BIN` deve puntare a `whisper-cli.exe`
- `YT_TRANSCRIBER_WHISPER_MODEL` deve puntare a un file `.bin`
- dopo la modifica delle variabili ambiente utente conviene chiudere e riaprire la GUI
- il setup guidato Windows oggi copre `faster-whisper`, non `whisper.cpp`

## Export DOCX non riuscito

Possibili cause:

- dipendenze Node non installate
- permessi errati su `make_docx_styled.js`
- errore runtime Node.js

Verifica rapida:

```bash
node --check make_docx_styled.js
```

## Download YouTube fallito

Il progetto dipende da `yt-dlp` e dagli extractor disponibili. Un fallimento puo' dipendere da contenuto non pubblico, richiesta di login, limitazioni temporanee della piattaforma o regressioni dell'extractor.

Approccio prudente:

- aggiornare `yt-dlp` (vedi la sezione precedente: la causa piu' frequente e' proprio una versione datata) e verificarne la versione
- riprovare piu' tardi
- usare un file locale se il contenuto e' gia' stato scaricato con altri mezzi leciti

## GUI non parte

Possibili cause:

- assenza di ambiente grafico
- PyQt6 non installato
- dipendenze mancanti nel sistema

Verifiche utili:

```bash
python3 -m py_compile yt-transcriber_gui.py
python3 yt-transcriber_gui.py
```

Su sistemi headless conviene usare direttamente `yt-transcriber.sh`.

## Il `.deb` non contiene i file attesi

Verifiche minime:

```bash
dpkg-deb -c yt-transcriber_<version>_amd64.deb
```

Se serve, estrarre il pacchetto e controllare in particolare:

- `usr/lib/yt-transcriber/`
- `usr/share/doc/yt-transcriber/`
- presenza di asset, `README.md`, `LICENSE` e `THIRD_PARTY_LICENSES.md`

## Warning di permessi

Se compaiono warning durante build o smoke test, ricontrollare:

- permessi di `make_docx_styled.js`
- eseguibilita' di `yt-transcriber.sh`
- eventuali differenze introdotte manualmente nei file del repository
