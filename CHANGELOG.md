# Changelog

Questo file riassume in modo sintetico le variazioni documentabili del progetto.

## v1.1.5 - Portabilita' Linux migliorata

- yt-dlp non e' piu' obbligatorio per la trascrizione di file locali.
- La pipeline shell puo' usare faster-whisper come fallback se whisper.cpp non e' configurato.
- La GUI abilita l'avvio anche con fallback faster-whisper disponibile.
- Rimossa l'auto-install implicita di faster-whisper tramite pip.
- Documentazione aggiornata sul backend Whisper esterno al pacchetto .deb.

## v1.1.4

- Rafforzata la verifica release Debian con controllo del campo `Version` nel workflow dedicato.
- Allineata la CI ai file inclusi nella build verificando anche `set_lang_it.py`.
- Aggiornato il messaggio operativo di `npm ci` in `build_deb.sh` e resi piu' generici i riferimenti documentali collegati alla release tecnica.

## v1.1.3

- Correzione permessi `make_docx_styled.js`.
- Allineamento metadata `package.json` / `package-lock.json` a `yt-transcriber`.
- Aggiunta CI e release automatica Debian su GitHub Actions.

## v1.1.2

- Pulizia repository per pubblicazione pubblica.
- Allineamento licenza GPLv3.
- Inclusione `LICENSE` e `THIRD_PARTY_LICENSES.md` nel pacchetto Debian.

## v1.1.1

- Migliorata gestione backend Whisper.

## v1.1.0

- Aggiunta gestione single instance.
