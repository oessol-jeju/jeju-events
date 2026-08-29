# -*- coding: utf-8 -*-
"""인스타용 홍보 이미지 생성 — 실제 포스터 모자이크 + AMF 톤(검정·네온옐로우)"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, random, json, sys

BASE = os.path.dirname(os.path.abspath(__file__))
F    = '/System/Library/Fonts/AppleSDGothicNeo.ttc'
BOLD, HEAVY, MED, LIGHT = 6, 6, 2, 0      # Bold / Bold / Medium / Regular
HI   = (232, 255, 26)
INK  = (255, 255, 255)
DIM  = (150, 152, 146)

d = json.load(open(os.path.join(BASE, '..', 'docs', 'events.json'), encoding='utf-8'))
N     = len(d['events'])
FREE  = sum(1 for e in d['events'] if e['f'] == 'Y')

def tile_score(p):
    """디자인이 있는 포스터일수록 높은 점수. 단색 안내 이미지는 걸러낸다."""
    try:
        im = Image.open(p).convert('RGB'); im.thumbnail((80, 80))
    except Exception:
        return -1
    px = list(im.getdata())
    n = len(px)
    mean = [sum(c[i] for c in px) / n for i in range(3)]
    var = sum((c[0]-mean[0])**2 + (c[1]-mean[1])**2 + (c[2]-mean[2])**2 for c in px) / n
    colors = len({(c[0]//24, c[1]//24, c[2]//24) for c in px})
    return var ** 0.5 + colors * 1.5

_all = [os.path.join(BASE, 'tiles', f) for f in sorted(os.listdir(os.path.join(BASE, 'tiles')))]
_all = [t for t in _all if os.path.getsize(t) > 3000]
tiles = [t for t in sorted(_all, key=tile_score, reverse=True)[:30]]

def font(sz, idx=BOLD): return ImageFont.truetype(F, sz, index=idx)

def mosaic(W, H, cols, seed=3):
    """포스터를 격자로 채운 배경"""
    random.seed(seed)
    cw = W // cols
    ch = int(cw * 4 / 3)
    rows = H // ch + 2
    canvas = Image.new('RGB', (W, ch * rows), (10, 10, 9))
    pool = tiles[:]
    random.shuffle(pool)
    k = 0
    for r in range(rows):
        for c in range(cols):
            p = pool[k % len(pool)]; k += 1
            try:
                im = Image.open(p).convert('RGB')
            except Exception:
                continue
            # 4:3 세로로 크롭
            tr = cw / ch
            sr = im.width / im.height
            if sr > tr:
                nw = int(im.height * tr)
                im = im.crop(((im.width - nw) // 2, 0, (im.width + nw) // 2, im.height))
            else:
                nh = int(im.width / tr)
                im = im.crop((0, 0, im.width, min(nh, im.height)))
            im = im.resize((cw, ch), Image.LANCZOS)
            canvas.paste(im, (c * cw, r * ch))
    return canvas.crop((0, 0, W, H))

def veil(img, split, soft):
    """위쪽은 포스터가 보이고, 아래쪽은 검게 — 글자 영역을 확보한다."""
    W, H = img.size
    m = Image.new('L', (1, H)); px = m.load()
    for y in range(H):
        if y < split - soft:
            a = 0.30                                  # 위: 살짝만 어둡게
        elif y > split + soft:
            a = 0.97                                  # 아래: 거의 검정
        else:
            t = (y - (split - soft)) / (2 * soft)
            a = 0.30 + 0.67 * (t * t * (3 - 2 * t))   # 부드럽게 전환
        px[0, y] = int(255 * a)
    m = m.resize((W, H))
    return Image.composite(Image.new('RGB', (W, H), (7, 7, 6)), img, m)


def build(W, H, out, kind):
    cols = 4 if kind == 'feed' else 4
    bg = mosaic(W, H, cols=cols, seed=11)
    split = int(H * (0.42 if kind == 'feed' else 0.40))
    img = veil(bg, split, int(H * 0.06))
    dr = ImageDraw.Draw(img)

    M = int(W * 0.085)
    if kind == 'feed':                                  # 1080x1350
        y = split + int(H * 0.055)
        dr.text((M, y), 'WHAT’S ON IN JEJU', font=font(25, MED), fill=HI); y += 50
        dr.text((M, y), '9–10월 제주', font=font(96, HEAVY), fill=INK);    y += 116
        dr.text((M, y), '공연 · 전시 · 축제', font=font(52, MED), fill=INK); y += 96

        nf = font(104, HEAVY)
        dr.text((M, y), str(N), font=nf, fill=HI)
        w1 = dr.textlength(str(N), font=nf)
        dr.text((M + w1 + 12, y + 56), '개', font=font(40, MED), fill=INK)
        x2 = M + w1 + int(W * 0.16)
        dr.text((x2, y), str(FREE), font=nf, fill=INK)
        w2 = dr.textlength(str(FREE), font=nf)
        dr.text((x2 + w2 + 12, y + 56), '개 무료', font=font(40, MED), fill=DIM)
        y += 134
        dr.text((M, y), '매일 새벽 자동으로 갱신됩니다', font=font(31, LIGHT), fill=DIM)
        dr.text((M, H - int(H * 0.072)), '애월뮤직팩토리', font=font(26, MED), fill=DIM)
    else:                                               # 1080x1920
        y = split + int(H * 0.06)
        dr.text((M, y), 'WHAT’S ON IN JEJU', font=font(30, MED), fill=HI); y += 60
        dr.text((M, y), '9–10월', font=font(140, HEAVY), fill=INK);        y += 158
        dr.text((M, y), '제주', font=font(140, HEAVY), fill=INK);          y += 172
        dr.text((M, y), '공연 · 전시 · 축제', font=font(60, MED), fill=INK); y += 118

        nf = font(126, HEAVY)
        dr.text((M, y), str(N), font=nf, fill=HI)
        w1 = dr.textlength(str(N), font=nf)
        dr.text((M + w1 + 16, y + 70), '개', font=font(48, MED), fill=INK); y += 168
        dr.text((M, y), f'그중 {FREE}개는 무료', font=font(50, MED), fill=INK); y += 84
        dr.text((M, y), '매일 새벽 자동 갱신', font=font(38, LIGHT), fill=DIM)
        dr.text((M, H - int(H * 0.095)), '애월뮤직팩토리', font=font(30, MED), fill=DIM)
    img.save(out, quality=93)
    print(out, img.size, f'{N}건 / 무료 {FREE}')

build(1080, 1350, os.path.join(BASE, 'ig_feed.jpg'), 'feed')
build(1080, 1920, os.path.join(BASE, 'ig_story.jpg'), 'story')
