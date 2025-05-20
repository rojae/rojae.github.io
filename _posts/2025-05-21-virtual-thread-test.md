---
title: Java Virtual Thread Advantage
author: rojae
date: 2025-05-21 00:00:00 +0900
categories: [backend]
tags: [java, virtual-threads]
---

> 참고) 본 글은 깃허브 블로그 초기 셋팅을 위해서, 테스트로 작성된 글입니다.

## Java Virtual Thread Advantage
### Sequential Code (순차적인 코드)
```java
data1 = fetchFromDatabase(request);
data2 = fetchFromDatabase(request);
combineData = comfineDataProcess(data1, data2);
sendData(combineData);
```
- 이 부분은 blocking이 발생하여 이슈가 있을 수 있는 요소가 있다.

### non-blocking code (callback code)
```java
fetchFromDatabase(dbUrl, databaseCallback(data1){
    fetchFromService1(url1, restCallback(data2)){
        combindData = processAndCombind(data1, data2);
        sendData(combinedData);
    }
}
```
- callback, pipeline 스타일에 대해서는 문제가 다소 있다.
- 확장성이나 유지보수를 위해서 추가적으로 작업을 진행할 때에 '가독성'이 떨어져서 코드의 복잡성이 더욱 증가한다.

### Virtual Thread (가상 스레드 사용)
```java
data1 = fetchFromDatabase(request);
data2 = fetchFromDatabase(request);
combineData = comfineDataProcess(data1, data2);
sendData(combineData);
```
- 소스코드는 동일하지만, excutor 부분만 바꿔서 사용이 가능하다.
- 순차적인 소스코드 유지가 가능하다.

### Virtual Thread Advantage
#### Light Weight Thread (extends the thread class)
- Fast Cretion Time (생성이 빠름)
- Exhibits same behavior Platform Threads (플랫폼 쓰레드와 동일한 역할을 수행)
- Scales to milions of instance (백만개 단위의 쓰레드 생성이 가능함)

#### Advantages
- No need Thread Pool (쓰레드 풀이 필요하지 않음)
- Can block on IO with no scalability issue (IO와 확장성의 이슈가 없이도 blcoking 소스코드 작성이 가능하다.)
- Optimal Concurrency (동시성의 극대화)
- Code can still be __Sequential__ (소스코드이 순차적)
- Existing code will benefit from using Virtual Thread (기존에 작성된 코드를 유지할 수 있음)
- Combine With Futures and CompletableFuture (Fetures, CompletableFeture을 함께 결합하여 사용이 가능하다)


