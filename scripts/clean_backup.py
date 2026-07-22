#!/usr/bin/env python3
"""清空 backup.sql 数据行，仅保留表结构 + 索引 + 注释"""
import re

with open("amber/backup.sql", "r", encoding="utf-8") as f:
    lines = f.readlines()

out = []
in_copy = False
for line in lines:
    if line.startswith("COPY ") and "FROM stdin" in line:
        in_copy = True
        out.append(line)  # keep COPY header
        continue
    if in_copy:
        if line.strip() == "\\.":
            in_copy = False
            out.append(line)  # keep \. terminator
        continue
    out.append(line)

result = "".join(out)
with open("amber/backup.sql", "w", encoding="utf-8") as f:
    f.write(result)

print(f"原 {len(lines)} 行 → 现 {len(out)} 行")
print(f"删除 {len(lines) - len(out)} 行数据")
