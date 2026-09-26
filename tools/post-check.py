#!/usr/bin/env python3
"""블로그 글 검사. 표준 라이브러리만 사용한다.

사용법:
  python3 tools/post-check.py _posts/2026-09-26-slug.md [...]
  python3 tools/post-check.py --changed              # 마지막 커밋 + 작업 트리에서 바뀐 _posts/*.md (엄격 모드)
  python3 tools/post-check.py --changed --base REF   # REF...HEAD 범위에서 바뀐 글 (CI 용)
  python3 tools/post-check.py --strict FILE          # 대표 이미지 없음도 FAIL
  python3 tools/post-check.py --root DIR FILE        # assets/ 를 DIR 기준으로 찾음 (테스트용)
종료 코드: FAIL 이 하나라도 있으면 1.

판정 규칙:
  - 금지 어미 검사에서 제외: 코드 블록, <figure> 블록, `*` 로 시작하는 대화 줄(`*A: "..."*`,
    인용문 안의 `> *...*` 포함), 줄 끝에 `<!-- post-check: ignore -->` 가 있는 줄.
    `**굵게**` 로 시작하는 줄과 `* 불릿` 은 제외되지 않는다.
  - 대표 이미지(image.path) 가 없으면 단독 검사에서는 WARN, --strict/--changed 에서는 FAIL.
  - 본문이 참조하는 이미지가 없으면 항상 FAIL.
"""
import argparse
import os
import re
import subprocess
import sys

BANNED_ENDINGS = ("습니다", "합니다", "입니다", "하세요", "보세요", "됩니다")
REQUIRED_FIELDS = ("title", "author", "date", "categories", "tags")
IMG_RE = re.compile(r"/assets/img/posts/[A-Za-z0-9._/-]+")
FENCE_RE = re.compile(r"^\s*```")
PROMPT_RE = re.compile(r"^\{:\s*\.prompt-")
DIALOG_RE = re.compile(r"^\*(?!\*)(?!\s)")   # 단일 * 로 시작하고 바로 글자가 오는 줄 (굵게·불릿 제외)
IGNORE_MARK = "<!-- post-check: ignore -->"


def split_front_matter(text):
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, lines
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], lines[i + 1:]
    return None, lines


def parse_front_matter(fm_lines):
    """최상위 key: value 와 image.path 만 뽑는다."""
    data = {}
    current = None
    for line in fm_lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and ":" in line:
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip()
            current = key.strip()
        elif current == "image" and ":" in line:
            key, _, value = line.strip().partition(":")
            data["image." + key.strip()] = value.strip()
    return data


def body_prose_lines(body, offset):
    """코드 블록, figure, 대화 줄, ignore 표시 줄을 뺀 산문 줄을 (파일 행 번호, 내용) 으로 돌려준다.

    두 번째 반환값은 닫히지 않은 블록 정보 (("코드 블록"|"figure", 시작 행) 또는 None).
    """
    out = []
    in_code = False
    in_figure = False
    open_at = None
    for k, line in enumerate(body):
        file_line = offset + k
        if FENCE_RE.match(line):
            in_code = not in_code
            open_at = file_line if in_code else None
            continue
        if in_code:
            continue
        s = line.strip()
        if s.startswith("<figure"):
            in_figure = True
            open_at = file_line
        if in_figure:
            if "</figure>" in s:
                in_figure = False
                open_at = None
            continue
        if IGNORE_MARK in line:
            continue
        content = s.lstrip(">").strip() if s.startswith(">") else s
        if DIALOG_RE.match(content):
            continue
        out.append((file_line, line))
    unclosed = None
    if in_code:
        unclosed = ("코드 블록", open_at)
    elif in_figure:
        unclosed = ("figure", open_at)
    return out, unclosed


def check_file(path, root, strict):
    results = []  # (항목, 판정, 상세)
    text = open(path, encoding="utf-8").read()
    fm_lines, body = split_front_matter(text)
    if fm_lines is None:
        results.append(("프론트매터", "FAIL", "--- 로 감싼 프론트매터가 없음"))
        return results
    fm = parse_front_matter(fm_lines)
    offset = len(fm_lines) + 3          # body[0] 의 파일 행 번호 (1-based)
    prose, unclosed = body_prose_lines(body, offset)

    missing = [f for f in REQUIRED_FIELDS if f not in fm or not fm[f]]
    if "image.path" not in fm:
        missing.append("image.path")
    results.append(("프론트매터 필수 필드", "FAIL" if missing else "OK",
                    "누락: " + ", ".join(missing) if missing else "title, author, date, categories, tags, image.path"))

    hero = fm.get("image.path")
    body_refs = set()
    for _, line in prose:
        body_refs.update(IMG_RE.findall(line))
    for line in body:  # figure 안의 img 도 포함
        if "<img" in line or "src=" in line:
            body_refs.update(IMG_RE.findall(line))
    missing_body = [r for r in sorted(body_refs) if not os.path.isfile(os.path.join(root, r.lstrip("/")))]
    hero_missing = bool(hero) and not os.path.isfile(os.path.join(root, hero.lstrip("/")))
    if missing_body:
        results.append(("이미지 참조 존재", "FAIL", "본문 이미지 없음: " + ", ".join(missing_body)))
    elif hero_missing:
        results.append(("이미지 참조 존재", "FAIL" if strict else "WARN",
                        f"대표 이미지 없음: {hero}" + ("" if strict else " (발행 전에 채울 것)")))
    else:
        results.append(("이미지 참조 존재", "OK", f"{len(body_refs) + (1 if hero else 0)}개 확인"))

    banned = []
    for n, line in prose:
        for ending in BANNED_ENDINGS:
            if ending in line:
                banned.append(f"{n}행: …{ending}")
                break
    results.append(("금지 어미 (반말 회고체)", "FAIL" if banned else "OK",
                    "; ".join(banned[:5]) + (" 외" if len(banned) > 5 else "") if banned else "0건"))

    if unclosed:
        kind, at = unclosed
        results.append(("블록 닫힘", "FAIL", f"{at}행에서 연 {kind}이 닫히지 않음. 그 뒤는 검사하지 못함"))

    mermaid_blocks = sum(1 for line in body if line.strip().startswith("```mermaid"))
    mermaid_flag = fm.get("mermaid", "").lower() == "true"
    if mermaid_blocks and not mermaid_flag:
        results.append(("mermaid 설정", "FAIL", f"mermaid 블록 {mermaid_blocks}개인데 mermaid: true 없음"))
    elif not mermaid_blocks and mermaid_flag:
        results.append(("mermaid 설정", "FAIL", "mermaid: true 인데 mermaid 블록 없음"))
    else:
        results.append(("mermaid 설정", "OK", f"블록 {mermaid_blocks}개, mermaid: {'true' if mermaid_flag else '없음'}"))

    bad_prompts = []
    for k, line in enumerate(body):
        if PROMPT_RE.match(line.strip()):
            prev = body[k - 1] if k > 0 else ""
            if not prev.lstrip().startswith(">"):
                bad_prompts.append(f"{offset + k}행")
    results.append(("prompt 상자 위치", "FAIL" if bad_prompts else "OK",
                    "인용문 바로 다음 줄이 아님: " + ", ".join(bad_prompts) if bad_prompts else "모두 인용문 바로 다음"))

    todos = [str(offset + k) for k, line in enumerate(body) if "<!-- TODO" in line]
    results.append(("TODO 잔여", "FAIL" if todos else "OK",
                    f"{len(todos)}건 ({', '.join(todos[:5])}행)" if todos else "0건"))

    placeholders = [str(k + 2) for k, line in enumerate(fm_lines) if "{{" in line]
    placeholders += [str(offset + k) for k, line in enumerate(body) if "{{" in line]
    results.append(("템플릿 자리표시자 잔여", "FAIL" if placeholders else "OK",
                    f"{len(placeholders)}건 ({', '.join(placeholders[:5])}행)" if placeholders else "0건"))

    # 경고: 내부 링크 대상 존재
    warn = []
    posts_dir = os.path.join(root, "_posts")
    for n, line in prose:
        for slug in re.findall(r"\]\(/posts/([a-z0-9-]+)\)", line):
            if os.path.isdir(posts_dir) and not any(f.endswith(f"-{slug}.md") for f in os.listdir(posts_dir)):
                warn.append(f"{n}행: /posts/{slug} 없음")
    if warn:
        results.append(("내부 링크", "WARN", "; ".join(warn[:5])))
    if len(text) > 40000:
        results.append(("분량", "WARN", f"{len(text)}자. 4만 자를 넘는다"))
    return results


def git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, check=False)


def changed_posts(root, base):
    """base...HEAD (없으면 HEAD~1..HEAD) 에서 바뀐 글 + 작업 트리에서 바뀐 글."""
    files = set()
    diff = None
    if base and not set(base) <= {"0"}:
        r = git(root, "diff", "--name-only", f"{base}...HEAD", "--", "_posts")
        if r.returncode == 0:
            diff = r.stdout
        else:
            print(f"경고: base {base} 를 찾지 못해 HEAD~1 과 비교한다", file=sys.stderr)
    if diff is None:
        diff = git(root, "diff", "--name-only", "HEAD~1", "HEAD", "--", "_posts").stdout
    files.update(l.strip() for l in diff.splitlines() if l.strip().endswith(".md"))
    status = git(root, "status", "--porcelain", "--no-renames", "-z", "--", "_posts").stdout
    for entry in status.split("\0"):
        if len(entry) > 3 and entry[3:].endswith(".md"):
            files.add(entry[3:])
    result = []
    for f in sorted(files):
        full = os.path.join(root, f)
        if os.path.isfile(full):
            result.append(full)
        else:
            print(f"건너뜀 (파일 없음, 삭제된 글?): {f}", file=sys.stderr)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--root", default=".")
    ap.add_argument("--changed", action="store_true", help="바뀐 글만 검사 (엄격 모드)")
    ap.add_argument("--base", default=None, help="--changed 와 함께: 이 커밋부터 HEAD 까지의 변경")
    ap.add_argument("--strict", action="store_true", help="대표 이미지 없음도 FAIL")
    args = ap.parse_args()
    strict = args.strict or args.changed
    files = args.files or changed_posts(args.root, args.base)
    if not files:
        print("검사할 글 없음")
        return 0
    exit_code = 0
    for path in files:
        print(f"\n== {path}")
        print(f"{'항목':<22}| {'판정':<5}| 상세")
        print("-" * 70)
        for item, verdict, detail in check_file(path, args.root, strict):
            print(f"{item:<22}| {verdict:<5}| {detail}")
            if verdict == "FAIL":
                exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
