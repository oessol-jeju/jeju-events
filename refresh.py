#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
제주 공연·행사 통합 수집기
    python3 refresh.py                 # 이번달~다음달
    python3 refresh.py 2026-09 2026-10 # 기간 지정
출력: out/jeju_events_YYYYMMDD.csv  (구글시트에 '가져오기 > 시트 바꾸기'로 붙이면 끝)
"""
import re, csv, sys, json, html, os, subprocess, unicodedata, datetime
from concurrent.futures import ThreadPoolExecutor

BASE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(BASE, 'out'); os.makedirs(OUT, exist_ok=True)
UA   = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36'

def get(url, timeout=30, tries=2):
    import time as _t
    for i in range(tries):
        try:
            r = subprocess.run(['curl','-s','--compressed','-m',str(timeout),'-A',UA,'-L',url], capture_output=True)
            body = r.stdout.decode('utf-8','replace')
            if r.returncode == 0 and len(body) > 200:
                return body
        except Exception:
            pass
        _t.sleep(1.5 * (i + 1))
    print('  ! 못 가져옴:', url[:80])
    return ''

def flat(s):
    s = re.sub(r'<script.*?</script>','',s,flags=re.S); s = re.sub(r'<style.*?</style>','',s,flags=re.S)
    s = re.sub(r'<[^>]+>','|',s); s = html.unescape(s)
    s = re.sub(r'\s+',' ',s); return re.sub(r'(\|\s*)+','|',s)

def strip(x, cutters=(r'\|', r'✨', r'❍', r'📍', r'▶')):
    v = x or ''
    for c in cutters: v = re.split(c, v)[0]
    return re.sub(r'\s+',' ',v).strip(' -|,')

# ─────────────────────────── 1. 제주문화예술진흥원 (문예회관) ───────────────────────────
def src_munye(months):
    rows=[]
    for kind, path in (('공연','month1'), ('전시','month2')):
        seqs=[]
        for y,m in months:
            h = get(f'https://www.jeju.go.kr/jejuculture/show/{path}/calendar1.htm?year={y}&month={m}', tries=6)
            found = re.findall(rf'calendar1[.]htm[?]year={y}&amp;month={m}&amp;act=view&amp;seq=(\d+)"', h)
            if not found:
                print(f'    ⚠ 문예회관 {kind} {y}-{m} 달력을 못 읽었습니다 (일정이 없거나 사이트 응답 불안정)')
            seqs += found
        def one(sq):
            h = get(f'https://www.jeju.go.kr/jejuculture/show/{path}/calendar1.htm?act=view&seq={sq}&_layout=iframe&_view=null')
            t = flat(h)
            g = lambda p:(re.search(p,t).group(1).strip() if re.search(p,t) else '')
            raw = g(r'문화예술진흥원\|(.*?)\|')
            mt  = re.search(r'[「『](.+?)[」』]', raw)
            img = re.search(r'<img[^>]+src="(/files/[^"]+)"', h)
            return dict(구분=kind, 명칭=(mt.group(1) if mt else raw), 일시=g(r'\|일시\|(.*?)\|'),
                        이미지=('https://www.jeju.go.kr' + img.group(1)) if img else '',
                        시간=strip(g(r'\|공연시간\|(.*?)\|')), 장소=g(r'\|장소\s*\|(.*?)\|')+' (제주문예회관)',
                        요금=strip(g(r'\|관람료\|(.*?)\|')), 주최=strip(g(r'\|주최\|(.*?)\|')),
                        문의=strip(g(r'\|문의\|(.*?)\|')), 출처='제주문화예술진흥원',
                        링크=f'https://www.jeju.go.kr/jejuculture/show/{path}/calendar1.htm?act=view&seq={sq}')
        with ThreadPoolExecutor(max_workers=4) as ex:
            rows += [r for r in ex.map(one, dict.fromkeys(seqs)) if r and r.get('명칭')]
    return rows

# ─────────────────────────── 2. 플레이제주 ───────────────────────────
PJ_BOARDS = {'concert':'콘서트·뮤지컬','drama':'연극','classic':'클래식·오페라','korean':'국악·무용',
             'exhibition':'전시','festival':'행사·축제','family':'아동·가족'}
def src_playjeju(months):
    import urllib.parse
    jobs = [(bo, cat, sca) for bo, cat in PJ_BOARDS.items() for sca in ('예정', '공연중')]
    def crawl(job):
        bo, cat, sca = job
        rows = []
        for page in range(1, 7):
            s = get(f'https://www.playjeju.co.kr/bbs/board.php?bo_table={bo}&sca={urllib.parse.quote(sca)}&page={page}')
            blocks = re.split(r'<div class="list-row">', s)[1:]
            if not blocks: break
            for b in blocks:
                m = re.search(r'<strong class="en">(.*?)</strong>(.*?)(?:</div>\s*</div>\s*</div>\s*</div>)', b, re.S)
                if not m: continue
                cl = lambda x: re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',x))).strip()
                divs = [d for d in (cl(d) for d in re.findall(r'<div class="text-muted font-13"[^>]*>(.*?)</div>', m.group(2), re.S)) if d]
                date  = next((d for d in divs if re.search(r'\d{4}-\d{2}-\d{2}', d)), '')
                venue = next((d for d in divs if not re.search(r'\d{4}-\d{2}-\d{2}', d)), '')
                if not date: continue
                im = re.search(r'<img src="([^"]+)"[^>]*class="wr-img"', b)
                rows.append(dict(구분=cat, 명칭=cl(m.group(1)), 일시=date, 시간='', 장소=venue,
                    이미지=(im.group(1) if im else ''),
                    요금=('무료' if re.search(r'>\s*무료\s*<', b) else ''), 주최='', 문의='', 출처='플레이제주',
                    링크='https://www.playjeju.co.kr/bbs/board.php?bo_table=%s&wr_id=%s' % (bo,(re.search(r'wr_id=(\d+)',b) or ['',''])[1])))
            if len(blocks) < 10: break
        return rows
    with ThreadPoolExecutor(max_workers=6) as ex:
        return [r for chunk in ex.map(crawl, jobs) for r in chunk]

# ─────────────────────────── 3. 제주아트센터 ───────────────────────────
def src_artcenter(months):
    rows=[]
    for kind, base in (('공연','perf'), ('전시','exbit')):
        ids=[]; poster={}
        for y,m in months:
            page = get(f'https://www.jejusi.go.kr/acenter/show/{base}.do?year={y}&month={m}', tries=6)
            ids += re.findall(r'showId=(\d+)', page)
            for chunk in re.split(r'(?=showId=)', page)[1:]:
                sid = re.match(r'showId=(\d+)', chunk)
                fid = re.search(r'/acenter/api/download\.ac\?fileId=(\d+)', chunk[:1200])
                if sid and fid and sid.group(1) not in poster:
                    poster[sid.group(1)] = f'https://www.jejusi.go.kr/acenter/api/download.ac?fileId={fid.group(1)}'
        for sid in dict.fromkeys(ids):
            t = flat(get(f'https://www.jejusi.go.kr/acenter/show/{base}/view.do?showId={sid}'))
            g = lambda p:(re.search(p,t).group(1).strip() if re.search(p,t) else '')
            title = g(r'\|([^|]{2,120})\|장르\|'); pre = g(r'\|(\[[^\]]*\])\|[^|]{2,120}\|장르\|')
            rows.append(dict(구분=f'{kind}(제주아트센터)', 명칭=(pre+' '+title).strip() if pre else title,
                이미지=poster.get(sid, ''),
                일시=g(r'\|일시\|(.*?)\|'), 시간=g(r'\|시작시간\|(.*?)\|'), 장소='제주아트센터',
                요금=g(r'\|관람료\|(.*?)\|'), 주최=g(r'\|주최, 주관\|(.*?)\|'), 문의=g(rf'\|{kind}문의\|(.*?)\|'),
                출처='제주아트센터', 링크=f'https://www.jejusi.go.kr/acenter/show/{base}/view.do?showId={sid}'))
    return rows

# ─────────────────────────── 4. 서귀포시 문화행사일정 ───────────────────────────
def src_seogwipo(months):
    rows=[]
    for y,m in months:
        s = get(f'https://www.seogwipo.go.kr/tourismculture/culture/schedule1.htm?year={y}&month={m}', tries=6)
        for blk in re.findall(r'<div class="list schedule-item"(.*?)</div>', s, re.S):
            a = dict(re.findall(r'data-([a-z0-9-]+)="(.*?)"', blk, re.S))
            if 'title' not in a: continue
            u = lambda k: re.sub(r'\s+', ' ', html.unescape(a.get(k, ''))).strip()
            img = u('image')
            if img and img.startswith('/'): img = 'https://www.seogwipo.go.kr' + img
            rows.append(dict(구분=f"{u('type')}(서귀포시)", 명칭=u('title'),
                일시=u('date-range') or u('period'), 시간=u('time'), 장소=u('place'),
                요금='', 주최=u('organizer'), 문의=u('contact'), 이미지=img,
                출처='서귀포시 문화행사일정',
                링크=(u('homepage') or 'https://www.seogwipo.go.kr/tourismculture/culture/schedule1.htm')))
    return rows

# ─────────────────────────── 5. 제주문화예술재단 (공고 API) ───────────────────────────
def src_jfac(months):
    rows=[]; want={f'{y}-{int(m):02d}' for y,m in months}
    for p in range(1, 5):
        try: d = json.loads(get(f'https://www.jfac.kr/api/archive/noticesList?page={p}&size=50'))
        except Exception: break
        ns = d.get('notices') or []
        if not ns: break
        for n in ns:
            title = (n.get('title') or '').strip()
            # 공고 게시판이라 모집·공모·휴관 같은 행정 글이 대부분이다. 실제 개최 안내만 남긴다.
            if re.search(r'모집|공모|채용|휴관|휴무|간담회|설명회|심의|결과\s*발표|결과발표|대관\s*공고|연장|안내 사항', title):
                continue
            if not re.search(r'개최|전시|공연|축제|콘서트|페스티벌|음악회|상영|展', title):
                continue
            # 지난 연도 공고가 올해로 잘못 찍히는 걸 막는다
            if n.get('createTime', '')[:4] not in {str(y) for y, _ in months}:
                continue
            t = re.sub(r'\s+',' ', html.unescape(re.sub(r'<[^>]+>',' ', n.get('content') or '')))
            per = re.search(r'(?:전시\s*기간|공연\s*기간|행사\s*기간|기간|일시)\s*[:：]?\s*([^|]{4,60})', t)
            if not per: continue
            seg = per.group(1)
            if not any(re.search(rf'(?:{y}[.\-년]\s*)?{int(m)}\s*[.\-월]\s*\d{{1,2}}', seg) for y,m in months): continue
            loc = re.search(r'(?:장소|전시\s*장소|공연\s*장소)\s*[:：]\s*([^|]{2,60})', t)
            rows.append(dict(구분='재단 공고', 명칭=re.sub(r'^\[?안내\]?\s*', '', title), 일시=seg.strip(), 시간='',
                장소=(loc.group(1).strip() if loc else ''), 요금='', 주최=n.get('author',''), 문의='',
                출처='제주문화예술재단', 링크=f"https://www.jfac.kr/notification/notice/{n['id']}"))
        if len(ns) < 50: break
    return rows


# ─────────────────────────── 6. 비짓제주 (오픈API + 상세 페이로드) ───────────────────────────
# 목록: 오픈API category=c5 (축제/행사) 로 전체 ID·제목·주소·전화를 받는다.
# 날짜: API에는 기간 필드가 없어서, 상세 페이지의 Nuxt 페이로드에서
#       stday / fnsday / sttime / pricetype / host 를 꺼낸다.
# 상세는 1건당 800KB라 visitjeju_cache.json 에 캐시하고, 진행중·예정 건만 다시 확인한다.
VJ_API = 'https://api.visitjeju.net/vsjApi/contents/searchList'

def _vj_key():
    k = os.environ.get('VISITJEJU_API_KEY', '').strip()
    if k: return k
    f = os.path.join(BASE, 'visitjeju_apikey.txt')
    return open(f, encoding='utf-8').read().strip() if os.path.exists(f) else ''

def _vj_detail(cid):
    """상세 페이지 Nuxt 페이로드에서 축제 정보를 꺼낸다."""
    s = get(f'https://www.visitjeju.net/kr/festival/view?contentsid={cid}&menuId=DOM_000001718007000000')
    m = re.search(r'__NUXT_DATA__[^>]*>(\[.*?\])</script>', s, re.S)
    if not m: return {}
    try: arr = json.loads(m.group(1))
    except Exception: return {}
    hit = re.search(r'"festivalcontents"\s*:\s*(\d+)', s)
    if not hit: return {}
    def deref(v, d=0):
        if d > 6: return None
        if isinstance(v, int) and 0 <= v < len(arr): return deref(arr[v], d + 1)
        if isinstance(v, list): return [deref(x, d + 1) for x in v]
        if isinstance(v, dict): return {k: deref(x, d + 1) for k, x in v.items()}
        return v
    node = deref(int(hit.group(1)))
    while isinstance(node, list) and node: node = node[0]
    if not isinstance(node, dict): return {}
    pt = node.get('pricetype') or {}
    return {
        'stday':   node.get('stday') or '', 'fnsday': node.get('fnsday') or '',
        'sttime':  node.get('sttime') or '', 'fnstime': node.get('fnstime') or '',
        'pricetype': (pt.get('label') if isinstance(pt, dict) else '') or '',
        'price':   node.get('price'),
        'host':    node.get('host') or '', 'sponsor': node.get('sponsor') or '',
    }

def src_visitjeju(months):
    key = _vj_key()
    if not key:
        print('    (비짓제주 API 키 없음 — visitjeju_apikey.txt 를 만들어 주세요)')
        return []
    listing = {}
    for page in range(1, 30):
        try:
            d = json.loads(get(f'{VJ_API}?apiKey={key}&locale=kr&page={page}&category=c5', tries=6))
        except Exception:
            break
        if d.get('result') != '200':
            print('    비짓제주 API 응답 이상:', d.get('result'), d.get('resultMessage')); break
        its = d.get('items') or []
        for i in its:
            listing[i['contentsid']] = i
        if page >= (d.get('pageCount') or 1): break

    cpath = os.path.join(BASE, 'visitjeju_cache.json')
    cache = {}
    if os.path.exists(cpath):
        try: cache = json.load(open(cpath, encoding='utf-8'))
        except Exception: cache = {}

    # 다시 확인하는 대상: 캐시에 없는 것 + 최근/임박한 행사(날짜가 아직 바뀔 수 있음).
    # 이미 시작해서 길게 가는 상설 전시 같은 건 매번 다시 볼 필요가 없다.
    t = datetime.date.today()
    lo = (t - datetime.timedelta(days=30)).strftime('%Y%m%d')
    hi = (t + datetime.timedelta(days=120)).strftime('%Y%m%d')
    def recheck(c):
        if c not in cache: return True
        st = cache[c].get('stday') or ''
        fn = cache[c].get('fnsday') or ''
        if not st: return True
        return lo <= st <= hi or (fn and lo <= fn <= hi)
    todo = [c for c in listing if recheck(c)]
    if todo:
        print(f'    상세 조회 {len(todo)}건 (캐시 {len(cache)}건)')
        with ThreadPoolExecutor(max_workers=10) as ex:
            for cid, det in zip(todo, ex.map(_vj_detail, todo)):
                if det: cache[cid] = det
        try: json.dump(cache, open(cpath, 'w', encoding='utf-8'), ensure_ascii=False)
        except Exception: pass

    def ymd(v): return f'{v[0:4]}-{v[4:6]}-{v[6:8]}' if v and len(v) == 8 else ''
    rows = []
    for cid, it in listing.items():
        det = cache.get(cid) or {}
        a, b = ymd(det.get('stday', '')), ymd(det.get('fnsday', ''))
        if not a: continue
        fee = det.get('pricetype', '')
        if fee == '유료' and det.get('price'): fee = f"{int(det['price']):,}원"
        rows.append(dict(
            구분='축제·행사(비짓제주)', 명칭=it.get('title', ''),
            일시=(a if a == b or not b else f'{a} ~ {b}'),
            시간=det.get('sttime', ''),
            장소=it.get('roadaddress') or it.get('address') or '',
            요금=fee, 주최=det.get('host', ''), 문의=it.get('phoneno') or '',
            이미지=(((it.get('repPhoto') or {}).get('photoid') or {}).get('thumbnailpath') or ''),
            출처='비짓제주', 링크=f'https://www.visitjeju.net/kr/festival/view?contentsid={cid}'))
    return rows

# ─────────────────── 7. manual.csv (포스터 접수 · 인스타 · 재단 PDF · 손입력) ───────────────────
# 컬럼: 구분,명칭,일시,시간,장소,요금,주최,문의,출처,링크
# 자동 수집이 못 잡는 소규모 행사는 전부 여기로 들어온다.
def src_manual(months):
    f = os.path.join(BASE, 'manual.csv')
    if not os.path.exists(f): return []
    out = []
    with open(f, encoding='utf-8-sig') as fh:
        for r in csv.DictReader(fh):
            r = {k: (v or '').strip() for k, v in r.items() if k}
            if not r.get('명칭'): continue
            r.setdefault('출처', '직접등록')
            out.append(r)
    return out

# ─────────────────────────── 정규화 · 병합 ───────────────────────────
def parse_dates(s, year_hint=None):
    s = s or ''
    ds = re.findall(r'(20\d{2})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})', s)
    out = [f'{a}-{int(b):02d}-{int(c):02d}' for a, b, c in ds]
    if not out and year_hint:
        md = re.findall(r'(?<!\d)(\d{1,2})\s*[.월]\s*(\d{1,2})\s*[.일]?', s)
        md = [(int(a), int(b)) for a, b in md if 1 <= int(a) <= 12 and 1 <= int(b) <= 31]
        out = [f'{year_hint}-{a:02d}-{b:02d}' for a, b in md[:2]]
    if not out: return '', ''
    a, b = out[0], (out[1] if len(out) > 1 else out[0])
    return (a, b) if b >= a else (a, a)

def key(t):
    t = unicodedata.normalize('NFC', t or '')
    t = re.sub(r'<(자체|대관)>|[「」『』<>《》〈〉\[\]()]|공연|무료','', t)
    return re.sub(r'[\s·:,\'"~\-—]','', t).lower()[:24]

def balance(t):
    for o,c in (('「','」'),('『','』'),('《','》'),('〈','〉'),('<','>'),('(',')'),('[',']')):
        if t.count(o) != t.count(c): t = t.replace(o,'').replace(c,'')
    return re.sub(r'\s+',' ',t).strip()

def categorize(g, t):
    if '전시' in g: return '전시'
    if any(k in g for k in ('콘서트','뮤지컬','클래식','오페라','국악','무용','연극','공연')): return '공연'
    if '아동' in g or '가족' in g: return '아동·가족'
    if '축제' in g or '행사' in g: return '축제·행사'
    if re.search(r'전시|展|미술관|갤러리', t): return '전시'
    if re.search(r'콘서트|공연|리사이틀|연주회|뮤지컬|연극|오페라', t): return '공연'
    return '기타'

SGP = r'서귀포|중문|성산|표선|남원|안덕|대정|기당|소암|이중섭|가파도|마라도|김창열|본태|김정문화회관|새연교|약천사'
JJU = r'제주시|한림|애월|조천|구좌|한경|우도|추자|제주문예회관|제주아트센터|제주도립미술관|제주현대미술관|산지천|예술공간 이아|제주아트플랫폼|김택화|해녀박물관|설문대|관덕정|제주목|제주문학관|이디홀|세이레|9\.81|김영갑|저지|한라'

def build(months, extra=None):
    S = f'{months[0][0]}-{int(months[0][1]):02d}-01'
    ly, lm = months[-1]
    E = f'{ly}-{int(lm):02d}-31'
    raw = []
    for name, fn in (('문예회관',src_munye), ('플레이제주',src_playjeju), ('제주아트센터',src_artcenter),
                     ('서귀포시',src_seogwipo), ('재단공고',src_jfac), ('비짓제주',src_visitjeju), ('직접등록',src_manual)):
        try:
            got = fn(months); raw += got; print(f'  {name:8s} {len(got):4d}건')
        except Exception as e:
            print(f'  {name:8s} 실패: {e}')
    raw += (extra or [])

    merged = {}
    for r in sorted(raw, key=lambda x: x.get('명칭','')):
        a, b = parse_dates(r.get('일시',''), year_hint=months[0][0])
        if not a or b < S or a > E: continue
        t = balance(re.sub(r'^<(자체|대관)>\s*','', re.sub(r'\s+',' ', r.get('명칭','')).strip()))
        t = re.sub(r'^[📢📌🎉📜⏰💫🎈✨]+\s*','', t).strip()
        if len(t) < 2: continue
        k = (key(t), a)
        rec = dict(카테고리=categorize(r.get('구분',''), t), 명칭=t, 시작일=a, 종료일=b,
                   시간=strip(r.get('시간',''))[:35], 장소=strip(r.get('장소',''))[:60],
                   요금=strip(r.get('요금',''))[:40], 주최=strip(r.get('주최',''))[:45],
                   문의=strip(r.get('문의',''))[:40], 이미지=(r.get('이미지','') or '').strip(),
                   출처=r.get('출처',''), 링크=r.get('링크',''))
        if k in merged:
            m = merged[k]
            for f in ('시간','장소','요금','주최','문의','이미지'):
                if not m[f] and rec[f]: m[f] = rec[f]
            if rec['출처'] not in m['출처']: m['출처'] += ' / ' + rec['출처']
            if len(rec['명칭']) > len(m['명칭']): m['명칭'] = rec['명칭']
        else:
            merged[k] = rec

    rows = sorted(merged.values(), key=lambda x: (x['시작일'], x['명칭']))
    for i, r in enumerate(rows, 1):
        s = r['장소'] + ' ' + r['명칭']
        r['번호'] = i
        r['지역'] = '서귀포시' if re.search(SGP, s) else ('제주시' if re.search(JJU, s) else '')
        r['무료'] = 'Y' if re.search(r'무료|free', r['요금']+' '+r['명칭'], re.I) else \
                    ('N' if re.search(r'\d{1,3},?\d{3}\s*원|유료|R석|전석', r['요금']) else '')
        r['비고'] = ''
    return rows

def main():
    if len(sys.argv) >= 3:
        months = [tuple(map(int, a.split('-'))) for a in sys.argv[1:3]]
    else:
        t = datetime.date.today()
        n = (t.replace(day=28) + datetime.timedelta(days=7))
        months = [(t.year, t.month), (n.year, n.month)]
    print('수집 대상:', ', '.join(f'{y}년 {m}월' for y, m in months))
    rows = build(months)
    cols = ['번호','카테고리','명칭','시작일','종료일','시간','장소','지역','무료','요금','주최','문의','이미지','출처','링크','비고']
    p = os.path.join(OUT, 'jeju_events_%s.csv' % datetime.date.today().strftime('%Y%m%d'))
    with open(p, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    print(f'\n총 {len(rows)}건 → {p}')
    from collections import Counter
    print(dict(Counter(r['카테고리'] for r in rows)))

if __name__ == '__main__':
    main()
