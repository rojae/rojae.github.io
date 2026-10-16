---
title: "해외에서는 어떻게 본인인증을 할까요?"
author: rojae
date: 2026-09-30 00:00:00 +0900
published: false
categories: [backend]
tags: [authentication, identity-verification, digital-identity, sna, java]
image:
  path: /assets/img/posts/2026-09-30-silent-network-authentication-trust-boundaries/cover.svg
  alt: 해외 서비스의 인증 — 연락처 확인, 신원 확인, 계정 로그인
description: "국내의 문자·이메일 인증, PASS·은행·간편인증과 비교하면 해외는 어떻게 인증할까요? 미국 Login.gov, 스웨덴 BankID, 싱가포르 Singpass와 SNA를 목적별로 살펴봅니다."
---

> 수단의 이름보다 **그 수단으로 무엇을 확인했는가**를 기준으로 해외 세 서비스와 SNA를 비교합니다. 국가 전체의 관행이 아니라 공식 문서로 확인한 사례이며, 마지막에 결과를 구분하는 Java 21 예제를 붙였습니다.
{: .prompt-info }
<!-- post-check: tone=polite -->

<style>
  .preview-img { aspect-ratio: auto; }
  .preview-img img { height: auto; aspect-ratio: auto; object-fit: contain; }
  /* This article uses two-column comparison tables. Keep both columns readable. */
  .content .table-wrapper > table { width: 100%; table-layout: fixed; }
  .content .table-wrapper > table th,
  .content .table-wrapper > table td {
    white-space: normal;
    word-break: keep-all;
    overflow-wrap: break-word;
    vertical-align: top;
    line-height: 1.65;
  }
  .content .table-wrapper > table th:first-child,
  .content .table-wrapper > table td:first-child { width: 32%; }
  @media (max-width: 575px) {
    .content .table-wrapper > table th,
    .content .table-wrapper > table td { padding: 0.65rem 0.6rem; }
  }
</style>

## 해외 서비스에는 PASS 버튼이 없는데요

국내 서비스에 가입할 때는 문자 인증번호를 입력하거나 PASS 앱을 열곤 합니다. 은행 앱에서는 신분증을 촬영하고, 다른 서비스에서는 간편인증으로 로그인을 마치기도 합니다.

이 화면들을 떠올리면 질문이 생깁니다.

> 우리에게 익숙한 인증 수단이 없는 해외에서는, 이 사람이 본인인지 어떻게 확인할까요?

이메일만 확인하고 가입이 끝나는 흐름과, 신분증까지 제출하는 흐름은 왜 다를까요? 해외에도 PASS처럼 여러 서비스에서 쓸 수 있는 수단이 있을까요? 인증번호를 입력하지 않는 SNA는 어디에 들어갈까요?

이 질문에 답하려면 먼저 우리가 **“인증했다”라는 말로 묶고 있던 서로 다른 확인**을 나눠야 합니다.

## 연락처 점유 확인, 신원 확인, 계정 로그인은 질문이 다릅니다

일상적으로 문자·이메일 인증을 “소유인증”, 이름과 개인 정보를 대조하는 절차를 “본인인증”이라고 부릅니다. 이 글에서는 구분을 분명히 하기 위해 다음 세 표현을 사용하겠습니다.

| 구분 | 서비스가 묻는 질문 |
|---|---|
| **연락처 점유 확인** | 지금 이 번호나 이메일에 접근할 수 있나요? (보낸 코드를 받거나 회선을 확인) |
| **신원 확인** | 제시한 이름·생년월일 등의 신원이 실제 사람과 연결되나요? |
| **계정 로그인** | 이 계정에 연결한 인증 수단을 사용할 수 있나요? |

표지 그림의 “연락처 확인”은 연락처 점유 확인을 줄인 말입니다.

> **쉽게 말하면** 우편함을 열 수 있는지 확인하는 것, 신분증의 주인인지 확인하는 것, 회원 계정에 다시 들어오는 것은 다른 일입니다. 하나를 확인했다고 나머지도 저절로 확인되지는 않습니다.
{: .prompt-tip }

여기서 “점유”는 법적인 소유권을 뜻하지 않습니다. **현재 그 연락처에 접근할 수 있다는 의미**입니다. 휴대전화 번호를 다른 사람이 넘겨받을 수도 있고 이메일 계정을 여럿이 사용할 수도 있으므로, 이것만으로 실명이나 특정 개인을 확정하지는 않습니다.

미국 NIST의 디지털 신원 가이드도 신원 확인인 *identity proofing*과 계정 인증인 *authentication*을 별도로 다룹니다. “처음 누구인지 확인하는 일”과 “다시 왔을 때 계정에 접근하게 하는 일”을 구분하는 기준입니다. 미국 연방 가이드의 용어이며, 모든 해외 서비스에 같은 절차를 강제한다는 뜻은 아닙니다. [NIST SP 800-63-4](https://pages.nist.gov/800-63-4/sp800-63.html)

## 같은 문자 인증도 같은 일을 하지는 않습니다

세 가지를 나눴다고 화면의 수단마다 하나씩 짝지을 수 있는 것은 아닙니다. “문자는 소유인증이고 PASS는 본인인증”이라고만 나누면 놓치는 부분이 있습니다. **휴대폰 본인확인도 문자 인증번호 방식으로 진행할 수 있기 때문입니다.** KISA는 휴대폰 본인확인에 SMS 방식과 PASS 앱 방식을 함께 안내합니다. **본인확인기관이 수행하는 SMS 방식의 휴대폰 본인확인은, 서비스가 직접 보낸 SMS 코드를 검증하는 것과 다른 절차입니다.** [KISA 휴대폰 본인확인 안내](https://identity.kisa.or.kr/web/main/contents/M030-02)

| 화면에서 보이는 수단 | 실제로 확인하는 내용 |
|---|---|
| 서비스가 직접 보낸 SMS·이메일 코드 | 그 연락처로 보낸 코드에 접근할 수 있는지 |
| 휴대폰 본인확인의 SMS·PASS 앱 | 본인확인기관의 절차에 따라 신원 정보를 확인하는지 |
| 은행 앱의 인증 | 계정 로그인, 계좌 확인, 비대면 신원 확인 등 해당 절차의 목적 |
| 인증서를 이용한 간편인증 | 해당 인증서로 로그인하거나 전자서명하는지 |

예를 들어 PASS 앱에는 휴대폰 본인확인 기능이 있고, PASS 인증서를 이용하는 기능도 있습니다. 같은 앱 안에 있다고 두 절차의 결과가 같은 것은 아닙니다. [PASS 인증서 약관](https://www.passauth.co.kr/tos)

은행 이름이 붙은 인증이나 간편인증도 마찬가지입니다. 버튼의 이름만으로 확인 수준을 정하지 않고, **발급 때 무엇을 확인했고 이번 응답으로 무엇을 보장하는지**를 봐야 합니다. 해외 사례도 이 질문으로 보면 차이가 드러납니다. 특히 신원 확인이 **어느 시점에, 어떤 방식으로** 일어나는지가 서비스마다 다릅니다.

## 미국 사례: 로그인한 뒤 신원을 더 확인합니다

미국 정부의 **Login.gov**를 보겠습니다. 계정을 만들 때는 이메일, 비밀번호, 추가 인증 수단을 설정합니다. 그 계정을 이용하는 기관에 따라 별도의 신원 확인을 요구할 수 있습니다. **계정 생성과 신원 확인이 같은 절차는 아닙니다.** [계정 생성 안내](https://www.login.gov/help/create-account/overview/), [신원 확인 안내](https://www.login.gov/help/verify-your-identity/overview/)

신원 확인 과정에서는 신분증과 개인 정보를 확인하며, 경우에 따라 셀피도 요청합니다. 서비스에 로그인할 수 있다는 사실에 더해, 그 서비스가 요구하는 신원 증거를 받는 흐름입니다.

민간 서비스가 활용할 수 있는 예로는 **Stripe Identity**가 있습니다. 신분증 검사를 구성하고, 필요하면 신분증 사진과 셀피를 비교하도록 요청할 수 있습니다. 서비스가 외부 검증 제품을 연동하는 방식입니다. [Stripe Identity API](https://docs.stripe.com/api/identity/verification_sessions/create)

신분증과 셀피 비교는 제출된 문서의 사진과 신청자가 맞는지 대조하는 과정입니다. 이메일을 읽을 수 있는지 묻는 절차보다 확인하려는 대상이 넓습니다.

다만 “미국은 가입할 때 모두 신분증을 낸다”는 뜻은 아닙니다. Login.gov는 특정 공공 서비스의 사례이고, Stripe Identity는 서비스가 선택해 연동하는 제품입니다. 필요한 신원 정보와 검증 절차는 서비스마다 다릅니다.

Login.gov에서는 계정이 먼저 있고 신원 확인이 뒤에 붙습니다. 반대로 신원 확인을 먼저 마친 수단을 여러 서비스가 함께 쓰는 구조도 있습니다.

## 스웨덴 사례: 은행이 발급한 디지털 ID를 활용합니다

**BankID**는 은행이 발급하는 디지털 신원 수단입니다. 은행·공공기관·민간 서비스에서 신원확인이나 전자서명에 사용할 수 있습니다. [BankID 이용약관](https://www.bankid.com/en/legal/terms-and-conditions/terms-of-use-bankid-mobile-application)

발급 은행인 Swedbank는 처음 Mobile BankID를 만들 때 여권·국가 신분증 또는 은행의 보안기기로 본인을 확인하는 경로를 안내합니다. 발급 절차를 거친 수단을 이후 다른 서비스에서 활용하는 구조입니다. [Swedbank 발급 안내](https://www.swedbank.se/privat/digitala-tjanster/mobilt-bankid/skaffa-bankid-i-telefonen-for-forsta-gangen.html)

> **쉽게 말하면** 신원을 확인한 뒤 발급받은 전자 신분증을 다른 창구에서도 사용하는 방식입니다. 매 서비스에서 처음부터 같은 신분증 사진을 받는 흐름과는 다릅니다.
{: .prompt-tip }

서비스에서 BankID 인증을 시작하면 사용자가 앱에서 확인하고, 서비스는 결과를 받습니다. 국내의 앱 기반 인증과 비슷하게 느껴질 수 있지만, 발급 조건과 전달되는 정보는 해당 서비스의 계약을 확인해야 합니다. [BankID 인증 흐름](https://www.bankid.com/en/business/about-the-service/identification)

여기서 볼 점은 **앱에 PIN을 입력한다는 동작보다, 그 앱의 인증 수단이 어떤 신원 확인을 거쳐 발급됐는가**입니다. PIN이나 생체 확인은 이미 발급된 수단을 사용할 때의 단계입니다.

## 싱가포르 사례: 로그인과 정보 제공도 나눕니다

신원을 확인하는 시점뿐 아니라, 확인된 정보를 서비스로 넘기는 기능을 로그인과 분리한 사례도 있습니다. **Singpass**는 싱가포르의 디지털 신원 체계입니다. 개발자 문서는 Login, Myinfo, Sign을 구분해 제공합니다. [Singpass 개발자 포털](https://developer.singpass.gov.sg/)

| 기능 | 서비스에서 하는 일 |
|---|---|
| **Login** | Singpass로 서비스에 로그인(요청 범위에 따라 NRIC(외국인은 FIN 등)·이름 포함) |
| **Myinfo** | 사용자가 동의한 개인 정보를 받아 신청서 등에 활용 |
| **Sign** | 문서에 전자서명 |

예를 들어 신청서를 작성하는 서비스라면, 로그인한 뒤 Myinfo로 필요한 정보 제공에 동의하는 흐름을 구성할 수 있습니다. 사용자가 이름과 주소를 직접 입력하는 대신 확인된 출처의 정보를 전달받는 방식입니다. Login은 계정 로그인 기능이며, 요청 범위에 따라 확인된 식별자(NRIC(외국인은 FIN 등)·이름)를 함께 받을 수 있습니다(2026-10-17 문서 확인). [Singpass ID 토큰 해석 문서](https://docs.developer.singpass.gov.sg/docs/technical-specifications/integration-guide/4.-parsing-the-id-token) Myinfo는 주소 등 더 넓은 확인된 정보를 동의를 받아 넘겨받는 기능입니다.

국내 간편인증과 화면이 닮았더라도, 로그인·신원 정보 제공·전자서명이 어떤 기능으로 나뉘는지를 보면 연동할 대상을 더 정확히 고를 수 있습니다.

## 세 사례를 나란히 놓으면

세 사례를 먼저 일어나는 일에서 나중 일어나는 일 순으로 놓고, 신원을 확인하는 지점과 확인된 정보를 받는 지점이 어디에 있는지 비교해 보겠습니다.

<figure class="post-figure post-figure--diagram" id="figure-cases" aria-labelledby="cases-caption">
  <div class="figure-head"><small>01 · 세 사례</small>신원 확인이 일어나는 곳과 서비스가 받는 사실이 다릅니다</div>
  <picture class="diagram-wide"><img data-preserve-picture="true" src="/assets/img/posts/2026-09-30-silent-network-authentication-trust-boundaries/cases-desktop.svg" alt="Login.gov는 계정 생성 뒤 이용 기관이 요구하면 신원을 확인하고 요구하지 않으면 바로 이용하며, BankID는 은행이 발급할 때 신원을 확인한 뒤 여러 서비스에서 재사용하고, Singpass는 요청 범위에 따라 식별자를 함께 줄 수 있는 Login(테두리만 있는 사각형)과 별도로, Myinfo로 확인된 정보 중 동의한 것만 서비스에 제공합니다." width="700" height="762" loading="lazy"></picture>
  <picture class="diagram-narrow"><img data-preserve-picture="true" src="/assets/img/posts/2026-09-30-silent-network-authentication-trust-boundaries/cases-mobile.svg" alt="Login.gov는 계정 생성 뒤 이용 기관이 요구하면 신원을 확인하고 요구하지 않으면 바로 이용하며, BankID는 은행이 발급할 때 신원을 확인한 뒤 여러 서비스에서 재사용하고, Singpass는 요청 범위에 따라 식별자를 함께 줄 수 있는 Login(테두리만 있는 사각형)과 별도로, Myinfo로 확인된 정보 중 동의한 것만 서비스에 제공합니다." width="320" height="1503" loading="lazy"></picture>
  <figcaption id="cases-caption">줄마다 마름모(신원 확인)와 사각형(확인된 정보 수신, 테두리만 있으면 요청 범위에 따라)이 놓인 위치를 비교해 보세요. 공식 문서의 흐름을 설명용 순서로 옮긴 것으로, Singpass 줄의 Login → Myinfo는 구성 예이고 Sign과 Singpass 계정 발급 때의 신원 확인은 다루지 않았습니다(BankID 발급은 Swedbank 안내 기준). <a class="diagram-source diagram-wide" href="/assets/img/posts/2026-09-30-silent-network-authentication-trust-boundaries/cases-desktop.svg" target="_blank" rel="noopener">그림 원본 보기 ↗</a><a class="diagram-source diagram-narrow" href="/assets/img/posts/2026-09-30-silent-network-authentication-trust-boundaries/cases-mobile.svg" target="_blank" rel="noopener">그림 원본 보기 ↗</a></figcaption>
</figure>

서비스를 설계하는 쪽에서 보면, 먼저 정할 것은 **필요한 신원 사실을 직접 확인할지, 이미 확인된 수단이나 정보를 받아 쓸지**입니다. 그 선택에 따라 연동할 기능(로그인, 정보 제공, 별도 신원 확인)과 서버가 결과로 기록할 사실이 달라집니다.

**해외에도 신원을 확인하는 절차와 여러 서비스에서 쓰는 디지털 ID가 있습니다.** 다만 국가별 기반과 서비스의 요구가 달라, 한국의 인증 버튼 하나와 일대일로 대응하지는 않습니다.

그렇다면 패스키나 소셜 로그인은 어디에 들어갈까요? 우선 **계정에 접근하는 수단**으로 봐야 합니다. 패스키로 로그인했다고 실명 확인까지 새로 수행한 것은 아닙니다. 신원 확인을 마친 계정에 패스키를 등록하고, 다음부터 그 키로 로그인하는 구성은 가능합니다. [FIDO Alliance 설명](https://fidoalliance.org/passkeys-and-verifiable-digital-credentials-a-harmonized-path-to-secure-digital-identity/) 이메일만 확인하는 가입 흐름도 마찬가지로, 그 단계에서 확인한 것은 이메일 접근 가능 여부이고 추가 신원 확인을 어떤 작업에서 요구할지는 별도 정책입니다.

## 그렇다면 SNA는 무엇을 바꿀까요

남은 질문은 인증번호를 입력하지 않는 SNA입니다. **SNA(Silent Network Authentication)**는 통신사 측의 회선 또는 SIM 기반 확인을 이용하는 전화번호 검증 방식입니다. 인증번호를 사용자가 읽고 입력하는 단계를 줄일 수 있습니다. SMS는 받은 코드를 사용자가 되돌려 주는 방식이고, SNA는 통신사 측이 회선 자체를 확인하는 방식입니다. [Twilio SNA 개요](https://www.twilio.com/docs/verify/sna)

Twilio의 네트워크 기반 방식에서는 휴대전화가 이동통신 경로로 인증 URL을 호출하고, 서비스 서버가 공급자에게 최종 결과를 확인합니다. 앱의 호출 완료만으로 번호가 일치했다고 판단하지는 않습니다. [Twilio 기술 개요](https://www.twilio.com/docs/verify/sna/tech-overview), [결과 확인 안내](https://www.twilio.com/docs/verify/best-practices-for-verify-sna-error-handling)

**SNA는 전화번호를 확인하는 경로를 바꿉니다.** 세 가지 확인 중에서는 여전히 연락처 점유 확인에 놓입니다. 그 결과만으로 이름·생년월일까지 확인했다고 보거나, 국내의 휴대폰 본인확인 계약을 그대로 대체한다고 가정하면 안 됩니다. 지원 통신사와 단말·연결 조건도 공급자별로 확인해야 합니다.

## Java에서는 인증 성공을 어떻게 표현할까요

서버에서도 이 구분이 필요합니다. 아래처럼 성공 여부 하나만 남기면 SMS 확인 성공이 신원 확인이 필요한 작업까지 허용하는 근거로 쓰일 수 있습니다.

### 적용 전: 무엇을 확인했는지 남지 않습니다

```java
static boolean allowBefore(boolean verified) {
    return verified;
}
```

- 이메일을 확인한 것인지 신원을 확인한 것인지 알 수 없습니다.
- 어느 사용자와 어떤 정책에 대한 결과인지 구분하기 어렵습니다.

### 적용 후: 확인한 사실과 필요한 조건을 맞춥니다

개념 설명만 읽으셔도 됩니다. 아래는 구현할 때 참고할 **Java 21 예제**이며, 외부 라이브러리는 쓰지 않습니다. 공급자의 실제 응답을 검증한 뒤 서버가 만든 결과를 `Evidence`로 표현합니다.

```java
enum Fact {
    PHONE_CONTROL,
    EMAIL_CONTROL,
    IDENTITY_CHECKED,
    ACCOUNT_AUTHENTICATED
}

record Evidence(
    String subjectId,
    Fact fact,
    String policyId,
    Instant expiresAt
) {}
```

`fact`는 확인한 사실, `policyId`는 **서비스가 정의한 검증 정책의 식별자**입니다. 아래의 `identity-v1`은 국가 공통 등급이나 법적 보증이 아닙니다. 어떤 제공자의 어떤 확인 결과를 받아들일지는 서비스가 별도로 정해야 합니다.

예제는 작업마다 요구하는 사실과 정책을 하나씩 정해 둡니다. 괄호 안은 실행 결과에 나오는 작업 이름입니다.

| 작업 | 요구하는 사실 · 정책 |
|---|---|
| 전화번호 확인 (`phone`) | `PHONE_CONTROL` · `phone-v1` |
| 신원 확인이 필요한 가입 (`identity onboarding`) | `IDENTITY_CHECKED` · `identity-v1` |
| 계정 로그인 (`sign-in`) | `ACCOUNT_AUTHENTICATED` · `login-v1` |

서버는 결과의 사실·정책을 이 요구와 대조하고, 요청 주체와 유효기간도 함께 확인합니다.

```java
static boolean allow(Action action,
        String sub, Evidence e,
        Instant now) {
    Requirement r =
        REQUIREMENTS.get(action);
    return r != null
        && e != null
        && sub.equals(e.subjectId())
        && now.isBefore(e.expiresAt())
        && e.fact() == r.fact()
        && r.policyId()
            .equals(e.policyId());
}
```

단순 SMS·SNA 결과를 신원 확인 성공으로 바꾸지 않는 것이 핵심입니다.

### 직접 실행하면 이렇게 구분됩니다

[전체 Java 예제 다운로드](/assets/code/identity-verification/IdentityPolicyDemo.java) 후 저장한 폴더에서 실행합니다. 위 코드들은 전체 파일의 일부이며 필요한 import와 작업별 정책은 다운로드 파일에 있습니다.

```bash
java --version
java IdentityPolicyDemo.java
```

Java 21.0.8에서 실행한 주요 결과입니다.

```text
SMS -> phone: ALLOW
SMS -> identity onboarding: DENY
SNA -> identity onboarding: DENY
Identity -> identity onboarding: ALLOW
Passkey -> sign-in: ALLOW
Passkey -> identity onboarding: DENY
```

전체 실행에서는 다른 사용자, 만료된 결과, 정책 불일치, 결과 누락까지 확인하고 `12 checks passed`를 출력합니다. 단순 SMS는 연락처 확인에 성공해도 신원 확인이 필요한 가입 단계에서는 거절됩니다. 예제에서 SNA 결과는 SMS와 같은 `PHONE_CONTROL`·`phone-v1`로 기록되므로 같은 이유로 거절됩니다. 패스키도 로그인에는 사용하지만 그것만으로 신원 확인을 새로 통과시키지는 않습니다.

이 예제는 **결과를 분류하고 작업 조건과 대조하는 방법**만 검증합니다. 실제 연동에는 공급자 응답의 진위·발급자·대상·요청 결합 확인, 재사용 방지, 계정 연결과 복구 정책이 더 필요합니다. 클라이언트가 보낸 `fact`나 `policyId`를 그대로 믿어서는 안 됩니다.

## 언제 쓰고, 언제 다른 확인을 더해야 할까요

| 이 정도의 확인을 검토할 때 | 이것만으로 충분하다고 보면 안 될 때 |
|---|---|
| 알림을 받을 이메일·번호 확인 | 법적 신원이나 과거 계정의 주인인지 판단 |
| 패스키 등으로 기존 계정 로그인 | 처음 제시한 이름·신분증의 진위 확인 |
| 신분증 검증이나 디지털 ID 활용 | 그 결과가 해당 업무의 모든 요건을 충족한다고 판단 |

처음 질문은 “해외에서는 PASS 대신 무엇을 쓸까?”였습니다. 세 사례에서 달랐던 것은 수단의 이름이 아니라, 신원 확인이 일어나는 시점과 서비스로 넘어오는 사실이었습니다.

그래서 해외 인증 수단의 연동을 검토할 때는 두 가지를 기준으로 삼습니다.

- 수단의 이름보다 **그 수단으로 확인한 사실**을 먼저 적습니다.
- 서버에서는 **로그인 성공과 신원 확인 결과를 다른 값으로 구분**합니다.

이 기준은 작업마다 요구하는 사실이 다를 때 의미가 있으며, 연락처 접근만 필요한 서비스라면 표 첫 행의 연락처 확인에서 시작해 신원이 필요한 작업에만 추가 확인을 요구할 수 있습니다. 화면에서도 “이메일 주소 확인”, “계정 로그인”, “이 작업에 필요한 신원 확인”처럼 목적을 알려 주고, 실패했을 때 쓸 수 있는 대체 경로를 제공해야 합니다.

## 참고한 내용들

- 문서 확인일: 2026년 9월 30일(Singpass ID 토큰 문서는 2026년 10월 17일). 공식 문서로 확인한 서비스 사례이며, 국가별 도입률이나 모든 서비스의 관행을 조사하지 않았고 실제 인증기관 연동도 수행하지 않았습니다.
- 실행 환경: Java 21.0.8에서 예제의 검사 12개 통과(`12 checks passed`).

### Reference Links

- [KISA — 휴대폰 본인확인](https://identity.kisa.or.kr/web/main/contents/M030-02)
- [PASS — 인증서 약관](https://www.passauth.co.kr/tos)
- [NIST — Digital Identity Guidelines, SP 800-63-4](https://pages.nist.gov/800-63-4/sp800-63.html) (2025년 최종본)
- [Login.gov — 계정 생성](https://www.login.gov/help/create-account/overview/), [신원 확인](https://www.login.gov/help/verify-your-identity/overview/)
- [Stripe — Identity VerificationSession API](https://docs.stripe.com/api/identity/verification_sessions/create)
- [BankID — 이용약관](https://www.bankid.com/en/legal/terms-and-conditions/terms-of-use-bankid-mobile-application), [인증 흐름](https://www.bankid.com/en/business/about-the-service/identification)
- [Swedbank — Mobile BankID 첫 발급 안내](https://www.swedbank.se/privat/digitala-tjanster/mobilt-bankid/skaffa-bankid-i-telefonen-for-forsta-gangen.html)
- [Singpass — 개발자 포털](https://developer.singpass.gov.sg/), [ID 토큰 해석](https://docs.developer.singpass.gov.sg/docs/technical-specifications/integration-guide/4.-parsing-the-id-token) (2026-10-17 조회)
- [FIDO Alliance — Passkeys and Verifiable Digital Credentials](https://fidoalliance.org/passkeys-and-verifiable-digital-credentials-a-harmonized-path-to-secure-digital-identity/)
- [Twilio — SNA 기술 개요](https://www.twilio.com/docs/verify/sna/tech-overview), [결과 확인 안내](https://www.twilio.com/docs/verify/best-practices-for-verify-sna-error-handling)
