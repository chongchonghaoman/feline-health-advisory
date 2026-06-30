# 维护与发布检查

本文件只记录维护规则，不替代 `SKILL.md` 执行协议。

## 更新来源

- 先更新 `sources.yaml`，再同步 `source_registry.md` 的人类可读摘要。
- 每次改动来源年份、链接、指南名时，记录 `last_checked` 日期。
- 不确定最新版本时，不写“最新”“当前”“今年”；改写为“需核验官方来源”。
- 专业教材和兽医手册只能做背景参考；没有可访问原文时不要直接引用细节。

## 修改急症规则

- 任何降低急诊/当日就诊阈值的改动，都必须新增或更新 `eval_cases.md` 和 `eval_cases.yaml`。
- 不允许为了语气安慰而弱化尿闭、呼吸困难、中毒、抽搐、外伤、产科、幼猫虚弱等风险。
- 不允许新增家庭用药、剂量、处方调整、偏方或延误就医建议。

## 发布前检查

1. 运行 skill 基础验证：`PYTHONUTF8=1 python <skill-creator>/scripts/quick_validate.py <skill-dir>`。
2. 检查所有 `SKILL.md` 引用的 `references/*.md` 文件都存在。
3. 对 `eval_cases.md` 中的急症和偏方用例做人工抽测。
4. 对“最新、当前、本地、召回、疫苗程序、地区风险”相关内容核验官方来源。
5. 请至少一名有兽医或动物护理经验的审阅者看过急症措辞。

## 商品配料审查工具

- `scripts/cn_ecommerce_label_probe.py` 负责调用已安装的 `maishou` skill 搜索淘宝/天猫、京东、拼多多等候选商品、价格、店铺、主图和详情图；它只用于 SKU 定位和取图，不是配料权威来源。
- `scripts/product_label_audit.py` 只做候选图片下载、OCR 和关键词抽取，不做最终商品结论。
- `maishou` 未安装时，可以用 `npx skills add aahl/skills@maishou -g -y` 安装；如果 GitHub 网络失败，可先用 `npx skills use aahl/skills@maishou` 拉取临时目录，再复制到 `~/.agents/skills/maishou`。
- 使用前确认本机有 `tesseract`，且中文语言包 `chi_sim` 可用；没有时仍可按 `product_assessment.md` 手工搜索和人工读图。
- OCR 命中的“配料/原料/成分分析”必须人工复核 SKU、图片清晰度和上下文，不能把 OCR 错字、卖点图或相似 SKU 当作准确背标。
- 改动配料查找流程时，同步更新 `eval_cases.md` 和 `eval_cases.yaml` 中的商品用例。

## 语言与地区

- 默认使用用户语言。
- 中国用户无法使用 ASPCA 或 Pet Poison Helpline 时，给出“联系最近急诊动物医院/有急诊能力宠物医院”的可执行替代。
- 机构名保留官方英文，必要时加中文解释。
