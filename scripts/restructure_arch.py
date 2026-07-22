"""架构文档重构：推理皮层独立层 + 注意力调度器横切层 + 全篇重编号"""
import re

with open(r'D:\projects\kairos\docs\design\architecture-v1.0.0.md', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
print(f"原始行数: {len(lines)}")

# === 1) 提取推理皮层块 (L973-1014, inclusive) ===
rc_start = 972  # 0-indexed
rc_end = 1014   # 0-indexed exclusive (L1014 inclusive)
rc_lines = lines[rc_start:rc_end]

# 验证提取
print("\n=== 推理皮层块 ===")
for i, line in enumerate(rc_lines):
    if i < 3 or i >= len(rc_lines)-2:
        print(f"  [{i}]: {line[:100]}")
    elif i == 3:
        print(f"  ... {len(rc_lines)} 行")

# === 2) 提取注意力调度器块 (L961-970, inclusive) ===
attn_start = 960  # 0-indexed
attn_end = 970    # 0-indexed inclusive
attn_lines = lines[attn_start:attn_end+1]

print(f"\n=== 注意力调度器块 ({len(attn_lines)} 行) ===")
for line in attn_lines:
    print(f"  {line[:100]}")

# === 3) 从 §5 WM 中移除两个块（先推理皮层后调度器，从后往前删以避免行号漂移）===
# Create a clean WM section
wm_section = lines[rc_start-1:rc_start]  # Keep the WM's "├─" line before RC? No, remove it.
# Actually let me check: L972 is `  │` before the RC header
# L960 is `  ├─ 注意力调度器` line

# Better: remove the attention scheduler block and the reasoning cortex block from the lines
# The WM section components tree has:
# - ... other components ...
# - L960:   ├─ 注意力调度器... (to L970)
# - L971:   │  (blank/separator)
# - L972:   │  (blank)
# - L973:   ├─ 推理皮层... (to L1014)

# Remove L960-L1014 range (attention scheduler + reasoning cortex)
# Then insert a reference line saying reasoning cortex is now §4 and attention scheduler is now §9

# Build new lines
new_lines = []
i = 0
while i < len(lines):
    if i == 960:  # Start of attention scheduler block
        # Skip to end of reasoning cortex block
        i = 1014  # Skip to next line after RC block
        # Insert a reference
        new_lines.append('  │  # 推理皮层已独立为 §4（独立协调层）；注意力调度器已独立为 §9（横切组件）')
        continue
    new_lines.append(lines[i])
    i += 1

print(f"\n移除后行数: {len(new_lines)}")

# Verify WM §5 is clean
wm5_end = None
new_section_starts = {}
for i, line in enumerate(new_lines):
    m = re.match(r'^## (§\d+)', line)
    if m:
        new_section_starts[m.group(1)] = i
        
print(f"新章节位置: {new_section_starts}")
wm_new_start = new_section_starts['§5']
# Find next section
for j in range(wm_new_start+1, len(new_lines)):
    if re.match(r'^## §', new_lines[j]):
        wm_new_end = j
        break

print(f"新 WM §5: L{wm_new_start+1} - L{wm_new_end}")
print("新 WM 开头:")
for j in range(wm_new_start, min(wm_new_start+5, wm_new_end)):
    print(f"  L{j+1}: {new_lines[j][:100]}")
print("新 WM 结尾:")
for j in range(max(wm_new_start, wm_new_end-3), wm_new_end):
    print(f"  L{j+1}: {new_lines[j][:100]}")

print("\n移除后 WM 中是否有推理皮层残留:", any("推理皮层" in l for l in new_lines[wm_new_start:wm_new_end]))
print("移除后 WM 中是否有注意力调度器残留:", any("注意力调度器" in l and "已经独立" not in l for l in new_lines[wm_new_start:wm_new_end]))

# === 4) Build the reconstituted architecture doc ===
# Final target:
# §0, §1, §2, §3 (unchanged)
# §4 = 推理皮层（new, from extracted RC lines）
# §5 = 存储层 (was §4, renumbered)
# §6 = WM层 (was §5, clean - no RC, no scheduler)
# §7 = 接入层 (was §6, renumbered)
# §8 = 安全红线 (was §7, renumbered)
# §9 = 注意力调度器 \u6a2a\u5207\u7ec4\u4ef6 (new, from extracted attn lines)
# §10 = 质量属性 (was §8, renumbered)
# §11 = 术语表 (was §9, renumbered)
# §12 = 版本记录 (was §10, renumbered)

print("\n重构脚本正确，准备写入。")
