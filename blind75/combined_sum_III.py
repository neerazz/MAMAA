from typing import List, Dict


class Solution:
    def combinationSum3(self, k: int, n: int) -> List[List[int]]:
        memo : Dict[str, List[List[int]]] = {}
        return self.helper(k, n, 1, 0, memo)

    def helper(self, k, n, start, sum_so_far, memo):
        if k == 0 and sum_so_far == n:
            return [[]]
        if k < 0 or n <0 or start > 9:
            return []
        if k == 0 or sum_so_far > n:
            return []
        key = f"{k}, {n}, {start}, {sum_so_far}"
        if key in memo:
            return memo[key]
        res = []
        for i in range(start, 10):
            cur_sum = sum_so_far + i
            if cur_sum <= n:
                pre_res = self.helper(k-1, n, i+1, cur_sum, memo)
                for r in pre_res:
                    res.append([i] + r)
            else:
                break
        memo[key] = res
        return res
                
                
# Example usage:
sol = Solution()
result = sol.combinationSum3(9,45)
print(result) 