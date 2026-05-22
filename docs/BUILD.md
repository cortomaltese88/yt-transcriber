# Build

Questa nota riassume la build locale di `yt-transcriber` senza modificare versione o tag.

## Requisiti

- Linux con strumenti Debian di base, incluso `dpkg-deb`
- Python 3.10+
- Node.js 16+ e `npm`
- Dipendenze runtime usate anche nei controlli: `bc`, `ffmpeg`, `yt-dlp`
- Cartella `node_modules/` disponibile oppure accesso a `npm ci`

## Installazione dipendenze Node

Eseguire dalla root del repository:

```bash
npm ci
```

Questo comando ripristina le dipendenze dichiarate in `package-lock.json`, incluse quelle necessarie per l'export DOCX.

## Controlli Python

Verificare almeno la compilazione bytecode dei file principali:

```bash
python3 -m py_compile yt-transcriber_gui.py transcriber_backend.py
```

Se si vuole allinearsi al controllo locale piu' esteso usato dallo smoke test, viene verificato anche `set_lang_it.py`.

## Smoke test

Eseguire:

```bash
./smoke_test.sh
```

Lo script controlla sintassi shell e JavaScript, coerenza versione, presenza asset, permessi di `make_docx_styled.js` e alcuni marker funzionali del progetto.

## Build del pacchetto Debian

Eseguire:

```bash
bash build_deb.sh
```

Output atteso:

```text
yt-transcriber_<version>_amd64.deb
```

Con la versione corrente del repository, il default locale di `build_deb.sh` produce `yt-transcriber_1.2.2_amd64.deb`.

## Audit minimo del .deb

Dopo la build conviene eseguire almeno:

```bash
dpkg-deb -f yt-transcriber_<version>_amd64.deb
dpkg-deb -c yt-transcriber_<version>_amd64.deb
```

In caso di audit piu' puntuale, estrarre il pacchetto in una directory temporanea e verificare almeno:

- presenza di `README.md`, `LICENSE` e `THIRD_PARTY_LICENSES.md` sotto `usr/share/doc/yt-transcriber/`
- presenza di `make_docx_styled.js` sotto `usr/lib/yt-transcriber/`
- permessi leggibili del file `make_docx_styled.js`
- assenza di file interni non destinati alla distribuzione

## Nota su APP_VERSION e build da tag

`build_deb.sh` usa `VERSION="1.2.2"` come default locale corrente, ma se la variabile ambiente `APP_VERSION` e' valorizzata usa quel valore dopo la rimozione dell'eventuale prefisso `v`.

Nel workflow di release, `APP_VERSION` deriva dal tag Git `v*`. Per una build manuale coerente con una release, conviene partire da un tag annotato esistente oppure esportare `APP_VERSION` in modo esplicito prima di eseguire `bash build_deb.sh`.
