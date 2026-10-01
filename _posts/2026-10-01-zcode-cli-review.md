---
title: zcode cli 사용기 - (공식이 없어, 비공식 cli 사용)
author: rojae
date: 2026-10-01 00:00:00 +0900
published: true
categories: [tech-talk]
tags: [zcode, glm, cli, npm, retrospective]
image:
  path: /assets/img/posts/2026-10-01-zcode-cli-review/cover.svg
---
> Z.AI의 `zcode`를 터미널에서 쓰려다 막힌 이야기다. 공식 배포는 데스크톱 앱뿐이었고, 터미널 화면은 비공식 npm 패키지로 띄웠다.
> + 같은 에러를 만났다면 [zcode-app-cli](https://npmx.dev/package/zcode-app-cli)를 보면 된다.
{: .prompt-info }

---

## **"Cannot find package '@zcode/tui'"**

밤 11시쯤, brew로 `zcode`를 깔고 로그인까지 마쳤다. `zcode`를 치자 이 한 줄이 나왔다.

```
Error: Cannot find package '@zcode/tui' imported from
/Applications/ZCode.app/Contents/Resources/glm/zcode.cjs
```

로그인은 됐고, `zcode -p "..."`로 한 줄 물으면 답도 왔다. 안 되는 건 터미널 화면(TUI) 하나였다.

---

## **"앱 안에는 화면이 없었다"**

brew가 깔아 주는 `zcode`는 데스크톱 앱 안의 스크립트를 부르는 래퍼다. 그 스크립트는 TUI를 `@zcode/tui` 패키지에서 불러오는데, 앱 번들 어디에도 그 패키지가 없었다. npm에도 공개돼 있지 않았다.

공식 GitHub 릴리스를 봐도 `.dmg`와 `.exe`뿐이었다. 데스크톱 앱은 GUI만 쓰니 터미널 화면을 넣을 이유가 없었던 것이다. 정리하면, **Z.AI는 터미널에서 쓰는 CLI를 공식으로 내놓지 않았다.**

소스에서 직접 빌드해 보려고도 했다. 2GB 넘는 의존성을 받다가, 그게 데스크톱 앱 전체를 빌드하는 과정이라는 걸 알고 멈췄다.

---

## **"비공식 CLI는 있었다"**

결국 쓴 건 누군가 npm에 올려 둔 [zcode-app-cli](https://npmx.dev/package/zcode-app-cli)였다. 설치 전에 설치 스크립트가 없는지만 확인했다.

```bash
npm view zcode-app-cli scripts dependencies
npm install -g --prefix ~/.local zcode-app-cli
zcode
```

brew의 `zcode`와 이름이 겹쳐서 `~/.local`에 깔았다. `~/.local/bin`이 PATH에서 앞에 있으면 이쪽이 먼저 잡힌다. 로그인 정보는 그대로 쓰였고, API 키도 필요 없었다.

```
╭─ ◆ ZCODE  v3.14.4-30 ──────────────────────────────╮
│ Ask a task about this workspace                    │
╰─ /help commands · /status details ─────────────────╯
 ◈ GLM-5.3 ─ ◉ build ─ ⚡ max ─ ctx 100% ─ session 0
```

되돌리고 싶으면 `npm uninstall -g --prefix ~/.local zcode-app-cli` 한 줄이면 된다.

> **쉽게 말하면** PATH는 **열쇠 꾸러미를 앞에서부터 꽂아 보는 순서**다. 같은 이름의 열쇠가 둘이면 앞에 걸린 것으로 문이 열린다.
{: .prompt-tip }

---

## **"느낀 점"**

아쉬운 건 하나다. 코딩용 모델과 코딩 플랜까지 내놓았는데, 개발자가 하루 종일 붙어 있는 터미널용 공식 CLI가 없다.

그래도 이상한 일은 아니다. 얼마 전까지는 ChatGPT도 Claude도 웹 채팅이 전부였다. 공식 CLI가 나오기 전에는 사람들이 API를 감싼 비공식 도구를 만들어 썼다. 지금 zcode가 그 자리에 있는 것 같다.

- 공식 배포에 없으면, 누군가 이미 만들어 둔 것이 있는지 먼저 찾아본다.
- 비공식 패키지는 설치 스크립트와 의존성부터 열어 본다.

*공식 CLI가 나오면 이 글은 지워도 될 것 같다.*
