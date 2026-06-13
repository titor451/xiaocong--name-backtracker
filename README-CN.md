# Name Backtracker

UTF-8 游戏角色名生成器 —— 基于回溯剪枝的三条约束优化。

## 背景

受 B 站视频 [BV1qUJ76wEp7](https://www.bilibili.com/video/BV1qUJ76wEp7/) 启发。
原视频在 UTF-8 空间穷举 1~8 字角色名，搜索空间达 4.19×10⁴¹。
本方案通过三条剪枝约束，将空间缩减至原始大小的 1.38%。

## 约束（剪枝规则）

1. **不含标点符号与运算符** — Unicode 分类 P*, S*
2. **不含特殊字母及其变体** — 仅保留 ASCII 拉丁 (A-Z a-z) + CJK 表意文字
3. **不含全角字符** — U+FF00~U+FFEF, East Asian Width = F

## 效果

| 指标 | 值 |
|------|------|
| 合法字符池 | 93,388 字 |
| 原始搜索空间 | 4.19 × 10⁴¹ |
| 剪枝后空间 | 5.79 × 10³⁹（缩减至 1.38%）|

## 用法

```bash
python backtracking.py
```

默认配置（可在文件顶部修改）：
- 名称长度：1~8 字
- 预览数量：200 条

### 自定义配置

```python
# 在文件顶部修改
MIN_LEN = 1          # 最少字数
MAX_LEN = 8          # 最多字数
PREVIEW_LIMIT = 200  # 预览条数（0 = 不限制 → 会跑很久）
```

### 自定义剪枝

在 `backtrack_with_pruning()` 的 `for ch in pool:` 循环内，可插入额外剪枝：

```python
for ch in pool:
    # 示例：不允许连续两个相同字符
    # if current and ch == current[-1]:
    #     continue
    current.append(ch)
    dfs(current)
    current.pop()
```

## 文件结构

```
├── backtracking.py     # 主程序
├── README.md           # 本文件
├── LICENSE             # MIT 许可证
└── .gitignore          # Git 忽略规则
```

## 原理

### 回溯生成

深度优先搜索 + 三层剪枝：
1. **深度剪枝**：达 MAX_LEN 后不再递归
2. **数量剪枝**：达 limit 后提前终止全量搜索
3. **可扩展剪枝**：在字符循环中插入任意自定义规则

### 搜索空间

```
长度 1: 93,388¹  = 9.34×10⁴
长度 2: 93,388²  = 8.72×10⁹
长度 3: 93,388³  = 8.14×10¹⁴
...
长度 8: 93,388⁸  = 5.79×10³⁹
合计:            5.80×10³⁹
```

## 许可证

MIT
