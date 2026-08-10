# Zhihu Publisher Skill

将用户内容转换为知乎适配格式，生成本地浏览器预览，并在用户确认后进入发布流程。支持文章（`article`）、提问（`question`）和想法（`pin`）。

## 安装

发布到 Skill 注册中心后，可以使用注册中心提供的标识安装，例如：

```bash
npx skills add zhihu/zhihu-publisher -g
```

图片上传依赖的安装引导见 [`reference/zhihu-mediacloud-uploader.md`](./reference/zhihu-mediacloud-uploader.md)。安装后，上传参数、凭证、MCP 配置、错误处理和上传结果字段均以 `zhihu-mediacloud-uploader` skill 自己的文档为准。

## 授权与凭证

首次使用前需要准备知乎 OpenAPI 凭证：

1. 从知乎个人主页 URL 获取 `ZHIHU_OPENAPI_APP_KEY`。
2. 前往知乎开放平台 `https://www.zhihu.com/playground/zhihu-publisher` 申请 `ZHIHU_OPENAPI_APP_SECRET`。
3. 将这两项凭证提供给 Agent，并要求 Agent 保存，供发布和媒体上传等多个知乎 OpenAPI skill 复用。
4. 如果已经为其他知乎 OpenAPI skill 配置过凭证，可以直接复用，无需重复配置。


## 使用方式

安装后直接向 Agent 描述目标，例如：

- “把这篇 Markdown 转成知乎文章并生成预览。”
- “把这段内容和图片发成知乎想法。”
- “先整理成知乎提问格式，不要发布。”
- “预览没问题，确认发布。”

完整流程：

0. 最先检查上传类型：只允许上传图片；遇到视频时提示暂不支持，停止后续动作并等待用户移除视频后重新提交。
1. 确认发布形态。
2. 将用户原始信息整理为 `./.zhihu-publish-output/draft/latest-draft.md`，并写入同次时间戳草稿。
3. 遇到本地图片或需要转存的公开图片 URL 时，先确保已安装 `zhihu-mediacloud-uploader`，再按该 skill 文档执行上传。
4. 从 draft 生成知乎适配结构化结果。
5. 生成本地浏览器预览；用户提供的内容图片按原始来源展示，本地图片使用本地文件 URI，网络图片直接使用用户提供的原始 HTTP(S) URL。生成后优先调用系统默认浏览器打开，不使用 Cursor `open_resource` 打开源码代替预览；浏览器无法打开时才降级提供本地文件链接。
6. 等待用户明确确认。
7. 进入发布流程。

## 图片上传依赖

首次需要上传时，若尚未安装 `zhihu-mediacloud-uploader`，按 [`reference/zhihu-mediacloud-uploader.md`](./reference/zhihu-mediacloud-uploader.md) 安装或启用该依赖 skill。安装后加载 `zhihu-mediacloud-uploader` 的 `SKILL.md`，上传工具选择、参数、凭证配置、MCP 初始化、返回字段和错误处理均以该 skill 及其 `references/` 文档为准。

当前发布文章、提问和想法的流程只允许上传图片，不得使用 `zhihu-mediacloud-uploader` 或其他上传能力上传视频。请求中含需要上传或随内容发布的视频时，Agent 必须提示“当前知乎发布流程暂不支持视频，请移除视频后重新提交。”并立即停止，不得继续后续发布步骤。

## 本地产物

运行产物默认写入执行 Skill 时的当前工作目录，不写入用户主目录：

产物按固定链路派生：

```text
用户输入 -> draft/latest-draft.md -> validate/latest.json -> preview/latest.html -> 用户确认 -> publish/latest-request.json -> publish/latest-response.json
```

```text
./.zhihu-publish-output/
├── draft/
│   ├── latest-draft.md
│   └── YYYY-MM-DD-HHmm-draft.md
├── validate/
│   ├── latest.json
│   └── YYYY-MM-DD-HHmm-result.json
├── preview/
│   ├── latest.html
│   └── YYYY-MM-DD-HHmm-preview.html
└── publish/
    ├── latest-request.json
    ├── latest-response.json
    ├── YYYY-MM-DD-HHmm-request.json
    └── YYYY-MM-DD-HHmm-response.json
```

- `./.zhihu-publish-output/draft/latest-draft.md`：用户原始发布意图和素材整理后的草稿，是后续阶段的事实源。
- `./.zhihu-publish-output/validate/latest.json`：从 draft 生成的知乎适配结构化结果，也是发布阶段的输入。
- `./.zhihu-publish-output/preview/latest.html`：仅供本地浏览器核对，不作为发布输入。
- `./.zhihu-publish-output/publish/latest-request.json`：发送给 publish OpenAPI 的请求体。
- `./.zhihu-publish-output/publish/latest-response.json`：publish OpenAPI 发布响应。

上游产物变化时，下游产物必须重新生成：draft 变化会使 validate、preview、publish 全部过期；validate 变化会使 preview 和 publish 过期；preview 变化后必须重新等待用户确认。

用户发现预览内容不对时，只修改 draft；修改 draft 时结合用户需求和 `zhihu-validate` 的说明文档，再重新 validate 和 preview。不要直接手改 validate JSON、preview HTML 或 publish request。

用户确认预览前，Skill 不会进入发布步骤。

### Git 防误提交

如果运行 skill 的当前工作目录位于 Git 仓库中，首次写入 `./.zhihu-publish-output/` 前，Agent 应检查该目录是否已被 Git ignore。

- 已被 ignore：直接继续。
- 未被 ignore：优先把相对仓库根目录的产物路径写入 `.git/info/exclude`，不要默认修改用户项目的 `.gitignore`。
- 无法写入 `.git/info/exclude` 时，Agent 应提示用户不要提交 `./.zhihu-publish-output/`。

该目录可能包含未发布正文、预览、请求体和响应结果；设计上不应包含 `ZHIHU_OPENAPI_APP_SECRET`。
