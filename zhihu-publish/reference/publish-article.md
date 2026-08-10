# Article Publish Spec

当 `./.zhihu-publish-output/validate/latest.json` 中 `type` 为 `article` 时，按本文档把 validate 结果转换为 publish OpenAPI request。

## 前置校验

- `latest.type` 必须为 `article`。
- `latest.title` 必须非空。
- `latest.body` 必须非空。
- 用户必须已经确认 `./.zhihu-publish-output/preview/latest.html`。

校验失败时停止发布；不要从 preview HTML 反向提取正文，也不要补写占位标题或正文。

## validate 字段来源

文章发布只从 validate 结果中读取正文内容字段：

| Request 字段 | validate 来源 | 规则 |
|---|---|---|
| `content.title` | `latest.title` | 必须非空 |
| `content.html` | `latest.body` | 必须非空；直接使用反序列化后的 HTML 字符串 |

不要从 validate 结果中提取或继承文章发布配置。即使 `latest.config` 中存在评论权限、话题、创作声明或目录开关，也必须在发布前重新和用户确认。

## 发布前交互确认

组装请求前，必须向用户确认以下发布参数。用户直接接受默认值时，可以继续发布。

确认时必须把评论权限和创作声明的可选项展示给用户，不能只问“请选择评论权限/创作声明”。评论权限只展示中文描述，不展示内部参数值；创作声明展示时使用本文“creation_statement”章节中的完整选项。默认项也要写清楚。

| 参数 | 默认值 | 处理规则 |
|---|---|---|
| 评论权限 | 所有人可评论 | 用户未指定时内部发送 `all` |
| 话题 `topics` | 不设置 | 需要用户手动粘贴知乎话题链接；询问时必须给出示例 `https://www.zhihu.com/topic/19555547/hot`；未提供时不发送 `topics` |
| 创作声明 `creation_statement` | 没有声明 | 默认不设置该字段；只有用户明确选择声明类型时才发送 |
| `table_of_contents_enabled` | 不创建目录（`false`） | 用户未指定时发送 `false` |

## Request Body

接受默认发布参数时，请求体形如：

```json
{
  "type": "article",
  "confirmed": true,
  "confirm_note": "confirmed by user after local preview",
  "content": {
    "title": "...",
    "html": "<p>...</p>",
    "comment_permission": "all",
    "table_of_contents_enabled": false
  }
}
```

如果用户确认了话题或创作声明，再追加对应字段：

```json
{
  "type": "article",
  "confirmed": true,
  "confirm_note": "confirmed by user after local preview",
  "content": {
    "title": "...",
    "html": "<p>...</p>",
    "comment_permission": "all",
    "table_of_contents_enabled": false,
    "creation_statement": "ai_creation",
    "topics": [
      {
        "topic_id": "",
        "topic_token": "19555547",
        "topic_name": ""
      }
    ]
  }
}
```

## 字段映射

| Request 字段 | 来源 | 规则 |
|---|---|---|
| `type` | 固定 | `article` |
| `confirmed` | 固定 | `true` |
| `confirm_note` | 固定 | `confirmed by user after local preview` |
| `content.title` | `latest.title` | 必须非空 |
| `content.html` | `latest.body` | 必须非空；不要从 preview HTML 中读取 |
| `content.comment_permission` | 用户发布前确认 | 默认 `all` |
| `content.table_of_contents_enabled` | 用户发布前确认 | 默认 `false` |
| `content.creation_statement` | 用户发布前确认 | 默认不发送 |
| `content.topics` | 用户发布前粘贴的话题链接 | 未提供时不发送；最多 3 个 |

不要发送 `images`、`ring`、`linkcard`。

## 评论权限

发布前询问用户评论权限。对用户只展示中文描述，不展示内部参数值，不要写成“任何人都可以评论（all）”；用户不选择时使用默认项“任何人都可以评论”，内部发送 `all`。

| 用户可见选项 | 内部值 |
|---|---|
| 任何人都可以评论 | `all` |
| 不允许评论 | `nobody` |
| 我关注的人能评论 | `followee` |
| 仅显示我筛选后的评论 | `censor` |
| 关注我的人能评论 | `follower` |

如果用户选择或输入的评论权限无法匹配上表任一中文描述，停止发布并要求用户重新选择；不要静默替换为默认值，也不要要求用户输入内部值。

## topics

文章话题可选，最多 3 个。话题必须由用户在发布前手动粘贴知乎话题链接；询问用户是否关联话题时，必须展示具体示例，例如：

```text
https://www.zhihu.com/topic/19555547/hot
```

提取规则：

- 从 `/topic/{topic_token}` 路径段中提取 `{topic_token}`；上例的 `topic_token` 是 `19555547`。
- 支持用户一次粘贴多个链接，按出现顺序去重，最多保留 3 个。
- `topic_id` 不需要用户提供，固定置为空字符串 `""`。
- `topic_name` 只有用户同时提供话题名时才填写；否则使用空字符串。
- 无法从链接中提取 `topic_token` 时，停止发布并要求用户补充正确的话题链接。

每个话题映射为：

```json
{
  "topic_id": "",
  "topic_token": "19555547",
  "topic_name": ""
}
```

## creation_statement

发布前询问用户创作声明，并向用户展示以下可选项(只展示中文含义即可)。创作声明默认不设置字段；只有用户明确选择声明类型时，才发送 `content.creation_statement`：

| 值 | 展示含义 | 发送规则 |
|---|---|---|
| 不设置 | 没有声明（默认） | 不发送 `creation_statement` |
| `spoiler` | 包含剧透 | 发送该值 |
| `medical_advice` | 包含医疗建议 | 发送该值 |
| `fictional_creation` | 虚构创作 | 发送该值 |
| `contain_finance` | 包含理财内容 | 发送该值 |
| `ai_creation` | 包含 AI 辅助创作，作者对内容负责 | 发送该值 |

如果用户选择没有声明，不要发送 `creation_statement`，也不要发送空字符串。

本次内容由 AI 生成或有 AI 辅助参与时（包括模型代写、扩写、改写或成段润色），必须主动推荐 `ai_creation`，并说明不声明可能影响后续 AI 识别与内容分发。推荐后是否声明仍由用户决定：用户未明确选择时不得发送该字段，也不得默认代选。

## table_of_contents_enabled

发布前询问用户是否创建文章内容目录。默认值为 `false`，表示不创建目录；只有用户明确要求创建目录时才发送 `true`。

## 示例

```json
{
  "type": "article",
  "confirmed": true,
  "confirm_note": "confirmed by user after local preview",
  "content": {
    "title": "HTTP publish article test",
    "html": "<p>This is an article published through PublishHandler.Publish.</p>",
    "comment_permission": "all",
    "table_of_contents_enabled": false,
    "creation_statement": "ai_creation",
    "topics": [
      {
        "topic_id": "",
        "topic_token": "19555547",
        "topic_name": ""
      }
    ]
  }
}
```
