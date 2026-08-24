#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""수집 결과 CSV → 스퀘어스페이스 코드블록에 붙여넣을 HTML 한 덩어리를 만든다.
    python3 build_page.py                       # out/ 의 가장 최근 CSV 사용
    python3 build_page.py out/jeju_events_....csv
결과: out/amf_jeju_events_embed.html
"""
import csv, json, os, sys, glob, datetime, re, html

BASE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(BASE, 'out')
DOCS = os.path.join(BASE, 'docs'); os.makedirs(DOCS, exist_ok=True)

CONF = os.path.join(BASE, 'site_config.json')
conf = json.load(open(CONF, encoding='utf-8')) if os.path.exists(CONF) else {}
DATA_URL = conf.get('data_url', '').strip()

src = sys.argv[1] if len(sys.argv) > 1 else max(
    glob.glob(os.path.join(OUT, 'jeju_events_*.csv')), key=os.path.getmtime)
rows = list(csv.DictReader(open(src, encoding='utf-8-sig')))

CAT_ORDER = ['공연', '전시', '축제·행사', '아동·가족']
KST = datetime.timezone(datetime.timedelta(hours=9))
now_kst = datetime.datetime.now(KST)
today = now_kst.date().isoformat()

def clean(v):
    return re.sub(r'\s+', ' ', (v or '')).strip()

data = []
for r in rows:
    if r['종료일'] < today:          # 이미 끝난 건 뺀다
        continue
    data.append({
        't': clean(r['명칭']),
        'c': r['카테고리'],
        's': r['시작일'], 'e': r['종료일'],
        'h': clean(r['시간'])[:24],
        'v': clean(r['장소'])[:70],
        'r': r['지역'],
        'f': r['무료'],
        'p': clean(r['요금'])[:34],
        'o': clean(r['주최'])[:40],
        'i': r.get('이미지', ''),
        'u': r['링크'],
    })
data.sort(key=lambda x: (x['s'], x['t']))

months = sorted({d['s'][:7] for d in data} | {d['e'][:7] for d in data})
months = [m for m in months if m >= today[:7]][:4]

bundle = {'built': now_kst.strftime('%Y-%m-%d %H:%M'),
          'today': today, 'months': months,
          'cats': [c for c in CAT_ORDER if any(d['c'] == c for d in data)],
          'events': data}
json.dump(bundle, open(os.path.join(DOCS, 'events.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, separators=(',', ':'))

# data_url 이 있으면 인라인 데이터를 생략한다. 방문자가 쓰지도 않을 사본을 받지 않도록.
if DATA_URL:
    payload = '[]'
else:
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

TPL = r'''<!-- 제주 공연·행사 일정 · 자동 생성 ({{BUILT}}) · 총 {{N}}건 -->
<div id="jeju-on">
<style>
#jeju-on{--ink:#ffffff;--dim:#8f918c;--ground:#0a0a0a;--card:#141414;--line:#2b2b2b;--hi:#e8ff1a;
  background:var(--ground);color:var(--ink);margin:0 -1px;padding:clamp(38px,6vw,72px) clamp(16px,4vw,54px);
  font-family:"IBM Plex Sans KR",-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;
  font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased;box-sizing:border-box}
#jeju-on *,#jeju-on *::before,#jeju-on *::after{box-sizing:border-box}
#jeju-on .jo-eyebrow{font-family:"Archivo",sans-serif;font-weight:600;font-size:11.5px;letter-spacing:.22em;
  text-transform:uppercase;color:var(--hi);margin:0 0 14px}
#jeju-on h2.jo-h{font-family:"Archivo",sans-serif;font-weight:800;font-size:clamp(30px,6.4vw,62px);
  line-height:.98;letter-spacing:-.018em;margin:0;text-transform:uppercase;text-wrap:balance;color:var(--ink)}
#jeju-on .jo-sub{font-weight:600;font-size:clamp(15px,2.1vw,20px);margin:12px 0 0;color:var(--ink)}
#jeju-on .jo-lede{color:var(--dim);margin:8px 0 0;max-width:56ch;font-size:14px}
#jeju-on .jo-bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:30px 0 6px}
#jeju-on .jo-chip{appearance:none;border:1px solid var(--line);background:transparent;color:var(--dim);
  font:inherit;font-size:13px;font-weight:500;padding:7px 15px;border-radius:99px;cursor:pointer;
  transition:color .12s,border-color .12s,background .12s;white-space:nowrap}
#jeju-on .jo-chip:hover{color:var(--ink);border-color:var(--dim)}
#jeju-on .jo-chip[aria-pressed="true"]{background:var(--hi);border-color:var(--hi);color:#0a0a0a;font-weight:600}
#jeju-on .jo-sep{width:1px;height:20px;background:var(--line);margin:0 4px}
#jeju-on .jo-search{flex:1 1 190px;min-width:150px;border:1px solid var(--line);background:#000;color:var(--ink);
  font:inherit;font-size:14px;padding:8px 14px;border-radius:99px}
#jeju-on .jo-search::placeholder{color:#5e615c}
#jeju-on .jo-chip:focus-visible,#jeju-on .jo-search:focus-visible,#jeju-on .jo-card:focus-visible{
  outline:2px solid var(--hi);outline-offset:2px}
#jeju-on .jo-count{font-family:"Archivo",sans-serif;font-size:12px;letter-spacing:.06em;color:var(--dim);
  margin:14px 0 22px;font-variant-numeric:tabular-nums}
#jeju-on .jo-count b{color:var(--hi);font-weight:700}
#jeju-on .jo-grid{display:grid;gap:clamp(10px,2vw,24px);
  grid-template-columns:repeat(auto-fill,minmax(min(212px,100%),1fr))}
#jeju-on .jo-card{display:flex;flex-direction:column;background:var(--card);border:1px solid var(--line);
  border-radius:3px;overflow:hidden;text-decoration:none;color:inherit;transition:border-color .14s,transform .14s}
#jeju-on .jo-card:hover{border-color:var(--hi);transform:translateY(-3px)}
#jeju-on .jo-shot{position:relative;aspect-ratio:3/4;background:#1c1c1c;overflow:hidden}
#jeju-on .jo-shot img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .3s}
#jeju-on .jo-card:hover .jo-shot img{transform:scale(1.035)}
#jeju-on .jo-noimg{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
  padding:16px;text-align:center;font-family:"Archivo",sans-serif;font-weight:700;font-size:13px;
  letter-spacing:.04em;color:#4c4e49;text-transform:uppercase}
#jeju-on .jo-when{position:absolute;left:0;top:0;background:var(--hi);color:#0a0a0a;
  font-family:"Archivo",sans-serif;font-weight:700;font-size:11.5px;letter-spacing:.03em;
  padding:5px 10px;font-variant-numeric:tabular-nums}
#jeju-on .jo-free{position:absolute;right:0;top:0;background:#fff;color:#0a0a0a;font-weight:700;
  font-size:11px;padding:5px 9px;letter-spacing:.02em}
#jeju-on .jo-body{padding:13px 14px 15px;display:flex;flex-direction:column;gap:5px;flex:1}
#jeju-on .jo-cat{font-family:"Archivo",sans-serif;font-size:10px;font-weight:600;letter-spacing:.16em;
  text-transform:uppercase;color:var(--hi)}
#jeju-on .jo-name{font-weight:600;font-size:14.5px;line-height:1.35;margin:0;
  display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
#jeju-on .jo-meta{font-size:12.5px;color:var(--dim);line-height:1.45;margin-top:auto;padding-top:7px;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
#jeju-on .jo-empty{padding:64px 20px;text-align:center;color:var(--dim);border:1px dashed var(--line)}
#jeju-on .jo-foot{margin-top:34px;padding-top:20px;border-top:1px solid var(--line);
  color:#63655f;font-size:12px;display:flex;flex-wrap:wrap;gap:6px 18px;justify-content:space-between}
#jeju-on .jo-foot a{color:var(--dim)}
#jeju-on .jo-more{display:block;margin:28px auto 0;appearance:none;border:1px solid var(--line);
  background:transparent;color:var(--ink);font:inherit;font-weight:600;font-size:14px;
  padding:13px 34px;border-radius:99px;cursor:pointer}
#jeju-on .jo-more:hover{border-color:var(--hi);color:var(--hi)}
@media (max-width:600px){
  #jeju-on{padding:34px 14px 44px}
  #jeju-on .jo-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  #jeju-on .jo-bar{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;margin:18px -14px 0;padding:0 14px 2px}
  #jeju-on .jo-bar::-webkit-scrollbar{display:none}
  #jeju-on .jo-chip{flex:0 0 auto;font-size:12.5px;padding:6px 13px}
  #jeju-on .jo-search{flex:0 0 auto;width:min(60vw,240px)}
  #jeju-on .jo-name{font-size:13px;-webkit-line-clamp:2}
  #jeju-on .jo-meta{font-size:11.5px;-webkit-line-clamp:2}
  #jeju-on .jo-body{padding:10px 11px 12px}
  #jeju-on .jo-when{font-size:10.5px;padding:4px 8px}
  #jeju-on .jo-foot{flex-direction:column;gap:6px}
}
@media (prefers-reduced-motion:reduce){#jeju-on *{transition:none!important}}
</style>

<p class="jo-eyebrow">What&rsquo;s on in Jeju</p>
<h2 class="jo-h">제주 공연&middot;행사 일정</h2>
<p class="jo-lede">제주에서 열리는 공연&middot;전시&middot;축제를 한자리에 모았습니다. 카드를 누르면 주최 측 안내 페이지로 이동합니다.</p>

<div class="jo-bar" id="jo-f1"></div>
<div class="jo-bar" id="jo-f2"></div>
<p class="jo-count" id="jo-count"></p>
<div class="jo-grid" id="jo-grid"></div>
<button class="jo-more" id="jo-more" hidden>더 보기</button>
<div class="jo-foot">
  <span class="jo-built">자료 업데이트 {{BUILT}} &middot; 애월뮤직팩토리 정리</span>
  <span>제주문화예술진흥원 &middot; 제주아트센터 &middot; 서귀포시 &middot; 비짓제주 &middot; 플레이제주 &middot; 제주문화예술재단</span>
</div>
</div>
<script>
(function () {
  var SRC = "{{DATAURL}}";
  var DATA = {{PAYLOAD}};
  var TODAY = "{{TODAY}}", MONTHS = {{MONTHS}}, CATS = {{CATS}}, STEP = 24;
  var root = document.getElementById("jeju-on");
  if (!root || root.dataset.ready) return;
  root.dataset.ready = "1";

  // 데이터는 매일 자동 갱신된다. 못 받아오면 붙여넣을 때 심어둔 사본을 쓴다.
  if (SRC) {
    fetch(SRC, { cache: "no-cache" })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (j) {
        if (j && j.events && j.events.length) {
          DATA = j.events; TODAY = j.today || TODAY;
          MONTHS = j.months || MONTHS; CATS = j.cats || CATS;
          var f2 = root.querySelector(".jo-built");
          if (f2 && j.built) f2.textContent = "자료 업데이트 " + j.built.slice(0, 10).replace(/-/g, ".");
          shown = STEP; draw();
        }
      })
      .catch(function () {
        if (!DATA.length) {
          document.getElementById("jo-grid").innerHTML =
            '<div class="jo-empty" style="grid-column:1/-1">일정을 불러오지 못했습니다. 잠시 후 새로고침해 주세요.</div>';
          document.getElementById("jo-count").textContent = "";
        }
      });
  }

  var f = { cat: "", region: "", month: "", free: false, q: "" }, shown = STEP;

  if (!document.getElementById("jo-fonts")) {
    var l = document.createElement("link");
    l.id = "jo-fonts"; l.rel = "stylesheet";
    l.href = "https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=IBM+Plex+Sans+KR:wght@400;500;600&display=swap";
    document.head.appendChild(l);
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function label(m) { return (+m.slice(5, 7)) + "월"; }
  function when(d) {
    var a = d.s.slice(5).replace("-", "."), b = d.e.slice(5).replace("-", ".");
    return a === b ? a : a + "–" + b;
  }
  function match(d) {
    if (f.cat && d.c !== f.cat) return false;
    if (f.region && d.r !== f.region) return false;
    if (f.free && d.f !== "Y") return false;
    if (f.month && !(d.s.slice(0, 7) <= f.month && d.e.slice(0, 7) >= f.month)) return false;
    if (f.q) {
      var q = f.q.toLowerCase();
      if ((d.t + " " + d.v + " " + d.o).toLowerCase().indexOf(q) < 0) return false;
    }
    return true;
  }
  function chip(k, v, text) {
    var on = f[k] === v || (k === "free" && f.free === v);
    return '<button class="jo-chip" data-k="' + k + '" data-v="' + esc(v) + '" aria-pressed="' + on + '">' + text + "</button>";
  }

  function draw() {
    var hits = DATA.filter(match);

    document.getElementById("jo-f1").innerHTML =
      chip("cat", "", "전체") +
      CATS.map(function (c) { return chip("cat", c, c); }).join("") +
      '<span class="jo-sep"></span>' +
      MONTHS.map(function (m) { return chip("month", m, label(m)); }).join("");

    document.getElementById("jo-f2").innerHTML =
      chip("region", "", "제주 전역") + chip("region", "제주시", "제주시") + chip("region", "서귀포시", "서귀포시") +
      '<span class="jo-sep"></span>' + chip("free", true, "무료만") +
      '<input class="jo-search" id="jo-q" type="search" placeholder="행사명 · 장소 검색" value="' + esc(f.q) + '">';

    document.getElementById("jo-count").innerHTML =
      "<b>" + hits.length + "</b>건" + (f.q ? " &middot; &ldquo;" + esc(f.q) + "&rdquo;" : "");

    var slice = hits.slice(0, shown);
    if (!DATA.length && SRC) {
      document.getElementById("jo-grid").innerHTML =
        '<div class="jo-empty" style="grid-column:1/-1">일정을 불러오는 중…</div>';
      document.getElementById("jo-count").textContent = "";
      document.getElementById("jo-more").hidden = true;
      return;
    }
    document.getElementById("jo-grid").innerHTML = slice.length ? slice.map(function (d) {
      var img = d.i
        ? '<img src="' + esc(d.i) + '" alt="' + esc(d.t) + ' 포스터" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.display=\'none\'">'
        : '<span class="jo-noimg">' + esc(d.t.slice(0, 26)) + "</span>";
      var meta = [d.v, d.h].filter(Boolean).join(" &middot; ");
      return '<a class="jo-card" href="' + esc(d.u) + '" target="_blank" rel="noopener">' +
        '<span class="jo-shot"><span class="jo-when">' + when(d) + "</span>" +
        (d.f === "Y" ? '<span class="jo-free">무료</span>' : "") + img + "</span>" +
        '<span class="jo-body"><span class="jo-cat">' + esc(d.c) + "</span>" +
        '<span class="jo-name">' + esc(d.t) + "</span>" +
        '<span class="jo-meta">' + meta + "</span></span></a>";
    }).join("") : '<div class="jo-empty" style="grid-column:1/-1">조건에 맞는 행사가 없습니다. 필터를 풀어 보세요.</div>';

    var more = document.getElementById("jo-more");
    more.hidden = hits.length <= shown;
    more.textContent = "더 보기 (" + Math.max(0, hits.length - shown) + "건 남음)";

    Array.prototype.forEach.call(root.querySelectorAll(".jo-chip"), function (b) {
      b.onclick = function () {
        var k = b.dataset.k;
        if (k === "free") f.free = !f.free;
        else f[k] = (f[k] === b.dataset.v) ? "" : b.dataset.v;
        shown = STEP; draw();
      };
    });
    var q = document.getElementById("jo-q");
    if (q) {
      q.oninput = function () {
        var pos = this.selectionStart; f.q = this.value; shown = STEP; draw();
        var n = document.getElementById("jo-q"); if (n) { n.focus(); n.setSelectionRange(pos, pos); }
      };
    }
  }

  document.getElementById("jo-more").onclick = function () { shown += STEP; draw(); };
  draw();
})();
</script>
'''

subs = {
    'PAYLOAD': payload,
    'TODAY': today,
    'BUILT': now_kst.strftime('%Y.%m.%d'),
    'N': str(len(data)),
    'MONTHS': json.dumps(months),
    'CATS': json.dumps([c for c in CAT_ORDER if any(d['c'] == c for d in data)], ensure_ascii=False),
    'DATAURL': DATA_URL,
}
out = TPL
for k, v in subs.items():
    out = out.replace('{{' + k + '}}', v)

dst = os.path.join(OUT, 'amf_jeju_events_embed.html')
open(dst, 'w', encoding='utf-8').write(out)
print(f'{len(data)}건 → {dst}  ({len(out)/1024:.0f}KB)')
print('포스터 있는 건:', sum(1 for d in data if d['i']))
