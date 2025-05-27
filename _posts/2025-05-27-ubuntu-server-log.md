---
title: 우분투 서버 로그 확인 방법 - 간단하게 정리
author: rojae
date: 2025-05-27 03:30:00 +0900
categories: [infra]
tags: [infra, ubuntu]
mermaid: true
image:
  path: /assets/img/posts/2025-05-27-ubuntu-server-log/ubuntu.png
---
# 우분투 서버 로그 확인 방법

우분투에서는 대부분의 로그 파일이 `/var/log` 디렉토리에 저장됩니다. 아래는 자주 확인하는 로그 파일들과 명령어입니다.

---

## 📄 시스템 로그 (`/var/log/syslog`)

시스템 전반의 일반 로그를 확인할 수 있습니다.

```bash
cat /var/log/syslog
```

---

## 🧩 커널 로그 (`/var/log/kern.log`)

커널 관련 메시지를 확인하려면 다음 명령어를 사용합니다.

```bash
cat /var/log/kern.log
```

---

## 🔐 인증 로그 (`/var/log/auth.log`)

로그인, sudo 등 인증 관련 로그를 확인합니다.

```bash
cat /var/log/auth.log
```

---

## 🌐 Nginx 로그 (`/var/log/nginx/`)

웹 서버인 Nginx의 로그는 다음 경로에서 확인합니다.

```bash
cd /var/log/nginx/

cat access.log  # 접근 로그
cat error.log   # 오류 로그
```

---

## 🌍 Apache 로그 (`/var/log/apache2/`)

Apache 로그도 유사하게 확인할 수 있습니다.

```bash
cd /var/log/apache2/

cat access.log  # 접근 로그
cat error.log   # 오류 로그
```

---

## 🛠 사용자 지정 로그

일부 서비스는 전용 디렉토리에 로그를 저장합니다. 예:

```bash
/var/log/mysql/       # MySQL 로그
/var/log/docker.log   # Docker 로그
```

---

> 로그를 실시간으로 확인하고 싶다면 `tail -f` 명령어를 활용하세요:

```bash
tail -f /var/log/syslog
```

---
