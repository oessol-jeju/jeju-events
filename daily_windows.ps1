# 매일 자동 수집 → 깃허브 푸시. Windows 작업 스케줄러가 부른다 (daily.sh 의 윈도우판).
# 등록: Register-ScheduledTask 는 README 「데스크톱 자동 실행」 참조.
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
New-Item -ItemType Directory -Force out | Out-Null
$LOG = Join-Path $PSScriptRoot 'out\daily.log'

function Log($m) { "$m" | Out-File -FilePath $LOG -Append -Encoding utf8 }

Log ("════════ " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + " 시작 (데스크톱)")

# 깃허브 보조 실행(13:00)이나 맥이 먼저 커밋해 두면 푸시가 막힌다.
# events.json 은 매번 새로 만드는 파생물이라 원격 것을 그대로 받아도 손해가 없다.
git fetch -q origin 2>&1 | Out-Null
git merge --ff-only -q origin/main 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Log "원격과 갈라져 있어 원격 기준으로 맞춥니다."
    git reset -q --hard origin/main 2>&1 | Out-Null
}

$r = python refresh.py 2>&1 | Out-String
Log $r
if ($LASTEXITCODE -ne 0) { Log "수집 실패"; exit 1 }

$b = python build_page.py 2>&1 | Out-String
Log $b
if ($LASTEXITCODE -ne 0) { Log "생성 실패"; exit 1 }

git add docs/events.json visitjeju_cache.json
git diff --staged --quiet
if ($LASTEXITCODE -eq 0) {
    Log "바뀐 게 없습니다."
} else {
    git -c user.name="jeju-events bot" -c user.email="oessol@gmail.com" `
        commit -q -m ("행사 데이터 갱신 " + (Get-Date -Format 'yyyy-MM-dd')) 2>&1 | Out-Null
    $p = git push -q origin main 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) { Log "푸시 완료" } else { Log ("푸시 실패: " + $p) }
}
Log ("════════ " + (Get-Date -Format 'HH:mm:ss') + " 끝")

# 로그가 무한정 커지지 않게 최근 2000줄만 남긴다
$lines = Get-Content $LOG -Encoding utf8
if ($lines.Count -gt 2000) { $lines[-2000..-1] | Set-Content $LOG -Encoding utf8 }
