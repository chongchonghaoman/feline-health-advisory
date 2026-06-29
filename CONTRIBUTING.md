# Contributing

谢谢你愿意一起把这个 Skill 做得更稳。这个项目的核心目标是减少猫主在高风险场景下被误导、延误或鼓励自行用药。

## 修改原则

- 不降低急症红旗等级。
- 不新增药物剂量、家庭处方、人药建议或偏方建议。
- 不把行为问题默认解释成“报复”“调皮”；突然行为改变要先考虑医学原因。
- 涉及“最新”“当前”“本地”“疫苗程序”“召回”“地区风险”时，必须核验官方来源。
- 专业兽医资料中的剂量、麻醉、手术、催产、急救流程不能改写成家庭操作步骤。

## 提交前检查

1. 更新或新增对应的 `references/eval_cases.md` 和 `references/eval_cases.yaml`。
2. 如修改来源年份、链接、指南名，同步 `references/sources.yaml` 和 `references/source_registry.md`。
3. 运行 skill 验证：

```bash
python <skill-creator>/scripts/quick_validate.py <path-to-feline-health-advisory>
```

4. 人工抽测至少一个急症用例、一个偏方/人药用例、一个行为医学伪装用例。

## 推荐 Issue 类型

- 急症红旗遗漏
- 中文真实表达补充
- 来源更新
- 回归测试用例
- 语言可读性优化

如果你不确定某个建议会不会鼓励延误就医，请按更保守的方向写。
