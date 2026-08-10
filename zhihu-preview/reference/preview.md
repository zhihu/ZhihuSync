# 知乎内容预览规则

将 `zhihu-validate` 生成的知乎适配内容渲染为本地浏览器可打开的预览 HTML。预览只呈现内容字段，不展示发布配置，也不负责生成、补全或改写发布内容。

---

## 1. 输入与输出

### 1.1 输入

读取：

```text
./.zhihu-publish-output/validate/latest.json
./.zhihu-publish-output/draft/latest-draft.md   # 仅用于用户内容图片的原始来源映射
```

输入是已经生成好的知乎适配结构化内容：

```json
{
  "type": "article | question | pin",
  "title": "...",
  "body": "<p>...</p>",
  "media": [],
  "linkCard": null,
  "config": {}
}
```

- `title`、`body`、`media`、`linkCard` 必须来自 `zhihu-validate` 转换结果。
- 预览只渲染 `type`、`title`、`body`、`media`、`linkCard`，忽略 `config`。
- 预览不得重新推断内容形态，不得重新生成标题、正文、媒体或链接卡片。
- draft 不是第二份内容输入。仅当图片由用户提供时，读取其中的原始图片引用并建立预览图片来源映射：本地图片使用原始本地文件 URI，网络图片使用用户提供的原始 HTTP(S) URL；其他字段一律不得从 draft 读取或覆盖 validate 结果。

### 1.2 输出

生成：

```text
./.zhihu-publish-output/preview/latest.html
./.zhihu-publish-output/preview/YYYY-MM-DD-HHmm-preview.html
```

- 输出文件必须是完整 HTML 文档，可直接用本地浏览器打开。
- 预览 HTML 只用于用户核对，不作为发布输入。
- 每次生成同时写入带时间戳的历史文件，并覆盖 `latest.html`。
- 生成预览不得修改 `./.zhihu-publish-output/validate/latest.json`。
- 恢复用户提供的原始图片来源只改变 preview HTML，不改变 validate JSON、draft 或后续 publish 输入。

---

## 2. HTML 文件结构

生成完整 HTML 文档，推荐结构：

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'none'; connect-src 'none'; object-src 'none'; frame-src 'none'; form-action 'none'; base-uri 'none'; img-src https: http: file:; style-src 'unsafe-inline';">
  <title>知乎发布预览</title>
  <style>
    /* 基础预览样式 */
  </style>
</head>
<body>
  <article class="zhihu-preview">
    <section class="preview-type">内容类型：文章</section>
    <h1 class="preview-title">标题</h1>
    <section class="preview-body">正文 HTML</section>
    <section class="preview-extra">独立媒体与链接卡片</section>
  </article>
</body>
</html>
```

预览应包含基础 CSS，使正文、图片、链接卡片、表格和代码块在浏览器中可读。

---

## 3. 展示顺序

预览按以下顺序展示：

1. 内容类型
2. 标题
3. 正文
4. 独立媒体与链接卡片

---

## 4. 内容展示规则

### 4.1 内容类型

将 `type` 映射为用户可读文案：

| `type` | 展示文案 |
| ------ | -------- |
| `article` | 文章 |
| `question` | 提问 |
| `pin` | 想法 |

### 4.2 标题

- `title` 存在时展示为主标题。
- `title` 为空时，不展示标题区，也不要显示“无标题”。

### 4.3 正文

- 使用 `body` 作为正文来源。
- 保持 `body` 中已有内容顺序，不新增、不删除、不重排正文内容。
- `body` 为空时，不展示正文区。
- 生成预览前解析 `body` 的 HTML 结构；如果 validate 的 `body` 中存在实际的 `script`、`iframe`、`object`、`embed`、`svg`、`style` 元素，`on*` 事件属性、`srcdoc` 属性，或属性值中存在 `javascript:`、`vbscript:`、`file:` 等危险 URL，停止生成预览，不得渲染或覆盖已有 `latest.html`。不得通过字符串搜索判断危险内容，代码块或普通文本中经过转义的标签与 URL 不应触发拦截。完成此检查后，由 preview 按第 5.2 节注入已确认的用户原始图片来源；其中从本地图片路径生成的 `file:` URI 是唯一允许的 `file:` 来源。
- 可对 `body` 中的知乎适配 HTML 做浏览器预览适配，适配规则见第 5 节。

### 4.4 独立媒体与链接卡片

- `media` 有内容时，在正文之后按原顺序展示。
- 图片与独立链接卡片 **展示互斥，图片优先**：
  - 有图片时只展示媒体区，不展示底部 `linkCard`。
  - 无图片且 `linkCard` 有内容时，在正文之后展示链接卡片。
- 正文内文字链接随 `body` 正常渲染，不受上述互斥影响。
- 只展示已有字段；缺失标题、封面或 URL 时，不生成占位文案。

---

## 5. 浏览器预览适配规则

预览阶段可以把知乎适配 HTML 渲染成更适合浏览器核对的展示结构，但不得修改输入 JSON。

### 5.1 通用规则

- 不新增正文语义内容。
- 不删除正文语义内容。
- 不读取或渲染 `config` 中的发布配置。
- 仅为浏览器展示补充容器、样式或派生展示结构。
- URL 以 `//` 开头时，预览中可补全为 `https://`。

### 5.2 图片

正文中的图片：

- 使用 `src` 展示图片。
- `data-caption` 非空时，在图片下方展示图注。
- `data-size="small"` 时按小图样式展示。
- `data-size="normal"` 时按正文宽度展示。
- `data-original-src`、`data-watermark-src`、`data-private-watermark-src` 不直接展示为文本。

想法独立媒体区图片：

- 兼容 `media[].image.url` 与 `media.medias[].image.url` 两种结构，按原顺序展示图片。
- 有 `width`、`height` 时可用于设置图片比例或展示尺寸。
- 不把独立媒体图片写入 `body`。

用户原始图片来源映射是强制的，按以下规则执行：

1. 从 draft 按出现顺序提取用户提供的图片引用，并区分本地路径与网络 URL；不要把普通路径文本、链接卡片封面或公式当作内容图片。
2. 使用结构化解析：文章和提问从 validate 的 `body` 中提取非公式内容图片，排除带 `eeimg` 的公式图片；想法从 `media[]` 或 `media.medias[]` 中提取独立媒体图片。将全部 draft 图片引用与这些 validate 图片按原始顺序一一对应，并把每张图片的显示地址替换为对应的原始来源。必须逐个修改解析后的图片节点，不得全局替换 URL 字符串；相同上传 URL 可能对应不同图片位置。
3. 每个本地路径必须解析为绝对路径，并确认是存在且可读的图片文件。使用平台标准路径 / URL API 将绝对路径转换为百分号编码的 `file:` URI，例如 `file:///Users/name/My%20Image.png`；不得手工拼接未编码路径。将 URI 写入 HTML 属性时使用 DOM / HTML 序列化器正确转义，不得拼接 HTML 字符串。
4. 每个网络图片引用必须是合法的绝对 `http://` 或 `https://` URL。preview 生成阶段不得重新下载、转存、解析重定向或规范化该 URL；直接使用用户在 draft 中提供的原始 URL，包括其路径和查询参数。写入 HTML 属性时使用 DOM / HTML 序列化器正确转义；序列化产生的实体转义不视为修改 URL。
5. 对应正文图片在 preview HTML 中将显示用 `src` 替换为第 3 或第 4 步得到的原始来源，并移除可能覆盖 `src` 或包含上传后 URL 的 `srcset`、`data-original-src`、`data-watermark-src`、`data-private-watermark-src`。对应想法媒体生成的 `<img>` 只使用原始来源作为 `src`。不得把上传后 URL、重定向后的 URL 或其他地址作为备用来源。
6. 映射后的改动只存在于新生成的 preview HTML。不得修改 `validate/latest.json`、其中的 `body` / `media` 对象或 draft；publish 仍使用 validate 中的上传后 URL。
7. 本地文件不存在、不可读、不是图片，网络图片引用不是合法的绝对 HTTP(S) URL，或 draft 图片与 validate 图片无法一一对应时，停止生成预览并说明原因；不得回退到上传后 URL，也不得覆盖已有 `latest.html`。生成 preview 时不要求主动请求网络图片；浏览器打开预览后若原始 URL 加载失败，应显示加载失败，不得静默切换为上传后 URL。

例如用户提供 `https://fastly.picsum.photos/id/96/600/400.jpg?hmac=iHxmTGq3eu4wyDxXNdgDdiejFfIj8BN6l5n2b63pGak` 时，preview HTML 的对应 `<img src>` 必须使用该原始 URL；validate 和 publish 仍使用转存后的知乎媒体地址。

公式图片和链接卡片封面不属于上述用户内容图片来源映射，继续使用 validate 中的地址。

### 5.3 公式

公式图片：

- `src` 为 `//www.zhihu.com/equation?...` 时，预览中补全为 `https://www.zhihu.com/equation?...`。
- `eeimg="1"` 按行内公式展示。
- `eeimg="2"` 按块级公式展示。
- `alt` 可作为图片不可加载时的替代文本或悬浮说明。

### 5.4 链接卡片

正文中的链接卡片：

```html
<a data-draft-type="link-card">...</a>
```

预览时渲染为卡片样式：

- 标题：优先使用 `data-draft-title`，缺失时使用标签内文本。
- 封面：有 `data-draft-cover` 时展示。
- 链接：使用 `href`。

想法独立 `linkCard`：

- 无独立图片且 `linkCard` 存在时展示。
- 标题使用 `data_draft_title`。
- 封面使用 `data_draft_cover`。
- 链接使用 `url`。

### 5.5 表格

- 保留 `<table>`、`<tbody>`、`<tr>`、`<th>`、`<td>`。
- 增加边框、单元格间距和横向滚动容器。
- 不额外生成表头或改写单元格内容。

### 5.6 代码

- `<pre lang="">` 渲染为代码块。
- `lang` 非空时可展示语言 ID。
- `<code>` 渲染为行内代码。
- 不对代码内容做重新格式化。

### 5.7 空段落

- `<p><br></p>` 在预览中保留为空行。
- 不把空段落渲染为“空内容”等占位文案。

---

## 6. 确认规则

- 预览只展示同一份结构化内容，不生成第二份标题或正文。
- 生成完成后，按 `../SUBSKILL.md` 的「向用户交付预览」规则确认 `latest.html` 存在，并优先调用平台命令使用系统默认浏览器打开本地 HTML；不得使用 Cursor `open_resource` 打开源码来代替浏览器预览。只有系统浏览器无法打开时，才提供绝对路径的可点击 Markdown 文件链接作为降级入口，并等待用户明确确认。
- 用户发现预览内容不对或要求修改内容时，先回到根 `zhihu-publisher`，结合用户需求和 `zhihu-validate` 的说明文档更新 `./.zhihu-publish-output/draft/latest-draft.md`，再重新运行 validate 和 preview。
- 不直接修改 `./.zhihu-publish-output/validate/latest.json` 或 `./.zhihu-publish-output/preview/latest.html` 来修正预览。
- 用户确认预览前，不进入发布步骤。
