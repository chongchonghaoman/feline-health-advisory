# 一名合格且专业的铲屎官.skill

> 一个猫咪健康与行为分诊 skill：先识别急症，再补齐病史，最后给出安全、可执行的下一步。

英文代号：**Feline Health Advisory**  
内部调用名：`$feline-health-advisory`

很多猫主问 AI 时，真正需要的不是“像兽医一样背知识”，而是先别错过危险信号：

- 公猫反复蹲猫砂盆，每次只有几滴尿，是不是“上火”？
- 猫舔了百合叶子，现在看着还好，要不要观察？
- 老猫突然喝水多、变瘦、半夜叫，是不是年纪大了？
- 猫吐了几次，能不能先喂蒙脱石散？
- 小奶猫体冷、不吃奶，要不要针管灌奶？

这个 Skill 的目标是让 AI 在回答猫咪健康、行为、护理、疫苗、营养、猫砂盆、多猫冲突等问题时，优先做**安全分诊**，而不是直接给家庭治疗方案。

## 它解决什么问题

普通宠物问答最容易出问题的地方，不是讲得不够多，而是顺序错了。

这个 Skill 强制 AI 按下面的顺序回答：

1. **先看急症红旗**  
   尿闭、呼吸困难、中毒、抽搐、外伤、难产、幼猫虚弱、老年急变等，先建议急诊或当日就医。

2. **再问最少必要病史**  
   年龄、性别/绝育、症状开始时间、吃喝、排尿排便、精神状态、是否接触毒物或人药。

3. **再给权威来源下的建议**  
   参考 WSAVA、AAHA/AAFP、AAFP/ISFM、Cornell Feline Health Center、Merck/MSD Veterinary Manual、ASPCA Poison Control 等来源。

4. **最后给清晰下一步**  
   什么时候观察，什么时候预约，什么时候急诊，去医院前该带什么资料。

## 适合谁

- 想给 AI 加上猫咪健康分诊能力的用户
- 想做宠物健康问答、猫咪护理助手、猫主教育 bot 的开发者
- 希望减少“偏方、人药、延误急诊”风险的 AI 工作流维护者
- 想把猫咪行为问题和潜在医学原因分开处理的铲屎官

## 不做什么

这个项目刻意不做远程诊断，也不做远程处方。

- 不给具体药物剂量
- 不建议自行使用人药
- 不替代兽医诊断
- 不把“看着还好”当成中毒或急症的安全保证
- 不因为预算、距离、时间不便而降低急症等级

这不是不专业，而是边界感。猫的用药安全窗很窄，剂量需要诊断、体重、年龄、脱水状态、肝肾功能和监测条件一起判断。

## 快速安装

把这个仓库放到你的 Codex skills 目录中：

```bash
git clone https://github.com/chongchonghaoman/feline-health-advisory.git ~/.codex/skills/feline-health-advisory
```

Windows 示例：

```powershell
git clone https://github.com/chongchonghaoman/feline-health-advisory.git "$env:USERPROFILE\.codex\skills\feline-health-advisory"
```

然后在对话里显式调用：

```text
Use $feline-health-advisory：我家猫今天一直蹲猫砂盆，但尿很少。
```

## 示例问题

```text
我家公猫一晚上进猫砂盆十几次，每次就几滴，还一直舔下面，是不是上火？
```

期望行为：识别尿道阻塞风险，建议立即急诊，不建议等到明天或喂偏方。

```text
猫舔了一下百合叶子，现在吃喝正常，需要观察吗？
```

期望行为：说明百合暴露即使暂时无症状也可能紧急，建议联系急诊兽医或毒物咨询。

```text
猫突然尿床，是不是报复我出差？
```

期望行为：先排除泌尿疼痛、尿频尿血等医学原因，再讨论猫砂盆、压力和环境。

## 项目结构

```text
feline-health-advisory/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── references/
    ├── triage_red_flags.md
    ├── intake_questions.md
    ├── scenario_routes.md
    ├── source_registry.md
    ├── sources.yaml
    ├── eval_cases.md
    ├── eval_cases.yaml
    ├── maintenance.md
    └── authoritative_sources.md
```

核心文件：

- `SKILL.md`：执行协议，定义触发、分诊顺序、禁止项和语言策略。
- `triage_red_flags.md`：急症红旗，包括尿闭、中毒、呼吸、产科、幼猫、老年猫急变。
- `intake_questions.md`：最小病史采集模板。
- `scenario_routes.md`：疾病、行为、猫砂盆、疫苗、营养、幼猫、老年猫、中毒等主题路由。
- `sources.yaml`：结构化来源登记。
- `eval_cases.yaml`：对抗性回归测试用例。

## 设计原则

### Emergency first

急症回答先给行动，再解释背景。不要让引用、科普或长篇分析挡在“现在去急诊”前面。

### Triage, not diagnosis

回答风险等级和下一步，不把 AI 变成远程兽医。

### Owner-safe language

用猫主听得懂、做得到的语言说清楚：该观察什么、带什么去医院、哪些事不要做。

### Source-aware

涉及“最新”“当前”“本地”“疫苗程序”“召回”“地区风险”时，需要核验官方来源。无法核验时，必须说明不确定。

## 维护

发布或修改前至少检查：

```bash
python <skill-creator>/scripts/quick_validate.py <path-to-feline-health-advisory>
```

并人工抽测 `references/eval_cases.md` / `references/eval_cases.yaml` 中的高风险用例。

维护规则见 [`references/maintenance.md`](references/maintenance.md)。

## 免责声明

本项目用于猫咪健康与行为问题的 AI 分诊和主人教育，不能替代兽医诊断、检查或治疗。急症、疑似中毒、无法排尿、呼吸异常、严重外伤、抽搐、幼猫虚弱、难产等情况，请立即联系兽医或急诊动物医院。
