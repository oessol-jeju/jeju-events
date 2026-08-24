#!/bin/bash
# 매일 자동 수집 → 깃허브 푸시. launchd 가 부른다.
cd "$(dirname "$0")" || exit 1
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/opt/homebrew/bin"
LOG="out/daily.log"
mkdir -p out
{
  echo "════════ $(date '+%Y-%m-%d %H:%M:%S') 시작"
  python3 refresh.py    || { echo "수집 실패"; exit 1; }
  python3 build_page.py || { echo "생성 실패"; exit 1; }
  git add docs/events.json visitjeju_cache.json
  if git diff --staged --quiet; then
    echo "바뀐 게 없습니다."
  else
    git -c user.name="jeju-events bot" -c user.email="oessol@gmail.com" \
        commit -q -m "행사 데이터 갱신 $(date '+%Y-%m-%d')"
    git push -q origin main && echo "푸시 완료"
  fi
  echo "════════ $(date '+%H:%M:%S') 끝"
} >> "$LOG" 2>&1
# 로그가 무한정 커지지 않게 최근 2000줄만 남긴다
tail -n 2000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
