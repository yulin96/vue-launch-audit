# Vue Launch Audit Skill

这个 skill 用来帮助 Codex 在 Vue / Vite 项目发布前做检查，重点不是代码风格，而是找会影响上线的真实问题：页面进不去、关键流程失败、请求或跳转异常、错误提示误导用户、品牌或产品名称写错等。

## 适合什么时候用

- 发布前检查 Vue、Vite、移动 H5、活动页、轻量业务页。
- 排查用户流程是否能正常完成，比如进入页面、提交表单、分享、上传、支付、确认结果等。
- 检查路由、请求、状态之间是否有隐藏问题。
- 检查生产环境相关风险，比如环境变量、构建脚本、第三方 SDK、统计埋点、分享配置。
- 检查页面文案里的品牌名、产品名、大小写和明显拼写错误。

## 不适合什么时候用

- 只做普通代码格式整理。
- 只想优化组件结构但不关心上线风险。
- 非 Vue / Vite 项目的完整发布审查。

## 使用方式

在需要检查的 Vue 项目里，让 Codex 使用这个 skill：

```text
使用 $vue-launch-audit 帮我检查这个项目发布前有没有风险。
```

如果只是想检查文案里的固定错误词，可以直接运行内置脚本：

```bash
python "$CODEX_HOME/skills/vue-launch-audit/scripts/scan_terms.py" \
  --root . \
  --rules "$CODEX_HOME/skills/vue-launch-audit/references/term-rules.json"
```

也可以临时追加一组词：

```bash
python "$CODEX_HOME/skills/vue-launch-audit/scripts/scan_terms.py" \
  --root . \
  --rules "$CODEX_HOME/skills/vue-launch-audit/references/term-rules.json" \
  --pair CorrectName=WrongName
```

## 工作方式

这个 skill 会引导 Codex 先确定完成标准，再检查项目结构、构建脚本、入口、路由、关键页面、请求封装、状态管理和生产配置。检查时优先看真实用户会遇到的问题，而不是把普通优化建议包装成发布风险。

如果用户只是要求审查，输出会按风险级别汇报，并说明验证情况。如果用户要求修复，Codex 会先找原因，再改最影响上线的问题，并重新验证。

## 文件作用

| 文件 | 作用 |
| --- | --- |
| `SKILL.md` | skill 的主说明文件。它告诉 Codex 什么时候触发这个 skill，以及发布检查应该按什么流程做、优先看什么、最后怎么汇报。 |
| `agents/openai.yaml` | 给界面展示用的简短信息，包括显示名称、简短描述和默认提示语。 |
| `references/review-checklist.md` | 更完整的发布检查清单。当项目比较复杂，或者需要扩大检查范围时，Codex 可以打开这份清单补充检查点。 |
| `references/term-rules.json` | 文案检查规则。里面维护“正确写法”和“常见错误写法”，供扫描脚本使用。 |
| `scripts/scan_terms.py` | 文案扫描脚本。它会遍历项目里的常见文本文件，找出规则里列出的错误写法，并输出文件位置和建议改成什么。 |
| `.gitignore` | 忽略临时文件，例如 Python 缓存、系统缩略图等，避免它们被提交。 |
| `README.md` | 给人看的说明文档，也就是当前文件。用于快速了解这个 skill 是做什么的、怎么用、每个文件有什么作用。 |

## 维护建议

- 如果发现新的常见错词，优先加到 `references/term-rules.json`。
- 如果发布检查经验变多，但不是每次都必须读，放到 `references/review-checklist.md`。
- 如果是每次使用都必须遵守的流程或汇报规则，放到 `SKILL.md`。
- 改完 `scripts/scan_terms.py` 后，至少用一组规则实际跑一次，确认输出和退出码正常。
