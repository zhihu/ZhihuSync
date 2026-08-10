# 知乎内容转换规则

将用户提供的内容转换为知乎可发布的标题与正文。配置项（话题、目录、创作声明等）按 [`config.md`](./config.md) 生成。

---

## 1. 适用范围

| 内容形态 | 转换产出 |
| -------- | -------- |
| 提问 | `title` + `body`（问题说明，可选） |
| 想法 | `title`（字段必需，内容可为空字符串）+ `body` + 独立媒体区（图片）+ 链接卡片（可选） |
| 文章 | `title` + `body` |

正文最终形态为 **知乎可发布的 HTML 字符串**（想法的正文 HTML 与独立媒体区分离）。

### 1.1 内容保真与修改授权

- 默认忠实保留用户提供的标题、正文、事实、观点、论证关系、结构和语气。
- 用户要求“发布”“转换”“适配知乎”或“生成预览”，只授权执行发布流程和必要的格式适配，不代表授权润色或修改内容。
- 未经用户对具体动作和字段的明确允许，不得删减、截断、精简、总结、扩写、补充事实、重排、合并、拆分或语义改写用户内容，也不得主动改标题或改变语气。
- 授权范围必须按用户的具体选择执行。例如“标题选 2”只授权精简标题，不授权精简正文；“正文选 4”只授权按确认后的方案拆分正文，不授权改变各部分观点。
- Markdown 到知乎 HTML 的结构转换、HTML 转义、媒体引用替换，以及本文明确要求的确定性格式规范化可以执行，但必须保持用户可见文字的原意。提问标题按第 2.1 节补全结尾问号属于确定性格式规范化。
- 如果平台限制只能通过修改用户内容才能满足，停止转换并请求用户选择；没有明确授权时，不得为了通过校验而自行修改。

### 1.2 HTML 安全约束

- 输出只允许本文各元素「转换格式」明确列出的标签和属性；未列出的标签、属性和 `data-*` 属性默认禁止。
- 用户输入中的原始 HTML 不得原样透传，必须转换为本文支持的结构。
- 禁止 `script`、`iframe`、`object`、`embed`、`svg`、`style` 等可执行或可嵌入外部内容的标签。
- 禁止所有 `on*` 事件属性，以及未在本文转换格式中明确允许的 `style`、`srcdoc`、`class`、`id` 属性。
- URL 属性必须先解码 HTML 实体并去除首尾空白，再按对应元素规则校验；禁止 `javascript:`、`vbscript:`、`file:` 和未被对应元素规则明确允许的 `data:` URL。
- 发现上述危险标签、属性或 URL 时停止转换，不生成新的结构化结果，也不得覆盖已有 `latest.json`；不得静默删除危险内容后继续。
- 对 `div`、`span`、`font` 等不危险但不受支持的标签，移除标签格式并保留转义后的文本内容，同时向用户说明发生了格式降级。

### 1.3 转换前长度检查与用户决策

在转换标题、正文或上传媒体前，根据已确认的内容形态执行长度预检。按下文各形态的计数口径判断；提问标题没有问号且转换时需要补 `？` 时，必须把补入的问号计入标题长度。

标题或正文未超出上限时直接继续。发现超限时：

1. 告知用户超限字段、实际长度和当前形态的上限。
2. 提供下列对应选项，然后停止转换并等待用户明确选择。未经选择，不得自行截断、精简、切换形态、拆分内容、上传媒体、生成时间戳结果或覆盖 `validate/latest.json`。
3. 标题和正文同时超限时，在同一次回复中分别列出两组选项，允许用户分别选择，例如“标题选 2，正文选 4”。不要替用户合并决策。

**标题超出上限时，只提供：**

1. 由用户自行修改到合适长度，修改后告知模型。
2. 由模型精简标题。

用户选择 1 时，等待用户提供修改后的标题。用户选择 2 仅表示授权精简标题；保留原意、关键实体和提问意图进行精简，不得新增事实，也不得同时修改正文；将精简后的标题写回 draft，再重新检查长度并开始转换。

**正文超出上限时，提供：**

1. 由用户自行修改到合适长度，修改后告知模型。
2. 由模型精简正文。
3. 当前形态为想法时，建议改为文章；其他形态不显示此选项。
4. 拆分成多个提问、想法或文章。

按用户选择继续：

- 选择 1：等待用户提供修改后的正文，再写回 draft 并重新检查。
- 选择 2：该选择仅授权精简正文；保留核心观点、事实、必要论据和原有结构进行精简，不得编造、改变原意或同时修改标题；将精简后的正文写回 draft，再重新检查。
- 选择 3：先等待用户确认改为文章；确认后更新 draft 中的内容形态，并按文章的标题与正文规则重新检查。不得把“建议改为文章”视为用户已经同意。
- 选择 4：如果用户尚未说明拆分后的内容形态、数量或语义边界，先询问并可给出建议；确认拆分方案后按完整语义单元拆分。每份内容作为独立发布项，分别重新执行内容形态确认、draft、validate、preview 和用户确认，不得用一份预览确认代替全部拆分项。

任何选择导致标题、正文或内容形态变化时，都必须先更新 `draft/latest-draft.md` 并写入新的时间戳草稿，再重新执行本节检查。旧的 validate、preview 和 publish 产物随 draft 变化失效。

---

## 2. 标题规则

### 2.1 提问

- **必填**
- 长度 **4～51 字**（含结尾问号）
- **禁止换行**
- 标题末尾应体现疑问语气；若无问号，自动补全 `？`
- 不要生成两个问号；标题应表达 **一个明确问题**，不要把多个问题合并成一个标题

**示例**

| 输入 | 转换后标题 |
| ---- | ---------- |
| `React 和 Vue 怎么选` | `React 和 Vue 怎么选？` |
| `如何学习 Python？Java 怎么入门？` | 应拆分为多个提问，不合并 |

### 2.2 想法

- 字段**必需**；没有标题意图时使用空字符串
- 若生成标题：无最小字数要求，**最多 50 字**，禁止换行

**示例**

| 输入 | 转换后标题 |
| ---- | ---------- |
| （无标题意图） | `title` 使用空字符串 |
| `今日读书笔记` | `今日读书笔记` |

### 2.3 文章

- **必填**
- **100 字以内**，禁止换行

**示例**

| 输入 | 转换后标题 |
| ---- | ---------- |
| `创造力，从何而来？` | `创造力，从何而来？` |

---

## 3. 正文基础规则

### 3.1 提问

- **问题说明（正文）可选**，无正文字数上下限
- 正文使用与文章相同的富文本 HTML 格式（见第 4 节），但 **不支持注释**

### 3.2 想法

- **正文可选**
- 正文、图片、链接卡片中 **至少应有一项有效内容**
- 正文文本不得超过 **2000 字**（按纯文本计，不含 HTML 标签）
- 仅支持第 5 节列出的能力，**不支持其他富文本格式**

### 3.3 文章

- **正文必填**
- 长度 **最少 9 个字**，不得超过 **10 万字**（按纯文本计，不含 HTML 标签）

---

## 4. 正文元素能力（文章 / 提问）

文章与提问的正文格式相同，最终输出为 HTML。下表给出各元素应转成的格式与示例。

### 4.1 段落

| 元素 | 转换格式 | 示例 |
| ---- | -------- | ---- |
| 段落 | `<p></p>` | `<p>这是一段正文。</p>` |
| 空段落 / 空行 | `<p><br></p>` | `<p><br></p>` |

- 空段落用于保留正文中的空行；不要输出空的 `<p></p>`。

### 4.2 标题（一级 / 二级）

| 元素 | 转换格式 | 示例 |
| ---- | -------- | ---- |
| 一级标题 | `<h2></h2>` | `<h2>一级标题</h2>` |
| 二级标题 | `<h3></h3>` | `<h3>二级标题</h3>` |

> 目录配置会基于正文中的 `h2` / `h3` 结构生成，见 [`config.md`](./config.md)。

### 4.3 加粗 / 斜体

| 元素 | 转换格式 | 示例 |
| ---- | -------- | ---- |
| 加粗 | `<b></b>` | `<b>加粗内容</b>` |
| 斜体 | `<i></i>` | `<i>斜体内容</i>` |

### 4.4 列表

| 元素 | 转换格式 | 示例 |
| ---- | -------- | ---- |
| 有序列表 | `<ol><li></li></ol>` | `<ol><li>第一项</li><li>第二项</li></ol>` |
| 无序列表 | `<ul><li></li></ul>` | `<ul><li>要点 A</li><li>要点 B</li></ul>` |

### 4.5 引用

| 元素 | 转换格式 | 示例 |
| ---- | -------- | ---- |
| 引用块 | `<blockquote></blockquote>` | `<blockquote>这是一段引用内容。</blockquote>` |

多段引用内容用 `<br>` 分隔。示例：`<blockquote>第一段<br>第二段</blockquote>`

### 4.6 分割线

| 元素 | 转换格式 | 示例 |
| ---- | -------- | ---- |
| 分割线 | `<hr />` | `<hr />` |

### 4.7 代码块 / 行内代码

| 元素 | 转换格式 | 示例 |
| ---- | -------- | ---- |
| 代码块（无语言） | `<pre lang=""></pre>` | `<pre lang="">const x = 1;</pre>` |
| 代码块（有语言） | `<pre lang="语言ID"></pre>` | `<pre lang="cpp">const x = 1;</pre>` |
| 行内代码 | `<code></code>` | `这是一段<code>行内代码</code>示例` |

- 代码块**不要**写成 `<pre><code></code></pre>`，代码内容直接放在 `<pre>` 内。
- `lang` 使用语言 **id**（如 `cpp`、`python`、`js`），不是显示名（如 `C++`）。
- 支持的语言列表见 [`code-languages.md`](./code-languages.md)。

### 4.8 注释（仅文章）

| 元素 | 转换格式 | 示例 |
| ---- | -------- | ---- |
| 注释 / 引用标注 | `<sup data-text="" data-url="" data-draft-node="inline" data-draft-type="reference" data-numero="">[序号]</sup>` | 见下方完整示例 |

**完整示例**

```html
<sup
  data-text="注释说明"
  data-url="https://example.com/ref"
  data-draft-node="inline"
  data-draft-type="reference"
  data-numero="1"
>[1]</sup>
```

- `data-text`、`data-url` 至少一个非空；仅有 `data-url` 时必须是合法链接。
- `data-numero` 按文中**不同注释**首次出现顺序从 `1` 递增；同一注释多处引用时 `data-numero` 相同。
- 标签内文本为 `[序号]`，序号与 `data-numero` 一致。
- 转换输出 **不包含** `data-ref-key`。

> **提问不支持注释**，转换时不得生成 `data-draft-type="reference"` 元素。

### 4.9 图片

- **本地图片**：必须先上传得到知乎媒体 URL 及水印相关字段，再拼接到正文中。
- **非知乎域名的公网图片**：必须先转存到知乎媒体云，再使用上传结果转换。
- **已有知乎媒体地址**：地址合法且具备转换所需媒体属性时可以直接复用；属性不足时仍需通过媒体上传或查询流程补全。
- 需要上传但上传能力不可用或上传失败时，停止转换，不生成结构化结果或预览，不得直接使用原始 URL、本地路径或编造媒体属性。

| 元素 | 转换格式 | 示例 |
| ---- | -------- | ---- |
| 图片 | `<img src="" data-caption="" data-size="" data-rawwidth="" data-rawheight="" data-watermark="" data-original-src="" data-watermark-src="" data-private-watermark-src="" />` | 见下方完整示例 |

**完整示例**

```html
<img
  src="https://pic4.zhimg.com/v2-5d3669ef59a7e0b8345b561bdb018d90.png"
  data-caption=""
  data-size="normal"
  data-rawwidth="482"
  data-rawheight="438"
  data-watermark="original"
  data-original-src="https://pic4.zhimg.com/v2-5d3669ef59a7e0b8345b561bdb018d90.png"
  data-watermark-src=""
  data-private-watermark-src=""
/>
```

- 转换输出 **不包含** `class`（如 `origin_image`）或 `data-original`（应使用 `data-original-src`）。
- 图片注释写入 `data-caption`；无注释时留空 `""`，不超过 140 字。
- `data-size`：根据 `data-rawwidth` 判断，`>= 343` 为 `normal`，否则为 `small`。
- 本地图片转换前必须先上传；转换时使用图片上传结果填充 `src`、`data-original-src`、`data-rawwidth`、`data-rawheight`、`data-watermark`、`data-watermark-src`、`data-private-watermark-src`。`data-watermark` 应使用上传结果中的值，不要写成固定值。
- 无宽高信息时，可省略 `data-rawwidth`、`data-rawheight`、`data-watermark`、`data-private-watermark-src`，保留 `src`、`data-caption`、`data-size`、`data-original-src`、`data-watermark-src`。
- 本地路径（如 `file://`）不得直接写入 HTML，须先上传。

### 4.10 链接

文章 / 提问正文中的文字链接使用 `link` 类型，**不是**想法的 `text-link` 格式。

#### 文字链接

| 元素 | 转换格式 | 示例 |
| ---- | -------- | ---- |
| 文字链接 | `<a href="">链接文字</a>` | 见下方完整示例 |

**完整示例**

```html
<p><a href="https://www.example.com">链接标题</a></p>
```

- 文字链接为行内元素，放在 `<p>` 段落内。
- 一般只需 `href` 与标签内文字；**不需要** `data-insert-way`、`data-draft-node`、`data-draft-type="text-link"`。
- 可选 `data-draft-title`，值可与标签内文字相同。

#### 链接卡片

| 元素 | 转换格式 | 示例 |
| ---- | -------- | ---- |
| 链接卡片 | `<a href="" data-draft-node="block" data-draft-type="link-card" data-draft-title="" data-draft-cover="">标题文字</a>` | 见下方完整示例 |

**完整示例**

```html
<a
  href="https://www.zhihu.com"
  data-draft-node="block"
  data-draft-type="link-card"
  data-draft-title="知乎 - 有问题，就会有答案"
  data-draft-cover=""
>知乎 - 有问题，就会有答案</a>
```

- 链接卡片为块级元素（`data-draft-node="block"`），**不要**包在 `<p>` 内。
- 标签内文字一般为 `data-draft-title`（页面标题），不是裸 URL。
- 生成链接卡片前应先解析链接；转换时使用解析结果填充 `data-draft-title`、`data-draft-cover`。
- 无封面时 `data-draft-cover` 留空 `""`；解析结果包含 `data-content-type`、`data-content-id` 时填写，否则可省略。

### 4.11 公式

公式最终输出为 `<img eeimg>`，**不包含** `class="formula"` 或 `loading="lazy"`。

知乎编辑器以 `eeimg` 识别公式，以 `alt` 读取 LaTeX 原文。`src` 是由同一份 LaTeX URL 编码得到的公式图片地址。这里的“原文”包括公式定界符内侧已有的首尾空白；移除 `$...$` 或 `$$...$$` 定界符后，**不得再对 LaTeX 内容执行 `trim`、`strip` 或其他首尾空白归一化**。最终交给编辑器的必须是**反序列化后的 HTML**，不能是 JSON 字符串的转义展示形式。

| 元素 | 转换格式 | 示例 |
| ---- | -------- | ---- |
| 行内公式 | `<img eeimg="1" src="" alt="" />` | 见下方完整示例 |
| 块级公式 | `<img eeimg="2" src="" alt="" />` | 见下方完整示例 |

**完整示例（行内公式）**

```html
<img
  eeimg="1"
  src="//www.zhihu.com/equation?tex=E%3Dmc%5E2"
  alt="E=mc^2"
/>
```

**完整示例（块级公式）**

```html
<img
  eeimg="2"
  src="//www.zhihu.com/equation?tex=%5Csum_%7Bi%3D1%7D%5En%20i"
  alt="\sum_{i=1}^n i"
/>
```

- `alt` 存放 LaTeX 原文。
- `src` 为 `//www.zhihu.com/equation?tex=` + URL 编码后的 LaTeX。
- 移除 Markdown 公式定界符时只移除 `$` / `$$` 本身，保留定界符内侧的全部字符，包括首尾空格。例如 `$$ E=mc^2 $$` 的 LaTeX 原文是 ` E=mc^2 `，不能转换成 `E=mc^2`。
- `alt` 与用于生成 `src` 的字符串必须完全相同；不要分别清洗。空格编码为 `%20`，因此上例的 `src` 查询值必须以 `%20` 开头并以 `%20` 结尾。
- `eeimg="1"` 为行内公式，`eeimg="2"` 为块级公式；转换时优先保留输入 HTML 中已有的 `eeimg`。只有输入明确标记为块级公式时才输出 `eeimg="2"`；没有明确块级信息时，即使公式独立成段，也按 `eeimg="1"` 输出。
- 有尺寸信息时可加 `data-rawwidth`、`data-rawheight`；一般可省略。

**首尾空格回归示例（块级嵌套分式）**

输入：

```markdown
$$ \eta = \frac{t_s}{t_s + 2t_p} = \frac{\dfrac{V}{C}}{\dfrac{V}{C} + 2t_p} $$
```

反序列化后的输出：

```html
<img eeimg="2" src="//www.zhihu.com/equation?tex=%20%5Ceta%20%3D%20%5Cfrac%7Bt_s%7D%7Bt_s%20%2B%202t_p%7D%20%3D%20%5Cfrac%7B%5Cdfrac%7BV%7D%7BC%7D%7D%7B%5Cdfrac%7BV%7D%7BC%7D%20%2B%202t_p%7D%20" alt=" \eta = \frac{t_s}{t_s + 2t_p} = \frac{\dfrac{V}{C}}{\dfrac{V}{C} + 2t_p} " />
```

#### JSON 序列化与编辑器导入

- `latest.json` 必须由 JSON 序列化器对完整结果对象执行**一次**序列化，不要预先对 `body` 手工转义。
- JSON 文件中出现的 `\"` 与 `\\` 是序列化表示；读取 JSON 后，`body` 中的标签属性应为真实的 `"`，LaTeX 命令应为单个反斜杠。
- 消费端应先解析 JSON，再把 `payload.body` 直接交给知乎编辑器；不要执行 `JSON.stringify(payload.body)`，也不要把整段 JSON 文本当作 HTML。

正文中的半角双引号也必须由 JSON 字符串语法表示。模型生成的候选结果和最终文件都不能出现未转义、会提前结束 `body` 字符串的 `"`。

**转换阶段的正文值**：

```html
<p>她说："你好。"</p>
```

**JSON 文件中的正确表示**：

```json
{
  "body": "<p>她说：\"你好。\"</p>"
}
```

**JSON 解析后恢复的正文值**：

```html
<p>她说："你好。"</p>
```

不要把转换阶段正文值中的双引号替换为字面量 `\"`；转义只属于 JSON 文件表示。validate 必须按 `../SUBSKILL.md` 先生成候选，再通过 `scripts/finalize_validate_json.py` 解析并重新序列化后提交最终文件。

**反序列化后应交给编辑器的 HTML**：

```html
<img eeimg="1" src="//www.zhihu.com/equation?tex=E%3Dmc%5E2" alt="E=mc^2" />
```

**错误：把 JSON 转义字符作为 HTML 的一部分**：

```text
<img eeimg=\"1\" src=\"//www.zhihu.com/equation?tex=E%3Dmc%5E2\" alt=\"E=mc^2\" />
```

### 4.12 表格

表格最终 HTML **不含** `class`，使用 `data-draft-*` 属性。

| 元素 | 转换格式 | 示例 |
| ---- | -------- | ---- |
| 表格 | `<table data-draft-node="block" data-draft-type="table" data-size="" data-row-style=""><tbody><tr><th></th><td></td></tr></tbody></table>` | 见下方完整示例 |

**完整示例**

```html
<table
  data-draft-node="block"
  data-draft-type="table"
  data-size="normal"
  data-row-style="normal"
>
  <tbody>
    <tr>
      <th>列 A</th>
      <th>列 B</th>
    </tr>
    <tr>
      <td>单元格 1</td>
      <td>单元格 2</td>
    </tr>
  </tbody>
</table>
```

- 表头单元格用 `<th>`，普通单元格用 `<td>`；转换输出**只有** `<tbody>`，不用 `<thead>`。
- `data-size`：表格宽度样式，默认 `normal`。
- `data-row-style`：行样式，默认 `normal`。
- 单元格内仅支持纯文本；换行用 `<br>`，不要用其他富文本标签。

---

## 5. 正文元素能力（想法）

想法的正文与媒体分离，规则如下。

### 5.1 正文 HTML

- 仅支持 **纯文本段落** 与 **文字链接**
- 不支持标题、加粗、斜体、列表、引用、代码、公式、表格等富文本格式

**文字链接示例**（想法使用 `text-link` 格式，与文章不同）

```html
<p><a
  href="https://www.example.com"
  data-insert-way="force"
  data-draft-node="inline"
  data-draft-type="text-link"
  data-draft-title="链接文字"
>链接文字</a></p>
```

### 5.2 正文内话题

- 想法话题属于正文表达的一部分，嵌入正文中；文章和提问的话题不使用本节格式。
- 只转换用户在 draft 中明确提供或确认的话题；用户未提供或确认时，不得自动生成。
- 显示文字为 `#话题名#`，HTML 结构使用 `<a class="hash_tag">`，**不是**纯文本。
- 最多 **10 个**（与 [`config.md`](./config.md) 一致）。
- 想法允许使用已有话题，也允许创建新话题。发布想法时按话题名检查是否存在：存在则复用已有话题及其真实 ID，不存在则创建新话题后使用新 ID。
- validate 阶段不得编造 `data-topic-id`；已有真实 ID 时填写，尚未完成存在性检查或准备创建新话题时省略该属性，只保留 `data-topic-name` 和显示文字。

| 元素 | 转换格式 | 示例 |
| ---- | -------- | ---- |
| 话题 | `<a class="hash_tag" data-topic-name="">#话题名#</a>`；已有真实 ID 时增加 `data-topic-id` | 见下方完整示例 |

**已有话题示例**

```html
<p>今天读完了这本书，<a class="hash_tag" data-topic-name="#读书笔记#" data-topic-id="19550286">#读书笔记#</a> <a class="hash_tag" data-topic-name="#心理学#" data-topic-id="19551125">#心理学#</a></p>
```

**待发布时检查或创建的话题示例**

```html
<p>今天开始新的记录，<a class="hash_tag" data-topic-name="#每日工作复盘#">#每日工作复盘#</a></p>
```

- `data-topic-name` 与标签内文字均为 `#话题名#` 格式。
- `data-topic-id` 只能填写查询或创建接口返回的真实 ID；属性缺失表示由发布想法阶段继续检查并处理。
- 转换输出使用 `class="hash_tag"`；若输入中存在 `class="zed-topic"` 的话题节点，应归一化为 `class="hash_tag"`。

### 5.3 图片（独立媒体区）

- 图片 **不走正文富文本**，放入独立媒体区（与正文 HTML 分离）
- 最多 **18 张**（默认上限；具体以发布配置为准）
- 本地图片需先上传得到公网 URL 及水印相关字段
- 与独立 `linkCard` **展示互斥且图片优先**：有图片时不输出底部链接卡片（见 5.4）

**媒体区数据结构示例**

```json
{
  "media": {
    "medias": [
      {
        "image": {
          "url": "https://pic-private.zhihu.com/v2-watermark~resize:1440:q75.png?...",
          "originalUrl": "https://pic-private.zhihu.com/v2-original~resize:1440:q75.png?...",
          "width": 1254,
          "height": 1254,
          "watermark": "watermark",
          "watermarkUrl": "https://pic-private.zhihu.com/v2-watermark~resize:1440:q75.png?..."
        }
      }
    ]
  }
}
```

本地图片转换前必须先上传。当上传结果同时满足 `success: true`、`media_type: "image"` 和 `upload_result: "UPLOAD_SUCCESS"` 时，按下表生成每个 `image`。`extra.watermark_image_key` 和 `media_key` 都有值且不同时视为水印处理成功；两者相同或任一值缺失时视为水印处理失败。

| validate 字段 | 图片上传结果取值 | 规则 |
| ---- | ---- | ---- |
| `url` | `extra.watermark_image_url.primary` | 水印处理成功且该路径有值时完整复制，包括查询参数；否则使用空字符串 `""` |
| `originalUrl` | `media_url.primary` | 原图主访问地址；有值时完整复制，包括查询参数，否则使用空字符串 `""` |
| `width` | `media_meta.width` | 有值时保留为数字；未取得时使用空字符串 `""` |
| `height` | `media_meta.height` | 有值时保留为数字；未取得时使用空字符串 `""` |
| `watermark` | 由 `extra.watermark_image_key` 与 `media_key` 比较得出 | 两者都有值且不同时使用 `"watermark"`；水印处理失败、两者相同或任一值缺失时使用空字符串 `""` |
| `watermarkUrl` | `extra.watermark_image_url.primary` | 水印处理成功且该路径有值时完整复制，包括查询参数；否则使用空字符串 `""` |

- 水印处理失败时，`url`、`watermark` 和 `watermarkUrl` 使用空字符串 `""`；`originalUrl`、`width` 和 `height` 仍按原图字段的实际返回值填写，未取得的单项也使用空字符串 `""`。
- 图片字段必须全部保留，不得因为值缺失而省略任一字段；不得用其他字段代填缺失值。
- 不得将 `media_key` 直接写入 URL 字段，也不得用 `media_key` 自行拼接或推导 URL。
- 不得删除 `primary` URL 中的查询参数；字段未取得时使用 `""`，不得编造或用示例值填充。

**水印处理失败示例**

```json
{
  "image": {
    "url": "",
    "originalUrl": "https://pic-private.zhihu.com/v2-original~resize:1440:q75.png?...",
    "width": 1254,
    "height": 1254,
    "watermark": "",
    "watermarkUrl": ""
  }
}
```

### 5.4 链接卡片

- 最多 **1 个**
- 不属于正文 HTML，作为独立字段 `linkCard`（与文章正文内的 `link-card` 不同）
- 与图片区 **展示互斥**：有图片时 **不要** 再输出 `linkCard`；若仍需链接，改为正文文字链接（见 5.1）
- 仅在 **无图片** 时使用独立 `linkCard`
- 当输入内容中存在可解析链接且无图片时，可生成独立 `linkCard`；生成前应先解析链接，并使用解析结果填充 `url`、`data_draft_title`、`data_draft_cover`。
- 解析结果包含 `data_content_type`、`data_content_id` 时填写；外链无对应内容类型或内容 ID 时可省略。

**数据结构示例**

```json
{
  "linkCard": {
    "url": "https://www.zhihu.com",
    "data_content_type": "Pin",
    "data_content_id": "123456",
    "data_draft_title": "知乎 - 有问题，就会有答案",
    "data_draft_cover": "https://pic.example.com/cover.jpg"
  }
}
```

- `url`：卡片链接地址（必填）
- `data_draft_title`：卡片标题
- `data_draft_cover`：封面图 URL，无封面时可为空字符串 `""` 或省略
- `data_content_type`、`data_content_id`：内容类型与 ID（由链接解析接口返回；外链可能无此字段）

---

## 6. 转换产出结构

转换完成后，应产出如下 JSON 结构：

### 6.1 提问

```json
{
  "type": "question",
  "title": "如何系统学习前端开发？",
  "body": "<p>问题背景与补充说明...</p>"
}
```

### 6.2 想法

```json
{
  "type": "pin",
  "title": "可选标题",
  "body": "<p>正文内容 <a class=\"hash_tag\" data-topic-name=\"#话题名#\" data-topic-id=\"19550286\">#话题名#</a></p>",
  "media": { "medias": [] },
  "linkCard": null
}
```

### 6.3 文章

```json
{
  "type": "article",
  "title": "文章标题",
  "body": "<h2>章节一</h2><p>正文...</p>"
}
```

> `config` 字段由 [`config.md`](./config.md) 规则单独生成，不在本文档范围内。
