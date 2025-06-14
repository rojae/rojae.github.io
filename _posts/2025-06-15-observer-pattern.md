---
title: (행위 패턴) Observer Pattern - 옵저버 패턴
author: rojae
date: 2025-06-15 02:29:30 +0900
published: true
categories: [design-pattern]
tags: [java, design-pattern, behavioral-pattern, observer-pattern]
mermaid: true
image:
  path: /assets/img/posts/2025-06-14-chain-of-responsibility-pattern/chain-of-responsibility.png
---

# 서비스가 커질수록 필요한 설계 패턴 – 메시징 시스템 예제 중심으로

초심으로 돌아가서, 과거 `디자인패턴`의 필요성에 대해서 이야기했던 글이 있다.
그러면서 발송 앞단의 서버를 구현하는 내용을 작성했다. (일명 : `message-gateway-api`)

- 👉 [서비스가 커질수록 필요한 설계 패턴 – 메시징 시스템 예제 중심으로](/posts/design-pattern-intro)

# 그래서 발송 부분은? - message-sender-api

생각해보면, 발송 부분은 작성하지 못했는데 이 부분에 대해서 작성을 하려고 한다.
다만 내용이 좀 패턴위주가 아닌 `패턴을 사용한 기술`과 `프레임워크`를 살펴보려고 한다.

# 발송 서버를 구현하면서 추가가 될 부분

발송 처리를 위해서는 `실시간 처리`의 `효율화`를 위해서 `Webflux`와 `Kafka`를 사용할 것이다.
이떄 우리가 개발을 해야할 부분은 다음과 같다.

## 메시지 발송 등록 부분 (message-gateway-api)
사실, 지금까지 작성했던 글들의 내용이 모두 메시지 발송 등록 부분에 해당한다.

- 👉 [(생성패턴) Factory Pattern - 슬쩍 팩토리에서 처리하기 (메시징 서비스를 예제로)](/posts/factory-pattern)
- 👉 [(구조패턴) Strategy Pattern - 발송 후처리 전략 설립하기 (메시징 서비스를 예제로)](/posts/strategy-pattern)
- 👉 [(구조패턴) Template Method Pattern - 후처리 로직의 중복을 제거해보자 (메시징 서비스를 예제로)](/posts/template-method-pattern)
- 👉 [(행위 패턴) Chain of Responsibility Pattern - 메시지 발송 전 처리 파이프라인 만들기](/posts/chain-of-responsibility-pattern)

### Virtual Thread를 사용한 병렬처리

###    

## 메시지 발송 처리 부분 (message-sender-api)

### 

### 

# Observer Pattern (옵저버 패턴)

대규모 메시징 시스템을 운영하다 보면, 기획자나 매니저로부터 수많은 요구사항이 들어옵니다. 
발송 전에 처리해야 할 조건은 점점 늘어나고 복잡해지네요.

_개발자 입장에서는 이를 어떻게 "우아하게" 대응할 것인지 고민하게 됩니다._
