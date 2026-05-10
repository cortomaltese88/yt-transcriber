"""
Forza la lingua italiana (it-IT) in un file .docx:
1. Aggiunge <w:lang w:val="it-IT"/> a ogni run che non ce l'ha
2. Imposta la lingua di default del documento in settings.xml
"""
import sys, zipfile, shutil, os, re

def process(path_in, path_out):
    tmp = path_in + '.tmp'
    shutil.copy2(path_in, tmp)
    try:
        with zipfile.ZipFile(tmp, 'r') as zin, zipfile.ZipFile(path_out, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == 'word/document.xml':
                    xml = data.decode('utf-8')
                    # Aggiungi <w:lang> dopo ogni <w:rPr> che non contiene già w:lang
                    # Pattern: inserisce prima di </w:rPr>
                    xml = re.sub(
                        r'(<w:rPr>(?:(?!<w:lang).)*?)(</w:rPr>)',
                        r'\1<w:lang w:val="it-IT" w:eastAsia="it-IT" w:bidi="ar-SA"/>\2',
                        xml, flags=re.DOTALL
                    )
                    # Per i run senza rPr, aggiungi rPr con lang
                    xml = re.sub(
                        r'(<w:r>)(<w:t)',
                        r'\1<w:rPr><w:lang w:val="it-IT" w:eastAsia="it-IT" w:bidi="ar-SA"/></w:rPr>\2',
                        xml
                    )
                    data = xml.encode('utf-8')
                elif item.filename == 'word/settings.xml':
                    xml = data.decode('utf-8')
                    # Imposta lingua di default
                    if '<w:themeFontLang' in xml:
                        xml = re.sub(r'<w:themeFontLang[^/]*/>', '<w:themeFontLang w:val="it-IT"/>', xml)
                    else:
                        xml = xml.replace('</w:settings>', '<w:themeFontLang w:val="it-IT"/></w:settings>')
                    data = xml.encode('utf-8')
                zout.writestr(item, data)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    print(f'Done: {path_out}')

for p in sys.argv[1:]:
    out = p.replace('.docx', '_it.docx')
    process(p, out)
    shutil.move(out, p)
    print(f'Language set: {p}')
