#!/bin/bash
# 매일 자동 수집 → 깃허브 푸시. launchd 가 부른다.
cd "$(dirname "$0")" || exit 1
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/opt/homebrew/bin"
LOG="out/daily.log"
mkdir -p out
{
  echo "════════ $(date '+%Y-%m-%d %H:%M:%S') 시작"

  # 깃허브 보조 실행(13:00)이 먼저 커밋해 두면 푸시가 막힌다.
  # events.json 은 매번 새로 만드는 파생물이라 원격 것을 그대로 받아도 손해가 없다.
  git fetch -q origin || true
  if ! git merge --ff-only -q origin/main 2>/dev/null; then
    echo "원격과 갈라져 있어 원격 기준으로 맞춥니다."
    git reset -q --hard origin/main
  fi

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
