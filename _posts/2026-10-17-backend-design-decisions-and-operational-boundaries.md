---
title: 실패한 요청 뒤에 무엇을 남길 것인가
description: 인증·제휴·배치·전자문서를 운영하며 정한 완료, 원자성, 복구의 경계
author: rojae
date: 2026-10-17 00:15:00 +0900
published: true
categories: [backend]
tags: [spring, redis, transaction, integration, operations]
editorial: true
image:
  path: /assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/boundaries.png
  alt: 인증 완료와 동의 항목별 트랜잭션의 경계
  hidden: true
---
<!-- post-check: tone=polite -->

<div class="design-story" markdown="1">

<div class="story-opening">
  <p class="story-kicker">ENGINEERING DECISIONS · 실무 설계 회고</p>
  <p class="story-thesis">실패를 지우는 것보다 먼저,<br> <strong>이미 끝난 일과 아직 남은 일을 나눴습니다.</strong></p>
  <nav class="story-route" aria-label="글의 네 가지 질문">
    <a href="#completion"><span>01</span> 완료</a><a href="#consistency"><span>02</span> 일관성</a><a href="#recovery"><span>03</span> 복구</a><a href="#operations"><span>04</span> 운영</a>
  </nav>
</div>

인증은 성공했는데, 뒤따른 동의 항목 하나가 실패했습니다. 이 요청의 결과를 어떻게 남겨야 할까요?

제휴 연동을 설계하며 고민한 문제입니다. 전체를 실패로만 기록하면 이미 끝난 인증과 동의를 구분하기 어렵고, 성공으로만 표시하면 처리하지 못한 항목을 놓칩니다. 외부 금융사까지 포함된 흐름에서는 우리 DB를 롤백해도 외부에서 끝난 일까지 되돌릴 수 없습니다.

이 문제를 풀려면 **완료된 결과를 어디까지 보존할지**부터 정해야 했습니다. 이후에는 그 상태를 여러 요청이 어떻게 갱신할지, 실패한 작업을 언제 다시 시도할지, 운영자는 어떤 기록을 보고 판단할지가 이어졌습니다. 제휴·통합인증·배치·전자문서에서 했던 선택을 이 네 가지 질문으로 묶었습니다.

## 01. 완료된 결과를 보존할 경계 정하기
{: #completion }

### 인증과 동의를 각각 확정했습니다

제휴 연동에서는 인증 이후 여러 동의 항목을 처리했습니다. 모두 하나의 트랜잭션에 묶으면 한 항목의 실패로 앞서 처리한 DB 변경까지 롤백될 수 있습니다. 하지만 인증 완료와 동의 항목별 완료는 따로 보존해야 하는 업무 결과였습니다.

그래서 인증 트랜잭션을 먼저 커밋하고, `AFTER_COMMIT` 이벤트에서 동의 처리를 시작했습니다. 각 항목에는 `REQUIRES_NEW`를 적용해 독립된 트랜잭션을 열었습니다. 동의 A는 성공하고 B는 실패한 상황을 예로 들면, 아래처럼 완료된 결과를 남길 수 있습니다.

<figure class="story-figure diagram-frame" id="figure-completion" aria-labelledby="completion-caption">
  <div class="figure-topline"><span>01 · 트랜잭션</span><strong>B가 실패해도, 앞선 커밋은 유지됩니다</strong></div>
  <picture class="diagram-wide"><img data-preserve-picture="true" src="/assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/completion-desktop.svg" alt="인증 커밋 이후 각 동의를 독립된 트랜잭션으로 처리합니다. 동의 A 성공·B 실패의 예에서 인증과 A의 커밋은 유지됩니다." width="700" height="420" loading="lazy"></picture>
  <picture class="diagram-narrow"><img data-preserve-picture="true" src="/assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/completion-mobile.svg" alt="인증 커밋 이후 각 동의를 독립된 트랜잭션으로 처리합니다. 동의 A 성공·B 실패의 예에서 인증과 A의 커밋은 유지됩니다." width="320" height="548" loading="lazy"></picture>
  <figcaption id="completion-caption">A → B 순서와 시간 간격은 설명용입니다. 실제 실행 순서나 병렬 실행 여부를 나타내지 않습니다.<a class="diagram-source diagram-wide" href="/assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/completion-desktop.svg" target="_blank" rel="noopener">그림 원본 보기 ↗</a><a class="diagram-source diagram-narrow" href="/assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/completion-mobile.svg" target="_blank" rel="noopener">그림 원본 보기 ↗</a></figcaption>
</figure>

인증과 A의 완료 기록을 보존하면, 운영자는 B의 실패 이력을 함께 보고 남은 처리를 판단할 수 있습니다. **부분 성공을 허용한 만큼, 항목별 결과와 이력을 함께 남겨야 했습니다.**

트랜잭션을 나눈 뒤에도 항목별 예외 처리와 결과 기록은 애플리케이션에서 구현해야 합니다. `REQUIRES_NEW`가 정하는 것은 독립적인 커밋·롤백의 경계입니다. 한 항목이 예외를 던진 뒤 다음 항목을 실행할지까지 전파 옵션이 결정해 주지는 않습니다. [Spring의 트랜잭션 전파 설명](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-propagation.html#tx-propagation-requires_new)

또한 인증 커밋 직후 프로세스가 종료된다면 동의 처리 자체가 시작되지 못할 수 있습니다. `AFTER_COMMIT`은 실행 시점을 정하는 기능이므로, 이 경우의 후속 작업 전달까지 보장하려면 별도의 내구성 설계가 필요합니다. 완료 결과를 보존하는 문제와 후속 처리를 반드시 실행하는 문제는 여기서 나뉩니다. [Spring의 트랜잭션 연계 이벤트 설명](https://docs.spring.io/spring-framework/reference/data-access/transaction/event.html)

### 외부 호출에서는 우리가 확인할 수 있는 상태도 나눴습니다

우리 DB의 완료 상태를 구분해도 외부 금융사에서 어디까지 처리했는지는 별도의 문제로 남았습니다. 여기에 브라우저의 중복 진입까지 겹칠 수 있어, **제휴 시작부터 인증 이후 동의까지**의 흐름에 요청 식별자를 사용했습니다.

브라우저에서 UUID를 만들고 Redis에 해당 키가 없을 때만 저장한 뒤 외부 연동으로 넘어갔습니다. 외부 호출이 실패해도 키는 유지하고, MongoDB에 오류를 기록했습니다. 브라우저에서는 우리 쪽 인증 상태를 조회하고 재시도 안내를 받을 수 있도록 했습니다. 쿠폰 발급은 이 경로와 별도의 백엔드 작업이었습니다.

각 기록의 역할은 달랐습니다. Redis 키는 요청의 진입을 제어하고, 인증 상태는 우리 쪽 진행 결과를, 오류 이력은 실패 지점을 설명했습니다. 이들을 한 값으로 합치면 “진입한 요청”과 “완료된 요청”을 구분하기 어렵습니다.

외부 금융사는 상태 조회 API를 제공하지 않았기 때문에, 외부 결과를 직접 대조하는 데에는 한계가 있었습니다. 재시도에서도 금융사 쪽의 중복 처리에 의존했습니다. **우리 쪽 중복 진입 제어만으로 외부 처리까지 정확히 한 번 보장했다고 말할 수 없는 이유입니다.**

## 02. 동시 요청이 바꾸는 상태 보호하기
{: #consistency }

### 장애 횟수를 함께 집계하고, 변경된 상태를 전파했습니다

완료와 실패를 구분해 기록하더라도, 여러 서버가 그 값을 동시에 바꾸면 갱신 과정도 살펴야 합니다. 통합인증의 장애 집계에서는 원자적으로 갱신할 값과 서버마다 전달할 상태를 나눴습니다.

2024년 통합인증 프로젝트에서 저는 **3인 팀의 기술 설계를 주도하고, 세 사이트·다섯 인증 유형의 인증 기능을 전체 구현**했습니다. 인증사 오류가 누적되면 해당 인증사를 자동 비활성화하고, 휴대폰 본인확인은 대체 인증사로 요청 비율을 조정했습니다.

이 판단에 쓸 장애 횟수를 각 서버의 메모리에만 쌓으면 전체 상황을 같은 기준으로 보기 어렵습니다. Redis에 집계를 모으고, 장애 횟수 갱신 로직을 Lua 스크립트로 묶어 실행 도중 다른 요청이 끼어들지 않도록 했습니다.

집계가 정확해도 각 서버가 계속 예전 인증사 상태를 읽으면 요청을 보내는 판단은 달라질 수 있습니다. 그래서 상태 변경은 Redis Pub/Sub으로 알리고, 각 서버에서는 Caffeine 로컬 캐시로 조회했습니다. 알림 누락에 대비해 RDB 원본을 주기적으로 읽고 캐시를 다시 맞추는 경로도 뒀습니다.

<figure class="story-figure diagram-frame" id="figure-state" aria-labelledby="state-caption">
  <div class="figure-topline"><span>02 · 상태 전달</span><strong>갱신의 원자성과 상태의 전파는 별개입니다</strong></div>
  <picture class="diagram-wide"><img data-preserve-picture="true" src="/assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/state-desktop.svg" alt="장애 집계는 Redis Lua에서 원자적으로 갱신합니다. 상태 변경은 Pub/Sub으로 알리고 각 서버의 Caffeine 캐시에서 조회하며, RDB 원본의 주기 조회로 알림 누락을 보완합니다." width="700" height="500" loading="lazy"></picture>
  <picture class="diagram-narrow"><img data-preserve-picture="true" src="/assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/state-mobile.svg" alt="장애 집계는 Redis Lua에서 원자적으로 갱신합니다. 상태 변경은 Pub/Sub으로 알리고 각 서버의 Caffeine 캐시에서 조회하며, RDB 원본의 주기 조회로 알림 누락을 보완합니다." width="300" height="744" loading="lazy"></picture>
  <figcaption id="state-caption">위쪽은 장애 횟수 갱신, 아래쪽은 상태 전파·조회 경로입니다. 알림까지 하나의 Lua 실행에 포함된다는 뜻은 아닙니다.<a class="diagram-source diagram-wide" href="/assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/state-desktop.svg" target="_blank" rel="noopener">그림 원본 보기 ↗</a><a class="diagram-source diagram-narrow" href="/assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/state-mobile.svg" target="_blank" rel="noopener">그림 원본 보기 ↗</a></figcaption>
</figure>

갱신을 보호할 방법은 실제로 수행하는 연산에 따라 달라집니다. 단순히 카운터를 증가시키는 작업에는 `INCR` 자체도 원자적입니다. Lua가 필요한지는 **여러 연산을 하나의 실행 범위로 묶어야 하는지**를 보고 판단해야 합니다. [Redis의 Lua 실행 설명](https://redis.io/docs/latest/develop/programmability/eval-intro/), [INCR 명령](https://redis.io/docs/latest/commands/incr/)

스크립트 호출에는 `EVALSHA`를 사용했습니다. 스크립트 본문은 SHA로 참조하고 매번 달라지는 값만 인자로 넘겨, 같은 본문의 반복 전송을 줄였습니다. 캐시되는 것은 스크립트이며, 호출마다 갱신 로직은 실행됩니다.

당시 상태 변경 작업의 규모에서는 Kafka를 추가 운영할 필요가 크지 않다고 판단해 Pub/Sub과 주기 조회를 조합했습니다. 대신 **알림을 놓친 서버는 재동기화 전까지 오래된 상태를 사용할 수 있습니다.** 운영 구성을 단순하게 유지하면서 감수한 비용입니다. [Redis Pub/Sub 전달 보장](https://redis.io/docs/latest/develop/pubsub/#delivery-semantics)

### 배치에서는 기준 행의 생성과 누적 갱신을 나눴습니다

배치에서는 같은 질문을 RDB의 업무 행에 적용했습니다. 일배치의 첫 데이터 묶음들이 동시에 도착하면서, 진행 상태와 누적 결과를 관리할 배치 마스터를 함께 만들려 했습니다. 마스터가 만들어진 뒤에도 중복 확인과 누적 계산 사이에 다른 요청이 끼어들 수 있었습니다.

| 충돌하는 작업 | 보호할 조건 | 선택 |
|---|---|---|
| 아직 없는 마스터 생성 | 같은 배치의 기준 행은 하나 | 별도 트랜잭션 + 유니크 제약, 충돌 시 기존 행 재조회 |
| 이미 있는 마스터 갱신 | 중복 확인과 누적 계산을 함께 수행 | 같은 업무 행의 비관적 잠금 안에서 검사·갱신 |
{: tabindex="0" aria-label="배치 경합 처리 비교" }

생성 시 유니크 충돌이 주 트랜잭션에 영향을 주지 않도록, 마스터 생성만 `REQUIRES_NEW`로 분리했습니다. 먼저 생성한 쪽이 커밋하면 충돌한 쪽은 기존 행을 다시 조회했습니다. 이후 중복 확인과 누적 갱신은 같은 배치 행의 비관적 잠금 안에서 수행했습니다.

이렇게 하면 검사와 갱신 사이를 보호할 수 있지만, 같은 행을 바꾸려는 요청은 기다려야 합니다. 잠금 안의 작업이 길어질수록 같은 배치의 대기 시간도 길어지는 비용을 함께 봐야 했습니다.

갱신을 안전하게 처리하는 것만으로 배치의 완료 조건이 정해지지는 않았습니다. 설명용으로 1·2·3번 묶음을 기대할 때, 1번과 3번이 도착했다는 사실은 2번까지 처리됐다는 뜻이 아닙니다. 그래서 마지막 묶음 번호뿐 아니라 중간 누락과 실제 누적 건수를 함께 확인했습니다.

Redis의 장애 횟수에는 Lua를, RDB의 배치 누적에는 행 잠금을 사용했습니다. 선택을 가른 기준은 **어떤 저장소의 어떤 검사·갱신을 함께 보호해야 하는가**였습니다.

## 03. 실패 기록에서 다음 처리로 이어 가기
{: #recovery }

### TTL 만료를 재시도의 계기로 사용했습니다

실패 상태를 정확히 남겨도 작업이 저절로 다시 진행되지는 않습니다. 다음 시도의 조건이 필요합니다. 통합인증에서는 장애 인증사를 자동 비활성화하고, 로컬 장애 상태의 TTL을 **10분**으로 뒀습니다. TTL이 만료되면 비율을 보정하고 다시 시도하도록 구현했습니다.

10분은 로컬 상태의 유효 시간입니다. 그 시간이 지났다는 사실만으로 인증사가 정상화됐다고 판단할 수는 없습니다. 이 때문에 **정상화된 인증사를 원래 요청 비율로 자동 복귀시키는 기능**은 별도의 과제였습니다. 설계 리뷰와 검토까지 진행했지만, 안정적으로 운영하던 흐름을 바꾸는 데 보수적으로 접근하면서 구현으로 이어지지는 못했습니다.

<figure class="story-figure diagram-frame" id="figure-recovery" aria-labelledby="recovery-caption">
  <div class="figure-topline"><span>03 · 복구 전이</span><strong>재시도까지 구현했고, 자동 복귀는 남았습니다</strong></div>
  <picture class="diagram-wide"><img data-preserve-picture="true" src="/assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/recovery-desktop.svg" alt="장애 인증사 비활성화와 대체 비율 조정, 10분 TTL 만료 후 비율 보정·재시도는 구현했습니다. 정상화 확인 후 원래 비율로의 자동 복귀는 설계 검토 후 미구현입니다." width="700" height="475" loading="lazy"></picture>
  <picture class="diagram-narrow"><img data-preserve-picture="true" src="/assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/recovery-mobile.svg" alt="장애 인증사 비활성화와 대체 비율 조정, 10분 TTL 만료 후 비율 보정·재시도는 구현했습니다. 정상화 확인 후 원래 비율로의 자동 복귀는 설계 검토 후 미구현입니다." width="300" height="780" loading="lazy"></picture>
  <figcaption id="recovery-caption">실선은 구현한 경로, 점선은 설계 검토 후 구현하지 않은 경로입니다.<a class="diagram-source diagram-wide" href="/assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/recovery-desktop.svg" target="_blank" rel="noopener">그림 원본 보기 ↗</a><a class="diagram-source diagram-narrow" href="/assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/recovery-mobile.svg" target="_blank" rel="noopener">그림 원본 보기 ↗</a></figcaption>
</figure>

남은 과제는 원래 비율로 돌아갈 근거를 정하는 일입니다. 다시 설계한다면 정상화 판단에 쓸 신호와, 비율을 되돌린 뒤 실패가 늘었을 때의 대응을 함께 검토하겠습니다.

### 실패한 쿠폰 발급은 주기적으로 재처리했습니다

쿠폰·이벤트 혜택 발급에서는 **아직 발급하지 못한 작업을 다시 이어 가야 했습니다.** 브라우저 인증·동의와 별도로 백엔드에서 발급하고, 실패를 MongoDB에 남겨 주기적으로 재처리하는 경로를 실제 운영에 반영했습니다.

그 결과 최초 발급에 실패한 고객도 늦게나마 쿠폰을 받아 이벤트 혜택을 받을 수 있었습니다. 이 사례에서 실패 이력은 운영자가 읽는 기록이면서, 후속 작업이 다시 출발할 대상이기도 했습니다. 다만 주기적 재처리와 중복 발급 방지는 별개의 보장이므로, 이 경로만으로 정확히 한 번의 발급까지 보장했다고 보지는 않습니다.

제휴 업무에서 담당자가 처리할 범위도 구분했습니다. 어드민에서는 **동의 철회**를 제공했습니다. 새 동의 등록은 별도 금융사 페이지의 인증이 필요해 제공하지 않았고, 회원 탈회와 동의 철회도 분리했습니다. 후속 처리를 운영에 넣을 때에는 실패 여부뿐 아니라, 그 작업에 필요한 인증 절차와 처리 주체도 함께 봐야 했습니다.

## 04. 운영자가 다음 확인 지점을 찾을 수 있게 하기
{: #operations }

### 복제 상태와 접속 경로를 나누어 확인했습니다

사람이 판단을 이어받는 구간에서는 기록과 구성도를 보고 다음 확인 대상을 찾을 수 있어야 합니다. 전자문서 프로젝트에서는 DB 복제와 접속 경로를 구분하고, 각각의 상태를 확인할 운영 절차를 남겼습니다.

이 프로젝트는 두 명이 서버 22대의 인프라와 API·관리자·배치, KISA VPN 연동을 다뤘습니다. 저는 첫 심사 준비와 보완에 참여했으며, 2022년 7월 2차 적합 판정과 9월 가오픈을 경험했습니다.

Galera를 선택할 때에는 라이선스 비용도 고려했습니다. 다만 DB 사이의 복제가 정상이라는 사실만으로 애플리케이션의 접속 경로까지 정상이라고 판단할 수는 없습니다. 데이터 복제는 Galera가, 접속 경로의 가용성은 MaxScale과 Keepalived가 담당하도록 역할을 나눠 봤습니다.

<figure class="story-figure diagram-frame" id="figure-availability" aria-labelledby="availability-caption">
  <div class="figure-topline"><span>04 · 가용성</span><strong>접속 경로와 데이터 복제를 따로 봅니다</strong></div>
  <picture class="diagram-wide"><img data-preserve-picture="true" src="/assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/availability-desktop.svg" alt="MaxScale과 Keepalived는 DB 접속 경로의 가용성을, Galera는 DB 노드 사이의 데이터 복제를 담당합니다." width="700" height="510" loading="lazy"></picture>
  <picture class="diagram-narrow"><img data-preserve-picture="true" src="/assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/availability-mobile.svg" alt="MaxScale과 Keepalived는 DB 접속 경로의 가용성을, Galera는 DB 노드 사이의 데이터 복제를 담당합니다." width="320" height="550" loading="lazy"></picture>
  <figcaption id="availability-caption">DB 노드와 연결은 역할을 설명하기 위한 예시입니다. 실제 노드 수·네트워크 배치와 접속 계층의 내부 연결은 생략했습니다.<a class="diagram-source diagram-wide" href="/assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/availability-desktop.svg" target="_blank" rel="noopener">그림 원본 보기 ↗</a><a class="diagram-source diagram-narrow" href="/assets/img/posts/2026-10-17-backend-design-decisions-and-operational-boundaries/availability-mobile.svg" target="_blank" rel="noopener">그림 원본 보기 ↗</a></figcaption>
</figure>

구성도에는 각 요소의 관계를, 인계 문서에는 담당자가 수행할 확인과 조치를 남겼습니다. 노드 상태 확인, 재기동, 인증서 갱신, 순차 배포 절차를 정리해 다음 담당자가 참고할 수 있도록 했습니다. 구성요소를 아는 것에서 한 걸음 더 나아가, **어느 상태를 확인하고 어떤 순서로 조작할지**까지 전달하려 했습니다.

### 메시징에서는 접수 이후의 전달 상태를 관찰했습니다

메시징에서도 확인 지점을 구분해야 했습니다. API의 접수 응답만으로는 이후의 전달 지연이나 에이전트 상태를 알기 어려웠습니다. 저는 Kafka·InfluxDB·Grafana를 이용한 모니터링 개발을 맡았고, 실제 메일 지연에 대응했습니다.

여기서 운영자가 찾아야 할 것은 접수 이후 어느 구간이 지연되고 있는지였습니다. 제휴에서 인증 완료와 동의 완료를 나눈 것처럼, 메시징에서도 접수와 실제 전달을 구분해야 후속 확인 대상을 좁힐 수 있었습니다.

## 다음 설계에서 먼저 살펴볼 기록

처음의 요청으로 돌아가면, 남겨야 할 결과는 구체적입니다. 인증은 확정됐고, 동의 A는 성공했으며, B에는 확인할 실패 이력이 있습니다. 이 구분이 있어야 이미 끝난 결과를 보존하면서 남은 작업을 판단할 수 있습니다. 다만 동의 처리가 시작조차 되지 못한 항목은 실패 이력도 남지 않으므로, 그 경우는 앞서 말한 후속 작업 전달의 내구성 과제로 남습니다.

다음 설계에서도 실패한 요청 하나를 따라가 보려 합니다. **어디까지 끝났는지, 어떤 갱신을 함께 보호하는지, 다음 처리는 무엇을 계기로 시작하는지, 운영자는 어디에서 확인할 수 있는지**를 차례로 살펴볼 것입니다. 이 질문에 답할 수 있어야 트랜잭션·캐시·재처리가 실패 이후에도 어떻게 이어지는지 설명할 수 있기 때문입니다.

<details markdown="1" class="experience-notes">
<summary>보충 · 약관, 공통 모듈과 다른 운영 경험</summary>

실패 대응 외에도, 함께 바뀌어야 할 것과 따로 바뀌어야 할 것을 나누는 판단은 반복됐습니다.

**약관에서는 내용과 화면 배치를 분리했습니다.** 사이트별 HTML과 익일 반영 방식 대신, 약관 내용의 버전·시행일과 화면별 그룹·노출 순서를 나눴습니다. 시행일에 맞춘 노출은 자동화하고, 등록 오류 수정 같은 운영 상황을 고려해 버전 번호는 운영자가 관리하도록 남겼습니다. 사이트마다 다른 테이블·시퀀스 이름은 naming strategy와 설정으로 처리했습니다. 저는 주요 모델·구현과 공동 발표를 맡았고, 회원 동의 확장은 역할을 나누어 진행했습니다.

**공통 모듈에서는 사이트 정책까지 같다고 가정하지 않았습니다.** DB 통합 뒤에도 남은 API·검증 중복을 줄이기 위해 팀에서 공통 모듈을 설계했고, 저는 제휴·인증 모듈을 맡았습니다. 공통 흐름을 재사용하면서 사이트별 정책 차이를 유지했습니다. 재사용 범위가 넓어질수록 공유 코드 변경 시 함께 확인할 사용처도 늘어납니다.

**함께 참고할 운영 경험**

- **결제:** 브라우저 갱신 이후 특정 카드 인증이 실패하는 상황에 대응하고 연동 업체에 공유했습니다. VAN 장애 알림도 다뤘습니다. 관리자에서는 JPA와 MyBatis를 병행하며 사용 문서를 정리하고 팀에 공유했습니다.
- **로그인:** DB 연결 장애 분석과 Java/Spring 전환 설계에 참여했습니다. Caffeine 적용은 팀 작업이었습니다. 보안 라이브러리의 .NET 버전 제약은 DB 장애 원인과 별도 조건으로 다뤘습니다.
- **DNS:** 기존 HTTP 연결 재사용과 새 연결의 이름 해석을 나눠 재현하고 내부에 공유했습니다. 주소 조회 성공을 보관하는 positive 캐시와 실패를 보관하는 negative 캐시도 구분했습니다. DNS 변경이 기존 연결의 대상까지 즉시 바꾸지는 않기 때문입니다.
- **정보 보호·전환:** CI 저장·조회 경로의 암호화, 종료되는 NICE API의 교체, SCDF를 통한 개인정보 배치 전환도 맡았습니다.

</details>

</div>
