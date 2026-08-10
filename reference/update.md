# Skill Update Check

用于判断当前安装的 `zhihu-publisher` 是否落后于版本接口发布的版本，并在用户确认后更新。

## 目录

- [触发时机](#触发时机)
- [版本来源](#版本来源)
- [检查流程](#检查流程)
- [判定规则](#判定规则)
- [更新规则](#更新规则)

## 触发时机

在以下场景读取本文档：

- 每个会话首次加载 `zhihu-publisher` skill 后，自动检查一次。
- 用户询问是否有新版本、要求检查版本、检查更新、更新或升级 skill。
- 用户遇到明显像旧版本导致的问题，例如文档行为不一致、已修复问题仍复现、安装后能力缺失。

同一会话只自动检查一次。用户再次明确询问更新、版本、升级，或遇到明显像旧版本导致的问题时，可以重复检查。

## 版本来源

本地版本和 skill 名称都读取当前 skill 根目录 `SKILL.md` frontmatter：

- skill 名称：`name`，当前应为 `zhihu-publisher`。
- 本地版本：`metadata.version`。
- 任一字段不存在或版本格式不合法时，说明无法确定当前版本，不要使用 Git tag 或其他值补全。

版本接口的 base URL 按以下优先级确定：

- 如果环境变量 `ZHIHU_PUBLISH_BASE_URL` 非空，使用该值。
- 否则使用默认值 `https://openapi.zhihu.com`。

移除 base URL 末尾的 `/` 后拼接固定路径 `/openapi/publish_skill/version`。不得通过 GitHub、Git 远端、tag 或 release 判断最新版本。

版本接口返回一个 JSON 对象；顶层 key 是 skill 名称，对应对象包含：

| 字段 | 含义 |
|---|---|
| `version` | 该 skill 的最新版本 |
| `repository` | 首选更新方式使用的仓库标识，例如 `zhihu/zhihu-publisher` |
| `download_link` | 备用更新方式使用的 ZIP 下载地址；可能为空 |

## 检查流程

根据当前系统使用对应命令访问版本接口。

macOS / Linux（sh、bash 或 zsh）：

```bash
publish_version_base_url="${ZHIHU_PUBLISH_BASE_URL:-https://openapi.zhihu.com}"
curl --fail --silent --show-error "${publish_version_base_url%/}/openapi/publish_skill/version"
```

Windows（PowerShell）：

```powershell
$publishVersionBaseUrl = if ([string]::IsNullOrWhiteSpace($env:ZHIHU_PUBLISH_BASE_URL)) {
  "https://openapi.zhihu.com"
} else {
  ($env:ZHIHU_PUBLISH_BASE_URL).TrimEnd("/")
}
curl.exe --fail --silent --show-error "$publishVersionBaseUrl/openapi/publish_skill/version"
```

Windows 必须显式调用 `curl.exe`，不要调用可能映射到 `Invoke-WebRequest` 的 PowerShell `curl` 别名。

1. 结构化解析 response JSON，不要用字符串截取字段。
2. 使用本地 `SKILL.md` 的 `name` 在顶层对象中做精确匹配；本 skill 只读取 `zhihu-publisher` 对象，不读取其他 skill 的版本。
3. 读取匹配对象的 `version`、`repository` 和 `download_link`；不要自行推导或替换这些值。
4. 按语义化版本的数字顺序比较远端 `version` 与本地 `metadata.version` 的 `MAJOR.MINOR.PATCH`。

不要使用字符串排序判断版本大小；例如 `0.10.0` 必须大于 `0.2.0`。

## 判定规则

| 情况 | 处理 |
|---|---|
| 接口版本大于本地版本 | 提示有新版本，可更新；等待用户选择更新或暂不更新 |
| 接口版本等于本地版本 | 提示当前已是最新版本 |
| 本地版本大于接口版本 | 提示当前本地版本高于接口版本，可能是开发版或未发布版本 |
| 无法访问接口或 response 不是合法 JSON | 说明无法检查版本，不要猜测 |
| response 中没有同名对象 | 说明版本接口未提供当前 skill 的版本信息 |
| 同名对象缺少合法 `version` | 说明版本信息不完整，不要判断是否需要更新 |

检查发现新版本时，先提示用户更新并等待选择；用户选择前不要继续 draft、validate、preview、上传媒体或 publish。用户选择暂不更新时，可以继续后续流程，但必须说明当前会话仍使用本地已加载版本。

自动检查失败且用户本次没有主动要求检查更新时，简要说明原因后继续后续流程。用户主动要求检查更新时，检查失败后停止并返回失败原因。

## 更新规则

- 不要静默自动更新。只有用户明确确认更新后，才执行以下流程。
- 更新前保留版本接口中同名对象的 `repository` 和 `download_link`，不得使用其他来源替换。

### 首选：repository

`repository` 非空时，执行：

```bash
npx skills add {repository} -g
```

将 `{repository}` 替换为接口返回的原始值。命令成功后，提示用户完全退出并重启 Agent；重启前不要继续发布流程。

### 备用：download_link

仅当 `repository` 为空、首选命令不可用或执行失败时使用：

1. 如果 `download_link` 为空，说明没有可用的备用下载地址，并原样报告首选方式的失败原因。
2. 如果 `download_link` 非空，按当前系统使用以下命令下载该地址表示的 ZIP 文件；不要自行拼接或改写 URL。

macOS / Linux：

```bash
curl --fail --location --output zhihu-publisher-{version}.zip "{download_link}"
```

Windows（PowerShell）：

```powershell
curl.exe --fail --location --output "zhihu-publisher-{version}.zip" "{download_link}"
```

将 `{version}` 和 `{download_link}` 替换为同名对象返回的原始值。

3. 不要自动解压、覆盖或删除当前 skill 文件。
4. 下载成功后，向用户提供 ZIP 的绝对路径和当前 skill 目录的绝对路径，提示用户解压并将内容拷贝到当前 skill 目录。
5. 提示用户完成拷贝后完全退出并重启 Agent；重启前不要继续发布流程。
