# Changelog

Questo file riassume in modo sintetico le variazioni documentabili del progetto.

## v1.2.2

- Corretta propagazione del modello selezionato dalla GUI ai backend Whisper.
- Migliorata gestione dei modelli whisper.cpp mancanti, con messaggi e dialog contestuali.
- Incluso `platform_paths.py` nel pacchetto Debian.
- Corretto il rilevamento backend Whisper/Vulkan quando manca il modello selezionato ma il backend e' disponibile.
- Rafforzati smoke test e controlli statici sul packaging.

## v1.2.1 - Fix minori backend manager Linux

- Corretta la normalizzazione di `WHISPER_MODEL` con short-name come `medium` anche per backend `whisper.cpp` esistenti non app-managed.
- Aggiunto un messaggio piu' chiaro se manca `python3-venv` durante il setup di `faster-whisper`.

## v1.2.0 - Setup guidato backend Whisper

- Aggiunta GUI `Configura backend Whisper`.
- `whisper.cpp` installabile e configurabile come backend consigliato in home utente.
- `faster-whisper` installabile come fallback Python in venv utente.
- Aggiunti i comandi `yt-transcriber --setup-whisper-cpp` e `yt-transcriber --setup-faster-whisper`.
- Aggiunta la modalita' `--check-only` per gli script setup backend.
- Nessun `sudo` automatico.
- Nessun uso di `pip --break-system-packages`.
- Aggiunto il rilevamento backend app-managed `whisper_app_cpu`.
- Aggiunto il rilevamento backend app-managed `faster_whisper_venv`.
- Migliorata la gestione della chiusura GUI durante setup.
- Rafforzata la verifica runtime di `whisper-cli`.
- Normalizzato `WHISPER_MODEL=medium` per il modello app-managed.

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
