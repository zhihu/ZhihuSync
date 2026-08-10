---
name: zhihu-publisher
description: >-
  Orchestrate Zhihu content publishing by running draft capture, image upload,
  validate, preview, user confirmation, and publish stages in order. Only images
  may be uploaded; video upload is not supported. Use when
  the user asks to publish content to Zhihu, convert or adapt content for Zhihu,
  generate a Zhihu preview, validate Zhihu-ready content, continue after preview
  confirmation, handle Zhihu article/question/pin publishing workflows, or asks
  what zhihu-publisher is, how to use it, first-time setup, authorization,
  credentials, zhihu OpenAPI app_key/app_secret configuration, skill version, or
  update availability.
  Trigger on requests such as 发布到知乎, 发成知乎文章, 发成想法, 发起提问, 生成知乎预览,
  校验知乎发布内容, 预览没问题, 确认发布, zhihu-publisher 是什么, 怎么用,
  首次使用, 授权, 配置凭证, app_key, 检查更新, 检查版本, 更新
  zhihu-publisher, 升级 zhihu-publisher.
license: MIT
metadata:
  author: zhihu
  version: "0.1.10"
---

# Zhihu Publisher

知乎发布流程的总编排入口。具体转换、预览和发布规则由子 skill 负责；本文件只规定执行顺序、阶段边界和关键产物路径。

## 介绍

当用户询问 `zhihu-publisher` 是什么、怎么用、首次使用、授权或凭证配置时：

- 先读取 `README.md`，基于其中内容向用户介绍本 skill 的能力、安装方式、授权说明, 使用方式、发布链路和本地产物。
- 只做介绍、首次使用说明和授权引导，不继续生成 draft、validate、preview 或 publish。

## 会话首次版本检查

每个会话首次加载本 skill 后，或当用户询问 `zhihu-publisher` 是否有新版本、要求检查更新、检查版本、更新或升级时：

- 立即读取 `reference/update.md`，按其中流程访问版本接口，并将同名 skill 的接口版本与本地 `SKILL.md` 中的 `metadata.version` 比较。
- 每个会话只自动检查一次；同一会话内只有用户再次明确询问更新、版本、升级，或遇到明显像旧版本导致的问题时，才重复检查。
- 自动检查发现新版本时，先提示当前版本、接口最新版本、更新建议和重启要求，并等待用户选择更新或暂不更新；用户选择前不要继续确认内容形态、整理 draft、validate、preview、上传媒体或 publish。
- 用户选择暂不更新或继续当前任务时，可以继续后续流程，但必须说明当前会话仍使用本地已加载版本。
- 用户明确询问版本或更新时，只返回版本判断、更新建议和重启要求；不要继续确认内容形态、整理 draft、validate、preview、上传媒体或 publish。
- 发现新版本时，只提示用户确认后再更新；不要静默自动更新 skill。
- 无法访问版本接口或无法解析版本时，说明无法检查的原因，不要猜测是否有新版本。

## 依赖 Skill

- `zhihu/zhihu-mediacloud-uploader`：仅用于将本发布流程支持的本地图片或公开图片 URL 转存到知乎媒体云，返回发布所需的 `media_key` 和图片信息。
- 安装或启用引导见 `reference/zhihu-mediacloud-uploader.md`。
- 上传参数、凭证配置、MCP 配置、错误处理和上传结果字段说明均以 `zhihu-mediacloud-uploader` 的 `SKILL.md` 及其 `references/` 文档为准；本 skill 不复制这些细节。
- 即使该依赖 skill 支持视频或其他文件，本 skill 也只能用它上传图片，不得使用其视频或通用文件上传能力。

## 启动前检查

完成下文工作流程第 0 步的无素材请求分流后，在确认内容形态、整理 draft、上传媒体或发布前，先完成以下检查：

0. 如果本会话首次加载本 skill 后尚未完成版本检查，先执行上文“会话首次版本检查”。自动检查失败时简要说明原因并继续后续启动检查；自动检查发现新版本时，先等待用户选择更新或暂不更新。用户明确询问版本或更新时，完成版本检查后停止，不做凭证、依赖或发布流程检查。
1. 检查知乎 OpenAPI 凭证来源。
   - 先检查当前进程环境变量 `ZHIHU_OPENAPI_APP_KEY` / `ZHIHU_OPENAPI_APP_SECRET` 是否完整。
   - 再检查共享凭证文件 `~/.zhihu/openapi-credentials.json` 是否存在且包含完整凭证。
   - 任一来源能提供完整凭证且来源之间不存在冲突时，继续后续流程；凭证权限和读取优先级仍由 `zhihu-mediacloud-uploader` 或 `reference/auth-info.md` 在实际上传/发布前检查。
   - 检查和汇报凭证状态时，只说明来源、完整性和一致性；不得输出、复述或掩码展示 `ZHIHU_OPENAPI_APP_SECRET` 的任何原始内容。
   - 凭证缺失、来源不一致、用户不清楚如何获取、用户直接提供凭证、或需要写入共享文件时，立即读取 `reference/auth-info.md`，按其中初始化流程处理。
   - 用户暂不配置凭证时，停止当前流程；不得继续确认内容形态、整理 draft、validate、preview、上传媒体或发布。
   - 不要解析其他 skill 的 MCP 配置文件来获取凭证；多个知乎 OpenAPI skill 复用 `ZHIHU_OPENAPI_APP_KEY` / `ZHIHU_OPENAPI_APP_SECRET` 和 `~/.zhihu/openapi-credentials.json`。
2. 检查当前 Agent 是否已能加载 `zhihu-mediacloud-uploader` skill。
   - 已能加载时，继续后续流程；需要上传媒体时再立即加载该 skill 的 `SKILL.md` 并按其文档执行。
   - 不能加载时，立即读取 `reference/zhihu-mediacloud-uploader.md`，按其中安装流程安装或引导用户安装。
   - 安装或依赖 skill 初始化流程要求重启 Agent 时，停止当前发布流程，提示用户重启后重新发起发布或上传请求；不要继续 draft、validate、preview 或 publish。

## 本地产物目录

运行产物默认写入执行 Skill 时的当前工作目录，**不写入用户主目录**：

产物依赖链：

```text
用户输入
  -> draft/latest-draft.md
  -> validate/latest.json
  -> preview/latest.html
  -> 用户确认
  -> publish/latest-request.json
  -> publish/latest-response.json
```

依赖关系：

| 产物 | 生成阶段 | 依赖输入 | 下游用途 |
|---|---|---|---|
| `draft/latest-draft.md` | draft | 用户原始信息、发布意图、内容形态、媒体引用和发布要求 | validate 的唯一默认事实源 |
| `validate/latest.json` | validate | `draft/latest-draft.md`，以及必要时 `zhihu-mediacloud-uploader` 的上传结果 | preview 和 publish 的结构化输入 |
| `preview/latest.html` | preview | `validate/latest.json`；存在用户提供的内容图片时，额外读取 `draft/latest-draft.md` 中的原始图片引用，本地图片还需读取对应文件 | 只供用户核对；图片使用用户提供的原始来源展示：本地图片使用本地文件地址，网络图片使用原始网络 URL；发布时仍只使用 validate 结果 |
| `publish/latest-request.json` | publish | `validate/latest.json`、用户确认、发布凭证和 publish OpenAPI 规则 | `curl` 请求体 |
| `publish/latest-response.json` | publish | `publish/latest-request.json` 和 publish OpenAPI HTTP 响应 | 返回给用户的发布结果记录 |

失效规则：

- `draft/latest-draft.md` 发生变化时，`validate/`、`preview/`、`publish/` 下游产物全部视为过期，必须重新生成。
- `validate/latest.json` 发生变化时，`preview/latest.html` 和 `publish/` 下游产物视为过期，必须重新预览并重新确认。
- 已上传的本地图片路径或文件内容发生变化时，旧 validate、preview 和 publish 产物全部视为过期；必须按最新本地文件重新上传、validate 和 preview。原始本地图片不存在或不可读时不得生成新预览。
- 用户发现 `preview/latest.html` 内容不对时，不直接修改 preview 或 validate 产物；必须先修改 `draft/latest-draft.md`，再重新生成 validate 和 preview。
- `preview/latest.html` 重新生成后必须重新等待用户确认；确认前不得发布。
- `publish/latest-response.json` 只对应同目录下同次生成的 request；不要用旧响应代表新的 request。

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

- 每次生成同时写入带时间戳的历史文件，并覆盖对应 `latest-*` 固定入口。
- 带时间戳文件用于历史追踪；`latest-*` 文件用于阶段间传递。
- 后续阶段默认只读取自己的直接上游产物，不跨阶段读取更早产物。唯一例外是 preview 可读取 `draft/latest-draft.md`，但只用于把用户提供的内容图片映射回原始来源：本地图片使用原始本地文件地址，网络图片使用用户提供的原始 URL；不得从 draft 重新生成标题、正文或其他发布字段。
- 发布阶段默认写入 `./.zhihu-publish-output/publish/latest-request.json` / `./.zhihu-publish-output/publish/latest-response.json`，并写入同次时间戳历史文件。
- 用户显式指定输出路径时，以用户指定路径为准。

Git 防误提交规则：

- 首次写入产物目录前，检查当前工作目录是否位于 Git worktree 中；不在 Git worktree 中时直接继续。
- 如果位于 Git worktree 中，检查产物目录是否已被 Git ignore。默认产物目录为当前工作目录下的 `./.zhihu-publish-output/`；用户显式指定输出路径时，检查用户指定的输出目录。
- 如果尚未 ignore，优先把该产物目录追加到当前 worktree 的 `.git/info/exclude`，不要默认修改用户项目的 `.gitignore`。`.git/info/exclude` 是本机私有忽略规则，不会进入提交。
- 写入 `.git/info/exclude` 时使用相对仓库根目录的路径，路径分隔符使用 `/`。例如当前工作目录就是仓库根目录时写入 `/.zhihu-publish-output/`；当前工作目录是仓库内 `docs/` 时写入 `/docs/.zhihu-publish-output/`。
- 如果无法写入 `.git/info/exclude`，继续流程前提示用户产物目录可能被 `git add .` 收入提交，并明确说明不要提交该目录。
- 不要把 `./.zhihu-publish-output/` 加入发布 request；该目录只用于本地草稿、校验、预览、请求和响应产物。

## 工作流程

按以下顺序执行，不要跳步：

进入步骤 0 前，先检查用户是否提供了需要上传或随内容发布的视频。发现视频时，只回复：`当前知乎发布流程暂不支持视频，请移除视频后重新提交。` 然后立即停止；不得执行版本或凭证检查、创建或修改 draft、加载上传依赖、上传、validate、preview 或 publish，也不得调用 `zhihu-mediacloud-uploader` 或其他上传能力处理该视频。

0. **处理无素材发布请求**
   - 用户要求发布文章、提问或想法，但既未提供可直接发布的标题、正文、媒体、链接或明确引用的现有草稿，也未明确要求模型创作内容时，先直接告诉用户当前没有提供要发布的内容。
   - 默认只请用户提供内容，不主动提供“由我为你生成内容”这一选项。使用清晰提示，例如：`你还没有提供要发布的内容。不建议完全由 AI 生成正文——平台侧的 AI 识别可能影响内容分发，建议以你的原创内容为主。请把要发布的标题、正文、图片或链接发给我。` 提示后停止，等待用户提交内容；在此之前不要检查凭证或依赖、推断内容形态、创建 draft、上传媒体、validate、preview 或 publish。
   - 用户只给出主题、受众或一句创作方向，但没有给出可直接发布的内容，也没有使用“写一篇”“生成内容”等明确创作指令时，仍按无素材请求处理。用户明确要求模型写作或生成时，视为已授权生成，不要反复劝阻或要求再次确认；但生成前必须先提示一次：不建议完全由 AI 生成正文，AI 识别可能影响内容分发，文章形态建议在创作声明中声明 AI 辅助创作。提示后直接继续生成。
   - 用户选择自己提供时，等待其提交内容；收到内容后从本步骤重新检查。用户选择由模型生成时，只根据用户已给出的内容形态、主题、意图和上下文创作；信息不足时只询问完成内容所必需的信息。
   - 为想法生成内容时，模型生成授权不包含话题生成授权。除非用户明确要求生成或添加知乎话题、标签或 `#话题#`，否则不要询问话题、推断话题、创建话题或在正文中插入话题；仅仅指定内容主题不等于要求生成知乎话题。
   - 用户正在继续已有 draft、validate、preview 或 publish 流程，或者明确引用了可读取的现有内容时，不按无素材新请求处理。

1. **启动前检查**
   - 先执行上文“启动前检查”。
   - 本会话首次加载本 skill 时，按 `reference/update.md` 自动检查一次接口版本；同一会话不重复自动检查。发现新版本时，先等待用户选择更新或暂不更新；用户选择前不继续发布流程。自动检查失败且本次不是用户主动要求检查更新时，说明原因后继续后续检查。
   - 如果用户本次只是在询问版本、更新或升级，按 `reference/update.md` 完成版本检查后停止，不继续发布流程。
   - 环境变量和共享凭证文件都不能提供完整凭证，或两者完整但不一致时，先按 `reference/auth-info.md` 提示用户初始化或选择来源；用户暂不配置凭证时，停止当前流程，不得继续 draft、validate、preview、上传媒体或发布。
   - 凭证检查通过后，再检查 `zhihu-mediacloud-uploader`；依赖 skill 需要安装、初始化或重启 Agent 时，按检查结果停止后续流程。

2. **确认内容形态**
   - 支持 `article`（文章）、`question`（提问）、`pin`（想法）。
   - 用户明确指定形态时，按用户指定执行。
   - 用户未指定形态时，先根据内容推断并推荐一个最合适的形态，说明推荐结果并询问用户是否确认，同时允许用户改选文章、提问或想法。
   - 用户确认前不要生成结构化结果、预览或上传媒体。

3. **整理发布草稿**
   - 写入 `./.zhihu-publish-output/` 前，先执行上文“Git 防误提交规则”。
   - 将用户提供的原始信息、发布意图、确认后的内容形态、标题意图、正文、媒体引用、链接、话题和其他发布要求整理为 Markdown 草稿。
   - 忠实保留用户提供的标题、正文、事实、观点、结构和语气。用户要求发布、转换或生成预览，不等于授权润色或改写；任何删减、精简、扩写、重排、合并、拆分或语义改写都必须先获得用户对具体动作和字段的明确允许。
   - 想法话题只记录用户明确提供或确认的话题；用户仅授权模型生成想法内容时，不得把该授权扩大为生成话题。用户未明确要求话题时，不询问、不推断、不创建，也不在正文中插入话题。
   - 草稿默认写入 `./.zhihu-publish-output/draft/YYYY-MM-DD-HHmm-draft.md`，并覆盖 `./.zhihu-publish-output/draft/latest-draft.md`。
   - 草稿只承载用户意图和原始材料，不生成知乎 HTML，不发起发布请求。
   - 本地图片路径、公开图片 URL、图片说明和用户给出的配置要求都应保留在草稿中，供 validate 阶段提取。
   - 用户提供的内容图片必须在 draft 中按出现顺序保留准确原始引用：本地图片保留传给 uploader 的绝对 `file_path`，网络图片保留用户提供的原始 `http://` 或 `https://` URL。不得用上传后 URL 替换任一原始引用；该顺序供 preview 与 validate 图片做一一映射。

4. **生成知乎适配结构化结果**
   - 阅读并执行 `zhihu-validate/SUBSKILL.md`。
   - 默认输入 `./.zhihu-publish-output/draft/latest-draft.md`。
   - 转换或上传媒体前，按 `zhihu-validate/reference/conversion.md` 执行标题与正文长度预检。发现超出当前内容形态的上限时，说明实际长度和上限，向用户提供该文档规定的选项，然后停止并等待选择；不得静默截断、精简、切换内容形态或拆分内容。
   - 用户选择自行修改时，等待用户提交修改后的内容；用户选择由模型精简、切换为文章或拆分时，先按用户选择更新 draft，并写入新的时间戳草稿，再重新执行长度预检和 validate。
   - 拆分出的每份内容必须作为独立发布项，分别执行内容形态确认、draft、validate、preview 和用户确认；一份预览的确认不得代表其他拆分项。
   - 输入含本地图片，或公开图片 URL 需要转存到知乎时，读取 `reference/zhihu-mediacloud-uploader.md` 确保依赖 skill 已安装。
   - 依赖安装或确认可加载后，加载并执行 `zhihu-mediacloud-uploader` 的 `SKILL.md`，但只允许用它上传图片；不要在本 skill 中复制或改写其上传参数、凭证、MCP、错误处理和响应字段规则。
   - 依赖 skill 要求重启 Agent 时，停止后续转换、预览和发布，提示用户重启后重新发起请求。
   - 上传失败时停止后续转换、预览和发布，不得将本地路径写入发布内容，也不得编造媒体上传结果。
   - validate 的模型输出只能先作为候选文件；必须由 `zhihu-validate/scripts/finalize_validate_json.py` 成功解析、检查并提交后，才能把新的 `latest.json` 交给 preview。脚本失败时不得覆盖旧产物或继续后续阶段。
   - 输出 `./.zhihu-publish-output/validate/latest.json`（及同次时间戳历史文件）。

5. **生成本地预览**
   - 阅读并执行 `zhihu-preview/SUBSKILL.md`。
   - 输入 `./.zhihu-publish-output/validate/latest.json`。
   - 如果本次发布包含用户提供的内容图片，额外读取 `./.zhihu-publish-output/draft/latest-draft.md` 中的原始图片引用，并与 validate 图片按顺序一一映射。只在 preview HTML 中将本地图片替换为原始本地文件 URI，将网络图片替换为用户提供的原始 `http://` 或 `https://` URL；不得使用其上传后 URL、重定向后的 URL 或其他替代地址。
   - 原始来源映射不得修改 `validate/latest.json`；发布仍使用其中的上传后知乎媒体 URL 和媒体属性。
   - 输出 `./.zhihu-publish-output/preview/latest.html`（及同次时间戳历史文件）。

6. **等待用户确认**
   - 严格执行 `zhihu-preview/SUBSKILL.md` 的「向用户交付预览」规则：先确认 `latest.html` 已生成，再优先调用平台命令使用系统默认浏览器打开本地 HTML。不得使用 `open_resource` 或其他只在代码编辑器中打开本地文件的工具代替浏览器预览。
   - 除非已有可验证证据证明规定的平台命令不存在、当前环境明确没有用户桌面能力，或用户拒绝所需授权，否则必须实际执行一次对应平台的外部浏览器命令。不得因为 Agent 无法观察外部窗口、宿主提供了内置浏览器或推测命令可能失败而跳过外部打开尝试。
   - Windows 必须在同一个 PowerShell 进程中先用 `Test-Path -LiteralPath` 和 `-PathType Leaf` 验证 Windows 绝对路径，再用 `Start-Process -ErrorAction Stop` 打开预览；当前终端是 Bash 时也必须从 Bash 调用 `powershell.exe` 执行同一段 PowerShell 逻辑，不得改用 `cmd /c start`、`cmd //c start`、`explorer.exe` 或其他替代命令。macOS 只能使用 `open`，Linux 只能使用 `xdg-open`，不得自行替换平台命令。必须保留平台命令的原始退出状态，不得使用 `|| echo ...` 等会把失败状态改写为成功的包装。
   - 系统默认浏览器打开命令成功后，不得再调用宿主内置浏览器、WebView 或浏览器控制工具打开同一预览；外部系统浏览器与宿主内置浏览器的打开路径必须互斥。
   - 外部打开命令退出状态为 0 且没有平台命令异常时，必须视为打开成功；Agent 无法观察外部浏览器窗口、命令异步返回或未获得窗口截图都不构成失败。降级到内置浏览器前，必须记录至少一项可验证证据：规定的平台命令确认不存在、原始退出状态非 0、命令抛出异常、宿主明确报告没有用户桌面能力，或用户拒绝所需授权；没有这些证据时不得调用内置浏览器。内置浏览器不可用、打开失败或用户拒绝所需授权时，才提供使用绝对路径的可点击 Markdown 文件链接，并明确提示部分宿主可能会显示 HTML 源码。默认不得启动本地 HTTP 服务。
   - 调用内置浏览器前，必须先向用户发送可见提示，说明系统默认浏览器未能打开、简要说明失败原因，并明确告知将改用内置浏览器；提示发送完成后才能执行内置浏览器打开动作。外部打开命令成功时不得发送该失败提示。
   - 浏览器打开成功或完成降级交付后立即停在确认阶段，等待用户明确确认；不要把“已生成预览”或“已打开预览”视为用户已经确认。
   - 用户发现预览内容不对或要求修改时，不要直接编辑 `./.zhihu-publish-output/preview/latest.html`、`./.zhihu-publish-output/validate/latest.json` 或发布请求文件。
   - 修改只能落到 draft：先结合用户的修改需求，重新阅读 `zhihu-validate/SUBSKILL.md` 以及必要的 `zhihu-validate/reference/conversion.md`、`zhihu-validate/reference/config.md`、`zhihu-validate/reference/code-languages.md`，再更新 `./.zhihu-publish-output/draft/latest-draft.md` 并写入新的时间戳草稿。
   - draft 修改应表达用户意图和可被 validate 规则稳定提取的源内容；如果用户需求无法被当前 validate 规则表达，应先说明限制，不要通过手改 validate JSON 或 preview HTML 绕过。
   - draft 更新后，重新运行 `zhihu-validate` 和 `zhihu-preview`，并再次等待用户确认。
   - 用户确认前，不要进入发布步骤。

7. **进入发布流程**
   - 用户确认后，阅读并执行 `zhihu-publish/SUBSKILL.md`。
   - 发布阶段读取 `./.zhihu-publish-output/validate/latest.json`。
   - 发布阶段先按 `reference/auth-info.md` 完成凭证检查，再按 `zhihu-publish/reference/publish-openapi.md` 和对应类型规范组装 publish OpenAPI HTTP 请求，用 `curl` 发出请求，并将请求和响应写入 `./.zhihu-publish-output/publish/`。

## 子 skill 职责

- `zhihu-validate/SUBSKILL.md`：生成知乎适配结构化结果。
- `zhihu-preview/SUBSKILL.md`：生成本地浏览器预览 HTML。
- `zhihu-publish/SUBSKILL.md`：用户确认后的发布流程。

关键产物：

- `./.zhihu-publish-output/draft/latest-draft.md`：用户原始发布意图和素材整理后的草稿，是后续阶段的事实源。
- `./.zhihu-publish-output/validate/latest.json`：发布适配结构化结果。
- `./.zhihu-publish-output/preview/latest.html`：本地预览页面，只用于核对。
- `./.zhihu-publish-output/publish/latest-request.json`：发送给 publish OpenAPI 的请求体。
- `./.zhihu-publish-output/publish/latest-response.json`：publish OpenAPI 发布响应。

## 关键约束

- 新发布请求没有可直接发布的内容且用户未明确授权模型生成时，必须先说明缺少内容并请用户提供，同时说明不建议完全由 AI 生成正文；默认不提供“由模型生成”这一选项。用户提交内容或明确要求生成前，不得执行凭证检查或任何发布阶段。
- 内容由 AI 生成或有 AI 辅助参与时，文章发布必须主动推荐创作声明 `ai_creation`，并说明不声明可能影响后续 AI 识别与内容分发；是否声明仍由用户决定，用户未明确选择时不得发送该字段。想法和提问的 publish OpenAPI 没有创作声明字段，只能在发布前口头提示，不得伪造、附加或用其他字段替代。
- 不要跳过形态确认。
- 不要跳过 draft 阶段；validate 默认只从 `draft/latest-draft.md` 提取本次发布内容。
- 未经用户明确允许，不得删减、精简、扩写、重排、合并、拆分或改写用户提供的内容；“发布”“转换”“生成预览”等请求本身不构成内容修改授权。
- 为用户生成想法时，不得把内容生成授权视为话题生成授权；只有用户明确要求生成或添加话题，或者明确提供、确认了具体话题，才能将话题写入 draft 和 `body`。内容主题本身不是知乎话题指令。
- 标题或正文超过当前内容形态的长度上限时，必须先提供选项并等待用户选择；未经用户选择，不得精简、切换形态、拆分、上传媒体或生成结构化结果。
- 需要上传图片时，不要绕过 `zhihu-mediacloud-uploader` 或直接使用本地路径生成 validate / publish 内容；仅 preview HTML 可按 `zhihu-preview` 规则使用本地图片文件 URI。
- 通过无素材请求分流后，必须先检查当前进程环境变量 `ZHIHU_OPENAPI_APP_KEY` / `ZHIHU_OPENAPI_APP_SECRET` 或共享凭证文件 `~/.zhihu/openapi-credentials.json` 是否能提供完整凭证；凭证检查通过后，再检查 `zhihu-mediacloud-uploader` 是否可加载。缺失时分别按 `reference/auth-info.md` 和 `reference/zhihu-mediacloud-uploader.md` 处理。
- 环境变量和共享凭证文件都不能提供完整凭证且用户暂不配置时，停止当前流程，不得继续 draft、validate、preview、上传媒体或发布；不要从其他 skill 的 MCP 配置中解析凭证。
- 各阶段按对应子 skill 执行，根 skill 不重复实现转换、预览或发布细则。
- 不要把预览 HTML 作为发布内容。
- 用户提供的内容图片在 preview HTML 中必须使用原始来源：本地图片使用原始本地文件 URI，网络图片使用用户提供的原始 `http://` 或 `https://` URL。不得使用上传后 URL、重定向后的 URL 或其他替代地址；该替换仅作用于 preview HTML，不得修改 validate 产物或发布输入。
- 生成预览后必须确认文件存在，并优先使用系统默认浏览器打开；除非已有可验证证据证明平台命令不存在、宿主明确没有用户桌面能力或用户拒绝授权，否则必须实际执行一次规定的外部浏览器命令，不得使用 `open_resource` 打开源码代替预览，也不得因无法观察外部窗口而跳过尝试。
- Windows 必须在同一个 PowerShell 进程中先用 `Test-Path -LiteralPath -PathType Leaf` 验证 Windows 绝对路径，再用 `Start-Process -ErrorAction Stop` 打开；当前终端是 Bash 时必须调用 `powershell.exe` 执行同一逻辑，不得替换为 `cmd /c start`、`cmd //c start`、`explorer.exe` 或其他命令。macOS 只能使用 `open`，Linux 只能使用 `xdg-open`。不得使用会掩盖原始退出状态的包装命令。
- 系统默认浏览器打开命令原始退出状态为 0 且无异常时，必须视为成功；Agent 无法观察外部窗口、命令异步返回或没有截图不能作为失败依据。成功后禁止再使用宿主内置浏览器、WebView 或浏览器控制工具打开同一预览。只有记录了规定的平台命令不存在、原始退出状态非 0、命令异常、宿主明确没有用户桌面能力或用户拒绝授权中的至少一项可验证证据，才允许尝试宿主内置浏览器；内置浏览器也不可用、打开失败或用户拒绝授权时，才提供指向 `preview/latest.html` 绝对路径的可点击 Markdown 文件链接，并提示宿主可能显示源码。默认不得启动本地 HTTP 服务。
- 外部系统浏览器打开失败并准备降级到内置浏览器时，必须先提示用户外部浏览器未能打开、简要说明失败原因，并告知即将改用内置浏览器；不得先打开内置浏览器再补充说明。
- 用户确认前，不要进入发布步骤。
- 用户发现预览不对或要求修改内容时，只能先更新 draft；更新 draft 时必须结合用户需求和 `zhihu-validate` 的说明文档，再重新生成 `latest.json` 并重新预览。
- 不要为了快速修正预览而直接编辑 `validate/latest.json`、`preview/latest.html` 或 `publish/latest-request.json`。
- 不支持的内容形态或配置项，应直接说明当前不支持。
- 本会话首次加载本 skill 时自动检查一次接口版本；用户询问版本、更新或升级时，也按 `reference/update.md` 检查并提示。不要静默自动更新，更新后必须提示用户重启 Agent。
- 除非用户显式指定其他路径，产物应写入当前工作目录下的 `./.zhihu-publish-output/`。
- 首次写入产物目录前必须执行 Git 防误提交检查；不要默认修改用户项目 `.gitignore`，优先使用 `.git/info/exclude`。
