# Kairos 文档审查报告（Linus 风格，逐字通读，排除 reviews/）

> 审查范围：50 份文档（foundation 3 / specification 14 / governance 9 / ops 6 / security 2 / quality 4 / development 4 / user 2 / references 7 / README 1）。
> 全部 `status: draft` / "无运行代码"。这意味着下面所有"命令/端口/配置键/限流值"都是**没有代码背书的承诺**——而承诺之间互相打架，比没有文档更糟，因为它会骗三个月后来的人。
> 审查方式：6 个独立阅读代理逐字通读各自切片 + 主审对最高危冲突做逐行复核（行号见正文）。每条都给文件名:行号 + 原文 + 实质问题，不含糊。

---

# 〇、总评（先说最该被枪毙的）

1. **全文事实无单一来源。** `documentation-governance.md §6` 自己规定了"单一事实源"，却恰恰是它规定的状态枚举、命名空间注册表、版本口径被几乎所有文档违反。治理文档处于"未治理"状态。
2. **数字三套口径互不咬合。** 能力数 99↔43、债务数 6↔10↔11、术语数 52↔60+、表数 11↔19、架构章节号 §1–§7↔§10.14——全库没有一个地方能把"功能→认知声明→组件→债务→测试"连贯追完。所谓"可追踪需求基线"目前只追了约 12%。
3. **同一系统"v1.0 做了什么"在文档间直接对立。** 认知基础说二维遗忘曲面/潜伏势能重估/叙事连贯性事件驱动"v1.0 已实现"，架构文档说"延至 v1.1"。下游实现者按不同文档会写出互不兼容的系统。
4. **安全红线 S-02 在两份文档间差 100 倍。** `security-specification.md:30` 写单客户端 ≤100 ops/s；`configuration.md:115` + `threat-model.md:38` 写 ~1 ops/s（60/min）。照 security 配防火墙会放 100 倍的流量。
5. **核心 schema 自己定义两遍且互斥。** `data-model.md` 把 `memory_states`、`knowledge_evolution` 各定义了两次，PK 类型、枚举、唯一约束全部对不上；外键 `BIGINT` ↔ `UUID[]` 混用。ORM/迁移会直接报错或建出两张表。

---

# 一、逐文档审查

## foundation/

### architecture-v1.0.0.md（2123 行，全库最该先修）
- **A-1 WM 层到底含不含推理皮层——自相矛盾。** `§0.5` 一致性规则表 L176 写"WM 层……含推理皮层（§4）……承载三类内部推理操作"；但 `§6.1` L1404 写"WM 层不再承载推理皮层（已独立为 §4）"；`§4` L825 标题"推理皮层（独立协调层）"；`§0.4` L164"推理皮层（§4）为独立协调层，不入功能栈层编号"；`§11` L2106 术语表"推理皮层……独立协调层（物理驻留 WM）"。一份文档里"WM 包含"和"WM 不再承载/已独立"直接对立。
- **A-2 同一组件在两个层里同时出现。** `§4` L829–867 的图标题是"工作记忆层"，列了模拟隔离区/策略提炼旁路/沙箱验证环/边缘槽/多路径结果集/组合性使用验证；`§6.2` L1408–1450 的 WM 层图里**又列了完全相同的一组组件**。`§11` 术语表又把它们归到 WM 层。文档对自己画的边界图没有单一事实来源。
- **A-3 总览图漏掉元认知层。** `§0.4` L112 明说"五层功能栈（接入/WM/存储/策略/**元认知**）+ 宪法主权面 + 监督平面"，但同节 L98–159 的 ASCII 总览图只画了 5 个框，元认知层根本没出现。图文层数不一致。
- **A-4 保守倾向闸门作用范围三处打架。** `§3.2` L738"仅适用于存储状态保守，不适用于调度行为"；`§10.9` L1775"自动激活（覆盖所有裁决而非仅平局）"；`§10.3` L1678"不仅作用于辞典式裁决器平局，还作为跨层原则冲突的默认兜底"。同一组件，一处只管存储、一处覆盖所有裁决、一处跨层兜底。
- **A-5 章节编号崩溃。** L2002 `### 10.16 提示词优化器`；L2030 `### 10.17 组件降级契约`；L2043 `### 10.16 领域路由`。§10.16 被两个不同主题各占一次，且 §10.17 排在第二个 §10.16 之前。更糟：领域路由在 `§3.4` L636 已完整定义过，L2043 是几乎重复的再定义。任何靠章节号交叉引用的工具/人都会指错位置。（已逐行核验。）
- **A-6 叙事连贯性检测器"能否直接告警"自相矛盾。** `§2.2` L483"不可直接触发紧急告警……由解释层裁定是否触发告警"；同节 L486"转移概率离散度突增 → 向宪法主权面发出「解释枯竭告警」"。同一检测器既"不可直接触发紧急告警"又"发出告警"。
- **A-7 单进程部署 vs 端云双节点。** `§0.5` L191"所有层运行在**同一进程中**"；`§5.11` L1378–1381 描述"终端节点 SQLite（本地缓存）"与"服务端节点 PostgreSQL（权威存储）"双向同步。前者是单体，后者是分布式拓扑，对"系统部署形态"给出不同事实。
- **A-8 五维使用向量到底是什么，文档内两说。** `§0.1` L43 用"目的性维度（检索/验证/贡献）、方式性维度（模拟/非模拟）、意识性维度（内隐/外显）"；`§3.8` L809 + 表 L813–819 却把"五维"列为"检索级/验证级/贡献级/模拟级/内隐级"五行。两套对"五维"的组成说法不重合。
- **A-9 内核级降级阈值硬编码 vs 全量可配置。** `§0.5` L197 写死"校准静默期超 3 天触发偏置方向检测；持续同向超 5 周期触发强制安全休眠"；`§10.9` L1761–1772 全量降级状态机用 `N/M 周期（见 ops/configuration.md）`。同一机制两档取值口径。
- **A-10 P6 模态离散化交叉引用错节。** `§3.2` L724 例外(2)写"模态离散化（§7）"，但真正的模态离散化 P6 例外在 `§5.6` L1304。引用指向错误章节。
- **废话**：`§0.4` 反复讲"主权面不参与生成过程"5 遍以上；`§0.16–37` 开发者速查表用"带遗忘策略的带权文件系统"类比，与 cognitive-foundation 苦心经营的"弱自反性/价值独立性"语气撕裂，读者会误以为系统只是个缓存。

### cognitive-foundation.md（806 行）
- **C-1（致命）v1.0 实现范围自相矛盾。** L32 把"时间轴二维遗忘曲面""潜伏势能重估"列入"(a) 可直接观测（v1.0 已实现且行为可验证）"；但 `architecture §4` L1027 白纸黑字"v1.0 简化实现：以单曲线指数衰减作为默认遗忘策略，二维曲面和潜伏势能重估延至 v1.1"。同一系统"v1.0 已实现"清单，认知文档说做了、架构文档说没做。
- **C-2（致命）叙事连贯性检测器触发模式对立。** L587"v1.0 以事件驱动模式运行……此实现消除了此前标注的 v1.1 依赖"；但 `architecture §2.2` L483 / `§2.2.1` L556"v1.0 降级为周期审计模式……v1.1 升级为事件驱动"。认知说 v1.0 已事件驱动，架构说 v1.0 是周期审计。
- **C-3（中）可及性预判版本归属冲突。** L32(c) 列"元记忆第四维可及性预判监测器"为"不可观测（v1.1+）"；但 `architecture §4` L862 / `§10.13` L1894 把它列为"v1.0 代理形式实现"。
- **C-4（中）P6 压缩比分母不一致。** L765"五轴 + VAD 三维 + 使用多维特征共 **10+ 维度**，最多 3-4 维压缩"；`architecture §3.2`/`§0.6` 用"~12 维"和"~14 维"两个分母，压缩 4 维(33%)/6 维(43%)。分母不同，30% 门槛含义不同，会毒害合规判定。
- **C-5（轻）同节内自我推翻。** L123"叙事自洽度不是独立记忆类型，而是……组织属性"；L125"叙事记忆……是跨基础类型交汇处的功能特化子类型"。同一节先用"属性"后用"子类型"。
- **C-6（轻）"五轴"与"四轴"混用。** L81"四轴在度量意义上是'价值—结构混合空间'"，全文框架却是"五轴"；L374 又写"五轴中需要校准的轴"。计数在 4/5 间漂移。
- **C-7（典型）免责声明自己打自己。** L77"此三条根因的集中声明在此替代后续分散的同主题重复声明——除非新增根因，本文不再为此增加新的免责声明"；L117-118 **又贴了一遍同样的声明**，并升级措辞。文档自己承诺"不再重复"，下一屏就重复。

### design-philosophy-relations.md（144 行，三份里最可读）
- **R-1（轻）** L93 把"价值独立性公理"映射到"完整七级链"，但公理本质是"使用≠见证"（S-14），夸大为全链来源；且"此处'身份>校准>时间'为链的截取段"语法上把非连续子串说成"截取段"，误导。
- **R-2（轻）** L11 `status: draft` 但内容已成熟，应标 review/approved 或显式标注待定部分。
- 它是派生图，不引入新断言，因此本身不会与他文档冲突——但它**忠实转述了**另两份文档的冲突点（如 L93 引用的"架构 §3.2 辞典式裁决器"正是 architecture 内部 A-4 矛盾所在组件）。一面镜子而已。

## specification/

### api-spec.md（750 行）
- **A1 章节编号彻底崩坏。** L501 `### 6.6 Reflect API`；L533 `### 6.5 健康报告与聚合统计`（顺序错乱插在 6.6 后）；L558 `### 6.6 Playbook API`（与 L501 的 6.6 撞号）；L602 `### 6.7 Recall Funnel API`；L622 `### 6.7 Recall Funnel API`（标题是 Recall Funnel，正文写的是 MCP Bridge）。一个 API 文档小节编号撞车，还把标题套在错内容上。
- **A2 真·第五节被吃了。** L366 `### GET /v1/memories/{id}?level=summary|overview|full — 多级读取` 没有父章节，夹在"四、事件总线"和"六、扩展端点"之间；L727 `## 七、错误码体系（原第五节）`。`/v1/memories/{id}` 的 `level` 参数规格成了孤儿段落。
- **A3 内存类型 taxonomy 自己打自己。** L35/256 用 `episodic/narrative/semantic/procedural`；L543 `"by_type": {"knowledge":300,"experience":200,"task":400,"context":600}` 是另一套 `knowledge/experience/task/context`；L544 `"by_state":{"active":1200,"stale":200}` 出现 `stale`，但本文 `status` 枚举（data-model L40）根本没有 `stale`。同一 `/v1/health/detail` 响应，两套枚举与全文对不上。
- **A4 同一 `level` 参数两定义。** L98 `?level=export|debug`（导出脱敏级别）；L366 `?level=summary|overview|full`（读取粒度）。相邻端点同参数两含义，且 L70 原始 `GET /v1/memories/{id}` 无 `level`。
- **A5 MCP Bridge 自相矛盾。** L626"MCP Bridge 不通过 REST API 暴露，而是独立 MCP 服务器进程"；L630–639 表格却把每个 MCP 工具逐个映射到 `POST /v1/memories` 等 REST 端点。到底走不走 REST？
- **B1 MCP 工具映射到 4 个根本不存在的 REST 端点。** L630–639：`kairos_search_memories → POST /v1/memories/search`、`kairos_get_hot_memories → GET /v1/memories/heat-top`、`kairos_feedback_memory → POST /v1/memories/{id}/feedback`、`kairos_get_stats → GET /v1/memories/stats`——这些端点全文从未定义。后端按本文实现后 MCP 层全是 404。
- **B2 `bank_id: "my-bank"` 来历不明。** L510 `POST /v1/reflect` body 带 `bank_id`，全文（含 data-model）无"memory bank"概念定义。
- **B3 限流只喊口号无数字。** L50/736–737 提 429，但无 RPS/配额/窗口；`ERR-RATE-001/002` 只说"等待后重试"。
- **C1 错误码表漏 422。** L50 列 422（语义校验失败），但 L731–742 错误码表完全没有 422 对应的 `ERR-*` 码。
- **C2 CLI 命令数造假。** L750"24 个 CLI 命令"，但 L415–421 又追加 3 条，总数应为 27。
- **C3 升华 status 两种互不兼容的形状。** L202–208 孤儿 JSON `{sublimation,forgetting,revaluation}` 无归属端点；L239 `GET /v1/sublimation/status` 返回 `{queue:[{id,stage,status}]}`。
- **C4 升华 stage 枚举自相矛盾。** L239 示例 stage 只列 `raw/strategy/behavior`，漏 `item`；data-model `sublimation_queue.stage` 是 `raw/item/strategy/behavior` 四态。

### data-model.md（530 行，schema 级灾难）
- **A1 `memory_states` 表定义两次，schema 互斥。** L227：`memory_id UUID` / `memory_type TEXT`（"记忆子类型"）/ state `active/stale/archived/suppressed/superseded` / UNIQUE(`memory_id`,`memory_type`)；L406：`memory_id TEXT` / `memory_type TEXT NOT NULL`（枚举 `knowledge/experience/task/user/context`）/ state `active/stale/archived/superseded`（少 `suppressed`）/ UNIQUE(`memory_type`,`memory_id`)。PK 类型、枚举、唯一约束列序全不同。ORM/迁移会直接报错或建两张表。（已核验 L227/L406 两个标题同名。）
- **A2 `knowledge_evolution` 表也定义两次，列名都不同。** L242 `relation TEXT`/`detected_by TEXT`/`confidence REAL`；L420 `relation_type TEXT`/`detection_method TEXT`/`confidence FLOAT`。（已核验 L242/L420。）
- **A3 实体/会话 ID 类型彻底错配。** L356 `entities.id` 是 `BIGSERIAL`（BIGINT）；L517 `entity_communities.member_entity_ids` 是 `UUID[]`（UUID 数组引用 BIGINT 主键，无法做外键）；L376 `memory_entities.superseded_by TEXT` 引用 `memory_entities(id)`（BIGINT）；L310 `weekly_packs.session_ids` 是 `UUID[]`，但会话 ID 全文档是 `TEXT`（L273/336/260）。UUID 数组引用 TEXT/BIGINT 主键，跨服务序列化必崩。
- **A4 "19 张表"是睁眼说瞎话。** L530 版本记录"19 张表（11 核心 + 8 张 v1.0 新增）"；实际本文表格标题数去重后约 29 个独立表名，且含两个同名重复。`implementation-map.md:57` 又称"11 张核心表"。口径三说。
- **A5 内存类型第三套分类。** L35 `episodic/narrative/semantic/procedural`；L411 `knowledge/experience/task/user/context`；api-spec L543 `knowledge/experience/task/context`。全文漂浮三套互不映射的分类轴，无对照表。
- **B1 `embedding VECTOR(1024/1536)`（L34）不是合法列定义。** 同时写两个维度，且 `entities.embedding` L361 与 `memory_chunks.embedding` L388 都是 `VECTOR(1024)`，而 `memories.embedding` 是 1536/1024。一条记忆 1536 维、分块 1024 维，向量检索如何对齐？未解释。
- **B2 `(path, version)` 唯一约束 vs `id` 主键语义没说清。** PATCH（api-spec L85）"内部实现为版本插入"，那么每次 PATCH 是新 `id` 新行还是同 `id` 新版本？对外暴露的"memory id"其实是版本 ID，`superseded_by` 链语义全变。文档回避了这个核心身份问题。

### detailed-design.md（422 行）
- **A1 自称 `v1.0.0` 却又标 draft。** L13/L14 "status: draft" / "非发布版本"；L422"v1.0.0 | 2026-07-21 | 初始版本……本文为 draft，非发布版本"。`v1.0.0` 语义上就是"已发布首版"，与"draft"直接矛盾。
- **A2 "核心 3 组件" vs 组件索引里 5 个 P0。** L19"首迭代完成核心 3 组件（WM 管理器/存储引擎/遗忘引擎）"；L27–34 索引里 §3 遗忘引擎/§5 校准调度器/§8 事件总线 全标 P0（加 WM、存储共 5 个）。
- **A3 引用了不存在的 §9。** L44"与注意力调度器协作（§9，全局资源分配）"；本文索引只到 §8，全文无 §9。
- **A4 `raw`/`item` 一词二义。** §2 写内存先写 `raw 层（不可检索）`→升格 `item（可检索）`（存储暂存）；§4 升华 `raw（原始表征）`→`item（标准表征）`→`strategy`→`behavior`（升华抽象层级）；data-model `sublimation_queue.stage` 还把 `raw/item` 当升华阶段。三处共用一词、含义不同。
- **B1 遗忘算法引用 data-model 不存在的字段。** L195 用 `memory.usage_count_last_30d`，但 data-model `usage_weight` 只有累计 `usage_count`（L104），无"近 30 天"窗口字段；L190 用 `memory.age_days / DECONTEXT_HALF_LIFE` 算 `decontext`，但 data-model 存的是已计算的 `decontextualization_level FLOAT`（L47）。计算值 vs 存储值谁为准？常量 `DECONTEXT_HALF_LIFE`/`AGE_DECAY_CONSTANT`/`LOG`/`SIGMOID`/`CLAMP` 全部无取值。
- **B4 `LAYER_DISTILL` 伪代码查不存在的列。** L348 `SELECT * FROM session_summaries WHERE date = today`（`session_summaries` 无 `date` 列，只有 `start_time`/`end_time` L280–281）；L353 `SELECT * FROM daily_reports WHERE week = current_week`（`daily_reports` 无 `week` 列，只有 `report_date` L291）。照抄必 SQL 报错。

### system-context.md（101 行）
- **嵌入模型维数约束自相矛盾。** L91"标准模式必需 text-embedding-3-small 1536 维；轻量模式 BGE-M3 1024 维（**标准模式不可切 BGE-M3**，维数受 NFR 基线约束）"——前半句说标准模式必需，后半句"不可切"包装成约束，废话。真正冲突在 requirements-baseline（见下）。
- **单进程假设与容量声明脱节。** L23–47 图把记忆系统/存储后端画成嵌套框但无文字说明是否同进程；L2.3 声称标准模式容量 ≥100 万条、8GB 内存，却把扩展性炸弹踢给下游，单进程塞 100 万条+向量+关系索引+升华+RL 的内存/锁冲突只字不提。
- **17 条安全红线列了名字但零定义**，本文只是喊口号。

### requirements-baseline.md（202 行）
- **嵌入模型默认写反（致命）。** L147"外部依赖：Embedding 模型（**默认 BGE-M3 轻量模式**）"；`system-context §三` 明确标准模式必需 text-embedding-3-small（1536），轻量才是 BGE-M3（1024）。本文件把"轻量模式的模型"写成全局"默认"，且完全没提 text-embedding-3-small。（已核验 requirements-baseline:147 与 system-context:91 对撞。）
- **v1.0 "可做"列表谎报进度。** L180 列"17 条安全红线 + HMAC 审计链""CLI 完整命令集""轻量/标准两级梯度"为 v1.0 完成态；但 L31 说"v1.0 目标：可运行核心闭环"，feature-list/claim-matrix 都明言"全系统尚无运行代码"。baseline 把目标/架构就绪写成已做。
- **D-204 定向遗忘状态精神分裂。** L189"~~定向遗忘机制（D-204）~~（已闭环，见 debt-collection DC-027；v1.0 范围以 feature-list M-04 为准）"——划线+「已闭环」表示做完，又补"v1.0 范围以 M-04 为准"；M-04 在 baseline 自己是 P1，use-cases 场景 5 把遗忘画成 `status=archived`（删除式），feature-list M-04 说是"非删除抑制"。到底做完没、语义是什么，三处对不上。
- **W-02 验收标准不可测。** L44"常驻记忆在 **100 轮遗忘周期**后仍存在"——"遗忘周期"什么单位？时间？扫描次数？未定义。

### feature-list.md（204 行）
- **"43 项完整清单"与"扩展 56 项"自相矛盾。** L17"本文列出的 **43 项能力**为草稿完善阶段时的完整功能清单"；L204 总计 43+56=**99 项**。若第九节扩展功能也是清单一部分，"43 项是完整清单"就是假的；且 56 项扩展功能无任何状态标记（冻结了没？在 v1.0 范围吗？沉默）。README:16/35 重复了"99 项"口径，与 feature-list:17 自身的"43 项"直接打脸。
- **"架构层已就绪" vs claim-matrix 的 ⚠️。** L17"各功能状态=冻结——设计已固化、**架构已实现**，代码未编写"；claim-matrix C-11"三类偏差 **v1.0 无监测覆盖**"、C-15"共享基元**仅概念声明，无组件定义**"。即 claim-matrix 把 feature-list 声称"架构已实现"的至少 6 项打脸为"未实现/仅概念"。
- **编号碰撞。** M-04 定向遗忘（非删除）与 use-cases 场景 5 的 `archived` 删除式遗忘冲突。
- **失效跨引用满天飞。** M-06→`api-spec §1.4`、SF-04→`api-spec §1.6`、A-02→`ops/configuration.md`、W-05→`glossary §2`——这些文件全不在本包（specification 只有 14 份 spec 文件），所有外部引用都是悬空指针。还大量引用 `§5.10`/`§7.4`/`§10.14`，但 implementation-map 引用的架构文档只有 §1–§7（见跨文档 E 节）。

### use-cases.md（136 行）
- **场景 5 遗忘语义与 M-04 冲突。** L83–89"得分 > 阈值的记忆进入遗忘队列 → **归档操作执行（标记 status=archived）**"；feature-list M-04 明确定义"定向遗忘**非删除**"。归档 vs 抑制 vs 复兴三种机制混为一谈。
- **场景 7 红线触发描述诡异。** L106–116"使用权重试图反向写回见证锚定"触发 S-14，但 L110"合并逻辑**错误地**尝试写回"——S-14 到底是"禁止自指写回"还是"捕获错误代码"？C-21 说"使用权重不可反向写回见证锚定"是公理，operation-catalog 把 S-14 同时标在"冲突检测写入"和"合并"上，语义漂移。
- **场景 6 降级阈值凭空出现。** L96–101 N、M "为配置参数"，指向 `architecture §10.9` 与 `ops/configuration.md` 的 `DEGRADATION_PERIOD_N/M`；implementation-map 的 config 是 `src/config.py` 70 项参数，未列这两个名。两个配置名只在本场景凭空出现。

### nfr-specification.md（86 行）
- **语义检索延迟：成功标准 vs 测试规模断层（致命）。** L29"语义检索 P50 ≤100ms（**检索计时（10 万条存储）**）"；requirements-baseline §0"管理**超过 100 万条记忆**，检索延迟 <100ms"。10 倍数量级差距，且 nfr 压根没在 100 万条规模测语义延迟。要么 ≤100ms 只在 10 万条成立（那 100 万条的成功标准是空话），要么两文档互相拆台。
- **"内存 8GB" vs "内存（全负载）≤1GB" 同表打架。** L41"内存 | 8 GB | 2 GB"；L65"内存（全负载） | ≤ 1 GB | ≤ 256 MB"。标签都叫"内存"却指两件事（机器规格 vs 进程常驻），不写清就是矛盾。
- **可用性 ≥99.9%（L55）无测量方法**，requirements-baseline §2 根本没列可用性 99.9%，只列了 RTO/RPO。凭空冒出来的数字。

### operation-catalog.md（104 行）
- **VAD 强制 vs 可选，直接打脸 claim-matrix（致命）。** L28"按路径写入 ✅ **VAD 强制录入**"；claim-matrix C-16（L42/L82）"VAD 一阶维度 **降级为条件激活（可选注入）**"。一份说写入时 VAD 强制，一份说 VAD 可选。实现者写写入路径时不知道该 reject 无 VAD 还是 allow。（已核验 operation-catalog:28 与 claim-matrix:42/82 对撞。）
- **"50 项操作对应 feature-list 80 项功能" 数字造假。** L104"与 feature-list.md 的 **80 项功能**之间存在多对多映射"；feature-list 实际总计 99 项（43+56），且第九节明确写 99。operation-catalog 引用的 feature-list 版本和当前不是同一份。
- **安全红线全包悬空。** S-02/03/07/09/11/13/14/15/16/17 被到处引用，但本包无任何文档定义这 17 条红线的具体行为；operation-catalog 把 S-14 同时标在"冲突检测写入"和"合并"上，语义漂移。
- **检索端点三套形态。** operation-catalog L42 `POST /v1/memories/search`；requirements-baseline R-02 L162 `GET /v1/memories?q=`；use-cases `memories_search` Tool——同一检索操作三种 API 定义，互不引用对方。

### implementation-map.md（143 行）
- **架构章节号与本包其他文档完全不兼容（最致命断链）。** 本文引用约定"`架构 §X.Y` 指 architecture-v1.0.0.md 第 X 节第 Y 小节"，自身用 §1 主权/§2 元认知/§3 策略/§4 存储/§5 WM/§6 接入/§7 监督（共 7 节）；但 feature-list 引用 `§10.14`/`§10.9`/`§7.4`/`§5.10`，use-cases 引用 `§10.9`，requirements-baseline 引用 `arch §6.3`/`§4.2`/`§1.2`，claim-matrix 引用 `§10.9`/`§4.2`/`§2.2`/`§3.2`，rl-weight-spec 引用 `§10.14`。**本文说架构只有 7 节，其他文件引用到第 10.14 节。** 要么是多份架构文档，要么章节号是编的。
- **11 张核心表 vs rl_weights 表缺失。** L57"`src/storage/models.py` | 11 张核心表 ORM 定义"；rl-weight-spec L60"`rl_weights` 表当前在 data-model.md 中未显式定义……代码实现时需在 data-model 中补充"。"11 张表"里不含 rl_weights，而 RL 优化器依赖它——映射不完整且自我矛盾。
- **组件计数谎报。** L143"约 40 个组件映射到 src/"；实际表格行数约 64 行。说"约 40"严重低估。
- **"约 20+ 端点"（L99）vs operation-catalog 枚举 50 项操作（大量 REST）**，对不上。

### claim-implementation-matrix.md（102 行）
- **"✅ 完整承载"语义与 feature-list "冻结/架构已实现"冲突。** L19"✅ 表示该认知声明在**架构文档中已有完整描述和组件对应（架构层已就绪），不表示代码已实现**"——这定义合理，但与 feature-list L17"**架构已实现**，代码未编写"的"已实现"措辞冲突；且 C-15（L41）标 ✅ 却备注"**共享基元为设计声明，无组件定义**"——没有组件定义却标"完整承载 ✅"，✅ 的定义被自己备注击穿。
- **C-11 "v1.0 无监测覆盖" 却列入 v1.0 范围。** L37"C-11：三类偏差 v1.0 不实现——无监测覆盖"；L100"v1.0.x：仅修改已声明为『✅ 完整承载』的组件"——但 C-11 是 ⚠️ 不是 ✅。前后分组自洽，但 feature-list 把含 C-11 对应功能标"架构已实现"，矛盾回到 feature-list。
- **来源列全悬空。** `§1.1`/`§1.2`/`D.6`/`C.5`/`E.2` 等指向"认知基础文档"，不在本包。

### rl-weight-spec.md（60 行）
- **默认值与"随机初始化"直接冲突。** L23–27 给每权重列了"默认值"（求和=1.0）；L29"**所有权重初始化为范围内随机值**，再经 Softmax 归一化"。"默认值"列与"随机+Softmax"初始化规则，二者未对齐。
- **5 个 RL 权重对不上"五维混合检索"的 5D。** operation-catalog L42 / feature-list R-09 的 5D = 语义+BM25+时序+信任+热度；RL 权重 = relevance/recency/frequency/user_feedback/trust_score，**BM25 维度在 RL 权重里完全不存在**。R-09 说"v1.0 RL 优化"但 RL 优化器根本没有 BM25 维度参数。
- **反馈端点冲突。** L35"`POST /v1/feedback` 接收用户反馈"；operation-catalog L72"`POST /v1/playbooks/{id}/feedback`"。通用反馈端点和 Playbook 专用反馈端点并存，且 `/v1/feedback` 在 operation-catalog 的 50 项操作里找不到。
- **超参全无默认值。** `KAIROS_RL_MAX_BUFFER_SIZE`、余弦衰减 `lr_min/base_lr/max_steps`、KL `max_extra=0.3`、EMA `decay`、`rcw_multiplier` 全部未在 implementation-map 的"70 项参数"里列出。上线即缺配置。
- **引用 `architecture §10.14`——implementation-map 的架构只有 7 节，§10.14 不存在**（再次印证架构章节号混乱）。

## governance/

### adr.md（289 行）
- **`status: draft`（L11）但 L16"决策已采纳（所有 ADR 的架构选择已锁定）"；每个 ADR 的"设计状态"大量是"进行中"（L23/53/109/137/163/243 等）。** 决策锁了、文件草稿、设计还在做——三句话三个状态。
- **与 changelog 直接冲突。** changelog L90 称 v1.0.0"设计冻结，代码未启动"；adr.md 自己承认多个设计"进行中"。到底冻没冻？
- **ADR-006 L178"采用空闲驱动的三优先级调度"——哪三个优先级？全篇没定义。** "调度器通过负载感知判断推理状态"——怎么感知、阈值多少、谁实现？空白。
- **否决方案分析多为复述。** 多数"否决方案"只是把备选方案表的"劣势"换个说法重复一遍（L46/74/130），无量化依据。

### changelog.md（90 行）
- **同一文件内自相矛盾。** L22"草稿完善阶段发布"；L90"设计冻结，代码未启动"。一句话草稿、一句话冻结。
- **债务版本号严重滞后于 debt-collection（致命）。** L75 `D-204 | 定向遗忘机制 | v1.1`；debt-collection D-204 L137 写"预期版本 v1.0（已并入 DC-019+DC-027 闭环）"——同一债务版本号一个 v1.1 一个 v1.0，状态一个待办一个已闭环。L80 `D-209 | v1.3`；debt D-209 L187 写 v1.2，roadmap M3a 也是 v1.2。L82 `D-211 | v1.1`；debt D-211 L207 写 v1.0.x，cognitive-architecture-gap G-01 也写 v1.0.x。三处两派。
- **"设计冻结"是假的。** 文件 `updated: 2026-07-20`；但 debt-collection 里 62 条 MNM-xx 条目全标 `2026-07-22`（L229 起）。冻结后两天又发生 62 项架构扩展。
- **追缴清单账目对不上。** L61"27 闭环 + 11 待实现 D-201~D-211"，"27 闭环"只数了 DC-001~DC-027，无视已闭环的 D-001~D-005、D-101~D-102、MNM-01~MNM-062；且 D-204 已闭环，所以"11 待实现"实际只有 10 个。

### cognitive-architecture-gap.md（49 行）
- **大量"设计描述级/接口预留/占位框架/认知层仅声明"中间态，无验收判据。** G-04 L26"不要求 v1.0 启动时全部实现"、G-05 L27"接口预留"、G-06 L28"占位框架"——既不是已实现也不是未实现，没有任何"什么叫补回"的判据。
- **与 debt-collection 不一致。** G-01 L23"预期回补 v1.0.x（最高优先级）"配 D-211 v1.0.x，但 changelog D-211 写 v1.1；G-04 说三类偏差检测器"不要求 v1.0 全部实现"，debt D-102 L92 称"✅已完成。架构§2.2 新增三种检测器预留"——一个说预留已做，一个说不用做，无交叉引用，读者无法判断。
- **L49"回路追溯"要求架构文档每处降维标注末尾指向本表编号（`→ G-01`）——无法验证的软约束**，纯靠自觉。

### debt-collection.md（385 行）
- **D-204 被塞进"需实现阶段完成项（代码级）"节，却已闭环。** 节标题"需要实际代码实现，当前阶段仅记录为路线图"；D-204 L137"已并入 DC-019+DC-027 闭环"、L140"无（已闭环，本条仅为补全追踪记录）"。一个已闭环的项被放在"待实现"清单，章节语义自我否定。
- **ID 碰撞（严重，违反 §5）。** MNM-47 L275"§8 新增 **S-18** fail-closed + **S-19** SHA-256 化石节点"；social-calibration-roadmap L136"新增 **S-18~S-20（多Agent校准安全规则）**"；documentation-governance L83"**S-18~S-20（v2.0 多 Agent 校准扩展）**"。**S-18、S-19 被两个完全不同的东西占用**（Hard Delete vs 多Agent校准）。同一编号两套定义，是 §5"禁止同一名称出现在两处不同定义"的硬违反。
- **命名空间 DC-/MNM-/DA-/B-/E-/P- 大量使用，但无一个在 documentation-governance §5 注册。** 治理清单自己漏注册了它管的所有子命名空间。
- **frontmatter `updated: 2026-07-20`，正文 MNM 条目全是 2026-07-22。** 头声称的更新时间早于内容实际生成时间。

### documentation-governance.md（107 行，规矩制定者却被违反得最惨）
- **状态枚举自相矛盾。** §4 L67–71 定义状态只有 `draft`/`v1.0.0`/`deprecated` 三档，且把 `v1.0.0` 当状态值用；L65 又说"晋升至 **final** 的规则待代码启动后执行"——`final` 根本不在状态枚举里。一处说 draft/v1.0.0/deprecated，一处说晋升到 final。
- **实际各下游文档用的状态词汇根本不是这套。** risks.md 用 `monitoring/open/mitigated/resolved`；cognitive-architecture-gap 用 `pending`；debt-collection 用 `✅已完成`。**治理规定的状态值，没有任何一份被治理的文档遵守。**
- **注册表残缺 + 碰撞（§5）。** L87 注册"债务编号（D-001~D-210）"，但 debt-collection 明明有 **D-211**；L81 注册功能编号含 `M` 前缀，但 risks.md 用 **M-001/M-002** 表示"方法论风险"，feature-list 用 **M-10~M-13**——同一 `M-` 前缀两处定义，直接违反 L90"禁止同一名称出现在两处"。§5 注册表覆盖不到一半实际前缀（T-/R-P6-/SCR-/G-/DA-/B-/E- 全未注册）。
- **伪指令。** §3 L48"每次里程碑前运行 `grep -rn '§\d\+\.\d\+' docs/`"只能找章节号格式，找不出"引用了不存在的章节"；§1 L37"运行 `grep -rn "旧值\|旧名" docs/`"——"旧值/旧名"是占位符，根本不是可执行命令。

### project-plan.md（85 行）
- **"4 个 Phase、12 周里程碑"凭空冒出。** L85"4 个 Phase、12 周里程碑"；但 L25 明说"具体周数待代码启动后根据实际进度制定"，且全文件无任何周数或日期。12 周是编的。
- **与 risks.md 脱节。** L74–77 列 4 条风险（pgvector 性能/LLM 嵌入依赖/SQLite 容量/跨层协调），只有"跨层协调"能在 risks.md 找到对应（R-006），另外 3 条在风险登记册里根本不存在。计划的风险清单和登记册是两套互不相通的列表。
- **"安全红线验证 17/17"（L67）但 debt MNM-47 声称已新增 S-18/S-19**——若算数，红线应是 19 条而非 17。

### release-process.md（142 行）
- **v1.0.0 一个版本号承载三种互斥语义。** §1 L33"v1.0.0 特殊规则：代码首次可运行时不变号"；§3 L56"代码启动前不可执行……实际执行须在代码启动后重新校准确认"；changelog 称它是"设计冻结的草稿版"。既是草稿版、又是代码首跑版本、又是未来要 ship 的 release。
- **SemVer 被自己打破。** §1 L31 PATCH="Bug 修复/性能优化/文档更新（无功能变化）"；但 debt-collection D-211、cognitive-gap G-01 把"认知完整性轴三维度量"这种**大型新功能**标成 `v1.0.x`（PATCH 级）。大功能塞进 PATCH，违反本节自己定义的 SemVer。
- **uv 与 pip 混用。** §3 步骤 3 `uv pip install dist/kairos-*.whl`（L64），步骤 5 `pip install kairos==1.0.1`（L81）——从 PyPI 拉而非本地 wheel，与"测试安装本地构建"意图矛盾；标签 `v1.0.1`（L71）与 pip `kairos==1.0.1`（无 v）两种写法。

### risks.md（172 行）
- **与 governance §5 冲突（命名空间）。** 用了 R-001~R-007、T-001~T-003、R-P6-001、M-001~M-002 四套前缀，只 R- 在 governance 注册；T-/R-P6-/M- 全未注册，且 M- 与 feature-list 的 M- 前缀碰撞。
- **状态词汇不统一。** `monitoring/open/mitigated/resolved` 与 documentation-governance §4 的 `draft/v1.0.0/deprecated` 完全不搭。
- **影响评估全是"中/中-低/低-中"形容词，无量化标尺。** R-001"中"、R-003"中-低"、R-005"中"——等于没说。
- **R-004 L63 状态 `mitigated`："审计庭已剥离至独立监督平面（§1.7）"，但同条又描述"宪法主权面仍集否决/冻结执行权与宪法修订立法权于一身"**——前半句说已缓解，后半句描述仍集中的结构。

### social-calibration-roadmap.md（170 行）
- **最严重含糊——假验收标准。** M2 L69–80 验证指标全是未填占位符："连续 **N** 个校准周期内无因降级决策导致的不可逆错误"——**N 未定义**；"假阳性率 < **阈值**"、"恢复后差异检验通过率 > **阈值**"、"至少 **Y** 个完整校准周期""至少 **Z** 次校准中断→恢复循环"——**Y、Z 全空**。这叫"验收标准"？填空题没填完。
- **ID 碰撞（与 debt / governance 冲突）。** L136（M4）"新增 **S-18~S-20（多Agent校准安全规则）**"；但 debt-collection MNM-47 L275 已把 S-18、S-19 分配给"Hard Delete 安全门 + Hash 净化"且标已闭环。同一 S-18/S-19 两套定义。
- **版本号与 debt 冲突。** roadmap M3a=v1.2、M3b=v1.3（与 debt D-209/D-210 一致）；但 changelog D-209 写成 v1.3（roadmap 这边对，changelog 错）。

## ops/

### configuration.md（223 行）
- **Env-var-only vs config-file 自相矛盾。** L19"所有配置参数通过环境变量设置，统一使用 `KAIROS_` 前缀"；L208（§二）"通过环境变量或配置文件设定，重启生效"。runbook L66 又备份 `~/.kairos/config.yaml`。三份文档对 config.yaml 是否存在意见不一。
- **参数重复定义。** `KAIROS_SANDBOX_CONFIDENCE_INTEGRATION_THRESHOLD`（默认 0.7）出现在 §3 L60 **和** §5 L97，且 L60 自己注"属 WM 层，见 §5"——作者承认放错节。定义一次就好。
- **时间单位未定义。** §3 L58 `KAIROS_CONSTITUTIONAL_LOCK_PERIOD` = "1000 个外部校准周期"——"外部校准周期"全文档从未定义。1000 个未定义单位 = 无意义。
- **章节顺序崩坏。** 文档流 §1→§7→**§9**(L126)→**§10**(L139)→**§8**(L148)→§8.1→§8.3→§8.4→§8.5，**无 §8.2**（§8.1 直接跳 §8.3）。任何交叉引用"configuration §8.2"或假设章节顺序的文档都会错。
- **参数计数错。** L223"= 83 项参数"；实际每节计数之和 4+9+9+24+7+2+9+5+11+1+1=82，且 §3 的 sandbox 参数被双重计数（既在 §3 又在 §5）。
- **WAL 归档错塞进 §7 "安全红线"。** L122–123 `KAIROS_WAL_ARCHIVE_COMMAND`/`RETENTION_DAYS` 是 Postgres 备份机制，不是安全红线。

### deployment.md（192 行）
- **容量单位 "SLO" 是垃圾。** L29"记忆容量 | 10 万条 **SLO** | 100 万条 **SLO** | ≥100 万条"——SLO（Service Level Objective）不是记忆条数单位。运维读"100 万条 SLO"无法规划磁盘。
- **三种模式"功能等价" vs 能力天差地别。** L35"三种模式下所有核心功能等价，仅容量、启动时间和认知能力深度不同"；但同表 L24–33 显示轻量模式元认知层"—"（缺失）、升华层"受限"、策略层"内置（权重衰减）"。"功能等价"直接矛盾于一个根本没有元认知监测器的部署模式。
- **`/health` schema 与 observability.md 对不上。** deployment L97–111 的 `calibration:{status,mode}`/`db:{status,pool_connections}`；observability L43–56 的 `/health` 是 `calibration:{status,last_arrival,mode}`/`db:{status,pool_connections,pool_available}`。同一端点的两个不同响应体，基于 `last_arrival` 的告警规则按 deployment 的 schema 取不到字段。
- **`kairos init` 不一致。** L157 `kairos init --db`；security-spec L120 引用 `kairos init --init-key <key>`。两个不同 init 子命令未对齐。
- **`kairos/kairos:latest` 镜像（L18 自承不存在）却声称 ~10 秒冷启动**——对不存在的镜像编造启动时间。

### observability.md（115 行）
- **冻结超时告警无阈值。** L92"冻结超时 | 冻结持续超过**预设时长** | critical"——"预设时长"从未定义。configuration 有 `KAIROS_FROZEN_EMERGENCY_TIMEOUT`=30 调度周期，但告警文案另造一个未定义的"预设时长"。
- **两套互不兼容的降级状态机，未说明关系。** L37 `kairos_degradation_mode` 枚举"0=正常 1=静默 2=受限交叉验证 3=安全休眠"（认知/校准驱动）；reliability L54–58 把降级定义为"黄色预警/红色警戒/崩溃边缘"（基于**磁盘使用率**）。两个不同状态机，SRE 看到 `degradation_mode=2` 分不清是磁盘"红色"还是配置"受限交叉验证"。
- **"监督平面专用信道"是未定义的基建。** L104–107 偏置放大率/自我参照效应/耦合计/VAD 独立性全路由到"监督平面专用信道"——**八份 ops/security 文档里没有任何一份定义了监督平面**。这是通向一个不存在组件的信道，纯手挥。
- **校准到达告警算不清。** L87"距上次校准 > 3 周期（=900s/15min）"匹配 metric（delta），但 health payload（L36/L52）只暴露绝对时间戳 `last_arrival`。告警所依赖的 delta 无法从文档化的 health 端点算出。

### reliability.md（108 行）
- **备份节奏自相矛盾。** §1.1 L25"升华层每次运行前自动创建数据库快照"（每次升华运行前）；§3 L96"数据库全量 | 每日 05:00"。两种矛盾的节奏；runbook §6.1 的周期性维护里**根本没有每日全量备份任务**——"每日 05:00"无操作 owner。
- **备份落盘位置歧义。** §1.1 L29 把 `kairos-YYYYMMDD.db` 扔进 `~/.kairos/backups/`；§3 L95 说常驻契约备份去 `~/.kairos/backups/core/`；deployment L49–50 只把 `backups/core/` 当唯一备份子目录。快照写父目录，策略表说子目录，选一个。
- **持久性承诺 vs 写入确认语义（静默丢数据风险）。** §1.3 L48"写入确认基于内存缓冲收讫而非落盘确认，缓冲层有持久化兜底"——显式在落盘前就 ack 写入。但 §二 L84 声称 DB RPO ≤5 分钟、L82 声称 API RPO ≤1 天。缓冲 ack 设计意味着缓冲与落盘之间的任何崩溃**会丢失已确认写入**——"≤5 分钟 RPO"对缓冲窗口是谎言，此风险从未被标注。
- **API RPO 两行自打。** §二 L82–83 先"Kairos API RPO ≤1 天"，紧跟"Kairos API（无状态）RPO —"。同一组件两行冲突的 RPO；无状态那行等于承认它没有数据可恢复，与前一行矛盾。

### runbook.md（222 行）
- **错误码索引不完整却声称完整。** §5.3 L159"错误码索引"，L174"完整错误码参考见 references/error-reference.md"；但 troubleshooting L40/L42 加了 **`ERR-DB-002`**（迁移失败）、**`ERR-LLM-002`**（日预算耗尽），runbook 索引里根本没有。且 `references/error-reference.md` 在本套文档里是悬空引用（见下条）。
- **config.yaml 再次出现。** §4.2 L66 备份 `~/.kairos/config.yaml` 和 `.env`；configuration L19 说配置仅环境变量。要么 config.yaml 存在要么不存在，runbook 假设存在，configuration 说不存在。
- **降级回滚半截。** §3.2 L101–106 `docker compose down` → "加载旧镜像版本" → `docker compose up -d` → `kairos db rollback`。"加载旧镜像版本"不是命令——operator 怎么 pin 旧镜像？compose（deployment L18）用的是 `:latest`，使得"加载旧镜像"在不带外部 tag 的情况下不可能。**你无法回滚一个 `:latest` 部署。**

### troubleshooting.md（47 行，全套最薄且表格破裂）
- **错误码表结构破裂。** L31 开一行"错误码索引 | ① 检查日志……② 按 ERR- 前缀检索……"只有一格，随后 L32+ 的 `ERR-*` 行是独立行，不再匹配原 3 列（症状|排查|恢复）表头。渲染出来是破表。
- **加了 runbook 没有的错误码**（`ERR-DB-002`/`ERR-LLM-002`），见 runbook 条。
- **"常驻契约不更新"（L25）"写入已落盘但当前 session 不刷新"——说写入*已*落盘；reliability L48 说写入是缓冲 ack、**未落盘**。两文档对"落盘"含义直接对立。
- **磁盘 >85%（L27）让 operator "手动清理过期备份或触发升华层激进归档"——不给任何命令**，且"激进归档"不是任何文档定义的 `kairos` 子命令。

## security/

### security-specification.md（146 行）
- **S-02 单客户端限流差 100 倍（全库最危险的不一致）。** L30"双级限流：单客户端建议 **≤100 ops/s**（令牌桶），系统级熔断 500 ops/s"；configuration L115 `KAIROS_RATE_LIMIT_WRITE_PER_MIN`=**60/min（≈1 ops/s）**"系统容量 ≥100 ops/s"；threat-model L38"单客户端建议 **≤60/min（约 1 ops/s）**，系统级硬上限 500 ops/s"。**（已核验三处原文。）** security 说单客户端可 100 ops/s，config+threat-model 说约 1 ops/s——100 倍差距。照 security 配防火墙/限流会放 100 倍流量，而实现实际只强制 1 ops/s。
- **S-01 "无 Key 拒绝启动" vs "运行时缺 Key 返回 401"。** L29"校验失败直接拒绝连接，不进入 HTTP 鉴权阶段"……"运行时缺 Key 返回 HTTP 401"；L120"首次部署可用 `kairos init --init-key <key>` 预注入 Key，不违反 S-01"——若 Key 可在 init 预注入，"无 Key=拒绝启动"保证就有个 bootstrap 例外，未在 S-01 本身反映。
- **[P] 模式无 bind 地址配置键。** S-04 L32"默认绑定 127.0.0.1；非本机请求拒绝"；但 [P]=对外开放（L19）。要公开就得改 bind 地址——**全文档（含 configuration/deployment）没有任何 bind host 配置键**。S-04 对 [P] 模式不可击败，因为没有文档化的旋钮去解绑 127.0.0.1。
- **静态加密技术未指定。** §3.1 L78"SQLite 加密扩展 / 全盘加密（OS 层）"——哪个 SQLite 加密扩展？SQLCipher？SEE？"加密扩展"是类别不是技术，实现者无法行动。
- **XSS 预设了不存在的 UI。** L35(S-07)/threat-model L35 提"导出接口 HTML 实体编码"/"注入 XSS"——什么渲染 HTML？八份文档里没有任何 Web UI 被定义。XSS 预设了一个未被指定的 HTML 表面，要么有未文档化的 UI，要么这是 cargo-cult。

### threat-model.md（88 行）
- **S-02 同上冲突**，且自身一句内自相矛盾：L38"系统级硬上限 500 ops/s（熔断）……系统级容量目标 ≥100 ops/s"——"硬上限 500"和"容量目标 ≥100"不是同一个量，句子把它们当一致陈述。500≠≥100；若容量仅 100 ops/s，500 ops/s 的"硬上限"会在断路器跳闸前先压垮系统。数字来自不同假设。
- **审计 HMAC 链是唯一的、写得扎实的可验证产物**（双链 content_hash + HMAC），但 L88"审计日志的存储位置与数据存储**物理隔离**（独立表或独立文件）"——"独立表"在同一数据库里是逻辑隔离不是物理隔离。审计者读此会过度信赖。

## quality/

### acceptance-criteria.md（124 行）
- **债务计数 6 vs 10 vs 11 三说。** L17"定义 **D-201~D-206 六项** v1.1 代码债务"；README L110"10 债务"；traceability-map L118"11 债务"。且 traceability 引用 D-201/D-203/D-204/D-205/D-206/D-208/D-209/D-210——**跳过 D-202 和 D-207**。D-202（动态身份增强）有 acceptance §一 条目却在 traceability 无行。
- **D-206 标题"四轴完整度量函数"列为 v1.1 债务，但 glossary L39 说 v1.0 已"承载四轴"。** 四轴度量到底 v1.0 完整还是 v1.1 债务？
- **§二 文档检查（L113-114）"认知基础 `status: draft`"、"架构文档 `status: draft`"作为发布门槛**——你不会用一个 v1.0.0 发布的门槛是"文档是 draft"。要么应是 approved/reviewed，要么这条毫无意义。
- **写入吞吐 ≥100 ops/s（L105）与 user-guide L199 系统硬上限 500 ops/s、benchmark 100 客户端并发矛盾**——100 客户端 × ≥100 ops/s = 10,000 ops/s，远超 500 熔断。

### benchmark-plan.md（110 行）
- **零代码却写基准计划。** §一 L23"基线的快照时机为每次 MINOR/PATCH 版本发布前的最后一次基准运行"——全库 pre-code，每个数字都是虚构。
- **§3.1 把"嵌入维度"当测试变量**——嵌入维度由模型固定（text-embedding-3-small=1536，BGE-M3=1024），你不能变一个模型固定的维度。无意义变量。
- **§3.3 并发 10/50/100 客户端，与 user-guide 硬上限 500 ops/s 冲突**——100 并发 × ≥100 ops/s 会触发自己的系统熔断。容量规划 incoherent。
- **§四 回归阈值"内存泄漏 | 连续 24h 增速 >1%/h | 阻塞发布"但 §3 测试只跑 60s–120s**——2 分钟基准测不出"连续 24h"泄漏。测试方法与阈值直接矛盾。

### test-plan.md（148 行）
- **单元/集成用例数"待定"。** L29–30"待定（代码启动后根据实现接口数量确定）"——一个 gating v1.0 发布的测试计划，连测什么都不知。
- **TC-W01-003（L60）把运行时 401 场景标上 "S-01" 语言**——S-01 是启动门禁（无 Key 拒绝启动），与运行时 401（ERR-AUTH-001）是两回事，测试标签混淆了红线。
- **§3.5 C-04（L94）`kairos admin degrade safety-sleep`——admin 子命令集在任何地方都未定义。**
- **范围排除 v1.1 定向遗忘（L38），但 acceptance D-204（v1.1 债务）要求定向遗忘测试**——acceptance 的 D-204 验收条件没有测试计划覆盖。

### test-strategy.md（172 行）
- **§2.2 S-07 行 markdown 表格破裂。** L67 该行前两个分隔符是**全角 `｜`** 而非半角 `|`，列数崩塌，任何合规解析器都会渲染错。
- **§2.2 S-01（L61）"拒绝启动（API Key 哈希存储 + 启动时校验）"但 user-guide/quick-start 用 `--init-key` 写 `secrets.yaml`**——"哈希存储"的哈希方案从未定义。
- **§2.5 种子（L101）"POST /v1/seeds 创建种子锚点"但 user-guide 种子是文件系统（`KAIROS_SEED_PATH`）**——三处种子位置（glossary `kairos://_system/seeds/` / user-guide 文件系统 / test-strategy REST）互不对齐。
- **覆盖率门槛漂移。** §五 L158–164 覆盖目标 ≥80% 行 + ≥70% 分支；test-plan 退出准则（L47）只提"单元覆盖率 ≥80%"——分支覆盖率被丢了。

## development/

### coding-conventions.md（117 行，相对干净）
- **§一 异步规则自击败。** L37"异步函数 `async def` + `_async` 后缀（仅在函数名不足以表达异步性时）"；示例 `async def retrieve_memories(...)` 无后缀——靠"名称不足时再加"这种无法在 review 中强制的规则。
- **§三 层内错误 `raise StorageLayerError("memory not found")` 与 error-reference `ERR-DB-004`=404 是同一条件**——coding-conventions 从未说明这些映射到 `ERR-DB-*`。
- **§四 日志 `error_code` 用 `ERR-DB-001` 等，但 integration-design 说 ERR-DB-* 不暴露**——日志用 API 故意隐藏的码，合理，但 error-reference 又给它们 HTTP 状态（见跨文档冲突 #4）。

### development-setup.md（125 行）
- **硬编码个人 GitHub URL。** L35 `git clone https://github.com/JohnL1989/kairos.git`——一个"架构设计阶段、无运行代码"的项目，此 repo 可能不存在/可能不是规范组织。脆弱。
- **`uv pip install -e ".[dev]"`（L44）vs user-guide/quick-start 的 `pip install kairos`（PyPI）**——同一 v1.0 两套不兼容的安装故事。用户照 quick-start `pip install kairos` 什么都装不到（无发布包，明确"无构建产物"）。
- **DSN 格式三说。** L59 `postgresql://postgres:kairos@localhost:5432/kairos`（带凭证）；user-guide L30 `postgresql://localhost:5432/kairos`（无凭证）；quick-start L56 `sqlite:///$HOME/.kairos/kairos.db`。三份文档三个不同默认 DB 路径/格式。
- **`pre-commit install`（L47）但从未提及或创建 `.pre-commit-config.yaml`。** 悬空工具链。

### integration-design.md（121 行）
- **§一 写签名（L33）`client.write(path, content, contract, ...)` 省略了 `memory_types` 和 `source`**——但它自己 §六 示例（L106）和 error-reference 都要求这两个参数。文件内部自不一致。
- **ERR-DB-*/ERR-LLM-* "仅日志记录" + "不暴露内部错误码"（L73-74）与 error-reference 把它们当 HTTP 返回直接冲突**（见跨文档 #4）。
- **§五 webhook（L81）"POST /v1/webhooks … 标记为 v1.1 持续完善"**——webhook 是 v1.1，但事件总线声称 v1.0（glossary）。v1.0/v1.1 边界模糊。

### technology-stack.md（83 行，干净参考文档）
- **嵌入模型口径一致**（标准 text-embedding-3-small 1536 / 轻量 BGE-M3 1024），但 user-guide L69 `KAIROS_LLM_API_KEY` 描述为"（升华/嵌入）"——暗示一个 key 同时管 LLM 和嵌入；text-embedding-3-small 需要 OpenAI key，BGE-M3 本地无 key。key 需求是模式相关的却未文档化。
- **§二 连接池"外部连接池仅在连接数 >> CPU 核数时介入"——">>"不是规格。** 含糊。
- **未说明 `apscheduler`（§一）如何与"事件总线基于数据库表"（glossary §六）协调**——调度 vs 事件重叠未描述。

## user/

### quick-start.md（118 行）
- **标题 "5 分钟跑通" vs L107 "全部操作约 2 分钟"**——自己选个数。
- **引导前要求 4 个 env（L27-30）却 L28 说可用 `kairos init --init-key` 生成——而 L42 `kairos admin key generate` 标"未来命令"。** 引导路径循环矛盾：step1 要 key（你还没有）→ 用 --init-key 生成（user-guide）→ 或用 admin key generate（未来）。
- **"开箱即用"（L17）声称 SQLite 零配置，却要求 4 个 secret + init**——不是零配置。
- **秘钥落点矛盾。** L28"生成四密钥并写入**环境文件**" vs user-guide L52"写入 **`~/.kairos/secrets.yaml`**"——环境文件 vs yaml 文件，不同持久化、不同消费路径。

### user-guide.md（209 行）
- **`kairos suppress` 标 v1.0 却实为 v1.1（致命）。** L17"`kairos suppress` 为 v1.0 功能"；但 traceability-map L45 把 M-04 定向遗忘 → **D-204 定向遗忘机制**（acceptance-criteria 里的 v1.1 债务）。文档化的 CLI 命令比实际发布早了一个版本。
- **§1.3 必需 env 与 quick-start 不一致。** L62-70 列 7 个必需变量含 `KAIROS_DB_DSN` 和 `KAIROS_LLM_API_KEY`；quick-start 只列 4 个，从不提 DB_DSN 或 LLM key。照 quick-start 的用户缺 3 个必需变量。
- **§2.1 写签名无 `memory_types` 参数**——与 integration-design/error-reference 要求冲突（跨文档 #6）。且 `source="chat_input"` 的合法 `source` 白名单全文档未定义。
- **§2.3 `kairos forget`（显式遗忘）vs `kairos suppress`（定向遗忘）未映射到 glossary 的 归档/抑制/硬删除三态**——forget 到底是归档还是硬删除？未说明。对一条数据销毁命令这是危险歧义。
- **§四 并发上限自相矛盾。** L199"并发写入 ≤100 ops/s（建议单客户端上限）……系统级硬上限 500 ops/s（熔断）"；benchmark §3.3 驱动 100 并发客户端——会击穿 500 熔断。容量模型不可能成立。

## references/

### glossary.md（116 行，全库写得最好）
- **术语数 52 vs 60+。** L116"7 类约 **52 条**术语"；README L108"**60+** 中英文术语对照"。（已核验。）
- **五轴口径模糊。** L39"五轴度量空间（v1.0 承载四轴，第五轴可及性以代理实现，完整度量 v1.1）"——与 acceptance D-206（"四轴完整度量函数"，v1.1 债务）冲突：到底四轴 v1.0 完不完整？
- **事件总线"10 类事件，优先级 0–9"（L94）但 integration-design 只列 3 个**——缺口未说明。
- **种子锚点 `kairos://_system/seeds/`（L87）vs user-guide 文件系统路径**——三处种子位置冲突之一。
- 质量：定义大多精确且有出处，缺陷都是跨文档引用层面的，非内部。

### error-reference.md（115 行）
- **自身暴露性矛盾。** L19"ERR-DB-*/ERR-LLM-*/ERR-SYS-* 为内部运维与日志使用……API 仅返回 HTTP 级子集"；但 §1.4/1.5/1.7 表给这些码分配了 HTTP 状态码 + 调用方恢复建议。若它们不返回，恢复建议是给空气的。
- **ERR-INPUT-004（L50）422 "缺少必填字段（content / path）"——漏了 `source`**（S-15 要求）。跨文档 #5。
- **ERR-INPUT-005（L51）校验 `memory_types` 白名单——参数在 user-guide 写签名里缺席。** 跨文档 #6。
- **ERR-DB-002（L60）"数据库迁移失败……`kairos db migrate`"——此命令在全库其他地方都不出现。** 孤儿命令。
- **计数 L115"7 类 30 个错误码"内部正确**（4+4+7+5+4+1+5=30）。

### traceability-map.md（118 行）
- **能力数 43（L16/L118）vs README 的 99**（跨文档 #1，已核验）。
- **债务数 11（L118）vs README 10 vs acceptance 6**（跨文档 #2，已核验）。
- **债务编号有洞。** 引用 D-201/D-203/D-204/D-205/D-206/D-208/D-209/D-210——**D-202、D-207 缺失**；D-202（动态身份增强）有 acceptance 条目却无 traceability 行。
- **C-35 三向映射**（L89-91）D-208/D-209/D-210 全挂在 C-35 社会性校准下，但 C-35 不在"认知声明↔差距"表内，债务编号从 D-206 跳到 D-208 无 D-207。编号方案不一致。
- **它只映射到 feature/claim/debt/gap，不映射到测试用例（TC-/E2E-）**——所以不是真正的"需求↔测试"可追溯，测试在映射之外。

### usage-load-algorithm.md（68 行）
- **版本记录过度承诺（L68）"使用负载五维系数 + 组合记忆/遗忘去语境化/升华优先级标量化规则"——正文（§一–§三）只有五维系数、置信累积、P6 注记，承诺的"组合记忆/遗忘去语境化/升华优先级标量化规则"**根本不在文档里**。缺内容。
- **§三（L47）"五维负载向量在帕累托计算中分别独立……禁止聚合为单标量（P6）"但 value-dimension-entropy §一 把同一五维聚合成单一熵标量 H**——两个文档对"能否标量化五维空间"说法相反。P6 禁止无声丢失维度信息，熵 H 正是维度缩减标量。未解决的张力。
- **系数 1.2/1.4/1.6/1.8/2.0 无推导无引用**，魔法数字。

### vad-coordinate-algorithm.md（82 行）
- **§2.2 A 归一化（L55）"A：记忆自身的 Arousal 值（归一化至 [0,1]）"——归一化公式（推测 (A+1)/2）未给**，实现者得猜。
- **§2.1 默认值（L46）"若所有分量均为默认值……V_init 取 V_default(0.1)，A_init 和 D_init 取 0"**——V_default=0.1（L42），A/D 默认 0 仅隐含，表述不一致。
- **§2.3 boost `max(0, cos(...)-0.5)×2.0` 的 "2.0" 增益是另一未引证的魔法数字。**
- **§2.4/§三 引用"架构 §5.2 整合窗""架构 §10.9"——外部悬空。**

### value-dimension-entropy.md（73 行）
- **§二 坍缩（L44）"触发**宪法修订端口**应急冻结"但 acceptance D-202 #3 是*降级*宪法修订端口对身份降级的权威**——同一端口既被降级（acceptance）又仍是应急冻结权威（本文）。权威模型未对齐。
- **§二 阈值 H≥1.0 健康 / 0.5≤H<1.0 警告 / H<0.5 坍缩**——五维 H_max=2.32，"健康"地板 1.0 意味着需熵 >43% 上限才算 OK，但无任何理由支撑 1.0 vs 1.5。武断。
- **§三 趋势斜率 < -0.05 "每周期显著加速下降"——"-0.05" 每什么单位？H 无量纲，斜率单位未指定。** 含糊。
- **P6 张力**（见 usage-load 条）：本文把五维缩成 H，P6（glossary/usage-load）禁止无声标量化。本文用"多样性健康"搪塞，但 P6 说任何标量化须保留回溯，熵丢弃了 per-dim 分布形状。潜在冲突。

### domain_keywords.yaml（43 行）
- **OCR（L19）列在 computer_vision en 关键词下，但 zh 列表（L18）未含 OCR 中文（"光学字符识别"）**——不对称，轻微数据不一致。
- **未在 README 索引（它是 .yaml，README 计 references 为 6 个 .md）**——trivial。
- 独立无冲突，低风险。

### README.md（137 行）
- **能力数自相矛盾（L16/L35 "99 项" vs L110 "43 能力"）**——同一文件内 99↔43，且 99 与 feature-list/traceability 的 43 冲突（跨文档 #1，已核验）。
- **债务数 L110"10 债务" vs traceability"11 债务"**（跨文档 #2）。
- **术语数 L108"60+" vs glossary"约 52"**（跨文档，已核验）。
- **reviews 链接可能 404。** L119-121 显示名 `reviews/architecture-audit-template.md` 映射到文件 `reviews/Kairos架构文档审计模板_精简版.md` 等——若链接用左列路径则 404。且 meta 讽刺：本库已有一份"Linus 风格批判"（reviews/Kairos文档全集_Linus风格批判_主审终稿_2026-07-22.md），本次审查与其独立收敛于同一批冲突（限流 100×、计数三说）。
- **文档总数 L125"52 份文档"漏算 domain_keywords.yaml**（references 实为 7 文件）。
- **L16"99 项能力处于架构就绪状态"过度承诺**——traceability 显示 11 债务 + 12 差距未补，"就绪"误导。

---

# 二、跨文档一致性对齐检查

## A. 术语 / 概念定义一致性

| 概念 | 文档 A 的定义 | 文档 B 的定义 | 结论 |
|---|---|---|---|
| 内存类型分类 | `episodic/narrative/semantic/procedural`（data-model L35, api-spec L35/256） | `knowledge/experience/task/context`（api-spec L543, data-model L411） | **三套轴，无对照表** |
| VAD 写入 | operation-catalog L28"✅ VAD 强制录入" | claim-matrix C-16 L42/L82"降级为条件激活（可选注入）"；cognitive-foundation L653"条件激活" | **直接对立** |
| 五轴 vs 四轴 | cognitive-foundation L81"四轴" vs L374"五轴" | glossary L39"v1.0 承载四轴，第五轴代理" | 计数漂移 |
| 状态枚举 | memories.status=`active/archived/suppressed/superseded` | health/detail 出现 `stale`（api-spec L544），不在主枚举 | `stale` 悬空 |
| 宪法修订端口权威 | acceptance D-202 #3"降级其权威" | value-dimension-entropy L44"仍应急冻结权威" | **未对齐** |
| 种子锚点位置 | glossary `kairos://_system/seeds/` | user-guide 文件系统 `~/.kairos/seeds/`；test-strategy `POST /v1/seeds` | **三处冲突** |
| 文档状态枚举 | documentation-governance §4 `draft/v1.0.0/deprecated` | risks `monitoring/open/mitigated/resolved`；gap `pending`；debt `✅已完成` | **无一份遵守** |
| M- 前缀 | governance §5 注册为功能编号 | risks M-001/M-002 方法论风险；feature-list M-10~M-13 | **前缀碰撞** |

## B. API 文档 ↔ 架构设计文档矛盾

1. **架构章节号体系断裂（最致命）。** `implementation-map.md` 引用的架构只有 §1–§7；`feature-list`/`use-cases`/`requirements-baseline`/`claim-matrix`/`rl-weight-spec` 引用 `§10.14`/`§10.9`/`§7.4`/`§5.10`/`§5.2`/`§4.2`/`§2.2`/`§3.2`。实现者按本文翻 `architecture §4.2`，feature-list 说组件在 `§5.2`，对不上。要么多份架构文档，要么章节号是编的。
2. **api-spec 把可验证定义全甩给未提供的 `architecture-v1.0.0.md`**（api-spec L349 事件枚举"以 §10.10 为准"；detailed-design L329/401"以 api-spec §四 为权威，完整枚举见 architecture §10.10"；data-model L17/L124"见架构 §4 / §10.10"）。三份 spec 把真东西推给一份不在审查范围、且被引用了至少 4 个章节的外部文档。若那份文档与本文任何一处有出入，本文即错；而本文之间已多处冲突。
3. **api-spec 映射到 4 个幽灵 REST 端点**（`/v1/memories/search`、`/v1/memories/heat-top`、`/v1/memories/{id}/feedback`、`/v1/memories/stats`），REST 侧未定义，MCP 照映射实现必 404。
4. **data-model `memory_states`/`knowledge_evolution` 双定义**与任何一份"架构已就绪"声明直接冲突——迁移脚本只能二选一。
5. **架构 v1.0 范围声明（§10.13 "约 40-50% 覆盖率"、"二维曲面/潜伏势能延至 v1.1"）与 cognitive-foundation L32（"v1.0 已实现"）对立**——见 foundation 节 C-1/C-2。

## C. README 承诺 ↔ 变更日志 / 设计 / 现实

1. **README L16/L35 "99 项能力架构就绪" vs 自身 L110 "43 能力" vs feature-list L17/ traceability L16/L118 "43"**——99 是幻觉，且 README 自己打自己。
2. **README L108 "60+ 术语" vs glossary L116 "约 52"**——差 8 条以上。
3. **README L110 "10 债务" vs traceability "11 债务" vs acceptance "6 债务 D-201~D-206"**——三说。
4. **README L125 "52 份文档"漏算 domain_keywords.yaml**（references 实为 7 文件）。
5. **changelog L90 "设计冻结，代码未启动" 与 adr.md 多处"进行中"、debt-collection 62 条 2026-07-22 条目直接冲突**——"冻结"是假的。
6. **feature-list L17 "架构已实现，代码未编写" 与 claim-matrix ⚠️（C-11/C-15/C-16 未实现/仅概念）冲突**——README 沿用了 feature-list 的过度承诺。

## D. 部署配置 ↔ 其他文档假设冲突

1. **S-02 限流 100× 冲突**（security-spec L30 ≤100 ops/s vs configuration L115/`KAIROS_RATE_LIMIT_WRITE_PER_MIN`=60/min≈1 ops/s vs threat-model L38 ≤60/min≈1 ops/s）——**全库最危险**。照 security 配会放 100 倍流量。
2. **`config.yaml` 是否存在三说**（configuration L19 "仅环境变量" vs configuration §二 L208 "或配置文件" vs runbook L66 备份 config.yaml）。
3. **`/health` schema 两说**（deployment L97–111 vs observability L43–56）——基于 `last_arrival` 的告警按 deployment 取不到。
4. **部署容量单位 "SLO"（deployment L29）是无效单位**，data-model 会用真实单位（条/GB）。
5. **镜像 `kairos/kairos:latest`（deployment L18，自承不存在）却声称 ~10s 冷启动**；且 `:latest` 使 runbook 的"加载旧镜像"回滚不可能。
6. **嵌入模型硬编码 `text-embedding-3-small`（deployment L105/observability L50）无配置键**，data-model/architecture 可能指定本地/自托管 embedder——冲突保证。
7. **Postgres 版本 `pgvector/pgvector:pg16`（PG 16）** 与 technology-stack "PostgreSQL 15–17" 跨度大，且 compose 用 `:pg16` 固定——脆弱。
8. **`KAIROS_SSRF_ALLOWED_HOSTS=api.deepseek.com`**（configuration）单硬编码厂商，与"多 Provider 加权"设计（§6 provider 参数）冲突。
9. **RPO ≤5min/≤1day（reliability）vs "缓冲 ack 非落盘"（reliability §1.3）**——架构的持久性保证会与这个被承认的缓冲 ack 设计冲突。
10. **configuration §8.1/§8.3/§8.4/§8.5（无 §8.2）+ §9/§10 在 §8 之前**——任何交叉引用 "configuration §8.2" 的文档都会错。

## E. 跨维度关联断裂点（最高危，按爆炸概率排序）

1. **架构章节号 §1–§7 vs §10.14** —— implementation-map 与 feature-list/use-cases/rl-weight-spec/claim-matrix/requirements-baseline 引用体系两套宇宙。实现者无法定位组件。**（致命）**
2. **S-02 限流 100×** —— security 与 configuration/threat-model 对同一条红线给差 100 倍的强度。**（致命，最危险）**
3. **VAD 强制 vs 可选** —— operation-catalog 与 claim-matrix/cognitive-foundation 直接对立，写入路径 reject/allow 决策无解。**（致命）**
4. **v1.0 实现范围对立** —— cognitive-foundation（二维遗忘曲面/潜伏势能重估/叙事连贯性事件驱动"已实现"）vs architecture（"延至 v1.1"）。**排期真相冲突。（致命）**
5. **能力数 99↔43 / 债务数 6↔10↔11 / 术语数 52↔60+ / 表数 11↔19** —— 全库无单一事实源。**（致命，数字三说）**
6. **data-model `memory_states`/`knowledge_evolution` 双定义 + 外键 BIGINT↔UUID[] 错配** —— 迁移必错。**（致命，schema 级）**
7. **嵌入模型默认 BGE-M3（requirements-baseline L147）vs text-embedding-3-small（system-context/technology-stack）** —— 标准模式维数直接冲突。
8. **`kairos suppress` v1.0（user-guide）vs D-204 v1.1 债务（traceability）** —— 命令发布版本错配。
9. **S-18/S-19 ID 碰撞** —— debt（Hard Delete）vs roadmap/governance（多Agent校准）两套定义，违反 §5。
10. **ERR-DB-*/ERR-LLM-* "不暴露"却给 HTTP 状态/恢复建议**（integration-design + error-reference 自相矛盾）—— API 客户端若依赖目录会出错。
11. **写参数 `source`/`memory_types` 跨 3 文档分裂**（user-guide 无 memory_types、integration-design 无 source、error-reference 校验两者）—— 写入契约无解。
12. **P6 vs 价值维度熵** —— glossary/usage-load 禁止无声标量化，value-dimension-entropy 却把五维缩成单一 H。潜在 P6 违反。
13. **并发上限自相矛盾** —— user-guide L199 硬上限 500 ops/s vs benchmark 100 并发客户端 × ≥100 ops/s；requirements-baseline/acceptance 写入吞吐 ≥100 ops/s 与 configuration 1 ops/s 客户端限流互斥。
14. **`config.yaml` 存在性三说** + **SQLite 默认路径三说**（quick-start/dev-setup/user-guide）+ **DSN 格式两说**（带凭证 vs 无凭证）+ **秘钥落点两说**（环境文件 vs secrets.yaml）+ **安装故事两说**（`pip install kairos` vs `uv pip install -e`）。

---

# 三、致命级汇总表（负责人先修这些）

| # | 冲突点 | 文档 X:行 | 文档 Y:行 | 严重度 |
|---|---|---|---|---|
| 1 | S-02 限流 100× | security-spec:30 (≤100 ops/s) | configuration:115 / threat-model:38 (≈1 ops/s) | 致命 |
| 2 | 架构章节号 §1–§7 vs §10.14 | implementation-map | feature-list/use-cases/rl-weight-spec/claim-matrix | 致命 |
| 3 | VAD 强制 vs 可选 | operation-catalog:28 | claim-matrix:42/82 + cognitive-foundation:653 | 致命 |
| 4 | v1.0 实现范围对立 | cognitive-foundation:32 | architecture §4:1027 / §2.2:483 | 致命 |
| 5 | 能力数 99 vs 43 | README:16/35 vs README:110 | feature-list:17 / traceability:16/118 | 致命 |
| 6 | memory_states 双定义 | data-model:227 | data-model:406 | 致命 |
| 7 | knowledge_evolution 双定义 | data-model:242 | data-model:420 | 致命 |
| 8 | 外键 BIGINT↔UUID[] | data-model:356/376/310 | data-model:517 | 致命 |
| 9 | 嵌入默认 BGE-M3 vs text-embedding-3-small | requirements-baseline:147 | system-context:91 / technology-stack:45-46 | 高 |
| 10 | 债务版本号 changelog vs debt | changelog:75/80/82 | debt-collection D-204/D-209/D-211 | 高 |
| 11 | S-18/S-19 ID 碰撞 | debt MNM-47:275 | roadmap:136 / governance:83 | 高 |
| 12 | kairos suppress v1.0 vs D-204 v1.1 | user-guide:17 | traceability:45 + acceptance:17 | 高 |
| 13 | 语义延迟 10万条 vs 100万条 | nfr:29 | requirements-baseline:30 | 高 |
| 14 | 内存 8GB vs ≤1GB | nfr:41 | nfr:65 | 中 |
| 15 | 部署 /health schema 两说 | deployment:97-111 | observability:43-56 | 中 |
| 16 | config.yaml 存在性三说 | configuration:19/208 | runbook:66 | 中 |

---

# 四、一句话结论

这份文档库最该先做的不是补功能，而是**先开一个会钉死四件事**：(1) 架构文档真实的章节号体系（§1–§7 还是到 §10.14？实现者现在根本定位不了组件）；(2) v1.0 到底有没有二维遗忘曲面/潜伏势能重估/事件驱动叙事检测（cognitive 与 architecture 二选一，全库统一）；(3) S-02 限流到底 1 ops/s 还是 100 ops/s（security 那份差 100 倍，是最危险的一条）；(4) 能力/债务/术语/表 的计数口径（99/43、6/10/11、52/60+、11/19 选一个写死，并让 traceability-map 真补全到测试）。这四件事不定，下游任何人拿这些文档都先陷入"到底信哪份"的泥潭，更别提开始写一行可验收的代码。其余的 schema 双定义、VAD 强制/可选、ID 碰撞、配置三说，都是在这四根支柱立起来之后才能收拾的债务。
