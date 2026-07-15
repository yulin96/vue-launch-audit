# Vue Launch Audit Skill

这个 skill 用来帮助 Codex 在 Vue 项目发布前做检查，包括使用 Vite 的 Vue 项目。重点不是代码风格，而是找会影响上线的真实问题：页面进不去、关键流程失败、请求或跳转异常、错误提示误导用户、品牌或产品名称写错等。

## 适合什么时候用

- 发布前检查 Vue、使用 Vite 的 Vue 项目、移动 H5、活动页、轻量业务页。
- 用户只说“检查一下”“上线前看一下”“发布前检查”“看看这个 H5 有没有风险”这类话时。
- 排查用户流程是否能正常完成，比如进入页面、提交表单、分享、上传、支付、确认结果等。
- 检查路由、请求、状态之间是否有隐藏问题。
- 检查生产环境相关风险，比如环境变量、构建脚本、第三方 SDK、统计埋点、分享配置。
- 检查页面文案里的品牌名、产品名、大小写和明显拼写错误。

## 不适合什么时候用

- 只做普通代码格式整理。
- 只想优化组件结构但不关心上线风险。
- 非 Vue 项目的完整发布审查，包括使用 Vite 但不是 Vue 的项目。

## 使用方式

在需要检查的 Vue 项目里，让 Codex 使用这个 skill：

```text
使用 $vue-launch-audit 帮我检查这个项目发布前有没有风险。
```

如果只是想检查文案里的固定错误词，可以直接运行内置脚本：

PowerShell：

```powershell
$skillDir = "<当前 SKILL.md 所在目录的绝对路径>"
python "$skillDir/scripts/scan_terms.py" `
  --root . `
  --rules "$skillDir/references/term-rules.json"
```

Bash：

```bash
skill_dir="<当前 SKILL.md 所在目录的绝对路径>"
python "$skill_dir/scripts/scan_terms.py" \
  --root . \
  --rules "$skill_dir/references/term-rules.json"
```

也可以临时追加一组词：

```bash
skill_dir="<当前 SKILL.md 所在目录的绝对路径>"
python "$skill_dir/scripts/scan_terms.py" \
  --root . \
  --rules "$skill_dir/references/term-rules.json" \
  --pair CorrectName=WrongName
```

默认规则只保留高置信度错词。如果项目采用内置品牌名、术语和标点风格，可以额外追加 `--rules "$skill_dir/references/term-style-rules.json"`；不确认项目规范时不要加载这组风格规则。

如果要先扫一遍常见的状态和异步风险，例如新接口数据合并到旧对象、空 `catch`、锁没有恢复、手写 `Promise` 分支没闭合、toast 参数形态可疑、动态脚本加载、watcher 反复触发请求或跳转，可以运行：

```powershell
$skillDir = "<当前 SKILL.md 所在目录的绝对路径>"
python "$skillDir/scripts/scan_vue_state_risks.py" --root .
```

```bash
skill_dir="<当前 SKILL.md 所在目录的绝对路径>"
python "$skill_dir/scripts/scan_vue_state_risks.py" --root .
```

这个脚本只负责找线索，不能直接等同于 bug。`REVIEW_FIRST` 和 `LEAD` 只表示检查顺序，不是真实严重度。命中的地方需要结合页面流程确认，尤其是对象合并、锁、toast、动态脚本和 storage 这类可能有正常用法的代码形态。它发现线索时会返回退出码 `1`，这表示“需要检查”，不是脚本运行失败。

## 工作方式

这个 skill 会引导 Codex 先确定完成标准，再检查项目结构、构建脚本、入口、路由、关键页面、请求封装、状态管理和生产配置。检查时优先看真实用户会遇到的问题，而不是把普通优化建议包装成发布风险。默认只检查构建脚本，不执行完整打包，除非用户明确要求。

这个 skill 的定位是检查和定位问题，不默认改代码。即使用户提到修复，也应该先输出问题原因、影响范围和建议改法；只有用户明确要求实现时，才进入代码修改。

## 文件作用

| 文件 | 作用 |
| --- | --- |
| `SKILL.md` | skill 的主说明文件。它告诉 Codex 什么时候触发这个 skill，以及发布检查应该按什么流程做、优先看什么、最后怎么汇报。 |
| `agents/openai.yaml` | 给界面展示用的简短信息，包括显示名称、简短描述和默认提示语。 |
| `references/review-checklist.md` | 更完整的发布检查清单。当项目比较复杂，或者需要扩大检查范围时，Codex 可以打开这份清单补充检查点。 |
| `references/term-rules.json` | 默认文案规则，只维护跨项目适用的高置信度错词。 |
| `references/term-style-rules.json` | 可选风格规则，只有确认项目采用对应品牌、术语、标点和空格规范时才加载。 |
| `scripts/scan_terms.py` | 文案扫描脚本。它会遍历项目里的常见文本文件，找出规则里列出的错误写法，并输出文件位置和建议改成什么。 |
| `scripts/scan_vue_state_risks.py` | 状态和异步风险扫描脚本。它会找对象合并更新、字段级更新、空错误处理、锁、watcher 和路由跳转等需要人工确认的风险线索。 |
| `.gitignore` | 忽略临时文件，例如 Python 缓存、系统缩略图等，避免它们被提交。 |
| `README.md` | 给人看的说明文档，也就是当前文件。用于快速了解这个 skill 是做什么的、怎么用、每个文件有什么作用。 |

## 维护建议

- 如果发现跨项目都明确错误的错词，优先加到 `references/term-rules.json`；存在产品或地区差异的写法放到可选风格规则或项目自己的规则文件。
- 如果只是某个项目的品牌名或产品名，优先运行脚本时用 `--pair Correct=Wrong` 临时传入。
- 如果发布检查经验变多，但不是每次都必须读，放到 `references/review-checklist.md`。
- 如果是每次使用都必须遵守的流程或汇报规则，放到 `SKILL.md`。
- 改完 `scripts/scan_terms.py` 后，至少用一组规则实际跑一次，确认输出和退出码正常。
- 改完 `scripts/scan_vue_state_risks.py` 后，至少在一个小样例或真实 Vue 项目里跑一次，确认它能输出风险线索且不会扫描 `node_modules`、`dist` 等目录。
