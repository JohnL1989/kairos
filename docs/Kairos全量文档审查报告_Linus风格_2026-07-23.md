# Kairos 全量文档审查报告（Linus 风格 · 代码审查级）

> 审查范围：对 `D:\projects\kairos\docs` 下 **除 `reviews/` 外** 的全部 **50 份文档**进行逐字通读。
> 口径：每份文档单独评估（逻辑矛盾 / 模糊表述 / 过时信息 / 缺失关键细节 / 废话），再做跨文档一致性对齐。
> 原则：不无中生有找茬，但遇到真正设计缺陷与文档债务一针见血、不含糊。每个问题都给**文件名 + 章节/条目 + 实质**。

---

## 0. 一句话结论

**这是一套数学内核基本自洽、但治理层与映射层大面积腐烂的文档集：权威模型（六级链 + 身份面否决权、五轴四轴承载）在核心文档里立得住，可一旦往外扩到 specification / governance / ops / quality / user，就开始出现"数字自己咬自己、状态模型各说各话、ID 跨文档断链、部署指南配置漏安全控件"的连锁溃烂。最致命的不是某句话写错，而是这些文档彼此"看起来都合理、合起来经不起一次交叉引用"。**

---

## 1. 最严重的 7 个问题（先说要害）

| # | 问题 | 破坏程度 | 涉及文档 |
|---|---|---|---|
| 1 | **Embedding 维度 1536 vs 1024 全文档撕裂** | 高（架构假设冲突） | system-context / nfr / technology-stack / observability |
| 2 | **API 端点 57 vs 实现地图 "~20+" 直接矛盾** | 高（承诺不可交付） | api-spec / implementation-map |
| 3 | **部署指南漏配 3 个 SSRF 安全变量** | 致命（真实安全缺口） | deployment 漏列 vs threat-model / configuration 要求 |
| 4 | **"七级链（身份入链）"废弃术语在 4 份规范文档残留** | 高（权威模型被推翻） | rl-weight-spec / design-philosophy-relations / feature-list / claim-matrix |
| 5 | **记忆状态模型三套口径互相打架** | 高（数据模型定义不清） | glossary / integration-design / data-model / use-cases |
| 6 | **量化数字全网互咬（功能 102/101、表 29/31、向量 1536/1024、✅30/27、operation 50/53/101）** | 中高（单一事实源失效） | feature-list / changelog / claim-matrix / debt-collection / operation-catalog |
| 7 | **test-plan 捏造 `C-` 前缀能力 ID、引用不存在的 `kairos admin degrade`、把 v1.0 已闭环的定向遗忘踢去 v1.1+** | 高（验收/测试不可信） | test-plan / user-guide / feature-list / debt-collection / acceptance-criteria |

---

## 2. 逐文档批评

### 2.1 README.md（文档索引 · 基线）

- **过时信息**：声称"52 份文档 + reviews 3 份"，但 `reviews/` 实际有 **23 个文件**（非 3）。索引与磁盘事实不符。
- **列表缺项**：`references/` 列 6 份，遗漏 `domain_keywords.yaml`（实际 7 份）。
- **链接失效**：评审链接写 `architecture-audit-template.md`、`comprehensive-audit-report.md`，实际文件名是 `Kairos架构文档审计模板_精简版.md`、`Kairos文档全量审查报告_Linus风格_2026-07-22.md`——链接点开即 404。
- **术语残留**：仍把 `design-philosophy-relations.md` 描述为"七级排序/P1–P6"旧术语体系，而该文档（见下）与认知基础早已重构为六级链 + 身份面否决权。README 没跟上。
- **缺失关键细节**：没有声明"全量文档为设计占位、无运行代码"，读者会误以为 `pip install kairos` 真能装。

### 2.2 foundation/（认知基础 · 3 份）

**cognitive-foundation.md（权威文档，~932 行）**
- **整体评价**：作为权威文档，六级链 + 身份面否决权模型立得住，附录 A–E 完整。**但极其冗长**：密集声明 + 归因声明 + 自述"3 个根因导致大量免责声明"，读起来像论文而不是规范。大量篇幅在自辩而非陈述。
- **缺失关键细节**：未显式说明"五轴中可及性轴 v1.0 仅以工程代理实现（四轴承载）"这一关键边界，需读者自己从架构文档拼出来。
- **含糊表述**：多处"保守倾向"被反复引用却未给可操作的判定阈值（阈值散落在 configuration.md）。

**design-philosophy-relations.md**
- **术语残留（第 1 条严重问题相关）**：仍写"七级链（身份>探索>宪法>校准>认知完整性>时间>间接度）"为简化表达。权威模型已将该旧模型重构为**六级链 + 身份面（独立正交治理面、以否决权介入、不在链内）**。本文档未同步，是术语污染源之一。

**architecture-v1.0.0.md（0.3MB 设计权威）**
- **P6 压缩比超限（受控偏离）**：内部写 P6 全局闸门压缩比上限 30%，但 v1.0 实际约 33–43%（双口径 12 维/14 维）——文档自称"受控偏离"。**问题**：偏离幅度达 +10~13 个百分点，却未在 configuration / observability 暴露任何压缩比指标或告警（见 ops 部分），"受控"二字目前是无仪表的承诺。
- **一致性**：六级链 + 身份面否决权、五轴四轴承载模型与认知基础对齐，这部分是对的。

### 2.3 specification/（12 份）

**requirements-baseline.md**
- 作为基线，未给出"节律偏差 ≤20%"等数值的来源（该数后来被 acceptance-criteria 引用却无锚点，见 quality 部分）。

**system-context.md**
- **数字冲突（问题 #1）**：轻量模式写嵌入维度 **1536**，但 nfr-specification 双值为"标准 1536 / 轻量 1024"。本文单写 1536 忽略轻量模式，与 nfr 直接冲突。

**feature-list.md**
- **数字自咬（问题 #6）**：头部写 **102 项能力（43 核心 + 59 扩展）**，末尾写 **101 项（43 + 58）**——102/101、59/58 双处不一致。
- **术语残留**：旧"七级链"表述未清。
- **缺失**：8 份质量/用户文档引用其能力 ID，但本文未提供稳定 ID 与 api-spec 端点的映射总表。

**claim-implementation-matrix.md**
- **数字虚报（问题 #6）**：文本称"30 个 ✅"，实际矩阵表内 ✅ 仅 **27 个**；"v1.0 完整承载"汇总列列 28 项且把**无 ✅ 的 C-04** 也算入。
- **术语残留**：C-23 残留"双轨"旧术语（已废弃，应为双副本分离）。
- **口径**：本文是"声明→实现"映射，但 traceability-map 又写"37 声明"，三者（claim-matrix 30 / traceability 37 / 实际 27）对不上。

**data-model.md**
- **状态模型冲突（问题 #5）**：称 `suppressed` 是 `archived` 的**子态**；但 use-cases 明确二者**不同**。数据模型的继承关系与使用场景描述打架。
- **数字（问题 #6）**：声称 31 张表；changelog 写 29 表——差值无解释。

**api-spec.md**
- **端点矛盾（问题 #2）**：版本记录写 **57 个 REST 端点**；implementation-map §六 写"约 **20+** 端点"。两个权威文档对"有多少接口"说法差近 3 倍。
- **字段命名不统一**：`provenance` 字段在用户文档被写成 `--source` / `source=`（见 user 部分）。
- **SDK 悬空**：user-guide 的 `KairosClient` SDK 在 api-spec 无任何规格（api-spec 只定义 REST / Agent Tool / CLI）。

**operation-catalog.md**
- **数字（问题 #6）**：本文 53 项操作；changelog 写 50 项；README 又引 53。operation 计数三处不齐。

**detailed-design.md**
- **算法 bug（真实设计缺陷）**：遗忘算法 `min(contract_mod, 1.0)` 使 `environmental(1.5)` / `temporary(2.0)` 与 `ondemand(1.0)` **无差别**（都被钳到 1.0），三种契约的"遗忘偏好差异"被这一行抹平。
- **状态语义冲突（问题 #5）**：`EVICTING` 状态描述为"移除"，与全局"遗忘 = 抑制（suppress）而非删除"的命题直接冲突（删除是硬删除 S-18 路径，不是遗忘路径）。

**implementation-map.md**
- **端点矛盾（问题 #2）**：与 api-spec 的 57 vs 20+ 冲突。
- 未给出"约 20+"与 57 之间的取舍说明（是真只实现 20+，还是 57 是设计目标？）。

**nfr-specification.md**
- **数字（问题 #1）**：嵌入维度双值（标准 1536 / 轻量 1024），与 system-context 单写 1536、technology-stack 统一 1536 冲突。
- **一致性（正面）**：延迟/吞吐/容量类数字与 acceptance-criteria / benchmark-plan 逐字一致，这部分是全集里最干净的交叉引用。

**rl-weight-spec.md**
- **术语/维度双错（问题 #4）**：写"七级链（身份>探索>宪法>校准>认知完整性>时间>间接度）"且称"五维"——权威模型是**六级**且身份面**不入链**。把 5 个使用子维度（检索/验证/贡献/模拟/内隐）误称为"五维"并与五轴度量空间同名混淆。**这是最严重的术语污染文档之一。**

**use-cases.md**
- **状态模型冲突（问题 #5）**：明确 `suppressed` 与 `archived` 不同；与 data-model 的"子态"说法矛盾。

### 2.4 governance/（9 份）

**documentation-governance.md**
- **自相矛盾（问题 #6 治理层）**：§5 命名空间注册表自身违反它定的规则——`risks.md` 的 `T-/M-` 前缀**未注册**且与 feature-list 功能前缀（`M-` 记忆类）**撞名**；`PL-` 前缀**漏注册**。一份讲"编号治理"的文档，自己的示例编号体系是乱的。

**debt-collection.md**
- **计数错误（问题 #6）**：MNM 台账累计与增量不符（MNM-23/32/48）；能力累计 **98** 与对外宣称 **101** 差 3 项，无解释。
- **错引**：D-304 引 `DC-027`，应为 **DC-028**（该错误已被 traceability-map 放大传播）。

**changelog.md**
- **数字无支撑（问题 #6）**：写 101 能力 / 58 扩展，无对应来源；表数 29 vs data-model 31 差值无说明；operation-catalog 50 vs 53 差值无说明。

**adr.md**
- **状态图例自相矛盾**：图例称"已采纳 = 设计已完成"，却标 **6 条"进行中"**——"已采纳"与"进行中"语义重叠，决策状态机不闭合。

**cognitive-architecture-gap.md**
- **表格列错位（问题 #7 类）**：G-05~G-12 表格列错位，导致"闭环判据"列丢失，读者无法判断差距项是否真的闭环。

**project-plan.md**
- **全无日期**：里程碑、依赖、owner 都有，但**零排期**。一份"计划"没有时间轴，等于没计划。

**release-guide.md**
- **当前不可执行却称"一小时走完"**：检查清单大量依赖 `kairos` 命令（设计占位，无运行代码），却承诺一小时完成发布；标题"发布流程"未随改名更新。

**social-calibration-roadmap.md**
- **阈值全空**：所有校准阈值留空未填。
- **状态矛盾**：D-305 状态与 debt-collection 不一致。

**risks.md**
- 前缀 `T-/M-` 未注册（见 documentation-governance 项）。

### 2.5 references/（7 份）

**glossary.md**
- **状态模型/轴表述（问题 #5/#1）**：五轴度量空间把"可及性"写成与四轴等权的第五轴，**无"v1.0 仅工程代理实现"限定**，掩盖真实 gap。
- **身份面缺失定义**：仅以"六级链 + 否决权"后缀出现，**无独立条目**定义身份面为独立正交治理面。
- **正面**：六级链表述正确，本目录 11 份文档中唯一正确呈现权威排序的之一。

**error-reference.md**
- **计数含死码（问题 #6 类）**：ERR-LLM-002 与 ERR-RATE-003 重复（"LLM 日预算耗尽"），文档自承"建议统一用 ERR-RATE-003"，但 ERR-LLM-002 仍计入头条 38 码，虚增一个。
- **组织混乱**：ERR-SYS-* 拆在 §1.7 与 §1.9 两节；字段命名 `retry_after_seconds`(snake) vs 描述"Retry-After"(camel) 不一致。
- **正面**：38 码总数与锚点一致，HTTP 状态/输入上限与 security/configuration 对齐。

**traceability-map.md**
- **自相矛盾（问题 #6）**：同文档内 line 16 称"11 开放 + 7 已闭环 = 18 债务"，line 118 称"11 债务（含 1 闭环）= 11"——18 ≠ 11。
- **错数传播（问题 #6）**：写"claim-matrix（37 声明）""feature-list（43 能力）"，分别与权威 30 / 101 冲突；并传播 D-304→DC-027 错引。

**usage-load-algorithm.md**
- **自相矛盾（P6 范围）**：line 49"负载系数不参与价值裁决"，Section 四 又"系数越高，该维度负载对决策影响越大"——升华/遗忘优先级本就是价值/运营决策，两说互否。
- **过度声称**：声称 5 维向量可"从分量重建"12 维组合态，但文档自承"未显式建模"交互结构，重建声称夸大。

**vad-coordinate-algorithm.md**
- **标签误导**：V_init=0.03 后"向上舍入至 0.1"实为 **3.3× 抬底**（floor-to-default），非"舍入"。
- **阈值悬空**：line 70 情感去强化触发"占比超阈值"——**阈值值未给**。

**value-dimension-entropy.md**
- **交叉引用含糊**：line 46"由 §2.2 元认知层执行"——本文无 §2.2，应为 architecture §2.2，未注明。

**domain_keywords.yaml**
- **违反自身规范**：line 4 声明"每域 5-7 关键词"，但 `computer_vision` 英文侧仅 **4 个**（缺 OCR 英文等价），破例。"5-7"按语言还是合计未定义。
- **计数**：实际仅 **10 个域**，非 11。

### 2.6 development/（4 份）

**technology-stack.md**
- **自相矛盾（版本）**：line 26"Litestar 兼容 2.0–2.10+"，line 74 兼容矩阵写"2.0–2.4"——2.10+ 与 2.4 直接冲突，二选一。
- **维度站队（问题 #1）**：line 37/45/46 统一嵌入维度 1536（含 BGE-M3 由 1024 上采样），坐实 1536 一侧，与 nfr 1024 不可调和。

**development-setup.md**
- **文档不文档当前代码（结构缺陷）**：正文 90% 是 `kairos init` / `kairos serve` 等**未来 CLI**，line 17/21 自承这些命令不可用（无 pyproject，入口是 `python amber/main.py`）。唯一能跑的路径被埋在免责段，开发者照正文走必失败。
- **冗余双免责**：line 17 与 line 21 两段近义"草稿完善"声明，应合并。
- **自矛盾**：line 33 称 BGE-M3"首次 `kairos serve` 下载"，与 line 17"入口是 `python amber/main.py`"冲突。

**coding-conventions.md**
- **缺失护栏**：未要求 `DictionaryOrderer` 实现六级排序，也未**明令禁止**废弃的七级排序——而七级是已知陷阱，命名约定应显式封杀。
- **悬空引用**：line 94 引 `observability.md` logger 字段，本目录集内不可验。

**integration-design.md**
- **状态模型冲突（问题 #5）**：line 63 定义四态机 `active/stale/archived/superseded`，**完全省略 glossary 的 `suppressed`/`delete`** 且引入 glossary 没有的 `stale`/`superseded`——两份文档对"记忆有哪些状态"说法不同。
- **不可解析句**：line 63 为四重从句长句，自承"四态机不产生新的持久状态机态"，削弱刚断言的模型。

### 2.7 security/（2 份）

**security-specification.md**
- **范围虚假（问题 #3 类）**：标题"将 S-01~S-19 整合为可验证安全需求"，但权威模型 S-01~19/**S-20~22**，本文**缺 S-20~S-22** 却自称"规范源"。
- **自相矛盾**：read-only 角色 line 69 标"仅 P"，line 34 S-06 标"L+P"——同一角色适用范围两说。
- **逻辑未闭合**：SALT 季度轮换"保留旧盐值"，但启动只校验单一 `KAIROS_SALT` 环境变量，多盐并存机制完全未定义。
- **缺量化**：每个 S 红线只有"验证方法"，无"违反影响等级/CVSS 类评级"——作为规范源却零风险量化。
- **跨存储事务空话**：S-18 硬删除"vector 清理失败则事务回滚"，但 vector 与 SQLite/PG 是异构存储无分布式事务，fail-closed 回滚是空话。

**threat-model.md**
- **范围虚假**：同缺 S-20~S-22。
- **模式冲突（问题 #3 类）**：§一 L2 把 S-04（127.0.0.1 绑定）当 [P] 措施，但 security S-04 明说"仅 [L]，[P] 靠代理"——威胁模型让公开模式也靠本机绑定防同网段，与自家安全文档矛盾。
- **防护错配**：Information Disclosure（12, High）防护措施列 S-04（网络绑定），真正控制应是 S-07（脱敏）。
- **审计链自相矛盾**：§五 伪代码 `plaintext + prev_hmac` 且存 `prev_hmac`，但校验段说"content_hash 链 + HMAC 链"，术语混用，双链校验流程未闭合。
- **严重度体系不互认**：P0/P1/P2 与 STRIDE 分数两文档无换算关系。

### 2.8 ops/（6 份）

**deployment.md**
- **真实安全缺口（问题 #3）**：§三 环境变量表**漏列** `KAIROS_SSRF_IP_CHECK`、`KAIROS_SSRF_DNS_REBIND_PROTECTION`、`KAIROS_INPUT_LIMIT_QUERY_CHARS`——threat-model §三 与 configuration §7 均要求。照本文部署会得到**不完整的 SSRF 防护**（缺二次 IP 校验与 DNS 重绑定防护）。
- **自相矛盾**：§一 称"三种模式所有核心功能等价"，同表又列升华层"受限/可用/完整"、策略层"内置/完整/完整+探索"、元认知层"—/—/完整"——功能并不等价，该句是凑结论的空话。
- **端口不一**：§四 轻量模式 `kairos serve`（无端口），runbook §1.1 写 `kairos serve --port 8010`。
- **全为占位**：line 18 自承所有命令无构建产物，当前 100% 不可执行。
- **路径对不上**：§二 数据目录树根 `~/.kairos/kairos/`，但 DSN 默认 `sqlite:///$HOME/.kairos/kairos.db` 落在 `~/.kairos/` 而非 `kairos/` 子目录。
- **密钥计数错**：§三 称"四个 KAIROS_* 密钥"，但表内必填含 `KAIROS_LLM_API_KEY` 共 **5 个**。

**configuration.md**
- **自计数错（问题 #6）**：版本记录 line 226 称"§1:4 项，§6:2 项"，实际 §1 有 5 行、§6 有 3 行。
- **重复定义**：`KAIROS_SANDBOX_CONFIDENCE_INTEGRATION_THRESHOLD=0.7` 在 §3 与 §5 各定义一次，跨层双定义，调参以哪处为准未声明。
- **降级态缺角（问题 #7 类）**：他律性降级三态机，observability 定义 **3 态**（含安全休眠），本文 §4 只有 N/M 两周期参数，第三态无阈值。
- **P6 闸门全缺席（问题 #7 类）**：权威 P6 压缩上限 30%（实际 33–43% 受控偏离），本文作为"参数主索引"**无任何压缩比参数**——operator 对压缩失控零可见零可控。
- **孤儿参数**：`KAIROS_ADMIN_IPS`、`KAIROS_CORE_LIMIT_BYTES/LINES`、`KAIROS_SEARCH_DEFAULT_LIMIT` 出现在 deployment 却未进本主索引；LLM 超时/熔断（reliability §1.5）未作为 env 参数收录。

**reliability.md**
- **RTO 表自矛盾（问题 #3 类）**：第 1 行"Kairos API | RPO ≤1天"，第 2 行"Kairos API（无状态）| 不持有需恢复数据"——同一组件既称有需恢复数据又称无状态，两行互斥。
- **DoS 立场冲突**：对"大量写入耗尽存储"判"接受"，却又有整套磁盘 75/85/92% 三级响应——与 threat-model 的"接受"判据矛盾。
- **密钥备份安全缺失**：runbook 明文拷贝 `.env` 备份，本文未评估含密钥备份的加密。

**observability.md**
- **维度站队（问题 #1）**：§1.2 明写嵌入 1536 双模式，坐实 1536 一侧，与 nfr 1024 冲突。
- **降级态数不一**：`kairos_degradation_mode` 0/1/2/3（4 值含 3 降级态）vs configuration 仅 2 周期参数（缺安全休眠阈值）。
- **P6 指标缺席（问题 #7 类）**：无压缩比 gauge/告警，压缩失控不可观测。
- **告警措辞错误**：§四"写入/检索延迟退化：NFR 写入 P95 通过率 < 99%"——把"P95 延迟"与"通过率"揉成一串，语义不清，无法据此写规则。

**troubleshooting.md**
- **表格结构损坏**：主表头三列（症状/步骤/命令），但 ERR 索引后所有 `ERR-*` 行只有 2 单元格（缺症状列），Markdown 渲染会塌。
- **错误码覆盖不全（问题 #6）**：仅列 12 个 ERR 码，权威 error-reference 有 38 个，且未声明"仅列常见"——读者会误以为就这些。
- **与 runbook 不一致**：本文列 ERR-DB-002、ERR-LLM-002，runbook 漏这两项。

**runbook.md**
- **错误码不一致**：§5.3 漏 ERR-DB-002、ERR-LLM-002（troubleshooting 有）。
- **端口不一**：§1.1 轻量 `kairos serve --port 8010` vs deployment 无端口。
- **拓扑不符**：§2.1 标准备份 `pg_dump -h localhost`，但部署容器网络 PG 在 `db:5432`，容器内连 `localhost` 可能失败。
- **API Key 轮换越界**：§6.1 把 API Key 季度轮换列为所有模式维护项，但 security §2.1 明说 rotate **仅 [P]**。
- **全为占位**：line 19 自承命令无运行代码。

### 2.9 quality/（4 份）

**test-strategy.md**
- **版本边界冲突（问题 #7）**：§2.4 把 `kairos://_system/intentions/` 意图创建当 v1.0 单测项，但 feature-list PM-01 标 `⏳ v1.1+`、v1.0 数据模型未落地——把 v1.1+ 塞进 v1.0 范围。
- **身份面 VETO 零覆盖（问题 #4）**：权威模型身份面有否决权，但 §2.1 覆盖表**无对应测试项**。
- **含糊**：§2.3"三类许可类型"从未枚举；P6"4/4"与"三类"口径不清。

**acceptance-criteria.md**
- **版本归属冲突（问题 #7）**：导语称"定义 v1.1+ 债务"，却含 **D-304 定向遗忘**，而本文 §二与 debt-collection 均标其"v1.0 已闭环"。
- **追溯断裂（问题 #6）**：§二 9 项功能检查**零挂 feature-list ID**（无 W-/R-/SF-/CAL-/M- 映射），README/traceability 要求的 RTM 在此断裂。
- **检查项不全**：文档检查漏掉 claim-matrix / detailed-design / requirements-baseline / system-context / use-cases / rl-weight-spec / operation-catalog / architecture / cognitive-foundation 等 README 实际登记文档。

**benchmark-plan.md**
- **判据不一致（问题 #7 类）**：§3.4 升华批处理、§3.5 磁盘增长**无通过/失败判据**，而 §3.1/3.2/3.3 都引用 NFR 目标值。
- **规模代表不足**：写入只测 1 万条，但 NFR 容量目标 100 万——测出的 P50/P95 对 100 万环境无代表意义。
- **P6 门槛缺席（问题 #7 类）**：压缩 cap 30% / 实际 33–43% 在质量文档完全不出现，无法验收"受控偏离"。
- **基线悬空**：§四 回归阈值"超基线 50%/100%"，但 `benchmark-baseline-*.json` 尚未生成。

**test-plan.md**
- **捏造 ID（问题 #7 · 最严重）**：§3.5 标题"校准与降级（C-01~C-04）"使用 **C- 前缀**，但全仓库校准类真实 ID 是 **CAL-01~CAL-06**，"C-" 类不存在——**虚构 ID**。
- **版本归属冲突（问题 #7）**：把"定向遗忘"归 v1.1+ 不覆盖，但 feature-list M-04（核心 v1.0）、debt-collection D-304（v1.0 闭环）、acceptance-criteria（已闭环）、user-guide（v1.0 功能）四份一致——唯独本文冲突。
- **引用不存在的命令**：TC-C03-001 用 `kairos admin freeze`（api-spec 是 `kairos freeze`）；TC-C04-001 用 `kairos admin degrade safety-sleep`（api-spec **无此命令**，降级是 `POST /v1/degradation/switch` mode=`safe_hibernation`）。
- **覆盖缺口**：W-03 批量导入（api-spec 有 `POST /v1/memories/batch`）零用例；显式遗忘 M-03（`kairos forget`）无独立用例。
- **标题暗示全覆盖**：§3.1"W-01~W-07"实际只列 W01/W02/W04/W07，缺 W03/W05/W06。

### 2.10 user/（2 份）

**quick-start.md**
- **重复初始化**：第二步 `kairos init --init-key`"初始化数据库并生成全部密钥"，第三步 `kairos init --db ...` 又"初始化数据库"——步骤语义冲突。
- **字段命名不一**：`--source user_input` 与 api-spec `provenance`、user-guide `source=` 三方不一致。
- **缺失**：未提示 `kairos serve` 实际绑定 127.0.0.1（S-04），远程访问会失败；零引用 S-xx / feature-list ID。

**user-guide.md**
- **代码块断裂**：§1.2 第 49 行提前闭合 ```，第 50 行 `kairos serve --port 8010` 变普通文本，第 51 行开无语言 ``` 无闭合——fence 不平衡，渲染即坏。
- **非法枚举值（问题 #7 类）**：§2.1 `client.write(source="chat_input")` 中 `chat_input` **不在 api-spec provenance enum**（合法值：user_input / external_calibration / internal_inference / system_generated / exploration）。quick-start 用 `user_input`（合法），user-guide 用 `chat_input`（非法）——两份用户文档自身都不一致。
- **SDK 悬空**：§2.1 `KairosClient` 在 api-spec 无任何规格。
- **版本冲突（问题 #7）**：§定位"kairos suppress 为 v1.0 功能"与 test-plan"v1.1+ 不覆盖"冲突。

---

## 3. 跨文档一致性问题汇总（分类）

### 3.1 量化数字互相打架（速查表）

| 维度 | 文档 A 说 | 文档 B 说 | 文档 C 说 | 实质 |
|---|---|---|---|---|
| 功能能力数 | feature-list 102(43+59) | feature-list 101(43+58) | README 101(43+58) | 自身双处不一致 |
| 声明数 ✅ | claim-matrix 30 | claim-matrix 实际 27 | traceability 37 | 三数互咬 |
| 数据表数 | data-model 31 | changelog 29 | — | 差值无解释 |
| 操作数 | operation-catalog 53 | changelog 50 | README 53 | 三处不齐 |
| 嵌入维度 | system-context 1536 | nfr 1536/1024 | tech-stack 1536 | 轻量 1024 被吞 |
| API 端点 | api-spec 57 | implementation-map ~20+ | — | 差近 3 倍 |
| 债务数 | traceability 18 | traceability 11 | debt-collection 98能力/101宣称 | 自相矛盾 |
| Litestar 版本 | tech-stack 2.10+ | tech-stack 2.4 | — | 直接冲突 |
| 错误码覆盖 | error-reference 38 | troubleshooting 12 | runbook 10 | ops 漏配 |

**根因**：没有单一事实源（Single Source of Truth）。每个文档各自维护一份计数，且无任何人用脚本交叉校验。

### 3.2 术语 / 权威模型不一致

1. **"七级链（身份入链）"废弃术语残留**：rl-weight-spec、design-philosophy-relations、feature-list、claim-matrix（C-23"双轨"）仍用旧表述。权威已是**六级链 + 身份面（独立正交、否决权、不入链）**。
2. **身份面 VETO 定义缺失**：glossary 仅以"+"后缀出现，无独立条目；test-strategy 零覆盖测试项。
3. **记忆状态模型三套口径**：glossary（archived/suppressed/delete）vs integration-design（active/stale/archived/superseded）vs data-model（suppressed 是 archived 子态）vs use-cases（suppressed≠archived）。**四份文档四种说法**。
4. **"五维"歧义**：rl-weight-spec / usage-load / value-dimension-entropy 把"使用子维度"称"五维"，与"五轴度量空间"同名混用，glossary 虽区分但下游未同步。

### 3.3 API 文档 ↔ 架构 / 实现脱节

- **端点 57 vs 20+**（api-spec ↔ implementation-map）：究竟交付多少接口无定论。
- **CLI 命令虚构/不一致**：test-plan 引 `kairos admin freeze`/`kairos admin degrade`（api-spec 无）；runbook/deployment 端口不一；development-setup 正文全是未来 CLI。
- **SDK 无规格**：user-guide `KairosClient` 在 api-spec 无锚点。
- **字段命名三套**：`provenance` / `--source` / `source=` 跨 api-spec / quick-start / user-guide。

### 3.4 README 承诺 ↔ 实际 / 变更日志

- README 号称 52 份 + reviews 3 份，reviews 实为 23 份、references 漏 domain_keywords.yaml。
- changelog 的 101/58/29/50 等数字均无对应来源支撑，与 data-model(31)/operation-catalog(53) 不符。
- README 评审链接指向不存在的文件名。

### 3.5 部署 / 配置冲突

- **致命**：deployment 漏配 3 个 SSRF 变量（IP_CHECK / DNS_REBIND_PROTECTION / INPUT_LIMIT_QUERY_CHARS），operator 照配即留安全缺口。
- **降级态缺角**：observability 3 态 vs configuration 2 周期参数。
- **P6 压缩闸门全文档缺席**：30% 上限 / 33–43% 实际无任何参数或指标，operator 零可见零可控。
- **三模式 vs 单布尔**：`KAIROS_LITE_MODE` 无法区分标准↔全量，文档自述"只改数据源"与该事实矛盾。
- **孤儿参数**：deployment 独有 CORE_LIMIT_*/ADMIN_IPS/SEARCH_DEFAULT_LIMIT 未进 configuration 主索引；LLM 超时/熔断未作为 env 收录。

### 3.6 治理文档自相矛盾

- documentation-governance §5 命名空间注册表自身违规（T-/M- 未注册、与 feature-list 撞名、PL- 漏注册）。
- debt-collection MNM 计数错、能力累计 98 vs 101、D-304 错引 DC-027→DC-028。
- adr 状态图例"已采纳=已完成"却标 6 条"进行中"。
- project-plan 全无日期；release-guide 清单当前不可执行却称一小时走完。
- cognitive-architecture-gap G-05~G-12 列错位丢闭环判据。

### 3.7 版本归属冲突（最明确的直接矛盾）

**定向遗忘 M-04 / D-304**：feature-list（核心 v1.0）、debt-collection（v1.0 闭环）、acceptance-criteria（已闭环）、user-guide（v1.0 功能）四份一致；**唯独 test-plan 标"v1.1+ 不覆盖"**。这是六文档间最干净的直接矛盾，改 test-plan 一处即可。

**前瞻意图 PM-01**：test-strategy §2.4 当 v1.0 单测，feature-list 标 v1.1+。

---

## 4. 修复优先级清单（按破坏程度）

**P0 — 现在就改，否则文档不可信：**
1. 修 `test-plan`：删 `C-` 前缀改 `CAL-`；定向遗忘改回 v1.0 覆盖；`kairos admin freeze`→`kairos freeze`；删 `kairos admin degrade`（改 `POST /v1/degradation/switch`）。
2. 修 `deployment`：补 `KAIROS_SSRF_IP_CHECK` / `KAIROS_SSRF_DNS_REBIND_PROTECTION` / `KAIROS_INPUT_LIMIT_QUERY_CHARS`（真实安全缺口）。
3. 修 `api-spec` ↔ `implementation-map`：统一端点数（57 是设计目标还是实际？给一句话定性）。
4. 修 `rl-weight-spec`：删"七级链/五维"，改"六级链 + 身份面否决权 + 五轴（四轴承载）"。

**P1 — 一周内收口：**
5. 统一嵌入维度口径：system-context / nfr / tech-stack / observability 明确"标准 1536 / 轻量 1024"，全文一致。
6. 修记忆状态模型：glossary / integration-design / data-model / use-cases 收敛到一套状态定义（含 suppressed 与 archived 关系）。
7. 建立单一事实源：用一份 `metrics.md` 或脚本固定"能力数/表数/端点数/错误码数"，其余文档引用不重复计数。
8. 修 `traceability-map` 自矛盾（18 vs 11 债务）与错数（37 声明 / 43 能力）。
9. 修 `feature-list` 102/101 自咬；`claim-matrix` ✅ 30→27。

**P2 — 债务清理：**
10. `configuration`：删重复参数定义、修自计数、补 P6 压缩比参数、补第三降级态阈值。
11. `documentation-governance` §5 命名空间注册表自清；`adr` 状态图例；`project-plan` 补日期。
12. `user-guide` 修代码块 fence、改 `chat_input`→合法枚举；`quick-start` 合并重复初始化。
13. `troubleshooting` 修表格结构、补错误码至 38；`runbook` 对齐错误码与端口。
14. `domain_keywords.yaml` 补 OCR 英文、定"5-7"口径。
15. `detailed-design` 修遗忘算法 `min(contract_mod,1.0)` 抹平三契约差异；`EVICTING` 语义改"抑制"而非"移除"。

---

## 5. 总评（Linus 口吻）

数学内核（熵、VAD、负载、排序链）是这堆文档里最干净的部分，算得对账、阈值自洽——说明写的人真懂。但往外一层就塌了：**治理编号说自己违规、部署指南漏安全控件、测试文档捏造能力 ID、用户文档教非法枚举值、六个文档对"定向遗忘归哪版"能吵起来**。

最不能忍的不是某个笔误，而是**没有单一事实源**——每个文档自己数一遍数，从来没人交叉校验，于是 102/101、31/29、57/20+、38/12 这种笑话能同时存在。还有"七级链"这种早被推翻的术语，在规范文档里阴魂不散，等于权威模型自己打自己脸。

结论：**先把 P0 的 4 件事做了**（test-plan 的假 ID 与版本归属、deployment 的安全漏配、api-spec 端点数、rl-weight-spec 的术语），这四项不动，其余装修都是给危房刷漆。然后建单一事实源，否则下个月又是一地鸡毛。

---

*审查完成于 2026-07-23 · 覆盖 50 份文档（排除 reviews/）· 所有问题均附文件名 + 章节定位*
