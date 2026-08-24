# 제주 공연·행사 통합 수집

## 폴더

```
jeju-events/
├── refresh.py            수집기 (이것만 돌리면 됨)
├── manual.csv            손으로 넣는 행사 — 포스터 접수·인스타·재단 PDF 결과가 모이는 곳
├── visitjeju_apikey.txt  비짓제주 오픈API 키 (환경변수 VISITJEJU_API_KEY 로도 됨)
├── visitjeju_cache.json  비짓제주 상세 캐시 — 지우면 다시 다 받는다(3분)
├── vj_api_test.py        비짓제주 API 점검용
├── build_page.py         CSV → 홈페이지에 붙일 HTML 생성
├── ig_extract.js         인스타 게시물에서 본문·날짜 뽑는 브라우저 코드
└── out/                  결과 CSV
```

## 자동으로 도는 것 (손 안 대도 됨)

| 언제 | 어디서 | 무엇을 |
|---|---|---|
| 매일 07:30 | **맥** (launchd) | 8개 소스 전부 수집 → 깃허브 푸시 |
| 매일 13:00 | 깃허브 Actions | 접속 가능한 소스만 갱신 (보조) |

맥이 주 수집기다. **깃허브 러너에서는 아래 4곳에 접속이 안 된다** (2026-08 확인, 4개 소스 전부 0건):

- `jeju.go.kr` (문예회관) · `jejusi.go.kr` (제주아트센터) · `seogwipo.go.kr` · `playjeju.co.kr`

접속되는 곳은 `visitjeju.net`, `jejunolda.com`, `jfac.kr` 뿐이다.
그래서 깃허브 쪽은 못 가져온 소스의 **직전 데이터를 그대로 이어받아** 반쪽 데이터가 배포되는 걸 막는다.

맥 자동 실행 상태 확인:

```bash
tail -30 ~/jeju-events/out/daily.log
```

멈추려면:

```bash
launchctl unload ~/Library/LaunchAgents/kr.oesol.jeju-events.plist
```

## 손으로 돌릴 때

```bash
python3 ~/jeju-events/refresh.py
```

인자 없이 돌리면 **이번 달 + 앞으로 두 달**을 긁는다. 특정 기간은 이렇게:

```bash
python3 ~/jeju-events/refresh.py 2026-09 2026-10
```

끝나면 `out/jeju_events_YYYYMMDD.csv`가 생긴다.
구글 시트에서 **파일 → 가져오기 → 업로드 → 가져오기 위치: 현재 시트 바꾸기**로 붙이면 갱신 끝.

이어서 홈페이지용 HTML도 다시 만든다.

```bash
python3 ~/jeju-events/build_page.py
```

`out/amf_jeju_events_embed.html` 이 새로 생긴다. 파일을 통째로 복사해서
스퀘어스페이스 **제주 공연·행사 일정** 페이지의 코드 블록 내용을 바꿔치기하면 된다.
(지난 날짜 행사는 자동으로 빠진다.)

## 애월뮤직팩토리 홈페이지에 붙이기

한 번만 해두면 되는 세팅:

**① 페이지 만들기**
페이지 추가 → 빈 페이지 → 이름 `제주 공연·행사 일정` → 페이지 설정에서 URL 슬러그를 `/jeju-events` 로.
섹션 안에 **코드 블록**(Code)을 하나 넣고 `out/amf_jeju_events_embed.html` 내용을 통째로 붙여넣는다.
섹션 여백은 0, 폭은 **전체 너비(Full Bleed)** 로 두면 검은 배경이 화면 끝까지 찬다.

**② 홈 최상단 버튼**
HOME 편집 → 맨 위에 섹션 추가 → 코드 블록에 `out/amf_home_button.html` 붙여넣기.
페이지 슬러그를 `/jeju-events` 말고 다르게 지었다면 파일 안 `href="/jeju-events"` 를 바꾼다.

> 코드 블록에서 스크립트가 안 돌면 스퀘어스페이스가 **개발자 모드/코드 주입**을 막고 있는
> 요금제일 수 있다(비즈니스 플랜 이상 필요). 그때는 코드 블록 대신
> **설정 → 고급 → 코드 주입**에 넣거나, 페이지를 임베드로 대체해야 한다.

## 어디서 긁어오나

| 소스 | 방식 | 자동 |
|---|---|---|
| 제주문화예술진흥원 (문예회관) | 공연달력·전시달력 → 상세 | ✅ |
| 플레이제주 | 7개 게시판 × 예정/공연중 | ✅ |
| 제주아트센터 | 월별 일정 → 상세 | ✅ |
| 서귀포시 문화행사일정 | 월별 · 축제/공연/전시/교육 | ✅ |
| 제주문화예술재단 | 공고 API에서 일정 있는 건만 | ✅ |
| 제주인놀다 (재단) | 사이트 검색 엔드포인트, 날짜별 조회 | ✅ |
| 비짓제주 | 오픈API(축제/행사 803건) + 상세 페이로드 | ✅ |
| 직접등록 | `manual.csv` | ⚠️ |

### 비짓제주가 도는 방식

목록은 오픈API로 받는다.

```
GET https://api.visitjeju.net/vsjApi/contents/searchList
    ?apiKey=…&locale=kr&category=c5&page=N        # c5 = 축제/행사, 9페이지 803건
```

그런데 **API 응답에는 행사 기간이 없다.** 그래서 날짜·시간·요금·주최는 상세 페이지의
Nuxt 페이로드(`__NUXT_DATA__`) 안 `festivalcontents` 노드에서 꺼낸다.

```json
{"stday":"20260917","fnsday":"20260917","sttime":"19:30",
 "pricetype":{"label":"유료"},"price":50000,"host":null}
```

상세는 1건당 800KB라 `visitjeju_cache.json`에 저장하고, 그 다음부터는
**새로 생긴 것 + 시작일이 최근 30일~앞으로 120일 안인 것**만 다시 확인한다.
첫 실행은 3분쯤, 이후는 훨씬 빠르다.

API 키 점검:

```bash
python3 ~/jeju-events/vj_api_test.py $(cat ~/jeju-events/visitjeju_apikey.txt)
```

## 알아둘 것

- **문예회관 공연 일정은 두 달 앞까지만 올라온다.** 2026-08-24 기준 10월 공연 달력은 비어 있다
  (대관 확정이 안 됐을 뿐, 수집 실패가 아니다). 9월 중순에 한 번 더 돌리면 채워진다.
- 실행할 때마다 총 건수가 1~2건 흔들리면 사이트 응답이 불안정한 것이다. 다시 돌리면 된다.
  목록 페이지는 6번까지 재시도하고, 못 읽으면 ⚠ 로 알려준다.

### 제주인놀다가 도는 방식

제주인놀다가 내건 오픈API는 **등록(create/update/delete) 전용**이라 읽어올 수 없다.
대신 사이트가 실제로 쓰는 검색 엔드포인트를 그대로 호출한다.

```
GET https://www.jejunolda.com/event/progress.htm
    ?act=search&format=json&pageSize=100&page=1&indayString=2026-09-20
```

`indayString` 은 **그날 열리는 행사**를 준다. 9~10월 61일치를 훑어 seq 로 중복을 없앤다.
좌표(x=위도, y=경도)와 포스터도 들어 있어서 나중에 지도를 붙일 때 쓸 수 있다.

> 날짜(start/end)가 epoch 밀리초인데 **저장 방식이 섞여 있다.** 어떤 건 UTC 자정,
> 어떤 건 KST 자정(15:00Z)으로 들어가 있다. 둘 다 +9시간 뒤 날짜를 취하면 맞는다.
> 이걸 놓치면 행사 절반이 하루씩 밀려서 중복 제거가 안 된다.

## manual.csv

자동 수집이 못 잡는 소규모 행사는 전부 여기로. 컬럼은 이 순서 그대로:

```
구분,명칭,일시,시간,장소,요금,주최,문의,출처,링크
```

- `일시`는 `2026-10-04` 또는 `2026-10-04 ~ 2026-10-06` 형식
- `구분`에 전시/공연/축제·행사/아동·가족 중 하나를 쓰면 카테고리가 자동으로 잡힌다
- 자동 수집분과 이름·시작일이 겹치면 알아서 합쳐진다 (빈 칸을 서로 채움)

## 인스타그램 게시물 넣기

1. 브라우저에서 게시물 URL을 연다 (로그인 불필요, 공개 게시물만)
2. `ig_extract.js` 내용을 콘솔에 붙여 넣는다
3. 나오는 `caption`·`posted`를 보고 `manual.csv`에 한 줄 추가

계정을 통째로 정기 수집하려면 Instagram Graph API의 `business_discovery`가 필요하다
(인스타 비즈니스 계정 + 연결된 페이스북 페이지 + Meta 앱 심사). 스크래핑은 차단된다.

## 접수창구 (포스터 업로드)

주최자가 포스터를 올리는 페이지: 아티팩트로 배포됨.
접수된 건은 페이지 안 **관리 → 대기 목록 CSV 내려받기**로 받아서 `manual.csv`에 붙이면 된다.
포스터에서 행사명·일시·장소를 읽는 건 사람(또는 클로드)이 확인하고 채운다.


---

# 사이트로 키우기

## 구조

```
GitHub Actions (매일 05:00)
   └ refresh.py → build_page.py
        └ docs/events.json  ──(GitHub Pages, CORS 허용)──┐
                                                          │
스퀘어스페이스 AMF 홈페이지                                  │
   └ 코드 블록 (한 번만 붙임) ── fetch ────────────────────┘
```

스퀘어스페이스는 깃허브에서 자동 배포가 안 된다. 그래서 **껍데기만 스퀘어스페이스에 두고
데이터는 깃허브에서 매일 갱신**한다. 코드 블록은 처음 한 번만 붙이면 그 뒤로 손댈 일이 없다.

데이터를 못 받아오면 붙여넣을 때 심어둔 사본을 그대로 보여주므로, 깃허브가 죽어도 페이지는 뜬다.

## 한 번만 하는 세팅

**① 깃허브 저장소 만들기** (github.com에서 `jeju-events` 새 저장소, Private 가능)

```bash
cd ~/jeju-events
git remote add origin https://github.com/<계정명>/jeju-events.git
git push -u origin main
```

**② API 키를 Secrets에 넣기**
저장소 → Settings → Secrets and variables → Actions → New repository secret
- 이름: `VISITJEJU_API_KEY`
- 값: `visitjeju_apikey.txt` 안의 값

**③ GitHub Pages 켜기**
Settings → Pages → Source: `Deploy from a branch` → Branch `main` / 폴더 `/docs` → Save

**④ 데이터 주소 알려주기**
`site_config.json` 의 `data_url` 을 아래로 채우고 커밋:

```json
{ "data_url": "https://<계정명>.github.io/jeju-events/events.json" }
```

**⑤ 임베드 다시 만들어 붙이기**

```bash
python3 build_page.py
pbcopy < out/amf_jeju_events_embed.html
```

스퀘어스페이스 코드 블록에 붙여넣으면 끝. 이후로는 아무것도 안 해도 매일 갱신된다.

> 저장소가 Private 이면 GitHub Pages 는 유료 플랜에서만 된다. 무료로 쓰려면 Public 으로.
> 올라가는 건 행사 정보뿐이고 API 키는 `.gitignore` 로 제외돼 있다.

## 소모임 채우기 — spaces.csv

`spaces.csv` 에 제주 문화공간 40곳을 정리해 뒀다. 중요한 발견:

- **22곳은 이미 자동 수집된다** (미술관·도서관·문예회관 등 기관). 인스타를 붙일 필요가 없다.
- **인스타가 필요한 건 18곳**, 그중 9곳이 독립서점이다.

대상이 18곳뿐이라 Meta Graph API 앱 심사(2~3주, 반려 가능)를 기다릴 이유가 약하다.
`ig_extract.js` 브라우저 방식이면 로그인 없이 지금 당장 되고, 18곳은 한 번에 몇 분이면 훑는다.
대상이 100곳을 넘어가면 그때 Graph API 로 옮기면 된다.

순서:
1. `spaces.csv` 의 `인스타계정` 칸을 채운다 (인스타 앱에서 공간명 검색 → 핸들 복사)
2. 계정별 최근 게시물을 훑어 캡션에서 행사 정보를 뽑는다
3. `manual.csv` 에 추가 → `refresh.py` → `build_page.py`
