const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Header, Footer, PageNumber, BorderStyle, ShadingType,
  WidthType, TableCell, TableRow, Table, LevelFormat,
  TabStopType, TabStopPosition, PageBreak
} = require('docx');
const fs   = require('fs');
const path = require('path');

const transcriptPath = process.argv[2];
const outputDir      = process.argv[3];

if (!transcriptPath || !outputDir) {
  console.error('Uso: node make_docx_styled.js <transcript.txt> <output_dir>');
  process.exit(1);
}
if (!fs.existsSync(transcriptPath)) {
  console.error(`File trascrizione non trovato: ${transcriptPath}`);
  process.exit(1);
}
if (!fs.existsSync(outputDir)) {
  console.error(`Output dir non esiste: ${outputDir}`);
  process.exit(1);
}

const today = new Date().toISOString().slice(0,10).replace(/-/g,'');

// Palette
const BLUE       = '1B3A6B';
const BLUE_MID   = '2E5FA3';
const BLUE_LIGHT = 'D6E4F7';
const GOLD       = 'C8922A';
const BORDER_COL = 'BFCFE0';
const WHITE      = 'FFFFFF';
const DARK_TEXT  = '1A1A2E';
const MUTED      = '6B7A99';

// ── Legge titolo e URL dalle prime righe del file ─────────────────────────────
function readMeta(filePath) {
  const lines = fs.readFileSync(filePath, 'utf8').split('\n');
  let title = '', url = '';
  for (let i = 0; i < Math.min(5, lines.length); i++) {
    const l = lines[i].trim();
    if (!title && l && !l.startsWith('http')) title = l;
    if (!url && l.startsWith('http'))           url   = l;
  }
  return { title: title || 'Trascrizione', url: url || '' };
}

function safeTitle(t) {
  return t.replace(/[^a-zA-Z0-9àèéìòùÀÈÉÌÒÙ _\-]/g,'').replace(/ +/g,'_').slice(0,50);
}

function ruler() {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: GOLD, space: 1 } },
    spacing: { before: 0, after: 240 }
  });
}

function spacer(before=0, after=120) {
  return new Paragraph({ text: '', spacing: { before, after } });
}

function makeCoverPage(videoTitle, docType, url) {
  // docType: 'Trascrizione' o 'Riassunto'
  const isTranscript = docType === 'Trascrizione';
  return [
    spacer(2400, 0),
    spacer(0, 80),
    spacer(0, 480),
    new Paragraph({
      children: [new TextRun({ text: docType.toUpperCase(), font: 'Arial', size: 52, bold: true, color: BLUE, characterSpacing: 100 })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 160 }
    }),
    ruler(),
    new Paragraph({
      children: [new TextRun({ text: videoTitle, font: 'Arial', size: 24, color: BLUE_MID, italics: false })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 480 }
    }),
    spacer(400, 0),
    ...(url ? [new Paragraph({
      children: [new TextRun({ text: url, font: 'Arial', size: 16, color: '0563C1' })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 120 }
    })] : []),
    new Paragraph({
      children: [new TextRun({ text: today.slice(0,4)+'-'+today.slice(4,6)+'-'+today.slice(6,8), font: 'Arial', size: 16, color: MUTED })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 0 }
    }),
    new Paragraph({ children: [new PageBreak()] })
  ];
}

function parseAndRender(text) {
  const lines = text.split('\n');
  const children = [];
  let i = 0;
  // Salta metadati: titolo (riga 0), url opzionale, riga vuota opzionale
  if (i < lines.length) i++;                                              // skip title
  if (i < lines.length && lines[i].trim().startsWith('http')) i++;        // skip url
  if (i < lines.length && !lines[i].trim()) i++;                          // skip blank

  while (i < lines.length) {
    const line = lines[i].trim();

    if (!line) { children.push(spacer(0,80)); i++; continue; }

    if (line.startsWith('━')) { children.push(ruler()); i++; continue; }

    if (line.startsWith('# ')) {
      children.push(new Paragraph({
        children: [new TextRun({ text: line.slice(2), font: 'Arial', size: 32, bold: true, color: BLUE })],
        spacing: { before: 360, after: 160 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BLUE_LIGHT, space: 4 } }
      }));
      i++; continue;
    }

    if (line.startsWith('## ')) {
      children.push(new Paragraph({
        children: [new TextRun({ text: line.slice(3), font: 'Arial', size: 26, bold: true, color: BLUE_MID })],
        spacing: { before: 280, after: 120 }
      }));
      i++; continue;
    }

    if (line.startsWith('### ')) {
      children.push(new Paragraph({
        children: [new TextRun({ text: line.slice(4), font: 'Arial', size: 22, bold: true, color: GOLD })],
        spacing: { before: 200, after: 80 }
      }));
      i++; continue;
    }

    // Intestazione relatore (testo tutto maiuscolo, non tabella)
    if (line.match(/^[A-ZÀÈÉÌÒÙ \/\-:0-9°,\.]+$/) && line.length > 6 && !line.startsWith('|')) {
      children.push(new Paragraph({
        children: [new TextRun({ text: line, font: 'Arial', size: 20, bold: true, color: BLUE, allCaps: true })],
        spacing: { before: 160, after: 40 },
        shading: { fill: BLUE_LIGHT, type: ShadingType.CLEAR }
      }));
      i++; continue;
    }

    // Parentesi relatore
    if (line.startsWith('(') && line.endsWith(')') && line.length > 4) {
      children.push(new Paragraph({
        children: [new TextRun({ text: line, font: 'Arial', size: 18, italics: true, color: MUTED })],
        spacing: { before: 20, after: 200 }
      }));
      i++; continue;
    }

    // Bold **...**
    if (line.startsWith('**') && line.endsWith('**') && line.length > 4) {
      children.push(new Paragraph({
        children: [new TextRun({ text: line.replace(/\*\*/g,''), font: 'Arial', size: 22, bold: true, color: BLUE })],
        spacing: { before: 160, after: 60 }
      }));
      i++; continue;
    }

    // Tabella |...|
    if (line.startsWith('|')) {
      if (lines[i+1]?.trim().match(/^\|[-| ]+\|$/)) {
        const tableLines = [];
        while (i < lines.length && lines[i].trim().startsWith('|')) {
          if (!lines[i].trim().match(/^\|[-| ]+\|$/)) tableLines.push(lines[i].trim());
          i++;
        }
        if (tableLines.length > 0) {
          const rows = tableLines.map((tl, ri) => {
            const cells = tl.split('|').filter(c => c.trim() !== '').map(c => c.trim());
            return new TableRow({
              children: cells.map(cell => new TableCell({
                borders: { top:{style:BorderStyle.SINGLE,size:1,color:BORDER_COL}, bottom:{style:BorderStyle.SINGLE,size:1,color:BORDER_COL}, left:{style:BorderStyle.SINGLE,size:1,color:BORDER_COL}, right:{style:BorderStyle.SINGLE,size:1,color:BORDER_COL} },
                shading: ri===0 ? {fill:BLUE,type:ShadingType.CLEAR} : {fill:ri%2===0?'F0F4FA':WHITE,type:ShadingType.CLEAR},
                margins: {top:80,bottom:80,left:120,right:120},
                children: [new Paragraph({ children: [new TextRun({ text: cell, font:'Arial', size:18, bold:ri===0, color:ri===0?WHITE:DARK_TEXT })] })]
              }))
            });
          });
          children.push(new Table({ width:{size:9000,type:WidthType.DXA}, rows }));
          children.push(spacer(120,120));
        }
        continue;
      } else { i++; continue; }
    }

    // Bullet
    if (line.startsWith('- ') || line.startsWith('* ')) {
      children.push(new Paragraph({
        numbering: { reference:'bullets', level:0 },
        children: [new TextRun({ text: line.slice(2), font:'Arial', size:20, color:DARK_TEXT })],
        spacing: { before:40, after:40 }
      }));
      i++; continue;
    }

    // Paragrafo normale
    children.push(new Paragraph({
      children: [new TextRun({ text: line, font:'Arial', size:20, color:DARK_TEXT })],
      spacing: { before:40, after:80 },
      alignment: AlignmentType.JUSTIFIED
    }));
    i++;
  }
  return children;
}

function makeDoc(textContent, videoTitle, docType, url, outPath) {
  const bodyChildren = parseAndRender(textContent);
  const coverChildren = makeCoverPage(videoTitle, docType, url);

  const doc = new Document({
    numbering: {
      config: [{ reference:'bullets', levels:[{
        level:0, format:LevelFormat.BULLET, text:'▸', alignment:AlignmentType.LEFT,
        style:{ paragraph:{indent:{left:720,hanging:360}}, run:{color:GOLD} }
      }]}]
    },
    styles: {
      default: { document: { run: { font:'Arial', size:20, color:DARK_TEXT } } }
    },
    sections: [{
      properties: {
        page: {
          size: { width:11906, height:16838 },
          margin: { top:1200, right:1200, bottom:1200, left:1440 }
        }
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            children: [
              new TextRun({ text: videoTitle, font:'Arial', size:16, color:BLUE_MID }),
              new TextRun({ text: '\t', font:'Arial', size:16 }),
              new TextRun({ text: docType, font:'Arial', size:16, color:GOLD })
            ],
            tabStops: [{type:TabStopType.RIGHT, position:TabStopPosition.MAX}],
            border: { bottom:{style:BorderStyle.SINGLE,size:6,color:BLUE_LIGHT,space:4} },
            spacing: { before:0, after:160 }
          })]
        })
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            children: [
              new TextRun({ text:'Studio GD LEX  |  ', font:'Arial', size:16, color:MUTED }),
              new TextRun({ children:[PageNumber.CURRENT], font:'Arial', size:16, color:BLUE_MID }),
              new TextRun({ text:' / ', font:'Arial', size:16, color:MUTED }),
              new TextRun({ children:[PageNumber.TOTAL_PAGES], font:'Arial', size:16, color:BLUE_MID })
            ],
            alignment: AlignmentType.CENTER,
            border: { top:{style:BorderStyle.SINGLE,size:4,color:BLUE_LIGHT,space:4} },
            spacing: { before:120, after:0 }
          })]
        })
      },
      children: [...coverChildren, ...bodyChildren]
    }]
  });

  return Packer.toBuffer(doc).then(buf => {
    fs.writeFileSync(outPath, buf);
    console.log('Written:', outPath);
  });
}

// ── Main ──────────────────────────────────────────────────────────────────────
const { title: videoTitle, url } = readMeta(transcriptPath);
const transcript = fs.readFileSync(transcriptPath, 'utf8');
const safe       = safeTitle(videoTitle) || 'transcript';

const outT = path.join(outputDir, `${today}_${safe}_trascrizione.docx`);

// Genera solo la trascrizione — il riassunto è prodotto da Claude
makeDoc(transcript, videoTitle, 'Trascrizione', url, outT)
  .then(() => console.log('All done.'))
  .catch(e => { console.error(e); process.exit(1); });
