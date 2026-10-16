---
title: FluxGate는 왜 Redis Lua를 썼을까 - (원자성과 재시도)
author: rojae
date: 2026-10-17 00:10:00 +0900
published: true
categories: [backend]
tags: [redis, lua, rate-limiting, concurrency, fluxgate]
image:
  path: /assets/img/posts/2026-10-17-fluxgate-lua-atomicity-and-failure-boundaries/atomicity.png
  alt: 모든 밴드를 검사한 뒤 함께 차감하거나 거절하는 FluxGate의 처리 흐름을 요약한 표지
---

> 확인과 차감을 한 실행 범위로 묶으면 무엇이 보장되는지, 그 범위가 여러 제한과 여러 슬롯으로 넓어질 때 거절·실패 뒤에 무엇이 남는지 따라갑니다.
{: .prompt-info }
<!-- post-check: tone=polite -->

## 토큰 하나에 요청 둘이 들어오면

남은 토큰은 1개인데 요청 2개가 동시에 들어옵니다. 앱 서버가 잔여량 조회와 차감을 별도 명령으로 보낸다면, 두 요청이 모두 차감 전의 잔여량을 읽을 수 있습니다. 둘 다 “1개 남았으니 통과”라고 판단합니다.

<figure class="post-figure post-figure--diagram" id="figure-race" aria-labelledby="race-caption">
  <div class="figure-head"><small>01 · 동시 요청</small>같은 입력인데 통과 건수가 달라집니다</div>
  <picture class="diagram-wide"><img data-preserve-picture="true" src="/assets/img/posts/2026-10-17-fluxgate-lua-atomicity-and-failure-boundaries/race-desktop.svg" alt="잔여 토큰 1에 요청 A와 B가 동시에 들어올 때, 명령을 따로 보내면 B의 조회가 A의 조회와 차감 사이에 끼어들어 두 요청이 모두 통과합니다. Lua 한 실행 범위에서는 A의 조회·판단·차감이 끝난 뒤 B가 잔여 0을 보고 거절되어 통과는 1건만 남습니다." width="700" height="492" loading="lazy"></picture>
  <picture class="diagram-narrow"><img data-preserve-picture="true" src="/assets/img/posts/2026-10-17-fluxgate-lua-atomicity-and-failure-boundaries/race-mobile.svg" alt="잔여 토큰 1에 요청 A와 B가 동시에 들어올 때, 명령을 따로 보내면 B의 조회가 A의 조회와 차감 사이에 끼어들어 두 요청이 모두 통과합니다. Lua 한 실행 범위에서는 A의 조회·판단·차감이 끝난 뒤 B가 잔여 0을 보고 거절되어 통과는 1건만 남습니다." width="320" height="900" loading="lazy"></picture>
  <figcaption id="race-caption">잔여 1과 요청 A·B는 설명을 위한 상황입니다. <a class="diagram-source diagram-wide" href="/assets/img/posts/2026-10-17-fluxgate-lua-atomicity-and-failure-boundaries/race-desktop.svg" target="_blank" rel="noopener">그림 원본 보기 ↗</a><a class="diagram-source diagram-narrow" href="/assets/img/posts/2026-10-17-fluxgate-lua-atomicity-and-failure-boundaries/race-mobile.svg" target="_blank" rel="noopener">그림 원본 보기 ↗</a></figcaption>
</figure>

각 Redis 명령은 원자적입니다. 틈은 명령과 명령 사이에 있습니다. “명령을 따로 보낼 때”에서 B의 조회는 A의 조회와 차감 사이에 들어왔고, 한도 1에 통과 2건이 남았습니다. Redis는 Lua 스크립트 한 번을 끝까지 실행하는 동안 다른 명령을 처리하지 않습니다. 이 글에서는 그 구간을 **한 실행 범위**라고 부릅니다. 조회부터 차감까지를 한 실행 범위에 두면, B는 A가 끝난 뒤의 잔여량 0을 보고 거절됩니다.

개인 오픈소스 FluxGate에서 Redis Lua를 선택한 이유가 이 동시 요청의 원자성이었습니다. 그런데 함께 묶을 대상이 버킷 하나에서 여러 제한, 여러 Redis 슬롯으로 늘어나면 질문이 달라집니다. 한 실행 범위는 어디까지 닿을까요? 닿지 않는 곳에서는 거절과 실패 뒤에 무엇이 남을까요? 차감은 끝났는데 응답을 못 받았다면 다시 실행해도 될까요?

이 글은 개인 오픈소스와 사내 POC의 설계를 설명합니다. 공개 버전 `v0.3.7`과, 공개 버전과 별도로 작업 중인 장기 지원 브랜치(LTS)를 구분합니다. LTS 소스는 확인한 커밋 `d2b771a`에 고정했습니다. 상용 운영 성과나 성능 측정은 다루지 않습니다. 구현 근거는 마지막에 모았습니다.

## 확인과 차감을 한 실행 범위에 둡니다

토큰 버킷은 정해진 속도로 토큰을 채우고, 요청마다 필요한 양을 쓰는 제한 방식입니다. 여러 앱 서버가 같은 제한을 적용하려면 공유된 잔여량을 기준으로 판단해야 합니다.

여기서 필요한 원자성은 **상태 확인과 변경 사이에 다른 요청이 끼어들지 않는 성질**입니다. FluxGate는 이 일을 Redis 안의 짧은 Lua 스크립트로 처리합니다.

> **쉽게 말하면** 좌석이 남았는지 확인하는 창구와 예약하는 창구를 하나로 합치는 일입니다. 확인한 좌석을 다른 창구가 먼저 팔아 버리는 틈을 없앱니다.
{: .prompt-tip }

그림 1이 두 요청 사이의 끼어듦을 보여 줬다면, 아래 블록은 요청 하나가 한 실행 범위 안에서 거치는 단계를 보여 줍니다. 구조를 비교하는 **설명용 의사코드**이며 실행 코드나 실측 결과가 아닙니다.

```text
# 명령을 따로 보낼 때 (앱 서버에서)
잔여량 = Redis에서 조회
허용 여부 = 보충량과 잔여량으로 계산
허용한다면 Redis에 차감 결과 저장

# Lua 한 실행 범위 (Redis 안에서)
현재 시각 확인 → 보충량 계산
→ 허용 판단 → 차감 결과 저장
```

단일 `INCR`처럼 명령 하나로 끝나는 일은 이미 원자적입니다. Lua는 **여러 연산으로 이루어진 판단**을 함께 끝내야 할 때 필요합니다. 토큰 버킷은 시각과 잔여량을 읽고 보충량을 계산한 뒤에야 차감 여부를 정할 수 있으므로 여기에 해당합니다.

LTS 스크립트는 Redis의 `TIME`을 사용해 시각을 얻습니다. 앱 서버마다 다른 시계를 기준으로 보충량을 계산하는 문제를 줄이는 선택입니다. 다만 Redis 시계 자체의 정확성과, 스크립트에 명시된 Lua 5.1 숫자 정밀도 한계는 여전히 고려해야 합니다.

**그 대가로, 스크립트가 도는 동안 같은 Redis의 다른 작업은 기다립니다.**

## SHA가 기억하는 것은 코드입니다

이 절은 실행 범위를 넓히는 이야기가 아니라, 같은 스크립트를 매번 호출하는 비용을 줄이는 최적화입니다. `EVALSHA`는 Redis에 로드된 스크립트의 SHA를 지정해 실행하는 명령입니다. 키는 `KEYS`, 용량·기간·요청량 같은 값은 `ARGV`로 전달합니다.

캐시되는 것은 스크립트 본문입니다. 매번 본문 전체를 보내는 대신 SHA와 이번 요청의 인자만 보내므로, 줄어드는 것은 본문의 반복 전송입니다. 이전 요청의 결과를 재사용하는 구조가 아니며, Redis 호출과 스크립트 실행은 요청마다 일어납니다.

Redis 재시작이나 스크립트 캐시 제거 뒤, 또는 Cluster에서 다른 노드로 넘어간 뒤에는 `NOSCRIPT`가 올 수 있습니다. 스크립트 캐시는 노드마다 따로 있기 때문입니다. `NOSCRIPT`는 실행할 스크립트가 없다는 응답이고, 현재 구현은 이때 본문을 보내는 `EVAL`로 대체 실행합니다.

```text
EVALSHA(scriptSha, keys, args)
  └─ NOSCRIPT 응답 → EVAL(script, keys, args)
```

`NOSCRIPT`는 스크립트가 실행되지 않았다는 응답이므로, 대체 실행해도 같은 요청을 두 번 차감하지 않습니다. 대신 그 호출에는 본문을 담은 `EVAL` 왕복이 더해지고, 다음 호출을 위해 스크립트를 다시 적재합니다. 재적재는 연달아 몰리지 않도록 간격을 두고 시도합니다. 남는 비용은 `EVAL` 왕복 한 번과 스크립트 재적재입니다.

## 락과 무엇이 같고 무엇이 다른가

확인과 차감을 직렬화하는 방법이 Lua만은 아닙니다. RDB 행 잠금도 공유 상태의 동시 변경을 직렬화할 수 있습니다. 어느 쪽이든 “함께 끝내야 하는 일”을 정해야 한다는 점은 같습니다.

| 수단 | 함께 관리할 범위와 비용 |
|---|---|
| RDB 행 잠금 | 트랜잭션 안의 업무 검증·갱신, 잠금 대기 |
| Redis Lua | 제한 상태의 계산·갱신, 스크립트 실행 시간과 Redis 의존성 |

FluxGate는 Redis 위에 별도 락을 두는 방식(락 소유자·만료 시간·스핀 대기를 설계해야 하는 방식)과도 다르게, 필요한 갱신을 Redis 안의 스크립트에서 끝냈습니다. 당시 선택의 출발점은 Redis에 둔 제한 상태였고, RDB 행 잠금과의 비교는 이 구조를 설명하며 사후에 정리한 내용입니다. 두 방식을 실험으로 비교하지는 않았습니다.

스크립트가 실행되는 동안 다른 Redis 작업은 끼어들지 못합니다. 그래서 Lua 안에는 짧은 상태 갱신만 두고, 오래 걸리는 계산이나 외부 업무는 넣지 않아야 합니다.

## 제한이 두 개라면 모두 확인해야 합니다

초당 제한과 분당 제한을 함께 적용할 수 있습니다. 이처럼 한 규칙 안에서 기간이 다른 제한을 여기서는 **밴드**라고 부릅니다. 버킷 하나를 지키던 실행 범위가 밴드 여러 개로 넓어져야 하는 지점입니다.

앞 밴드에서 먼저 차감하고 뒤 밴드에서 거절하면 어떻게 될까요? 분당 밴드에 남은 토큰이 없는 요청 하나를 두 구현에 넣어 보겠습니다.

<figure class="post-figure post-figure--diagram" id="figure-bands" aria-labelledby="bands-caption">
  <div class="figure-head"><small>02 · 멀티밴드</small>같은 거절, 다른 흔적</div>
  <picture class="diagram-wide"><img data-preserve-picture="true" src="/assets/img/posts/2026-10-17-fluxgate-lua-atomicity-and-failure-boundaries/bands-desktop.svg" alt="분당 밴드가 소진된 요청 하나가 거절될 때, 공개 v0.3.7은 앞서 차감한 초당 밴드를 N-1로 남깁니다. LTS는 한 실행 범위에서 두 밴드를 토큰 차감 없이 먼저 검사하므로 거절 뒤 두 밴드가 그대로 남습니다." width="700" height="498" loading="lazy"></picture>
  <picture class="diagram-narrow"><img data-preserve-picture="true" src="/assets/img/posts/2026-10-17-fluxgate-lua-atomicity-and-failure-boundaries/bands-mobile.svg" alt="분당 밴드가 소진된 요청 하나가 거절될 때, 공개 v0.3.7은 앞서 차감한 초당 밴드를 N-1로 남깁니다. LTS는 한 실행 범위에서 두 밴드를 토큰 차감 없이 먼저 검사하므로 거절 뒤 두 밴드가 그대로 남습니다." width="320" height="930" loading="lazy"></picture>
  <figcaption id="bands-caption">위는 공개 <code>v0.3.7</code>에서 밴드가 초당 → 분당 순서로 설정됐을 때, 아래는 LTS 커밋 <code>d2b771a</code>의 처리입니다. N은 설명용 값입니다. 여러 규칙이 다른 슬롯에 걸친 경우는 다음 절에서 다룹니다. <a class="diagram-source diagram-wide" href="/assets/img/posts/2026-10-17-fluxgate-lua-atomicity-and-failure-boundaries/bands-desktop.svg" target="_blank" rel="noopener">그림 원본 보기 ↗</a><a class="diagram-source diagram-narrow" href="/assets/img/posts/2026-10-17-fluxgate-lua-atomicity-and-failure-boundaries/bands-mobile.svg" target="_blank" rel="noopener">그림 원본 보기 ↗</a></figcaption>
</figure>

공개 `v0.3.7`은 Java에서 밴드를 설정된 순서대로 소비합니다. 밴드마다 차감을 시도하고 거절된 밴드에서 바로 반환하므로, 밴드가 초당 → 분당 순서로 설정됐다면 요청은 최종 거절됐지만 초당 밴드의 토큰은 이미 줄어 있습니다. 검사와 차감이 밴드 단위로 끝나기 때문에, 뒤 밴드의 거절이 앞 밴드의 차감을 되돌리지 못합니다.

현재 LTS는 멀티밴드를 **모두 통과하거나 차감하지 않는 방식(all-or-nothing)**으로 처리합니다. 한 실행 범위 안에서 먼저 모든 밴드를 검사하고(Pass 1), 하나라도 거절하면 차감 단계로 넘어가지 않습니다. 모두 통과할 때만 함께 차감합니다(Pass 2).

이 성질은 Lua로 묶었다고 저절로 생기지 않습니다. Redis Lua는 스크립트 도중 오류가 나도 앞선 쓰기를 되돌리지 않습니다. LTS의 all-or-nothing은 토큰을 차감하지 않고 검사만 하는 Pass 1과 차감하는 Pass 2를 나눈 설계에서 나옵니다. 같은 규칙 설정에서 거절되면 토큰은 차감하지 않고 키 만료 시간만 갱신합니다(규칙 용량이 바뀐 직후의 상태 이전은 별도).

**이 보장은 함께 처리할 키가 한 실행 범위에 들어갈 때까지만 성립합니다.**

## 다른 슬롯이면 보상이 필요합니다

규칙이 여러 개이고 그 키들이 흩어져 있으면 이 전제가 깨집니다. Redis Cluster는 키를 해시 슬롯이라는 구역에 나눠 두고, 여러 키를 한 스크립트에서 처리하려면 같은 슬롯에 있어야 합니다.

현재 구현은 슬롯을 확인해 처리 경로를 고릅니다. 같은 슬롯에서는 함께 처리하고, 다른 슬롯에 걸친 여러 규칙은 순차 소비한 뒤 실패하면 앞의 차감을 환급합니다. 이 환급이 **보상 처리**입니다. 이미 끝난 변경을 나중의 작업으로 되돌리는 방식입니다.

> **쉽게 말하면** 여러 곳에서 결제하다 마지막 결제가 실패해 앞선 결제를 취소하는 일입니다. 취소가 끝나기 전에는 돈이 빠져 있고, 취소 작업도 실패할 수 있습니다.
{: .prompt-tip }

따라서 보상 환급을 여러 슬롯 전체의 원자성으로 볼 수는 없습니다. 환급 전에 다른 요청이 줄어든 잔여량을 볼 수 있습니다. 프로세스가 종료되거나 Redis 호출이 실패하면 차감이 남을 수도 있습니다. 같은 슬롯에 모으면 함께 처리할 수 있는 범위가 넓어지지만, 키 배치와 부하 분산의 제약을 함께 검토해야 합니다.

**환급 전에는 줄어든 잔여량이, 환급 실패 시에는 차감이 남습니다.**

## 응답이 없으면 실행 여부부터 봅니다

환급이 실패하는 경우처럼, Redis 호출 자체가 실패했을 때도 남는 상태를 따로 따져야 합니다. Redis에 명령을 보낸 뒤 연결이 끊겼다고 해 보겠습니다. 실행 전에 실패했을 수도 있고, 차감은 끝났지만 응답만 잃었을 수도 있습니다.

두 번째 경우에 같은 명령을 다시 보내면 한 요청에 두 번 차감할 수 있습니다. 현재 저장소 구현은 **실행 여부가 불명확한 명령 실패를 자동 재시도하지 않습니다.** 명령 타임아웃도 기본값에서는 재시도하지 않지만, `retryOnTimeout` 설정을 켜면 재시도되며 이는 이중 차감 가능성을 감수하는 선택입니다.

| 받은 결과 | 현재 구현의 대응 |
|---|---|
| `NOSCRIPT` | 실행되지 않았으므로 `EVAL`로 대체 실행 |
| 명령 중 연결 실패 | 이미 차감했을 수 있으므로 재시도하지 않음 |
| 명령 타임아웃 | 기본은 재시도하지 않음, `retryOnTimeout`을 켜면 재시도 |

실패했다는 사실만으로 재시도 여부를 정할 수는 없습니다. “첫 실행이 상태를 바꾸지 않았다는 근거가 있는가”를 확인해야 합니다.

**호출자는 차감됐는지 알 수 없는 상태로 실패를 받습니다.**

## 장애 때 허용할지도 정책입니다

재시도하지 않거나 재시도로도 끝나지 않은 실패는 장애 정책으로 넘어갑니다. 제한 판단을 마치지 못한 요청을 허용할지 막을지 정하는 단계입니다. 현재 구현은 인스턴스 메모리 안에서 동작하는 대체 제한기를 설정해 두었다면 먼저 그것으로 판단합니다.

장애 정책의 기본값은 `DENY`이며, 이 경로는 사용 불가 오류(HTTP 503)로 이어집니다. `ALLOW`는 제한 판단을 마치지 못해도 서비스를 계속 이용하게 하는 선택입니다. 배포하는 쪽에서는 서비스 가용성과 제한 준수 중 무엇을 우선할지 정해야 하며, Lua가 상태 갱신을 묶어 주어도 이 정책까지 대신 결정해 주지는 않습니다. 정리하면 `DENY`는 장애 동안 정상 요청을 막고, `ALLOW`는 그동안 제한을 놓칩니다.

판단 위치도 장애 경계를 바꿉니다. **Direct**는 앱 내부 핸들러가 엔진과 Redis를 호출하고, **HTTP**는 별도 제한 서비스에 판단을 요청하므로 적용 지점을 분리하는 대신 네트워크 호출과 서비스 장애 경계가 늘어납니다.

## 규칙 알림과 토큰 차감은 별개입니다

여기까지가 토큰 차감의 원자성이었다면, 규칙 변경은 그와 다른 일관성 문제입니다. 관리 화면에서 바꾸는 제한 규칙의 원천 저장소는 MongoDB이고, 실행 중인 인스턴스는 규칙을 캐시합니다. Redis Pub/Sub으로 변경을 알리면 알림을 받은 인스턴스가 규칙 캐시를 갱신합니다.

Pub/Sub은 놓친 메시지를 재생해 주지 않습니다. LTS는 이를 기본 60초 간격의 주기 조회로 보완하며, 이 기능은 설정으로 끌 수 있고 실제 보완 경로는 설정과 캐시 조건에 따라 달라집니다. 별도 메시지 로그 운영을 줄이는 대신 일시적으로 오래된 규칙을 쓰는 구간을 받아들인 선택입니다. 알림을 놓친 인스턴스는 보완 조회 전까지 이전 규칙을 씁니다.

## Lua를 검토할 때

FluxGate가 Lua를 쓴 이유는 확인과 차감의 원자성이었고, 그 이유가 닿는 범위는 한 실행 범위에 들어가는 키들까지였습니다. 그 바깥, 즉 다른 슬롯의 규칙, 응답을 잃은 호출, Redis 밖의 규칙 원천은 보상 환급·재시도 정책·장애 정책·재동기화로 따로 설계했습니다.

| 상황 | 먼저 확인할 것 |
|---|---|
| Redis의 여러 연산을 하나로 묶어야 할 때 | 함께 읽고 바꿀 키, 짧게 끝나는 실행 범위 |
| 명령 하나로 충분할 때 | 기존 원자적 명령으로 처리할 수 있는지 |
| 여러 제한을 함께 적용할 때 | 밴드 전체의 차감 여부, Cluster 슬롯 배치 |
| 요청이 실패하거나 응답을 잃었을 때 | 남은 차감, 보상 실패 가능성, 재실행 근거 |
| 제한 규칙을 바꿀 때 | 토큰 차감과 다른 일관성 문제: 알림 누락과 보완 조회 간격 |

이 판단은 함께 읽고 바꿀 키가 한 실행 범위에 들어가고 그 안의 작업이 짧게 끝날 때 성립합니다. 스크립트부터 쓰기 전에 다음 세 가지를 적어 보는 편이 설계를 더 정확하게 설명합니다.

- **보호하는 상태와 그 범위:** 어떤 키를 어느 실행 범위에서 함께 바꾸는가.
- **거절 뒤 남는 차감과 환급 실패:** 성공 경로만큼 거절·보상 실패 뒤의 상태를 확인했는가.
- **다시 실행해도 된다는 근거:** 재시도 전에 첫 실행이 상태를 바꾸지 않았음을 알 수 있는가.

## 구현 근거

- [공개 v0.3.7 — 밴드 순차 소비](https://github.com/OpenFluxGate/fluxgate/blob/v0.3.7/fluxgate-redis-ratelimiter/src/main/java/org/fluxgate/redis/RedisRateLimiter.java)
- [LTS Lua — 멀티밴드의 2단계 처리](https://github.com/OpenFluxGate/fluxgate/blob/d2b771ab7ee9864a040e6672014fb16fb54b4873/fluxgate-redis-ratelimiter/src/main/resources/lua/token_bucket_consume.lua#L1-L15), [시간·정밀도 처리](https://github.com/OpenFluxGate/fluxgate/blob/d2b771ab7ee9864a040e6672014fb16fb54b4873/fluxgate-redis-ratelimiter/src/main/resources/lua/token_bucket_consume.lua#L51-L56)
- [LTS 제한기 — 같은 슬롯의 원자 처리와 다른 슬롯의 보상](https://github.com/OpenFluxGate/fluxgate/blob/d2b771ab7ee9864a040e6672014fb16fb54b4873/fluxgate-redis-ratelimiter/src/main/java/org/fluxgate/redis/RedisRateLimiter.java#L43-L71)
- [LTS 저장소 — EVALSHA·NOSCRIPT 처리](https://github.com/OpenFluxGate/fluxgate/blob/d2b771ab7ee9864a040e6672014fb16fb54b4873/fluxgate-redis-ratelimiter/src/main/java/org/fluxgate/redis/store/RedisTokenBucketStore.java#L694-L736), [명령 단계 실패 처리](https://github.com/OpenFluxGate/fluxgate/blob/d2b771ab7ee9864a040e6672014fb16fb54b4873/fluxgate-redis-ratelimiter/src/main/java/org/fluxgate/redis/store/RedisTokenBucketStore.java#L760-L777)
- [LTS 재시도 설정 — 타임아웃과 명령 실패의 재시도 판단](https://github.com/OpenFluxGate/fluxgate/blob/d2b771ab7ee9864a040e6672014fb16fb54b4873/fluxgate-core/src/main/java/org/fluxgate/core/resilience/RetryConfig.java#L145-L182)
- [LTS 자동 설정 — 알림·주기 조회 구성](https://github.com/OpenFluxGate/fluxgate/blob/d2b771ab7ee9864a040e6672014fb16fb54b4873/fluxgate-spring-boot3-starter/src/main/java/org/fluxgate/spring/autoconfigure/FluxgateReloadAutoConfiguration.java#L245-L273), [주기 조회 기본값 60초](https://github.com/OpenFluxGate/fluxgate/blob/d2b771ab7ee9864a040e6672014fb16fb54b4873/fluxgate-spring-boot3-starter/src/main/java/org/fluxgate/spring/properties/FluxgateProperties.java#L1689-L1695)
- [LTS 핸들러 — 실패한 호출을 장애 정책으로 넘기는 경로](https://github.com/OpenFluxGate/fluxgate/blob/d2b771ab7ee9864a040e6672014fb16fb54b4873/fluxgate-spring-boot3-starter/src/main/java/org/fluxgate/spring/handler/ResilientRateLimiter.java#L148-L189), [장애 정책](https://github.com/OpenFluxGate/fluxgate/blob/d2b771ab7ee9864a040e6672014fb16fb54b4873/fluxgate-spring-boot3-starter/src/main/java/org/fluxgate/spring/handler/ResilientRateLimiter.java#L274-L308)
- [LTS 아키텍처 — Direct·HTTP 경로](https://github.com/OpenFluxGate/fluxgate/blob/d2b771ab7ee9864a040e6672014fb16fb54b4873/docs/ko/architecture/README.ko.md#L173-L186)
- Redis 공식 문서: [스크립트 실행과 원자성](https://redis.io/docs/latest/develop/programmability/eval-intro/), [Pub/Sub의 전달 특성](https://redis.io/docs/latest/develop/pubsub/)

<details markdown="1">
<summary>같은 커밋에서 확인하기</summary>

Git이 설치된 환경의 빈 작업 디렉터리에서 실행합니다. Redis를 실행하는 대신 고정한 소스를 조회하는 절차입니다.

```bash
git clone https://github.com/OpenFluxGate/fluxgate.git fluxgate-source-check
git -C fluxgate-source-check --no-pager show d2b771ab7ee9864a040e6672014fb16fb54b4873:fluxgate-redis-ratelimiter/src/main/resources/lua/token_bucket_consume.lua
git -C fluxgate-source-check --no-pager show d2b771ab7ee9864a040e6672014fb16fb54b4873:fluxgate-redis-ratelimiter/src/main/java/org/fluxgate/redis/store/RedisTokenBucketStore.java
```

- Lua에서 `Pass 1` → `return rejection` → `Pass 2` 순서를 확인합니다. 거절되면 차감 단계로 넘어가지 않습니다.
- Java에서 `RedisNoScriptException` 뒤의 `connectionProvider.eval`과 명령 실패 시의 `Phase.COMMAND`를 확인합니다.
- `bad object`나 `path ... does not exist`가 나오면 가져온 저장소·커밋·경로를 확인합니다.

</details>
