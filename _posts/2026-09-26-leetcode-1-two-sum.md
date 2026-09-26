---
title: LeetCode 1. Two Sum - (한 번 훑으면서 짝을 기억하기)
author: rojae
date: 2026-09-26 13:00:00 +0900
published: false
categories: [problem-sloving]
tags: [ps, leetcode, hash-map, array]
image:
  path: /assets/img/posts/2025-09-08-ps-start-with-leetcode/leetcode.png
---
> [LeetCode 1. Two Sum](https://leetcode.com/problems/two-sum/) · Easy
{: .prompt-info }

## 문제

정수 배열 `nums`와 목표값 `target`이 주어진다. 두 수를 더해 `target`이 되는 인덱스 쌍을 하나 돌려준다. 답은 정확히 하나 있고, 같은 원소를 두 번 쓸 수 없다.

## 첫 접근

이중 반복문으로 모든 쌍을 더해 봤다. 답은 맞는데 배열이 길어지면 `O(n²)`이라 느리다. "이미 본 수를 기억해 두면 다시 훑을 필요가 없지 않나"에서 막혔다. 기억을 어디에 둘지 몰랐다.

## 핵심 관찰

**지금 보는 수 `x`의 짝은 `target - x`다. 짝을 앞에서 봤는지만 알면 된다.**

## 코드

```java
public int[] twoSum(int[] nums, int target) {
    Map<Integer, Integer> seen = new HashMap<>();   // 값 -> 인덱스
    for (int i = 0; i < nums.length; i++) {
        int need = target - nums[i];               // 지금 수의 짝
        if (seen.containsKey(need)) {
            return new int[] { seen.get(need), i }; // 앞에서 본 짝이 있으면 끝
        }
        seen.put(nums[i], i);                      // 없으면 지금 수를 기억
    }
    throw new IllegalArgumentException("답이 없다");
}
```

## 복잡도

| 시간 | 공간 |
|------|------|
| O(n) | O(n) |

## 놓친 것, 다시 풀면

- `[3, 3]`, `target = 6` 같은 중복 값. 지금 수를 기억하기 전에 짝을 먼저 찾으니 같은 인덱스를 두 번 쓰지 않는다.
- 다시 풀면 `containsKey` 뒤에 `get`을 또 부르지 말고 `Integer j = seen.get(need)` 한 번으로 줄이겠다.
