# Publish OpenAPI 公共规范

本文档只记录 `zhihu-publish` 调用 publish OpenAPI endpoint 的公共 HTTP 协议、签名、响应和 curl 执行方式。按内容类型组装 `content` 字段时，必须再读取对应类型规范：

| `latest.json.type` | 类型规范 |
|---|---|
| `article` | `reference/publish-article.md` |
| `question` | `reference/publish-question.md` |
| `pin` | `reference/publish-pin.md` |

## Endpoint

```text
POST {BASE_URL}/openapi/publish
Content-Type: application/json
```

请求地址和 URL 路径：

```text
BASE_URL=https://openapi.zhihu.com
API_PATH=/openapi/publish
```

`BASE_URL` 优先使用环境变量 `ZHIHU_PUBLISH_BASE_URL`；如果没有提供，则使用默认值 `https://openapi.zhihu.com`。

## Headers

| Header | 必填 | 说明 |
|---|---|---|
| `Content-Type` | 是 | 固定 `application/json` |
| `X-App-Key` | 是 | `ZHIHU_OPENAPI_APP_KEY`，用户 member token / URLToken |
| `X-Timestamp` | 是 | Unix 秒级时间戳 |
| `X-Log-Id` | 是 | 请求日志 ID，调用方生成，建议唯一 |
| `X-Extra-Info` | 是 | 可为空字符串，但签名时必须参与计算 |
| `X-Sign` | 是 | HMAC-SHA256 签名后 Base64 |

签名规则：

```text
sign_string = app_key:{X-App-Key}|ts:{X-Timestamp}|logid:{X-Log-Id}|extra_info:{X-Extra-Info}
X-Sign = Base64(HMAC-SHA256(sign_string, ZHIHU_OPENAPI_APP_SECRET))
```

`ZHIHU_OPENAPI_APP_SECRET` 不写入请求头、请求体、request 文件或最终回复。

即使 `X-Extra-Info` 为空字符串，也必须实际发送该 Header。使用 curl 时，空值必须写为 `-H "X-Extra-Info;"`；`-H "X-Extra-Info: "` 会被 curl 解释为移除该 Header。

## Request Envelope

所有类型共用外层结构：

```json
{
  "type": "article | question | pin",
  "confirmed": true,
  "confirm_note": "confirmed by user after local preview",
  "content": {}
}
```

公共要求：

- `type` 必须等于 `validate/latest.json.type`。
- `confirmed` 必须为 `true`；没有用户确认预览时不得发送请求。
- `confirm_note` 可使用固定文案 `confirmed by user after local preview`。
- `content` 必须按对应类型规范生成，不要把不属于该类型的字段写入请求体。

## Response

HTTP 状态码只表示 HTTP 请求是否到达服务并得到响应，不表示内容发布成功。发布成功与否必须以 response body 中的 JSON 为准；即使 HTTP 状态码是 `200`，只要 JSON 中的 `status` 不是 `0`，也必须按发布失败处理。

成功响应：

```json
{
  "status": 0,
  "msg": "success",
  "data": {
    "type": "article",
    "content_token": "123456",
    "url": "https://zhuanlan.zhihu.com/p/123456"
  }
}
```

失败响应：

```json
{
  "status": 1,
  "msg": "failed to publish: ...",
  "data": null
}
```

鉴权失败可能返回 HTTP 401；发布频率超限可能返回 HTTP 429，body 中 `msg` 为 `rate limit exceeded`。当前 `zhihu-publisher` skill 每人每天最多发布 50 次。

发布结果判定规则：

- `curl` 执行失败：请求失败，不要判断为发布成功。
- response body 不是合法 JSON：发布结果未知/失败，提示用户检查 `latest-response.json`。
- response JSON 中 `status == 0`：发布成功，返回 `data.content_token` 和 `data.url`。
- response JSON 中 `status != 0`、缺少 `status`，或 `status` 不是数字：发布失败，向用户返回 JSON 中的 `status` / `msg` 和本地 response 文件路径。
- HTTP 非 2xx 时通常为请求失败；如果 response body 是合法 JSON，仍然要读取并向用户展示其中的 `status` / `msg`，但不要因为 HTTP 状态码本身判断发布成功。

## Curl Execution

请求必须由 `curl` 发出，且请求体必须来自已经落盘的 request JSON：

```text
./.zhihu-publish-output/publish/latest-request.json
```

执行前必须已经按根目录 `../../reference/auth-info.md` 完成凭证检查；如果凭证来自共享文件，需要先读入到运行时变量中。生成和执行 curl 时必须按当前操作系统/ shell 选择模板：

凭证载入运行时变量后，必须再次确认 `ZHIHU_OPENAPI_APP_KEY` 和 `ZHIHU_OPENAPI_APP_SECRET` 都非空；任一字段为空时必须在签名和 curl 执行前停止。

- Linux、macOS、WSL、Git Bash：使用 POSIX shell 模板。
- Windows 原生 PowerShell：使用 PowerShell 模板，并显式调用 `curl.exe`，不要使用 `curl` 别名。
- 如果当前 Agent 不确定运行环境，先识别 shell；不要把 Bash 写法直接用于 Windows PowerShell，也不要把 PowerShell 写法直接用于 Linux/macOS。

### Linux / macOS / POSIX Shell

```bash
REQUEST_FILE="./.zhihu-publish-output/publish/latest-request.json"
RESPONSE_FILE="./.zhihu-publish-output/publish/latest-response.json"
OPENAPI_APP_KEY="${ZHIHU_OPENAPI_APP_KEY:-}"
OPENAPI_APP_SECRET="${ZHIHU_OPENAPI_APP_SECRET:-}"
SHARED_CREDENTIALS_FILE="$HOME/.zhihu/openapi-credentials.json"
if { [ -z "$OPENAPI_APP_KEY" ] || [ -z "$OPENAPI_APP_SECRET" ]; } && [ -f "$SHARED_CREDENTIALS_FILE" ]; then
  FILE_OPENAPI_APP_KEY="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8")).get("ZHIHU_OPENAPI_APP_KEY", ""))' "$SHARED_CREDENTIALS_FILE")"
  FILE_OPENAPI_APP_SECRET="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8")).get("ZHIHU_OPENAPI_APP_SECRET", ""))' "$SHARED_CREDENTIALS_FILE")"
  OPENAPI_APP_KEY="${OPENAPI_APP_KEY:-$FILE_OPENAPI_APP_KEY}"
  OPENAPI_APP_SECRET="${OPENAPI_APP_SECRET:-$FILE_OPENAPI_APP_SECRET}"
fi
if [ -z "$OPENAPI_APP_KEY" ] || [ -z "$OPENAPI_APP_SECRET" ]; then
  printf '%s\n' 'missing ZHIHU_OPENAPI_APP_KEY or ZHIHU_OPENAPI_APP_SECRET' >&2
  exit 1
fi
BASE_URL="${ZHIHU_PUBLISH_BASE_URL:-https://openapi.zhihu.com}"
BASE_URL="${BASE_URL%/}"
API_PATH="/openapi/publish"
TS="$(date +%s)"
LOG_ID="zhihu-publisher-$(date +%Y%m%d%H%M%S)"
EXTRA_INFO="${ZHIHU_PUBLISH_EXTRA_INFO:-}"
if [ -z "$EXTRA_INFO" ]; then
  EXTRA_INFO_HEADER="X-Extra-Info;"
else
  EXTRA_INFO_HEADER="X-Extra-Info: $EXTRA_INFO"
fi
SIGN="$(printf 'app_key:%s|ts:%s|logid:%s|extra_info:%s' "$OPENAPI_APP_KEY" "$TS" "$LOG_ID" "$EXTRA_INFO" | openssl dgst -sha256 -hmac "$OPENAPI_APP_SECRET" -binary | base64)"

HTTP_STATUS="$(curl -sS -o "$RESPONSE_FILE" -w '%{http_code}' -X POST "$BASE_URL$API_PATH" \
  -H "Content-Type: application/json" \
  -H "X-App-Key: $OPENAPI_APP_KEY" \
  -H "X-Timestamp: $TS" \
  -H "X-Log-Id: $LOG_ID" \
  -H "$EXTRA_INFO_HEADER" \
  -H "X-Sign: $SIGN" \
  --data-binary @"$REQUEST_FILE")"
```

### Windows PowerShell

```powershell
$RequestFile = ".\.zhihu-publish-output\publish\latest-request.json"
$ResponseFile = ".\.zhihu-publish-output\publish\latest-response.json"
$OpenApiAppKey = $env:ZHIHU_OPENAPI_APP_KEY
$OpenApiAppSecret = $env:ZHIHU_OPENAPI_APP_SECRET
$SharedCredentialsFile = Join-Path $HOME ".zhihu\openapi-credentials.json"

if (([string]::IsNullOrWhiteSpace($OpenApiAppKey) -or [string]::IsNullOrWhiteSpace($OpenApiAppSecret)) -and (Test-Path -LiteralPath $SharedCredentialsFile)) {
  $Creds = Get-Content -LiteralPath $SharedCredentialsFile -Raw -Encoding UTF8 | ConvertFrom-Json
  if ([string]::IsNullOrWhiteSpace($OpenApiAppKey)) {
    $OpenApiAppKey = [string]$Creds.ZHIHU_OPENAPI_APP_KEY
  }
  if ([string]::IsNullOrWhiteSpace($OpenApiAppSecret)) {
    $OpenApiAppSecret = [string]$Creds.ZHIHU_OPENAPI_APP_SECRET
  }
}

if ([string]::IsNullOrWhiteSpace($OpenApiAppKey) -or [string]::IsNullOrWhiteSpace($OpenApiAppSecret)) {
  throw "missing ZHIHU_OPENAPI_APP_KEY or ZHIHU_OPENAPI_APP_SECRET"
}

if ([string]::IsNullOrWhiteSpace($env:ZHIHU_PUBLISH_BASE_URL)) {
  $BaseUrl = "https://openapi.zhihu.com"
} else {
  $BaseUrl = $env:ZHIHU_PUBLISH_BASE_URL -replace "/+$", ""
}

$ApiPath = "/openapi/publish"
$Ts = [string]([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())
$LogId = "zhihu-publisher-{0}" -f (Get-Date -Format "yyyyMMddHHmmss")
$ExtraInfo = if ($null -eq $env:ZHIHU_PUBLISH_EXTRA_INFO) { "" } else { $env:ZHIHU_PUBLISH_EXTRA_INFO }
$ExtraInfoHeader = if ([string]::IsNullOrEmpty($ExtraInfo)) { "X-Extra-Info;" } else { "X-Extra-Info: $ExtraInfo" }
$SignString = "app_key:{0}|ts:{1}|logid:{2}|extra_info:{3}" -f $OpenApiAppKey, $Ts, $LogId, $ExtraInfo
$KeyBytes = [Text.Encoding]::UTF8.GetBytes($OpenApiAppSecret)
$DataBytes = [Text.Encoding]::UTF8.GetBytes($SignString)
$Hmac = [Security.Cryptography.HMACSHA256]::new($KeyBytes)
try {
  $Sign = [Convert]::ToBase64String($Hmac.ComputeHash($DataBytes))
} finally {
  $Hmac.Dispose()
}

$HttpStatus = & curl.exe -sS -o $ResponseFile -w "%{http_code}" -X POST "$BaseUrl$ApiPath" `
  -H "Content-Type: application/json" `
  -H "X-App-Key: $OpenApiAppKey" `
  -H "X-Timestamp: $Ts" `
  -H "X-Log-Id: $LogId" `
  -H $ExtraInfoHeader `
  -H "X-Sign: $Sign" `
  --data-binary "@$RequestFile"

if ($LASTEXITCODE -ne 0) {
  throw "curl.exe failed with exit code $LASTEXITCODE"
}
```

执行规则：

- 可以在内部生成等价 curl 命令，但不要把 `OPENAPI_APP_SECRET`、`ZHIHU_OPENAPI_APP_SECRET` 或由 secret 计算出的 `X-Sign` 实际值写入 request 文件、response 文件、日志或最终回复。
- 如需向用户展示 curl，只展示未展开变量的模板或把敏感值替换为 `<redacted>`；不要展示包含真实 secret 或真实 `X-Sign` 的完整命令。
- `latest-response.json` 保存 HTTP response body。
- 执行 curl 后必须解析 `latest-response.json`，按 Response 中的发布结果判定规则得出成功/失败结论；不要只根据 HTTP status 判断。
- 最终回复中返回 HTTP status、response body 中的 `status` / `msg`，只有 JSON `status == 0` 时才返回成功结论和 `data.content_token` / `data.url`。
- curl 失败或 response body 非法 JSON 时，停止并向用户说明本地 request/response 文件路径。
