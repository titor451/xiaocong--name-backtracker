import unicodedata
import sys
import time
from typing import List, Optional

# ======================== 配置 ========================
MIN_LEN = 1          # 最小名称长度
MAX_LEN = 8          # 最大名称长度
PREVIEW_LIMIT = 0  # 最大生成数量（0表示不限制）

# ======================== 第1步：构建合法字符池（应用三条规则） ========================

def is_punctuation_or_operator(ch: str) -> bool:
    """规则1：标点符号与运算符 (Unicode 分类 P*, S*)"""
    cat = unicodedata.category(ch)
    return cat.startswith("P") or cat.startswith("S")

def is_special_letter_variant(ch: str) -> bool:
    """规则2：特殊字母变体（非ASCII拉丁 + 非CJK的字母）"""
    cat = unicodedata.category(ch)
    if not cat.startswith("L"):
        return False
    cp = ord(ch)
    name = unicodedata.name(ch, "")
    # 白名单：ASCII 拉丁字母 (A-Z a-z)
    if cp < 0x80 and "LATIN" in name:
        return False
    # 白名单：CJK 表意文字（汉字、部首等）
    if any(kw in name for kw in ("CJK", "IDEOGRAPH", "KANGXI", "RADICAL")):
        return False
    return True

def is_fullwidth(ch: str) -> bool:
    """规则3：全角字符（U+FF00~U+FFEF 或 East Asian Width = 'F'）"""
    cp = ord(ch)
    if 0xFF00 <= cp <= 0xFFEF:
        return True
    try:
        return unicodedata.east_asian_width(ch) == "F"
    except ValueError:
        return False

def is_control_or_whitespace(ch: str) -> bool:
    """辅助：控制字符与空白字符（总是禁止）"""
    cat = unicodedata.category(ch)
    return cat in ("Cc", "Cf", "Cs", "Co", "Cn") or cat.startswith("Z")

def is_valid_character(ch: str) -> bool:
    """三条规则 + 基本控制字符过滤"""
    if is_control_or_whitespace(ch):
        return False
    if is_punctuation_or_operator(ch):
        return False
    if is_fullwidth(ch):
        return False
    if is_special_letter_variant(ch):
        return False
    return True

# 扫描范围（根据实际需求可调整，这里覆盖常用汉字范围）
SCAN_RANGES = [
    (0x0021, 0x007E),       # Basic Latin（不含空格）
    (0x2E80, 0x2EFF),       # CJK Radicals Supplement
    (0x2F00, 0x2FDF),       # Kangxi Radicals
    (0x3400, 0x4DBF),       # CJK Extension A
    (0x4E00, 0x9FFF),       # CJK Unified Ideographs
    (0xF900, 0xFAFF),       # CJK Compatibility Ideographs
    (0x20000, 0x2A6DF),     # CJK Extension B
    (0x2A700, 0x2B73F),     # Extension C
    (0x2B740, 0x2B81F),     # Extension D
    (0x2B820, 0x2CEAF),     # Extension E
    (0x2CEB0, 0x2EBEF),     # Extension F
    (0x30000, 0x3134F),     # Extension G
]

def build_valid_pool() -> List[str]:
    """扫描上述范围，收集所有合法字符"""
    pool = []
    for start, end in SCAN_RANGES:
        for cp in range(start, end + 1):
            ch = chr(cp)
            if is_valid_character(ch):
                pool.append(ch)
    pool.sort()
    return pool

# ======================== 第2步：回溯剪枝生成器 ========================

def backtrack_with_pruning(
    pool: List[str],
    min_len: int,
    max_len: int,
    limit: int = 0,
    verbose: bool = False
) -> List[str]:
    """
    使用回溯剪枝生成所有满足长度限制的名称。

    剪枝策略：
      - 深度剪枝：达到 max_len 后不再递归
      - 数量剪枝：达到 limit 后提前终止全部搜索
      - 可扩展：字符循环处可插入自定义剪枝（如去重、禁相邻重复等）

    注意：depth 在 [min_len, max_len] 内时记录结果，
          但记录后不 return（除非达到 max_len），
          从而继续往更深层生长更长的名字。
    """
    results: List[str] = []
    pool_size = len(pool)
    if pool_size == 0:
        return results

    stop_flag = False

    def dfs(current: List[str]) -> None:
        nonlocal stop_flag
        if stop_flag:
            return

        depth = len(current)

        # 当前深度在有效范围内 → 记录
        if min_len <= depth <= max_len:
            name = "".join(current)
            results.append(name)
            # 实时输出：每找到一个合法名字就打印
            if verbose:
                print(f"  [#{len(results):>8}] {name}")
                sys.stdout.flush()
            if limit > 0 and len(results) >= limit:
                stop_flag = True
                return
            # 已达最大长度 → 不继续向下生长
            if depth == max_len:
                return
            # 否则：记录后继续生长（关键：不 return）

        # 深度已达上限 → 无法再生长（兜底保护）
        if depth >= max_len:
            return

        # 遍历字符池，尝试每一个字符
        for ch in pool:
            # ----- 可在此处添加自定义剪枝规则 -----
            # 例：不允许连续两个相同字符
            # if current and ch == current[-1]:
            #     continue
            # ------------------------------------
            current.append(ch)
            dfs(current)
            current.pop()
            if stop_flag:
                return

    dfs([])
    return results

# ======================== 第3步：辅助函数（统计和验证） ========================

def print_pool_stats(pool: List[str]):
    """输出字符池的统计信息"""
    print(f"合法字符总数: {len(pool)}")
    cat_count = {}
    for ch in pool:
        cat = unicodedata.category(ch)
        cat_count[cat] = cat_count.get(cat, 0) + 1
    print("分类统计:")
    for cat, cnt in sorted(cat_count.items()):
        print(f"  {cat}: {cnt}")

def validate_name(name: str) -> bool:
    """验证单个名称是否符合三条规则（用于测试）"""
    for ch in name:
        if is_control_or_whitespace(ch):
            return False
        if is_punctuation_or_operator(ch):
            return False
        if is_special_letter_variant(ch):
            return False
        if is_fullwidth(ch):
            return False
    return True

# ======================== 第4步：主程序示例 ========================

def main():
    print("正在构建合法字符池（应用三条限制）...")
    sys.stdout.flush()
    pool = build_valid_pool()
    print_pool_stats(pool)

    print(f"\n开始回溯剪枝生成名称（长度 {MIN_LEN}~{MAX_LEN}，最多 {PREVIEW_LIMIT} 个，实时输出）...")
    sys.stdout.flush()
    start_time = time.time()
    names = backtrack_with_pruning(pool, MIN_LEN, MAX_LEN, PREVIEW_LIMIT, verbose=True)
    elapsed = time.time() - start_time

    print(f"\n生成完成，共 {len(names)} 个名称，耗时 {elapsed:.3f} 秒")

    # 验证所有生成的名字都合法
    all_valid = all(validate_name(name) for name in names)
    print(f"\n所有生成的名字均符合三条规则: {all_valid}")

    # 搜索空间估计
    pool_size = len(pool)
    total = 0
    for L in range(MIN_LEN, MAX_LEN + 1):
        total += pool_size ** L
    print(f"\n搜索空间估计:")
    print(f"  合法字符池: {pool_size:,}")
    print(f"  搜索空间上界 (1~{MAX_LEN}): {total:.2e}")
    print(f"  原始视频数字: 4.19e41")

if __name__ == "__main__":
    main()
