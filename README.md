# 一名合格且专业的铲屎官.skill

猫没有说明书，但铲屎官可以有一本不玄学的百科全书。

这是一个给 AI 用的养猫知识 skill。它面向真实生活里的养猫问题：日常照护、行为、环境、健康风险、营养、幼猫老年猫、多猫家庭，以及猫食品商品审查。它的目标不是让 AI 装成远程兽医，也不是把每只猫塞进同一个模板，而是尽量把回答拉回专业猫科资料里的“标准线”，再结合你家猫的实际情况给出能执行的建议。

- 内部调用名：`feline-health-advisory`
- 展示名：`一名合格且专业的铲屎官.skill`

## 它是什么

你可以把它理解成：

- 一本铲屎官养猫百科全书。
- 一个“先给标准答案，再看个体差异”的回答框架。
- 一个遇到危险信号会先踩刹车的安全员。
- 一个能看配料、背标、适用生命阶段的猫食品审查助理。
- 一个负责提醒人类：猫是猫，不是会动的情绪盲盒。

它追求的是“尽量标准化”，不是“假装绝对正确”。猫不是 Excel，生活也不是实验室，但大多数养猫问题都不该每次从零开始摇骰子。

## 为什么做它

养猫信息太容易变成玄学接力。

同一个问题，可能有人说要饿一顿，有人说要打一顿，有人说“我家这么做没事”，还有人上来就推荐神秘小药片。听起来都很有生活气息，问题是猫的身体不一定同意。

这个 skill 的思路更朴素：

1. 先看有没有急症风险。
2. 再找猫科医学、行为、福利和营养资料里的通用共识。
3. 然后问清楚这只猫的年龄、症状、环境、饮食和变化。
4. 最后给出铲屎官今天就能做的步骤。

也就是说，少一点“祖传感觉”，多一点“猫科基本法”。

## 可以问什么

几乎所有真实养猫问题都可以问。它不是只做急症分诊，也不是只查猫粮配料。

| 问题类型 | 例子 |
|---|---|
| 日常养护 | 剪指甲、洗澡、梳毛、抱猫、出门、笼养、夜里跑酷 |
| 行为与互动 | 咬手、抓沙发、乱尿、躲人、打架、过度舔毛、不让摸 |
| 环境与福利 | 猫砂盆摆放、多猫资源、搬家适应、玩具、抓板、休息区 |
| 健康风险 | 呕吐、腹泻、拒食、尿少、呼吸异常、抽搐、外伤、中毒 |
| 生命阶段 | 幼猫喂养、疫苗驱虫、绝育、老年猫变化、慢病猫照护 |
| 营养与喂食 | 湿粮干粮、换粮、挑食、猫条、主食罐、餐盒、餐包 |
| 商品审查 | 某款产品能不能吃、是否适合幼猫、配料表是否可信、安全性如何 |

## 它怎么回答

默认回答顺序是：

1. **先排危险**：有没有需要立刻联系兽医或急诊动物医院的红旗。
2. **给标准线**：相关指南、机构或可靠资料一般怎么处理这个问题。
3. **看你家这只猫**：年龄、体重、性别、绝育、病史、精神、吃喝、尿便、环境变化。
4. **给行动方案**：现在做什么、别做什么、观察什么、拍什么、记录什么。
5. **设升级阈值**：什么情况不能继续观察，必须就医或复诊。

它会尽量把“我觉得”降到最低，把“依据是什么”说清楚。没有来源支撑的经验判断，也要标出来，不硬装权威。

## 一些标准线

这些是 skill 的底层脾气，基本不会让步：

- 不把猫咬人、乱尿、躲藏、抓家具直接解释成报复、欠收拾或故意气人。
- 不建议打猫、弹鼻子、喷壶、按头、关禁闭、强迫抱摸、用手脚逗猫。
- 不给远程诊断，不给药物剂量，不教人药、偏方、自行催吐或灌药。
- 不因为“旗舰店”“销量高”“好价”“猫爱吃”就说某个食品安全健康。
- 不把商品标题当配料表，不把达人文案当背标。
- 不把急症说成“再观察观察”。猫不会发邮件通知你它快撑不住了。

专业不是把人吓成雕像，也不是把话说得像说明书泡水。专业是把风险、依据和下一步讲清楚。

## 典型问题会怎么处理

### 猫咬手，要不要打？

不建议打。

标准回答会先区分：玩耍性咬人、过度刺激、害怕防御、疼痛、压力或资源不足。然后建议停止用手脚逗猫，改用逗猫棒和可咬玩具；看到尾巴抽动、耳朵后压、皮肤抽动、转头盯手等信号就结束互动。如果是突然开始咬人，或伴随躲藏、食欲下降、不让摸，要考虑疼痛或疾病。

### 猫乱尿，是不是报复？

先别开庭。

标准回答会先排尿频、尿少、尿血、疼痛、舔尿道口等医学风险。非急症时，再看猫砂盆数量、位置、大小、清洁频率、猫砂材质、多猫冲突和压力源。猫很多时候不是在“报复”，它是在用身体和环境问题发消息，只是格式很不友好。

### 两只猫打架怎么办？

不建议吼、打、硬关在一起“让它们熟”。

标准回答会看资源是否足够分散，猫砂盆、食盆、水碗、休息点、通道和高处是否被垄断；必要时重新隔离，做气味交换、门缝喂食、逐步可视接触和短时正向互动。

### 幼猫不吃干粮怎么办？

先看精神、体重、呕吐腹泻、脱水和拒食时长。没有红旗时，再谈湿粮、泡软、少量多餐、稳定主食和逐步过渡。幼猫不是小型垃圾处理器，爱吃不等于适合长期当饭吃。

### 某款主食罐好价能不能买？

先锁 SKU 和背标。

价格很重要，但放在最后。真正有用的是配料、添加剂组成、保证分析、适用生命阶段、产品标准、生产或进口信息、批号、召回和口碑风险。猫爱吃只能说明猫爱吃，不自动等于健康。

## 猫食品配料表 SOP

当你问“帮我找准确配料表”时，skill 会按 [`references/ingredient_acquisition.md`](references/ingredient_acquisition.md) 走硬流程：

1. 商品名反搜，拆出品牌、系列、规格、口味、平台商品号和短链。
2. 查官方页、旗舰店页、平台详情图、公开缓存和买家晒图。
3. 国内页面没有背标时，查海外同款或同系列英文页：`ingredients`、`composition`、`analytical constituents`、`guaranteed analysis`。
4. 查条码或 GTIN，但只把它当身份线索，不把条码命中当成配料表。
5. 下载图片、OCR、人工核对原图。
6. 仍然拿不到时，明确向客服索要中文标签或外包装背标照片。

证据等级：

| 等级 | 含义 |
|---|---|
| A | 清晰包装背标，或官方/旗舰店完整标签图 |
| B | 官方页面文字给出配料或保证分析 |
| C | 买家晒图、测评图、平台图能看清配料 |
| D | 只有卖点图、标题、价格、达人文案、相似 SKU |

只有 A/B 级才说“配料已核到”。C 级可以参考但要保留不确定性。D 级不能拿来给猫下饭。

## 主要参考底座

这个 skill 优先参考美国、欧洲和国际猫科医学、行为、福利和营养资料，包括：

| 来源 | 主要用途 |
|---|---|
| AAFP / FelineVMA | 猫科指南、猫友好诊疗、疫苗、老年猫、多猫紧张 |
| ISFM / iCatCare | 猫行为、福利、环境、日常养护、铲屎官教育 |
| AAFP/ISFM Environmental Needs Guidelines | 猫环境需求五支柱、压力、乱尿、抓挠、多猫冲突 |
| Cat Friendly Homes | 面向普通铲屎官的猫友好家庭养护 |
| WSAVA | 疫苗、营养评估、疼痛、福利等全球指南 |
| Cornell Feline Health Center | 猫疾病、营养和健康科普 |
| Merck/MSD Veterinary Manual | 兽医专业背景和疾病机制 |
| UC Davis/Koret Shelter Medicine | 救助、多猫、猫瘟、上呼吸道感染、隔离 |
| ABCD / CAPC / ESCCAP | 猫癣、寄生虫、传染病和人畜共患背景 |

完整来源登记见 [`references/source_registry.md`](references/source_registry.md) 和 [`references/sources.yaml`](references/sources.yaml)。

## 不会安装也能直接用

把下面这段复制给 ChatGPT、Codex 或其他 AI，再填你的问题：

```text
你是一名基于美国、欧洲和国际猫科医学、猫行为、动物福利与营养资料的科学养猫顾问。请像“一名合格且专业的铲屎官百科全书”一样回答我的真实养猫问题。

回答原则：
- 任何问题先筛急症红旗：无法排尿、呼吸困难、疑似中毒、抽搐、严重外伤、幼猫虚弱、难产等，先建议立即联系兽医或急诊动物医院。
- 非急症问题要给标准养护答案，不要只说“看情况”。
- 行为问题不要拟人化成报复、调皮、故意作恶；先考虑正常猫行为、环境资源、压力、疼痛和疾病。
- 不建议打猫、喷壶、关禁闭、强抱强摸、用手脚逗猫。
- 不给药物剂量、人药建议、偏方或自行催吐方案。
- 猫食品商品问题先锁 SKU、找配料表/背标/保证分析/适用生命阶段，再判断能不能吃；价格最后再说。

我的问题：
猫的年龄：
性别/是否绝育：
体重：
问题描述：
从什么时候开始：
精神/吃喝/尿便：
生活环境/多猫情况：
如果是商品，请附商品名、规格、口味、价格、平台、店铺或链接：
```

## 安装

### Codex

macOS / Linux:

```bash
git clone https://github.com/chongchonghaoman/feline-health-advisory.git ~/.codex/skills/feline-health-advisory
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills"
git clone https://github.com/chongchonghaoman/feline-health-advisory.git "$env:USERPROFILE\.codex\skills\feline-health-advisory"
```

### WorkBuddy

macOS / Linux:

```bash
git clone https://github.com/chongchonghaoman/feline-health-advisory.git ~/.workbuddy/skills/feline-health-advisory
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.workbuddy\skills"
git clone https://github.com/chongchonghaoman/feline-health-advisory.git "$env:USERPROFILE\.workbuddy\skills\feline-health-advisory"
```

安装后重启应用，可以这样显式调用：

```text
Use $feline-health-advisory：猫咬我手，是不是要打一下才知道疼？
```

```text
Use $feline-health-advisory：我家猫突然尿床，是不是报复我？
```

```text
Use $feline-health-advisory：这款主食罐 mobi 能不能吃？帮我先找配料表。
```

## 项目结构

```text
feline-health-advisory/
|-- SKILL.md
|-- README.md
|-- CONTRIBUTING.md
|-- agents/
|   `-- openai.yaml
|-- scripts/
|   |-- cn_ecommerce_label_probe.py
|   `-- product_label_audit.py
`-- references/
    |-- triage_red_flags.md
    |-- intake_questions.md
    |-- scenario_routes.md
    |-- product_assessment.md
    |-- ingredient_acquisition.md
    |-- source_registry.md
    |-- sources.yaml
    |-- authoritative_sources.md
    |-- eval_cases.md
    |-- eval_cases.yaml
    `-- maintenance.md
```

核心文件：

- [`SKILL.md`](SKILL.md)：skill 入口和执行协议。
- [`references/scenario_routes.md`](references/scenario_routes.md)：日常养护、行为、营养、疾病、幼猫、老年猫、多猫等主题路由。
- [`references/triage_red_flags.md`](references/triage_red_flags.md)：急症红旗。
- [`references/intake_questions.md`](references/intake_questions.md)：最小病史采集。
- [`references/source_registry.md`](references/source_registry.md)：权威来源摘要。
- [`references/product_assessment.md`](references/product_assessment.md)：猫食品商品审查。
- [`references/ingredient_acquisition.md`](references/ingredient_acquisition.md)：准确配料表获取 SOP。
- [`references/eval_cases.yaml`](references/eval_cases.yaml)：对抗性回归测试。
- [`scripts/cn_ecommerce_label_probe.py`](scripts/cn_ecommerce_label_probe.py)：电商候选商品和详情图探针。
- [`scripts/product_label_audit.py`](scripts/product_label_audit.py)：图片 OCR 和标签线索抽取。

## 维护原则

修改这个 skill 时，优先守住这些底线：

1. 不降低急症红旗等级。
2. 不新增药物剂量、人药建议、偏方建议。
3. 不把打猫、喷壶、关禁闭、强迫互动写成行为建议。
4. 不把“报复”“故意”“欠收拾”当成猫行为解释。
5. 不把平台经验帖、短视频、群聊截图当作权威来源。
6. 不把商品标题、旗舰店、销量、好价当作配料或安全证据。
7. 涉及最新、本地、召回、法规、疫苗程序时，核验官方来源。

可运行 skill 验证：

```bash
python <skill-creator>/scripts/quick_validate.py <path-to-feline-health-advisory>
```

Windows PowerShell 建议启用 UTF-8：

```powershell
$env:PYTHONUTF8='1'
python <skill-creator>\scripts\quick_validate.py <path-to-feline-health-advisory>
```

更多贡献规则见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

## 免责声明

本项目用于猫咪日常养护、行为、福利、营养、健康风险分诊和猫食品商品审查，不能替代兽医诊断、检查或治疗。

如果出现无法排尿、呼吸异常、疑似中毒、抽搐、严重外伤、幼猫虚弱、难产等情况，请立即联系兽医或急诊动物医院。
