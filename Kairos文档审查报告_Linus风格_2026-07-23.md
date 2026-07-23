# Kairos 文档全集审查报告（Linus 风格）

> 审查范围：`D:\projects\kairos\docs` 下全部文档，**排除 `reviews/`**（按指令）。
> 审查方法：逐字通读 50 份文档（约 12,000 行），按目录分派独立审查代理提取逐文档批评与"事实清单"，再由主审比对事实清单、对高影响冲突**逐条回读原文核实**（feature-list / operation-catalog / README / claim-matrix / implementation-map / security-spec / cognitive-architecture-gap / traceability-map / requirements-baseline / 关键 ops 文件均已回读确认）。
> 风格说明：不客套、不找茬、不模糊。只点真问题，每条给文档名 + 段落/条目 + 实质。

---

## 〇、总评（先说结论）

这不是一个"文档写得不好"的问题。这是一个**用约 12,000 行、50 份精密文档，去治理一个明确声明"全系统尚无运行代码"的空壳**的问题。

文档集自称拥有 101 项能力、37 项认知声明、29 张表、19 条安全红线、10 个 ADR、52 份文档。这些数字彼此对不上（101 vs 80、52 vs 53 vs 50、37 声明的映射债务数在文件自身里 18 vs 11、README 的 27+62+11 算成 89）。更致命的是：**同一批文档里，有些把系统写成"已落地/架构已实现/代码可定位"，有些又反复声明"无运行代码"**——读者根本不知道该信哪句。

文档债务的核心不是"没写完"，而是**假确定性**：把占位值标成"规格"、把未定义术语当黑话用、把"铁律"承认已被打破 43% 还叫"受控偏离"、把发布指南写成可以发布一个不存在的包。这比空白更危险——它会让第一个照着写的开发者，在 R-02 端点、SQLite 备份路径、缺失 Key 的 HTTP 码上，直接写错。

**一句话：先写代码，再写 50 份手册。现在这堆东西是一座给幽灵住的、物业规范极其详尽的空楼。**

---

## 第一部分：逐文档批评

### A. foundation/（地基文档）

**A-1 `architecture-v1.0.0.md`（2241 行，核心架构）**
- **层数精神分裂**：§0.4:117 说"当前五层功能栈（接入/WM/存储/策略/元认知）"又称"合计 7 个结构单元"；同段又说"本文六层将宪法主权面计入层数"；§0.5 一致性表（约 181–189 行）实际列了 7 行（宪法主权面/元认知/策略/存储/WM/接入/监督平面）。§12:2241 又说"六层功能栈 + 监督平面"，§10.6:1813 说"六层架构 + 正交平面"。五/六/七三种计数，无一处的"六层"能和其一致性表对上。
- **安全红线 19≠20**：§8 定义 S-01…S-19（实测 19 条，1683–1701 行），但版本记录（2241 行附近）自称"安全红线 20 条"。差一个，且版本记录是文档自己的"事实"。
- **状态自打脸**：frontmatter `status: draft`（约 11 行）vs 版本记录"架构首版定稿"。不能既是草稿又是定稿。
- **全是占位**：§0.4:100"所有阈值和常量均为 v1.0 占位值"、§10.5:1770"本节指标目标值均为示例占位"。整张量化指标表（验证有效率/身份保留/遗忘后悔率等 20+ 项）自我声明无效。§10.5 又用"≥60%/≤20%/≤5%"等精确数字包装——占位值写成可验收表，纯属催眠。
- **可执行的规格几乎为零**：所有具体阈值/常量都"详见 ops/configuration.md"（出现 30+ 次），API 契约"见 api-spec.md"，RL 优化器"见 specification/rl-weight-spec.md"——核心架构文档自己不含任何可落地的数字或接口。2241 行里大量是"声明/边界声明/认知关节"嵌套注释框，自我复述而非规格。
- **断链**：引用 `api-spec.md`、`data-model.md`、`security/security-specification.md`、`reliability文档`、`部署文档`、`ADR-007` 等，全部在本文集外，且 ADR 文件在本批审查中未提供。

**A-2 `cognitive-foundation.md`（915 行）**
- **标题与正文矛盾**：标题"记忆即使用"是第一性原理，但 §引论:30 自承"使用（间接度）并非最高优先——身份/探索/宪法/校准/认知完整性均优先于使用"。核心 thesis 被六个更高优先级覆盖，标题误导。
- **"P1–P6"标注错乱**：§2.2 标题写"设计原则 P1–P5"（约 399 行），P6 在 §2.3；版本记录（约 915 行）却称"六条设计原则 P1–P6"。小节编号与总数对不上。
- **"声明"通胀**：全文"声明"出现数百次，文档花在 caveat 元数据上的篇幅远超认知内容本身。约 90% 是限定脚手架，core 极薄。
- **降维门禁无阈值**："降维升级门禁条件"全部写"满足后升级"，无任何阈值/日期，无法验收。

**A-3 `design-philosophy-relations.md`（166 行）**
- **"简化表达"逻辑不通**：§107 表格称"身份>校准>时间"是七级链"身份>探索>宪法>校准>认知完整性>时间>间接度"的"简化表达"；但前者只取 3 级且重排（丢了探索/宪法/认知完整性），与 §44 的 ASCII 全链矛盾。同一文档对自己"简化表达"的定义自相矛盾。
- **"张力对"管理列空话**：§128–133 管理机制列写"探索安全边界 + 保守偏向告警""弱自反性声明 + 三阶段演进"，多格直接"见架构 §X"，无独立内容。
- 其余基本是跨引用索引，独立信息少。

### B. specification/（规格文档）

**B-1 `system-context.md`（系统上下文）**
- **假设与依赖打架**：§79 把"外部校准源存在"列为假设，§93 又说"外部校准信号 治理必需 | 虚拟校准（受限模式）"——即"必须有外部校准源"同时"可以没有（虚拟校准）"。
- **19 条红线只字未提**：边界表反复引用 S-01~S-19，但全文无任何一条的定义或编号，全靠口头引用。
- **单进程假设无支撑**：§83"单进程部署"作为假设，但无任何容量/并发数字支撑单进程扛 100 万条记忆 + 语义检索。

**B-2 `requirements-baseline.md`（需求基线）**
- **RTM 硬伤（已回读确认）**：§161 R-01 → `GET /v1/memories?path=`；§162 R-02（语义检索）→ `GET /v1/memories?q=`。但 operation-catalog §42–44 明确：语义检索是 `POST /v1/memories/search`，`?q=` 是**文本/关键词检索**，路径检索是 `GET /v1/path`。需求基线把"语义检索"映射到了关键词端点——**照此写代码必错**。
- **延迟措辞伪装**：§30"检索延迟 <100ms"没说百分位；§133 NFR"语义检索 P50 ≤100ms"。`<100ms` 把平均伪装成保证。
- **定向遗忘状态自相矛盾**：§189 把 D-204 标"已闭环……v1.0 范围"，但 §5"v1.0 设计覆盖"列表（172–183 行）根本没列定向遗忘；M-04 仅是 P1。进不进 v1.0 自相矛盾。
- **RTM 自承不全**：§166"完整 RTM 表在 v1.0 代码启动前补全"，当前只追了 5 条还追错 2 条（见上）。一份"受管的可追踪需求基线"目前只追了 5/全量。
- **真空指标**：§136"单元测试覆盖率 ≥80%"、"19/19 条红线逐条验证"——对零代码项目谈覆盖率和红线验证，是真空指标。

**B-3 `use-cases.md`（使用场景）**
- **状态机三套词**：场景 5（约 85 行）"suppressed 抑制但可复兴，archived 压缩但不抑制"；feature-list M-10 状态机 `Active→Stale→Archived→Suppressed→Superseded`；operation-catalog 软删除又按契约分"permanent 拒绝/常驻按需软删/临时硬删"。遗忘/归档/抑制术语与状态流三处各说各话，无单一事实源。
- **命令不存在**：场景 1（约 26 行）用 `kairos init`，但 operation-catalog 根本没列此 CLI 命令（它只列 API/Tool）；development-setup 也自承 CLI 未构建。
- **未定义控制变量**：场景 3"系统空闲（持续 N 周期）"——N 未定义，甩锅给 architecture §10.9；用例里出现未定义变量等于没写。

**B-4 `feature-list.md`（功能清单）**
- **总数造假（已回读确认）**：§17 声称"101 项能力（43 核心 + 58 扩展）"，§208 合计也写 101。但扩展表实际行数：记忆写入 "+5" 把 W-09（冲突检测写入）与"冲突合并"重复计数（W-09 即冲突合并），实为 4；系统管理 "+12 (A-08~A-19)" 实际表列到 A-20（图谱距离重排序，184 行），且跳过 A-14。逐行实数为 **57 条扩展**（非 58），加 43 核心 = **100**，不是 101。ID 跟踪靠肉眼，无人校验。
- **blanket 声明对 PM-01/PM-02 为假**：§17 统一宣称 101 项"冻结——设计已固化、架构已实现，代码未编写"；但 §84–85 的 PM-01/PM-02 明确标"⏳ v1.1+"，"数据模型和 API 未落地"。核心 43 中的两项既非 v1.0 也非"架构已实现"，blanket 声明对它们为假。
- **无验收标准却称"架构已实现"**：§23 自承"101 项功能当前无逐项验收标准"——那"架构已实现"拿什么验证？无验收的"实现"= 没实现。
- **缺优先级列**：核心表（一~八）无优先级列，而 requirements-baseline 里 W/R/M/CAL/A 都有 P0/P1/P2。作为"实现者输入锚点"不给优先级，等于让实现者自己猜先写哪个。

**B-5 `operation-catalog.md`（操作目录）**
- **操作数 53 vs 52（已回读确认）**：§100–103 ENC 7 + RET 15 + STR 31 = **53**，却写"总计 52"。差一。
- **功能数 80 是哪来的（已回读确认）**：§105 称"与 feature-list.md 的 **80 项功能**之间存在多对多映射"——feature-list 自己说 101（实 100），operation-catalog 又说 80。三数（101/100/80）无一相同。
- **同端点算两次**："校准信号注入 POST /v1/calibrate"同时出现在 ENC（34 行）和 STR（75 行），污染计数。
- **"P6 合规"黑话**：全文反复出现"P6 合规/压缩~33%"，但本集 5 份文档无一份定义 P6 是什么（P6 在 foundation/cognitive 文档里，未在本批提供）。读者无法判断"压缩~33%"意味着什么。

**B-6 `data-model.md`（数据模型，564 行）**
- **`lma_urn` 笔误**：§43 格式写成 `urn:kair os:lma:<uuid>`——"kair os" 中间有空格，明显是 "kairos" 复制粘贴笔误。URN 规范里有空格，下游解析全崩。
- **实体 ID 类型自相矛盾**：`entities.id` 是 `BIGSERIAL`（BIGINT，约 371 行），但 `entity_communities.member_entity_ids` 是 `UUID[]`（约 505 行），`weekly_packs.session_ids` 是 `UUID[]`。实体用 BIGINT 主键，社区却用 UUID 数组引用——两套 ID 空间，要么引用永远失效，要么这两张表不是一套。
- **`suppressed` 死定义**：`status` 列（约 46 行）写"suppressed 为 archived 子态"，但 `memory_states` 表（约 246 行）把 active/stale/archived/suppressed/superseded 列为平级；api-spec 的 `/v1/memories/stats` 与 `/v1/health/detail` 也把 archived 和 suppressed 当独立计数。"suppressed 是子态"这条声明在系统里根本没被遵守。
- **`embedding` 无 NOT NULL**：向量列允许 NULL，却没说 NULL 记忆如何参与向量检索、索引怎么处理 NULL。
- **"1024 维线性投影到 1536 维"包装成已定方案**：轻量模式描述重复 4 次，但投影矩阵从哪来、怎么训练、是否冻结，全没说。把未解决的工程问题包装成已定方案。
- **版本记录编造**：版本记录（564 行）称"新增表 vector_collections、community_detection"——全文无这两张表的 schema。又称"核心记忆表 29+ 字段"——实际 `memories` 列我数到约 38 列；又称"九类根键"，正文第九节只列 4 个（HKLA/HKCU/HKLM/HKCS）。9≠4。
- **审计链无顺序保证**：`audit_log.previous_hash` 要求指"上一条日志的 HMAC"，但表里无序号/游标列定义"上一条"的顺序。并发写入时前驱如何确定？审计链完整性前提塌了。
- **`usage_events` 无索引**：遗忘引擎要按 `memory_id + timestamp > NOW-30d` 扫，但该表无 `(memory_id, created_at)` 索引——全表扫，性能 defect。
- **`superseded_by` 悬空外键**：参照 `memories(id)`，但 api-spec 允许临时契约硬删除，硬删后指向它的外键全悬空，且无 ON DELETE 行为声明。
- **Windows 注册表命名错乱**：用 HKLA/HKCU/HKLM/HKCS 描述 LLM 记忆系统，写入权限里出现"编译器"——这系统哪来的编译器？术语错乱。

**B-7 `api-spec.md`（接口规格，841 行）**
- **认证（唯一过关项）**：`Authorization: Bearer <key>`，read/write/admin 三级，设计合理。
- **核心搜索无分页**：`POST /v1/memories/search`（5 维混合检索）返回 `{data[], explanation}`，无 total、无 cursor、无 next（约 98 行）。最该分页的端点反而没分页。
- **限流有名字没数值**：`ERR-RATE-001/002`（429）存在，但无任何限额数值（RPS？burst？按 key 还是按 IP？）。限流"有名字没数值"= 没定义。
- **错误码断链**：§7 错误码表是"HTTP 级错误码子集"，完整集在 `references/error-reference.md`——该文件虽在本批但 §7 表本身缺 409/ERR-CONFLICT-*（PATCH /v1/memories/{id} 用 If-Match→409，但 §7 无 409）。
- **两个端点撞车**：§1.2 `GET /v1/memories/heat-top` 后（约 100–104 行）又跟一个标"响应 200 OK"的块，字段 `{data[], total, path}`——和 heat-top 的 `{data[], total}` 形状不同且多了顶层 `path`，归属不清。
- **`/v1/memories/stats` vs `/v1/health/detail` 状态集合不一致**：stats 的 `by_state` 只有 active/stale/archived/superseded；health/detail 多一个 suppressed:30。同一系统两统计端点给不一致状态集（呼应 data-model 的 suppressed 矛盾）。
- **"可审计"是假的**：PATCH /v1/memories/{id}（约 117 行）称"内部实现为版本插入，修改历史可审计"，但 data-model 只有 `superseded_by` 指向新版本，**旧版本 content 被覆盖丢失**，无版本历史表。
- **`POST /v1/constitution` 用 POST 做 "view"**：`action: "view | revise"`——用 POST 做查询语义荒谬，且 `preference_key` 合法取值列表完全没给。
- **明文 HTTP**：base `http://localhost:8010`（约 19 行），Bearer Token 在线路上裸奔。要么强制 HTTPS，要么明确仅本地回环——当前写法是个漏洞。
- **端点数严重低估**：声称"20+ 端点"，实际 REST 端点 60+（见事实清单）。
- **`POST /v1/webhooks` 既预留又计入**：§1.7 标"v1.1 预留端点"，版本记录却把它算进"v1.0.0 初始接口规格 20+ 端点"。

**B-8 `detailed-design.md`（详细设计，432 行）**
- **hall 阶段两套词**：§2 存储写入用 `raw→item`，data-model/api-spec 的 hall 用 `processing/validation/canonical`。同一概念两套命名。
- **截断后两个系数等价却并存**：§3 `environmental=1.5`、`temporary=2.0`，但都 `min(...,1.0)` 截断到 1.0（约 212 行）。截断后两者完全等价，却用两个不同系数，纯属迷惑。
- **字段名写错，代码跑不起**：§3 伪代码 `usage_events WHERE ... timestamp > NOW-30d`，但 data-model 的 usage_events 只有 `created_at`，**无 `timestamp` 列**。
- **声明了不写**：§3 职责边界列"潜伏势能重估""复兴加速通道"，下面伪代码完全没实现这两块。
- **WM 槽位 7±2 是 cargo-cult**：§1"维护当前活跃记忆槽位（7±2）"——把 Miller 1956 心理学实验当架构硬约束，无任何推导。
- **悬空组件**：§7 `REASONING_LOOP` 调 `PREDICTOR.QUERY`/`CORTEX.FILTER`/`CORTEX.REASON`——PREDICTOR、CORTEX 三份文档里从没定义过。

**B-9 `implementation-map.md`（实现映射，143 行）**
- **与"无代码"状态冲突（已回读确认）**：claim-matrix §19、README §16 均声明"全系统尚无运行代码"；但本文 §17 虽写"编码启动后"，却把组件逐一映射到具体 `src/` 路径并写死算法细节——§76 `RL 权重优化器 | src/storage/rl_optimizer.py | Cosine LR + ε-greedy + RCW + KPop + EMA 权重优化`、§57"19 张表…ORM 定义"、§143"约 80 个组件映射到 src/"。读起来像已实现代码地图，与项目自身"零代码"声明制造虚假"已落地"印象。两份不可能同等可信。
- **组件数虚报**：§143 称"约 80 个组件"，逐表实数为约 63 行（§1=6,§2=5,§3=4,§4=24,§5=8,§6=8,§7=3,横切=5）。63≠80。
- **分类错放**：§89 把"跨平台身份映射 `src/access/identity_mapper.py`"塞进工作记忆层 §5，路径却是 `src/access/`，明显属接入层。
- **断链引用**：§101 "MCP Bridge……10 tools(见 api-spec §6.9)"——前文所有引用都带 `foundation/architecture-v1.0.0.md` 前缀，唯独此处跳到未定义来源的 `api-spec`。
- **RL 权重算法未映射到策略层**：RL 优化器只作为存储层一个文件被提及，与 rl-weight-spec 的"二级多维排序"定位脱节。

**B-10 `claim-implementation-matrix.md`（声明-承载对齐矩阵，102 行）**
- **免责声明与 ✅ 语义自伤（已回读确认）**：§19 声明"✅ 表示架构层已就绪，不表示代码已实现；全系统尚无运行代码"。这是诚实的。但 §71 的"v1.0 完整承载（✅）"清单把 25+ 条声明列进去，配合"架构层已就绪"的措辞，极易被误读为"已实现"。免责声明被自己的分组格式架空。
- **C-01 分组矛盾（已回读确认）**：§77 把 C-01 列在"⚠️ 部分承载"（理由：认知完整性轴 v1.0 二值化），但 §71 的 ✅ 清单又包含 C-25~C-30（含 C-01 相关的四轴），且 §27 行内标记 C-01 为 ✅。**同一声明在逐行和分组里状态不一**。
- **版本边界含糊**：§101–102 "v1.1 推进所有 ⚠️ 项至完整承载"，但 ⚠️ 组的 C-15（内隐调制）"共享基元仅概念声明，无组件定义"、C-36（动机性遗忘）"机制差异"——这些在 v1.1 真能"推进至完整承载"吗？没给机制，只是喊口号。
- **"暂定"写在承诺清单里**：§90 C-06"表征降级门控"预期实现写"暂定"——"暂定"写在承诺实现清单里，等于没承诺。

**B-11 `nfr-specification.md`（NFR 规格，86 行）**
- **可用性指标自我否决**：§55 系统可用性"≥ 99.9%（v1.0 设计目标……单进程无守护模式不承诺此指标）"——同一单元格先承诺 ≥99.9%，立刻又说单进程模式不承诺，还补"此指标未在 requirements-baseline 中定义"。既未定义又算什么需求？
- **数字全是拍脑袋**：§19 自承"尚未经代码运行验证"，§32 吞吐 ≥100/≥500 ops/s、§68 磁盘年增长"≤2GB"均无硬件基准/推导。"可配置"当万能挡箭牌（§78 LLM 日预算"可配置，超限熔断"，无数值）。

**B-12 `rl-weight-spec.md`（RL 权重规格，79 行）**
- **"和≠1 正常"与示例自相矛盾**：§48"不做 simplex 归一化（和≠1 是正常的）"，但 §26–30 默认值 `0.40+0.20+0.15+0.15+0.10=1.00`，§79 JSON 示例总和正好 1.0。文档一边说和≠1 正常，一边给的范例和=1。要么范例该故意不归一，要么那句"和≠1 正常"是错的。
- **P6 自相矛盾**：§20/§72 反复宣誓"禁止单标量聚合"，但 §43 写"跨维冲突……由辞典式优先级解决：relevance < recency < frequency < user_feedback < trust_score"——给五个维度排了单一线性优先级链，本质是用固定顺序把多维压成一维裁决，与"禁止单标量聚合"精神抵触。合规表里却勾了 ✅。
- **未定义术语**：§76 的 "RCW + KPop" 本规格从未解释；EMA decay、`max_steps`、`lr_min`、`base_lr`、`KAIROS_RL_MAX_BUFFER_SIZE` 全部无数值。
- **`user_profiles` 表悬空（已回读确认冲突）**：§79 称权重"以 JSONB 存储于 `user_profiles` 表的 `rl_weights` 字段"，并要求"代码实现时需在 data-model.md user_profiles 表补充该字段"；但 implementation-map §57 明确定义"19 张表（11 核心 + 8 张 v1.0 新增）"，未提 `user_profiles`。要么 19 张表数漏了，要么 RL spec 引用了不存在的表。
- **日期漂移**：本文 created 2026-07-22/updated 2026-07-23，比 implementation-map（07-20）新 2–3 天，却引用 architecture §10.14；旧文档未同步。

### C. development/（开发文档）

**C-1 `technology-stack.md`（技术选型，83 行）**
- **框架之争的另一半**：§26 选 Litestar ≥ 2.0；但 development-setup §17 说实际入口是 `python amber/main.py（FastAPI）`，implementation-map §99 也写"Litestar handler"。技术选型与 setup/实现映射三方对不上（见跨文档 C-1）。
- **APScheduler 版本不存在**：§28"目标兼容：3.10–3.12"——APScheduler 3.x 线最高 3.10，没有 3.11/3.12。编造的兼容范围。
- **Litestar 范围过时**：§26"目标 2.0–2.4"，当前 Litestar 早已 2.10+。stale。
- **无 CLI 框架**：系统全 CLI 驱动（`kairos init/serve/admin`），§1–§6 从不提 Typer/Click/argparse。最常用面未指定。
- **`uv + pip` 无版本**：§56 写"包管理 | uv + pip"无版本，setup 却要求 `uv ≥ 0.4`。版本纪律不一致。

**C-2 `development-setup.md`（开发环境搭建，133 行）**
- **框架自相矛盾**：§17"实际入口为 python amber/main.py（FastAPI）" vs technology-stack §26 Litestar。一个项目不能两个 web 框架同时是"选定"。
- **缺启动必需的环境变量（致命）**：security-spec §5 要求 `KAIROS_SALT`/`KAIROS_SECRET_KEY`/`KAIROS_AUDIT_HMAC_KEY`/`KAIROS_API_KEY`/`KAIROS_DB_PASSWORD`/`KAIROS_DB_DSN` 启动必填；本文**一个都没列**。开发者照此文档 verbatim 跑，直接启动拒绝，且唯一能救的 `kairos init --init-key` 又自承"CLI 尚未构建"（§21）。死循环。
- **CLI 前提自相矛盾**：§21"CLI 尚未构建" vs 全文是 CLI 教程（`kairos init`/`serve`/`admin key generate`）。
- **默认路径两说**：§62 `kairos init --db sqlite:///data/kairos-dev.db` vs security-spec §4 默认 `~/.kairos/`。
- **密码占位符连不上**：§66 `POSTGRES_PASSWORD=kairos`，§67 示例却写 `postgresql://postgres:***@localhost:5432/kairos`，`***` 连不上。
- **BGE-M3 既是前置又是自动下载**：§33 表列"轻量模式本地运行需要"，又说"自动下载（首次 kairos serve 时）"。既是前置又自动，矛盾。
- **pre-commit 无配置**：§50 `pre-commit install` 但从未提 `.pre-commit-config.yaml`，tech-stack §5 也漏了 pre-commit。
- **Windows 激活命令错**：§44 `.venv\Scripts\activate` 在 Git Bash 下需 `source .venv/Scripts/activate`。

**C-3 `coding-conventions.md`（开发规范，119 行）**
- **"无代码" vs "有入口"**：§21"以下命令（uv run kairos、docker build 等）为目标示例。当前草稿完善阶段期尚无运行代码"；但 development-setup §17 说真实入口是 `python amber/main.py`。一份说无代码，一份说这是运行入口。
- **命名规则自相矛盾**：§39"异步函数 | async def + _async 后缀（仅在函数名不足以表达异步性时）"——"仅在…时"使后缀成可选，例子却只有一个。等于"按心情遵守"的规则。
- **示例推翻规则**：§36 称 `kebab-case（路径段）`，例子 `kairos://users/default/core/` 是带斜杠的 camel/snake URI，不是 kebab-case。
- **死配置键**：§35 列 `KAIROS_DAILY_BUDGET_FEN`/`FORGETTING_SCORE_THRESHOLD`/`MAX_PROTOCOL_COUNT=10` 作例子，三者在全集群任何文档都未定义/默认值/引用。"FEN" 是象棋记谱单位，明显 copy-paste 残留。

**C-4 `integration-design.md`（集成设计，135 行）**
- **章节编号错乱**：§80"## 五、事件回调"、§118"## 五、MCP 集成"、§90"## 六、配置集成"夹在中间。两个"五"、六在五前。任何"§5"交叉引用都找不到北。
- **超时歧义**：§31 客户端默认 `timeout 30s`，§99 `timeout=30`，但 §2 表（49–55 行）给 write=10s/search=10s/calibration=5s/freeze=5s/config=5s。客户端 30s 和 op 级 10s/5s 谁先触发？未定义。
- **两种不兼容的并发模型**：§61 单进程"最后写入者胜出（version 递增）"；§67 多进程 PostgreSQL"乐观锁（If-Match）→ 409 Conflict 重试"。最后写入者胜 vs 409 冲突重试是相反策略，未说明何时用哪种、如何切换。
- **"stale 是状态还是不是"自相矛盾**：§63 称标记态"非持久状态机态"，又引用四态机 `(active/stale/archived/superseded)` 其中 stale 是成员。既是又不是。
- **未定义的 "Hermes Agent"**：§120 把 MCP 消费者叫"Hermes Agent"，全集群其他文档叫"宿主 Agent"/"Agent 应用"。Hermes 从哪来？未命名也未澄清。
- **webhook 开空头支票**：§82 webhook 接收/处理"标记为 v1.1 持续完善"——"以后再说"。

### D. security/（安全文档）

**D-1 `security-specification.md`（安全规格，148 行）**
- **S-01 缺 Key 返回码冲突（已回读确认）**：§29"运行时缺 Key 返回 HTTP 401"；但 coding-conventions（§86）写"安全红线违反 | return 403"，integration-design（§76）写"安全红线违反 | 返回 403 + ERR-SEC-*"，error-reference 把一切红线违反归 ERR-SEC-001(403)。S-01 是红线，却一文档 401、两文档 403。
- **权威声明自相矛盾**：§25"本文 S 编号……所有文档以此编号为准"（自称权威），但 threat-model §16 把 S-01~S-19 的权威指向 `architecture §8`。到底谁 canonical？两文档说法冲突。
- **S-03 阈值缺失**：§31"超限返回 413"，无数字；64KB 限只在 threat-model §51。需求文档不含自己需求的阈值。
- **read-only 范围内部矛盾**：§34 说 read-only 写操作→403（L+P），§2.2 表（69 行）read-only 权限列为"仅 P"。L 模式下 read-only key 存在与否，两处不一致。
- **静态加密是甩锅**：§3.1"At-rest | SQLite 加密扩展 / 全盘加密（OS 层）"——"OS 层 FDE"不是应用安全控制，等于应用啥也不做指望 OS。SQLCipher 提了名但无版本/密钥/配置。
- **盐轮转机制没设计**：§109"轮换时保留旧盐值验证已有哈希"——验证器怎么知道每条哈希用哪个盐？无 versioned-salt/salt-id 方案，只断言不设计。
- **事件响应儿戏**：§140"单人开发 = 你自己发现→自己修→自己记教训"——直接架空 threat-model 的 STRIDE"Critical 必须修复后方可发布"严重度模型。

**D-2 `threat-model.md`（威胁模型，103 行）**
- **权威冲突**：§16 把 S-01~S-19 指向 `architecture §8`；security-spec §25 自称权威。见上。
- **§4 标题自打脸**：§68"以下安全红线的威胁场景在当前 STRIDE 映射中未覆盖"，但表格随后给 S-05、S-10…S-19 的缓解——"未覆盖"然后"这是覆盖"。自相矛盾。
- **有威胁无需求（gap）**：§3 LLM 攻击（提示注入致令牌耗尽/ prompt 泄露/成本炸弹/Judge 漂移）有缓解（日预算上限/黄金集回归）但**无对应 S-0x 编号**；SSRF（§61）缓解用 `KAIROS_SSRF_*` 环境变量，但这些变量**在 security-spec §5 密钥管理里完全没出现**。威胁模型定义了安全规格不追踪的控制。
- **审计链描述不可实现**：§91–98 定义 content_hash 链 + HMAC 链两条，验证步写"条目 N 的 previous_hash == 条目 N-1 的 hash"——但存储字段是 `content_hash`/`hmac`/`prev_hmac`/`prev_content_hash`，无 `previous_hash`。"哪条 hash"混淆，无法落地。
- **"物理隔离"非物理**：§103"审计日志存储位置与数据存储物理隔离（独立表或独立文件）"——同一 SQLite 文件里的独立表不是物理隔离。括号内悄悄推翻了声称。

### E. ops/（运维文档）

**E-1 `configuration.md`（配置参考，225 行）**
- **`KAIROS_LITE_MODE` 幽灵参数**：§2 称"部署模式特有参数（如 deployment.md 中的 `KAIROS_DB_DSN`、`KAIROS_LITE_MODE`）分别在对应文档中定义"——`KAIROS_DB_DSN` 在 deployment 有，但 `KAIROS_LITE_MODE` 在 deployment 全文查无。断链。
- **可靠性参数未真正暴露**：§2 称"可靠性参数（LLM 超时/熔断）分别在对应文档中定义"，reliability §1.5 列了超时/重试/熔断表，但**未作为 `KAIROS_*` 环境变量暴露**。不是真"可配置参数"。
- **重复键**：`KAIROS_SANDBOX_CONFIDENCE_INTEGRATION_THRESHOLD` 在 §3:61 和 §5:98 逐字重复，版本记录却分别计数（§3 算 9、§5 算 7），总数 95 含重复。记账马虎。
- **单位纪律不一致**：`KAIROS_VIRTUAL_CALIBRATION_TIMEOUT=900`（秒，§31）绝对秒，而同表族几乎都用"调度周期"单位（调度周期=`KAIROS_SCHEDULER_INTERVAL=300s`）。900s=3 周期却不这么写。

**E-2 `deployment.md`（部署指南，194 行）**
- **无回滚（已回读确认）**：§8 升级给 `docker compose pull`+`up -d`+`kairos db migrate`，但 image 是 `kairos/kairos:latest`（§123，无版本钉死），无任何"回退旧镜像"命令。部署文档忘了怎么撤销部署——不可原谅。
- **自动迁移 vs 手动迁移打架**：§155"轻量模式自动创建数据库和表结构。启动时自动执行迁移"，但 §8 升级/runbook 又让你手动 `kairos db migrate`。自动还是手动？二选一。
- **SQLite 路径错（已回读确认）**：§59 轻量模式 DSN `sqlite:///data/kairos.db`；但 reliability §29 备份 `~/.kairos/kairos.db`，runbook §59 恢复至 `~/.kairos/kairos.db`。**部署的运行时 DB 路径与备份/恢复路径不一致 → 备份抓错文件，数据丢失 bug**。
- **`.env` 从哪来没说**：§143 用 `${KAIROS_DB_PASSWORD}`，从没解释 `docker compose` 自动加载 `.env` 及如何创建；`kairos init --init-key`（§66）"写入环境文件"但文件名/路径从不说明。
- **全文占位**：§18 自承"无构建产物或 Docker 镜像，部署命令将在代码启动后交付"。三种部署模式，零可执行。

**E-3 `observability.md`（可观测性，129 行）**
- **容器日志去向矛盾**：§19"日志通过异步 I/O 写入 `~/.kairos/logs/`——always"；但 deployment §171 说容器模式→stdout，本地→`~/.kairos/logs/`。容器日志到底去哪，两文档冲突。
- **`trace_id` 不存在却被宣称**：§84"日志 schema 已包含 `trace_id` 字段（§二）"，但 §二 日志 schema（64–79 行）字段是 timestamp/level/logger/message/module/function/line/memory_id/forgetting_score/event_id/duration_ms/error_code，**无 `trace_id`**。拿不存在的字段做请求级追踪，不可实现。
- **`/metrics` 端点没人配**：§19"指标通过 `/metrics` 端点以 Prometheus 文本格式暴露（端口 8010/metrics）"，但 deployment 从未暴露/文档化 `/metrics`（只有 `/health`），docker-compose 无 exporter/Prometheus/Grafana。指标表 11 项无采集器、无 scrape 配置、无仪表盘——摆设。
- **告警绑phantom SLO**：§四 告警"NFR 写入 P95 通过率 < 99%"，但无 SLO 文档在本批（NFR 在 specification，未提供）。告警对着不存在的目标算数学。
- **900s 双重语义不调和**：configuration `KAIROS_VIRTUAL_CALIBRATION_TIMEOUT=900s` 生成虚拟信号；observability"校准中断警告"也在 900s 触发——一个是"生成合成校准"，一个是"警告校准过期"，同一 900s 两语义未调和。

**E-4 `reliability.md`（可靠性，108 行）**
- **备份路径错（已回读确认）**：§29 SQLite 备份 `cp ~/.kairos/kairos.db ...`；但 deployment 运行时 DB 是 `sqlite:///data/kairos.db`。备份抓的是错误/不存在的文件 → 具体数据丢失 bug。
- **持久性 vs RPO 自相矛盾**："写入确认基于内存缓冲收讫而非落盘确认"（约 48 行）；若缓冲不持久，崩溃丢已确认写入，直接冲突 RPO"≤5 分钟"和"数据可靠性"声称。
- **恢复演练没机制**：§四"每月自动运行一次干恢复演练，由健康检查触发"——无 scheduler/ cron/触发机制说明。"触发"靠什么？
- **磁盘阈值两机制打架**：§56–58 硬编 75/85/92%；deployment §72–73 用 `KAIROS_CORE_LIMIT_BYTES=25KB`/`KAIROS_CORE_LIMIT_LINES=200` 作真实容量闸门。两套竞争机制未调和。

**E-5 `runbook.md`（运维手册，223 行）**
- **恢复步骤缺失**：§6.4"证伪响应"让你"按架构 §10.10 证伪响应路径处理"——无实际步骤，纯指针。
- **冻结/降级告警无处置**：observability 说"冻结超时自动告警至外部管理员"，runbook **无对应人工处置步骤**。恢复 playbook 缺口。
- **错误码索引不全**：§5.3 错误码索引止于 ERR-SEC-001；troubleshooting 还定义了 ERR-DB-002、ERR-LLM-002、"安全事件排查"、"升级失败回滚"。runbook 索引相对兄弟文档不全。
- **lite 模式绑定模糊**：§1.1 `kairos serve --port 8010` vs deployment `127.0.0.1:8010:8010`——lite 模式绑 localhost 还是全接口？安全歧义。

**E-6 `troubleshooting.md`（故障排查，47 行）**
- **表格结构损坏**："错误码索引"（约 31 行）、"安全事件排查"（约 44 行）被塞进"症状"列，排查步骤/恢复命令单元格为空——明显 copy-paste 格式失败。
- **"一键模式"未定义**：约 28 行"一键模式"——全 6 份文档从未解释。
- **与部署矛盾**：ERR-DB-002"数据库迁移失败"暗示迁移会失败需手动回滚；但 deployment §155 称迁移启动时自动。若自动，为何会静默失败需排查？叙事不一致。

### F. quality/（质量文档）

**F-1 `acceptance-criteria.md`（验收标准）**
- **不接 feature-list 的 ID**：功能检查表（80–88 行）写"记忆 CRUD/路径空间/语义检索/双副本分离…"纯散文，无一引用 traceability-map 的 W-01~/R-01~/M-01~ 等 ID。**验收标准根本没接到功能 ID**，可追溯性为零。
- **半吊子判据**：D-201 第 3 条（28 行）主判据"偏差 ≤20%"，又自承"对短周期事件（日周期 20%≈4.8h）实用意义有限"，塞进"±2h 补充判据"——判据自我削弱。
- **D-202 自相矛盾且不可验收**：D-202 第 3 条（36 行）"身份记忆降级门槛由宪法修订端口降至元认知层+宪法解释层联合审批"——既说"降至"（门槛更低=更易降级），第 2 条又说"核心身份不可降级"，且全文未定义"核心/外围"。
- **D-204 状态跨文档打架**：本文把 D-204 列作待验收债务；traceability-map §45 标 D-204"已闭环"；debt-collection 说 D-204"已并入 DC-019+DC-027 闭环"。同一债务三说。
- **监测器无通过阈值**：D-206 三项监测器（67–70 行）只说"可通过 API 查询"，无任何通过阈值。

**F-2 `benchmark-plan.md`（性能基准，110 行）**
- **断链**：§17/§44 引"NFR 规格 §一"，本批无 NFR 文档（在 specification，未提供），目标值来源不可验证。
- **§3.4/§3.5 无验收挂钩**：升华批处理、磁盘增长只有"步骤"无通过/失败判据；acceptance-criteria 非功能检查只接 §3.1–3.3。
- **轻量模式是摆设**：§27–29 定义"轻量模式 2核/2GB"，但所有数据规模（33–38 行）都标"标准模式/PostgreSQL"，轻量模式零基准目标。
- **内存泄漏判据不可执行**：§101"连续 24h 增速 >1%/h 阻塞发布"——基准套件是快照测试，24h 连续监测如何跑、谁跑、何时告警，只字未提。

**F-3 `test-plan.md`（测试计划，148 行）**
- **覆盖夸大（已回读确认）**：§1 称"v1.0 核心覆盖"，但 §3.1 标题"写入（W-01~W-07）"只给 W-01/02/04/07 用例，**W-03 批量导入、W-05 关系标注、W-06 高信用源豁免完全无用例**；§3.2/3.3 只覆盖 R-01、R-02，R-03~R-08 全空；§3.5 标题"C-01~C-04"只给 C-01/03/04，缺 C-02；CAL-02/05/06 无用例；SF-01~SF-04 在 traceability 是 v1.0 能力，test-plan 核心路径里一个 TC-SF-* 都没定义。声称覆盖 v1.0 核心，实际大量 v1.0 能力零用例。
- **自我矛盾**：§19"代码启动前应完成核心路径用例定义……按 TDD"与同段"具体用例数待代码启动后根据实际接口数量确定"互相否定。
- **S-01 张冠李戴**：TC-W01-003（60 行）把运行时缺 Key 返回 401 标为"S-01 启动拦截"；但 test-strategy §2.2 明确 S-01="无 Key 启动 拒绝启动"（启动期拦截），运行时 401 是 ERR-AUTH-001。两层级混为一谈。
- **退出准则漏项**：test-plan §2 只提"单元覆盖率≥80%/6 E2E/19 红线"，漏了 test-strategy §5 的"分支覆盖率≥70%"和"P6 合规 100%(4/4)"。

**F-4 `test-strategy.md`（测试策略，174 行）**
- **E2E 六条两套清单（已回读确认）**：§四（147–154 行）列：冷启动→写入→检索 / 升华触发→审批 / 外部校准→见证更新 / **外部校准中断→降级** / 冻结→恢复 / **安全红线 S-14**。test-plan §3.6 的 E2E-01~06 是：写入→检索 / **写入→遗忘→复兴** / 写入→升华 / 校准→见证更新 / 冻结→恢复 / **审计链验证**。两处都自称"6 条关键路径"，但"外部校准中断→降级"/"S-14" vs "遗忘→复兴"/"审计链验证"互不全重叠、无交叉引用。**到底哪 6 条是发布红线？**
- **S-07 表格格式损坏**：§67 `| S-07｜敏感信息加密与脱敏｜...` 用全角 `｜` 混排，破坏 markdown 表格列结构。
- **ERR-SEC-001 与 §2.2 冲突**：error-reference 把一切红线违反归 ERR-SEC-001(403)；但本文 §2.2 给 S-02→429、S-03→413、S-15→422、S-06→403——红线违反 HTTP 码根本不统一为 403。
- **单元用例无对应**：§2.3–2.6 枚举 P6(4)/前瞻(4)/种子(4)/推理皮层(2) 共 14 组单测，test-plan 里无任何 TC-* 对应（test-plan 只写"单元 待定"）。策略在枚举，计划在拖延。

### G. references/（参考文档）

**G-1 `domain_keywords.yaml`（45 行）**
- **中英数量不对等**：`computer_vision` 中文 5 个（含 OCR），英文 4 个（缺 OCR 对应词）。
- **纯占位 stub**：头部注释"无同义词/权重/匹配规则"，领域路由如何打分/阈值多少/TF-IDF 何时引入（"代码启动后"）全无定义。
- **断链**：§3 指向"architecture §10.16 / §3.1"，本批无 architecture 文档。

**G-2 `error-reference.md`（错误参考，133 行）**
- **ERR-LLM-002 冗余**：§70 自写"同 ERR-RATE-003，建议统一使用 ERR-RATE-003"——既建议统一，为何保留 ERR-LLM-002？两份码指同一事，制造歧义。
- **与 test-strategy 冲突**：ERR-SEC-001(403) 与各 S-xx 具体 HTTP 码（429/413/422/403）矛盾，见 F-4。
- **404 语义不一致**：ERR-DB-004(404) 用于"记忆未找到"；但 test-plan TC-R01-002 要求"路径不存在返回空列表，非 404"。按 ID 查 vs 按路径检索返回码不同，未说明有意还是疏忽。
- （唯一做对：计数"9 类 38 个"经核算确实 38 条。）

**G-3 `glossary.md`（术语表，116 行）**
- **"约 52 条"**：§116 用"约"——术语表要么精确要么别写数字。
- **HMAC 不绑"原因"**：审计链公式（§107）`hmac(n)=HMAC(key, timestamp+operator+action+content_hash+prev_hmac)` 不含"原因/reason"，但 acceptance-criteria D-204 第 3 条要求审计日志含"原因"。**原因字段不被完整性保护**，审计防篡改出现缺口。
- **"五轴"vs"五维"混淆**：glossary"五轴度量空间"（§39）指五个正交轴；usage-load-algorithm"五维负载向量"指使用价值轴的五个子维度。两处都叫"五"，读者极易误认同一概念，glossary 未澄清。

**G-4 `traceability-map.md`（可追溯性映射，118 行）**
- **债务计数自相矛盾（已回读确认）**：§16 头部"debt-collection（11 项开放 + 7 项已闭环）"=18 项；版本记录 §118"11 债务（含 1 项已闭环）"=11 项。同一文件两处总债务数不同。
- **D-204 状态冲突**：§45 M-04 行"D-204（已闭环，见 DC-019+DC-027）"；acceptance-criteria 把 D-204 列作开放债务；debt-collection 说已并入闭环。三说。
- **空单元格泛滥**：W-07、M-06、A-01、A-02、A-07、CAL-06 等整行"对应认知声明/债务/差距"全空——健康检查、配置查看、DB 迁移、记忆导出等 v1.0 能力**无任何声明约束**。stub 证据。
- **D-202/D-203 无映射**：acceptance-criteria 的 D-202（动态身份增强）、D-203（能力转化状态机）在本表无任何能力指向。
- （37 声明数对得上：claim-matrix 确有 C-01…C-37 共 37 行，README 的"37 声明"无误；agent 此前称"仅 17 个"是误数，已纠正。）

**G-5 `usage-load-algorithm.md`（68 行）**
- **"五类"vs"五维"**：标题"五类负载算法"（§14）与正文"五维负载向量"（§20）自不一致。
- **P6 自打嘴巴**：§三（§47）"禁止聚合为单标量（P6）"，但 §一（§22–29）给每个维度赋加权系数 1.2/1.4/1.6/1.8/2.0，且 §四明说"系数越高，该维度负载对决策影响越大"——**正是用标量权重决定维度重要性**，与"禁止标量聚合"的 P6 声明相互拆台，文档用"工程便利"一笔带过。
- **参数一半内联一半外置**：系数内联，但 `MERGE_THRESHOLD=0.7`、`base_rate=0.01` 推给 `ops/configuration.md`，同一算法引用不一致。

**G-6 `value-dimension-entropy.md`（73 行）**
- **冻结权归属混乱**：§二（§44）坍缩时"触发宪法修订端口应急冻结"；glossary 说宪法修订端口是主权面用于校准信号注入；test-strategy §2.3 说"例外率超限冻结"冻结的是操作权限；acceptance D-202 又把冻结/降级审批权"降至元认知层+宪法解释层"。**谁有权冻结、什么信号触发，三处打架**。
- **"五"是否同一五**：同 usage-load 的问题，熵算法把五个使用子维度当概率分布，与"五轴"命名撞车，无澄清。

**G-7 `vad-coordinate-algorithm.md`（82 行）**
- **复制粘贴**：§42 与 §46 几乎是同一句"若所有分量均为默认值……V_init=0.03，此时向上舍入/取整后写为 0.1"逐字重复。低级错误。
- **自相矛盾措辞**：§42 称默认 0.1 为"默认厌恶中性值（默认 0.1，偏好轻微正面）"——"厌恶"是负值含义，0.1 却是正值（轻微正面）。同一句既说厌恶又说正面，逻辑不通。

### H. governance/（治理文档）

**H-1 `adr.md`（架构决策记录，289 行）**
- **"已采纳"+"设计进行中"伪确定性**：盖子称"所有 ADR 架构选择已锁定"，但 ADR-001 说采用 PostgreSQL，正文又塞"轻量模式继续支持 SQLite+sqlite-vec"，而用户指南/快速入门把 SQLite 当默认/开箱即用。决策状态写"已采纳 + 设计状态：进行中"——"已决定但没设计完"，等于没定。
- **含糊的劣势**：ADR-003 说四条公理"抽象度高，新读者门槛更高"作劣势，却没解释门槛多高、谁来填；ADR-004"需要手动组织路径"作劣势不量化成本。
- **断链**：ADR-007 引"架构 §3.2 多 Provider 冲突消解协议"——本批无 architecture 文档，§X.Y 全是死链嫌疑。

**H-2 `changelog.md`（变更日志，76 行）**
- **draft 玩到 draft.3**：`status: draft` 却给 v1.0.0-draft.3 叫"R15 全量审计修复"。draft 版本号玩到 .3 还编造 R15 轮次。
- **数字打架**：§25"99→101 项能力（9处）"；README §16"101 项能力（43 核心 + 58 扩展）"；MNM 表一路 43→68→72→…→98 项（debt-collection 内）；又说"43→101"。到底 98 还是 101？
- **断链**：引 `README L152`、`L2058`、`cognitive-foundation 表`、`architecture §10.10`——L2058 行？哪份文档有 2000+ 行被引用？悬空引用。
- **自扇耳光**：前句"刚统一 9 处计数"，后句"全量 grep 清扫零残留"——自己打自己脸。

**H-3 `cognitive-architecture-gap.md`（差距表，49 行）**
- **P6 "铁律"已破却称"受控偏离"（已回读确认）**：G-07（§29）"P6 全局闸门合规——压缩比 ≤30%"，但"双口径统计（简版~33%/12维基数，全量~43%/14维基数）均已超出 30% 上限；活跃例外类型数 4>2"。**一个被反复称为"铁律/全局闸门"的规则，v1.0 已破 33%~43%，却归为"受控偏离"**。被打破近一半的"铁律"等于没有铁律。risks R-020 还补刀"若 v1.1 仍无法恢复，P6 从铁律退化为软约束"——自己埋雷。
- **判据不可执行**：12 条全部"收敛状态：pending"，"闭环判据"写"可输出非 1.0 的值"等空话，但 v1.0 连代码都没有，判据无法执行。
- （差距统计表"总计 12"对得上，少数算对的地方。）

**H-4 `debt-collection.md`（追缴清单，424 行）**
- **DC-ID 追踪成环**：changelog 说"traceability-map 引用 DC-019/DC-027"；D-204（§168）说"审计报告追踪缺失项（DC-019/DC-027 引用 D-204 但无独立条目）"。DC-019（§411）、DC-027（§419）存在，DC-028（§424）"D-204 定向遗忘机制 已闭环（与 DC-019 合并闭环）"。D-204、DC-019、DC-027、DC-028 四者说辞不完全一致（一个说 v1.0 已并入，一个说 v1.1+），追踪闭环声明成俄罗斯套娃。
- **编号灾难性碰撞**：D-201（§102）、D-202（§110）在"需实现阶段"区已用过；§134 又出现第二个 D-201（逻辑-因果轴完整落地）、§144 第二个 D-202（动态身份增强）、§154 D-203、§164 D-204、§174 D-205……**D-201~D-204 被复用两次**。documentation-governance §5 注册表写"债务编号（D-001~D-211）"——但 D-201~D-211 在前半段（D-201 注册表、D-202 编译器、D-203 管道、D-204 CRI）已被占用，后半段又用 D-201~D-211 当另一组。ID 碰撞。
- **表格结构崩坏**：DC-003~DC-026 在 MNM 表中间插进来（§395–418），与前面 DC-001/DC-002（§250）和后面 DC-027~DC-031 混排，中间夹 MNM-101~MNM-107（§388）。DC 与 MNM 编号空间在同一张大表里交错。

**H-5 `documentation-governance.md`（文档治理，110 行）**
- **自我否定**：§4"代码启动前，全部文档保持 draft 状态"，却定义 `v1.0.0` 状态"与 architecture-v1.0.0.md 无矛盾"——但 adr/README 给文档打 `status: v1.0.0`，草稿阶段冒出 v1.0.0 状态，规则自相矛盾。
- **空话**：§3 审查周期"每月全量文档状态审计（draft→final 晋升）"，§4 却又说晋升规则"待代码启动后执行"——每月审计个寂寞？
- **断链**：§1 联动表引 architecture/data-model/api-spec/nfr/threat-model 等，全在文档库外。

**H-6 `project-plan.md`（项目计划，85 行）**
- **致命矛盾**：标题"从草稿完善阶段到 v1.0.0 可运行的里程碑分解"，但 §17"当前 v1.0.0 为草稿完善阶段版本，代码尚未启动"。Phase 0~3 全是代码里程碑，却"周数待代码启动后制定"——**一份没有周数、没有日期的"计划"**。README §63 写"4 Phase × 12 周里程碑"，project-plan 正文根本没有 12 周字样。数字从哪来？
- **含糊**：风险表"跨层协调复杂度超限"缓解写"绝对上限 10 条协议控制"，但 risks R-006 说"已有 7 条，仅余 3 条"且"软门禁（非强制拦截）"。计划和风险对"上限是否强制"表述不一。
- **ASCII 画箭头干嘛**：Phase 图箭头下写"具体周数待定"。

**H-7 `release-guide.md`（发布指南，143 行）**
- **教人发布不存在的包**：§1"v1.0.0 = 设计冻结版（当前版本）。代码首版从 v1.1.0 起"，但 §2 检查清单要求"单元测试覆盖率 ≥80%""6 条 E2E 全部通过""19 条安全红线逐条验证"——对没代码的版本做发布检查；§3 直接写 `kairos --version`/`kairos health`/`uv build` 等命令，但 quick-start/user-guide 都明说"CLI 尚未构建、命令为虚构"。
- **断链**：§135 引 `security/security-specification.md §4`——外部文件。

**H-8 `risks.md`（风险登记册，172 行）**
- **编号断裂**：架构级 R-001~R-007，哲学张力 T-001~T-003，方法论 M-001~M-002，然后突然 **R-020**（§137）"P6 受控偏离缺乏可验证问责路径"——R-008~R-019 去哪了？直接跳 R-020。
- **含糊**：R-001"治理/功能复杂度比偏高"——"比"是多少？无数值，纯定性抱怨。
- **"mitigated" 自欺**：R-004 说审计庭已剥离至独立监督平面"已缓解"（`mitigated`）；R-007 又说解释层偏置"无独立监测回路"。缓解了一半就宣布 mitigated。
- **"resolved" 文字游戏**：T-001"状态演化轴缺位"标 `resolved`，描述却"认知模型的全过程覆盖因此被显式缩减"——解决的是文档声明，不是问题本身。

**H-9 `social-calibration-roadmap.md`（社会性校准路线图，170 行）**
- **与现实冲突**：全文建在"代码未启动"前提上，却定义 M1~M4、SCR-01~05，以及"生产环境稳定运行至少 3 个完整校准周期""经历过 2 次完整的外部校准中断→恢复循环"等验证指标。**零代码系统谈生产环境运行周期，纯幻想**。M2 触发条件要求"单Agent系统已在生产环境稳定运行至少 3 个完整校准周期"——你连 serve 都跑不起来。
- **与 ADR-007 版本漂移**：ADR-007 说 v1.0 单 Provider，多 Provider 冲突消解 v1.1+；roadmap M3/M4 大谈多 Agent 校准（必多 Provider），与 D-209/D-210 的 v1.2/v1.3、D-208 的"v2.0 前置"对不上。

**H-9b `README.md`（文档索引，137 行）**
- **算术错误（已回读确认）**：§110"43 能力↔37 声明↔89 追踪项（27 闭环 DC + 62 MNM + 11 待实现 D）"。**27+62+11 = 100 ≠ 89**。
- **数字乱飞**：§16"101 项能力（43 核心 + 58 扩展）"；§35"12 类 101 项"；§110"43 能力↔37 声明↔89 追踪项"。
- **操作数三说**：§45 称 operation-catalog"50 项标准操作"，文件自身说 52（实 53）。
- **文档计数矛盾**：§125"总计 52 份文档（…governance 9…）"，但 §68 列 governance 时只列 8 个（漏一个）。
- **死链（已回读确认）**：§68 `[governance/release-process.md](governance/release-process.md)`——实际文件名是 `release-guide.md`，链接 404。
- **断链一堆**：大量 `foundation/...`、`specification/...` 指向未在本批提供的文件。

### I. user/（用户文档）

**I-1 `quick-start.md`（快速入门，118 行）**
- **自扇耳光**：§17"CLI 工具尚未构建"，§21"命令将在代码启动后交付"，但 §34 直接给 `pip install kairos`、`kairos init`、`kairos serve` 当真命令写。§107"全部操作约 2 分钟"——对不存在的 CLI 测 2 分钟？
- **两个 `kairos init` 参数混乱**：§42 `kairos init --init-key` 是第二步，§55 `kairos init --db sqlite:///$HOME/.kairos/kairos.db` 是第三步，用户搞得清？且 §29 说 KAIROS_SALT"由 init --init-key 自动生成，前置条件阶段无需手动设置"，又列在"前置条件"里，逻辑绕。
- **断链**：指向 `amber/README.md`（外部实验代码）。

**I-2 `user-guide.md`（用户指南，210 行）**
- **最诚实也最分裂**：§21 自承"全部 CLI 命令为虚构"，但 §50 有未闭合代码块（```bash 后直接 `kairos serve`，缺开头 ```），**Markdown 语法破损**。
- **数字矛盾**：§200"并发写入 ≤60/min（≈1 ops/s）"——60/min 明明是 1 ops/s，但又说"系统容量目标 ≥100 ops/s（多客户端）"。60/min 单客户端 vs 100/s 系统容量差 100 倍，限流逻辑没说清。
- **种子锚点代码块破损**：§186 `# 种子路径设置` 前缺 ```bash 围栏，与 §187 混在一起。
- **与 quick-start 路径风格不一**：quick-start §55 `$HOME/.kairos/kairos.db`；user-guide §36 `~/.kairos/kairos.db`（等价但 `$HOME` vs `~` 风格不一），而 changelog §28 说"用户文档 ~/.kairos/kairos.db，部署文档 /data/kairos.db"——治理文档自己要求"单一事实源"却三处写法不一。

---

## 第二部分：跨文档一致性对齐问题（核心交付）

> 每条：涉及文档 → 具体位置 → 实质 → 后果。已回读核实的标【已核实】。

**1. 「无运行代码」 vs 「已实现/可定位」的系统性假确定性【已核实】**
- 涉及：`claim-implementation-matrix.md` §19、`README.md` §16、`feature-list.md` §17；对比 `implementation-map.md` §17/§57/§76/§143、`development-setup.md` §17、`api-spec.md` 全文。
- 实质：项目反复声明"全系统尚无运行代码"，但 implementation-map 把组件逐一映射到 `src/` 具体路径并写死算法（rl_optimizer.py "Cosine LR + ε-greedy + RCW + KPop + EMA"），api-spec 给出 60+ 端点契约，feature-list 称"架构已实现"。两拨文档对"现在有没有代码"给出相反印象。
- 后果：第一个开发者无法判断该照"设计稿"还是"已实现代码"写，整个文档集的可信度归零。

**2. 功能总数三版不一【已核实】**
- 涉及：`feature-list.md` §17/§208（101）、`operation-catalog.md` §105（80）、`feature-list.md` 扩展表实算（100）。
- 实质：feature-list 自称 101 但逐行实算 100（"+5 写入"重复计数 W-09）；operation-catalog 又称 feature-list 是"80 项功能"。
- 后果：能力规模无单一事实源，任何"覆盖率/完成度"统计都是空谈。

**3. 操作总数三版不一【已核实】**
- 涉及：`operation-catalog.md` §100–103（自称 52，实 53）、`README.md` §45（50）。
- 实质：ENC 7 + RET 15 + STR 31 = 53，却写 52；README 又说 50。且"校准信号注入"同端点算两次。
- 后果：运维/测试无法确认系统到底暴露多少操作。

**4. R-01/R-02 端点映射硬冲突（会写出错代码）【已核实】**
- 涉及：`requirements-baseline.md` §161–162 vs `operation-catalog.md` §42–44（及 `api-spec.md`）。
- 实质：需求基线把 R-02（语义检索）映射到 `GET /v1/memories?q=`，把 R-01（路径前缀检索）映射到 `GET /v1/memories?path=`；但 operation-catalog 明确 `?q=` 是文本/关键词检索、语义检索是 `POST /v1/memories/search`、路径检索是 `GET /v1/path`。
- 后果：照需求基线写接口，语义检索会被实现成关键词搜索。这是会直接进代码的 bug。

**5. S-01 缺 Key 返回码 401 vs 403【已核实】**
- 涉及：`security-specification.md` §29（401）、`coding-conventions.md` §86（403）、`integration-design.md` §76（403）、`error-reference.md`（ERR-SEC-001=403）。
- 实质：同一红线 S-01，安全规格说运行时缺 Key 返回 401，另两份文档及错误参考说红线违反统一 403。
- 后果：客户端/测试对"无 Key 该收什么码"无一致预期，鉴权测试必挂。

**6. 安全红线权威归属冲突**
- 涉及：`threat-model.md` §16（指向 `architecture §8`）vs `security-specification.md` §25（"所有文档以此编号为准"）。
- 实质：threat-model 把 S-01~S-19 的权威定义指向架构文档 §8；security-spec 自称编号权威。两文档对"谁 canonical"说法冲突。

**7. Web 框架 Litestar vs FastAPI【已核实】**
- 涉及：`technology-stack.md` §26（Litestar）、`development-setup.md` §17（FastAPI）、`implementation-map.md` §99（Litestar）。
- 实质：技术选型定 Litestar，但 setup 说实际运行代码是 FastAPI，implementation-map 又写 Litestar handler。单一项目两个 web 框架。
- 后果：框架未定，所有 API/路由/中间件文档悬空。

**8. SQLite 数据库路径三处不一（数据丢失 bug）【已核实】**
- 涉及：`deployment.md` §59（`sqlite:///data/kairos.db`）、`reliability.md` §29（`~/.kairos/kairos.db`）、`runbook.md` §59（`~/.kairos/kairos.db`）、`security-spec.md` §4（`~/.kairos/`）。
- 实质：部署的运行时 DB 在 `/data/kairos.db`，但备份（reliability）和恢复（runbook）都针对 `~/.kairos/kairos.db`。
- 后果：备份抓的是错误/不存在的文件，恢复时无数据——具体数据丢失 defect。

**9. P6「铁律」已被打破 33%~43% 却称"受控偏离"【已核实】**
- 涉及：`cognitive-architecture-gap.md` G-07 §29、`claim-matrix.md` C-30、`risks.md` R-020、架构文档 P6 多处。
- 实质：P6（禁止无声丢失维度信息，压缩比≤30%）被反复称"铁律/全局闸门"，但 G-07 自承 v1.0 压缩比 33%/43% 已超 30% 上限、活跃例外 4>2，归为"受控偏离"；R-020 更说"若 v1.1 仍无法恢复，从铁律退化为软约束"。
- 后果：一条"不可谈判"的规则已被打破近一半且无强制机制，"铁律"名存实亡，且认知基础文本仍当硬约束引用。

**10. 部署无回滚 + 镜像未钉版本【已核实】**
- 涉及：`deployment.md` §123（`:latest`）、§8（升级步骤无回退）。
- 实质：生产镜像 `kairos/kairos:latest` 无版本钉死，升级只有 `pull`+`up -d`+`migrate`，无"回退旧镜像"命令；migrations 称"支持回滚"但部署层面无对应步骤。
- 后果：发布出错无法确定性回滚。

**11. traceability-map 债务计数自相矛盾【已核实】**
- 涉及：`traceability-map.md` §16（11 开放 + 7 闭环 = 18）vs §118（11 含 1 闭环）。
- 实质：同文件头部与版本记录对总债务数给出 18 和 11 两种说法。

**12. README 算术错误【已核实】**
- 涉及：`README.md` §110（27+62+11=89）。
- 实质：27+62+11=100，却写"89 追踪项"；同时 operation-catalog 称 feature-list 80 项（见第 2 条）。

**13. 两套 E2E 关键路径清单【已核实】**
- 涉及：`test-strategy.md` §四 vs `test-plan.md` §3.6。
- 实质：都自称"6 条关键路径"，但一组是"外部校准中断→降级 / S-14"，另一组是"遗忘→复兴 / 审计链验证"，互不全重叠、无交叉引用。
- 后果：发布红线到底哪 6 条，测试与策略对不上。

**14. "语义检索"语义冲突**
- 涉及：`feature-list.md` R-02（"纯向量语义"）vs `operation-catalog.md` §42（5D 混合排序：语义+BM25+时序+信任+热度）。
- 实质：feature-list 把 R-02 定义成纯向量，operation-catalog 把语义端点实现成 5 维混合（含 BM25/热度），等于把 hybrid（R-09）偷换成 core（R-02）。

**15. 遗忘/归档/抑制状态机三套词**
- 涉及：`use-cases.md` 场景 5、`feature-list.md` M-10、`operation-catalog.md` 软删除分级、`data-model.md` `memory_states`。
- 实质：suppressed/archived 关系在四份文档里各说各话（子态 vs 平级、状态码 vs 契约分级），无单一事实源。

**16. RL 权重持久化表 `user_profiles` 不存在【已核实】**
- 涉及：`rl-weight-spec.md` §79 vs `implementation-map.md` §57（19 张表）。
- 实质：RL spec 要求权重存 `user_profiles.rl_weights` JSONB，但 implementation-map 的 19 张表清单无此表。要么表数漏了，要么 RL spec 引用不存在的表。

**17. `usage_events.timestamp` 字段名错误（跨 detailed-design ↔ data-model）**
- 涉及：`detailed-design.md` §3 vs `data-model.md`（仅 `created_at`）。
- 实质：遗忘伪代码引用 `usage_events.timestamp`，但数据模型该表无 `timestamp` 列，只有 `created_at`。照伪代码写必报字段不存在。

**18. 自动迁移 vs 手动迁移冲突**
- 涉及：`deployment.md` §155（启动时自动）vs `deployment.md` §160/§186、`runbook.md`（手动 `kairos db migrate`）vs `troubleshooting.md` ERR-DB-002（迁移会失败需手动回滚）。
- 实质：同一部署文档既说自动又说手动；troubleshooting 又预设迁移会失败。叙事不一致。

**19. 容器日志去向冲突**
- 涉及：`observability.md` §19（always `~/.kairos/logs/`）vs `deployment.md` §171（容器→stdout）。
- 实质：容器模式日志到底落盘还是 stdout，两文档相反。

**20. `trace_id` 被宣称却不存在**
- 涉及：`observability.md` §84（称 schema 含 `trace_id`）vs `observability.md` §二 schema（无 `trace_id`）。
- 实质：同一文档内，日志 schema 字段里没有它宣称用于请求级追踪的 `trace_id`。

**21. 审计 HMAC 不绑"原因"**
- 涉及：`glossary.md` §107（公式无 reason）vs `acceptance-criteria.md` D-204（要求含原因）。
- 实质：审计完整性公式不含"原因"字段，但验收标准要求审计日志记原因——原因字段不受防篡改保护。

**22. "五轴" vs "五维" 命名撞车**
- 涉及：`glossary.md` §39（五轴度量空间）vs `usage-load-algorithm.md`/`value-dimension-entropy.md`（五维负载/使用子维度）。
- 实质：两处都叫"五"，读者极易误认同一概念，无文档澄清。

**23. 冻结/降级触发权归属混乱**
- 涉及：`value-dimension-entropy.md` §44（宪法修订端口）、`glossary.md`（主权面）、`test-strategy.md` §2.3（操作权限）、`acceptance-criteria.md` D-202（元认知+宪法解释层）。
- 实质：谁有权冻结、什么信号触发，四处说法不一。

**24. 版本语义自相矛盾**
- 涉及：`release-guide.md`（v1.0.0=设计冻结，代码从 v1.1.0 起）、`project-plan.md`（v1.0.0=可运行里程碑）、`adr.md`/`documentation-governance.md`（`status: v1.0.0`）、`changelog.md`（v1.0.0-draft.1/.2/.3）。
- 实质：v1.0.0 既是"设计冻结草稿"又是"可运行里程碑"，版本语义自相矛盾。

**25. D-201~D-211 债务编号灾难性碰撞**
- 涉及：`debt-collection.md`（前半段 D-201~D-211 被占用，后半段复用同名）。
- 实质：D-201~D-204 在文档前后两段被赋予完全不同的含义，编号空间撞车；DC-019/DC-027/DC-028/D-204 互相成环。

**26. 风险编号断裂 R-008~R-019 消失**
- 涉及：`risks.md`（R-001~R-007 后直接 R-020）。
- 实质：R-008~R-019 整段缺失，编号体系崩了。

**27. 发布指南教人发布不存在的包**
- 涉及：`release-guide.md` §2/§3 vs `quick-start.md` §17、`user-guide.md` §21。
- 实质：release-guide 对"无代码"版本列发布检查清单、写 `kairos` 命令，而用户文档自承 CLI 虚构。

**28. `KAIROS_LITE_MODE` 幽灵参数**
- 涉及：`configuration.md` §2（称 deployment 定义）vs `deployment.md`（无此参数）。
- 实质：配置索引导向一个部署文档里不存在的参数，断链。

**29. APScheduler / Litestar 版本范围不存在或已过时**
- 涉及：`technology-stack.md` §26（Litestar 2.0–2.4，实际 2.10+）、§28（APScheduler 3.10–3.12，无 3.11/3.12）。
- 实质：版本兼容范围编造/过时，依赖声明不可信。

---

## 第三部分：最该立刻修的（按优先级）

1. **先把"有没有代码"这件事统一说清楚**（跨 #1）。在 README、claim-matrix、feature-list、implementation-map 顶部加一句一致的状态声明，并让 implementation-map 明确标注"路径为规划目标，非现有代码"。否则整本文档集可信度为零。
2. **修 R-01/R-02 端点映射**（跨 #4）。这是会直接进代码的 bug——需求基线与操作目录/接口规格对"语义检索""路径检索"的端点定义相反。统一到 `POST /v1/memories/search`（语义）、`GET /v1/path`（路径）、`GET /v1/memories?q=`（文本）。
3. **修 SQLite 路径**（跨 #8）。deployment 的 `/data/kairos.db` 与 reliability/runbook 的 `~/.kairos/kairos.db` 必须统一，否则备份抓错文件。
4. **统一 S-01 返回码**（跨 #5）。401 还是 403，全安全文档对齐。
5. **定 Web 框架**（跨 #7）。Litestar 还是 FastAPI，技术选型/setup/实现映射三处必须一致。
6. **补部署回滚 + 钉镜像版本**（跨 #10）。
7. **数字对账**（跨 #2/#3/#11/#12）。feature-list 101→实 100、operation-catalog 52→53/README 50、traceability 18 vs 11、README 100≠89。选一个事实源，全改。
8. **P6 别再叫"铁律"**（跨 #9）。要么补强制机制让它真≤30%，要么把文档里的"铁律/全局闸门"改成"v1.0 已知偏离"，别两头糊弄。
9. **修数据模型硬伤**（B-6）：`lma_urn` 笔误、`entities.id` BIGINT vs 社区 UUID[]、`usage_events.timestamp` 字段名、`embedding` 无 NOT NULL、审计链无顺序列。
10. **治理编号体系重洗**（跨 #25/#26）：D-201~D-211 碰撞、R-008~R-019 断裂，必须重排。

---

## 附：已回读核实的事实清单（供复核）

- feature-list 扩展表实算 57 行（非 58），核心 43 + 57 = **100**（非 101）；"+5 写入"重复计数 W-09="冲突合并"。
- operation-catalog ENC 7 + RET 15 + STR 31 = **53**（自称 52）；§105 称 feature-list "80 项功能"。
- README §110：27+62+11 = **100 ≠ 89**；§68 链接 `governance/release-process.md` 实际为 `release-guide.md`。
- requirements-baseline §161–162：R-01→`GET /v1/memories?path=`，R-02→`GET /v1/memories?q=`；operation-catalog §42–44：语义=`POST /v1/memories/search`，文本=`?q=`，路径=`GET /v1/path`。
- security-spec §29：运行时缺 Key → 401；coding-conventions §86 / integration-design §76 / error-reference：红线违反 → 403。
- deployment §59 `sqlite:///data/kairos.db`；reliability §29 `~/.kairos/kairos.db`；runbook §59 `~/.kairos/kairos.db`。
- cognitive-architecture-gap G-07：P6 压缩比 33%/43% 超 30% 上限，标"受控偏离"。
- technology-stack §26 Litestar 2.0–2.4（过时）、§28 APScheduler 3.10–3.12（不存在）。
- implementation-map §76 rl_optimizer.py "Cosine LR + ε-greedy + RCW + KPop + EMA"；§143"约 80 个组件"（实约 63）。
- traceability-map §16 债务 11+7=18，§118 债务 11（含 1 闭环）。
- claim-matrix 确有 C-01…C-37 共 37 行（"37 声明"无误）；✅ 清单不含 C-11，C-11 仅在 ⚠️ 组（此前代理误报已纠正）。

> 注：本审查严格排除 `reviews/` 目录。项目 `reviews/` 下已存在一份 `comprehensive-audit-report.md`（Linus 风格·主审终稿），本次未读取其内容，仅按指令排除。
