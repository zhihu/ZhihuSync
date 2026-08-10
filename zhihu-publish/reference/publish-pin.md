# Pin Publish Spec

当 `./.zhihu-publish-output/validate/latest.json` 中 `type` 为 `pin` 时，按本文档把 validate 结果转换为 publish OpenAPI request。

## 前置校验

- `latest.type` 必须为 `pin`。
- `latest.body` 必须非空；本文的 `html` 指 request 中的 `content.html`，来源是 validate 的 `latest.body`。
- 用户必须已经确认 `./.zhihu-publish-output/preview/latest.html`。
- 如果 validate 结果中同时存在非空独立图片和独立链接卡片，停止发布并提醒用户：`当前不支持 单条想法中同时包括链接卡片 与  图片`。

`zhihu-validate` 允许想法正文为空，只要独立图片或链接卡片有效；但当前 publish OpenAPI 要求 `content.html` 非空。遇到空正文想法时停止发布，要求用户回到 draft 补充正文并重新 validate / preview，不要自行生成占位正文。

## validate 字段来源

想法发布只从 validate 结果中读取以下内容字段：

| Request 字段 | validate 来源 | 规则 |
|---|---|---|
| `content.title` | `latest.title` | 可选；空时可省略 |
| `content.html` | `latest.body` | 必须非空；直接使用反序列化后的 HTML 字符串 |
| `content.linkcard` | `latest.linkCard` | 可选；仅在无独立图片时发送 |
| `content.images` | `latest.media` 或 `latest.images` | 可选；仅独立图片；仅在无独立链接卡片时发送 |

不要从 validate 结果中提取或继承想法发布配置。即使 `latest.config` 中存在评论权限或圈子，也必须在发布前重新和用户确认。

想法话题属于正文表达，已经在 `latest.body` 中，不发送 `topics`。不要发送 `creation_statement` 或 `table_of_contents_enabled`。

## 发布前交互确认

组装请求前，必须向用户确认以下发布参数。用户直接接受默认值时，可以继续发布。

确认时必须把评论权限可选项展示给用户，不能只问“请选择评论权限”。展示时只展示中文描述，不展示内部参数值。

| 参数 | 默认值 | 处理规则 |
|---|---|---|
| 评论权限 | 所有人可评论 | 用户未指定时内部发送 `all` |
| 圈子 `ring` | 不设置 | 用户需要发布到圈子时，要求用户粘贴知乎圈子链接；询问时必须给出示例 `https://www.zhihu.com/ring/host/1871220824524066816`；未提供时不发送 `ring` |

## Request Body

无独立图片、无链接卡片、无圈子时，请求体形如：

```json
{
  "type": "pin",
  "confirmed": true,
  "confirm_note": "confirmed by user after local preview",
  "content": {
    "title": "...",
    "html": "<p>...</p>",
    "comment_permission": "all"
  }
}
```

有独立图片时，请求体形如：

```json
{
  "type": "pin",
  "confirmed": true,
  "confirm_note": "confirmed by user after local preview",
  "content": {
    "title": "...",
    "html": "<p>...</p>",
    "comment_permission": "all",
    "images": [
      {
        "url": "https://pic-private.zhihu.com/v2-watermark~resize:1440:q75.png?..."
      }
    ]
  }
}
```

有链接卡片时，请求体形如：

```json
{
  "type": "pin",
  "confirmed": true,
  "confirm_note": "confirmed by user after local preview",
  "content": {
    "title": "...",
    "html": "<p>...</p>",
    "comment_permission": "all",
    "linkcard": {
      "data_content_type": "common_url",
      "data_content_id": "0",
      "url": "https://example.com",
      "data_draft_title": "",
      "data_draft_cover": "",
      "is_from_forward": false
    }
  }
}
```

如果用户确认了圈子，再在 `content` 中追加 `ring`：

```json
{
  "ring": {
    "ring_id": "1871220824524066816",
    "ring_name": ""
  }
}
```

## 字段映射

| Request 字段 | 来源 | 规则 |
|---|---|---|
| `type` | 固定 | `pin` |
| `confirmed` | 固定 | `true` |
| `confirm_note` | 固定 | `confirmed by user after local preview` |
| `content.title` | `latest.title` | 可选；空时可省略 |
| `content.html` | `latest.body` | 必须非空；不要从 preview HTML 中读取 |
| `content.comment_permission` | 用户发布前确认 | 默认 `all` |
| `content.images` | validate 独立图片 | 可选；仅在无独立链接卡片时发送 |
| `content.linkcard` | `latest.linkCard` | 可选；仅在无独立图片时发送 |
| `content.ring` | 用户发布前粘贴的圈子链接 | 可选；未提供时不发送 |

## 评论权限

发布前询问用户评论权限。对用户只展示中文描述，不展示内部参数值，不要写成“任何人都可以评论（all）”；用户不选择时使用默认项“任何人都可以评论”，内部发送 `all`。

| 用户可见选项 | 内部值 |
|---|---|
| 任何人都可以评论 | `all` |
| 不允许评论 | `nobody` |
| 我关注的人能评论 | `followee` |
| 仅显示我筛选后的评论 | `censor` |
| 关注我 3 天以上的人可评论 | `follower_n_days` |

如果用户选择或输入的评论权限无法匹配上表任一中文描述，停止发布并要求用户重新选择；不要静默替换为默认值，也不要要求用户输入内部值。

## images

仅映射想法独立媒体区图片。文章和提问正文图片已经在 HTML 中，不适用本文档。

兼容两种 validate 结构：

- `latest.media` 是数组：遍历 `media[].image`。
- `latest.media` 是对象：遍历 `media.medias[].image`。
- 如果 validate 结果直接提供 `latest.images`，遍历其中每一项。

每张图片在 publish request 中映射为：

```json
{
  "url": "https://pic-private.zhihu.com/v2-watermark~resize:1440:q75.png?..."
}
```

字段规则：

- 每张图片按固定优先级选择 URL：优先使用非空 `watermarkUrl`；为空时使用非空 `url`；仍为空时使用非空 `originalUrl`。
- 将选中的字段值原样写入 publish request 的 `images[].url`，完整保留查询参数；不得裁剪、补全、规范化或改写。
- `watermarkUrl`、`url`、`originalUrl` 都为空时，将空字符串写入 `images[].url`；不得继续回退使用 `media_key`、`mediaKey` 或其他字段。

如果生成了非空 `images`，不要再发送独立 `linkcard`。如果 `images` 和 `linkcard` 同时存在，停止发布并提醒用户：`当前不支持 单条想法中同时包括链接卡片 与  图片`。

## linkcard

仅在没有独立图片时发送。字段名是 `linkcard`，不是 `linkCard`。

映射规则：

| Request 字段 | 来源 |
|---|---|
| `data_content_type` | `linkCard.data_content_type` 或 `linkCard.dataContentType`，缺失时可用 `common_url` |
| `data_content_id` | `linkCard.data_content_id` 或 `linkCard.dataContentId`，缺失时可用 `0` |
| `url` | `linkCard.url`，必须非空 |
| `data_draft_title` | `linkCard.data_draft_title` 或 `linkCard.dataDraftTitle`，缺失时用空字符串 |
| `data_draft_cover` | `linkCard.data_draft_cover` 或 `linkCard.dataDraftCover`，缺失时用空字符串 |
| `is_from_forward` | `linkCard.is_from_forward` 或 `linkCard.isFromForward`，缺失时用 `false` |

如果用户意图发布链接卡片但 `url` 缺失，停止发布并要求回到 draft 修正，不要编造链接。

## ring

圈子不从 validate 结果读取。发布前询问用户是否发布到圈子；询问时必须展示具体示例。如果需要发布到圈子，要求用户粘贴知乎圈子链接，例如：

```text
https://www.zhihu.com/ring/host/1871220824524066816
```

提取规则：

- 从 `/ring/host/{ring_id}` 路径段中提取 `{ring_id}`；上例的 `ring_id` 是 `1871220824524066816`。
- `ring_id` 必须是数字字符串。
- `ring_name` 不需要用户提供，固定置为空字符串 `""`。
- 无法从链接中提取 `ring_id` 时，停止发布并要求用户补充正确的圈子链接。

映射为：

```json
{
  "ring_id": "1871220824524066816",
  "ring_name": ""
}
```

## 示例

带图片和圈子的想法：

```json
{
  "type": "pin",
  "confirmed": true,
  "confirm_note": "confirmed by user after local preview",
  "content": {
    "title": "HTTP publish pin test",
    "html": "<p>This is a pin published through publish OpenAPI.</p>",
    "comment_permission": "all",
    "images": [
      {
        "url": "https://pic-private.zhihu.com/v2-watermark~resize:1440:q75.png?..."
      }
    ],
    "ring": {
      "ring_id": "1871220824524066816",
      "ring_name": ""
    }
  }
}
```

带链接卡片的想法：

```json
{
  "type": "pin",
  "confirmed": true,
  "confirm_note": "confirmed by user after local preview",
  "content": {
    "title": "HTTP publish pin linkcard test",
    "html": "<p>This is a pin with a link card.</p>",
    "comment_permission": "all",
    "linkcard": {
      "data_content_type": "common_url",
      "data_content_id": "0",
      "url": "https://example.com",
      "data_draft_title": "",
      "data_draft_cover": "",
      "is_from_forward": false
    }
  }
}
```
