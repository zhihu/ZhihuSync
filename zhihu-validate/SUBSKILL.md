---
name: zhihu-validate
description: Convert ./.zhihu-publish-output/draft/latest-draft.md into Zhihu-ready structured JSON. Use when validating or converting draft content for Zhihu articles, questions, or pins before preview or publish.
---

# Zhihu Validate

读取 `./.zhihu-publish-output/draft/latest-draft.md`，将草稿内容转换为知乎适配的结构化结果，并写入本地产物目录。本 skill 只负责转换与配置生成，不负责整理原始草稿、浏览器预览或发布。

## 使用时机

当根 `zhihu-publisher` 已生成 draft，或用户要求将已有 draft 转换为供预览 / 发布使用的知乎结构化数据时使用本 skill。

支持的内容形态：

- `article`：文章
- `question`：提问
- `pin`：想法

## 输入路径

默认读取执行 Skill 时当前工作目录下的草稿文件：

```text
./.zhihu-publish-output/draft/latest-draft.md
```

读取规则：

1. 该文件必须存在；不存在时停止并要求先执行根 `zhihu-publisher` 的 draft 阶段。
2. 用户显式指定其他输入路径时，以用户指定路径为准。
3. 不直接从对话上下文重新整理发布内容；对话中的新增修改、以及用户对预览结果的修正要求，都应先由根 `zhihu-publisher` 结合用户需求和本文参考文件更新 draft，再重新 validate。

## 输出路径

默认写入执行 Skill 时的当前工作目录，**不写入用户主目录**：

```text
./.zhihu-publish-output/validate/
├── .candidate.json                 # 生成中的临时候选；不得作为下游输入
├── latest.json                      # 固定读取入口，每次覆盖
└── YYYY-MM-DD-HHmm-result.json      # 历史留存，每次新增
```

写入规则：

1. 目录不存在时先创建。
2. 模型生成的完整结果先写入 `.candidate.json`；不得直接写入时间戳结果或 `latest.json`。
3. 必须使用 `scripts/finalize_validate_json.py` 提交候选。脚本从候选所在目录生成时间戳结果和 `latest.json`，成功后删除候选。
4. 脚本失败时保留候选和已有 `latest.json`，不得进入 preview；用户显式指定输出目录时，将 `.candidate.json` 写入该目录再运行脚本。

## 工作流程

0. 检查上传类型。
   - 本流程只允许上传图片。发现需要上传或随内容发布的视频时，只回复：`当前知乎发布流程暂不支持视频，请移除视频后重新提交。` 然后立即停止；不得生成或修改 validate 产物，也不得调用任何上传能力。
   - `zhihu-mediacloud-uploader` 只能用于上传图片，严禁用它或其他上传能力上传视频及其他非图片。
1. 确认内容形态。
   - 优先使用 draft 中记录的内容形态。
   - draft 未记录内容形态时，先根据草稿内容推断并向用户确认；确认后应更新 draft，再继续转换。
2. 读取 `./.zhihu-publish-output/draft/latest-draft.md`，按 `reference/conversion.md` 的「转换前长度检查与用户决策」检查标题和正文。
   - 在任何内容转换或媒体上传前执行长度预检。
   - 发现超出当前内容形态的上限时，报告实际长度与上限，提供对应选项并停止，等待用户明确选择；不得生成时间戳结果，也不得覆盖已有 `latest.json`。
   - 用户的选择和由此产生的精简内容、内容形态变更或拆分结果必须先由根 `zhihu-publisher` 写回 draft，再重新执行本步骤。
3. 按 `reference/conversion.md` 转换标题、正文和正文相关结构。
   - 严格执行 `reference/conversion.md` 的「内容保真与修改授权」规则。只做知乎发布所需的结构和格式适配，不得把转换、发布或预览请求视为润色授权。
   - 文章、提问生成 `title` 与 `body`。
   - 想法生成 `title`（可选）、`body`，以及可能存在的 `media`、`linkCard`。
   - 想法只转换 draft 中由用户明确提供或确认的话题；用户未提供或确认时，不得自动生成话题标签。
   - 代码块语言必须使用 `reference/code-languages.md` 中的语言 ID。
   - 本地图片或需要转存的公开图片 URL，先按根 Skill 的依赖说明读取 `../reference/zhihu-mediacloud-uploader.md`，确保 `zhihu-mediacloud-uploader` skill 已安装并可加载。
   - 安装或确认可加载后，加载并执行 `zhihu-mediacloud-uploader` 的 `SKILL.md`；上传参数、凭证、MCP、错误处理和响应字段只参考该依赖 skill 的文档。
   - 上传失败或依赖 skill 要求重启 Agent 时停止转换，不得将本地路径写入发布内容，也不得编造上传结果。
   - 转换完成后，按 `reference/conversion.md` 的 HTML 安全约束检查 `body`；发现未允许的危险标签、属性或 URL 时立即停止，不生成时间戳结果，也不得覆盖已有 `latest.json`。
   - 不得原样透传用户输入中的原始 HTML，也不得为了通过检查而静默删除危险内容后继续转换；不危险但不受支持的格式按转换规则降级为文本。
4. 按 `reference/config.md` 生成 `config`。
   - 配置与正文分离。
   - 文章和提问的话题只使用已存在且可发布的话题，写入 `config.topics`，不得创建新话题，也不得写入正文 HTML。
   - 想法中经用户明确提供或确认的话题属于正文内容，写入 `body`，不写入 `config.topics`；发布想法时按话题名检查是否存在，存在则复用，不存在则允许创建。用户未提供或确认话题时，不主动生成。
   - 不把目录、创作声明、评论权限、圈子等配置说明写进正文 HTML。
5. 将完整结果写入本地产物目录的 `.candidate.json`，再通过确定性脚本提交（见上文「输出路径」）。
   - 候选必须只包含完整结果对象，不要输出 Markdown 代码围栏、说明文字或第二个 JSON 值。
   - 不要预先手工转义 `title` 或 `body`；候选中的字符串必须按 JSON 语法表示，最终文件由脚本统一重新序列化。
   - 使用 Python 3 和解析得到的 skill 目录绝对路径调用脚本；没有 Python 3 时停止，不得绕过门禁：

     ```text
     <python3> <skill目录>/zhihu-validate/scripts/finalize_validate_json.py \
       ./.zhihu-publish-output/validate/.candidate.json
     ```

   - JSON 解析失败时，根据脚本给出的行列只修复语法、字符串转义或候选外多余文本，不得改变内容语义；每次修复后重新运行脚本，最多修复两次。
   - 其他错误回到本流程对应步骤修正。脚本最终仍失败时停止，不覆盖已有 `latest.json`，也不进入 preview。

## 输出结构

结构化结果始终使用统一结构：

```json
{
  "type": "article | question | pin",
  "title": "",
  "body": "",
  "media": [],
  "linkCard": null,
  "config": {}
}
```

字段说明：

- `type`：内容形态。
- `title`：转换后的标题，始终为字符串；无标题想法固定使用空字符串，不得省略该字段。
- `body`：知乎发布适配 HTML，始终为字符串，不是浏览器预览 HTML；允许想法正文为空字符串，但正文、媒体、链接卡片至少有一项有效内容。
- `body` 在 JSON 文件中会按 JSON 语法转义；消费端读取 JSON 后，必须直接使用反序列化得到的 HTML 字符串，不得再次 `JSON.stringify(body)` 或把带字面量 `\"` 的文本交给编辑器。
- `media`：独立媒体区，主要用于想法图片；没有独立媒体时使用空数组。
- `linkCard`：独立链接卡片，主要用于想法；没有独立链接卡片时使用 `null`。
- `config`：发布配置，按 `reference/config.md` 生成。

## 边界

- 不生成本地浏览器预览 HTML；预览由 `zhihu-preview` 读取 `./.zhihu-publish-output/validate/latest.json` 后完成。
- 不整理原始发布草稿；草稿由根 `zhihu-publisher` 写入 `./.zhihu-publish-output/draft/latest-draft.md`。
- 不发布内容。
- 未经用户对具体动作和字段的明确允许，不得删减、精简、扩写、重排、合并、拆分或语义改写用户提供的内容。
- 用户未提供或确认话题时，不得为想法自动生成话题。
- 不得在标题或正文超出上限时自行截断、精简、切换内容形态或拆分；必须先等待用户选择，并在 draft 更新后重新开始转换。
- 不为了预览改写 `title`、`body`、`media`、`linkCard` 或 `config`。
- 不得绕过 `scripts/finalize_validate_json.py` 直接创建或覆盖时间戳结果与 `latest.json`；脚本失败时不得进入 preview。
- 不输出未支持的内容形态；遇到不支持的能力时，应说明无法转换或降级为已支持格式。
- 除非用户显式指定其他路径，产物应写入当前工作目录下的 `./.zhihu-publish-output/validate/`。

## 资源

- `scripts/finalize_validate_json.py`：解析、检查、规范化并安全提交 validate 候选 JSON；生成最终文件时必须使用。
- `reference/conversion.md`：标题、正文、富文本、想法媒体和链接卡片转换规则。
- `reference/config.md`：发布配置生成规则。
- `reference/code-languages.md`：代码块语言 ID 列表。
