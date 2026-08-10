# 知乎内容配置规则

根据已转换完成的标题与正文生成知乎发布配置项。标题与正文转换按 [`conversion.md`](./conversion.md) 执行。

---

## 1. 配置产出结构

标题与正文转换完成后，按内容形态生成 `config` 对象。配置与正文分离，供发布阶段使用；预览阶段不展示配置。

```json
{
  "type": "article",
  "title": "...",
  "body": "...",
  "config": {
    "topics": [],
    "tableOfContentsEnabled": false,
    "creationStatement": {},
    "commentPermission": "all",
    "ring": null
  }
}
```

字段说明：

- `type`：内容形态，取值为 `article`、`question`、`pin`；用于决定标题、正文与配置规则。
- `title`：按 [`conversion.md`](./conversion.md) 转换后的标题；所有形态均保留该字段，文章、提问内容必填，想法没有标题意图时使用空字符串。
- `body`：按 [`conversion.md`](./conversion.md) 转换后的正文 HTML；想法的独立图片与独立 `linkCard` 不写入 `body`。
- `config`：正文之外的发布配置集合，不属于正文 HTML；不同内容形态只输出其支持的配置项，不需要为不支持的配置项补空值。
- `config.topics`：文章和提问的话题配置列表，只能包含已存在且可发布的话题；想法的话题属于正文表达，不写入 `config.topics`。
- `config.tableOfContentsEnabled`：文章目录开关，仅文章需要考虑。
- `config.creationStatement`：文章创作声明配置；无声明时使用默认「无声明」配置。
- `config.commentPermission`：评论权限；默认 `all`。
- `config.ring`：圈子配置，主要用于想法；不使用时为 `null`。

---

## 2. 话题

### 2.1 文章与提问

- 只能选择 **已存在且可发布** 的话题。
- 按关键词查询已有话题，将查询结果写入 `config.topics`。
- **不得创建新话题**；未找到匹配话题时，不写入 `config.topics`，并向用户说明该话题不可用于当前文章或提问。
- 每个已有话题包含：

```json
{
  "topic_id": "19683675",
  "topic_name": "话题名"
}
```

### 2.2 想法

- 话题只使用用户明确提供或确认的内容；用户未提供或确认时，不得自动生成。
- 想法允许使用已有话题，也允许创建新话题。
- 想法话题属于正文表达，写入 `body`，不写入 `config.topics`。
- 发布想法时必须按话题名检查话题是否存在：存在时复用已有话题及其真实 ID，不存在时创建新话题后使用新 ID。
- validate 阶段不得编造 `topic_id`；尚未完成存在性检查时，只保留话题名，由发布想法阶段完成查询、复用或创建。

### 2.3 按形态

| 形态 | 与正文关系 | 数量上限 | 创建规则 | 说明 |
| ---- | ---------- | -------- | -------- | ---- |
| 提问 | **独立于正文** | 最多 **5** 个 | 仅使用已有话题，不创建 | 写入 `config.topics`，不嵌入 `body` HTML |
| 文章 | **独立于正文** | 最多 **3** 个 | 仅使用已有话题，不创建 | 写入 `config.topics`，不嵌入 `body` HTML |
| 想法 | **属于正文表达** | 最多 **10** 个 | 仅处理用户明确提供或确认的话题；发布时检查，不存在则创建 | 嵌入正文，格式 `#话题名#`，见 [`conversion.md`](./conversion.md) 第 5.2 节；用户未提供或确认时不得自动生成；**不写入** `config.topics` |

### 2.4 示例

**提问 / 文章**

```json
{
  "config": {
    "topics": [
      {"topic_id": "19683675", "topic_name": "跑步鞋"},
      {"topic_id": "19550228", "topic_name": "前端开发"}
    ]
  }
}
```

**想法**

```json
{
  "config": {}
}
```

想法的话题已在 `body` 中以 `#话题名#` 表达，不在 `config` 中重复配置；发布时再检查话题是否存在，存在则复用，不存在则创建。

---

## 3. 目录

| 形态 | 是否支持 | 规则 |
| ---- | -------- | ---- |
| 文章 | **支持** | 目录是文章发布配置；应基于正文中的 `h2` / `h3` 标题结构生成 |
| 提问 | 不支持 | 不要生成目录配置 |
| 想法 | 不支持 | 不要生成目录配置 |

### 3.1 文章目录配置

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| `tableOfContentsEnabled` | `boolean` | 是否启用目录 |

- 正文存在至少一个 `h2` 或 `h3` 标题时，必须设为 `true`
- 正文不存在 `h2` / `h3` 标题时，必须设为 `false`


**示例**

```json
{
  "config": {
    "tableOfContentsEnabled": true
  }
}
```

发布字段：`table_of_contents_enabled`。

---

## 4. 创作声明

| 形态 | 是否支持 | 规则 |
| ---- | -------- | ---- |
| 文章 | **支持** | 必须按可选枚举设置；默认「无声明」 |
| 提问 | 不支持 | 不要生成创作声明配置 |
| 想法 | 不支持 | 不要生成创作声明配置 |

### 4.1 枚举值（展示文案）

| 展示文案 | 说明 |
| -------- | ---- |
| 包含剧透 | |
| 包含医疗建议 | |
| 虚构创作 | |
| 包含理财内容 | |
| 包含 AI 辅助创作 | |
| 作者对内容负责 | |
| 无声明 | **默认值** |

> `disclaimer_type` 的具体取值以可用创作声明选项中的 `type` 字段为准；上表为展示文案枚举，选择后映射为对应 `type`。

### 4.2 配置结构

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| `disclaimer_type` | `string` | 声明类型，默认 `none` |
| `disclaimer_status` | `string` | `none` 时为 `close`；其他类型为 `open` |

**示例（无声明，默认）**

```json
{
  "config": {
    "creationStatement": {
      "disclaimer_type": "none",
      "disclaimer_status": "close"
    }
  }
}
```

**示例（包含 AI 辅助创作）**

```json
{
  "config": {
    "creationStatement": {
      "disclaimer_type": "<对应「包含 AI 辅助创作」的 type>",
      "disclaimer_status": "open"
    }
  }
}
```

---

## 5. 评论权限设置

| 形态 | 是否支持 | 规则 |
| ---- | -------- | ---- |
| 文章 | **发布前不可配置** | 默认 **任何人可评论**（`all`） |
| 想法 | **支持** | 可配置评论权限 |
| 提问 | 不支持 | 不要生成评论权限配置 |

### 5.1 想法评论权限枚举

| 展示文案 | `comment_permission` 值 |
| -------- | ----------------------- |
| 任何人都可以评论 | `all` |
| 仅显示筛选后的评论 | `censor` |
| 关注我 3 天及以上的人能评论 | `follower_n_days` |
| 我关注的人能评论 | `followee` |
| 不允许评论 | `nobody` |

- 默认值：`all`

**示例**

```json
{
  "config": {
    "commentPermission": "all"
  }
}
```

---

## 6. 圈子

| 形态 | 是否支持 | 规则 |
| ---- | -------- | ---- |
| 想法 | **支持** | 可同步到圈子或设置仅圈子可见；**只能选择一个**圈子 |
| 提问 | 不支持 | 不要生成圈子配置 |
| 文章 | 不支持 | 不要生成圈子配置 |

> 圈子是想法发布配置，**不是正文内容**。

### 6.1 圈子配置结构

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| `id` | `string` | 圈子 ID |
| `name` | `string` | 圈子名称 |
| `ring_only` | `boolean` | `false` = 同步到圈子；`true` = 仅圈子可见 |

### 6.2 同步模式

| 模式 | `ring_only` | 说明 |
| ---- | ----------- | ---- |
| 同步到圈子 | `false` | 内容正常发布，并同步到所选圈子 |
| 仅圈子可见 | `true` | 内容仅在所选圈子内可见 |

**示例（同步到圈子）**

```json
{
  "config": {
    "ring": {
      "id": "12345",
      "name": "示例圈子",
      "ring_only": false
    }
  }
}
```

**示例（未选择圈子）**

```json
{
  "config": {
    "ring": null
  }
}
```

---

## 7. 各形态 config 字段汇总

| 配置项 | 提问 | 文章 | 想法 |
| ------ | ---- | ---- | ---- |
| `topics` | 最多 5，仅使用已有话题，不创建 | 最多 3，仅使用已有话题，不创建 | 不配置；只将用户明确提供或确认的话题写入正文，发布时检查并按需创建；没有时不生成 |
| `tableOfContentsEnabled` | — | 支持 | — |
| `creationStatement` | — | 支持 | — |
| `commentPermission` | — | 固定 `all` | 支持，默认 `all` |
| `ring` | — | — | 支持，最多 1 个 |

---

## 8. 完整产出示例

### 8.1 文章

```json
{
  "type": "article",
  "title": "创造力，从何而来？",
  "body": "<h2>引言</h2><p>正文...</p>",
  "config": {
    "topics": [
      {"topic_id": "19683675", "topic_name": "创造力"}
    ],
    "tableOfContentsEnabled": true,
    "creationStatement": {
      "disclaimer_type": "none",
      "disclaimer_status": "close"
    },
    "commentPermission": "all"
  }
}
```

### 8.2 提问

```json
{
  "type": "question",
  "title": "如何系统学习前端开发？",
  "body": "<p>补充说明...</p>",
  "config": {
    "topics": [
      {"topic_id": "19550228", "topic_name": "前端开发"}
    ]
  }
}
```

### 8.3 想法

```json
{
  "type": "pin",
  "title": "",
  "body": "<p>今天很有收获 <a class=\"hash_tag\" data-topic-name=\"#读书笔记#\">#读书笔记#</a></p>",
  "media": [
    {
      "image": {
        "url": "https://pic1.zhimg.com/v2-example.jpg",
        "originalUrl": "https://pic1.zhimg.com/v2-example_r.jpg",
        "width": 800,
        "height": 600
      }
    }
  ],
  "linkCard": null,
  "config": {
    "commentPermission": "all",
    "ring": null
  }
}
```
