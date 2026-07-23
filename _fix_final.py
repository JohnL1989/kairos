#!/usr/bin/env python3
"""Final refinement batch - all 12 items from latest review."""
import os

cf_path = 'D:/projects/kairos/docs/foundation/cognitive-foundation.md'
arch_path = 'D:/projects/kairos/docs/foundation/architecture-v1.0.0.md'

# ===== Read files =====
with open(cf_path, 'r', encoding='utf-8') as f:
    cf = f.read()
with open(arch_path, 'r', encoding='utf-8') as f:
    arch = f.read()

changes = []

# ===== 1.1 五轴叙述框架 =====
old_v1_1_decl = '> v1.0 五轴承载声明：使用价值轴、见证价值轴、时间轴为完整连续度量；可及性轴以降维代理（路径注册表深度度量）承载；认知完整性轴在 v1.0 中不作为价值轴参与帕累托计算——其功能降级为布尔结构标记 `is_structure`。'
new_v1_1_decl = '> v1.0 五轴承载声明：使用价值轴、见证价值轴、时间轴为完整连续价值度量；认知完整性轴为结构保护属性（非价值轴，v1.0 降级为布尔 `is_structure`）；可及性轴为工程代理（路径注册表深度度量）。**本文保留「五轴」一词作为分析框架的名称，不代表五轴在 v1.0 中具有同等的度量地位**——v1.0 中仅三轴为完整连续价值度量，一轴为结构属性，一轴为工程代理。'
if old_v1_1_decl in cf:
    cf = cf.replace(old_v1_1_decl, new_v1_1_decl)
    changes.append("1.1 五轴叙述区分")
else:
    changes.append("❌ 1.1 text not found")

# ===== 1.2 A.6 可证伪条件更新 =====
old_a6 = '核心命题的可证伪条件——"记忆以使用为衡量标准"本身也受声明门禁约束'
new_a6 = '核心命题的可证伪条件——"记忆服务于认知存续"本身也受声明门禁约束'
if old_a6 in cf:
    cf = cf.replace(old_a6, new_a6)
    changes.append("1.2 A.6可证伪条件更新")
else:
    # Try alternative phrasing
    changes.append("❌ 1.2 A.6 text not found")

old_a6_2 = '若存在完全独立于使用事件且无法被现有解释框架'
new_a6_2 = '若系统中存在一类记忆，其保留与遗忘完全不受认知存续的任何约束（即既不服务于身份存续、也不服务于认知边界测绘或结构完整性），且在现有解释框架下无法被归类为受控例外，则该命题被削弱。\n\n> 此条件替代 v1.0 前版本「独立于使用事件」的判据——命题从「记忆即使用」更新为「记忆服务于认知存续」后，可证伪条件随之从「使用无关记忆」扩展为「认知存续无关记忆」。'
if old_a6_2 in cf:
    cf = cf.replace(old_a6_2, new_a6_2)
    changes.append("1.2 A.6 可证伪条件扩展")
else:
    changes.append("❌ 1.2 A.6-2 text not found")

# ===== 1.3 "默认判据"→"最常调用" =====
old_default_use = '使用价值是日常操作的默认判据，但当与更高优先级维度冲突时，系统选择认知存续而非使用效率。'
new_default_use = '使用价值是常规操作中最常调用的维度，而非默认判据。系统的运行逻辑是同时评估所有价值维度（含探索/宪法/校准等硬约束），使用价值权重在日常调度中占主导但不排他。六级辞典式排序链不只是兜底时激活——它是价值体系的完整排序，探索/宪法/校准作为硬约束始终参与候选生成。使用价值在常规中权重大，但从未获得独立裁决权。'
if old_default_use in cf:
    cf = cf.replace(old_default_use, new_default_use)
    changes.append("1.3 默认判据→最常调用")
else:
    changes.append("❌ 1.3 text not found")

# ===== 1.4 保守倾向位置调整 =====
old_conserv_pos = '   > **自指约束**：保守偏向的检测依赖外部校准信号提供的效率基线——元认知层输出的「保守偏向报告」仅报告指标偏离趋势，不判断「是否因保守导致效率下降」。在没有外部校准的期间，保守偏置无法被可靠检测。此约束不削弱保守倾向的操作化规则（存储状态保守、激活权重保守、探索预算保守），仅声明偏置检测的可靠性条件。\n   │   │   闸门输出写入使用事件总线，附加 tiebreak_reason=conservative_bias 标签'
new_conserv_pos = '   │   │   闸门输出写入使用事件总线，附加 tiebreak_reason=conservative_bias 标签\n   │   │   \n   │   │   > **约束说明**：保守偏向的检测依赖外部校准信号提供的效率基线——元认知层输出的「保守偏向报告」仅报告指标偏离趋势，不判断「是否因保守导致效率下降」。在没有外部校准的期间，保守偏置无法被可靠检测。此约束不削弱保守倾向的操作化规则（存储状态保守、激活权重保守、探索预算保守），仅声明偏置检测的可靠性条件。'
if old_conserv_pos in arch:
    arch = arch.replace(old_conserv_pos, new_conserv_pos)
    changes.append("1.4 保守倾向约束→约束说明")
else:
    changes.append("❌ 1.4 text not found")

# ===== 1.5 §2.2 告警残余清理 =====
告警_cleanup = [
    ('超阈值触发告警至 ME-2', '超阈值触发报告至 ME-2'),
    ('发出情感多样性告警', '发出情感多样性报告'),
    ('超阈值时发至策略层...的心理旋转告警', '超阈值时发至策略层...的心理旋转报告'),
    ('超阈值时发至策略层...的告警', '超阈值时发至策略层...的报告'),
]
for old, new in 告警_cleanup:
    if old in arch:
        arch = arch.replace(old, new)
        changes.append(f"1.5 §2.2 告警→报告: {old[:30]}")

# Also check for告警 not in security context
for term in ['告警（', '告警。', '告警；']:
    count = arch.count(term)
    if count > 0:
        changes.append(f"⚠️ 告警剩余 ≈ {count}处（需人工确认安全上下文）")

# ===== 1.6 §1 标题更新 =====
old_s1_title = '## 一、宪法主权面与身份面'
new_s1_title = '## 一、外部治理接口与身份面（合并说明：原宪法主权面与监督平面已合并为外部治理接口，见速查表）'
if old_s1_title in arch:
    arch = arch.replace(old_s1_title, new_s1_title)
    changes.append("1.6 §1 标题→外部治理接口")

old_s17_title = '### 1.7 监督平面'
new_s17_title = '### 1.7 监督平面（已合并入外部治理接口——本节保留为监督职能历史记录）'
if old_s17_title in arch:
    arch = arch.replace(old_s17_title, new_s17_title)
    changes.append("1.6 §1.7 监督平面→监督职能")

# ===== 1.7 推理皮层边界判据→设计时分类 =====
old_boundary = '输入全部来自内部、输出全部指向内部'
new_boundary = '输入全部来自内部、输出全部指向内部（**运行时自动判定**降级为**设计时分类规则**——每种操作在注册时声明其输入/输出分类，审计庭审计声明诚实性，不试图运行时自动识别分类）'
if old_boundary in arch:
    arch = arch.replace(old_boundary, new_boundary)
    changes.append("1.7 推理皮层边界→设计时分类")
else:
    changes.append("❌ 1.7 boundary text not found")

# ===== 2.1 cf §三 准见证锚定 v1.1标记 =====
old_cf_sec3 = '## 三、系统的上限与演进'
new_cf_sec3_title = '## 三、系统的上限与演进\n\n> ⓘ 本节定义的受限自主阶段「准见证锚定」三阶递进模型为 **v1.1+ 扩展目标**。v1.0 中受限交叉验证模式的降级状态机以校准时延为唯一触发输入，暂未纳入三条充分性条件（≥3 种记忆类型互证、各类型 ≥2 次独立检索记录、检索独立性检验通过）的检测逻辑。认知层定义的此模型为规范目标，架构层 v1.1 目标为将其与降级状态机的触发逻辑绑定。'
if old_cf_sec3 in cf:
    cf = cf.replace(old_cf_sec3, new_cf_sec3_title)
    changes.append("2.1 cf §三 准见证锚定 v1.1标记")
else:
    changes.append("❌ 2.1 text not found")

# ===== 2.2 外部校准源充分性修辞统一 =====
old_calib_cf = '外部校准源充分性尚未被建模为系统一等公民'
new_calib_cf = '外部校准源充分性为 v1.0 设计框架占位，v1.1 实现为系统一等公民'
if old_calib_cf in cf:
    cf = cf.replace(old_calib_cf, new_calib_cf)
    changes.append("2.2 cf 外部校准源→设计框架占位")

old_calib_arch = 'v1.0 新增设计框架'
new_calib_arch = 'v1.0 设计框架占位（v1.1 实现为系统一等公民）'
if old_calib_arch in arch:
    arch = arch.replace(old_calib_arch, new_calib_arch)
    changes.append("2.2 arch 外部校准源→设计框架占位")

# ===== 2.3 注意力调度器架构图注 =====
old_diagram_note = '物理驻留 WM'
new_diagram_note = '物理驻留 WM（注意力调度器在图中标注于 WM 层附近仅表示其与 WM 槽位容量的关联关系，不表示其物理驻留——调度器为独立服务，见 §9）'
if old_diagram_note in arch:
    arch = arch.replace(old_diagram_note, new_diagram_note)
    changes.append("2.3 架构图注意力注")

# ===== 3.1 内核级偏置检测→纯统计趋势 =====
old_bias_detect = '偏置方向检测'
new_bias_detect = '指标单向趋势检测（仅检测指标持续同向变化如检索占比持续上升，不判断该变化是否有害——「偏置」一词在此处意为统计方向的单向收敛，非有害偏差）'
if old_bias_detect in arch:
    arch = arch.replace(old_bias_detect, new_bias_detect)
    changes.append("3.1 偏置检测→统计趋势检测")

# ===== Write =====
with open(cf_path, 'w', encoding='utf-8') as f:
    f.write(cf)
with open(arch_path, 'w', encoding='utf-8') as f:
    f.write(arch)

print("Changes made:")
for c in changes:
    print(f"  {c}")
