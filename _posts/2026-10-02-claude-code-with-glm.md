---
title: Claude Code에서 GLM 쓰기 - (판단은 Claude, 분량은 GLM에 나눠 맡기기)
author: rojae
date: 2026-10-02 00:00:00 +0900
published: true
categories: [infra]
tags: [claude-code, glm, zai, agents-md, codex, llm]
image:
  path: /assets/img/posts/2026-10-02-claude-code-with-glm/cover.svg
---
> Claude Code는 그대로 두고, `claude-glm` 명령 하나를 더 만들어 GLM에 번역·문서화 같은 분량 작업을 맡기는 방법입니다. 명령은 전부 복사해서 그대로 붙이면 됩니다. 규칙은 `AGENTS.md` 한 파일에 적어 Claude Code와 Codex가 같이 읽게 합니다.
> + 터미널용 zcode 설치는 [zcode cli 사용기](/posts/zcode-cli-review)에 따로 적었습니다.
{: .prompt-info }
<!-- post-check: tone=polite -->

---

## 왜 나눠 쓰나요

영문 문서 40개를 한글로 맞추는 일이 있다고 해 보겠습니다. 어려운 일은 아닙니다. 그냥 많습니다. 이걸 Claude에 맡기면 설계나 디버깅에 써야 할 사용량이 번역에 들어갑니다.

그래서 일을 둘로 나눕니다. **판단이 필요한 일은 Claude**, **분량이 많은 일은 GLM**에 맡깁니다.

| 장점 | 무엇이 좋아지나 |
|------|-----------------|
| 비용 절감 | Claude 사용량을 설계·디버깅에 아낍니다. GLM은 코딩 플랜 정액으로 돌립니다 |
| 속도 | 파일 단위로 쪼개 여러 개를 동시에 돌립니다. 하나씩 기다리지 않습니다 |
| 번역·문서화 병렬화 | 한↔영 문서 맞추기, Javadoc 달기, README 정리처럼 판단이 적은 일을 한꺼번에 넘깁니다 |
| 기존 환경 유지 | `claude`는 그대로 Anthropic을 씁니다. 스킬·설정·단축키도 그대로입니다 |

> **쉽게 말하면** Claude는 **설계 담당 선임**이고, GLM은 **분량을 나눠 받는 동료 여럿**입니다. 선임이 번역까지 혼자 하면 설계가 밀립니다.
{: .prompt-tip }

---

## 어떻게 붙나요

Z.AI는 Anthropic과 같은 형식의 API 주소(`https://api.z.ai/api/anthropic`)를 제공합니다. Claude Code는 환경변수로 API 주소와 모델 이름을 바꿀 수 있습니다. 그래서 **프로그램은 Claude Code 그대로, 뒤에서 답하는 모델만 GLM**이 됩니다.

공식 문서는 `~/.claude/settings.json`에 넣으라고 안내합니다. 그러면 `claude`가 전부 GLM으로 바뀝니다. 저는 둘 다 쓰고 싶어서 **명령을 하나 더 만듭니다.**

| 명령 | 뒤에서 답하는 모델 |
|------|-------------------|
| `claude` | Anthropic (그대로) |
| `claude-glm` | GLM (`glm-5.3`, 가벼운 일은 `glm-5.3-flash`) |

---

## 환경

| 항목 | 값 |
|------|-----|
| OS | macOS (키체인 사용) |
| Claude Code | 2.1.285 |
| Z.AI | GLM 코딩 플랜, API 키 1개 |
| 확인한 모델 | `glm-4.5-flash` (무료). `glm-5.3` 은 같은 스크립트, 이름만 다름 |
| 전제 | `~/.local/bin` 이 `PATH`에 있음 |

---

## 순서대로

### 1. API 키를 키체인에 넣기

[Z.AI 콘솔](https://z.ai/manage-apikey/apikey-list)에서 API 키를 발급받습니다. 키는 파일이나 대화창에 붙이지 말고 macOS 키체인에 넣습니다. `-w`를 맨 끝에 두면 키를 입력하라는 프롬프트가 뜨고, 셸 히스토리에도 남지 않습니다.

```bash
security add-generic-password -a zai -s zai-api-key -U -w
```

확인:

```bash
security find-generic-password -a zai -s zai-api-key -w >/dev/null && echo saved
# saved
```

> **쉽게 말하면** 키체인은 **맥에 붙은 금고**입니다. 스크립트는 금고에서 키를 꺼내 쓰고, 파일에는 아무것도 남기지 않습니다.
{: .prompt-tip }

### 2. `claude-glm` 명령 만들기

아래 블록을 통째로 붙이면 `~/.local/bin/claude-glm`이 생깁니다.

```bash
mkdir -p ~/.local/bin
cat > ~/.local/bin/claude-glm <<'EOF'
#!/usr/bin/env sh
# Claude Code를 z.ai GLM 백엔드로 실행한다.
# 전역 ~/.claude/settings.json 은 건드리지 않는다. 이 프로세스 환경변수로만 바꾼다.
#
#   claude-glm                          대화형, glm-5.3
#   claude-glm -p "작업"                헤드리스
#   GLM_MAIN=glm-5.3-flash claude-glm   저위험 대량 작업은 Flash
set -eu

KEY=$(security find-generic-password -a zai -s zai-api-key -w 2>/dev/null) || {
  echo "claude-glm: 키체인에 zai-api-key 가 없습니다." >&2
  echo "  security add-generic-password -a zai -s zai-api-key -U -w" >&2
  exit 1
}

MAIN="${GLM_MAIN:-glm-5.3}"
FAST="${GLM_FAST:-glm-5.3-flash}"

# --model 을 명시해 설정 기본값([1m] 접미사 등)이 붙지 않게 한다.
ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic" \
ANTHROPIC_AUTH_TOKEN="$KEY" \
ANTHROPIC_MODEL="$MAIN" \
ANTHROPIC_SMALL_FAST_MODEL="$FAST" \
ANTHROPIC_DEFAULT_OPUS_MODEL="$MAIN" \
ANTHROPIC_DEFAULT_SONNET_MODEL="$MAIN" \
ANTHROPIC_DEFAULT_HAIKU_MODEL="$FAST" \
ANTHROPIC_API_KEY= \
exec claude --model "$MAIN" "$@"
EOF
chmod +x ~/.local/bin/claude-glm
```

확인:

```bash
which claude-glm
# /Users/<you>/.local/bin/claude-glm
```

`claude-glm not found`가 나오면 `~/.local/bin`이 `PATH`에 없는 것입니다.

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

### 3. 한 줄 물어보기

테스트할 때는 모델을 무료 `glm-4.5-flash`로 바꿔 두세요. 코딩 플랜 한도(429)와 상관없이 확인할 수 있습니다. 이 글의 확인 출력도 전부 이 모델로 받았습니다.

```bash
export GLM_MAIN=glm-4.5-flash GLM_FAST=glm-4.5-flash
```

확인:

```bash
claude-glm -p "Reply with exactly: OK"
# OK
```

테스트가 끝나면 `unset GLM_MAIN GLM_FAST` 한 줄로 기본 모델(`glm-5.3`)로 돌아갑니다. 저는 19초 걸렸습니다. `OK` 위에 `"glm-5.3" isn't described by this version's model catalog` 경고가 같이 나올 수 있습니다. 아래 함정 절에서 다룹니다. 동작에는 문제가 없습니다.

대화형으로 쓰려면 그냥 `claude-glm`만 치면 됩니다. 화면, 스킬, 슬래시 명령이 `claude`와 같습니다.

### 4. 규칙은 `AGENTS.md`에, `CLAUDE.md`는 링크로

어떤 일을 GLM에 넘길지는 에이전트가 읽는 규칙 파일에 적어 둡니다. 여기서 한 가지를 정리하고 가겠습니다.

- Claude Code는 `CLAUDE.md`를 읽습니다.
- Codex 같은 다른 에이전트는 `AGENTS.md`를 읽습니다.

두 파일을 따로 두면 언젠가 내용이 갈라집니다. 그래서 **규칙은 `AGENTS.md` 하나에 쓰고, `CLAUDE.md`는 그 파일을 가리키는 링크로** 둡니다.

> **쉽게 말하면** 심볼릭 링크는 **바로가기 아이콘**입니다. `CLAUDE.md`를 열면 실제로는 `AGENTS.md`가 열립니다. 고칠 곳이 한 군데뿐입니다.
{: .prompt-tip }

처음에는 빈 연습 폴더에서 해 보는 것을 권합니다. 5단계까지 이 폴더에서 이어집니다.

```bash
mkdir -p ~/glm-playground && cd ~/glm-playground
```

이제 아래를 붙입니다. 제가 실제로 쓰는 [OpenFluxGate](https://github.com/OpenFluxGate) 작업 폴더의 `AGENTS.md`에서 GLM 부분만 덜어 낸 것입니다.

```bash
cat >> AGENTS.md <<'EOF'

## z.ai 로 넘길 작업

z.ai(GLM)는 사람이 직접 호출한다. 다른 에이전트가 자동으로 위임하지 않는다.

| 명령 | 용도 |
|---|---|
| `claude-glm` | Claude Code UI·스킬 그대로, 모델만 GLM. 헤드리스는 `claude-glm -p "..."` |
| `zcode` | 독립 에이전트. 문서·PPT·엑셀·PDF 작업 |

`claude` 와 `codex` 의 기본 동작은 바꾸지 않는다.

### 넘길 것

- 단순 반복 작업
- 번역 (한↔영 문서 맞추기 등)
- 문서 작업
- 명확하게 명세된 작업. 판단이 필요 없는 것
- 개인정보·비밀값이 없는 작업

### 넘기지 말 것

- 개인정보, 자격증명, 고객 데이터, 비공개 사업 정보. z.ai 는 제3자 처리자다.
- 설계 판단, 되돌리기 어려운 결정
- 자동화 파이프라인의 부품

### Claude Code 에게

- 분량이 벽인 작업은 직접 하지 말고 claude-glm 위임을 **제안**한다. 자동으로 넘기지 않는다.

### 키 관리

API 키는 macOS 키체인에 있다 (`-a zai -s zai-api-key`). 설정 파일·커밋·대화에 키를 노출하지 않는다.
EOF
ln -s AGENTS.md CLAUDE.md 2>/dev/null || echo "CLAUDE.md 가 이미 있습니다. 내용을 AGENTS.md 로 옮기고 지운 뒤 이 줄만 다시 실행하세요."
```

실제 프로젝트에 적용할 때 이미 `CLAUDE.md`가 있다면, 그 내용을 `AGENTS.md`로 옮긴 뒤 지우고 링크를 겁니다.

확인:

```bash
ls -l CLAUDE.md
# CLAUDE.md -> AGENTS.md
claude -p "AGENTS.md 기준으로, 영문 문서 40개 번역은 누구에게 맡겨야 해? 한 줄로."
# z.ai(GLM)에 직접 `claude-glm`으로 맡기면 됩니다. AGENTS.md는 번역을 넘길 작업으로 분류하고,
# 위임은 자동이 아니라 사람이 호출하도록 정해 두었습니다. ...
```

📌 마지막 줄의 "자동으로 넘기지 않는다"가 중요합니다. Claude가 알아서 GLM을 부르면 무엇이 어디로 나갔는지 사람이 모릅니다. 넘기는 결정은 사람이 합니다.

### 5. 여러 개를 동시에 넘기기

여기가 이 글의 핵심입니다. `claude-glm -p`는 표준 입력으로 문서를 받고, 결과를 표준 출력으로 내보냅니다. 그래서 `xargs -P`로 몇 개를 동시에 돌릴지 정할 수 있습니다.

먼저 연습 폴더에 번역할 문서 3개와 Java 파일 하나를 만듭니다. 내 프로젝트에서 할 때는 이 블록을 건너뛰면 됩니다.

```bash
cd ~/glm-playground
git init -q
mkdir -p docs/ko src/main/java/demo
printf '# 설치\n\n저장소를 클론한 뒤 `./gradlew build` 를 실행합니다.\n' > docs/ko/install.md
printf '# 설정\n\n`application.yml` 에서 [포트](https://example.com)를 바꿀 수 있습니다.\n' > docs/ko/config.md
printf '# 문제 해결\n\n빌드가 실패하면 `./gradlew clean` 을 먼저 실행합니다.\n' > docs/ko/troubleshoot.md
cat > src/main/java/demo/Calc.java <<'EOF'
package demo;

public class Calc {
    public int add(int a, int b) { return a + b; }
    public int div(int a, int b) { return a / b; }
}
EOF
git add -A && git -c user.name=demo -c user.email=demo@example.com commit -qm init
```

**번역**: `docs/ko/`의 문서를 4개씩 동시에 영어로 옮겨 `docs/en/`에 씁니다.

```bash
mkdir -p docs/en
ls docs/ko/*.md | xargs -P 4 -I{} sh -c '
  claude-glm -p "Translate this Markdown document to English. Keep code blocks and links as they are. Output only the translated document." \
    < "{}" > "docs/en/$(basename "{}")"
'
```

**문서화**: 파일마다 public 메서드에 Javadoc을 답니다. 이번에는 파일을 고쳐야 하니 쓸 수 있는 도구를 `Read`, `Edit`로만 열어 줍니다.

```bash
find src/main/java -name '*.java' | xargs -P 4 -I{} \
  claude-glm -p "{} 의 public 메서드에 한국어 Javadoc 을 달아 줘. 코드 동작은 바꾸지 마." \
    --allowedTools "Read" "Edit"
```

> **쉽게 말하면** `xargs -P 4`는 **계산대를 4개 여는 것**입니다. 손님(파일)은 비어 있는 계산대로 갑니다. 너무 많이 열면 아래 함정 절의 사용량 한도에 걸립니다.
{: .prompt-tip }

확인:

```bash
ls docs/ko | wc -l; ls docs/en | wc -l
# 3
# 3
git diff --stat
# src/main/java/demo/Calc.java | 20 ++++++++++++++++++++
```

제가 무료 모델로 돌렸을 때 번역은 문서 3개가 동시에 19초 만에 끝났고, 코드 블록과 링크도 그대로 남았습니다. Javadoc은 파일 하나에 3분 가까이 걸렸습니다. 파일을 읽고 고치는 왕복이 있어서 번역보다 느립니다. 그래서 동시에 돌리는 효과가 큽니다.

개수가 같고, `git diff`에 의도한 파일만 바뀌었으면 됩니다. 결과는 마지막에 `claude`(Anthropic)로 한 번 훑어보게 하면 안심이 됩니다.

---

## zcode는 언제 쓰나요

`zcode`는 Z.AI가 만든 별도 에이전트입니다. PPT·엑셀·PDF처럼 결과물이 문서 파일인 일에 씁니다. 공식 터미널 CLI가 없어서 비공식 패키지로 씁니다. 설치는 [zcode cli 사용기](/posts/zcode-cli-review)를 참고하시면 됩니다.

```bash
zcode -p "README.md 를 읽고 발표용 5장 요약을 만들어 줘" --disallowed-tools "Bash Write Edit"
```

zcode에는 모델을 고르는 옵션이 없어서 코딩 플랜 모델로만 돕니다. 한도에 걸리면 무료 모델로 우회할 수 없으니 풀릴 때까지 기다려야 합니다.

📌 제가 써 본 바로는 `--disallowed-tools "Bash Write Edit"`가 실제로 막히는 유일한 경계였습니다. 쓰기를 열어 주면 격리되지 않습니다. Bash를 막았는데도 홈 디렉터리에 pip 설치를 했습니다. 쓰기 작업은 전용 worktree 안에서만 시킵니다.

---

## 빠지기 쉬운 함정

### `"glm-5.3" isn't described by this version's model catalog`

Claude Code가 모르는 모델 이름이라 문맥 창(context window)을 200k로 가정하겠다는 경고입니다. → 동작에는 지장이 없습니다. 긴 대화에서 자동 요약이 일찍 걸릴 수 있다는 정도만 알아 두면 됩니다.

### `API Error: Request rejected (429) · Usage limit reached for 5 hour`

코딩 플랜의 5시간 사용량을 다 쓴 것입니다. 이 글을 쓰다가 저도 걸렸습니다. 이때 `claude-glm`은 바로 실패하지 않고 재시도하느라 3분 가까이 붙잡고 있다가 끝났습니다. → 동시 실행 수를 줄이거나, 분량 큰 저위험 작업은 Flash로 돌립니다. 에러 메시지에 풀리는 시각이 나옵니다.

```bash
GLM_MAIN=glm-5.3-flash claude-glm -p "..."
```

제 경우에는 `glm-5.3-flash`도 같은 한도에 묶여 있었습니다. 이때는 무료 모델 `glm-4.5-flash`로 바꾸면 바로 돌아갑니다. 이 글의 확인 출력도 이 모델로 받았습니다.

```bash
GLM_MAIN=glm-4.5-flash GLM_FAST=glm-4.5-flash claude-glm -p "Reply with exactly: OK"
```

### `claude.ai connectors are disabled ...`

`claude-glm`으로 띄우면 claude.ai 계정에 연결한 커넥터(Gmail, Drive 등)가 꺼진다는 안내가 나옵니다. 인증 수단을 Z.AI 키로 바꿨으니 당연한 동작입니다. → 커넥터가 필요한 일은 `claude`로 합니다.

### 모델 이름 뒤에 `[1m]`이 붙어 실패

`~/.claude/settings.json`의 기본 모델이 `opus[1m]` 같은 형식이면 그 접미사가 GLM 모델 이름에 붙어 나갈 수 있습니다. → 스크립트에서 `--model "$MAIN"`을 명시해 막아 두었습니다.

### 셸에 `ANTHROPIC_API_KEY`가 남아 있음

이 값이 있으면 Claude Code가 그쪽 키를 먼저 쓰려고 합니다. → 스크립트에서 `ANTHROPIC_API_KEY=`로 비워 두었습니다.

### Codex에도 붙이고 싶을 때

2026-10-01 기준으로 Codex 0.159.3에서는 안 됩니다. Codex는 커스텀 공급자에 `wire_api = "responses"`만 받는데, Z.AI는 Responses API를 제공하지 않습니다. → 변환 프록시 없이는 불가능해서 Codex는 GPT로 둡니다. 대신 Codex도 `AGENTS.md`의 레인 규칙은 같이 읽습니다.

> 개인정보나 비밀값이 섞인 코드는 GLM에 넘기지 않습니다. Z.AI는 제3자 처리자입니다. zcode에 동의 없는 업로드 이력이 있었던 일도 [zcode cli 사용기](/posts/zcode-cli-review)에 적어 두었습니다.
{: .prompt-warning }

---

## 되돌리기

```bash
unset GLM_MAIN GLM_FAST
rm -rf ~/glm-playground
rm ~/.local/bin/claude-glm
security delete-generic-password -a zai -s zai-api-key
```

실제 프로젝트에서 `CLAUDE.md` 링크를 풀고 Claude 전용 파일로 되돌리려면, 그 프로젝트 루트에서 따로 실행합니다.

```bash
rm CLAUDE.md && mv AGENTS.md CLAUDE.md
```

`claude`는 처음부터 건드리지 않았으니 되돌릴 것이 없습니다.

---

## 참고한 내용들

### 스크립트가 바꾸는 환경변수

| 변수 | 값 | 의미 |
|------|----|------|
| `ANTHROPIC_BASE_URL` | `https://api.z.ai/api/anthropic` | 요청을 보낼 주소 |
| `ANTHROPIC_AUTH_TOKEN` | 키체인의 Z.AI 키 | 인증 헤더 |
| `ANTHROPIC_MODEL` | `glm-5.3` | 기본 모델 |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` / `_SONNET_MODEL` | `glm-5.3` | Claude Code가 opus·sonnet을 부를 때 대신 쓸 모델 |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL`, `ANTHROPIC_SMALL_FAST_MODEL` | `glm-5.3-flash` | 가벼운 내부 호출용 |
| `ANTHROPIC_API_KEY` | (빈 값) | 셸에 남은 Anthropic 키가 끼어들지 않게 |

### Reference Links

- [Z.AI: Claude Code에서 GLM 쓰기](https://docs.z.ai/devpack/tool/claude)
- [Claude Code: 환경변수](https://docs.anthropic.com/en/docs/claude-code/settings#environment-variables)
- [AGENTS.md](https://agents.md/)
- [zcode cli 사용기 - (공식이 없어, 비공식 cli 사용)](/posts/zcode-cli-review)
