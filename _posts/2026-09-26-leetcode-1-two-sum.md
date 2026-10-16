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

제약은 길이 2 이상 10⁴ 이하, 원소와 `target`은 -10⁹ 이상 10⁹ 이하다. 그래서 `target - nums[i]`는 `int` 범위를 넘지 않고, 이중 반복문도 최대 5×10⁷번 비교라 시간 초과는 아니다. 느린 것이지 틀린 것은 아니다.

## 첫 접근

이중 반복문으로 모든 쌍을 더해 봤다. 답은 맞는데 배열이 길어지면 `O(n²)`이라 느리다. "이미 본 수를 기억해 두면 다시 훑을 필요가 없지 않나"에서 막혔다. 기억을 어디에 둘지 몰랐다.

## 핵심 관찰

**지금 보는 수 `x`의 짝은 `target - x`다. 짝을 앞에서 봤는지만 알면 된다.**

왜 앞만 보면 되나. 답이 되는 두 인덱스를 `j < i`라고 하면, `i`번째를 볼 때 `nums[j]`는 이미 지나갔다. 지나간 값을 전부 맵에 넣어 두면 `i`에서 `target - nums[i]`로 `j`를 바로 찾는다. 답이 정확히 하나이므로 처음 찾은 쌍이 그 답이다. 지금 수는 짝을 찾은 뒤에 넣으니 같은 원소를 두 번 쓸 일도 없다.

`[3, 2, 4]`, `target = 6`으로 따라가면 이렇다. 첫 칸에서 짝이 자기 자신(3)인데도 맵이 비어 있어 같은 원소를 쓰지 않는다.

| i | nums[i] | 짝 (target - x) | 맵에 있나 | 맵 (값 → 인덱스) |
|---|---|---|---|---|
| 0 | 3 | 3 | 없음 → 3을 기억 | {3 → 0} |
| 1 | 2 | 4 | 없음 → 2를 기억 | {3 → 0, 2 → 1} |
| 2 | 4 | 2 | **있음 → 답 [1, 2]** | - |

## 코드

```java
public int[] twoSum(int[] nums, int target) {
    Map<Integer, Integer> seen = new HashMap<>(); // 값 -> 인덱스
    for (int i = 0; i < nums.length; i++) {
        int need = target - nums[i];             // 지금 수의 짝
        if (seen.containsKey(need)) {
            // 앞에서 본 짝이 있으면 끝
            return new int[] { seen.get(need), i };
        }
        seen.put(nums[i], i);                    // 없으면 기억
    }
    throw new IllegalArgumentException("답이 없다");
}
```

## 복잡도

| 시간 | 공간 |
|------|------|
| O(n) (해시 평균) | O(n) |

`HashMap` 조회가 평균 O(1)이라는 전제다. 충돌이 심하면 더 걸리지만 이 문제의 입력에서는 신경 쓸 일이 없다.

## 경계와 확인

- `[3, 3]`, `target = 6` 같은 중복 값. 지금 수를 기억하기 전에 짝을 먼저 찾으니 같은 인덱스를 두 번 쓰지 않는다. 같은 값이 여러 번 나오면 `put`이 뒤 인덱스로 덮어쓰지만, 짝을 찾는 쪽은 앞에서 본 유효한 인덱스를 돌려주므로 답은 그대로 맞다.
- 이 글의 확인은 로컬 실행 기준이다. `[2, 7, 11, 15], 9 → [0, 1]`, `[3, 2, 4], 6 → [1, 2]`, `[3, 3], 6 → [0, 1]`, 답이 없는 `[1, 2], 9 → 예외`를 확인했다.
- 다시 풀면 `containsKey` 뒤에 `get`을 또 부르지 말고 `Integer j = seen.get(need)` 한 번으로 줄이겠다. 조회가 한 번 줄 뿐 복잡도는 같다.

## 가져갈 것

- 합이 정해진 쌍을 찾는 문제는 "짝을 맵에 기억"으로 한 번에 끝난다. 차가 정해진 쌍도 같은 틀이다.
- 입력을 정렬해도 되는 문제라면 정렬 뒤 투포인터도 후보다. 인덱스를 돌려줘야 하는 이 문제에서는 정렬이 인덱스를 흐트러뜨리므로 맵이 편하다.
