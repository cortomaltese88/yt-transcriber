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

Verifiche utili:

```bash
yt-dlp --version
```

Se la sorgente online fallisce, provare a scaricare il file esternamente e usare la modalita' file locale.

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

- aggiornare o verificare `yt-dlp`
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
