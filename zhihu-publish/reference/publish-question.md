# Question Publish Spec

当 `./.zhihu-publish-output/validate/latest.json` 中 `type` 为 `question` 时，按本文档把 validate 结果转换为 publish OpenAPI request。

## 前置校验

- `latest.type` 必须为 `question`。
- `latest.title` 必须非空。
- 用户必须已经确认 `./.zhihu-publish-output/preview/latest.html`。

问题说明 `latest.body` 可为空。校验失败时停止发布；不要从 preview HTML 反向提取正文，也不要补写占位标题、说明或话题。

## validate 字段来源

问题发布只从 validate 结果中读取以下内容字段：

| Request 字段 | validate 来源 | 规则 |
|---|---|---|
| `content.title` | `latest.title` | 必须非空 |
| `content.html` | `latest.body` | 可为空字符串；不要编造问题说明 |

不要从 validate 结果中提取或继承问题关联话题。即使 `latest.config.topics` 存在，也必须在发布前重新和用户确认。

## 发布前交互确认

组装请求前，必须询问用户是否需要关联话题。用户可以不提供话题；未提供时不要发送 `content.topics`。如需要关联话题，则提示用户粘贴知乎话题链接，最多 5 个话题。

示例：

```text
https://www.zhihu.com/topic/19555547/hot
```

## Request Body

```json
{
  "type": "question",
  "confirmed": true,
  "confirm_note": "confirmed by user after local preview",
  "content": {
    "title": "...",
    "html": "<p>...</p>"
  }
}
```

如果用户提供了话题链接，再在 `content` 中追加：

```json
{
  "topics": [
    {
      "topic_id": "",
      "topic_token": "19555547",
      "topic_name": ""
    }
  ]
}
```

## 字段映射

| Request 字段 | 来源 | 规则 |
|---|---|---|
| `type` | 固定 | `question` |
| `confirmed` | 固定 | `true` |
| `confirm_note` | 固定 | `confirmed by user after local preview` |
| `content.title` | `latest.title` | 必须非空 |
| `content.html` | `latest.body` | 可为空字符串；不要从 preview HTML 中读取 |
| `content.topics` | 用户发布前粘贴的话题链接 | 可选；未提供时不发送；最多 5 个 |

不要发送 `comment_permission`、`creation_statement`、`table_of_contents_enabled`、`images`、`ring`、`linkcard`。

## topics

问题话题可选。需要关联话题时，话题必须由用户在发布前手动粘贴知乎话题链接，例如：

```text
https://www.zhihu.com/topic/19555547/hot
```

提取规则：

- 从 `/topic/{topic_token}` 路径段中提取 `{topic_token}`；上例的 `topic_token` 是 `19555547`。
- 用户不提供话题，或明确选择跳过话题时，不发送 `content.topics`。
- 支持用户一次粘贴多个链接，按出现顺序去重，最多保留 5 个。
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

## 示例

```json
{
  "type": "question",
  "confirmed": true,
  "confirm_note": "confirmed by user after local preview",
  "content": {
    "title": "How should teams evaluate AI tool productivity?",
    "html": "<p>This is a question detail published through publish OpenAPI.</p>"
  }
}
```
