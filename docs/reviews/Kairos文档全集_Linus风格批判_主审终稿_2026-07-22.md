---
title: Kairos 文档全集 Linus 风格批判（主审终稿）
created: 2026-07-22
status: review-output
note: 本文为对 D:\projects\kairos\docs 下全部源文档的独立主审批判。逐字通读由主审 + 4 个并行子审查代理完成，关键数字矛盾已由主审用 grep/Read 二次核验（文中标注「主审核验」）。
---

# Kairos 文档全集 · Linus 风格代码审查级批判（主审终稿）

> 风格说明：严苛、务实、直击要害。每条问题都给【文档 + 位置 + 实质】。不刻意找茬，但凡真问题一针见血。区分三类：🔴 设计缺陷/硬矛盾（必须修）、🟡 模糊/缺失/过期（该补全）、⚪ 废话/轻（可删）。

---

## 0. 总判决书

这套文档最大的问题不是某句话写错了，而是**它假装自己描述了一个系统，而系统连一行代码都没有**——并且这个"没有代码"的事实被埋进 frontmatter 的 `draft`、changelog 的小字、user 文档的"未来命令"里，同时大段正文用完成时态宣布"核心能力已发布""ADR 已采纳""27 项债务已闭环"。

一个标榜 `foundation/architecture-v1.0.0.md` 为「全体系设计权威」的项目，连**系统有几层、维度基数是多少、债务到底几条、评审清单引用的文件名**这种最应该权威的数字/事实都自相矛盾或对不齐。草稿不是借口；声称权威却对不齐自己，比没有文档更糟——因为它会骗人。

最该挨骂的三件事，按危害排序：
1. **章节号系统性漂移**：架构重排后（插入 §4 推理皮层，存储层 §4→§5），下游 11 篇规格几乎全部还指着旧的 §4.2，等于给实现者发了一叠指向错误坐标的地图。
2. **数字三套口径互不咬合**：43 能力 / 37 声明 / 11 组件映射 / 10~11~18 债务 / 12 差距——全库没有一个地方能把"功能→认知声明→组件→债务→测试"连贯追完。所谓"可追踪需求基线"目前只追了 12%。
3. **安全与性能参数自己打自己**：限流 1 ops/s、安全红线 100 ops/s、基准门槛 100 ops/s 写入吞吐，三者不可能同时成立。

---

## 1. 主审核验过的全局硬伤（已用 grep/Read 二次确认）

| # | 矛盾 | 证据 | 实质 |
|:--|:-----|:-----|:-----|
| H1 | 评审清单与磁盘对不齐（非计数打架） | README L123 标题"50 份"，其分解式 `3+11+4+9+6+4+2+2+6+2+1`=**50**，与实际磁盘 50 份文档（不含 3 个 `.workbuddy/memory` 文件）**三者自洽**；但 README L118–119 评审文档索引列出 `Kairos文档全集_Linus风格批判报告_2026-07-22.md`（磁盘不存在），却遗漏实际存在的 `Kairos文档全集_Linus风格批判_主审终稿_2026-07-22.md` | 计数本身没错，错在索引引用了过期/不存在的文件名、漏列了真实文件——读者按索引去找会扑空。**主审核验：磁盘确为 50 份文档，非 52。** |
| H2 | （已订正）specification 数量无误 | README L34–44 规格表实际列出 **11** 个文件，含 `rl-weight-spec.md`（L44），与 L123 的 `specification 11` 一致；`rl-weight-spec.md` 已在索引内，并非"幽灵文件" | 原主审将此表误读为 10 项（漏看 L44），此处订正。rl-weight-spec 的真实问题见 §2.2 / §3.2（无 `rl_weights` 表、无 `POST /v1/feedback` 端点、权重维度与架构 §10.14 脱钩），与是否在索引无关。 |
| H3 | 架构章节重排未向下游同步（系统性 off-by-one） | `architecture-v1.0.0.md` 标题：`## §4 推理皮层`、`## §5 存储层`、`## §8 安全红线`。`feature-list.md` 却把存储层组件全标 `§4.2`（应为 §5.2）、`§6.3`(应为 §7.3)、`§4.6`(应为 §5.6)、`§8.8`(应为 §10.10)。**主审核验：§4=推理皮层、§5=存储层 确凿。** | 整批规格引用的"设计权威章节"大半已失效。 |
| H4 | 债务计数 10 / 11 / 18 三说 | `debt-collection.md` 实有 `D-201…D-211` = **11** 条；`changelog.md:61` 写"18 待实现"；`traceability-map.md` 标题写"10 债务"。**主审核验：D-201…D-211 确存 11 条。** | 同一概念三个数，谁说了算都不知道。 |
| H5 | 限流/安全/基准三处量级互斥 | `configuration.md`: `KAIROS_RATE_LIMIT_WRITE_PER_MIN=60`（=1/s）、`READ_PER_MIN=120`（=2/s）；`security/threat-model.md` S-02："≤100 ops/s"；`quality/benchmark-plan.md §3.3`：写入吞吐"≥100 ops/s"。**主审核验：60/120 与 * 默认值确凿。** | 单客户端 1/s 永远撑不起"≥100 ops/s 写入吞吐"的发布门槛——要么限流是摆设，要么基准永不可过。 |
| H6 | SSRF 默认全放通 | `configuration.md`: `KAIROS_SSRF_ALLOWED_HOSTS = *`（"无限制"），仅靠 `IP_CHECK` 兜底。**主审核验：默认 `*` 确凿。** | 安全反模式：默认 deny 才是正解，这里默认 allow。 |
| H7 | P6「铁律」已被自己打破却不叫破 | `cognitive-architecture-gap.md G-07`：压缩比 33%/43% 均超 30% 上限、活跃例外 4>2；`architecture §0.6/§10.11` 同时给 12 维/14 维/33%/43% 多口径；`cognitive-foundation.md E.7` 又说 10+ 维、压缩 3–4 维。 | 全系统维度基数（10/12/14）和压缩数（3–4/6）三处对不上，且把"已破的红线"标成"受控偏离"却不给消除条件。 |

---

## 2. 逐文档批评

### 2.1 foundation/（地基文档）

**README.md** 🔴⚪
- 【L123 计数实为自洽】标题"50 份"、分解式 3+11+4+9+6+4+2+2+6+2+1=50、磁盘实际 50 份，三者一致（见 H1 订正）——计数没翻车。
- 【L118–119 评审清单 stale】索引列出磁盘不存在的 `Kairos文档全集_Linus风格批判报告_2026-07-22.md`，漏列实际存在的 `主审终稿`；规格表 L34–44 实际列 11 项（含 rl-weight-spec，见 H2 订正），并非 10。
- 【L16 状态措辞】"无运行代码"与各文档 `status: draft` 一致——这点没毛病，但架构已写到事件总线 JSON schema、完整安全红线，草稿/定稿边界含糊，读者分不清哪句是承诺哪句是设想。
- ⚪ 索引本职是"对账"，结果自己算术翻车，纯属粗心。

**architecture-v1.0.0.md** 🔴🔴（标榜"设计权威"，问题最密集）
- 【层数五套说法】L112 同节内同时出现"五层功能栈""六层（主权面计入）""7 个结构单元"；L163 又说接入层"不纳入编号"；L170–177 一致性表又把接入层列为独立行。系统到底 5/6/7 层，文档自己没定。
- 【"1–4 层" vs "1–5 层"】§1.1/§1.3 写宪法主权面"与 1–4 层正交"，§11 术语表写"与 1–5 层正交"——同源矛盾（接入层算不算功能栈）。
- 【结构原则"四类"vs"六类"】L188 仍写"现有四种结构原则"，L308/L346 已改为"六类"。
- 【P6 压缩比多口径】§0.6/§10.11 并列 ~33%(12维)/43%(14维)；§3.3 自己算 6/14≈43%；但 2 类压 3 维应得 3/12=25%，推不出 33%——凭空数字当事实。
- 【章节引用错指】§5.3/§5.6 把"差异检验"指向 §10.7（实为设计约束表），正确在 §5.5；§7.3 把注意力调度器指向 §4（实为 §9）；§3.3/§10.14 引用 `specification/rl-weight-spec.md` 但该文件不在索引（H2）。
- 【整段复制粘贴】L1318/L1320 几乎原样重复且粘了残缺的 `**：` 格式；"自利倾向告警"段在 §6.2/§9.1/§9.2/§10.2 一字不差重复 4 次；§9.2 与 §10.2 职责表重复。

**cognitive-foundation.md** 🟡⚪
- ⚪ 通篇"诚实性声明/受控偏离声明/边界声明"通胀，L116 自嘲"声明归因声明"承认泛滥却仍不删——信噪比极低。
- 【P6 跨文档矛盾】E.7 写"10+ 维、压缩 3–4 维(≤30%)"，与架构 §3.3 的"14 维、压缩 6 维(43%)"对不上（见 H7）。
- 【§2.2 标题漏 P6】标题"P1–P5"，P6 在 §2.3，正文却反复引 P1–P6。
- 【L75/L79 "正交"软化】把"五轴正交"退成"设计假设"，但下游架构照当刚性约束用，地基被自己挖松。
- 【物理行号引用】大量"(L216-221)"指向作者私有行号，读者无法定位，纯死链。

**design-philosophy-relations.md** 🔴⚪
- 【悬空引用架构 §4.3/§4.5/§4.6】全文多处引"§4.3 差异检验/§4.5/§4.6 受控例外"，但架构 §4 只有 §4.1/§4.2（推理皮层），这些子节不存在（主审核验 §4 无 §4.3+）。
- 【章节归属漂移】把"辞典式裁决器"引到 §3.2（实为 §3.3）、"真理模式切换协议"引到 §3.2（实为 §0.4）、"保守倾向闸门"引到 §3.2（实为 §3.3）——作为"理念→架构地图"系统性指错。
- 【排序链自相矛盾】总览图/映射链写完整七级链"身份>探索>宪法>校准>认知完整性>时间>间接度"，L93 却写"身份>校准>时间"——漏了中间环节且非连续截取。
- ⚪ L16 自称"不重复理念完整声明"，下文又把内容铺一遍。

### 2.2 specification/（规格文档）

**system-context.md** 🟡（最干净之一）
- 【外部依赖·嵌入模型】"默认 BGE-M3"无限定词；`requirements-baseline §3` 注明"BGE-M3 轻量模式"，标准模式默认 `text-embedding-3-small`——无限制词会误导实现者。
- ✓ "17 条安全红线"数字对（S-01..S-17）。

**use-cases.md** 🟡
- 【场景2·步骤3】降级"路径前缀匹配"，但架构 §5.2 写降级是"全文检索(tsvector)"——两处落点不同，需裁定。
- 【场景6】引用 `ops/configuration.md` 的 N/M 参数，但该文档未交付具体值，关键阈值甩给未交付文档。
- ✓ 其余场景与架构 §5.2/§5.4/§10.9 一致。

**feature-list.md** 🔴🔴（全批最该挨骂的规格）
- ✓ 总计 43（7+8+6+4+3+2+6+7）加总正确——唯一做对的数。
- 【章节号系统性错乱】W-01/W-03/W-06 引 §6.3（应为 §7.3）；W-04/R-01…F-03 一整批引 §4.2（应为 §5.2）；M-01 引"§5.2 推理皮层"（§5.2 是存储层，推理皮层是 §4）；CAL-06 引 §8.8（应为 §10.10）；A-01 引 §7 安全红线（应为 §8）。
- 【三处自填"—"却明明有承载】M-06/SF-04/A-03 写"无对应架构组件"，但 `api-spec` 有 `export`/`sublimation/status`/`scheduler/status` 端点、`data-model` 有 `sublimation_queue`——能力清单自己说没承载，权威文档已承载。
- 【引用悬空文件】W-05"见 glossary §2"、SF-03"D.8"、A-04"B.2" 不在本批范围，无法核验。

**requirements-baseline.md** 🔴
- 【RTM 空头矩阵】§4 只列 W-01/W-02/R-01/R-02/CAL-01 五项就"…"，43 项能力 38 项无追踪，却称"受管的可追踪需求基线"。
- 【RTM 错引 §6.3】同 feature-list 的过期心智模型（应为 §7.3）。
- 【"默认 BGE-M3"】无限定词，同 system-context 歧义。
- ✓ §2 NFR 与 nfr-specification 一致。

**api-spec.md** 🔴
- 【导出端点违反红线】`GET /v1/memories/{id}/export` 返回"导出格式的记忆完整内容"，直接违反架构 S-07 与 nfr §五 的"导出脱敏"。明文敏感信息出网。
- 【游离端点】§4 事件总线后突插 `GET /v1/memories/{id}?level=`（行 361），结构错位像补丁没归位。
- 【错误码两张皮】§5 要求调用方按 `ERR-*` 处理，但端点响应只返回裸 HTTP 状态，从不携带 `ERR-*`。
- 【CLI 计数少算】版本记录"24 条"，§四 又新增 3 条（≥27），implementation-map 也照抄 24。

**data-model.md** 🔴
- 【表计数跨文档错位】README L36 / implementation-map L57 称"11 张核心表"，而 data-model 实际定义 **19 张**（版本记录 L331 自陈"19 张表（11 核心 + 8 张 v1.0 新增补充表）"）。"核心 11"与"全量 19"口径未统一——按 README 的 11 去对账会漏掉 8 张新增表（sublimation_outputs / memory_states / knowledge_evolution / journal_entries / session_summaries / daily_reports / weekly_packs / user_profiles）。
- 【memory_types 字段异味】定义为 TEXT 却建 GIN 索引（GIN 应挂 jsonb/数组）。
- 【缺 raw/item 中间态】`memories.status` 只有 active/archived/suppressed/superseded，但 detailed-design §2、架构 §7.3 都描述摄取期"不可检索的 raw 态"——状态机与数据模型脱节。
- 【缺 rl_weights 表】rl-weight-spec 要求权重存 `rl_weights`，data-model 无此表。

**detailed-design.md** 🔴
- 【§7 Markdown 破损】行 333–335 空代码围栏残桩；行 338 开启的 `LAYER_DISTILL` 代码块从未闭合，导致后续正文被吞进未闭合代码块，渲染必崩。
- 【未定义符号】`REASONING_LOOP` 引 `PREDICTOR`/`CORTEX`/`EVENT_BUS`，全文未定义（架构里叫预测器/策略层/事件总线）。
- 【§1 WM 7±2 槽位】魔法数，无容量预算来源。

**implementation-map.md** 🟡
- 【"11 张表"照抄 data-model 错误】继承上游腐烂（实为 19）。
- 【组件数"约 40"实为 44】6+5+4+8+6+6+3+6=44，"40+"字面成立但偏少。
- 【CLI 24 条】同 api-spec 少算 3 条。
- ✓ §8 "10 类事件枚举"与架构/api-spec 一致。

**nfr-specification.md** 🟡（最干净）
- ✓ 指标表与 requirements-baseline/架构一致。
- 🟡 §一"升华批处理 ≤30s…源自架构 §10.5 理论推导"，但架构 §10.5 是观测指标表，未给 30s/60s 推导来源——"理论推导"无锚点。

**claim-implementation-matrix.md** 🟡（最诚实）
- ✓ C-01..C-37 共 37 条计数正确。
- 🟡 37 条"认知声明"与 feature-list 43 项"功能"是两套互不相干的 taxonomy，全篇无任何一行把 C-xx 映射到 W-/R-/M- 功能——"声明-承载对齐"只对齐到架构章节，没对齐到功能清单。

**rl-weight-spec.md** 🔴（最新却最悬空）
- 【权重维度脱钩】定义 relevance/recency/frequency/user_feedback/trust_score（5 维）；架构 §10.14 基线公式是 w_v(语义)+w_l(bm25)+w_t(时间)+w_r(可靠)+w_h(热度)（6 维），词汇不交集——实现者不知每个 RL 权重乘到公式哪一项。
- 【初始化哲学冲突】"随机初始化 + Softmax 归一" vs 架构固定权重(0.40/0.20/0.15/0.10/0.15)。
- 【引用不存在的端点/表】`POST /v1/feedback`（api-spec 无此端点）、`rl_weights` 表（data-model 无此表）。
- 【优化器参数不一致】"Cosine 学习率衰减" vs 架构 `KAIROS_RL_DECAY_FACTOR=0.97` 固定值。

### 2.3 development/（开发文档）

**technology-stack.md** 🟡
- 【连接池触发阈值】"连接数 >> CPU 核数时介入"——`>>` 无操作定义，未给阈值。
- 【pg 版本】兼容矩阵写 PG 15–17，deployment 锁 pg16，development-setup 用 pg15——三处大版本不一致。
- 🟡 选型与部署"模式切换如何决定用哪个嵌入模型"未衔接。

**development-setup.md** 🔴
- 【pg 版本】§三 `pgvector/pgvector:pg15`，deployment 用 `pg16`——同项目大版本三说。
- 【SQLite 路径三说】`kairos init --db sqlite:///data/kairos-dev.db`，deployment 用 `--db`（无参），reliability 假设 `~/.kairos/kairos.db`——三处三路径。
- 【外部硬链接】仓库 `github.com/JohnL1989/kairos.git` 纯手写，无校验。

**coding-conventions.md** 🔴
- 【配置键前缀自破】§一示例 `FORGETTING_SCORE_THRESHOLD` 缺 `KAIROS_` 前缀，而 configuration 全为 `KAIROS_*`——规范自己违反自己。
- 【日志 schema 两版】§四列 7 字段；observability §二列 12 字段且用 `timestamp` 非 `time`——同项目两份日志契约必有一份作废。
- ⚪ §一"async def + _async 后缀（仅在不表达时）"——"仅在不表达时"无判定标准，废话规则。

**integration-design.md** 🟡
- 【超时语义未区分】§二写入/检索同步超时 10s，§一/§六客户端默认 30s——socket 级 vs 操作级未区分。
- 【Webhook 待 v1.1】核心异步通知机制 v1.0 缺失，却未在 quality "不覆盖"清单声明，造成能力真空。

### 2.4 ops/（运维文档）

**observability.md** 🔴
- 【告警占位符未填】§三校准中断告警"距上次校准 > N 周期 / > M 周期"——N、M 全文无值，模板填空没填完，规则不可执行。
- 【健康检查 schema 两版】§二含 `pool_available`，deployment §四 只有 `pool_connections`——不一致。
- ⚪ §二同时有 `logger`/`module` 两高度重叠字段，冗余。

**reliability.md** 🔴
- 【API RPO 自相矛盾】表列"Kairos API（RPO ≤1 天）"又列"Kairos API（无状态）（RPO —）"两行——无状态组件先给 RPO 再否认，读者不知 API 到底有无需恢复状态。
- 【缓冲写入 vs RPO 冲突】§1.3"写入确认基于内存缓冲收讫而非落盘"，与 §二数据库 `RPO ≤5 分钟(WAL)` 冲突：ack 在落盘前返回，崩溃丢已确认写入。
- 【SQLite 路径】§1.1 `~/.kairos/kairos.db` 与 deployment/development-setup 三说。

**troubleshooting.md** 🟡
- 【错误码索引表断裂】"错误码索引"行只有第一列，后续 ERR-* 作独立行续写，Markdown 表格错位。
- 【恢复命令指向未实现 CLI】`kairos admin key rotate`/`db verify`/`db repair` 全部指向不存在的 CLI。
- 【引用未登记变量】`ERR-RATE-001/002` 让运维调 `KAIROS_RATE_LIMIT_WRITE_PER_MIN`，但该变量不在 deployment §三（只在 configuration §7）——故障文档引了部署文档未列的变量。

**deployment.md** 🔴🔴
- 【环境变量表 vs configuration 严重错位】deployment 列 `KAIROS_DAILY_BUDGET_FEN`/`CORE_LIMIT_*`/`SEARCH_DEFAULT_LIMIT`/`SCHEDULER_INTERVAL`/`ADMIN_IPS` 等**在 configuration 中缺席**；反之 configuration §7 的 `RATE_LIMIT_*_PER_MIN`/`INPUT_LIMIT_*`/`SSRF_*`/`WAL_ARCHIVE_*` **未出现在 deployment**。照 deployment 配必漏关键安全/限流参数。
- 【Docker db 端口未暴露】§五 compose 只 `kairos:8010:8010`，但 runbook §2.1 恢复命令 `pg_dump -h localhost`——宿主机连不到容器内 PG，自家部署与自家恢复手册互斥。
- 【功能等价自相矛盾】§一文字"三种模式所有核心功能等价"，同表显示轻量"无元认知层"、策略层"受限"——等价 vs 能力深度不同，自己打架。
- 【引用未登记参数】§七 `KAIROS_LOG_LEVEL` 既不在 §三 表也不在 configuration。

**runbook.md** 🟡
- 【备份对象不存在】§2.2 备份 `config.yaml`/`.env`，但 deployment 数据目录无此二文件（靠 env 注入）。
- 【localhost 恢复在部署形态下必失败】同 deployment 未暴露 db 端口（见上）。
- 【配置管理三套口径】runbook 用 `kairos config show/set/reset` + 配置文件；deployment 只讲 env；configuration §二 说"环境变量或配置文件"却从未定义配置文件格式——三处口径不一。
- ⚪ 全篇命令均属未实现 CLI，对当前阶段零可执行性。

**configuration.md** 🔴🔴
- 【"幽灵表"】§7 之后突插一份 2~3 列不齐的表，重列 `WAL_ARCHIVE_*`（与 §7 重复）并凭空塞入 `KAIROS_RL_*`/`FORGETTING_HALF_LIFE`/`FRESHNESS_*`/`DOMAIN_KEYWORDS_PATH` 等约 16 个参数——脱离章节、未计入文末"83 项"统计，参数治理出现"野表"。
- 【"调度周期"无绝对时长】全文数十处用"N 个调度周期"作单位，却从未定义 1 调度周期=多少秒，运维算不出真实超时。
- 【默认值不可落地】`KAIROS_WM_SLOT_CAPACITY = 7±2`——"±2"无法作为 config reset 目标。
- 【参数重复登记】`KAIROS_SANDBOX_CONFIDENCE_INTEGRATION_THRESHOLD=0.7` 在 §3/§5 定义两次。
- 【限流量级冲突】`WRITE_PER_MIN=60`（1/s）与 security S-02 "≤100 ops/s" 差 100 倍且单位不同（见 H5/H6）。

### 2.5 security/（安全文档）

**security-specification.md** 🟡
- ✓ S-01~S-17 全覆盖、结构清晰。
- 【S-02 限流虚实】"≤100 ops/s" 但真正落地参数是 `WRITE_PER_MIN=60`(1/s)——security 在喊一个 configuration 没实现的强度。
- 【S-09/S-07 纯口号】"注入扫描""敏感模式检测"只列类别不给定检测方法（正则？模型？），与 test-strategy 互相循环定义。
- 【密钥表漏 DB 密码】§5 列 API_KEY/SALT/SECRET/AUDIT_HMAC/LLM Key，漏了 deployment §三 的 `KAIROS_DB_PASSWORD`。
- 【localhost 免 TLS vs [P] 模式】S-04 默认绑 127.0.0.1，但对外开放模式必须监听非回环，无绑定地址参数可配，冲突未化解。

**threat-model.md** 🟡
- ✓ STRIDE + HMAC 双链给了可落地算法（难得），但缺链头锚点（首条 prev_hmac 为何值）与防截断说明。
- 🔴 `KAIROS_SSRF_ALLOWED_HOSTS` 默认 `*`——默认全放通（见 H6）。
- 【S-10~S-17 多口号】"测试验证不可绕过""受差异检验强制执行"靠"不可绕过"四字担保，无实现机制。
- 【S-04 与 [P] 模式冲突】默认绑 127.0.0.1 与对外开放模式根本冲突，未化解。

### 2.6 quality/（质量文档）

**test-strategy.md** 🟡
- 【S-07 表坏行】§2.2 用全角 `｜` 且写成 5 列（他行 4 列），Markdown 断裂。
- 【"6 条 E2E"两文档不是同一组】本文件 6 条与 test-plan §3.6 的 6 条仅 3 条重合——"关键路径 E2E 100%(6/6)"在两文档指向不同对象。
- ⚪ 对"无代码"系统，通过标准无法运行，属预写不可自检。

**acceptance-criteria.md** 🔴
- 【标题范围自相矛盾】D-201~D-206 称"v1.1 代码债务"，§二 又冠"v1.0.0 发布硬性检查项"——v1.0 到底包不包含 v1.1 债务？
- 【非功能阈值悬空】P50≤50ms 等全标"见 benchmark-plan/NFR"，NFR 不在本批范围，来源不可核验。
- 【文档检查自指】要求"功能清单/数据模型/接口规格/项目计划齐备"，其中多项是否在仓库真实存在待核。

**benchmark-plan.md** 🔴
- 【吞吐目标与限流互斥】§3.3 写入 ≥100 ops/s、检索 ≥500 ops/s，但 `WRITE_PER_MIN=60`(1/s/客户端)——即便 100 客户端并发也撑不起发布门槛（见 H5）。
- 🟡 硬件基线（4核/8GB）与 deployment 三模式容量未对齐说明"100 万条 SLO"在哪档硬件成立。

**test-plan.md** 🟡
- 【用例数"待定"】§1 单元/集成"用例数"两格直接写"待定"——测试计划最核心规模指标留空，却标 v1.0.0。
- 【依赖未实现契约】全部用例基于 `kairos write/search` 等 CLI 与 REST 端点，无代码状态下均不存在。
- 【v1.1 范围口径不一】§1"不覆盖 v1.1+（定向遗忘）"，但 acceptance-criteria 把 D-204 定向遗忘列为 v1.0.0 硬性检查项。

### 2.7 governance/（治理文档）

**adr.md** 🟡
- 【"已采纳"与"进行中"混用】§0 宣称"决策已采纳（所有 ADR 架构选择已锁定）"，但 10 项中 6 项"进行中"——"锁了什么"对执行者无约束力。
- 【ADR-001 甩锅】自己论证 SQLite "单实例单写入"无法满足并发，却又塞回做"可选部署形态"——没勇气砍掉。
- 【ADR 间未对齐轻量模式检索路径】ADR-001（SQLite+sqlite-vec 向量为主）与 ADR-004（路径空间第一检索）在轻量模式下是否兼容未对齐。

**cognitive-architecture-gap.md** 🔴
- 【G-07 P6 已破却不叫破】明确写压缩比超 30% 上限、例外 4>2，却归类为"受控偏离"而非能力缺口，且全库无一处定义消除的可验证条件（risks R-P6-001 自承"缺乏可验证问责路径"）——永久偏离。
- 【G-01 对应债务列空】"最高优先级"却排 v1.0.x，本表"对应债务"列空，与 traceability/debt-collection 编号断裂。
- 【§0.1 引用待核】第 17 行引 `architecture §0.1 四轴承载完整性声明`，架构是否真有 §0.1 需核（主审注：架构 §0 是"认知基础与设计哲学"，无 .1 子节，疑似悬空）。

**risks.md** 🟡
- 【自欺式缓解】R-001 治理组件"监控不强制"降级运行，标记 monitoring/mitigated——把没解决的问题降级掩盖。
- 【T-002 与 R-001 互不引用】最大风险(高)与治理过度风险(中)应关联却无交叉引用。
- 【P6 消除依赖未声明】R-P6-001 缓解前提"VAD 条件激活恢复"依赖 G-02，但 G-02 与 R-P6-001 谁先谁后未声明。

**project-plan.md** 🔴
- 【无代码却排 12 周精确到周+80% 覆盖率】§1 自承"代码尚未启动"，Phase 1 交付物却列"记忆 CRUD/向量检索/事件总线"并验证"单元测试 ≥80%"——把希望写成计划。
- 【10 万容量瓶颈无来源】§76"轻量模式 10 万条上限"单独抛出，无引用。
- 【与"无代码"直接冲突】Phase 3 第 11–12 周就"E2E 6 条关键路径""安全红线 17/17"，等于计划里 v1.0.0 已是可运行版本，与 README/adr"进行中"冲突。

**release-process.md** 🔴🔴
- 【教发布一个不存在的 wheel】§3 全是 `uv build`/`pip install kairos==1.0.1`/`kairos health` 等命令，但代码尚未启动——假装发布流程可走，比 user 文档更恶劣。
- 【版本语义灾难】§33"代码首次可运行时不变号"——文档版 v1.0.0 与代码版 v1.0.0 同号两义；`kairos db rollback` 在 error-reference/user-guide 从未出现，命令事实源不明。

**documentation-governance.md** 🔴⚪
- 【自己违反自己】§5 编号注册表声称"先注册再使用"，但债务段 D-001~D-210 把事后补的 101/102/201 段全塞进去，注册表没预留下界；且所有文档 status 均为 draft，§4 要求的"draft→final 晋升"从未发生——治理规则变摆设。
- 【v1.0.0 撞名】§4 把 `v1.0.0` 当状态名，与 release-process 的 SemVer `v1.0.0` 撞名，两套语义混用。
- 【联动表引用十几个无法验证的文件】等于空承诺。

**social-calibration-roadmap.md** 🟡（最诚实，反复声明"代码未启动"）
- 【M2 验收无数字】"连续 N 个校准周期""假阳性率 < 阈值"——N、阈值全占位，M2 永远无法判定通过。
- 【把文档描述当实现】§82"依赖架构 §10.9 完整实现"，但 §28 自承"代码实现 ❌ 未启动"——"架构里写了状态机"被当"实现"。
- ✓ D-205/D-209/D-210 关联数字对得上（少数对齐处）。

**debt-collection.md** 🔴🔴
- 【"18 待实现"从哪来】changelog 写 18，本文件实际 D-201~D-211 为 11 条（D-204 已并入闭环则 10）——11≠18（见 H4）。
- 【D-204 状态冲突】本文件说已闭环（DC-019/DC-027），changelog "已知债务"表仍列 v1.1 待实现——同一债务两说。
- 【DC-027 完成时间晚于文档更新】DC-027 完成 2026-07-22，文档 updated 字段 2026-07-20，文档未同步 updated 日期——治理文档自己漂移。
- 【D-205 被当路线图前置依赖却无方案】roadmap M2 依赖 D-205，但 D-205 "当前阻碍：需要认知层先给出方案"——连方案都没有的债务当前置依赖，M2 不可能触发。

**changelog.md** 🔴
- 【完成时态误导】第 22–43 行大段"核心能力/架构"用已完成时态，第 89 行小字才承认"代码未启动"——读者会误以为能力已实现。
- 【数字乱编】"27 闭环 + 18 待实现"（18 与 debt-collection 11 冲突）；D-209 标 v1.3，debt-collection 标 v1.2，roadmap 标 M3a=v1.2——三处对不上。
- 【评析轮数】"15 轮" vs risks "第十三/十四/十五份"——轮数与份数混用。

### 2.8 references/（参考文档）

**error-reference.md** 🟡（相对可执行）
- ✓ "7 类 30 个错误码"计数正确（4+4+7+5+4+1+5=30）。
- 【死码】ERR-LLM-002 自己写"建议统一使用 ERR-RATE-003"——那它为何还存在？违反单一事实源。

**usage-load-algorithm.md** 🟡
- 【系数无来源】1.2/1.4/1.6/1.8/2.0 推给 `ops/configuration.md` 的 `COMPOSITION_*_WEIGHT`，但未验证该文件确有，且为什么内隐"最大影响"无论证。
- ⚪ 标题"使用负载计量器"却只影响影子副本置信度累积速率、不参与价值裁决——定位模糊，像把次要工程参数包装成算法。

**vad-coordinate-algorithm.md** 🟡
- 【依赖未定义组件】第 40 行"轻量级情感分析模型"身份不明——在哪部署、是否依赖 LLM Provider 未定义，每条记忆都带 VAD 却依赖未定义推断组件，架构级空白。
- 【兜底退化未讨论】大量记忆 VAD 趋同于(0.1,0,0)，§2.3 用余弦相似度 boost，趋同向量余弦失真未讨论。
- 【§2.4 引"架构 §5.2 整合窗"】§5.2 是否真有"整合窗"小节待核（主审注：架构 §5.2 是向量空间，无明显"整合窗"子节，疑似悬空）。

**traceability-map.md** 🔴
- 【债务数三说】标题"10 债务"，正文只映射 7 个 distinct 债务（D-201/D-204/D-205/D-206/D-208/D-209/D-210），debt-collection 实际 11（见 H4）。
- 【能力凭空出现】W-07 脱敏/M-06 导出/A-01 等声明列全为"—"——有功能却无认知声明支撑，feature-list 与认知基础对不齐。
- 【CAL-06 逻辑倒置】有差距 G-05 却无对应认知声明。
- ✓ 差距表↔认知声明映射（G-01~G-12）反而最完整。

**glossary.md** 🔴
- 【第五轴自相矛盾】"四轴度量空间（五轴模型…）"把两个矛盾名塞一单元格；说"第五轴 v1.0 以代理实现"，但 cognitive-gap G-09 说"v1.0 默认关闭"——代理实现 vs 默认关闭冲突。
- 【他律性约束定义为事实、实为未兑现承诺】定义为"已成立的约束"，risks T-002/D-205 说前提未做。
- 【认知关节循环定义】"基于不确定认知所做的可拆卸可替换的设计决策点"——用"不确定认知"定义"认知关节"，零信息量。
- ⚪ "约 52 条术语"用"约"，与 documentation-governance "精确编号"原则相悖。

**value-dimension-entropy.md** 🟢（reference 里最干净）
- ✓ 熵公式正确，与 usage-load 互证一致。
- 🟡 §二 H<0.5 直接绑"应急冻结"系统级动作，却未引用 risks R-005 的误冻风险与冻结粒度；§三 "-0.05 显著"无统计依据。

### 2.9 user/（用户文档）

**user-guide.md** 🔴🔴
- 【教操作无代码系统】第 19 行小字承认"无构建产物/SDK"，第 27–35 行却用大段代码块呈现 `pip install kairos`/`kairos init`——警告是事后小字，诱导读者撞墙。
- 【`--init-key` 命令事实源不明】user-guide/quick-start 都说它有，但 release-process/error-reference/project-plan 全程未提。
- 【`kairos suppress`/`kairos approve` 仅出现在用户文档】发布步骤/功能清单均未提，用户文档教了只有自己知道的命令。
- 【并发上限精确却虚】§四"≤100 ops/s / 硬上限 500 ops/s / 目标 ≥100 ops/s"全部指向未读 NFR——无代码系统却把并发精确到 ops/s，设计幻想。

**quick-start.md** 🔴
- 【"5 分钟跑通" vs "这东西还不存在"】第 18 行警告"无构建产物"，第 34 行第一步就是 `pip install kairos`——矛盾呈现，假装教程。
- 【同文档命令状态不一】`admin key generate` 标"未来"，`init --init-key` 标"可用"，两都是 Key 生成命令，用户困惑。
- 【是否需要 PostgreSQL 引导不一】quick-start 说"无需 PostgreSQL 轻量开箱即用"，user-guide 把标准/轻量并列——新人被搞晕。

---

## 3. 跨文档一致性对齐检查

### 3.1 术语定义一致性（同一概念多处定义）
- **维度基数 / 第五轴**：architecture(14维/压缩6)、cognitive-foundation(10+维/压缩3–4)、architecture §0.6/§10.11(12维/33%) 三说；glossary 说"第五轴 v1.0 以代理实现"，cognitive-gap G-09 说"默认关闭"。→ **无权威值，概念地基松。**
- **他律性约束**：glossary 定义为已成立事实；risks T-002 / debt D-205 说前提未建模。→ 术语层与风险层假设冲突。
- **认知关节**：glossary 循环定义，零信息量。
- **P6**：glossary 弱定义"禁止无声丢失维度信息"；usage-load 给操作定义"禁止聚合为单标量"；architecture 当刚性铁律但已被 G-07 打破。→ 定义强度三档。
- **日志契约**：coding-conventions(7字段) vs observability(12字段, time→timestamp) 两版。
- **健康检查 schema**：observability(pool_available) vs deployment(无) 两版。
- **配置管理形态**：deployment(env+compose) vs runbook(config.yaml/.env + kairos config) vs configuration("env 或文件") 三套口径。

### 3.2 API 文档 ↔ 架构设计文档
- 🔴 **章节号系统性漂移**（H3）：feature-list/requirements-baseline 把存储层组件指到 §4.2，架构实为 §5.2；§6.3→§7.3、§4.6→§5.6、§8.8→§10.10、§7 安全红线→§8。架构重排后下游未同步，整批规格引用的"设计权威章节"大半失效。
- 🔴 **导出端点违反 S-07 红线**：api-spec `export` 返回完整内容，架构 S-07/nfr §五 要求脱敏。
- 🔴 **临时记忆存不存打架**：架构 §3.7"铁律不写回持久化"、§7.2"不进入存储层"；data-model 把 `temporary` 列为 `memories.contract` 合法持久值；api-spec `DELETE /v1/memories/{id}`(仅临时契约) 当已存储记录。
- 🔴 **RL 权重维度脱钩**：rl-weight-spec(5维, 随机+Softmax) vs 架构 §10.14(6维, 固定权重)；rl 引用的 `POST /v1/feedback`、`rl_weights` 表在 api-spec/data-model 均不存在。
- 🟡 **design-philosophy 引用架构 §4.3/§4.5/§4.6/§3.2 等不存在子节**（主审核验 §4 仅推理皮层，无 §4.3+）。

### 3.3 README 承诺 ↔ 变更日志 / 实际设计
- 🔴 **"无运行代码" vs changelog 完成时态**：README/changelog 小字承认无代码，但 changelog 大段宣布"核心能力/架构已发布"、project-plan 把 CRUD/红线验证排进 12 周里程碑、release-process 教发布 wheel——底层假设"当前状态"在文档间打架。
- 🟡 **README 评审清单与磁盘对不齐（非数字打架）**（H1/H2 订正）：标题/分解式/磁盘均为 50，自洽；但评审文档索引（L118–119）引用磁盘不存在的 `Kairos文档全集_Linus风格批判报告_2026-07-22.md`、遗漏实际存在的 `主审终稿`；规格表 11 项含 rl-weight-spec，无"幽灵文件"。
- 🟡 README "设计权威"声称与 architecture 自身层数/章节引用混乱相矛盾。

### 3.4 部署配置 ↔ 其他文档假设
- 🔴 **deployment §三 与 configuration §7 参数集严重错位**：deployment 有而 configuration 无（DAILY_BUDGET_FEN/CORE_LIMIT_*/SEARCH_DEFAULT_LIMIT/SCHEDULER_INTERVAL/ADMIN_IPS）；configuration 有而 deployment 无（RATE_LIMIT_*_PER_MIN/INPUT_LIMIT_*/SSRF_*/WAL_ARCHIVE_*）。照 deployment 配必漏安全/限流参数。
- 🔴 **Docker db 端口未暴露 vs runbook localhost 恢复**：自家部署与自家恢复手册互斥。
- 🔴 **限流/安全/基准三量级互斥**（H5）：1 ops/s / 100 ops/s / ≥100 ops/s 写入吞吐不可能同时成立。
- 🔴 **SSRF 默认 `*`**（H6）。
- 🟡 **"调度周期"无绝对时长**：configuration 数十处用此单位，疑似 = `KAIROS_SCHEDULER_INTERVAL=300s` 但未声明，运维换算不出真实超时。
- 🟡 **SQLite 路径三说**：development-setup / reliability / deployment 三处三路径。
- 🟡 **pg 大版本三说**：technology-stack(15–17) / deployment(16) / development-setup(15)。

### 3.5 跨维度关联断裂点（编号体系 / 引用失效）
- 🔴 **四大计数体系互不咬合**：43 能力(feature-list) / 37 声明(claim-matrix) / 44 组件(impl-map) / 10~11~18 债务(debt/traceability/changelog) / 12 差距(gap)。RTM 只覆盖 5/43 能力。功能→声明→组件→债务→测试 链路断。
- 🔴 **悬空章节引用泛滥**：architecture §5.3/§5.6→§10.7(实为设计约束表，应为 §5.5)；design-philosophy→§4.3/§4.5/§4.6/§3.2(不存在)；cognitive-gap→§0.1(疑似不存在)；vad→§5.2 整合窗(疑似不存在)；feature-list→glossary §2/D.8/B.2(未核验)。
- 🟡 **`references/domain_keywords.yaml` 未被 README 索引**：架构 §10.16 通过 `KAIROS_DOMAIN_KEYWORDS_PATH` 引用该文件，但 README 索引未列它（spec/references 表均遗漏），读者无从得知其存在。（注：原稿称 rl-weight-spec 为"幽灵文件"已订正——它实际在 README L44 索引内。）
- 🟡 **CLI 命令事实源分裂**：`kairos approve`/`admin key generate`/`--init-key`/`db rollback` 只在某些文档出现，无单一事实源。
- 🟡 **债务编号段事后补**：documentation-governance §5 注册表没预留下界，D-101/102/201/211 段事后塞入，违反"先注册再使用"。
- 🟡 **所有文档 status 恒为 draft**，documentation-governance §4 的晋升规则从未执行。

---

## 4. 一句话结论与优先修复清单

**结论**：这不是一份"有缺陷的设计文档"，而是一份**用免责声明砌成、却假装已落地的讣告式文档集**——它详述了一个不存在的系统的每一根螺丝，却在层数、维度、债务条数、文档总数这些最该权威的数字上集体翻车，且让下游 11 篇规格指向错误的架构章节。在写出第一行代码之前，先把这些数字和引用对齐，否则实现者拿到的是一叠互相指向错误坐标的地图。

**优先修复（按阻断程度）**：
1. 🔴 全库扫描并修正"见 §X.Y"类引用，以 architecture 实际章节（§4=推理皮层/§5=存储层/§8=安全红线）为准，re-number 下游规格（feature-list/requirements-baseline 系统性 §4.2→§5.2）。
2. 🔴 统一四大计数口径：43 能力 / 37 声明 / 债务条数（定 10 还是 11 还是 18）/ 12 差距，并在 traceability-map 真实补全映射。
3. 🔴 解决限流/安全/基准三量级互斥：要么把 `WRITE_PER_MIN` 提到与 S-02(100 ops/s) 同量级，要么把 benchmark 门槛降到限流以内——二选一，别两边都写。
4. 🔴 deployment §三 与 configuration §7 参数集合并对齐，把 security/限流/SSRF/WAL 参数全部进 deployment 环境变量表。
5. 🔴 把 `KAIROS_SSRF_ALLOWED_HOSTS` 默认改为 deny（具体域名），非默认 allow。
6. 🟡 定义"1 调度周期 = KAIROS_SCHEDULER_INTERVAL(300s)"并全文替换；清理 configuration §7 后的"幽灵表"。
7. 🟡 在文档顶部统一、醒目地声明"无运行代码"状态，并把 changelog 的完成时态、project-plan 的 12 周可运行里程碑、release-process 的发布命令改为"待代码启动后生效"。
8. 🟡 消除"临时记忆存不存""导出脱敏"两处架构级矛盾；补 `rl_weights` 表与 `POST /v1/feedback` 端点或删除 rl-weight-spec 的悬空引用。
9. ⚪ 删减 cognitive-foundation 的声明通胀、architecture 的复制粘贴段、各文档"未来命令"的假装教程格式。
10. 🟡 执行 documentation-governance §4 晋升机制（至少把 1 份文档升 final），否则治理文档自己就是反例。

---

*主审注：本报告逐文档结论基于 4 个并行子审查代理的逐字通读。经本次会话（2026-07-22）用 grep/Read 实读复核：H3（架构 §4=推理皮层/§5=存储层/§8=安全红线）、H4（D-201…D-211 确为 11 条）、H5（限流 60/120 与 * 默认）、H6（SSRF 默认 `*`）、H7（P6 多口径）均确凿。**订正说明**：原稿 H1「文档数 50/51/52 三数打架」与 H2「spec 表 10 项、rl-weight-spec 为幽灵文件」经本次实读 README L34–44 / L118–123 与磁盘计数，确认为误读——README 计数为自洽的 50，rl-weight-spec 已在索引 L44 内；H1 真实缺陷是评审清单引用了不存在的文件名。原稿 §2.1 L102 对 data-model 版本记录"11 张核心表"的表述亦订正为"19 张（11 核心+8 新增）"。其余章节引用类问题（H3 系统性 off-by-one）维持原判。reviews/ 目录下已有历史批判产物（审计模板/早期报告/本主审终稿），本稿为综合主审终稿。*
