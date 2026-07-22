"""架构文档完整重构"""
import re

with open(r'D:\projects\kairos\docs\design\architecture-v1.0.0.md', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
print(f"原始行数: {len(lines)}")

# === 提取推理皮层块 (L973-1014) ===
rc_lines = lines[972:1014]
# 去掉顶部的"├─"前缀和后续每行的"│"前缀，转为独立层的格式
rc_lines_clean = []
for line in rc_lines:
    if line.startswith('  ├─ '):
        rc_lines_clean.append(line.replace('  ├─ ', ''))
    elif line.startswith('  │'):
        rc_lines_clean.append(line.replace('  │  ', '').replace('  │ ', '').replace('  │', ''))
    else:
        rc_lines_clean.append(line)
# 移除末尾空白行
while rc_lines_clean and rc_lines_clean[-1].strip() == '':
    rc_lines_clean.pop()

# === 提取注意力调度器块 (L961-970) ===
attn_lines = lines[960:971]
attn_clean = []
for line in attn_lines:
    if line.startswith('  ├─ '):
        attn_clean.append(line.replace('  ├─ ', ''))
    elif line.startswith('  │'):
        attn_clean.append(line.replace('  │  ', '').replace('  │ ', '').replace('  │', ''))
    else:
        attn_clean.append(line)
while attn_clean and attn_clean[-1].strip() == '':
    attn_clean.pop()

print(f"推理皮层: {len(rc_lines_clean)} 行; 注意力调度器: {len(attn_clean)} 行")

# === 构建新文档 ===
# 分段: [0-686): §0-§3 (unchanged, up to §4 存储层 header)
# [686-911): §4 存储层 (will become §5)
# [911-973): §5 WM层 (without RC/Attn) (will become §6)
# [973-1015): §5 WM层的RC+Attn (removed - extracted above)
# [1015-1058): §6 接入层 (will become §7)
# [1058-1092): §7 安全红线 (will become §8)
# [1092-1298): §8 质量属性 (will become §10)
# [1298-1366): §9 术语表 (will become §11)
# [1366-1371): §10 版本记录 (will become §12)

part0 = lines[0:686]           # §0-§3 (unchanged) + §4 header
part4 = lines[686:911]         # 原文§4 存储层 -> §5
part5 = lines[911:960]         # 原文§5 WM层(无RC/Attn) -> §6
part6 = lines[1014:1058]       # 原文§6 接入层 -> §7   (跳过L960-1014=注释+RC块)
part7 = lines[1058:1092]       # 原文§7 安全红线 -> §8
part8_quality = lines[1092:1298] # 原文§8 质量属性 -> §10
part9_terms = lines[1298:1366]   # 原文§9 术语表 -> §11
part10_version = lines[1366:1371] # 原文§10 版本记录 -> §12

# 创建新的推理皮层 §4 内容
new_sec4 = [
    '## §4 推理皮层（独立协调层）',
    '',
    '### 4.1 定位',
    '',
    '推理皮层是独立于五层功能栈的**推理协调层**——它不承载记忆数据（不属于存储层）、不承载工作区（不属于 WM 层）、不承载使用决策（不属于策略层），而是作为记忆系统内部推理回路的最小承载层。',
    '',
    '推理皮层服务三类必需的内部推理操作——(a) 前瞻保持触发监控（匹配当前上下文与未来意图）；(b) 使用事件优先级排序（候选排序与上下文裁剪）；(c) 候选集上下文裁剪（WM 维护缓冲与 LTM 激活集之间的实时调节）。',
    '三类操作构成记忆系统**最小必要回路**——不依赖外部推理引擎即可独立运转的认知循环。推理不在回路中的操作（多步任务规划、外部工具调度、用户意图的深层语义理解）仍归属外部应用层。',
    '',
    '### 4.2 职责边界',
    '',
]
# 清理后的 RC 行，去掉"│"和"├─"前缀
for rcl in rc_lines_clean:
    new_sec4.append(rcl)

new_sec4.extend(['', '---', ''])

# 创建新的注意力调度器 §9 内容
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
for al in attn_clean:
    new_sec9.append(al)

new_sec9.append('')
new_sec9.append('**自利倾向告警**：审计庭每周期检查 WM 层在注意力分配中获得的占比是否偏离全周期基线。WM 层获得的预算占比连续超阈值时，发出「注意力调度器 WM 自利告警」至宪法主权面，触发分配规则审查。')
new_sec9.extend(['', '---', ''])

# 拼接
result = []
result.extend(part0)  # §0-§3
result.extend(new_sec4)  # §4 推理皮层
for line in part4:
    result.append(re.sub(r'^## §4 ', '## §5 ', line))  # §4→§5
for line in part5:
    result.append(re.sub(r'^## §5 ', '## §6 ', line))  # §5→§6
for line in part6:
    result.append(re.sub(r'^## §6 ', '## §7 ', line))  # §6→§7
for line in part7:
    result.append(re.sub(r'^## §7 ', '## §8 ', line))  # §7→§8
result.extend(new_sec9)  # §9 注意力调度器
for line in part8_quality:
    result.append(re.sub(r'^## §8 ', '## §10 ', line))  # §8→§10
for line in part9_terms:
    result.append(re.sub(r'^## §9 ', '## §11 ', line))  # §9→§11
for line in part10_version:
    result.append(re.sub(r'^## §10 ', '## §12 ', line))  # §10→§12

# 更新 §5.2 引用 → §6.2 (WM层编号变了)
result_text = '\n'.join(result)
result_text = result_text.replace('§5.2', '§6.2')
result_text = result_text.replace('§5.1', '§6.1')

# 更新§6.3引用 → §7.3 (接入层)
result_text = result_text.replace('§6.3', '§7.3')

# 更新§4.2, §4.5, §4.6等 → §5.2, §5.5, §5.6 (存储层)
result_text = re.sub(r'(?<!\d)§4\.(\d+)', r'§5.\1', result_text)

# 更新影响评估：原§5(WM)→§6的引用要处理
result_text = re.sub(r'(?<!\d)§5\.(\d+)', r'§6.\1', result_text)

# 原§6(接入)→§7
result_text = re.sub(r'(?<!\d)§6\.(\d+)', r'§7.\1', result_text)

# 原§7(安全)→§8
result_text = re.sub(r'(?<!\d)§7\.(\d+)', r'§8.\1', result_text)

# 原§8(质量)→§10
result_text = re.sub(r'(?<!\d)§8\.(\d+)', r'§10.\1', result_text)

# 原§9(术语)→§11
result_text = re.sub(r'(?<!\d)§9\.', '§11.', result_text)

# 原§10(版本)→§12
result_text = re.sub(r'(?<!\d)§10\.', '§12.', result_text)

# 重写层编号对照
result_text = result_text.replace(
    '架构「第一层」= WM 层 = 认知基础「第二层」',
    '架构「第一层」= WM 层 = 认知基础「第二层」\n> 推理皮层（§4）为独立协调层，不入功能栈层编号。注意力调度器（§9）为横切组件，不入功能栈层编号。'
)

# 更新术语表中的推理皮层引用
result_text = result_text.replace(
    '| **推理皮层** | §5.2——WM 子模块',
    '| **推理皮层** | §4——独立协调层'
)

# 验证
new_lines = result_text.split('\n')
print(f"\n新文档行数: {len(new_lines)}")

# 检查所有章节标题
new_sections = {}
for i, line in enumerate(new_lines):
    m = re.match(r'^## (§\d+)', line)
    if m:
        new_sections[m.group(1)] = i
        print(f"  {m.group(1)} @ L{i+1}: {line.strip()[:60]}")

# 检查残留的旧编号引用
old_refs = ['§4\.', '§5\.', '§6\.', '§7\.', '§8\.', '§9\.', '§10\.']
for ref in old_refs:
    count = len(re.findall(rf'§{ref[:-1]}\.', result_text))
    if count > 0:
        print(f"  残留 §{ref} 引用: {count} 处")
        
# 写入
with open(r'D:\projects\kairos\docs\design\architecture-v1.0.0.md', 'w', encoding='utf-8') as f:
    f.write(result_text)
print(f"\n✅ 已写入 {len(new_lines)} 行")
