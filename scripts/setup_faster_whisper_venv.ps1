param(
    [Parameter(Position = 0)]
    [string]$Model = "base",

    [switch]$CheckOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-UserVenvDir {
    $localAppData = $env:LOCALAPPDATA
    if ([string]::IsNullOrWhiteSpace($localAppData)) {
        return Join-Path $HOME "AppData\Local\yt-transcriber\venv"
    }
    return Join-Path $localAppData "yt-transcriber\venv"
}

function Get-UserVenvPython {
    param(
        [Parameter(Mandatory = $true)]
        [string]$VenvDir
    )

    return Join-Path $VenvDir "Scripts\python.exe"
}

function Get-BasePython {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return @{
            Label = "python"
            Invoke = {
                param([string[]]$Args)
                & python @Args
            }
        }
    }

    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) {
        try {
            & py -3 -c "import sys" | Out-Null
            return @{
                Label = "py -3"
                Invoke = {
                    param([string[]]$Args)
                    & py -3 @Args
                }
            }
        } catch {
        }
    }

    return $null
}

function Invoke-BasePython {
    param(
        [Parameter(Mandatory = $true)]
        $PythonInfo,

        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    & $PythonInfo.Invoke $Args
}

$venvDir = Get-UserVenvDir
$venvPython = Get-UserVenvPython -VenvDir $venvDir
$pythonInfo = Get-BasePython

Write-Host "==> Setup faster-whisper in venv utente Windows"
Write-Host "    venv: $venvDir"
Write-Host "    modello: $Model"
if ($CheckOnly) {
    Write-Host "    modalita': check-only"
}

if (-not $pythonInfo) {
    Write-Error "ERRORE: Python non trovato. Installa Python e assicurati che 'python' o 'py -3' siano disponibili nel PATH."
    exit 1
}

if ($CheckOnly) {
    Write-Host "==> Check-only: nessuna modifica verra' eseguita"
    Write-Host "    Python base: $($pythonInfo.Label)"
    Write-Host "    Python venv atteso: $venvPython"

    try {
        Invoke-BasePython -PythonInfo $pythonInfo -Args @("-m", "venv", "--help") | Out-Null
        Write-Host "    Stato modulo venv: disponibile"
    } catch {
        Write-Host "    Stato modulo venv: assente"
    }

    if (Test-Path -LiteralPath $venvDir -PathType Container) {
        Write-Host "    Stato venv dir: presente"
    } else {
        Write-Host "    Stato venv dir: assente"
    }

    if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
        Write-Host "    Stato python venv: presente"
        try {
            & $venvPython -c "import faster_whisper" | Out-Null
            Write-Host "    Stato faster_whisper nel venv: import OK"
        } catch {
            Write-Host "    Stato faster_whisper nel venv: non importabile"
        }
    } else {
        Write-Host "    Stato python venv: assente"
        Write-Host "    Stato faster_whisper nel venv: non verificabile"
    }

    Write-Host "    Stato modello $Model: verifica senza download non disponibile"
    exit 0
}

try {
    Invoke-BasePython -PythonInfo $pythonInfo -Args @("-m", "venv", "--help") | Out-Null
} catch {
    Write-Error "ERRORE: modulo venv non disponibile per $($pythonInfo.Label)."
    exit 1
}

$venvParent = Split-Path -Parent $venvDir
if (-not (Test-Path -LiteralPath $venvParent -PathType Container)) {
    New-Item -ItemType Directory -Path $venvParent -Force | Out-Null
}

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    Write-Host "==> Creo il venv utente"
    Invoke-BasePython -PythonInfo $pythonInfo -Args @("-m", "venv", $venvDir)
} else {
    Write-Host "==> Venv gia' presente"
}

Write-Host "==> Aggiorno pip nel venv"
& $venvPython -m pip install --upgrade pip

Write-Host "==> Installo faster-whisper nel venv"
& $venvPython -m pip install faster-whisper

Write-Host "==> Verifico import faster_whisper"
& $venvPython -c "import faster_whisper; print('OK faster_whisper')"

Write-Host "==> Scarico/verifico modello faster-whisper: $Model"
& $venvPython -c @"
from faster_whisper import WhisperModel
WhisperModel("$Model", device="cpu", compute_type="int8")
print("Modello pronto")
"@

Write-Host "==> Completato"
Write-Host "    Python venv: $venvPython"
Write-Host "    Ora yt-transcriber puo' usare il fallback faster-whisper dal venv utente."
