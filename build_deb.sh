#!/usr/bin/env bash
# build_deb.sh — Costruisce il pacchetto .deb per yt-transcriber
# Studio GD LEX

set -euo pipefail

VERSION="1.0.2"
PACKAGE="yt-transcriber"
ARCH="amd64"
MAINTAINER="Studio GD LEX <info@studiogdlex.it>"
DESCRIPTION="Pipeline Trascrizione Audio/Video — Studio GD LEX"
BUILD_DIR="/tmp/deb_build/${PACKAGE}_${VERSION}"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Build .deb ${PACKAGE} v${VERSION} ==="

# Verifica dipendenze Node necessarie al runtime DOCX
if [[ ! -d "$SOURCE_DIR/node_modules/docx" ]]; then
    echo "ERRORE: dipendenza Node mancante: node_modules/docx"
    echo "Esegui 'npm install' nella cartella del progetto prima di build_deb.sh"
    exit 1
fi

# Pulizia
rm -rf "$BUILD_DIR"

# Struttura directory debian
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/lib/${PACKAGE}"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/512x512/apps"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$BUILD_DIR/usr/share/doc/${PACKAGE}"

# ── File dell'app ─────────────────────────────────────────────────────────────
cp "$SOURCE_DIR/yt-transcriber_gui.py"   "$BUILD_DIR/usr/lib/${PACKAGE}/"
cp "$SOURCE_DIR/yt-transcriber.sh"       "$BUILD_DIR/usr/lib/${PACKAGE}/"
cp "$SOURCE_DIR/transcriber_backend.py"  "$BUILD_DIR/usr/lib/${PACKAGE}/"
cp "$SOURCE_DIR/make_docx_styled.js"     "$BUILD_DIR/usr/lib/${PACKAGE}/"
cp "$SOURCE_DIR/set_lang_it.py"         "$BUILD_DIR/usr/lib/${PACKAGE}/"

# node_modules (docx) — se presenti
if [[ -d "$SOURCE_DIR/node_modules" ]]; then
    cp -r "$SOURCE_DIR/node_modules" "$BUILD_DIR/usr/lib/${PACKAGE}/"
fi

# package.json
if [[ -f "$SOURCE_DIR/package.json" ]]; then
    cp "$SOURCE_DIR/package.json" "$BUILD_DIR/usr/lib/${PACKAGE}/"
fi

chmod +x "$BUILD_DIR/usr/lib/${PACKAGE}/yt-transcriber.sh"

# ── Launcher /usr/bin ─────────────────────────────────────────────────────────
cat > "$BUILD_DIR/usr/bin/${PACKAGE}" << 'LAUNCHER'
#!/usr/bin/env bash
APP_DIR="/usr/lib/yt-transcriber"
case "${1:-}" in
    --help|-h)
        exec bash "$APP_DIR/yt-transcriber.sh" --help ;;
    http*|--local)
        exec bash "$APP_DIR/yt-transcriber.sh" "$@" ;;
    *)
        exec python3 "$APP_DIR/yt-transcriber_gui.py" "$@" ;;
esac
LAUNCHER
chmod +x "$BUILD_DIR/usr/bin/${PACKAGE}"

# ── Icone ─────────────────────────────────────────────────────────────────────
if [[ -f "$SOURCE_DIR/yt-transcriber.png" ]]; then
    cp "$SOURCE_DIR/yt-transcriber.png" \
       "$BUILD_DIR/usr/share/icons/hicolor/256x256/apps/${PACKAGE}.png"
fi
if [[ -f "$SOURCE_DIR/yt-transcriber_512.png" ]]; then
    cp "$SOURCE_DIR/yt-transcriber_512.png" \
       "$BUILD_DIR/usr/share/icons/hicolor/512x512/apps/${PACKAGE}.png"
fi
if [[ -f "$SOURCE_DIR/yt-transcriber.svg" ]]; then
    cp "$SOURCE_DIR/yt-transcriber.svg" \
       "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/${PACKAGE}.svg"
fi

# ── .desktop ──────────────────────────────────────────────────────────────────
cat > "$BUILD_DIR/usr/share/applications/${PACKAGE}.desktop" << DESKTOP
[Desktop Entry]
Name=yt-transcriber
GenericName=Trascrizione Audio/Video
Comment=${DESCRIPTION}
Exec=/usr/bin/yt-transcriber
Icon=yt-transcriber
Terminal=false
Type=Application
Categories=Qt;AudioVideo;Audio;Video;
Keywords=trascrizione;youtube;whisper;video;audio;sottotitoli;
StartupNotify=true
DESKTOP

# ── Copyright ─────────────────────────────────────────────────────────────────
cat > "$BUILD_DIR/usr/share/doc/${PACKAGE}/copyright" << COPYRIGHT
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: yt-transcriber
Upstream-Contact: Studio GD LEX <info@studiogdlex.it>

Files: *
Copyright: ${VERSION} Studio GD LEX
License: Proprietary
 This software is proprietary and confidential.
 All rights reserved. Studio GD LEX.
COPYRIGHT

gzip -9 -c /dev/null > "$BUILD_DIR/usr/share/doc/${PACKAGE}/changelog.gz"

# README
if [[ -f "$SOURCE_DIR/README.md" ]]; then
    cp "$SOURCE_DIR/README.md" "$BUILD_DIR/usr/share/doc/${PACKAGE}/README.md"
fi

# ── DEBIAN/control ────────────────────────────────────────────────────────────
# Calcola dimensione installata
INSTALLED_SIZE=$(du -sk "$BUILD_DIR/usr" | cut -f1)

cat > "$BUILD_DIR/DEBIAN/control" << CONTROL
Package: ${PACKAGE}
Version: ${VERSION}
Architecture: ${ARCH}
Maintainer: ${MAINTAINER}
Installed-Size: ${INSTALLED_SIZE}
Depends: python3 (>= 3.10), python3-pyqt6, ffmpeg, nodejs (>= 16), yt-dlp, bc
Suggests: pandoc, fpdf2
Section: utils
Priority: optional
Description: ${DESCRIPTION}
 Pipeline completa per la trascrizione di video YouTube e file audio/video locali.
 Utilizza Whisper.cpp con supporto GPU (Vulkan/CUDA) o faster-whisper come fallback.
 Genera trascrizioni in formato docx, pdf, txt, srt, vtt con interfaccia grafica
 in stile Matrix. Sviluppato per Studio GD LEX.
CONTROL

# ── DEBIAN/postinst ───────────────────────────────────────────────────────────
cat > "$BUILD_DIR/DEBIAN/postinst" << 'POSTINST'
#!/bin/bash
set -e

# Aggiorna cache icone
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor/ 2>/dev/null || true
fi

# Aggiorna database desktop
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
fi

echo "yt-transcriber installato. Avvia con: yt-transcriber"
POSTINST
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# ── DEBIAN/prerm ──────────────────────────────────────────────────────────────
cat > "$BUILD_DIR/DEBIAN/prerm" << 'PRERM'
#!/bin/bash
set -e
# Nessuna operazione speciale alla rimozione
PRERM
chmod 755 "$BUILD_DIR/DEBIAN/prerm"

# ── DEBIAN/postrm ─────────────────────────────────────────────────────────────
cat > "$BUILD_DIR/DEBIAN/postrm" << 'POSTRM'
#!/bin/bash
set -e
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor/ 2>/dev/null || true
fi
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
fi
POSTRM
chmod 755 "$BUILD_DIR/DEBIAN/postrm"

# ── Build ─────────────────────────────────────────────────────────────────────
OUTPUT_DEB="${SOURCE_DIR}/${PACKAGE}_${VERSION}_${ARCH}.deb"
dpkg-deb --build --root-owner-group "$BUILD_DIR" "$OUTPUT_DEB"

echo ""
echo "=== Build completato ==="
echo "  Pacchetto: $OUTPUT_DEB"
echo "  Dimensione: $(du -sh "$OUTPUT_DEB" | cut -f1)"
echo ""
echo "  Installa con:"
echo "    sudo dpkg -i $OUTPUT_DEB"
echo "    sudo apt-get install -f  # risolve dipendenze mancanti"
echo ""
echo "  Disinstalla con:"
echo "    sudo apt remove yt-transcriber"
