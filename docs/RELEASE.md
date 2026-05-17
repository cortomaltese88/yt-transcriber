# Release

Questa procedura documenta il flusso release attuale senza introdurre nuovi step automatici.

## Workflow GitHub Actions attuale

- `CI`: eseguito su `push` verso `main`, `pull_request` verso `main` e `workflow_dispatch`
- `Release Debian Package`: eseguito su `push` di tag `v*` e `workflow_dispatch`

Il workflow di release verifica la coerenza versione, esegue `npm ci`, `py_compile`, `./smoke_test.sh`, costruisce il `.deb`, lo audita e pubblica l'asset nella release GitHub.

## File da aggiornare per il bump versione

Prima di creare un tag release, allineare la versione almeno in:

- `README.md`
- `package.json`
- `package-lock.json`
- `build_deb.sh`
- `yt-transcriber_gui.py`

## Controlli prima del tag

Eseguire dalla root del repository:

```bash
python3 -m py_compile yt-transcriber_gui.py transcriber_backend.py
./smoke_test.sh
bash build_deb.sh
```

Controllare anche che:

- il working tree sia pulito
- il file `.deb` generato abbia il nome atteso
- i contenuti del pacchetto siano coerenti con la versione
- README e documentazione siano aggiornati se il comportamento e' cambiato

## Creazione del tag annotato

Quando tutti i controlli sono verdi:

```bash
git tag -a v<version> -m "Release v<version>"
```

Esempio:

```bash
git tag -a v1.1.3 -m "Release v1.1.3"
```

## Push del tag

Pubblicare il tag sul remoto:

```bash
git push origin v<version>
```

Il push del tag avvia il workflow `release-deb`.

## Controllo release GitHub e asset

Dopo l'esecuzione del workflow, verificare che:

- la release GitHub associata al tag esista
- sia presente l'asset `yt-transcriber_<version>_amd64.deb`
- l'asset corrisponda alla versione appena taggata

## Se il workflow fallisce

In caso di errore:

- leggere il job GitHub Actions che ha fallito
- correggere il problema nel branch locale
- rieseguire i controlli locali
- creare un nuovo commit correttivo prima di ritentare la release

Se il tag punta a uno stato errato, valutare con prudenza la strategia Git piu' adatta prima di ripubblicare. Evitare workaround manuali sulla release che aggirino i controlli previsti dal workflow.

## Asset storici

Non caricare manualmente vecchi file `.deb` o pacchetti generati in precedenza. Ogni release deve pubblicare solo l'asset coerente con il tag corrente.

