---
name: zhihu-preview
description: >-
  Generate a local browser-preview HTML file from Zhihu-ready structured JSON,
  restoring every user-provided content image to its original source: local
  file URIs for local images and the exact original HTTP(S) URL for network
  images, while leaving validated publish data unchanged. Use after
  zhihu-validate has produced ./.zhihu-publish-output/validate/latest.json and
  before user confirmation.
---

# Zhihu Preview

读取 `./.zhihu-publish-output/validate/latest.json`，将其中的知乎适配内容转换为本地浏览器可打开的预览 HTML。存在用户提供的内容图片时，只为图片来源映射额外读取 `./.zhihu-publish-output/draft/latest-draft.md`：本地图片在 preview HTML 中使用原始本地文件 URI，网络图片使用用户提供的原始 `http://` 或 `https://` URL。本 skill 不展示发布配置，也不负责重新生成或发布内容。

## 使用时机

当 `zhihu-validate` 已生成结构化结果，用户需要核对知乎发布效果时使用本 skill。

## 输出路径

默认写入执行 Skill 时的当前工作目录，**不写入用户主目录**：

```text
./.zhihu-publish-output/preview/
├── latest.html                      # 固定读取入口，每次覆盖
└── YYYY-MM-DD-HHmm-preview.html     # 历史留存，每次新增
```

写入规则：

1. 目录不存在时先创建。
2. 使用默认路径时，生成完整 HTML 后先写入 `YYYY-MM-DD-HHmm-preview.html`，再写入 `latest.html`（覆盖旧 latest）。

## 工作流程

1. 读取 `./.zhihu-publish-output/validate/latest.json`。
   - 该文件必须是合法 JSON。
   - 不重新推断内容形态。
2. 检查 draft 中是否包含用户提供的内容图片。
   - 只为原始图片来源映射读取 `./.zhihu-publish-output/draft/latest-draft.md`；不得从 draft 读取或重建标题、正文、媒体、链接卡片或配置。
   - 按 `reference/preview.md` 将 draft 图片与 validate 中的对应图片按顺序一一映射。本地图片映射为原始本地文件 URI，网络图片映射为用户提供的原始 HTTP(S) URL。原始本地文件不存在、不可读，网络 URL 不是合法的绝对 HTTP(S) URL，或图片无法唯一映射时停止；不得用上传后 URL 兜底，也不得覆盖已有 `latest.html`。
3. 按 `reference/preview.md` 生成完整 HTML 文档。
   - 可以对知乎适配 HTML 做浏览器预览适配。
   - 只渲染输入 JSON 中的 `type`、`title`、`body`、`media`、`linkCard`。
   - 不渲染 `config`，也不修改输入 JSON 中的任何字段。
   - 用户提供的内容图片使用原始来源作为显示地址：本地图片使用原始本地文件 URI，网络图片使用用户提供的原始 HTTP(S) URL。公式图片、链接卡片封面等非内容图片继续使用 validate 中的地址。
4. 将预览文件写入本地产物目录（见上文「输出路径」）。
   - 不要把 `latest.html` 作为发布输入。
5. 按「向用户交付预览」规则优先使用系统默认浏览器打开预览，等待用户确认。

## 向用户交付预览

完成文件写入后，严格按以下顺序执行：

1. 在文件系统中确认 `latest.html` 存在且是文件。检查失败时报告预览生成失败，不得提供一个未经确认或不存在的链接。
2. 将 `latest.html` 解析为绝对路径；不得使用相对路径或 `~`。
3. 识别操作系统，并优先实际执行对应平台的外部浏览器命令。除非已有可验证证据证明规定的平台命令不存在、宿主明确报告当前环境没有用户桌面能力，或用户拒绝所需授权，否则必须执行一次规定命令；不得因为 Agent 无法观察外部窗口、宿主提供了内置浏览器或推测命令可能失败而跳过外部打开尝试。
   - macOS：必须使用 `open "/绝对路径/latest.html"`，不得改用其他命令。
   - Windows：必须在同一个 PowerShell 进程中依次执行路径验证和打开操作：`$p = "C:\\绝对路径\\latest.html"; if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw "Preview file not found" }; Start-Process -FilePath $p -ErrorAction Stop`。当前终端是 Bash 时，也必须调用 `powershell.exe -NoProfile -NonInteractive -Command` 执行等价的同一段 PowerShell 逻辑，并确保 `$p` 由 PowerShell 解析；不得改用 `cmd /c start`、`cmd //c start`、`explorer.exe` 或其他替代命令。
   - Linux：必须使用 `xdg-open "/绝对路径/latest.html"`，不得改用其他命令。
   - 当前宿主执行 GUI 命令需要用户授权时，先请求授权；不得绕过宿主权限机制。只有用户明确拒绝授权后，才能将其记录为未执行平台命令的降级证据。
   - 如果不执行平台命令，必须记录“平台命令确认不存在”“宿主明确报告没有用户桌面能力”或“用户拒绝授权”中的至少一项具体证据；没有证据时不得跳过。
4. 不得使用 `open_resource` 或其他只会在代码编辑器中打开本地文件的工具作为 HTML 预览手段。它们可以显示源码，但不能视为已向用户打开渲染后的预览。
5. 直接读取平台命令的原始退出状态和异常；不得追加 `|| echo ...`、无条件成功的后续命令或其他会掩盖原始退出状态的包装。原始退出状态为 0 且没有平台命令异常时，必须视为系统浏览器打开成功；Agent 无法观察外部浏览器窗口、命令异步返回或未获得窗口截图都不构成失败。告知用户预览已在默认浏览器中打开，然后请用户核对并明确确认；不得再调用宿主内置浏览器、WebView 或浏览器控制工具打开同一预览，也不要求用户再点击本地文件链接。外部系统浏览器与宿主内置浏览器的打开路径必须互斥。
6. 进入内置浏览器降级前，必须记录至少一项可验证证据：规定的平台命令确认不存在、平台命令原始退出状态非 0、命令抛出异常、宿主明确报告没有用户桌面能力，或用户拒绝所需授权。没有这些证据时不得进入本步骤；Agent 无法观察外部浏览器窗口、命令异步返回、未获得窗口截图、宿主提供了内置浏览器或推测外部命令可能失败均不属于降级证据。
   - 调用内置浏览器、WebView 或浏览器控制工具前，必须先向用户发送可见提示，说明系统默认浏览器未能打开、简要说明实际失败原因，并明确告知将改用内置浏览器。可以使用：`系统默认浏览器未能打开（原因：{实际失败原因}），将改用内置浏览器显示预览。`
   - 只有提示发送完成后，才能调用宿主提供的内置浏览器、WebView 或浏览器控制工具打开同一绝对路径（或等价的 `file:` URI）；不得先打开再补充提示。内置浏览器打开成功后，告知用户已通过内置浏览器打开预览，然后请用户核对并明确确认。
7. 仅当内置浏览器不可用、打开失败或用户拒绝所需授权时，才降级提供以下格式的可点击 Markdown 文件链接，并始终用 `<...>` 包裹链接目标，以兼容路径中的空格、中文和其他特殊字符：

   ```markdown
   [打开知乎发布预览](</绝对路径/.zhihu-publish-output/preview/latest.html>)
   ```

   降级时必须同时说明：某些宿主可能会把该链接作为源码文件在编辑器中打开，用户需要手动选择系统浏览器打开。可以在链接后附加纯文本绝对路径作为备用，但它不能替代可点击链接。
8. 默认不得为了交付预览启动本地 HTTP 服务。当前预览可能包含本地图片 `file:` URI，从 HTTP 页面加载这些图片可能被浏览器阻止；HTTP 服务还会引入端口和进程生命周期管理。
9. 系统默认浏览器或内置浏览器打开成功，或完成文件链接降级交付后，立即停止并等待用户明确确认。系统默认浏览器已经打开成功时不得继续执行任何内置浏览器打开动作；用户确认前不得进入发布流程。

## 输入

主要输入：`./.zhihu-publish-output/validate/latest.json`。

辅助输入：`./.zhihu-publish-output/draft/latest-draft.md`，仅在存在用户提供的内容图片时读取其原始本地路径或网络 URL。

输入结构：

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

`media` 兼容图片数组以及包含 `medias` 图片数组的对象；具体映射按 `reference/preview.md` 执行。

## 输出

```text
./.zhihu-publish-output/preview/latest.html
```

输出是本地浏览器预览页面，只用于用户核对。

## 边界

- 不修改 `./.zhihu-publish-output/validate/latest.json`。
- 不修改 `./.zhihu-publish-output/draft/latest-draft.md`；draft 只用于识别用户提供的内容图片及其原始来源。
- 用户提供的内容图片只在 preview HTML 中恢复原始来源：本地图片使用本地文件 URI，网络图片使用用户提供的原始 HTTP(S) URL；不得把这些预览地址写回 validate 或用于发布。
- 不生成第二份发布内容。
- 不发布内容。
- 不展示 `config` 中的发布配置，也不把配置说明写入预览 HTML。
- 不得在未确认 `latest.html` 存在时打开或交付预览；交付时必须优先按「向用户交付预览」规则调用系统默认浏览器，不得把 `open_resource` 打开源码视为预览成功。
- 除非已有可验证证据证明规定的平台命令不存在、宿主明确没有用户桌面能力或用户拒绝授权，否则必须实际执行一次规定的外部浏览器命令；不得基于推测或无法观察窗口而跳过。
- Windows 必须在同一个 PowerShell 进程中先用 `Test-Path -LiteralPath -PathType Leaf` 验证 Windows 绝对路径，再用 `Start-Process -ErrorAction Stop` 打开；当前终端是 Bash 时必须调用 `powershell.exe` 执行同一逻辑，不得替换为 `cmd /c start`、`cmd //c start`、`explorer.exe` 或其他命令。macOS 只能使用 `open`，Linux 只能使用 `xdg-open`，不得自行替换。不得用 `|| echo ...` 或其他包装掩盖平台命令的原始退出状态。
- 平台命令原始退出状态为 0 且无异常时，必须视为系统默认浏览器打开成功；不能因 Agent 看不到外部窗口、命令异步返回或没有截图而改判失败。
- 系统默认浏览器打开成功后，不得再使用宿主内置浏览器、WebView 或浏览器控制工具打开同一预览；外部系统浏览器与宿主内置浏览器不得同时打开。
- 只有记录了规定的平台命令不存在、原始退出状态非 0、命令异常、宿主明确没有用户桌面能力或用户拒绝授权中的至少一项可验证证据，才允许尝试宿主内置浏览器；没有证据时不得降级。只有内置浏览器也不可用、打开失败或用户拒绝所需授权时，才使用绝对路径 Markdown 链接作为最终降级入口。不得默认启动本地 HTTP 服务。
- 降级到内置浏览器前，必须先向用户提示系统默认浏览器未能打开、实际失败原因以及即将改用内置浏览器；提示发送完成前不得调用内置浏览器。
- 用户发现预览内容不对或要求修改内容时，应先回到根 `zhihu-publisher`，由根流程结合用户需求和 `zhihu-validate` 的说明文档更新 `./.zhihu-publish-output/draft/latest-draft.md`，再重新运行 validate 和 preview。
- 不要直接修改 `./.zhihu-publish-output/validate/latest.json` 或 `./.zhihu-publish-output/preview/latest.html` 来修正预览。
- 除非用户显式指定其他路径，产物应写入当前工作目录下的 `./.zhihu-publish-output/preview/`。

## 参考文件

- `reference/preview.md`：预览 HTML 结构、展示顺序和浏览器预览适配规则。
