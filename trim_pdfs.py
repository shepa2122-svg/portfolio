# -*- coding: utf-8 -*-
"""
Обрезает все PDF в папке до первых N страниц (по умолчанию 3).
Оригиналы сохраняются в _pdf_originals рядом со скриптом, PDF, где уже <= N страниц, не трогаются.

  pip install pypdf
  python trim_pdfs.py                      (папка assets\\MAP, 3 страницы)
  python trim_pdfs.py assets\\MAP 3
"""
import os, sys, shutil
try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    sys.exit('Сначала выполните:  pip install pypdf')

here   = os.path.dirname(os.path.abspath(__file__))
folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join('assets', 'MAP')
limit  = int(sys.argv[2]) if len(sys.argv) > 2 else 3
folder = folder if os.path.isabs(folder) else os.path.join(here, folder)
backup = os.path.join(here, '_pdf_originals')
if not os.path.isdir(folder): sys.exit('Нет папки: ' + folder)

done = skipped = failed = 0
for dp, _, files in os.walk(folder):
    for f in files:
        if not f.lower().endswith('.pdf'): continue
        path = os.path.join(dp, f)
        rel = os.path.relpath(path, here)
        try:
            r = PdfReader(path); n = len(r.pages)
            if n <= limit:
                skipped += 1; print('  оставлен (%d стр.)  %s' % (n, rel)); continue
            w = PdfWriter()
            for i in range(limit): w.add_page(r.pages[i])
            tmp = path + '.tmp'
            with open(tmp, 'wb') as out: w.write(out)
            r.stream.close() if hasattr(r.stream, 'close') else None
            bp = os.path.join(backup, rel); os.makedirs(os.path.dirname(bp), exist_ok=True)
            if not os.path.exists(bp): shutil.copy2(path, bp)
            os.replace(tmp, path)
            done += 1; print('  обрезан %d -> %d стр.  %s' % (n, limit, rel))
        except Exception as e:
            failed += 1; print('  ОШИБКА  %s: %s' % (rel, e))
print('\nОбрезано: %d, без изменений: %d, ошибок: %d' % (done, skipped, failed))
if done: print('Оригиналы лежат в: ' + backup + '  (на сайт их не загружайте)')
