import io
from pathlib import Path

files = [
    "00_README_总览与唯一主线.md",
    "README_工作区导航.md",
    "补正实验包/README.md",
    "补正实验包/开始执行.md",
    "第4-5章_判别与恢复/有害更新判别_计划核查与执行准备_20261118.md",
    "工程化/README.md",
    "工程化/REPRODUCE.md",
    "工程化/工程化路线_20261118.md",
    "工程化/W0_BASELINE.md",
    "工程化/W4b_接入记录_20261119.md",
    "00_总览/交接_新对话_20261118.md",
    "00_总览/成果总览_20261118.md",
]
pairs = [
    ("279/300", "285/300"),
    ("剩 21（D 1 + G 20）", "剩 15（D 1 + G 14）"),
    ("剩 **21**（D 1 + G 20）", "剩 **15**（D 1 + G 14）"),
    ("G 池 20（2026-11-19 追加，未使用）", "G 池 20（2026-11-19 追加，W4c 已用 6，剩 14）"),
    ("G 20（未用）", "G 20（W4c 用 6）"),
    ("W4c 已完成（0 P0）", "W4c 已完成（清单 0 P0 + 退化段 6 P0）"),
    ("W4c（三算法清单，0 P0）", "W4c（三算法清单 + 退化段，6 P0）"),
    ("W4c 为 0 P0 清单", "W4c 清单 0 P0 + 退化段 6 P0"),
    ("W4c 已完成（0 P0），W5", "W4c 已完成（清单 0 P0 + 退化段 6 P0），W5"),
    ("W4c 已完成（0 P0）；", "W4c 已完成（清单 0 P0 + 退化段 6 P0）；"),
]
for name in files:
    p = Path(name)
    s = p.read_text(encoding="utf-8")
    orig = s
    for a, b in pairs:
        s = s.replace(a, b)
    if s != orig:
        p.write_text(s, encoding="utf-8", newline="\n")
        print("updated", name)
