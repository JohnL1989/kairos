"""架构文档重构 v3 — 修复切片偏移bug"""
import re

with open(r'D:\projects\kairos\docs\design\architecture-v1.0.0.md', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
print(f"原始行数: {len(lines)}")

# 定位所有章节标题（1-indexed还原为0-indexed）
sec_idx = {}
for i, line in enumerate(lines):
    m = re.match(r'^## (§\d+)', line)
    if m:
        sec_idx[m.group(1)] = i
        print(f"  原始 {m.group(1)} @ 0-indexed {i}")

# 提取推理皮层(0-indexed 972-1014)和注意力调度器(0-indexed 960-970)
rc_lines = lines[972:1014]
attn_lines = lines[960:971]

# 清洗推理皮层行
def clean_block(block, strip_header_chars=True):
    result = []
    for line in block:
        if line.startswith('  ├─ ') or line.startswith('  └─ '):
            result.append(line.replace('  ├─ ', '').replace('  └─ ', ''))
        elif line.startswith('  │'):
            result.append(line[4:] if len(line) > 4 else '')
        else:
            result.append(line)
    while result and result[-1].strip() == '':
        result.pop()
    return result

rc_clean = clean_block(rc_lines)
attn_clean = clean_block(attn_lines)
print(f"\n推理皮层: {len(rc_clean)} 行; 注意力调度器: {len(attn_clean)} 行")

# 构建新文档：从原始lines中移除[960:1014]区间
cleaned = lines[:960] + lines[1014:]

print(f"\n移除RC+Attn后: {len(cleaned)} 行")
for i, line in enumerate(cleaned):
    m = re.match(r'^## (§\d+)', line)
    if m:
        print(f"  清洗后 {m.group(1)} @ index {i}")

# 现在cleaned不含推理皮层和注意力调度器。接下来：
# 插入§4（推理皮层）在§4存储层之前
# 插入§9（注意力调度器）在原§8质量属性之前

# 在cleaned中找到新位置
sec4_idx = None   # 存储层
sec8_idx = None   # 质量属性（将变成§10）
for i, line in enumerate(cleaned):
    m = re.match(r'^## (§\d+)', line)
    if m:
        if m.group(1) == '§4':  # 存储层
            sec4_idx = i
        elif m.group(1) == '§8':  # 质量属性
            sec8_idx = i

print(f"\n存储层§4 @ {sec4_idx}, 质量属性§8 @ {sec8_idx}")

# 构建推理皮层 §4
new_sec4 = [
    '## §4 推理皮层（独立协调层）',
    '',
    '### 4.1 定位',
    '',
    '推理皮层是独立于五层功能栈的**推理协调层**——它不承载记忆数据（不属于存储层）、不承载工作区（不属于 WM 层）、不承载使用决策（不属于策略层），而是作为记忆系统内部推理回路的最小承载层。',
    '',
    '推理皮层服务三类必需的内部推理操作——(a) 前瞻保持触发监控（匹配当前上下文与未来意图）；(b) 使用事件优先级排序（候选排序与上下文裁剪）；(c) 候选集上下文裁剪（WM 维护缓冲与 LTM 激活集之间的实时调节）。三类操作构成记忆系统**最小必要回路**——不依赖外部推理引擎即可独立运转的认知循环。推理不在回路中的操作（多步任务规划、外部工具调度、用户意图的深层语义理解）仍归属外部应用层。',
    '',
    '### 4.2 职责边界',
    '',
]
new_sec4.extend(rc_clean)
new_sec4.append('')
new_sec4.append('---')
new_sec4.append('')

# 构建注意力调度器 §9
new_sec9 = [
    '## §9 注意力调度器（横切组件）',
    '',
    '### 9.1 定位',
    '',
    '注意力调度器是独立的**全局横切资源管理器**——不归属于任何功能层，统一管理编码、巩固、检索三个环节的注意力预算分配。其执行实体虽与 WM 槽位容量直接关联，但在结构上独立于 WM 层（§6），以消除 WM 自利倾向。',
    '',
    '### 9.2 职责',
    '',
]
new_sec9.extend(attn_clean)
new_sec9.append('')
new_sec9.append('**自利倾向告警**：审计庭每周期检查 WM 层在注意力分配中获得的占比是否偏离全周期基线。WM 层获得的预算占比连续超阈值时，发出「注意力调度器 WM 自利告警」至宪法主权面，触发分配规则审查。')
new_sec9.append('')
new_sec9.append('---')
new_sec9.append('')

# 拼接：部分1 (0→sec4_idx) + §4推理皮层 + 部分2 (sec4_idx→sec8_idx) + §9注意力 + 部分3 (sec8_idx→end)
part1 = cleaned[:sec4_idx]
part2 = cleaned[sec4_idx:sec8_idx]
part3 = cleaned[sec8_idx:]

result = []
result.extend(part1)
result.extend(new_sec4)
result.extend(part2)
result.extend(new_sec9)
result.extend(part3)

# 重编号（注意：插入两个新节后所有索引偏移了）
# §4(存储)→§5, §5(WM)→§6, §6(接入)→§7, §7(安全)→§8, §8(质量)→§10, §9(术语)→§11, §10(版本)→§12
result_text = '\n'.join(result)

# 节标题重编号
result_text = re.sub(r'^## §4 ', '## §5 ', result_text, flags=re.MULTILINE)
result_text = re.sub(r'^## §5 ', '## §6 ', result_text, flags=re.MULTILINE)
result_text = re.sub(r'^## §6 ', '## §7 ', result_text, flags=re.MULTILINE)
result_text = re.sub(r'^## §7 ', '## §8 ', result_text, flags=re.MULTILINE)
result_text = re.sub(r'^## §8 ', '## §10 ', result_text, flags=re.MULTILINE)
result_text = re.sub(r'^## §9 ', '## §11 ', result_text, flags=re.MULTILINE)
result_text = re.sub(r'^## §10 ', '## §12 ', result_text, flags=re.MULTILINE)

# 正文内交叉引用重编号
# §5.x → §6.x (WM层引用)
result_text = re.sub(r'(?<![§])(§5\.)(\d+)', r'§6.\2', result_text)
# §4.x → §5.x (存储层引用)  
result_text = re.sub(r'(?<![§])(§4\.)(\d+)', r'§5.\2', result_text)
# §6.x → §7.x (接入层)
result_text = re.sub(r'(?<![§])(§6\.)(\d+)', r'§7.\2', result_text)
# §7.x → §8.x (安全红线)
result_text = re.sub(r'(?<![§])(§7\.)(\d+)', r'§8.\2', result_text)
# §8.x → §10.x (质量属性)
result_text = re.sub(r'(?<![§])(§8\.)(\d+)', r'§10.\2', result_text)
# §9.x → §11.x (术语表)
result_text = re.sub(r'(?<![§])(§9\.)(\d+)', r'§11.\2', result_text)
# §10.x → §12.x (版本记录)
result_text = re.sub(r'(?<![§])(§10\.)(\d+)', r'§12.\2', result_text)

# 更新术语表中的引用
result_text = result_text.replace('| **推理皮层** | §5.2——WM 子模块', '| **推理皮层** | §4——独立协调层')
result_text = result_text.replace('| **推理皮层** | §6.2——WM 子模块', '| **推理皮层** | §4——独立协调层')

# 更新层编号对照
result_text = result_text.replace(
    '架构「第一层」= WM 层 = 认知基础「第二层」',
    '架构「第一层」= WM 层 = 认知基础「第二层」\n> 推理皮层（§4）为独立协调层，不入功能栈层编号。注意力调度器（§9）为横切组件，不入功能栈层编号。')

# 更新接入层中对注意力调度器的引用
result_text = result_text.replace('注意力调度器（§5.2）', '注意力调度器（§9）')
result_text = result_text.replace('注意力调度器（§6.2）', '注意力调度器（§9）')

# 验证
new_lines = result_text.split('\n')
print(f"\n新文档行数: {len(new_lines)}")

secs = {}
for i, line in enumerate(new_lines):
    m = re.match(r'^## (§\d+)', line)
    if m:
        secs[m.group(1)] = i
        print(f"  {m.group(1)} @ L{i+1}: {line.strip()[:70]}")

# 检查旧引用残留
old_refs_check = ['§4.', '§5.', '§6.', '§7.', '§8.', '§9.', '§10.']
for ref in old_refs_check:
    count = len(re.findall(rf'(?<!\d){ref}\d', result_text))
    if count > 0:
        # Check which ones are legit (in code blocks or comment lines)
        print(f"  可能残留 {ref}: {count} 处")

# 写入
with open(r'D:\projects\kairos\docs\design\architecture-v1.0.0.md', 'w', encoding='utf-8') as f:
    f.write(result_text)
print(f"\n✅ 写入完成")
