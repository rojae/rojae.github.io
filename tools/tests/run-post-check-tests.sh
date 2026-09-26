#!/usr/bin/env bash
# tools/post-check.py 의 동작을 fixture 로 검증한다.
set -u
cd "$(dirname "$0")/../.."
REPO=$(pwd)
ROOT=tools/tests/post-check
pass=0; fail=0
check() {  # $1 = 설명, $2 = 기대 종료코드, 나머지 = 인자
  local desc=$1 want=$2; shift 2
  python3 tools/post-check.py --root "$ROOT" "$@" >/tmp/pc.out 2>&1; local got=$?
  if [ "$got" = "$want" ]; then echo "PASS  $desc"; pass=$((pass+1))
  else echo "FAIL  $desc (exit $got, want $want)"; cat /tmp/pc.out; fail=$((fail+1)); fi
}
report() {  # $1 = 설명, $2 = grep 패턴
  if python3 tools/post-check.py --root "$ROOT" $ROOT/bad.md 2>/dev/null | grep -q "$2"; then
    echo "PASS  $1"; pass=$((pass+1))
  else
    echo "FAIL  $1"; fail=$((fail+1))
  fi
}
check "good-lab 통과"                       0 $ROOT/good-lab.md
check "good-essay 통과 (본문 이미지 없음)"  0 $ROOT/good-essay.md
check "bad 실패"                            1 $ROOT/bad.md
check "둘 다 주면 실패"                     1 $ROOT/good-lab.md $ROOT/bad.md
report "bad 에서 금지 어미 보고"       "금지 어미"
report "bad 에서 prompt 위치 보고"     "prompt"
report "bad 에서 TODO 보고"            "TODO"
report "bad 에서 mermaid 불일치 보고"  "mermaid"
report "bad 에서 자리표시자 보고"      "자리표시자"
# 변경된 글이 없을 때
rm -rf /tmp/pc-empty && mkdir -p /tmp/pc-empty && git -C /tmp/pc-empty init -q && git -C /tmp/pc-empty -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
out=$(python3 "$REPO/tools/post-check.py" --root /tmp/pc-empty --changed 2>&1); got=$?
if [ "$got" = "0" ] && echo "$out" | grep -q "검사할 글 없음"; then echo "PASS  변경 없음이면 0"; pass=$((pass+1)); else echo "FAIL  변경 없음이면 0 (exit $got)"; echo "$out"; fail=$((fail+1)); fi
echo "passed=$pass failed=$fail"
[ "$fail" = "0" ]
