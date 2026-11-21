# -*- coding: utf-8 -*-
"""
Читает РЕАЛЬНЫЕ имена файлов из assets/UIK и пересобирает блок площадок
в index.html (между строками // UIK-START и // UIK-END).
Запуск: положить рядом с index.html и выполнить   python make_uik.py
Можно указать пути:  python make_uik.py <папка UIK> <index.html>
"""
import os, re, sys, json, shutil, unicodedata

here = os.path.dirname(os.path.abspath(__file__))
uik_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, 'assets', 'UIK')
index   = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, 'index.html')

nfc = lambda s: unicodedata.normalize('NFC', s)
def nat(n): return [(0, int(t)) if t.isdigit() else (1, t.lower()) for t in re.split(r'(\d+)', nfc(n)) if t != '']
ORDER = ['ДИК', 'ГОР', 'КБ', 'КК', 'МИФ', 'SF', 'X', 'K', 'Dom', 'Igrovoj']
IMG = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')

if not os.path.isdir(uik_dir): sys.exit('Нет папки: ' + uik_dir)
rows = []
for folder in os.listdir(uik_dir):
    fp = os.path.join(uik_dir, folder)
    if not os.path.isdir(fp): continue
    files = [f for f in os.listdir(fp) if os.path.isfile(os.path.join(fp, f))]
    def is_img(f):
        l = nfc(f).lower()
        return l.endswith(IMG) and 'копия' not in l and 'точечный' not in l
    imgs = sorted((f for f in files if is_img(f)),
                  key=lambda f: (0 if re.match(r'^[0оo]бщий', nfc(f).lower()) else 1, nat(f)))
    man = prim = ''; docs = []
    for f in sorted(files, key=nat):
        l = nfc(f).lower()
        if l == 'primer.pdf': prim = f
        elif l.endswith('.pdf') and ('инстр' in l or l == 'ins.pdf' or 'балкон' in l or l.startswith('igrovoj_domik')): man = f
        elif l.endswith('.docx') and 'паспорт' in l: docs.append(f)
    m = re.search(r'(\d{3,5})[хx](\d{3,5})[хx](\d{3,5})', nfc(' '.join(files)))
    desc = 'Размеры: %s × %s × %s мм' % m.groups() if m else ''
    t = nfc(folder)
    t = re.sub(r'^Igrovoj Domik ', 'Игровой домик ', t); t = re.sub(r'^Dom ', 'Дом ', t)
    t = re.sub(r'^K-', 'К-', t); t = re.sub(r'^X(\d)', r'Х-\1', t); t = t.replace('_', '.')
    pr = next((i for i, o in enumerate(ORDER) if nfc(folder).startswith(o)), 99)
    rows.append((pr, nat(folder), folder, t, desc, imgs, man, prim, docs))
rows.sort(key=lambda r: (r[0], r[1]))

out = ['  // UIK-START  (блок создан скриптом make_uik.py, вручную не править)',
       '  // ===== Детские площадки (assets/UIK) =====',
       '  // [папка, название, описание, [картинки], инструкция, пример, [другие документы]]',
       '  const UIK_DATA=[']
for r in rows:
    out.append('    ' + json.dumps([r[2], r[3], r[4], r[5], r[6], r[7], r[8]], ensure_ascii=False) + ',')
out.append('  ];')
out.append("  const UIK=UIK_DATA.map(([f,title,desc,imgs,man,prim,docs],i)=>{const d='assets/UIK/'+f+'/';return {id:'uik-'+(i+1),group:'outdoor',title,desc,renders:imgs.map(x=>d+x),manual:man?d+man:'',docs:[...(prim?[{title:'Пример',file:d+prim}]:[]),...docs.map(x=>({title:x.replace(/\\.[^.]+$/,''),file:d+x}))]}});")
out.append('  // UIK-END')
block = '\n'.join(out)

s = open(index, encoding='utf-8').read()
pat = re.compile(r'[ \t]*// UIK-START.*?// UIK-END', re.S)
if not pat.search(s): sys.exit('В index.html нет маркеров // UIK-START ... // UIK-END')
shutil.copy(index, index + '.bak')
s = pat.sub(lambda _: block, s, count=1)
open(index, 'w', encoding='utf-8').write(s)

print('Готово. Площадок: %d  (копия: index.html.bak)' % len(rows))
for r in rows:
    flag = '' if r[5] else '   <-- НЕТ КАРТИНОК'
    print('  %-24s картинок: %2d  инструкция: %s%s' % (r[2], len(r[5]), 'да' if r[6] else 'нет', flag))
