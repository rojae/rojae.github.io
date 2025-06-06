---
title: 역삼 GFC에서 1년 - 벌써 일년
date: 2023-11-15 19:00:00 +0900
categories: [life]
tags: [life, career, retrospective, 지마켓, 서버개발]
image:
  path: /assets/img/posts/2023-11-15-one-year-in-gmarket/one-year-in-gmarket.jpeg
---

> 이 글은 과거 블로그에서 옮겨왔습니다.
> [출처: 로재의 개발 일기](https://redcoder.tistory.com/343)
{: .prompt-info }

# 역삼 GFC에서 벌써 1년

지마켓에 합류한 지 어느덧 1년.  
이직 글을 올린 게 엊그제 같은데, 벌써 시간이 이렇게 흘렀다.  
📌 [이직 후기 바로가기](https://redcoder.tistory.com/315)

---

## 1년 동안 나는 무엇을 했을까?

> "회원담당입니다."  
라고 하면 흔히 단순 회원 가입/로그인만 떠올리지만, 실제로는  
**가입, 로그인, 인증, 메시징 등 복잡한 시스템의 총괄자**에 가까웠다.  
사실 R&R에는 불만도 있었지만, 그만큼 성장도 많았다.

---

### 통합가입 개선 프로젝트

- **노후화된 ASP, .NET 시스템**을 걷어내고 Java Spring으로 전환
- JPA와 WebFlux 도입을 통해 **Reactive 기반의 정합성 높은 서비스**로 개편  
  → 회원 데이터는 민감하다. 꼬이면 대형 장애로 이어지기에, 수많은 테스트와 고민을 거쳤다.
- 개인적으로 [Udemy WebFlux 강의](https://www.udemy.com/course/build-reactive-restful-apis-using-spring-boot-webflux)도 수강하며 보강

**현재도 안정적으로 운영 중이며**, 틈틈이 지속 개선 중이다.

---

### 인증 시스템 개선 + 첫 PL 경험

- 사이트 전반에 걸친 인증 흐름을 **새롭게 정의하고 개선**
- **팀 내 첫 PL 역할**을 맡아, 일정/품질/운영까지 책임
- 밤낮없이 신경을 곤두세웠고, **좋은 동료 덕분에 무사히 LTS 완료**
- 아직 개선 여지는 있지만, 차근차근 나아가는 중이다. 😭

---

### 승진

무사히 마무리된 프로젝트 덕분일까.  
**매니저님의 좋은 평가**로 인해 이번에 **대리로 승진**하게 되었다.  
여러 시행착오와 고민 끝에 맞이한 결과라 더 의미가 깊다.

---

## 그래서 로재씨, 무엇을 느꼈나요?

이전 글에서 말했던 것처럼  
> 개발자는 근면성실해야 한다.  
그건 맞다. 하지만…

---

### "비즈니스 감각"은 선택이 아닌 필수다..!

![리더와 보스](/assets/img/posts/2023-11-15-one-year-in-gmarket/leader-boss.png)

> “리더와 보스는 다르다”  
PM/팀장만이 리더인 게 아니다.  
PL이 되면서 깨달았다. 개발자로서도 **비즈니스 사고는 필수**라는 것을.

- 이 이슈는 정말 크리티컬한가?  
- 일정과 리소스는 어떻게 확보할 수 있을까?  
- 이건 꼭 지금 해야 하는가, 아니면 나중에 해도 될까?

단순한 개발 작업도  
**"왜 해야 하는가?"**에 대한 설명이 있어야 리소스가 움직인다.  
→ **비즈니스 관점에서 소통하지 않으면, 아무리 좋은 설계라도 외면받을 수 있다.**

---

### 운영과 CS까지 고려한 설계가 필요하다.

개발이 잘 돼도  
운영과 고객 문의에 취약하면 **"좋은 시스템"이라 할 수 없다.**

- 장애 시 빠르게 대응 가능한가?
- CS팀이 현황을 알 수 있는가?
- 모니터링과 로그는 충분한가?

결국 우리는 **서비스 비즈니스**를 하고 있고,  
우리의 월급은 **레거시에서 나오는 매출이 지켜준다.**

---

## 기억하고 싶은 요약

- **개발은 도구**일 뿐이다.  
- **리딩은 PL과 매니저의 몫**. 수동적이면 성장 없다.
- **비즈니스와 개발의 연결고리**를 고민하자.
- 다음에는 **더 주도적인 로재**가 되자.

---

## 다음 목표 (Next Step)

- 안정성과 속도, 둘 다 잡는 설계자로
- 주니어를 도울 수 있는 멘토로
- 더 넓은 비즈니스 인사이트를 가진 개발자로

> 회의에서 말이 통하는 개발자.  
> 문제를 해결하는 개발자.  
> **성장을 멈추지 않는 개발자.**

내년에도 더 성장한 로재가 되어보자. 👏🏻  

> 나는 PL, PO를 꿈꾼다.
