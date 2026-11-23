# Обрезает все PDF в папке assets (и вложенных) до первых N страниц.
# Оригиналы сохраняются в папку _originals_pdf рядом со скриптом (с той же структурой).
# Запуск: положи файл рядом с index.html и дважды кликни, либо в CMD: py obrezat_pdf.py
# Нужен пакет: py -m pip install pypdf
import os, shutil, sys
from pypdf import PdfReader, PdfWriter

N = 3                      # сколько страниц оставить
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
BACKUP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_originals_pdf')

done = skipped = 0
for dp, _, files in os.walk(ROOT):
    for f in files:
        if not f.lower().endswith('.pdf'): continue
        p = os.path.join(dp, f)
        try:
            r = PdfReader(p)
            n = len(r.pages)
            if n <= N:
                skipped += 1; continue
            b = os.path.join(BACKUP, os.path.relpath(p, ROOT))
            os.makedirs(os.path.dirname(b), exist_ok=True)
            if not os.path.exists(b): shutil.copy2(p, b)
            w = PdfWriter()
            for i in range(N): w.add_page(r.pages[i])
            w.compress_identical_objects()
            tmp = p + '.tmp'
            with open(tmp, 'wb') as o: w.write(o)
            os.replace(tmp, p)
            print(f'{n} -> {N} стр.: {os.path.relpath(p, ROOT)}'); done += 1
        except Exception as e:
            print('ОШИБКА', p, e)
print(f'Готово. Обрезано: {done}, без изменений: {skipped}')
input('Нажми Enter для выхода...')
