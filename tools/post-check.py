#!/usr/bin/env python3
"""블로그 글 검사. 표준 라이브러리만 사용한다.

사용법:
  python3 tools/post-check.py _posts/2026-09-26-slug.md [...]
  python3 tools/post-check.py --changed        # 마지막 커밋에서 바뀐 _posts/*.md
  python3 tools/post-check.py --root DIR FILE  # assets/ 를 DIR 기준으로 찾음 (테스트용)
종료 코드: FAIL 이 하나라도 있으면 1.
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


def body_prose_lines(body):
    """코드 블록, figure, 대화(*로 시작) 를 뺀 산문 줄만 (번호, 내용) 으로 돌려준다."""
    out = []
    in_code = False
    in_figure = False
    for n, line in enumerate(body, start=1):
        if FENCE_RE.match(line):
            in_code = not in_code
            continue
        if in_code:
            continue
        s = line.strip()
        if s.startswith("<figure"):
            in_figure = True
        if in_figure:
            if "</figure>" in s:
                in_figure = False
            continue
        if s.startswith("*"):
            continue
        out.append((n, line))
    return out


def check_file(path, root):
    results = []  # (항목, 판정, 상세)
    text = open(path, encoding="utf-8").read()
    fm_lines, body = split_front_matter(text)
    if fm_lines is None:
        results.append(("프론트매터", "FAIL", "--- 로 감싼 프론트매터가 없음"))
        return results
    fm = parse_front_matter(fm_lines)

    missing = [f for f in REQUIRED_FIELDS if f not in fm or not fm[f]]
    if "image.path" not in fm:
        missing.append("image.path")
    results.append(("프론트매터 필수 필드", "FAIL" if missing else "OK",
                    "누락: " + ", ".join(missing) if missing else "title, author, date, categories, tags, image.path"))

    refs = set()
    if "image.path" in fm:
        refs.add(fm["image.path"])
    for _, line in body_prose_lines(body):
        refs.update(IMG_RE.findall(line))
    for line in body:  # figure 안의 img 도 포함
        if "<img" in line or "src=" in line:
            refs.update(IMG_RE.findall(line))
    missing_imgs = [r for r in sorted(refs) if not os.path.isfile(os.path.join(root, r.lstrip("/")))]
    results.append(("이미지 참조 존재", "FAIL" if missing_imgs else "OK",
                    "없음: " + ", ".join(missing_imgs) if missing_imgs else f"{len(refs)}개 확인"))

    banned = []
    for n, line in body_prose_lines(body):
        for ending in BANNED_ENDINGS:
            if ending in line:
                banned.append(f"{n}행: …{ending}")
                break
    results.append(("금지 어미 (반말 회고체)", "FAIL" if banned else "OK",
                    "; ".join(banned[:5]) + (" 외" if len(banned) > 5 else "") if banned else "0건"))

    mermaid_blocks = sum(1 for line in body if line.strip().startswith("```mermaid"))
    mermaid_flag = fm.get("mermaid", "").lower() == "true"
    if mermaid_blocks and not mermaid_flag:
        results.append(("mermaid 설정", "FAIL", f"mermaid 블록 {mermaid_blocks}개인데 mermaid: true 없음"))
    elif not mermaid_blocks and mermaid_flag:
        results.append(("mermaid 설정", "FAIL", "mermaid: true 인데 mermaid 블록 없음"))
    else:
        results.append(("mermaid 설정", "OK", f"블록 {mermaid_blocks}개, mermaid: {'true' if mermaid_flag else '없음'}"))

    bad_prompts = []
    for i, line in enumerate(body):
        if PROMPT_RE.match(line.strip()):
            prev = body[i - 1] if i > 0 else ""
            if not prev.lstrip().startswith(">"):
                bad_prompts.append(f"{i + 1}행")
    results.append(("prompt 상자 위치", "FAIL" if bad_prompts else "OK",
                    "인용문 바로 다음 줄이 아님: " + ", ".join(bad_prompts) if bad_prompts else "모두 인용문 바로 다음"))

    todos = [str(n) for n, line in enumerate(body, start=1) if "<!-- TODO" in line]
    results.append(("TODO 잔여", "FAIL" if todos else "OK",
                    f"{len(todos)}건 ({', '.join(todos[:5])}행)" if todos else "0건"))

    placeholders = [str(n) for n, line in enumerate(fm_lines + body, start=1) if "{{" in line]
    results.append(("템플릿 자리표시자 잔여", "FAIL" if placeholders else "OK",
                    f"{len(placeholders)}건 ({', '.join(placeholders[:5])}행)" if placeholders else "0건"))

    # 경고: 내부 링크 대상 존재
    warn = []
    for n, line in body_prose_lines(body):
        for slug in re.findall(r"\]\(/posts/([a-z0-9-]+)\)", line):
            posts_dir = os.path.join(root, "_posts")
            if os.path.isdir(posts_dir) and not any(f.endswith(f"-{slug}.md") for f in os.listdir(posts_dir)):
                warn.append(f"{n}행: /posts/{slug} 없음")
    if warn:
        results.append(("내부 링크", "WARN", "; ".join(warn[:5])))
    if len(text) > 40000:
        results.append(("분량", "WARN", f"{len(text)}자. 4만 자를 넘는다"))
    return results


def changed_posts(root):
    try:
        out = subprocess.run(["git", "-C", root, "diff", "--name-only", "HEAD~1", "HEAD", "--", "_posts"],
                             capture_output=True, text=True, check=False).stdout
        status = subprocess.run(["git", "-C", root, "status", "--porcelain", "--", "_posts"],
                                capture_output=True, text=True, check=False).stdout
    except FileNotFoundError:
        return []
    files = set(l.strip() for l in out.splitlines() if l.strip().endswith(".md"))
    for l in status.splitlines():
        p = l[3:].strip()
        if p.endswith(".md"):
            files.add(p)
    return sorted(os.path.join(root, f) for f in files if os.path.isfile(os.path.join(root, f)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--root", default=".")
    ap.add_argument("--changed", action="store_true")
    args = ap.parse_args()
    files = args.files or changed_posts(args.root)
    if not files:
        print("검사할 글 없음")
        return 0
    exit_code = 0
    for path in files:
        print(f"\n== {path}")
        print(f"{'항목':<22}| {'판정':<5}| 상세")
        print("-" * 70)
        for item, verdict, detail in check_file(path, args.root):
            print(f"{item:<22}| {verdict:<5}| {detail}")
            if verdict == "FAIL":
                exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
