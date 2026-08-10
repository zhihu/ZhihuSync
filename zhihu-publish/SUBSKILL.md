---
name: zhihu-publish
description: Publish validated and preview-confirmed Zhihu content as pin, article, or question through the publish OpenAPI endpoint. Use after zhihu-validate has produced ./.zhihu-publish-output/validate/latest.json, zhihu-preview has produced ./.zhihu-publish-output/preview/latest.html, and the user explicitly says 发布、确认发布、预览没问题发布, or send to Zhihu.
---

# Zhihu Publish

发布用户已校验、已预览并已明确确认的知乎内容。本 skill 读取 validate 产物，按 `pin` / `article` / `question` 类型规范组装 publish OpenAPI HTTP 请求，生成并执行 `curl` 命令，然后把发布结果返回给用户。

## 触发边界

仅在同时满足以下条件时执行：

1. 用户已经通过 `zhihu-validate` 生成 `./.zhihu-publish-output/validate/latest.json`。
2. 用户已经通过 `zhihu-preview` 生成并核对 `./.zhihu-publish-output/preview/latest.html`。
3. 当前或最近一条用户消息明确表达“确认发布 / 发布到知乎 / 预览没问题，发布”等发布指令。

用户没有明确确认预览时，停止并要求用户先确认预览；不要发送 HTTP 请求。

## 输入与产物

默认输入：

```text
./.zhihu-publish-output/validate/latest.json
./.zhihu-publish-output/preview/latest.html
```

发布阶段产物默认写入当前工作目录：

```text
./.zhihu-publish-output/publish/
├── latest-request.json
├── latest-response.json
├── YYYY-MM-DD-HHmm-request.json
└── YYYY-MM-DD-HHmm-response.json
```

用户显式指定输入、输出或服务地址时，以用户指定为准。

## 发布字段来源与变更边界

`./.zhihu-publish-output/validate/latest.json` 是所有无需发布前交互确认字段的唯一事实源。validate 阶段已经完成这些字段的转换与校验；publish 阶段只负责读取结果、按 OpenAPI 协议映射字段并发送请求，不得再次校验或修正这些字段。

需要发布前交互确认的字段是例外。它们不直接沿用 `latest.config`，必须按对应类型规范在发布阶段与用户交互，并以用户本次明确确认的选择组装 request；只有用户明确接受已经展示的默认项时，才能使用该默认值：

| 类型 | 无需交互确认、以 validate 为准 | 发布阶段交互确认后确定 |
|---|---|---|
| `pin` | `type`、`title`、`body`、`media` / `images`、`linkCard` | `comment_permission`、`ring` |
| `article` | `type`、`title`、`body` | `comment_permission`、`topics`、`creation_statement`、`table_of_contents_enabled` |
| `question` | `type`、`title`、`body` | `topics` |

- 不得修改或覆盖 `validate/latest.json`；交互确认结果只写入 publish request。
- 不得根据 draft、preview、对话上下文或外部数据修改无需交互确认的字段。
- 从 validate 映射到 request 的无需交互确认字段，必须直接使用 JSON 反序列化后的值；除对应类型规范明确规定的字段映射或回退外，不得增删、替换、补全、裁剪、规范化、去重、重排或使用回退值。OpenAPI 固定 envelope 字段、鉴权信息和发布阶段交互确认字段不受此限制。
- 只允许检查输入文件是否存在、是否为合法 JSON，以及 `type` 是否为支持的类型；这些检查只用于读取和路由，不构成对无需交互确认字段的再次校验。
- **不得校验图片可用性。** 图片不是发布阶段交互确认字段。不得对图片发起 `HEAD` / `GET` 请求，不得下载图片，不得检查 DNS、HTTP 状态、域名、URL 格式、文件格式、尺寸、本地文件或媒体云状态，也不得重新上传图片。
- validate 中的图片条目和顺序必须按对应类型规范映射。不得根据 `media_key` / `mediaKey` 拼接或替换 URL，不得因为图片当前不可访问、缺少某个推测字段或不符合 publish 阶段的额外判断而停止发布。
- 类型规范和公共 HTTP 规范用于确定字段映射、交互确认项、request envelope、鉴权、curl 和响应处理。若参考文档中的前置校验、兼容转换、默认填充或字段修正规则会改变无需交互确认字段，以本节为准；发布阶段交互确认字段仍严格执行对应类型规范。
- OpenAPI 因无需交互确认字段返回失败时，保存并原样报告响应；不得在 publish 阶段修改这些字段后自动重试。需要修改时，必须回到 draft -> validate -> preview 流程。

## 工作流程

1. 按以下规则做凭证预检查；这是进入发布请求组装和 curl 执行前的第一步：
   - 先检查当前进程环境变量 `ZHIHU_OPENAPI_APP_KEY` / `ZHIHU_OPENAPI_APP_SECRET` 是否完整。
   - 再检查共享凭证文件 `~/.zhihu/openapi-credentials.json` 是否存在且包含完整凭证。
   - 已有完整且一致的凭证时，继续后续步骤。
   - 检查和汇报凭证状态时，只说明来源、完整性和一致性；不得输出、复述或掩码展示 `ZHIHU_OPENAPI_APP_SECRET` 的任何原始内容。
   - 凭证缺失、来源不一致、用户不清楚如何获取、用户直接提供凭证、或需要写入共享文件时，立即加载根目录 `../reference/auth-info.md`，按其中初始化流程处理；处理完成前不要生成请求或发送 curl。
2. 确认 `latest.json` 和 `latest.html` 均存在；`latest.html` 只用于确认链路，不作为发布输入。
3. 用结构化 JSON 解析 `./.zhihu-publish-output/validate/latest.json`，不要用字符串拼接解析 JSON。解析只用于读取和映射，不得改变无需交互确认的字段。
4. 根据 `latest.type` 选择并读取类型规范；不得借此对无需交互确认的字段做二次校验或修正：
   - `pin`：读取 `reference/publish-pin.md`
   - `article`：读取 `reference/publish-article.md`
   - `question`：读取 `reference/publish-question.md`
   - 其他类型：停止发布并说明不支持
5. 按选中的类型规范完成发布前交互确认，再读取 `reference/publish-openapi.md`，按公共 HTTP 规范和类型规范组装 request body。无需交互确认的字段遵守「发布字段来源与变更边界」，交互确认字段以用户本次确认结果为准。
6. 将 request body 写入 `./.zhihu-publish-output/publish/latest-request.json` 与同次时间戳历史文件。request 必须是合法 JSON，只序列化一次。
7. 按 `reference/publish-openapi.md` 生成等价 `curl` 命令并执行 `POST {BASE_URL}/openapi/publish`。请求必须由 `curl` 发出，不能只展示命令。
8. 将 response body 写入 `latest-response.json` 与同次时间戳历史文件。
9. 解析 response JSON，并按 `reference/publish-openapi.md` 的 Response 判定规则确认发布成功或失败；不要只根据 HTTP 状态码判断。
10. 向用户返回 HTTP 状态、接口 `status` / `msg`、成功时的 `data.content_token` 和 `data.url`，以及本地 request / response 文件路径。

## 类型规范

发布类型只由 `./.zhihu-publish-output/validate/latest.json` 中的 `type` 决定：

| `latest.type` | 必读规范 | 说明 |
|---|---|---|
| `pin` | `reference/publish-pin.md` | 想法发布，处理正文、独立图片、链接卡片、圈子和评论权限 |
| `article` | `reference/publish-article.md` | 文章发布，处理标题、正文、话题、目录和创作声明 |
| `question` | `reference/publish-question.md` | 问题发布，处理问题标题、问题说明和可选话题 |

所有类型都必须同时读取 `reference/publish-openapi.md`，使用同一套 endpoint、headers、签名和 curl 执行规则。

## 返回用户

成功时返回：

- HTTP 状态码
- 响应中的 `status` 和 `msg`
- 内容形态
- `content_token`
- 知乎 URL
- 本地响应文件路径

失败时返回：

- HTTP 状态码
- 响应中的 `status` 和 `msg`
- 本地请求 / 响应文件路径
- 可执行的下一步，例如补齐话题 token、重新预览或检查鉴权配置
