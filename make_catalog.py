# -*- coding: utf-8 -*-
"""
Читает РЕАЛЬНЫЕ имена файлов с диска и пересобирает блоки в index.html:
  assets/UIK  -> между  // UIK-START  и  // UIK-END   (уличные площадки)
  assets/EX   -> между  // EX-START   и  // EX-END    (экстерьер)
Запуск: положить рядом с index.html и выполнить   python make_catalog.py
Другие пути:  python make_catalog.py <корень сайта>
"""
import os, re, sys, json, shutil, unicodedata

root  = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
index = os.path.join(root, 'index.html')

nfc = lambda s: unicodedata.normalize('NFC', s)
def nat(n): return [(0, int(t)) if t.isdigit() else (1, t.lower()) for t in re.split(r'(\d+)', nfc(n)) if t != '']
IMG = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')

def subdirs(d):
    return [f for f in os.listdir(d) if os.path.isdir(os.path.join(d, f))]

# ---------------- UIK: уличные площадки ----------------
def build_uik(d):
    ORDER = ['ДИК', 'ГОР', 'КБ', 'КК', 'МИФ', 'SF', 'X', 'K', 'Dom', 'Igrovoj']
    rows = []
    for folder in subdirs(d):
        fp = os.path.join(d, folder)
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
    out = ['  // UIK-START  (блок создан скриптом make_catalog.py, вручную не править)',
           '  // ===== Детские площадки (assets/UIK) =====',
           '  // [папка, название, описание, [картинки], инструкция, пример, [другие документы]]',
           '  const UIK_DATA=[']
    for r in rows:
        out.append('    ' + json.dumps([r[2], r[3], r[4], r[5], r[6], r[7], r[8]], ensure_ascii=False) + ',')
    out += ['  ];',
      "  const UIK=UIK_DATA.map(([f,title,desc,imgs,man,prim,docs],i)=>{const d='assets/UIK/'+f+'/';return {id:'uik-'+(i+1),group:'outdoor',title,desc,renders:imgs.map(x=>d+x),manual:man?d+man:'',docs:[...(prim?[{title:'Пример',file:d+prim}]:[]),...docs.map(x=>({title:x.replace(/\\.[^.]+$/,''),file:d+x}))]}});",
      '  // UIK-END']
    rep = ['%-24s картинок: %2d  инструкция: %s%s' % (r[2], len(r[5]), 'да' if r[6] else 'нет', '' if r[5] else '   <-- НЕТ КАРТИНОК') for r in rows]
    return '\n'.join(out), rep

# ---------------- EX: экстерьер ----------------
def build_ex(d):
    rows = []
    for folder in subdirs(d):
        fp = os.path.join(d, folder)
        imgs = [f for f in os.listdir(fp) if os.path.isfile(os.path.join(fp, f)) and nfc(f).lower().endswith(IMG)]
        # планы — в конец, остальное по номерам
        imgs.sort(key=lambda f: (1 if nfc(f).lower().startswith('план') else 0, nat(f)))
        rows.append((nat(folder), folder, imgs))
    rows.sort(key=lambda r: r[0])
    out = ['  // EX-START  (блок создан скриптом make_catalog.py, вручную не править)',
           '  // ===== Экстерьер (assets/EX): [папка, [картинки]] =====',
           '  const EXT_DATA=[']
    for _, f, imgs in rows:
        out.append('    ' + json.dumps([f, imgs], ensure_ascii=False) + ',')
    out += ['  ];',
      "  const EXT=EXT_DATA.map(([f,imgs])=>{const d='assets/EX/'+f+'/';return {id:'ex-'+f,group:'exterior',title:'Экстерьер '+f,desc:'',renders:imgs.map(x=>d+x),manual:'',docs:[]}});",
      '  // EX-END']
    rep = ['%-24s картинок: %2d%s' % (r[1], len(r[2]), '' if r[2] else '   <-- НЕТ КАРТИНОК') for r in rows]
    return '\n'.join(out), rep

if not os.path.isfile(index): sys.exit('Нет файла: ' + index)
s = open(index, encoding='utf-8').read()
shutil.copy(index, index + '.bak')
for name, folder, fn in (('UIK', 'UIK', build_uik), ('EX', 'EX', build_ex)):
    d = os.path.join(root, 'assets', folder)
    pat = re.compile(r'[ \t]*// %s-START.*?// %s-END' % (name, name), re.S)
    if not os.path.isdir(d): print('[%s] пропущено: нет папки %s' % (name, d)); continue
    if not pat.search(s): print('[%s] пропущено: в index.html нет маркеров // %s-START ... // %s-END' % (name, name, name)); continue
    block, rep = fn(d)
    s = pat.sub(lambda _: block, s, count=1)
    print('[%s] готово, папок: %d' % (name, len(rep)))
    for line in rep: print('   ', line)
open(index, 'w', encoding='utf-8').write(s)
print('Копия прежнего файла: index.html.bak')
