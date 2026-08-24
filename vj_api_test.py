#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""비짓제주 오픈API 키가 도착하면 이걸 먼저 돌려서 축제·행사가 나오는지 확인한다.
    python3 vj_api_test.py 발급받은키
"""
import sys, json, subprocess
from collections import Counter

KEY = sys.argv[1] if len(sys.argv) > 1 else ''
if not KEY:
    print('사용법: python3 vj_api_test.py <API_KEY>'); sys.exit(1)

BASE = 'https://api.visitjeju.net/vsjApi/contents/searchList'
def call(url):
    out = subprocess.run(['curl','-s','-m','30',url], capture_output=True).stdout
    try: return json.loads(out)
    except Exception: return {'result':'parse-error','raw':out[:300].decode('utf-8','replace')}

print('① 키 유효성 + 전체 규모')
d = call(f'{BASE}?apiKey={KEY}&locale=kr&page=1')
print('  result =', d.get('result'), d.get('resultMessage'))
if d.get('result') != '200':
    print('  → 키가 아직 활성화되지 않았거나 잘못됐습니다.'); sys.exit(1)
print('  totalCount =', d.get('totalCount'), '/ pageSize =', d.get('pageSize'), '/ pageCount =', d.get('pageCount'))

items = d.get('items') or []
print('\n② 콘텐츠 종류 분포 (1페이지 기준)')
for k, v in Counter((i.get('contentscd') or {}).get('label','?') for i in items).most_common():
    print(f'   {v:4d}  {k}')

print('\n③ 축제·행사(CNTS_) 콘텐츠가 API로 조회되는가')
d2 = call(f'{BASE}?apiKey={KEY}&locale=kr&cid=CNTS_300000000014627')   # 손열음 피아노 리사이틀
print('  result =', d2.get('result'), '/ resultCount =', d2.get('resultCount'))
if d2.get('items'):
    it = d2['items'][0]
    print('  title =', it.get('title'))
    print('  필드 목록 =', sorted(it.keys()))
    has_date = [k for k in it if any(w in k.lower() for w in ('date','ymd','start','end','period'))]
    print('  날짜로 보이는 필드 =', has_date or '없음 ← 있으면 목록 수집 자동화 가능')
else:
    print('  → 축제·행사는 이 API로 안 나옵니다. 기존 브라우저 방식 유지 필요.')

print('\n④ 샘플 1건 원본')
sample = (d2.get('items') or items or [None])[0]
print(json.dumps(sample, ensure_ascii=False, indent=1)[:1500] if sample else '  없음')
