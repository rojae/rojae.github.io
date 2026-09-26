#!/usr/bin/env bash
# tools/post-check.py 의 동작을 fixture 로 검증한다.
set -u
cd "$(dirname "$0")/../.."
REPO=$(pwd)
ROOT=tools/tests/post-check
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
pass=0; fail=0
check() {  # $1 = 설명, $2 = 기대 종료코드, 나머지 = 인자
  local desc=$1 want=$2; shift 2
  python3 tools/post-check.py --root "$ROOT" "$@" >"$TMP/out" 2>&1; local got=$?
  if [ "$got" = "$want" ]; then echo "PASS  $desc"; pass=$((pass+1))
  else echo "FAIL  $desc (exit $got, want $want)"; cat "$TMP/out"; fail=$((fail+1)); fi
}
report() {  # $1 = 설명, $2 = 파일, $3 = grep 패턴 (확장 정규식)
  if python3 tools/post-check.py --root "$ROOT" "$2" 2>/dev/null | grep -Eq "$3"; then
    echo "PASS  $1"; pass=$((pass+1))
  else
    echo "FAIL  $1"; python3 tools/post-check.py --root "$ROOT" "$2" 2>&1 | tail -n +3; fail=$((fail+1))
  fi
}
check "good-lab 통과 (코드·figcaption·대화·인용 대화·굵은 반말·ignore 예외)" 0 $ROOT/good-lab.md
check "good-essay 통과 (본문 이미지 없음)"  0 $ROOT/good-essay.md
check "bad 실패"                            1 $ROOT/bad.md
check "둘 다 주면 실패"                     1 $ROOT/good-lab.md $ROOT/bad.md
check "bold: 굵은 글씨·불릿 뒤 존댓말은 잡는다" 1 $ROOT/bold.md
check "unclosed: 닫히지 않은 figure 는 실패" 1 $ROOT/unclosed.md
check "nohero: 대표 이미지 없음은 단독 검사에서 통과(WARN)" 0 $ROOT/nohero.md
check "nohero: --strict 에서는 실패"        1 --strict $ROOT/nohero.md
report "bad 에서 금지 어미 보고 (본문 18행)"    $ROOT/bad.md "금지 어미.*18행"
report "bad 에서 prompt 위치 보고 (14행)"       $ROOT/bad.md "prompt.*14행"
report "bad 에서 TODO 보고 (20행)"              $ROOT/bad.md "TODO.*20행"
report "bad 에서 mermaid 불일치 보고"           $ROOT/bad.md "mermaid"
report "bad 에서 자리표시자 보고 (22행)"        $ROOT/bad.md "자리표시자.*22행"
report "nohero 에서 WARN 으로 보고"             $ROOT/nohero.md "이미지 참조 존재.*WARN"
report "unclosed 에서 닫히지 않음 보고"         $ROOT/unclosed.md "닫히지 않"
# --changed: 변경된 글이 없을 때
R=$TMP/empty; mkdir -p $R && git -C $R init -q && git -C $R -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
out=$(python3 "$REPO/tools/post-check.py" --root $R --changed 2>&1); got=$?
if [ "$got" = "0" ] && echo "$out" | grep -q "검사할 글 없음"; then echo "PASS  변경 없음이면 0"; pass=$((pass+1)); else echo "FAIL  변경 없음이면 0 (exit $got)"; echo "$out"; fail=$((fail+1)); fi
# --changed: 마지막 커밋에 나쁜 글이 있으면 1 (엄격 모드: 대표 이미지 없음도 FAIL)
R=$TMP/changed; mkdir -p $R/_posts && git -C $R init -q && git -C $R -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
cp $ROOT/bad.md $R/_posts/2026-01-01-bad.md && git -C $R add -A && git -C $R -c user.email=t@t -c user.name=t commit -q -m "bad post"
python3 "$REPO/tools/post-check.py" --root $R --changed >"$TMP/out" 2>&1; got=$?
if [ "$got" = "1" ] && grep -q "2026-01-01-bad.md" "$TMP/out"; then echo "PASS  --changed 가 마지막 커밋의 나쁜 글을 잡는다"; pass=$((pass+1)); else echo "FAIL  --changed 마지막 커밋 (exit $got)"; cat "$TMP/out"; fail=$((fail+1)); fi
# --changed --base: 두 커밋 전에 들어간 나쁜 글도 잡는다
first=$(git -C $R rev-parse HEAD~1)
echo "x" > $R/other.txt && git -C $R add -A && git -C $R -c user.email=t@t -c user.name=t commit -q -m "unrelated"
python3 "$REPO/tools/post-check.py" --root $R --changed --base "$first" >"$TMP/out" 2>&1; got=$?
if [ "$got" = "1" ] && grep -q "2026-01-01-bad.md" "$TMP/out"; then echo "PASS  --changed --base 가 여러 커밋 범위의 나쁜 글을 잡는다"; pass=$((pass+1)); else echo "FAIL  --changed --base (exit $got)"; cat "$TMP/out"; fail=$((fail+1)); fi
# --changed: 공백이 든 경로도 빠뜨리지 않는다 (untracked)
cp $ROOT/bad.md "$R/_posts/2026-01-02-with space.md"
python3 "$REPO/tools/post-check.py" --root $R --changed >"$TMP/out" 2>&1; got=$?
if grep -q "with space.md" "$TMP/out"; then echo "PASS  --changed 가 공백 경로를 잡는다"; pass=$((pass+1)); else echo "FAIL  --changed 공백 경로"; cat "$TMP/out"; fail=$((fail+1)); fi
echo "passed=$pass failed=$fail"
[ "$fail" = "0" ]
