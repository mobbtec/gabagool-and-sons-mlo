# LONG PIG v0.2.9 — labelled preview sheets from the Blender renders (NOT in-game screenshots):
#   release/LONG_PIG_v0.2.9_hall.jpg          hall, counter, entrance, doors (after)
#   release/LONG_PIG_v0.2.9_back_of_house.jpg kitchen, storage, corridor, staff room, office, WC (after)
#   release/LONG_PIG_v0.2.9_after_hours.jpg   OPEN vs AFTER HOURS (+ night)
#   release/LONG_PIG_v0.2.9_before_after.jpg  v0.2.8 vs v0.2.9, same cameras
#   python gs_46_v029_sheets.py [<project_root>]
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
SS = ROOT / "screenshots"
OUT = ROOT / "release"
OUT.mkdir(exist_ok=True)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BG, FG, SUB, ACC = (24, 22, 21), (240, 234, 222), (170, 160, 150), (150, 40, 45)
TW, TH = 800, 450
FOOT = "Рендер Blender/Cycles по файлам сборки v0.2.9 — НЕ скриншот из FiveM. Свет в игре будет отличаться."


def font(sz, bold=False):
    return ImageFont.truetype(FONTB if bold else FONT, sz)


def tile(path, label, w=TW, h=TH):
    im = Image.new("RGB", (w, h + 40), BG)
    if path.is_file():
        im.paste(Image.open(path).convert("RGB").resize((w, h), Image.Resampling.LANCZOS), (0, 0))
    else:
        ImageDraw.Draw(im).text((20, h // 2), "нет кадра", font=font(24), fill=SUB)
    d = ImageDraw.Draw(im)
    d.text((12, h + 8), label, font=font(21), fill=FG)
    return im


def sheet(name, title, rows, cols, items):
    W = cols * TW + (cols + 1) * 12
    H = 90 + rows * (TH + 40 + 12) + 40
    sh = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sh)
    d.rectangle((0, 0, W, 6), fill=ACC)
    d.text((16, 22), title, font=font(34, True), fill=FG)
    for i, (p, lab) in enumerate(items):
        r, c = divmod(i, cols)
        sh.paste(tile(p, lab), (12 + c * (TW + 12), 90 + r * (TH + 52)))
    d.text((16, H - 32), FOOT, font=font(18), fill=SUB)
    sh.save(OUT / name, quality=88)
    print("SHEET", name, sh.size)


A, C, N, B = SS / "v029_after", SS / "v029_closed", SS / "v029_night", SS / "v029_before"
sheet("LONG_PIG_v0.2.9_hall.jpg", "LONG PIG v0.2.9 — зал, касса, вход", 3, 3, [
    (A / "GS26_HALL.png", "Зал: кабинки, витрины, плитка"), (A / "GS26_COUNTER.png", "Касса и витрины: принтер, звонок"),
    (A / "GS26_STAFF.png", "Вдоль витрин к двери EMPLOYEES ONLY"), (A / "GS29_DOORS_HALL.png", "Двери зала: кухня (окошко) и служебная"),
    (A / "GS29_P2.png", "Дверь P2, табличка EMPLOYEES ONLY"), (A / "V12b.png", "Служебная дверь крупно"),
    (A / "GS26_BLINDS_OUT.png", "Снаружи: витрина W1, неон OPEN"), (A / "GS29_SIGN_OUT.png", "Неон и табличка OPEN снаружи"),
    (A / "GS29_SECRET.png", "Офис: шкаф с тайником (сейф, книги)")])
sheet("LONG_PIG_v0.2.9_back_of_house.jpg", "LONG PIG v0.2.9 — кухня и подсобки", 4, 3, [
    (A / "GS28_KITCHEN.png", "Кухня: остров, линия под вытяжкой"), (A / "GS28_KITCHEN2.png", "Кухня: холодильники, стеллаж"),
    (A / "GS29_LINE.png", "Горячая линия под вытяжкой"), (A / "GS29_PREP.png", "Заготовка: ножи, подсветка, чеки"),
    (A / "GS28_CORRIDOR.png", "Служебный коридор"), (A / "GS28_STORAGE.png", "Склад: товар на стеллажах"),
    (A / "GS29_STORAGE.png", "Склад: стеллаж у двери, коробки"), (A / "GS28_BACKROOM.png", "Комната персонала"),
    (A / "GS28_OFFICE.png", "Офис"), (A / "GS29_OFFICE.png", "Офис: стол, credenza, выключатель"),
    (A / "GS28_WC.png", "Туалет персонала")])
sheet("LONG_PIG_v0.2.9_after_hours.jpg", "LONG PIG v0.2.9 — AFTER HOURS: открыто / закрыто", 2, 3, [
    (A / "GS26_HALL.png", "Открыто (lp_open), день"), (C / "GS26_HALL.png", "After Hours (lp_closed): стулья на столах, ведро"),
    (C / "GS26_COUNTER.png", "Касса в режиме After Hours"),
    (A / "GS29_SIGN_OUT.png", "Снаружи: неон и табличка OPEN"), (C / "GS29_SIGN_OUT.png", "Снаружи: табличка CLOSED, неон выключен"),
    (N / "GS29_SIGN_OUT_night.png", "Неон OPEN ночью")])
pairs = [("GS26_HALL", "Зал"), ("GS26_COUNTER", "Касса / витрины"), ("GS26_STAFF", "Проход к служебной двери"),
         ("GS28_KITCHEN", "Кухня"), ("GS28_KITCHEN2", "Кухня 2"), ("GS28_CORRIDOR", "Коридор"), ("GS28_STORAGE", "Склад"),
         ("GS28_BACKROOM", "Комната персонала"), ("GS28_OFFICE", "Офис"), ("GS28_WC", "Туалет"),
         ("GS26_BLINDS_OUT", "Вход снаружи"), ("V12b", "Служебная дверь")]
items = []
for v, lab in pairs:
    items += [(B / f"{v}.png", f"{lab} — ДО (v0.2.8)"), (A / f"{v}.png", f"{lab} — ПОСЛЕ (v0.2.9)")]
for k in range(0, len(items), 12):
    sheet(f"LONG_PIG_v0.2.9_before_after_{k // 12 + 1}.jpg", f"LONG PIG — до / после по зонам ({k // 12 + 1}/2)", 3, 4,
          items[k:k + 12])
