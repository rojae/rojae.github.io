---
title: Orca Router 앞에 LiteLLM 한 겹 끼우기 - (게이트웨이, 비용, 폴백)
author: rojae
date: 2026-09-26 05:30:00 +0900
published: true
categories: [backend]
tags: [litellm, llm-gateway, cost-tracking, fallback, virtual-key, orca-router, deepseek, spring-webflux]
mermaid: true
image:
  path: /assets/img/posts/2026-09-26-litellm-gateway-in-front-of-orca-router/litellm-gateway.png
---
> 애플리케이션은 base URL 한 줄만 바꾸고, 키 관리와 비용 집계와 폴백을 게이트웨이로 옮겨 본 기록이다. LiteLLM을 실제로 띄워 무료 모델의 429와 예산 초과에 직접 부딪히며 얻은 것들을 정리해 둔다.
> + 샘플코드는 [litellm-gateway-sample](https://github.com/rojae/spring-sample/tree/main/litellm-gateway-sample)(게이트웨이 설정과 스크립트)과 [spring-sse-sample](https://github.com/rojae/spring-sample/tree/main/spring-sse-sample)(1편의 Spring 앱, 코드 변경 없음)에서 확인할 수 있다.
> + 이 글은 "LLM 통신 스택" 시리즈의 2편이다. 1편은 [SSE, LLM 시대에 다시 보기](/posts/sse-revisited-for-llm-streaming), 3편부터는 MCP(stdio와 Streamable HTTP, 게이트웨이 뒤의 MCP, 인증과 보안)를 다룰 예정이다.
{: .prompt-info }

---

## **"키가 앱마다 흩어져 있어요"**

LLM 기능이 서비스 하나에서 두 개, 세 개로 늘어나면 이런 상태가 된다.

- 업스트림 API 키가 앱마다 환경변수로 박혀 있고, 누가 어떤 키를 쓰는지 아무도 모른다.
- 이번 달 비용이 얼마인지는 공급자 콘솔에 들어가야 알 수 있고, 팀별로 나눠 볼 수 없다.
- 업스트림이 429를 내면 각 앱이 제각각 재시도한다. 아니면 그냥 죽는다.
- 모델을 바꾸려면 앱을 전부 다시 배포한다.

1편에서 만든 Spring 프록시도 Orca Router 키를 환경변수로 직접 들고 있었다. 앱이 하나일 때는 괜찮았는데, 이게 두 개 세 개가 되면 위의 네 가지가 그대로 내 문제가 된다.

---

## **"논의"**

게이트웨이를 끼우기 전에 오간 이야기는 대충 이랬다.

*A: "중간에 게이트웨이 하나 두면 되는 거 아니에요? 앱은 주소만 바꾸고요."*

*B: "무료 모델 쓰는데 비용 집계가 의미가 있어요? 어차피 0원인데."*

*C: "무료 모델이 429 나면 다른 무료 모델로 넘기면 되죠. 무료 모델 여러 개잖아요."*

A는 맞았다. B는 "의미 있게 만들 수 있다"가 답이었다. C는 틀렸는데, 틀렸다는 걸 실험으로 확인하기 전까지는 나도 그렇게 믿고 있었다.

---

## **"지금 다시 생각해보면서, 정리해보니.."**

위의 네 가지 문제는 모두 "애플리케이션이 알 필요 없는 일"이다. 그래서 중간에 한 겹을 끼운다. 앱은 게이트웨이 주소와 게이트웨이가 발급한 키만 알고, 업스트림 키와 비용과 라우팅은 게이트웨이가 가진다.

> **쉽게 말하면** 게이트웨이는 회사의 **총무팀**이다. 직원(앱)은 외부 업체(OpenAI, Orca Router)와 직접 계약하지 않고 총무팀에 요청서를 낸다. 총무팀이 업체 계약(API 키)을 들고 있고, 누가 얼마나 썼는지 장부(스팬드 로그)를 적고, 한 업체가 안 되면 다른 업체로 돌린다(폴백). 직원은 총무팀 내선번호(base URL)와 사원증(가상 키)만 있으면 된다.
{: .prompt-tip }

```mermaid
flowchart LR
    subgraph APPS["애플리케이션들"]
        A1["Spring SSE 프록시<br/>(1편)"]
        A2["배치 요약 잡"]
        A3["사내 챗봇"]
    end

    subgraph GW["LiteLLM Proxy (localhost:4000)"]
        direction TB
        K["가상 키 인증<br/>키별 모델 제한, 예산"]
        R["라우터<br/>모델 그룹, 폴백, 쿨다운"]
        C["비용 계산<br/>단가 × 토큰"]
        DB[("Postgres<br/>스팬드 로그, 키")]
        M["/metrics<br/>Prometheus"]
        K --> R --> C --> DB
        C -.-> M
    end

    subgraph UP["업스트림"]
        O1["Orca Router<br/>deepseek-v4-flash-free"]
        O2["Orca Router<br/>glm-5.3-flash-free"]
        O3["(나중에) OpenAI, Anthropic, ..."]
    end

    A1 & A2 & A3 -- "게이트웨이 키" --> K
    R -- "업스트림 키 (앱은 모름)" --> O1
    R -. "폴백" .-> O2
    R -.-> O3

    style K fill:#dcfce7,stroke:#22c55e
    style R fill:#e0f2fe,stroke:#0ea5e9
    style C fill:#fef3c7,stroke:#f59e0b
```

이 글에서는 이 그림의 초록, 파랑, 노랑 상자를 하나씩 실제로 눌러 본다. 게이트웨이로는 [LiteLLM](https://docs.litellm.ai)을 골랐다. OpenAI 호환 API를 그대로 노출하기 때문에 1편의 Spring 앱을 코드 변경 없이 붙일 수 있고, 가상 키와 비용 집계가 오픈소스 버전에 들어 있다.

---

## **"일단 띄워보자"**

### docker compose

LiteLLM 컨테이너와, 가상 키와 스팬드 로그를 저장할 Postgres다. (핵심만 남긴 것이고, `container_name`과 헬스체크 재시도 횟수 같은 나머지 필드는 저장소의 파일에 있다.)

```yaml
services:
  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    ports: ["${LITELLM_PORT:-4000}:4000"]
    environment:
      LITELLM_MASTER_KEY: ${LITELLM_MASTER_KEY:-sk-local-master-1234}
      DATABASE_URL: postgresql://llmproxy:dbpassword9090@db:5432/litellm
      ORCA_ROUTER_API_KEY: ${ORCA_ROUTER_API_KEY:?ORCA_ROUTER_API_KEY 가 필요합니다}
    volumes:
      - ./config.yaml:/app/config.yaml:ro
    command: ["--config", "/app/config.yaml", "--port", "4000"]
    depends_on:
      db:
        condition: service_healthy
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: litellm
      POSTGRES_USER: llmproxy
      POSTGRES_PASSWORD: dbpassword9090
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -d litellm -U llmproxy"]
      interval: 3s
```

호스트 포트는 `LITELLM_PORT`로 바꿀 수 있게 해 두었다. 4000은 다른 개발 도구와 자주 겹치는 포트다.

### config.yaml: 규칙 세 가지

```yaml
model_list:
  - model_name: deepseek-flash-free                   # 앱이 부르는 이름
    litellm_params:
      model: openai/deepseek/deepseek-v4-flash-free   # 규칙 1: OpenAI 호환이면 openai/ 프리픽스
      api_base: https://api.orcarouter.ai/v1          # 규칙 2: /v1 까지 적는다
      api_key: os.environ/ORCA_ROUTER_API_KEY         # 규칙 3: 키는 환경변수 참조
    model_info:
      input_cost_per_token: 0.00000022                # $0.22 / 1M (유료 쌍둥이 단가)
      output_cost_per_token: 0.00000066               # $0.66 / 1M

  - model_name: glm-flash-free                        # 폴백 대상 (역시 무료)
    litellm_params:
      model: openai/z-ai/glm-5.3-flash-free
      api_base: https://api.orcarouter.ai/v1
      api_key: os.environ/ORCA_ROUTER_API_KEY
    model_info:
      input_cost_per_token: 0.000000075
      output_cost_per_token: 0.00000025

  - model_name: broken-no-v1                          # 실패 재현용: /v1 빠뜨림
    litellm_params:
      model: openai/deepseek/deepseek-v4-flash-free
      api_base: https://api.orcarouter.ai
      api_key: os.environ/ORCA_ROUTER_API_KEY

litellm_settings:
  fallbacks: [{"deepseek-flash-free": ["glm-flash-free"]}]
  num_retries: 0          # 재시도 없이 바로 폴백
  allowed_fails: 1        # 1번 실패하면 그 배포를 쿨다운
  cooldown_time: 30
  callbacks: ["prometheus"]
  require_auth_for_metrics_endpoint: false
  # drop_params, request_timeout 과 router_settings(num_retries: 0) 는 저장소 파일 참고

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL
```

| 규칙 | 이유 |
|------|------|
| `model: openai/<업스트림 모델 ID>` | LiteLLM은 프리픽스로 어떤 프로바이더 코드로 호출할지 정한다. Orca Router는 OpenAI 호환이므로 `openai/` |
| `api_base`에 `/v1`까지 | LiteLLM은 뒤에 `/chat/completions`만 붙인다. 빠뜨리면 404 (원인 1) |
| `api_key: os.environ/...` | 설정 파일에 키를 적지 않는다. 컨테이너 환경변수에서 읽는다 |

> **쉽게 말하면** `model_name`은 **메뉴판 이름**이고 `litellm_params.model`은 **주방의 레시피**다. 손님(앱)은 "deepseek-flash-free 주세요"라고만 하면 되고, 그게 실제로 어느 업체의 어떤 모델인지는 주방(게이트웨이)만 안다. 레시피를 바꿔도 메뉴판은 그대로라서 손님은 모른다.
{: .prompt-tip }

### 무료 모델에 왜 단가를 붙이나

질문 B에 대한 답이다. Orca Router의 `deepseek/deepseek-v4-flash-free`는 요청당 $0이다. 그대로 두면 LiteLLM은 비용을 0으로 기록하고, 스팬드 로그는 아무 의미가 없어진다.

그래서 `model_info`에 **유료 쌍둥이 모델의 단가**(`deepseek/deepseek-v4-flash`, 입력 $0.22 / 출력 $0.66 per 1M)를 넣었다. 실제 청구는 0이지만 "유료였다면 얼마였을지"가 쌓인다. 나중에 유료로 넘어갈 때 예산을 잡는 근거가 되고, 팀별 사용량 비교도 된다. 이 트릭은 사내에서 구독제나 정액제 API를 쓸 때도 그대로 쓴다. 청구서에는 안 찍히지만 "누가 얼마나 썼는가"는 알아야 하기 때문이다.

> **쉽게 말하면** **무료 시식이지만 영수증에는 정가를 찍어 두는 것**이다. 돈은 안 냈지만 "이만큼 먹었다"는 기록이 남아야 나중에 정식으로 사 먹을 때 예산을 잡을 수 있다.
{: .prompt-tip }

```bash
export ORCA_ROUTER_API_KEY=...
docker compose -f litellm-gateway-sample/docker-compose.yml up -d
curl http://localhost:4000/health/liveliness   # "I'm alive!"
```

### 첫 호출

<figure style="text-align: center;">
  <img
    src="/assets/img/posts/2026-09-26-litellm-gateway-in-front-of-orca-router/gw-chat-terminal.png"
    alt="게이트웨이의 모델 목록과 첫 chat completion 호출"
    style="border-radius: 8px;">
  <figcaption style="margin-top: 0.5rem; font-size: 0.95rem; color: #666;">
    /v1/models 에는 config 의 model_name 세 개가 보이고, 응답 헤더에 모델 ID와 비용이 붙어 온다
  </figcaption>
</figure>

응답에서 세 가지를 확인할 수 있다.

- **`x-litellm-model-id`**: 실제로 어느 배포(deployment)가 처리했는지. 같은 `model_name` 아래 배포가 여러 개일 때 이 값으로 구분한다. 폴백이 일어났는지도 이 헤더로 안다.
- **`x-litellm-response-cost: 6.446e-05`**: 게이트웨이가 계산한 비용이다.
- **`model: deepseek-flash-free`**: 업스트림이 돌려준 `deepseek-v4-flash-ga-260731`이 아니라 **config의 `model_name`으로 바꿔서** 준다. 앱은 업스트림 모델 ID를 몰라도 된다.

> **쉽게 말하면** 응답 헤더의 `x-litellm-model-id`는 **영수증에 찍힌 담당 직원 번호**다. 같은 메뉴를 여러 주방이 만들 수 있을 때, 이번 주문을 실제로 누가 처리했는지 알려 준다. 폴백이 일어나면 이 번호가 바뀐다.
{: .prompt-tip }

비용이 맞는지 검산해 봤다.

```
prompt     98 × $0.22/1M = $0.00002156
completion 65 × $0.66/1M = $0.00004290
                    합계 = $0.00006446   ← x-litellm-response-cost 와 일치
```

`completion_tokens` 65개 안에 `reasoning_tokens` 16개가 포함되어 있다. 사고 과정 토큰도 출력 단가로 과금된다는 뜻이고, 이건 실제 DeepSeek 과금 방식과 같다.

### 스트리밍은 그대로 통과하나

1편의 핵심이 스트리밍이었으니, 게이트웨이를 거쳐도 SSE가 그대로 흘러나오는지가 중요하다.

<figure style="text-align: center;">
  <img
    src="/assets/img/posts/2026-09-26-litellm-gateway-in-front-of-orca-router/gw-stream-terminal.png"
    alt="LiteLLM 을 거친 스트리밍 응답 원문"
    style="border-radius: 8px;">
  <figcaption style="margin-top: 0.5rem; font-size: 0.95rem; color: #666;">
    reasoning_content 는 그대로 통과하고, usage 는 한 번만, 그리고 cost 필드가 추가됐다
  </figcaption>
</figure>

1편에서 업스트림에 직접 받은 원문과 비교하면 이렇다.

| 항목 | Orca Router 직접 (1편) | LiteLLM 경유 |
|------|------------------------|--------------|
| `reasoning_content` | delta에 따로 옴 | **그대로 통과** (`openai/` 프로바이더가 알 수 없는 필드를 버리지 않음) |
| `model` | `deepseek-v4-flash-ga-260731` | `deepseek-flash-free` (model_name으로 치환) |
| `usage` | **두 번** (finish 청크, 마지막 청크) | **한 번**, 마지막 청크에만 |
| `usage.cost` | 없음 | **`0.00006446` 추가** |
| `[DONE]` | 있음 | 있음 |

1편에서 "usage가 두 번 온다"고 프록시에서 막았던 문제가 여기서는 게이트웨이가 정리해 준다. 그리고 스트리밍 응답에도 `cost`가 붙는다. 클라이언트가 이 값을 읽으면 요청 단위로 비용을 표시할 수 있다.

### 가상 키에 예산 걸기

마스터 키는 관리자용이다. 앱에는 **가상 키**를 따로 발급하고, 거기에 모델 제한과 예산을 건다.

```bash
curl http://localhost:4000/key/generate \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"max_budget": 0.00005, "key_alias": "budget-demo"}'
```

예산을 일부러 5센트의 1/1000인 $0.00005로 잡았다. 요청 한 번(약 $0.00009)이면 넘는다.

> **쉽게 말하면** 가상 키는 **한도가 걸린 법인카드**다. 마스터 키는 카드를 발급하는 재무팀 권한이고, 앱에는 카드만 준다. 카드마다 쓸 수 있는 가게(모델)와 한도(예산)를 다르게 걸 수 있고, 한도가 차면 결제가 거절된다.
{: .prompt-tip }

<figure style="text-align: center;">
  <img
    src="/assets/img/posts/2026-09-26-litellm-gateway-in-front-of-orca-router/gw-budget-terminal.png"
    alt="예산이 걸린 가상 키로 두 번 호출: 첫 번째 성공, 두 번째 budget_exceeded"
    style="border-radius: 8px;">
  <figcaption style="margin-top: 0.5rem; font-size: 0.95rem; color: #666;">
    1회차 성공 (cost 8.844e-05). 2회차는 Budget has been exceeded. 그런데 key/info 의 spend 는 아직 0.0
  </figcaption>
</figure>

1회차 비용도 검산이 된다. 프롬프트 84 토큰과 출력 106 토큰(그중 사고 과정 91)이라서 `84 × $0.22/1M + 106 × $0.66/1M = $0.00008844`, 헤더의 `8.844e-05`와 같다. "ping" 한 마디에 사고 과정 토큰이 91개나 붙은 것도 눈여겨볼 만하다. 짧은 질문일수록 비용의 대부분이 사고 과정이다.

여기서 세 가지를 배웠다.

- **예산 검사는 요청 전에 한다.** 첫 요청은 예산 안에서 시작했으니 통과했고 결과적으로 예산을 넘겼다. 두 번째 요청은 시작 전에 막혔다. 즉 `max_budget`은 "이 금액에서 정확히 멈춘다"가 아니라 "이 금액을 넘긴 뒤의 다음 요청부터 막는다"다.
- **상태 코드가 422다.** 문서에는 400이나 429로 적힌 예가 섞여 있는데, 내가 쓴 `main-latest` 이미지는 422를 돌려줬다. 클라이언트에서 `type: "budget_exceeded"`로 분기하는 편이 안전하다.
- **`/key/info`의 `spend`는 바로 반영되지 않는다.** 두 번째 요청이 예산 초과로 막힌 직후에 조회했는데 `spend: 0.0`이었다. 예산 판정은 메모리 캐시에서 하고, DB 반영은 배치로 뒤따라온다. 몇 초 뒤 다시 조회하면 채워진다. 모니터링 대시보드가 "예산 초과인데 사용량은 0"으로 보일 수 있다는 뜻이다.

### 스팬드 로그 읽기

요청 한 건마다 Postgres에 한 줄이 남는다.

<figure style="text-align: center;">
  <img
    src="/assets/img/posts/2026-09-26-litellm-gateway-in-front-of-orca-router/gw-spend-terminal.png"
    alt="/spend/logs 로 본 요청별 비용"
    style="border-radius: 8px;">
  <figcaption style="margin-top: 0.5rem; font-size: 0.95rem; color: #666;">
    요청별 토큰 수와 가상 단가로 계산한 spend. 실패한 요청(broken-no-v1, 429)은 0 으로 남는다
  </figcaption>
</figure>

| 컬럼 | 의미 |
|------|------|
| `model` | 실제 호출한 업스트림 모델 (`openai/deepseek/...`). 응답의 `model`과 달리 여기는 원본 |
| `prompt_tokens`, `completion_tokens` | 업스트림 usage 그대로 |
| `spend` | `model_info` 단가로 계산한 금액 |
| `metadata.user_api_key_alias` | 어느 가상 키가 썼는지. 팀별 집계의 기준 |

실패한 요청도 `spend: 0.0`으로 남는다. 429나 404가 얼마나 났는지 이 로그로 셀 수 있다.

> **쉽게 말하면** 스팬드 로그는 **가계부**다. 언제, 누가(가상 키), 무엇을(모델), 얼마나(토큰), 얼마에(spend) 썼는지 한 줄씩 적힌다. 결제가 거절된 건도 0원으로 적어 두기 때문에 "왜 거절이 많았지"를 나중에 셀 수 있다.
{: .prompt-tip }

여기까지는 순조로웠다. 질문 A와 B는 이걸로 답이 됐다.

---

## **"의아했던 두 가지"**

그런데 일부러 망가뜨려 보는 단계에서 **아래 2가지 현상이 나왔다.**

1. *`api_base`에서 `/v1`을 빼고 두 번 호출했더니, 첫 번째는 404인데 두 번째는 429가 나왔다. 같은 설정인데.*
2. *무료 모델이 429를 맞으면 다른 무료 모델로 폴백하도록 해 뒀는데, 폴백 대상도 429를 받았다.*

둘 다 "429"라는 같은 얼굴을 하고 있지만, 사실상 **완전히 다른 곳에서 만들어진 429**였다. 하나는 게이트웨이가 스스로 만든 것이고, 하나는 업스트림이 계정 전체에 건 것이다.

---

## **"1. 쿨다운이 에러를 바꿔 놓는다"**
> **1.** *첫 번째는 404, 두 번째는 429.*
→ 답은 `allowed_fails`와 쿨다운에 있었다.

`broken-no-v1`은 `api_base`에서 `/v1`만 뺀 설정이다. 일부러 두 번 연속 호출했다.

<figure style="text-align: center;">
  <img
    src="/assets/img/posts/2026-09-26-litellm-gateway-in-front-of-orca-router/gw-broken-terminal.png"
    alt="api_base 에 /v1 이 없을 때의 404 와, 바로 다음 호출의 429 cooldown"
    style="border-radius: 8px;">
  <figcaption style="margin-top: 0.5rem; font-size: 0.95rem; color: #666;">
    첫 호출은 404. 두 번째는 같은 설정인데 429 all_deployments_in_cooldown
  </figcaption>
</figure>

첫 번째 에러는 예상대로다. LiteLLM이 `https://api.orcarouter.ai/chat/completions`를 호출했고, 그 주소에는 API가 없으니 Orca Router **웹사이트의 404 HTML 페이지**가 그대로 에러 메시지에 담겨 왔다. `OpenAIException - <!doctype html>`로 시작하는 에러를 보면 `api_base`부터 의심하면 된다.

두 번째 에러가 재밌다. 같은 요청인데 404가 아니라 **429 `all_deployments_in_cooldown`**이다. `allowed_fails: 1`로 설정했기 때문에 한 번 실패한 배포를 30초 동안 쿨다운에 넣었고, 그 그룹에 다른 배포가 없으니 "쓸 수 있는 배포가 없다"가 된 것이다.

> **쉽게 말하면** 쿨다운은 **방금 실수한 직원을 30초 동안 쉬게 하는 것**이다. 업스트림이 아플 때 계속 두드리지 않으려는 보호 장치다. 문제는 직원이 아픈 게 아니라 **주소를 잘못 적어 준 것**(설정 실수)이어도 똑같이 쉬게 한다는 점이다. 그래서 두 번째부터는 "직원이 없다"는 다른 에러가 보인다.
{: .prompt-tip }

> 운영 중에 "처음엔 404였는데 지금은 429가 나요"라는 보고를 받으면, 원인은 404 쪽이다. 429는 게이트웨이가 스스로 만든 결과다.
> 쿨다운은 진짜 장애에서 업스트림을 보호하는 장치지만, 설정 실수를 다른 에러로 덮어 버리기도 한다.
{: .prompt-warning }

---

## **"2. 무료 한도는 계정 단위다"**
> **2.** *폴백 대상인 무료 모델도 429를 받았다.*
→ 답은 Orca Router 무료 티어의 카운터가 **모델이 아니라 계정에 하나**라는 데 있었다.

무료 모델의 한도는 1편에서 확인한 대로 결제 이력이 없으면 **분당 10회**다. 넘기면 429가 온다. 그래서 질문 C대로 config에 이렇게 적어 뒀다.

```yaml
fallbacks: [{"deepseek-flash-free": ["glm-flash-free"]}]
```

"DeepSeek 무료가 429면 GLM 무료로 넘기자." 그럴듯했다. 12번 연속으로 쏴 봤다.

> **쉽게 말하면** 폴백은 **대타**다. 주전이 못 뛰면 대타가 나간다. 그런데 대타가 주전과 **같은 출전 횟수 제한을 나눠 쓰고 있다면** 주전이 한도를 다 쓴 순간 대타도 못 뛴다. 이 실험이 정확히 그 경우였다.
{: .prompt-tip }

<figure style="text-align: center;">
  <img
    src="/assets/img/posts/2026-09-26-litellm-gateway-in-front-of-orca-router/gw-burst-terminal.png"
    alt="12회 연속 호출: 11번째까지 성공, 12번째 429, 폴백도 429"
    style="border-radius: 8px;">
  <figcaption style="margin-top: 0.5rem; font-size: 0.95rem; color: #666;">
    #12 에서 429. LiteLLM 로그: Fallback to glm-flash-free also failed: RateLimitError
  </figcaption>
</figure>

11번째까지 성공하고 12번째에서 429가 났다. 그리고 **폴백 대상인 GLM 무료 모델도 같은 429**를 받았다. 업스트림 에러 메시지가 이유를 알려 준다.

```
Free model capacity is limited right now. Retry shortly, or add credits for higher,
more stable limits: https://www.orcarouter.ai/console/billing
```

음… 무료 티어의 분당 한도가 **모델별이 아니라 계정 단위**인 것 같았다. 추측으로 끝내기 싫어서 일일 한도가 초기화된 뒤 게이트웨이 없이 Orca Router에 직접 확인해 봤다. GLM 무료 모델만 10번 호출하고, DeepSeek 무료 모델을 처음으로 1번 호출했다.

<figure style="text-align: center;">
  <img
    src="/assets/img/posts/2026-09-26-litellm-gateway-in-front-of-orca-router/cross-model-limit-terminal.png"
    alt="GLM 무료 10회 뒤 DeepSeek 무료 첫 호출이 429"
    style="border-radius: 8px;">
  <figcaption style="margin-top: 0.5rem; font-size: 0.95rem; color: #666;">
    DeepSeek 은 한 번도 안 불렀는데 첫 호출부터 429. 카운터가 모델이 아니라 계정에 붙어 있다
  </figcaption>
</figure>

DeepSeek 무료 모델은 그 분에 한 번도 부르지 않았는데 첫 호출부터 429였다. 카운터는 계정에 하나다. DeepSeek 무료로 10번을 쓰면 GLM 무료도 같이 막히고, 그 반대도 같다. 그러니 무료 → 무료 폴백은 설정은 맞아도 효과가 없다.

폴백이 의미가 있으려면 **한도를 따로 세는 대상**이어야 한다. 무료 → 유료(같은 계정이라도 유료는 한도가 다름), 또는 다른 공급자다. 1편에서 Orca Router 문서가 "무료 모델은 폴백 체인의 대상으로 넣을 수 없다"고 한 것도 같은 맥락이다.

**아래는 원인 분석을 끝낸 뒤 그린 다이어그램이다.**

```mermaid
sequenceDiagram
    participant App as 앱
    participant GW as LiteLLM 라우터
    participant DS as deepseek-flash-free
    participant GLM as glm-flash-free
    participant Q as Orca Router 무료 한도<br/>(계정당 10 RPM)

    App->>GW: #12 /chat/completions
    GW->>DS: 호출
    DS->>Q: 카운트 11 → 초과
    Q-->>DS: 429
    DS-->>GW: RateLimitError
    Note over GW: num_retries: 0 → 즉시 폴백
    GW->>GLM: 호출 (폴백)
    GLM->>Q: 같은 계정, 같은 카운터
    Q-->>GLM: 429
    GLM-->>GW: RateLimitError
    GW-->>App: 429 (Fallback to glm-flash-free also failed)
    Note over App,Q: 폴백은 동작했다. 대상이 같은 한도를 나눠 쓴 게 문제
```

LiteLLM 입장에서는 정확히 설정대로 움직였다. 문제는 내가 폴백 대상을 고른 기준이었다. 게이트웨이의 폴백 설정을 볼 때는 "이 두 배포가 같은 한도를 공유하는가"를 먼저 물어야 한다.

---

## **"1편의 앱을 붙여보자"**

이제 진짜 목적이다. 1편의 스트리밍 프록시를 게이트웨이 뒤로 보낸다. 코드는 한 줄도 바꾸지 않고 환경변수만 바꾼다.

```bash
# 앱 전용 가상 키 (모델 제한 + 예산 $0.01)
curl http://localhost:4000/key/generate \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"max_budget": 0.01, "key_alias": "spring-sse-sample", "models": ["deepseek-flash-free"]}'

ORCA_BASE_URL=http://localhost:4000/v1 \
ORCA_MODEL=deepseek-flash-free \
ORCA_ROUTER_API_KEY=sk-...(위에서 받은 가상 키) \
SERVER_PORT=8090 ./gradlew :spring-sse-sample:bootRun
```

| 환경변수 | 1편 | 2편 |
|----------|-----|-----|
| `ORCA_BASE_URL` | `https://api.orcarouter.ai/v1` | `http://localhost:4000/v1` |
| `ORCA_MODEL` | `deepseek/deepseek-v4-flash-free` | `deepseek-flash-free` (config의 model_name) |
| `ORCA_ROUTER_API_KEY` | Orca Router 키 | **LiteLLM 가상 키** |

앱은 이제 Orca Router 키를 모른다. 데모 페이지에서 전송을 눌렀다.

<figure style="text-align: center;">
  <img
    src="/assets/img/posts/2026-09-26-litellm-gateway-in-front-of-orca-router/demo-via-gateway.png"
    alt="게이트웨이를 거쳐 정상 스트리밍되는 데모 페이지"
    style="border-radius: 8px; border: 1px solid #e5e7eb;">
  <figcaption style="margin-top: 0.5rem; font-size: 0.95rem; color: #666;">
    1편과 같은 화면. 뒤에 LiteLLM 이 끼어 있다는 걸 앱도 브라우저도 모른다
  </figcaption>
</figure>

서버 로그와 게이트웨이 쪽 기록을 나란히 놓으면 이렇다.

```
# Spring 로그
[stream] ttft=1653ms elapsed=2847ms chunks=192 content=130 reasoning=59 error=-

# LiteLLM 스팬드 로그 (최신 1건)
model=openai/deepseek/deepseek-v4-flash-free  prompt=98  completion=199  spend=0.0001529  key_alias=spring-sse-sample

# 앱 키 누적
{"key_alias":"spring-sse-sample","spend":0.00019382,"max_budget":0.01,"models":["deepseek-flash-free"]}
```

앱은 base URL만 바꿨는데, 게이트웨이에는 "spring-sse-sample 키가 이 요청에 $0.0001529를 썼고 누적 $0.00019382"가 남았다. 이 키의 예산 $0.01이 다 차면 앱은 위에서 본 `budget_exceeded`를 받게 된다. 1편에서 만든 `event: error` 처리가 그때 일한다.

---

## **"/metrics에는 무엇이 찍히나"**

`callbacks: ["prometheus"]`를 켜 두었다. `/metrics`는 `/metrics/`로 307 리다이렉트되니 `curl -L`이 필요하다.

```
$ curl -sL http://localhost:4000/metrics | grep -E "^litellm_" | sed 's/{.*//' | sort | uniq -c | sort -rn
  36 litellm_request_total_latency_metric_bucket
  36 litellm_llm_api_latency_metric_bucket
  18 litellm_llm_api_time_to_first_token_metric_bucket
  15 litellm_deployment_latency_per_output_token_bucket
   3 litellm_proxy_total_requests_metric_total
   3 litellm_deployment_total_requests_total
   3 litellm_deployment_state
   ...
```

요청 수, 배포별 상태, 지연 히스토그램, 그리고 **TTFT 히스토그램**(`litellm_llm_api_time_to_first_token_metric`)이 있다. 1편에서 파이썬 스크립트로 직접 재던 값이 게이트웨이에서는 기본으로 나온다.

> **쉽게 말하면** `/metrics`는 **자동차 계기판**이다. 속도(요청 수), 엔진 온도(에러율), 연료(비용)를 숫자로 계속 보여 주고, Prometheus가 그걸 주기적으로 읽어 그래프로 그린다. 1편에서는 이 계기판이 없어서 직접 스톱워치를 들었던 셈이다.
{: .prompt-tip }

> 문서 일부에는 Prometheus 콜백이 엔터프라이즈 기능으로 적혀 있다. 내가 쓴 `main-latest` 오픈소스 이미지에서는 위처럼 동작했다. 버전에 따라 다를 수 있으니 띄운 뒤 직접 확인하는 편이 안전하다.
{: .prompt-info }

---

## **"게이트웨이를 도입할 때"**

아래를 반드시 기억해야 한다.

| 구간 | 확인할 것 |
|------|-----------|
| 설정 | `openai/` 프리픽스, `api_base`에 `/v1`, 키는 `os.environ/` |
| 비용 | 무료·정액 모델에는 유료 단가를 가상으로 붙여 집계 |
| 예산 | 예산 검사는 요청 전. 한 번은 넘긴다. 상태 코드보다 `type: budget_exceeded`로 분기 |
| 예산 | `/key/info`의 `spend`는 몇 초 늦게 반영 |
| 폴백 | 폴백 대상이 원본과 **같은 한도를 공유하는지** 먼저 확인 |
| 쿨다운 | `allowed_fails`가 설정 실수를 429로 바꿔 보여 줄 수 있음. 첫 에러를 찾을 것 |
| 앱 | 앱은 게이트웨이 주소와 가상 키만 안다. 업스트림 키는 게이트웨이 환경변수에만 |

**결론적으로,** 게이트웨이는 문제를 없애 주는 게 아니라 문제가 생기는 자리를 한 곳으로 모아 준다. 그 한 곳에 로그와 비용과 한도가 같이 있다는 것이 도입의 진짜 이유다.

---

## **"느낀 점"**

한 겹이 늘면 확인할 곳도 한 곳 는다.

두 번 넘어졌는데, 둘 다 게이트웨이의 버그가 아니었다. 쿨다운은 설계대로 움직였고, 폴백도 설계대로 움직였다. 내가 모르고 있던 건 "쿨다운이 첫 에러를 덮는다"는 것과 "무료 한도는 계정에 하나"라는 사실이었다.

특히 폴백은 조심해야 한다.

"안 되면 다른 데로 넘긴다"는 말은 듣기 좋지만, 넘어가는 곳이 같은 지갑을 쓰고 있으면 아무 소용이 없다.

- 게이트웨이의 `fallbacks`를 적을 때는 "두 배포가 같은 한도를 공유하는가"부터 묻자.
- `allowed_fails`와 `cooldown_time`은 운영 값으로 조정하자. 실험용 `1`과 `30`은 첫 에러를 너무 빨리 숨긴다.
- 무료·정액 모델도 가상 단가를 붙여 두자. 0원 장부는 장부가 아니다.

*"429가 난다"는 보고를 받으면 그 429를 누가 만들었는지부터 물어봐야 한다.*

**쿨다운의 429 + 업스트림의 429**, 이 둘이 같은 얼굴로 섞이면

**진짜 원인이 한참 뒤로 숨는다는 걸** 이번에 제대로 배웠다.

---

## **"결론 요약"**

- **앱은 base URL과 가상 키만 바꿨고 코드는 그대로**다. 업스트림 키, 비용, 예산, 폴백은 게이트웨이가 가져갔다.
- **무료 모델도 가상 단가를 붙이면 비용이 집계**되고, 그 계산은 토큰 수로 검산이 된다.
- **예산 검사는 요청 전에 하므로 한 번은 넘긴다.** 상태 코드보다 `type: budget_exceeded`로 분기하자.
- **`/v1` 누락은 404이고, 그다음부터는 쿨다운 때문에 429로 보인다.** 첫 에러를 찾아야 한다.
- **무료 → 무료 폴백은 소용이 없다.** Orca Router 무료 한도는 계정 단위다. 폴백 대상은 한도를 따로 세는 곳이어야 한다.
- 게이트웨이는 문제를 없애는 게 아니라 **문제가 생기는 자리를 한 곳으로 모아 주는 것**이다.

---

## **"샘플 코드"**
이 코드는 테스트 편의를 위해 작성된 샘플이다. compose와 config.yaml, 그리고 첫 호출·스트리밍·연속 호출·예산 키·스팬드 로그·계정 단위 한도 확인 스크립트가 들어 있다.
> [litellm-gateway-sample](https://github.com/rojae/spring-sample/tree/main/litellm-gateway-sample)
> [spring-sse-sample](https://github.com/rojae/spring-sample/tree/main/spring-sse-sample) (1편 앱, 변경 없음)

---

## **"참고한 내용들"**

### 이 글에서 쓴 LiteLLM 설정

| 설정 | 위치 | 값 | 의미 |
|------|------|-----|------|
| `model: openai/<id>` | `litellm_params` | - | OpenAI 호환 업스트림을 `openai` 프로바이더 코드로 호출 |
| `api_base` | `litellm_params` | `https://api.orcarouter.ai/v1` | 뒤에 `/chat/completions`만 붙는다. `/v1` 필수 |
| `api_key` | `litellm_params` | `os.environ/...` | 컨테이너 환경변수 참조 |
| `input_cost_per_token`, `output_cost_per_token` | `model_info` | 토큰당 달러 | 무료·정액 모델의 가상 단가 |
| `fallbacks` | `litellm_settings` | `[{"A": ["B"]}]` | A 그룹 실패 시 B 그룹으로 |
| `num_retries` | `litellm_settings` / `router_settings` | `0` | 같은 배포 재시도 횟수. 0이면 바로 폴백 |
| `allowed_fails` | `litellm_settings` | `1` | 이 횟수만큼 실패하면 배포를 쿨다운 |
| `cooldown_time` | `litellm_settings` | `30` | 쿨다운 유지 시간(초) |
| `callbacks: ["prometheus"]` | `litellm_settings` | - | `/metrics` 노출 |
| `max_budget` | `/key/generate` | 달러 | 키별 누적 예산. 요청 전에 검사 |

### 이 글에서 만난 에러

| 상태 | `type` | 누가 만들었나 | 원인 |
|------|--------|---------------|------|
| 404 | `invalid_request_error` | 업스트림(Orca Router 웹사이트) | `api_base`에 `/v1` 누락 |
| 429 | `all_deployments_in_cooldown` | **LiteLLM** | 직전 실패로 배포가 쿨다운 중 |
| 429 | `RateLimitError` | 업스트림 | 무료 티어 분당 한도(계정 단위) 초과 |
| 422 | `budget_exceeded` | **LiteLLM** | 가상 키의 `max_budget` 초과 (`main-latest` 기준) |

### Reference Links

#### LiteLLM

- [OpenAI-compatible endpoints](https://docs.litellm.ai/docs/providers/openai_compatible)
- [Custom pricing](https://docs.litellm.ai/docs/proxy/custom_pricing)
- [Proxy config: fallbacks, cooldown](https://docs.litellm.ai/docs/proxy/configs)
- [Virtual keys and budgets](https://docs.litellm.ai/docs/proxy/users)
- [Prometheus metrics](https://docs.litellm.ai/docs/proxy/prometheus)

#### Orca Router

- [Free models](https://docs.orcarouter.ai/routing/free-models)
- [DeepSeek V4 Flash (Free)](https://www.orcarouter.ai/models/deepseek/deepseek-v4-flash-free)
