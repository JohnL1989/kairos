# Kairos 文档全集审查报告（Linus 风格 · 逐字通读版）

- **审查日期**：2026-07-23
- **审查范围**：D:\projects\kairos\docs 全部 50 份文件（排除 reviews/），约 600KB 逐字通读
- **审查方式**：逐文档批评 + 跨文档一致性对齐 + 量化评分 + 综合评价
- **态度声明**：不讲客套话。每条问题给出文档名、章节/行号、原文引用。没找茬，全是能定位的硬伤。

---

## 总判词（先说结论）

这套文档堆出了 101 项功能、57 个端点、37 条认知声明、19 条安全红线、31 张表——但**"排序链到底几级、维度到底几个、权重和到底是不是 1、记忆到底几种状态、功能到底 101 还是 102"这些最基本的事实，没有一处是全库对齐的**。纸面很厚，地基是斜的。三份 foundation 文档是分别起草、未经一次连贯通读校对的；specification 内部三套检索维度词汇并行；ops/quality 的验收目标在自己定义的限流约束下物理不可达；号称解决追溯断链的 traceability-map 自己就是断链制造机。

---

# 第一部分：逐文档审视

## 1. foundation/（3 份）

### 1.1 cognitive-foundation.md（232KB）

| # | 位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| F-01 | §A.7（约 L571–572） | "六级排序链的具体次序（探索>宪法>校准>认知完整性>时间>间接度）……此声明将**七级链**从「认知必然」降格为「规范性承诺」" | 逻辑矛盾 | 同一段落先写"六级排序链"，三行后叫"七级链"。列出的序列只有 6 项，身份明确"不在链中"。把 6 项叫七级链不是笔误，是暗示身份被算进了链——与全文立场直接冲突。 |
| F-02 | §C.5（L636 vs L644–646） | L636"双轨切换**已被身份面否决权模型替代——不再有**……模式切换"；L644 随即"**双轨渐进切换机制**（补充……）"；L646"双轨同步失败回退""双轨切换的偏置管理" | 逻辑矛盾 | 前一句宣布双轨切换已被替代废除，后三段又把它当现存机制详述。补写"补充"时没删旧结论——典型的没通读过自己文档。 |
| F-03 | §2.2（L407/L409） | 标题"设计原则 P1–P5"、正文"**五条设计原则**"，但 §2.3 与附录 E.6 通篇按 P1–P6 处理（E.6 标题即"P1–P6 与辞典式排序对应矩阵"） | 模糊表述 | 自称五条，实际当六条用。文档从未声明"P1–P5 不完整"，读者被"五条"误导。 |
| F-04 | §0.2（L32） | "四轴使用价值度量（**降维为五维使用向量**）" | 模糊表述 | "降维"降成五维——相对什么降？为凑"降维声明"话术生造的含混句。 |
| F-05 | 全文（L77、L113、L342、L389 等数十处） | "受控偏离""边界声明""假设软化""认知诚实性声明""降级为工程代理" | 废话连篇 | L77 自己承认这些免责声明"均可归因为 3 个根因"，却继续在后续 800 行反复粘贴同类免责。用"诚实姿态"包装"我们没想清楚"。该收敛成一张差距表，不是当修辞填充。 |
| F-06 | E.7（L891/L897） | "核心认知维度约 12 维" vs "12 维基数 / 14 维基数" | 模糊表述 | 双口径并列且无单一权威数。 |

### 1.2 architecture-v1.0.0.md（277KB）

| # | 位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| A-01 | §3.2（L768/L773/L780）**头号缺陷** | L768"优先级链：**身份>探索>宪法>校准>认知完整性>时间>间接度**"（7 项）；L773"不改变**六级链**的序位"；L780"与声明的 **7 级优先级链**" | 逻辑矛盾 | 同一节内七级/六级/7 级三称并用，且 L768 把身份写进链首——与本文 §0（L30/L97）、§11 术语表、版本记录声称的"身份为独立正交治理面、不在链中"全部矛盾。这一节不该修，该重写。 |
| A-02 | §0.6（L258） | "**P4 遗忘是工程权衡**"（cognitive §2.2 L417 为"**P4 遗忘是适应性优化**"） | 过时信息 | 同一条原则跨文档改名。"适应性优化"是价值立场，"工程权衡"是中性描述，语义权重不同，属硬冲突。 |
| A-03 | §11（L2256）vs 版本记录（L2273） | 术语表"**CRI > 0.6 触发降级**" vs 版本记录"CRI 阈值见 §3.9/§3.10「**受控待统一**」" | 自相矛盾 | 正文三处写死 0.6，版本记录说没定。要么全文 0.6 是占位，要么版本记录是过期复制粘贴。 |
| A-04 | §3.2（L754）vs §3.8（L847） | "每条记忆维护**五维特征向量**" vs "**五维**来自三个分类轴（目的性 3/方式性 2/意识性 2）" | 逻辑矛盾 | 3+2+2=7，不等于 5。轴拆分和向量维数必有一处是拍脑袋数字。 |
| A-05 | §3.2（L749） | Pareto 输入"多目标向量（**使用价值/见证价值/情感效价/时间衰减**）" | 逻辑矛盾 | cognitive 五轴是"使用/见证/时间/认知完整性/可及性"。架构只列 4 项、把 VAD 单列、缺认知完整性与可及性轴。哪些进 Pareto，实现者只能猜。 |
| A-06 | 全篇（L219/L527/L528/L607/L1057） | "注意力分布熵""使用价值分布的熵值""决策熵""结构熵值+价值维度熵值""概念结构熵值" | 缺失关键细节 | "熵"被当免定义万金油，至少 4 种互不相干的量共用一词，无统一公式。"熵超阈"时读者无法判断是不是同一个数，监控没法写。 |
| A-07 | §11 术语表 | claim、embedding 无正式定义 | 缺失关键细节 | "核心主张"出现在冲突消解逻辑（§5.5 L1361）里却不进术语表；embedding 只当"可替换组件"一笔带过。定义与使用脱节。 |

### 1.3 design-philosophy-relations.md

| # | 位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| P-01 | 总览图（L43–46）vs L107 | L44"辞典式排序（**七级链**）身份>探索>……"；L107"……为**七级链**（详见架构 §3.2）……**此处'身份>校准>时间'为简化表达**" | 逻辑矛盾 | 图里画的是完整七级不是三级，"简化表达"指向不明；且把七级链权威定义指到 architecture §3.2——一个自己写了三种说法的段落。指路指进坑里。 |
| P-02 | 全文核心设定（L43/L107/L154） | "七级链：身份>探索>宪法>校准>认知完整性>时间>间接度" | 逻辑矛盾 | 把身份列进排序链首位，与 cognitive（L30/L79/L372）和 architecture 多数章节"身份正交、以否决权介入、不在链中"相反。三份文件对同一宪法级不变量给出相反答案，这是设计缺陷不是措辞差异。 |

## 2. specification/（12 份）

### 2.1 api-spec.md

| # | 位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| S-01 | 版本记录（L844） | "REST API 57 个端点" | 模糊表述 | 数字不可核对：`GET /v1/search/explain` 在 §6.7(L695) 与 §6.8(L715) 重复定义，`GET /v1/memories/{id}` 在 §1.2(L84) 与 §5(L458) 重复定义。最该精确的总数自己都没数清。 |
| S-02 | §1.4（L160–168） | `GET /v1/memories/{id}/export` 却给出 JSON 请求体 `{"format":..., "include_metadata":true}` | 协议错误 | GET 带请求体在 REST 语义上是错的；clearance=debug 与 export 的返回差异只在注释夹带，没进响应 schema。 |
| S-03 | §1.2（L92） | `"weights":{"semantic":0.4,"path":0.3,"context":0.15,"temporal":0.1,"relational":0.05}` | 逻辑矛盾 | 这是第一套五维命名。与 feature-list R-09"语义+BM25+时序+信任+热度"、rl-weight-spec 六维（relevance/recency/…/trust_score）**三套互不映射的维度词汇**并行。检索是系统心脏，心脏有三套互不相通的术语表。 |
| S-04 | §6.8（L719–730） | MCP 工具表 10 个（kairos_feedback_memory / kairos_store_memory 等） | 跨文档脱节 | operation-catalog 引用的 `kairos_feedback_playbook`、`kairos_delete_memory`、`kairos_merge` 在此表中不存在。 |

### 2.2 data-model.md

| # | 位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| S-05 | §六 user_profiles.rl_weights（L346） | "各维权重和为 1（Bounded Simplex 约束）" | 逻辑矛盾 | rl-weight-spec L49 明写"不做 simplex 归一化（和≠1 是正常的）"，且默认值之和=1.05，api-spec §6.5 返回的也是 1.05。这条约束**永远不满足**。 |
| S-06 | §一 memories.status（L47） | "suppressed 为 archived 子态" | 逻辑矛盾 | use-cases 场景5（L85）把 suppressed 与 archived 当**正交态**（"suppressed 抑制但可复兴，archived 压缩但不抑制检索"）。遗忘/抑制语义的基石没对齐。 |
| S-07 | §一 content_summary（L33） | "用于 RL1 中层检索" | 模糊表述 | "RL1"全文档未定义，抄写残留。 |

### 2.3 detailed-design.md

| # | 位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| S-08 | §3 遗忘得分（L204–212） | "environmental:1.5（v1.0 简化版 clamp 至 1.0）…temporary:2.0（clamp 至 1.0）…三契约遗忘速率退化为两档" | 设计债务 | 注释自承"四契约遗忘差异"在 v1.0 名存实亡（permanent 0 / 其余全 1.0），但 requirements-baseline §0 仍把"四契约"列为 v1.0 覆盖，需求侧未标注降级。追溯断点。 |
| S-09 | §5 校准（L300–303） | "MERGE_THRESHOLD 默认 0.15（cosine 距离）…CONFLICT_THRESHOLD 默认 0.35" | 缺失关键细节 | 差异检验的嵌入从哪来、cosine 对 witness_anchor 哪个字段算，没说；use-cases 场景4 又把"使用权重影子副本"拉进比对，口径不一。 |

### 2.4 feature-list.md

| # | 位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| S-10 | L17 vs L23 vs L208 | "102 项能力（43+59）" / "101 项功能" / "43+58=101" | 逻辑矛盾 | 同一文件三处总数互不一致。连总数都数错的清单，可信度先垮一半。 |
| S-11 | 功能分类更新（L202） | "系统管理 7 +12（A-08~A-20，A-14 预留跳过）" | 逻辑矛盾 | 跳过 A-14 实际 11 项，写成 +12。这个 +1 误差正是 58 vs 59 的来源。 |
| S-12 | 状态声明（L17） | "状态标记为冻结——设计已固化、架构已实现，代码未编写" | 逻辑矛盾 | 与文档头 `status: draft` 并存；"架构已实现"与"全系统零代码"同句。draft 的东西自称冻结，是自己哄自己。且 L23 自承 101 项无逐项验收标准。 |

### 2.5 implementation-map.md

| # | 位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| S-13 | §四（L81） | "Active→Stale→Archived→Superseded 四态" | 逻辑矛盾 | data-model 与 feature-list M-10 均为五态（含 suppressed）。实现地图的状态机比数据模型少一态。 |
| S-14 | §六（L110） | "MCP Bridge … 10 tools（见 api-spec §6.9）" | 错误引用 | MCP Bridge 在 api-spec 是 §6.8，§6.9 是知识加工区 API。索引指错章节。 |

### 2.6 requirements-baseline.md

| # | 位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| S-15 | §1.1 表头（L37）vs §1.3–1.8 | 表头承诺"ID/描述/前置/后置/优先级/验收标准"六字段，M/F/SF/CAL/A/PM 各表仅三列 | 缺失关键细节 | 没有验收标准的"需求"不是需求，是功能 ID 列表。需求基线最该挨骂的一处。 |
| S-16 | §4 RTM（L157–167） | "完整 RTM 表在 v1.0 代码启动前补全。当前仅列核心路径。" | 缺失关键细节 | 需求基线的全部价值就是可追溯，RTM 只填 5 行就用"…"搪塞。空头支票。 |
| S-17 | §1.8（L119–120） | "PM-01 前瞻意图创建 P1" | 逻辑矛盾 | feature-list PM-01/PM-02 标"⏳ v1.1+、数据模型和 API 未落地"。同一功能 requirements 里是 P1（v1.0 范围暗示），feature-list 里是 v1.1+。范围归属自相矛盾。 |

### 2.7 use-cases.md

| # | 位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| S-18 | 场景5（L85–86） | "archived 压缩但不抑制检索"，随即拿"检索了一条**已归档**的记忆……触发复兴加速通道"举例 | 逻辑矛盾 | 按自己的定义，复兴应发生在被抑制的 suppressed 上；例子却拿 archived 当复兴对象。同场景自打嘴巴，且把"遗忘 F-01"与"定向遗忘 M-04"两条路径混为一谈。 |

### 2.8 operation-catalog.md

| # | 位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| S-19 | 一/三（L32/L65/L69/L73） | "kairos_delete_memory / kairos_merge / kairos_feedback_playbook" | 逻辑矛盾 | 三个工具名在 api-spec §6.8 的 10 个 MCP 工具里不存在。自称"与 api-spec 互补不冲突"，工具列却指向虚空。 |
| S-20 | 三区写入（L30） | "POST /v1/memories + hall" | 缺失关键细节 | api-spec §1.1 写入请求体没有 `hall` 字段。"三区写入"映射到哪个参数，没说。 |
| S-21 | 四 统计（L103） | "总计 53 项操作"（vs api-spec"57 端点"） | 模糊表述 | 53 与 57 的 4 项缺口从未解释。 |

### 2.9 system-context.md / 2.10 nfr-specification.md

| # | 位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| S-22 | system-context §三（L92）vs nfr §二（L48） | "BGE-M3 1024 维（线性投影至 1536，**DDL 以 1536 为准**）" vs nfr"向量维度 轻量模式 **1024**" | 逻辑矛盾 | nfr 把存储维数写成 1024，与 system-context/data-model 的 1536 DDL 冲突。容量与向量索引设计会按错维度建模。 |
| S-23 | nfr §五（L78） | "LLM 日预算：可配置，超限熔断" | 不可度量 | 无阈值、无单位、无熔断行为定义。四个字是愿望不是指标。 |
| S-24 | nfr §三（L55） | "≥99.9%……单进程无守护模式不承诺此指标"，自注"未在 requirements-baseline 中定义" | 自拆台 | 写了个自己不认的 KPI。 |

### 2.11 claim-implementation-matrix.md

| # | 位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| S-25 | 视觉误导警告（L21）vs 正文 vs L73 | 警告"30 个 ✅"，实际表中 ✅ 为 27 个，"v1.0 完整承载"清单列 28 项 | 逻辑矛盾 | 警告 30、实际 27、清单 28，三个数全不同。专门警告别人误读的段落自己就在误读。 |
| S-26 | C-04 行（L32）vs L73 | C-04 备注"关系索引……非一等结构"（无 ✅），却被列入"v1.0 完整承载（✅）"清单 | 逻辑矛盾 | 承载状态归属混乱，矩阵自相矛盾。 |

### 2.12 rl-weight-spec.md

| # | 位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| S-27 | L39/L42/L73 vs 维度表（L26–31） | 全文反复"**五维**独立排序"，维度表定义 **6** 维，step3 列出 6 个 | 逻辑矛盾 | 自己定义 6 个维度，自己在算法段数成 5 个，把 entity_boost 数没了。 |
| S-28 | 初始化（L49）vs 持久化（L80） | "不做 simplex 归一化（和≠1 是正常的）"，默认值之和 1.05 | 逻辑矛盾 | 与 data-model"Bounded Simplex 和=1"三方冲突（见 S-05）。 |

## 3. ops/（6 份）

| # | 文档:位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| O-01 | deployment.md §五 | compose 用 PostgreSQL DSN，却不设 `KAIROS_LITE_MODE=false`（§三定义默认 `true`=SQLite） | 逻辑矛盾 | "标准模式"旗舰示例照抄即以 SQLite 模式启动。部署文档的示范本身是错的。 |
| O-02 | deployment.md §五 | compose 环境变量缺 `KAIROS_LLM_ENDPOINT`（§三列为**必填**） | 缺失关键细节 | 照搬即 LLM 调用失败。 |
| O-03 | deployment.md §三 | `KAIROS_INPUT_LIMIT_QUERY_CHARS | 否 | 500 | ……（漏配的安全缺口……）` | 自相矛盾 | 同一行既给默认值 500（已配置）又自称"漏配的安全缺口"。到底配没配？ |
| O-04 | deployment.md §二 vs §三/§六/§七 | 目录树缺 `logs/`、`wal_archive/`、`migrations/`，正文却引用这三个目录 | 缺失关键细节 | 结构图与正文对不上。 |
| O-05 | deployment.md §六 vs coding-conventions §二 | 迁移文件"位于 `~/.kairos/migrations/`" vs 仓库根 `kairos/migrations/` | 逻辑矛盾 | `kairos db migrate` 到底读哪？CI 与产物部署会各走一边。 |
| O-06 | deployment.md §三 vs development-setup §三 | "五个 KAIROS_* 密钥（含 LLM_API_KEY）" vs "自动生成**全部四个密钥**" | 逻辑矛盾 | init --init-key 生成 4 个还是 5 个，两份文档没对齐。 |
| O-07 | deployment.md §三 | 环境变量总表缺 `KAIROS_WAL_ARCHIVE_RETENTION_DAYS`（configuration §7 与 reliability §三均引用，默认 7 天） | 缺失关键细节 | 部署文档漏配置键。 |
| O-08 | configuration.md §3 vs §5 | `KAIROS_SANDBOX_CONFIDENCE_INTEGRATION_THRESHOLD` 重复定义两次（均 0.7） | 废话连篇 | 版本记录自承"内含 2 项重复定义"，既不删也不标权威源。 |
| O-09 | configuration.md §7 | `KAIROS_SSRF_*` / `KAIROS_WAL_ARCHIVE_COMMAND` 归在"安全红线"下 | 逻辑矛盾 | security-spec 红线册 S-01~S-19 不含 SSRF 与 WAL。红线定义权分裂：真实威胁+真实控制，没有 S 编号认领。 |
| O-10 | configuration.md 版本记录 | "§10:2项，§10:4项 = 96 项参数" | 模糊表述 | 同一节号出现两次且计数不同，总数无法核对。 |
| O-11 | observability.md §一 | `kairos_degradation_mode`：0=正常 1=静默 2=受限交叉验证 3=安全休眠 | 模糊表述 | 全库口径是"三模式"（acceptance-criteria 同），指标却枚举 4 个 code。含不含 normal，没人说。 |
| O-12 | reliability.md §1.5 vs integration-design §二 | LLM 单次调用超时 30s/60s vs Agent 客户端默认 timeout 30s | 缺失关键细节 | 客户端 30s 先断、服务端 LLM 60s 仍在跑的竞态，文档装看不见。 |
| O-13 | reliability.md §1.1 vs runbook §2.1 | `pg_dump -d kairos -f …` vs `pg_dump -U kairos kairos` | 模糊表述 | 两份运维文档的"标准备份命令"不一致。 |
| O-14 | troubleshooting.md"无法启动" | 排查清单未含 `KAIROS_API_KEY`（runbook §5.1 与 S-01 均规定无 Key 拒绝启动） | 缺失关键细节 | 启动排查漏掉硬性启动前置，按图索骥找不到卡点。 |
| O-15 | troubleshooting.md 错误码索引 vs integration-design §四 | `ERR-DB-001 / ERR-LLM-001` 列为可查索引 vs "内部码**仅日志记录**，不暴露" | 逻辑矛盾 | 错误码暴露策略双标。真出事时用户手里的码对不上系统吐的码。 |
| O-16 | runbook.md §2.1 vs deployment §五 | `docker exec kairos-db pg_dump …` vs compose 服务名为 `db` | 逻辑矛盾 | 排障命令指向不存在的容器名，照抄报 `container not found`。 |
| O-17 | runbook.md §4.2 vs security-spec §2.1 | `kairos init --init-key` vs `kairos admin key generate` | 逻辑矛盾 | 密钥生成命令两套说法，CLI 契约未冻结就写文档。 |

## 4. security/（2 份）

| # | 文档:位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| SE-01 | threat-model.md §二 | STRIDE 主表仅 S-01~S-06；S-07/S-08/S-09 无独立威胁场景条目 | 缺失关键细节 | security-spec 的正式红线在威胁模型里没被正经分析，"STRIDE 完整展开"名不副实。 |
| SE-02 | threat-model.md §三 | "适配器 SSRF……出站 URL 白名单" | 逻辑矛盾 | 威胁列了、控制（KAIROS_SSRF_*）也列了，但没有任何 S 编号绑定（见 O-09）。安全审计做不到"红线 100% 覆盖"，因为红线册漏了已设计的控制。 |
| SE-03 | threat-model.md §三 | "Judge 漂移……黄金集回归 + 漂移告警" | 缺失关键细节 | 有威胁有缓解，无 S 编号、security-spec 无对应条目。控制没进规范源。 |
| SE-04 | security-specification.md §2.1 | "生成 \| kairos admin key generate" | 逻辑矛盾 | 见 O-17。规范源给的命令与其余所有文档不一致。 |

## 5. quality/（4 份）

| # | 文档:位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| Q-01 | acceptance-criteria §二 vs configuration §7 vs benchmark §3.3 | "检索吞吐 ≥ 500 ops/s" vs 单客户端读限流 120/min（2/s）vs 并发只测 10/50/100 | 逻辑矛盾 | 100 客户端读吞吐上限 200/s，够不到 500/s。**验收目标在自己的限流约束下物理不可达**，除非基准时偷偷关限流（文档未声明）。这是 NFR 与实现约束没对账，不是笔误。 |
| Q-02 | acceptance-criteria §二 vs test-plan §1 | "安全红线 S-01~S-19 \| 19/19 单元测试通过" vs "不覆盖：v1.1+ 功能（**定向遗忘**/社会性校准等）" | 逻辑矛盾 | S-16/S-19 就是定向遗忘红线。验收要求 19/19 全过，测试计划把它踢到 v1.1+ 不测。发布 gate 会卡在"你说测了我说没测"。 |
| Q-03 | test-plan §1 vs §3.7 | §1 不覆盖定向遗忘 vs §3.7 引用 test-strategy §2.2 的 19 条红线（含 S-16/S-19） | 逻辑矛盾 | 同一文档内部自打脸。 |
| Q-04 | test-plan §3.6 vs test-strategy §四 | 两份"6 条 E2E"清单内容不一致（test-plan 有"审计链验证"无"校准中断→降级"；test-strategy 反之） | 逻辑矛盾 | 哪 6 条是权威？无单一事实源。 |
| Q-05 | test-plan §3.1/§3.5 | `W-01` 与 `W-001` 混用；`TC-C01-001` 与 `TC-CAL03-001` 混用 | 模糊表述 | 用例 ID 体系不统一，追溯会乱。 |
| Q-06 | test-strategy §2.2 | S-07 行 5 个单元格（表头 3 列） | 格式错误 | Markdown 表格结构破损，S-07 及后续行列对齐全乱，渲染即垃圾。 |
| Q-07 | benchmark-plan §3.2 | 只写"统计 P50/P95/P99"，不引 acceptance 的通过阈值 | 缺失关键细节 | 方法文档不自带判据，回归判定靠人肉翻另一份文档。 |

## 6. development/（4 份）

| # | 文档:位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| DEV-01 | development-setup §三 vs deployment §三 | `kairos init --db sqlite:///data/kairos-dev.db` vs 默认 `sqlite:///$HOME/.kairos/kairos.db` | 逻辑矛盾 | 开发和部署的默认库路径不一致，且没人说明是"故意不同"还是"没对齐"。 |
| DEV-02 | development-setup §三 vs deployment §五 | Postgres 用户 `postgres` vs `POSTGRES_USER=kairos` | 逻辑矛盾 | 本地跑通不等于部署跑通。 |
| DEV-03 | technology-stack §六 vs deployment §五 | 兼容矩阵"PostgreSQL 15–17" vs 镜像钉死 `pgvector/pgvector:pg16` | 缺失关键细节 | 矩阵与实际部署版本未互引，也没解释为何不锁上限。 |
| DEV-04 | coding-conventions §一 | 配置键示例同一行 `KAIROS_DAILY_BUDGET_FEN`（带前缀）与 `FORGETTING_SCORE_THRESHOLD`（无前缀） | 逻辑矛盾 | configuration 明确"所有配置统一 KAIROS_ 前缀"。命名规范自己打破自己的命名法，且示例键名与实际键不符。 |
| DEV-05 | integration-design §四 | "ERR-DB-*/ERR-LLM-* 仅日志记录" | — | 本身合理，但与 troubleshooting 冲突（见 O-15），冲突责任在后者未对齐契约。 |

## 7. governance/（9 份）+ README + user/ + references/

| # | 文档:位置 | 引用 | 分类 | 问题实质 |
|---|------|------|------|----------|
| G-01 | README L16 vs project-plan L17 vs changelog L24 | "无运行代码（注：amber/ 存在实验性引擎原型）" vs "代码尚未启动" vs "承认 amber/ 代码存在（main.py 734行 + API 19模块 + schema 449行）" | 逻辑矛盾 | 到底有没有代码，三份文档互咬。changelog 还引用了 README 不存在的 L152（README 全文仅 139 行）。 |
| G-02 | README L36 vs changelog L25/L40 | "31 张表 Schema" vs 同版本内"统一为 31 张表（2处）"又"新增 db/schema.sql（**29 表** / 524 行 DDL）" | 逻辑矛盾 | 同一份 changelog 同一版本 31 vs 29，无人解释。 |
| G-03 | README L110 vs debt-collection 实际 | "27 闭环 DC + 62 MNM + 11 待实现 D" vs 实际 DC-001~031（31 条）、MNM 共 69 条（001~062 + 101~107）、D 项 22 条 | 计数漂移 | README 的分解式是拍脑袋。所有"总数"类陈述均不可信。 |
| G-04 | README L119–122 | reviews 表中 `comprehensive-audit-report.md` 同一文件列两行 | 废话连篇 | 复制粘贴没过脑子。 |
| G-05 | changelog L51 | "10 大断裂带聚合为 meta-debt（DC-029~DC-031）……无需逐条补录" | 缺失关键细节 | 10 个断裂带落 3 个编号，无法反查对应关系，追溯链自断。 |
| G-06 | release-guide §1 vs §3 | "v1.0.0=设计冻结版，代码首版从 v1.1.0 起" vs 示例 `git tag v1.0.1` / `pip install kairos==1.0.1` | 逻辑矛盾 | 无代码前提下 v1.0.1 无从发布，模板没对准现状。 |
| G-07 | cognitive-architecture-gap L27–34 | G-05~G-12 各行多一个空管道符，"闭环判据"整列被挤空 | 格式缺陷（致命） | **12 项差距中 8 项无闭环判据**——一个 Markdown 表格 bug 让"差距追踪"对多数项没有验收出口。 |
| G-08 | cognitive-architecture-gap L29 vs L40 | G-07 行内"受控偏离" vs 统计表归"能力缺口（降维）" | 逻辑矛盾 | 同一文档两种分类。 |
| G-09 | documentation-governance §4 | "代码启动前，全部文档保持 draft 状态" vs 状态表列 "v1.0.0 \| 可依赖" | 逻辑矛盾 | 规则自抽耳光；adr.md 用 v1.0.0 既违规又"合规"。 |
| G-10 | adr.md frontmatter | `status: v1.0.0` | 逻辑矛盾 | 9 份治理文档 8 份 draft，唯独 ADR 破例。治理规范的带头破坏者。 |
| G-11 | risks.md R-004 | 状态 "mitigated" vs 正文"当前剩下的'执行+立法'两权集中"、缓解="v2.0 重新评估" | 自相矛盾 | 标着已缓解的风险，正文在论证它没缓解。 |
| G-12 | social-calibration-roadmap L79/L110 | "单Agent系统已在**生产环境稳定运行**至少 3 个校准周期"为 M2 触发条件；"D-305 已有初步进展" vs D-305 自述"认知层面开放问题，无方案" | 逻辑矛盾 | 零代码系统把"生产稳定运行"写进门槛；"初步进展"与债务项自述矛盾。把幻想当验收门槛。 |
| G-13 | debt-collection L168 vs L424 | D-304 列于"需实现阶段完成项"又自称"已并入 DC-019+DC-027 闭环"，DC-028 又记"已闭环" | 自相矛盾 | 追踪链补丁自己制造重复条目。 |
| U-01 | quick-start L19 vs L107 | "5 分钟跑通" vs "全部操作约 2 分钟" | 自相矛盾 | 连宣传口径都不统一。 |
| U-02 | quick-start L55 vs user-guide L36 | `kairos init --db sqlite:///$HOME/.kairos/kairos.db` vs `kairos init --db ~/.kairos/kairos.db` | 逻辑矛盾 | 一个带 `sqlite:///` 协议前缀一个裸路径，照抄必有一份报错。 |
| U-03 | quick-start L29 vs user-guide L63–70 | "前置条件阶段无需手动设置任何密钥" vs `KAIROS_DB_DSN`/`KAIROS_LLM_API_KEY` 必填且无默认值 | 逻辑矛盾 | "开箱即用"与"必须手填"打架。 |
| U-04 | user-guide L186 | `# 种子路径设置` 裸在正文中 | 格式缺陷 | 被渲染成一级标题，配置行没进代码块。 |
| R-01 | domain_keywords.yaml 注释 | "用于领域路由检索（architecture §10.16/§3.1）" vs "v1.0 种子版本：……无同义词/权重/匹配规则" | 缺失关键细节 | 空壳关键词表挂靠路由算法章节，占位即宣称完成。 |
| R-02 | value-dimension-entropy §二 vs usage-load-algorithm §一 | "H < 0.5 触发应急冻结" vs 负载系数"检索 1.2（最低）……内隐 2.0（最大）" | 逻辑矛盾（算法级） | 熵算法拿"五维均匀分布"当健康基线，负载算法承认维度天然不均、检索主导正常。**一个正常的检索密集型系统会被熵算法判为坍缩并触发应急冻结**。且单标量 H 触发冻结直接撞 P6"禁止无声丢失维度信息"。真实设计缺陷。 |
| R-03 | value-dimension-entropy §二 | "健康 H ≥ 1.0 / 坍缩 H < 0.5" | 模糊表述 | H_max=2.32，阈值 1.0/0.5 无任何推导，纯拍数。 |
| R-04 | vad-coordinate-algorithm L46 vs L55 | V/A/D_init clamp 至 [-1,1] vs 巩固阶段 A"归一化至 [0,1]" | 缺失关键细节 | 同一 A 在两个阶段量程不同，用重映射值还是原值没说，单位混淆隐患。 |
| R-05 | error-reference L70 | "ERR-LLM-002（同 ERR-RATE-003，建议统一使用 ERR-RATE-003）" | 废话连篇 | 自承重复码还留着，技术债明摆着不清理。 |
| R-06 | traceability-map L91 | "C-35 社会性校准 \| **D-210** 跨Agent互信模型" | 逻辑矛盾 | 真实编号是 D-310，**D-210 不存在**。指向幽灵债务编号。 |
| R-07 | traceability-map L87 | "C-33 \| 降级状态机整体待实现（见 **D-306**）" | 逻辑矛盾 | D-306 是"四轴完整度量函数"，降级状态机实为 D-001（已闭环）。指错债务项。 |
| R-08 | traceability-map L99 | "C-01 四轴正交（时间轴）\| G-01 认知完整性轴三维度量" | 逻辑矛盾 | 时间轴声明映射到完整性轴差距，跨轴错配，违反自己声明的"仅建立直接对应"。 |
| R-09 | traceability-map L85 | "VAD 完整度量是四轴度量子集" | 概念混淆 | VAD 是情感纹理，不在四/五轴之内。 |
| R-10 | traceability-map L16 | "claim-matrix（37 声明）""debt-collection（11 开放 + 7 已闭环）" | 计数漂移 | 正文映射实际只出现 21 个 distinct C 编号；债务实际 22 D + 31 DC + 69 MNM。号称解决追溯断链的文档自己是断链制造机。 |

---

# 第二部分：跨文档一致性对齐（汇总）

## X-1 排序链：6 级还是 7 级？身份进不进链？【最严重】

| 文档 | 说法 |
|------|------|
| cognitive-foundation L30/L79/L372 | 六级链，身份为独立正交治理面，不在链中 |
| architecture §0/L97、§11 术语表、版本记录 | 六级链 + 身份否决权 |
| architecture §3.2 L768 | **七级链，身份居链首** |
| architecture §3.2 L773 / L780 | 同节又称"六级链"和"7 级优先级链" |
| design-philosophy-relations L43/L107 | **七级链，身份居首**，并把权威定义指向 architecture §3.2 |
| glossary §四 | "六级辞典式排序链……+ 身份面否决权" |

这不是哲学分歧，是必须落进裁决器代码的硬逻辑。任何实现者照这套文档写裁决器，都会在"身份要不要参与排序比较"上踩坑。**头等文档债务，必须先裁决单一事实源再谈其他。**

## X-2 价值维度/轴的数量口径

- cognitive §1.1：**五轴**（使用/见证/时间/认知完整性/可及性）；glossary 同。
- architecture §3.2 Pareto 输入：**4 向量**（使用/见证/情感效价/时间衰减），缺两轴、多 VAD。
- claim-matrix C-01：**四轴**正交（使用/见证/时间/认知完整性）。
- debt-collection D-306 / traceability-map：**"四轴完整度量函数"**。
- traceability-map L85 还把 VAD 说成"四轴度量子集"（VAD 根本不在轴内）。

四轴、五轴、4 向量三套口径并行，无桥接说明。

## X-3 检索权重：三套互不映射的维度词汇 + 归一化三方冲突

- api-spec §1.2：semantic/path/context/temporal/relational（五维）。
- feature-list R-09：语义+BM25+时序+信任+热度（五维，另一套名字）。
- rl-weight-spec：relevance/recency/frequency/explicit_feedback/entity_boost/trust_score（六维，正文自称"五维"）。
- 归一化：data-model 要求 Simplex 和=1；rl-weight-spec 声明和≠1 正常；默认值实际 1.05；api-spec 返回 1.05。**data-model 的约束永远无法满足。**

## X-4 记忆状态机

- data-model / feature-list M-10：五态（active/stale/archived/suppressed/superseded）。
- implementation-map §四：四态（漏 suppressed）。
- data-model："suppressed 是 archived 子态"；use-cases：两者正交且复兴例子用错对象。

遗忘/抑制/复兴逻辑的基石，四处四个说法。

## X-5 向量维度：1024 vs 1536

nfr-specification 写轻量模式存储 1024 维；system-context 与 data-model 明确"线性投影至 1536，DDL 以 1536 为准"。按 nfr 建索引就是错的。

## X-6 CLI 与密钥契约未冻结

- 密钥生成：`kairos admin key generate`（security-spec）vs `kairos init --init-key`（deployment/runbook/dev-setup）。
- 密钥数量：4 个（dev-setup）vs 5 个含 LLM Key（deployment）。
- DB 连接串：`sqlite:///` 前缀（quick-start/deployment）vs 裸路径（user-guide）。
- 默认库路径：`data/kairos-dev.db`（dev）vs `~/.kairos/kairos.db`（deploy）；Postgres 用户 `postgres` vs `kairos`。

## X-7 部署链自洽性崩坏

deployment compose：服务名 `db` ↔ runbook 备份命令用 `kairos-db`（不存在）；不设 `KAIROS_LITE_MODE=false`（默认 SQLite）；漏必填 `KAIROS_LLM_ENDPOINT`；环境变量总表漏 `KAIROS_WAL_ARCHIVE_RETENTION_DAYS`；迁移目录与 coding-conventions 冲突。**照文档部署"标准模式"，得到的是一个用 SQLite、连不上 LLM、备份命令报错的系统。**

## X-8 安全红线定义权分裂

configuration §7 把 SSRF/WAL 当红线；security-spec 红线册 S-01~S-19 不含它们；threat-model 列了 SSRF 威胁和控制但无 S 编号；threat-model 的 STRIDE 主表又没正经分析 S-07/S-08/S-09。红线册、威胁模型、配置文档三方各管一段，"红线 100% 覆盖"无法审计。

## X-9 测试范围与验收互咬

- 定向遗忘（S-16/S-19）：security-spec/acceptance/test-strategy 认定 v1.0 硬指标；test-plan §1 划入 v1.1+ 不覆盖（且与自己 §3.7 冲突）。
- E2E"6 条"：test-plan 与 test-strategy 两套不同清单。
- 吞吐验收 500 ops/s 在限流 120/min + 基准最大 100 并发下物理不可达。

## X-10 错误码暴露策略双标

integration-design："ERR-DB-*/ERR-LLM-* 仅日志记录，不暴露"；troubleshooting 把 ERR-DB-001/ERR-LLM-001 当用户可查索引。契约与排障指引相反。

## X-11 全库计数漂移（所有"总数"均不可信）

| 事实 | 说法 A | 说法 B | 实际核对 |
|------|--------|--------|----------|
| 数据表 | README/changelog"31 张" | changelog 同版本"schema.sql 29 表" | DDL 与规格未对账 |
| 功能总数 | feature-list L17"102（43+59）" | L23"101"、L208"43+58=101" | A 段实际 11 项非 12 |
| API | api-spec"57 端点" | operation-catalog"53 操作" | 2 个端点重复定义，缺口无解释 |
| claim ✅ | 警告"30 个" | 完整承载清单 28 项 | 实际表内 27 个 |
| MNM | README/changelog"62" | — | 实际 69（001~062+101~107） |
| DC | README"27" | — | 实际 31（DC-001~031） |
| 债务 D | traceability"18（11+7）" | — | 实际 22 条 D 项，另有 DC/MNM 未提 |
| C 声明映射 | traceability"37 声明" | — | 正文仅出现 21 个 distinct C 号 |

## X-12 "代码存在性"叙事失真

README"无运行代码（amber/ 原型）" ↔ project-plan"代码尚未启动" ↔ changelog"amber/ main.py 734 行 + 19 模块 + schema 449 行"，且 changelog 引用 README 不存在的 L152。feature-list 还写"架构已实现"。**一个项目连"我们有没有代码"都说不清楚。**

## X-13 references 算法与上游文档的断裂

- 熵算法与负载算法底层假设互斥（R-02），且都声称承载 P6，而熵算法的单标量冻结触发本身违反 P6。
- traceability-map 的 D-210 幽灵编号、D-306 错指、C-01→G-01 跨轴错配（R-06~R-08）。
- domain_keywords.yaml 空壳挂靠 architecture 路由章节（R-01）。

---

# 第三部分：评分体系

评分范围 0–100；≥85 优 / 70–84 良 / 55–69 中 / <55 差。

| 维度 | 权重 | 得分 | 等级 | 依据 |
|------|------|------|------|------|
| 文档内部一致性 | 20% | 42 | 差 | architecture §3.2 同节三种链级说法；feature-list 三处总数互斥；claim-matrix 三个数全错；test-plan §1 vs §3.7 自打脸 |
| 跨文档一致性 | 25% | 31 | 差 | 排序链 6/7 级三文互咬；维度四套口径；权重归一化三方冲突；状态机四处四说法；CLI/密钥/路径全线未对齐 |
| 可追溯性 | 15% | 35 | 差 | traceability-map 幽灵编号+错指+跨轴错配；RTM 仅 5 行；差距表 8/12 无闭环判据；计数全面漂移 |
| 可实现性/可操作性 | 15% | 45 | 差 | 部署示例照抄即错；吞吐验收物理不可达；熵算法会误冻正常系统；但 API/数据模型骨架尚可落地 |
| 术语治理 | 10% | 55 | 中 | glossary 本身质量尚可、覆盖广，是全库少有的亮点；但"熵"多义、claim/embedding 缺定义、四轴/五轴未桥接 |
| 完整性（关键细节覆盖） | 10% | 58 | 中 | 配置键、错误码、算法公式覆盖面大；但 NFR 不可度量项、requirements 三列表、威胁模型缺场景拉低 |
| 信息密度（反废话） | 5% | 50 | 差 | cognitive-foundation 数十处自我免责修辞；configuration 重复定义；README 重复行 |
| **加权综合** | 100% | **41.5** | **差** | — |

单项文档粗评（仅列两端）：
- 相对最好：glossary.md（~75 良）、vad-coordinate-algorithm.md（~70 良）、technology-stack.md（~72 良）、observability.md（~68 中）
- 最差：traceability-map.md（~25）、cognitive-architecture-gap.md（~30，表格 bug 致 8/12 判据丢失）、feature-list.md（~35）、rl-weight-spec.md（~38）、deployment.md（~40）

---

# 第四部分：综合评价（绝对客观）

**整体态势**：这是一个设计野心极大、文档产出量极大、但工程纪律接近于零的文档库。50 份文档呈现出"多人/多轮分头起草、从未做过一次全库对齐"的典型形态：每份文档单独看都像模像样，放在一起就互相拆台。项目自建的治理机制（documentation-governance、traceability-map、debt-collection、cognitive-architecture-gap）本应是纠偏工具，实际上是全库质量最差的一批——治理者自己是最大的被治理对象。

**最危险的事实**：三个。①排序链 6 级还是 7 级、身份进不进链，三份 foundation 文档给出相反答案，而这是要落进裁决器代码的宪法级不变量；②检索权重三套维度词汇 + 归一化三方冲突（和=1 vs 和=1.05），检索是系统心脏，照现文档实现必然写出互相矛盾的代码；③吞吐验收目标在自己定义的限流下物理不可达，发布 gate 从设计上就过不去。

**亮点**：glossary 是全库唯一接近"单一事实源"标准的文档；references 三份算法文档给出了可执行的公式和阈值（尽管熵算法有设计缺陷）；配置键、错误码、安全红线的覆盖广度显示了认真的意图；claim-matrix"视觉误导警告"这类自省机制方向正确（可惜自己数错数）。31 张表的 data-model 与 implementation-map 的表数核对是全库少数对得上的数字。

**结构性技术债**：①无单一事实源机制——同一事实（链级、维度数、状态机、总数）散落多文档各自发挥，无权威指针；②计数类陈述全面失信——31/29、101/102、62/69、27/31、57/53、37/21、18/22，没有一组对得上；③"设计冻结"是幻觉——draft 状态 + 零验收标准 + 零代码的东西自称冻结；④自我免责修辞泛滥替代真实决策，"受控偏离/认知诚实性声明"数十处堆叠，本质是把"未决"包装成"诚实"。

**落地优先级判断**：1）立即裁决排序链与身份面归属，改掉 architecture §3.2 和 design-philosophy——这是一切实现的前提；2）统一检索维度词汇表与权重归一化语义（改 data-model 或改 rl-weight-spec，二选一）；3）修 cognitive-architecture-gap 的 Markdown 表格 bug 和 traceability-map 的幽灵编号——半天工作量，收益立竿见影；4）对齐 CLI/密钥/部署链（compose、容器名、LITE_MODE、LLM_ENDPOINT）；5）仲裁测试范围（S-16/S-19 属于 v1.0 还是 v1.1）与吞吐验收的限流前提；6）全库计数重数一遍并写进 changelog。上述 1–3 不做，任何"启动编码"都是在斜地基上盖楼。

**一句话结论**：概念大厦宏伟，事实地基稀烂——先让 50 份文档对同一个事实说同一句话，再谈实现。

---

*审查方法：4 组并行逐字通读（foundation / specification / ops+security+quality+development / governance+user+references+README），每组独立提取带原文引用的缺陷与术语定义清单，主审汇总跨文档比对。*
