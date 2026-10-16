---
title: 가비아 도메인 메일을 Gmail로 받기 - (ImprovMX로 rojae@rojae.kr 연결한 기록)
author: rojae
date: 2026-10-08 00:00:00 +0900
published: true
categories: [infra]
tags: [dns, mx, spf, gmail, improvmx, gabia, custom-domain]
image:
  path: /assets/img/posts/2026-10-08-gabia-domain-mail-to-gmail/08-improvmx-dns-active.png
---
> 받는 길은 가비아 DNS와 무료 포워딩 서비스 ImprovMX로, 보내는 길은 Gmail SMTP로 따로 만들었습니다. 30분 정도 걸렸고, 중간에 멈칫한 두 군데(숨은 확인창, Gmail의 SMTP 자동 입력)와 보낸 메일의 서명이 Gmail 이름으로 찍히는 한계를 함께 적었습니다. 전달된 메일이 처음에는 스팸함으로 갈 수 있다는 점도 주의로 덧붙였습니다.
{: .prompt-info }
<!-- post-check: tone=polite -->

## 도메인 메일함을 안 열게 되는 이유

`rojae.kr` 도메인을 쓴 지 꽤 됐습니다. 블로그도 여기에 붙어 있고, 사이드 프로젝트 API도 서브도메인으로 올려 두었습니다.

그런데 정작 `rojae@rojae.kr`로 온 메일은 거의 보지 않았습니다. 확인하려면 다른 메일 서비스에 따로 로그인해야 했거든요.

Gmail은 하루에도 수십 번 여는데, 도메인 메일함은 한 달에 한 번 들어갈까 말까였습니다. 이러다 중요한 메일을 놓치겠다 싶어서 날을 잡았습니다. 목표는 이렇게 정했습니다.

> `rojae@rojae.kr`로 오는 메일을 Gmail에서 받고, Gmail에서 `rojae@rojae.kr`로 답장한다. 돈은 쓰지 않는다.

## 방법은 세 가지였습니다

무료 Gmail은 내 도메인 메일을 직접 받지 못합니다. MX 레코드를 Gmail 쪽으로 돌려도 받아 주지 않습니다. 그래서 길은 세 가지입니다.

| 방법 | 비용 | 좋은 점 | 아쉬운 점 |
|---|---|---|---|
| Google Workspace | 월 구독 | 도메인 전용 계정, 도메인 DKIM을 설정하면 발송 인증이 모두 맞음 | 개인용으로는 과함 |
| 포워딩 서비스 + Gmail "다른 주소로 보내기" | 무료 | Gmail 하나로 끝 | 보낸 메일의 서명이 Gmail 이름으로 찍힘 |
| 기존 메일 서비스 + Gmail POP3 가져오기 | 무료 | DNS를 안 건드림 | Gmail 웹의 POP3 가져오기가 2026년 1월에 종료됨 ([출처](https://www.theregister.com/2026/01/05/gmail_dropping_pop3/)) |

회사 메일이었다면 고민 없이 Workspace를 썼을 겁니다. 하지만 개인 연락용 주소에 매달 돈을 내기는 아까웠습니다. 그래서 두 번째 방법으로 갔고, 포워딩 서비스는 가입이 간단하고 무료 플랜이 넉넉한 ImprovMX로 골랐습니다.

두 번째 방법을 고르면 메일이 오가는 길이 둘로 나뉩니다. MX 레코드는 이 도메인 앞으로 온 메일을 어느 서버가 받을지 알려 주는 값이고, ImprovMX는 그 서버가 되어 받은 메일을 Gmail로 다시 보내 줍니다.

보낼 때는 이 길을 거치지 않고 Gmail의 SMTP 서버가 직접 내보냅니다. 아래 그림의 헤더 상자에서 Return-Path는 반송 주소, DKIM은 발송 서버가 메일에 붙이는 서명입니다.

<figure class="post-figure post-figure--diagram" id="figure-mailflow" aria-labelledby="mailflow-caption">
  <div class="figure-head"><small>01 · 메일 경로</small>받는 길과 보내는 길은 설정이 따로이고, 정렬이 어긋나는 곳은 보내는 길입니다</div>
  <picture class="diagram-wide"><img data-preserve-picture="true" src="/assets/img/posts/2026-10-08-gabia-domain-mail-to-gmail/mailflow-desktop.svg" alt="받는 경로(1~3단계)는 발신자에서 MX 조회(mx1·mx2.improvmx.com), ImprovMX 전달을 거쳐 Gmail 받은편지함으로 갑니다. 보내는 경로(4단계)는 Gmail에서 보낸 사람 rojae@rojae.kr을 고르고 smtp.gmail.com(587, TLS, 앱 비밀번호)을 거쳐 수신자에게 갑니다. 4단계에서 Gmail이 rojae@rojae.kr로 보내는 확인 메일은 받는 경로로 돌아옵니다. 보낸 메일의 From은 rojae@rojae.kr, Return-Path와 DKIM은 gmail.com이라 SPF·DKIM은 통과해도 DMARC 정렬은 되지 않습니다." width="700" height="620" loading="lazy"></picture>
  <picture class="diagram-narrow"><img data-preserve-picture="true" src="/assets/img/posts/2026-10-08-gabia-domain-mail-to-gmail/mailflow-mobile.svg" alt="받는 경로(1~3단계)는 발신자에서 MX 조회(mx1·mx2.improvmx.com), ImprovMX 전달을 거쳐 Gmail 받은편지함으로 갑니다. 보내는 경로(4단계)는 Gmail에서 보낸 사람 rojae@rojae.kr을 고르고 smtp.gmail.com(587, TLS, 앱 비밀번호)을 거쳐 수신자에게 갑니다. 4단계에서 Gmail이 rojae@rojae.kr로 보내는 확인 메일은 받는 경로로 돌아옵니다. 보낸 메일의 From은 rojae@rojae.kr, Return-Path와 DKIM은 gmail.com이라 SPF·DKIM은 통과해도 DMARC 정렬은 되지 않습니다." width="320" height="1098" loading="lazy"></picture>
  <figcaption id="mailflow-caption">위쪽 길이 1~3단계, 아래쪽 길이 4단계입니다. 헤더 상자에서는 From과 gmail.com이 어긋난 곳을 보세요. 설정은 따로지만 4단계의 확인 메일이 받는 길을 타므로 1~3단계를 먼저 끝내세요.<br><a class="diagram-source diagram-wide" href="/assets/img/posts/2026-10-08-gabia-domain-mail-to-gmail/mailflow-desktop.svg" target="_blank" rel="noopener">그림 원본 보기 ↗</a><a class="diagram-source diagram-narrow" href="/assets/img/posts/2026-10-08-gabia-domain-mail-to-gmail/mailflow-mobile.svg" target="_blank" rel="noopener">그림 원본 보기 ↗</a></figcaption>
</figure>

## 환경

| 항목 | 값 |
|------|-----|
| 도메인·DNS | 가비아 DNS 관리 툴 |
| 포워딩 | ImprovMX 무료 플랜 |
| 메일함 | Gmail 무료 계정 (2단계 인증 사용 중) |

## 순서대로

### 1. 지금 DNS가 어떤 상태인지 봅니다

가비아에 로그인해서 My가비아 → DNS 관리 툴로 들어가면 도메인 목록이 나옵니다.

<figure class="post-figure">
  <img src="/assets/img/posts/2026-10-08-gabia-domain-mail-to-gmail/01-gabia-dns-list.png" alt="가비아 DNS 관리 도메인 목록, rojae.kr의 DNS 정보에 CNAME·TXT·MX·A가 보임">
  <figcaption>rojae.kr의 DNS 정보 칸에서 CNAME·TXT·A와 함께 MX가 이미 걸려 있는지 봅니다.</figcaption>
</figure>

여기서 MX가 이미 보인다면, 예전에 다른 메일 서비스를 붙여 둔 흔적입니다. 저도 그랬습니다. 연결한 기억이 없었는데 MX가 두 줄 남아 있었습니다.

이번에 이걸 ImprovMX로 바꾸면, 바꾸는 순간부터 새 메일은 그쪽으로 가지 않습니다. 먼저 그 메일함을 아직 쓰고 있지 않은지 확인하고, 남길 메일이 있다면 미리 백업해 두세요.

A, CNAME, 사이트 인증용 TXT처럼 메일과 상관없는 레코드는 건드리지 않습니다. 그리고 SPF 레코드가 있는지도 같이 봐 두세요. 저는 없었습니다.

확인:

```bash
dig +short MX rojae.kr
# 지금 걸려 있는 MX가 나옵니다. 아무것도 안 나오면 MX가 없는 상태입니다
```

`dig`가 없는 환경(Windows 기본 등)에서는 `nslookup -type=MX rojae.kr`로 같은 내용을 볼 수 있습니다.

### 2. 가비아에서 MX를 바꾸고 SPF를 추가합니다

DNS 설정의 [레코드 수정]을 누르면 편집 창이 뜨고, 줄마다 수정·삭제 버튼이 있습니다. 기존 MX를 지우고 새로 추가해도 되지만, 저는 수정으로 값만 바꿨습니다. 타입, 호스트, TTL이 같으니 값과 우선순위만 고치면 됩니다.

기존 MX 줄의 [수정]을 누르면 브라우저 확인창이 먼저 뜹니다. 화면이 멈춘 것처럼 보이면 함정 1을 보세요. 확인을 누르면 줄이 입력칸으로 바뀝니다.

<figure class="post-figure">
  <img src="/assets/img/posts/2026-10-08-gabia-domain-mail-to-gmail/03-gabia-mx-edit.png" alt="가비아 레코드 수정 창에서 MX 줄이 입력칸으로 바뀐 상태">
  <figcaption>MX 줄의 버튼이 [확인]·[취소]로 바뀌고 값·우선순위 칸이 입력칸이 되면 편집 상태에 들어간 것입니다.</figcaption>
</figure>

넣을 값은 두 줄입니다.

| 타입 | 호스트 | 값 | 우선순위 | TTL |
|---|---|---|---|---|
| MX | @ | `mx1.improvmx.com.` | 10 | 600 |
| MX | @ | `mx2.improvmx.com.` | 20 | 600 |

값 끝의 점(`.`)은 가비아가 기존 값에도 붙여 쓰고 있어서 그대로 맞췄습니다. 빼도 가비아가 알아서 처리하지만, 형식이 같아야 나중에 보기 편합니다.

<figure class="post-figure">
  <img src="/assets/img/posts/2026-10-08-gabia-domain-mail-to-gmail/04-gabia-mx1-done.png" alt="첫 번째 MX를 mx1.improvmx.com.으로 변경하고 두 번째 MX는 이전 값인 상태">
  <figcaption>첫 번째 MX만 <code>mx1.improvmx.com.</code>으로 바뀌었고, 두 번째 줄은 아직 이전 값입니다.</figcaption>
</figure>

줄마다 있는 [확인]은 그 줄만 확정할 뿐, 아직 저장된 게 아닙니다. 두 번째 MX도 같은 방법으로 `mx2.improvmx.com.`, 우선순위 20으로 바꿨습니다. 확인창은 여기서도 또 뜹니다.

다음은 SPF입니다. [+ 레코드 추가]로 TXT 한 줄을 넣습니다.

```text
TXT  @  v=spf1 include:spf.improvmx.com include:_spf.google.com ~all
```

- `include:spf.improvmx.com`은 ImprovMX 서버가 `rojae.kr` 이름으로 보내도 된다는 뜻입니다. 받는 길 자체는 MX만으로 동작하지만, ImprovMX 대시보드도 이 값을 함께 검사합니다(캡처 08).
- `include:_spf.google.com`은 ImprovMX가 권장값으로 보여 주는 줄(캡처 08)을 그대로 넣은 것입니다. 이 구성에서는 실제로 쓰이지 않지만 손해는 없습니다. 이유는 뒤의 "알아 둘 점"에서 다룹니다.
- `~all`은 명단에 없는 서버면 의심만 하라는 뜻(softfail)입니다. 처음부터 거절(`-all`)로 두는 것보다, 명단을 빠뜨렸을 때 정상 메일이 거절될 위험이 적습니다.

> **쉽게 말하면** SPF는 **"우리 도메인 이름으로 메일을 보내도 되는 서버 명단"**입니다. 받는 쪽은 메일이 이 명단에 있는 서버에서 왔는지 보고 얼마나 믿을지 정합니다.
{: .prompt-tip }

> SPF 레코드는 도메인당 하나만 있어야 합니다. `v=spf1`로 시작하는 TXT가 두 개 이상이면 SPF 검사 자체가 오류(`permerror`)가 됩니다. 이미 SPF가 있다면 새로 만들지 말고 기존 줄에 `include:`를 이어 붙이세요. `google-site-verification` 같은 다른 TXT와는 같이 있어도 괜찮습니다.
{: .prompt-warning }

<figure class="post-figure">
  <img src="/assets/img/posts/2026-10-08-gabia-domain-mail-to-gmail/05-gabia-dns-after.png" alt="최종 DNS 레코드, MX 2개를 ImprovMX로 교체하고 SPF TXT를 추가한 상태">
  <figcaption>MX 두 줄이 ImprovMX로 바뀌고 맨 아래에 SPF TXT 한 줄이 들어간, 저장하기 직전 상태입니다.</figcaption>
</figure>

[저장]을 누르면 끝입니다. 이전 레코드의 TTL도 600초라 오래 기다리지 않았습니다. 이전 TTL이 길었다면 그만큼 기다려야 합니다.

확인:

```bash
dig +short MX rojae.kr
# 10 mx1.improvmx.com.
# 20 mx2.improvmx.com.

dig +short TXT rojae.kr | grep spf
# "v=spf1 include:spf.improvmx.com
#  include:_spf.google.com ~all"
# (실제 출력은 한 줄입니다)
```

### 3. ImprovMX에 도메인을 등록합니다

DNS가 ImprovMX를 가리키게 됐으니, 이제 ImprovMX가 이 도메인의 메일을 받아 어디로 넘길지 알려 줄 차례입니다.

[improvmx.com](https://improvmx.com)에는 Gmail로 받을 주소로 가입합니다. 기본 전달 대상이 가입한 주소이기 때문입니다. 가입하면 바로 대시보드가 나오고, 아직 도메인은 하나도 없습니다.

<figure class="post-figure">
  <img src="/assets/img/posts/2026-10-08-gabia-domain-mail-to-gmail/06-improvmx-empty.png" alt="ImprovMX 대시보드, No domains found 표시">
  <figcaption>가입 직후 "No domains found"가 보이면 정상이며, 아래 입력칸에 도메인을 넣습니다.</figcaption>
</figure>

아래 입력칸에 `rojae.kr`을 넣고 [Add Domain]을 누릅니다.

<figure class="post-figure">
  <img src="/assets/img/posts/2026-10-08-gabia-domain-mail-to-gmail/07-improvmx-domain-added.png" alt="도메인 추가 직후 catch-all 별칭이 자동 생성된 ImprovMX 화면">
  <figcaption>도메인을 추가하자마자 <code>* @rojae.kr → 가입한 Gmail</code> 별칭이 자동으로 생긴 것을 확인합니다.</figcaption>
</figure>

`*`는 모든 주소를 받는다는 뜻(catch-all)이라 `rojae@`든 `hello@`든 전부 제 Gmail로 옵니다. 개인 도메인이라 저는 이게 오히려 편했습니다.

서비스에 가입할 때마다 `netflix@rojae.kr`, `github@rojae.kr`처럼 주소를 다르게 쓰면, 나중에 스팸이 들어왔을 때 어디서 주소가 샜는지 바로 알 수 있습니다.

특정 주소만 받고 싶다면 `*`를 지우고 `rojae` 같은 별칭만 남기면 됩니다. 전달받을 주소를 가입 계정이 아닌 다른 메일로 바꾸면 그 주소로 인증 메일이 한 번 갑니다.

도메인 옆의 빨간 Setup 표시는 DNS를 아직 못 찾았다는 뜻입니다. 저는 DNS를 이미 넣어 둔 상태라 DNS Records 탭을 열어 보기만 하면 됐습니다.

확인:

<figure class="post-figure">
  <img src="/assets/img/posts/2026-10-08-gabia-domain-mail-to-gmail/08-improvmx-dns-active.png" alt="ImprovMX DNS 검증 완료, MX 2개와 SPF 1개 체크, 상태 Active">
  <figcaption>MX 두 개와 SPF 한 개에 모두 체크가 붙고 상태가 Active로 바뀌면 받는 쪽 DNS 검증이 끝난 것입니다.</figcaption>
</figure>

DNS를 먼저 넣고 ImprovMX에 등록하는 순서로 했더니 기다릴 것도 없이 바로 통과했습니다. 순서를 바꿔도 되지만, 그러면 DNS가 퍼질 때까지 Setup 상태로 잠깐 기다려야 합니다.

### 4. Gmail에서 rojae@rojae.kr로 보냅니다

여기부터는 그림의 아래쪽 길입니다. 이 단계의 확인 메일이 받는 길로 들어오므로, 3단계의 Active까지 끝낸 뒤에 시작합니다. 목표는 답장할 때 보낸 사람이 `@gmail.com`이 아니라 `rojae@rojae.kr`로 보이게 하는 것입니다.

먼저 앱 비밀번호를 준비합니다. Gmail SMTP에는 평소 로그인 비밀번호를 쓸 수 없고, 2단계 인증을 켠 계정에서 발급하는 16자리 앱 비밀번호가 필요합니다.

[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)에서 하나 만들어 두세요. 2단계 인증이 꺼져 있으면 이 메뉴가 보이지 않습니다.

그다음 Gmail 설정 → 모든 설정 보기 → 계정 및 가져오기 → 다른 주소에서 메일 보내기 → 다른 이메일 주소 추가를 누릅니다.

<figure class="post-figure">
  <img src="/assets/img/posts/2026-10-08-gabia-domain-mail-to-gmail/09-gmail-add-address.png" alt="Gmail 다른 이메일 주소 추가 팝업, 이름·이메일 주소·별칭으로 처리 체크">
  <figcaption>이름과 이메일 주소를 넣고, "별칭으로 처리(Treat as an alias)"는 체크된 그대로 둡니다.</figcaption>
</figure>

이름에는 받는 사람에게 보일 이름을, 이메일 주소에는 `rojae@rojae.kr`을 넣습니다. "별칭으로 처리"는 내 주소들끼리 오간 메일을 한 사람의 것으로 묶어 주는 옵션이라, 개인 별칭이면 켜 두는 게 맞습니다.

[다음 단계]를 누르면 SMTP 설정 화면이 나옵니다. Gmail이 칸을 미리 채워 두는데, 그대로 두면 안 됩니다(함정 2). 값은 이렇게 바꿉니다.

| 항목 | 값 |
|---|---|
| SMTP 서버 | `smtp.gmail.com` |
| 포트 | `587` |
| 사용자 이름 | Gmail 주소 전체 (`xxx@gmail.com`) |
| 비밀번호 | 앞에서 만든 앱 비밀번호 |
| 보안 연결 | TLS (권장) |

<figure class="post-figure">
  <img src="/assets/img/posts/2026-10-08-gabia-domain-mail-to-gmail/11-gmail-smtp-filled.png" alt="Gmail SMTP 설정에 smtp.gmail.com, 587, TLS를 입력한 화면">
  <figcaption>SMTP 서버 <code>smtp.gmail.com</code>, 포트 587, TLS로 바꾸고 사용자 이름은 Gmail 주소 전체를 넣은 상태입니다.</figcaption>
</figure>

[계정 추가]를 누르면 Gmail이 `rojae@rojae.kr`로 확인 메일을 보냅니다. 이 메일은 3단계에서 만든 포워딩을 타고 바로 제 Gmail로 돌아옵니다.

하나 더, 같은 화면에서 "메일에 답장할 때: 메일을 받은 주소에서 답장"을 골라 두는 걸 추천합니다. `rojae@rojae.kr`로 온 메일에 답장하면 보낸 사람이 알아서 `rojae@rojae.kr`이 됩니다. 매번 드롭다운을 바꾸다 보면 꼭 한 번은 잊어버리거든요.

확인: 확인 메일이 Gmail에 도착하고 메일 속 링크를 눌러 주소가 추가되면 성공입니다. 받는 쪽을 먼저 끝내 둔 덕분에 저는 한 번에 끝났습니다. [계정 추가] 단계에서 인증 오류가 나면 SMTP 서버, 사용자 이름(Gmail 주소 전체), 앱 비밀번호를 다시 점검하세요.

## 확인

두 길이 모두 열렸는지는 실제 메일 두 통으로 봅니다.

- **받는 쪽**: 다른 메일 계정에서 `rojae@rojae.kr`로 한 통 보냅니다. 몇 초 안에 Gmail에 들어오면 성공입니다. 처음 한두 통은 스팸함으로 갈 수도 있으니 거기도 같이 봐 주세요.
- **보내는 쪽**: 새 메일 쓰기에서 보낸 사람을 `rojae@rojae.kr`로 바꿔 다른 계정으로 한 통 보냅니다. 받은 쪽에서 보낸 사람이 `rojae@rojae.kr`로 보이면 성공입니다.

안 될 때는 증상에 따라 볼 곳이 다릅니다.

| 증상 | 볼 곳 |
|---|---|
| 메일이 전혀 안 옴 | MX 값과 `dig +short MX` 결과 (1·2단계) |
| 4단계 인증 메일이 안 옴 | 받는 길부터 (ImprovMX Active, 스팸함) |
| 보낼 때 반송·인증 오류 | SMTP 서버·사용자 이름·앱 비밀번호 (4단계, 함정 2) |
| 받은 메일이 스팸함으로 감 | 함정 3 |
| 보낸 사람 옆에 gmail.com이 보임 | 알아 둘 점 (이 구성의 한계) |

## 빠지기 쉬운 함정

앞의 둘은 제가 실제로 멈칫한 곳이고, 세 번째는 처음 며칠 겪을 수 있는 주의 사항입니다.

### 1. 레코드를 수정하려는데 화면이 멈춘 것처럼 보일 때

다른 서비스와 연동해서 만든 MX는 가비아가 "서비스 연동 레코드"로 따로 분류해 둡니다. 그래서 [수정]을 누르면 정말 바꿀 거냐는 브라우저 확인창이 뜹니다. 저는 이 창이 뒤에 숨어 있어서 편집 창이 멈춘 줄 알았습니다. 확인창을 찾아 확인을 누르면 되고, 두 번째 MX에서도 또 뜹니다.

### 2. Gmail이 SMTP 서버를 MX 주소로 채워 둘 때

<figure class="post-figure">
  <img src="/assets/img/posts/2026-10-08-gabia-domain-mail-to-gmail/10-gmail-smtp-autofill.png" alt="Gmail이 SMTP 서버를 mx1.improvmx.com, 사용자 이름을 rojae로 자동 입력한 모습">
  <figcaption>확대해서 보면 SMTP 서버에 <code>mx1.improvmx.com</code>, 사용자 이름에 <code>rojae</code>가 미리 들어가 있으며, 이 값 그대로는 인증에 실패합니다.</figcaption>
</figure>

Gmail은 도메인의 MX를 조회해서 SMTP 서버 칸에 `mx1.improvmx.com`을, 사용자 이름에 `rojae`를 미리 넣어 둡니다. 친절해 보여서 그대로 넘길 뻔했습니다.

그런데 MX는 그림의 위쪽, 받는 길의 서버입니다. ImprovMX에서 메일을 보내는 SMTP는 유료 플랜(작성 시점 기준 월 $9) 기능이라, 이대로 진행하면 인증에서 실패합니다. 4단계 표의 값으로 바꿔 주세요.

### 3. 전달된 메일이 스팸함으로 갈 때

Gmail 입장에서 포워딩된 메일은 "ImprovMX 서버가 보낸 메일"입니다. 그래서 원래 보낸 사람의 SPF가 깨진 것처럼 보일 수 있습니다.

ImprovMX는 SRS(전달하면서 반송 주소를 바꾸는 방식)를 씁니다. SRS는 SPF 실패를 막고, DMARC는 원래 보낸 쪽의 DKIM 서명이 남아 있을 때 통과합니다. 그래도 처음에는 Gmail이 익숙해질 때까지 스팸함으로 가는 경우가 있습니다.

"스팸 아님"을 몇 번 눌러 주거나, `to:rojae@rojae.kr` 조건으로 "스팸으로 보내지 않음" 필터를 하나 만들어 두면 됩니다.

## 알아 둘 점 – 보낸 메일의 서명은 Gmail 이름으로 찍힙니다

함정을 넘기고 나면 남는 것은 설정 실수가 아니라 이 구성 자체의 한계입니다. 그림 아래쪽 헤더 상자가 그 지점입니다. Gmail SMTP로 `rojae@rojae.kr` 메일을 보내면 헤더는 대략 이렇게 나갑니다.

```text
From:           rojae@rojae.kr
Return-Path:    xxx@gmail.com      ← 실제 발송 주소는 Gmail
DKIM-Signature: d=gmail.com        ← 서명한 도메인도 gmail.com
```

SPF와 DKIM 모두 `gmail.com` 기준으로는 통과합니다. 하지만 보낸 사람 주소의 도메인(`rojae.kr`)과는 이름이 맞지 않습니다. 이걸 "정렬되지 않았다"고 합니다.

> **쉽게 말하면** DMARC 정렬은 **"편지 봉투의 보낸 사람과 도장을 찍은 사람이 같은가"**를 보는 검사입니다. 이 구성에서는 봉투엔 `rojae.kr`, 도장엔 `gmail.com`이 찍힙니다. 도장 자체는 진짜라 통과는 하지만, 같은 사람이라는 증명은 되지 않습니다.
{: .prompt-tip }

그래서 `rojae.kr`에 `p=quarantine`이나 `p=reject` 같은 강한 DMARC 정책을 걸면, 제가 보낸 메일이 스팸함으로 격리되거나 거절됩니다. DMARC는 걸지 않거나, 걸더라도 리포트만 받는 `p=none`까지만 두세요.

```text
TXT  _dmarc  v=DMARC1; p=none; rua=mailto:dmarc@rojae.kr
```

`rua` 주소는 catch-all(`*`)이 있으면 그대로 받힙니다. `*`를 지웠다면 `dmarc` 별칭을 따로 만드세요.

SPF에 넣은 `include:_spf.google.com`도 같은 이유로 이 구성에서는 쓰이지 않습니다. Gmail SMTP로 보내는 메일의 반송 주소가 `gmail.com`이라 `rojae.kr`의 SPF를 거치지 않기 때문입니다. ImprovMX 권장값에 들어 있어 그대로 두었고, Workspace로 옮기면 그때 쓰입니다.

Outlook 같은 클라이언트에서는 보낸 사람 옆에 "via gmail.com"이나 "대리 발송"이 붙을 수 있습니다. 개인 연락용으로는 충분히 감수할 만했습니다.

ImprovMX 무료 플랜에는 도메인 수, 별칭 수, 하루 전달량, 첨부 크기 제한이 있습니다. 정확한 수치는 요금제 페이지를 확인해 주세요. 개인 연락용으로 쓰기에는 부족하지 않았습니다.

## 넣은 레코드와, 이 구성이 맞는 조건

결국 DNS 레코드 세 줄과 설정 화면 두 개(ImprovMX 도메인 등록, Gmail "다른 주소에서 메일 보내기")가 전부였습니다. 이번에 넣은 레코드는 이렇습니다.

| 레코드 (호스트) | 값 | 의미 |
|---|---|---|
| MX `@` | `mx1.improvmx.com.` (10) | 1순위 수신 서버 |
| MX `@` | `mx2.improvmx.com.` (20) | 2순위 수신 서버 |
| TXT `@` | `v=spf1 include:spf.improvmx.com include:_spf.google.com ~all` | 보내도 되는 서버 명단, 나머지는 softfail |
| TXT (선택) `_dmarc` | `v=DMARC1; p=none; rua=mailto:dmarc@rojae.kr` | 정책 없이 리포트만 받기 |

시간을 잡아먹은 건 기술이 아니라 엉뚱한 곳이었습니다. 연결한 기억도 없는 MX가 남아 있었고(1단계), 숨은 확인창 때문에 화면이 멈춘 줄 알았고(함정 1), Gmail이 채워 둔 SMTP 칸을 그대로 넘길 뻔했습니다(함정 2).

이 구성은 개인 연락용 주소를 돈 들이지 않고 Gmail 하나에서 주고받으려 할 때 맞습니다. DMARC를 `p=none`까지만 걸어도 되는 주소라면 충분합니다.

보낸 사람 옆의 "via gmail.com"이 신경 쓰이기 시작하거나 강한 DMARC 정책이 필요해지면, 그때가 Workspace나 Zoho, Fastmail 같은 정식 메일 호스팅으로 옮길 때입니다. 도메인 이름으로 직접 DKIM 서명을 해 주는 곳이어야 From·Return-Path·DKIM 서명 도메인 셋이 모두 맞습니다. SPF에 미리 넣어 둔 `include:_spf.google.com`은 그중 Workspace로 옮길 때만 쓰입니다.

## Reference Links

- [ImprovMX](https://improvmx.com)
- [Gmail 고객센터: 다른 주소에서 메일 보내기](https://support.google.com/mail/answer/22370)
- [Google 계정 고객센터: 앱 비밀번호로 로그인](https://support.google.com/accounts/answer/185833)
- [Gmail preparing to drop POP3 mail fetching (The Register)](https://www.theregister.com/2026/01/05/gmail_dropping_pop3/)
