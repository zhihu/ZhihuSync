# 知乎 OpenAPI 凭证说明

本文档说明知乎 OpenAPI 通用凭证是什么、如何获取，以及多个 skill 如何复用同一套值。
本文档是凭证含义、获取方式、持久化位置、读取优先级和初始化流程的唯一详细来源；子 skill 入口文档只保留入口和原则。

推荐用户侧统一使用不会与其他服务冲突的变量名：

```text
ZHIHU_OPENAPI_APP_KEY
ZHIHU_OPENAPI_APP_SECRET
```

推荐把凭证持久化到用户本地共享文件，供 `zhihu-mediacloud-uploader`、`zhihu-publish` 和后续知乎 OpenAPI skill 共同读取；环境变量只作为本次会话覆盖使用，且只使用上述两个 `ZHIHU_OPENAPI_*` 变量名。

---

## AI 初始化流程

按以下顺序处理凭证，不要让一个 skill 解析另一个 skill 的 MCP 配置文件：

1. 检查当前进程环境变量 `ZHIHU_OPENAPI_APP_KEY` / `ZHIHU_OPENAPI_APP_SECRET` 是否完整。
2. 检查共享凭证文件 `~/.zhihu/openapi-credentials.json` 是否存在且包含完整凭证。
3. 如果只有一个完整来源，直接使用该来源。
4. 如果环境变量和共享文件都完整但值不一致，停止并让用户选择来源；只展示来源名和 `ZHIHU_OPENAPI_APP_KEY`，不要展示任何 `ZHIHU_OPENAPI_APP_SECRET`。
5. 如果没有完整凭证，询问用户是否已经为其他知乎 OpenAPI skill 配置过共享凭证文件或当前会话环境变量。
6. 如果用户直接提供凭证，默认写入共享凭证文件，供多个知乎 OpenAPI skill 复用。
7. 如果用户还没有凭证，按本文“如何获取”引导用户获取 `ZHIHU_OPENAPI_APP_KEY` / `ZHIHU_OPENAPI_APP_SECRET`。

凭证检查和初始化过程中的输出规则：

- 只向用户说明凭证来源、是否完整、是否一致，以及后续需要用户做什么。
- 不要输出、复述、截断展示或掩码展示 `ZHIHU_OPENAPI_APP_SECRET` 的任何原始内容；用户直接粘贴 secret 时，只确认“已收到并将写入/使用”，不要在回复中重复该值。
- 不要运行或建议用户运行会打印 secret 的命令，例如 `env`、`printenv`、`set`、`echo $ZHIHU_OPENAPI_APP_SECRET`、PowerShell `Get-ChildItem Env:`。
- 如需展示示例命令或配置，只使用占位符 `<ZHIHU_OPENAPI_APP_SECRET>` 或 `<redacted>`。

读取优先级：

1. `ZHIHU_OPENAPI_APP_KEY` / `ZHIHU_OPENAPI_APP_SECRET`
2. `~/.zhihu/openapi-credentials.json`

---

## 持久化位置

默认保存到：

```text
~/.zhihu/openapi-credentials.json
```

文件内容：

```json
{
  "ZHIHU_OPENAPI_APP_KEY": "<知乎用户 Token>",
  "ZHIHU_OPENAPI_APP_SECRET": "<开放平台访问密钥>"
}
```

写入时要求文件仅当前用户可读写。

不要把凭证保存到 skill 仓库。

---

## 凭证含义

| 凭证 | 含义 | 如何获取 |
|---|---|---|
| `ZHIHU_OPENAPI_APP_KEY` | **知乎用户 Token**，即知乎主页 URL 中的用户名部分 | 直接从主页 URL 获取，无需申请 |
| `ZHIHU_OPENAPI_APP_SECRET` | **开放平台访问密钥（SK）**，用于请求签名，**不可泄露** | 在知乎开放平台申请 |

**示例：** 若知乎主页地址为 `https://www.zhihu.com/people/abc`，则 `ZHIHU_OPENAPI_APP_KEY` 为 `abc`。

---

## 如何获取

### ZHIHU_OPENAPI_APP_KEY（知乎用户 Token）

登录知乎后访问个人主页，URL 中的用户名即为 Token：

```
https://www.zhihu.com/people/<这里就是 ZHIHU_OPENAPI_APP_KEY>
```

### ZHIHU_OPENAPI_APP_SECRET（开放平台访问密钥）

前往知乎开放平台申请：

👉 **https://www.zhihu.com/playground/zhihu-publisher**

> 注：该页面目前处于内测阶段，如无法访问，请联系知乎开放平台负责人申请访问密钥。

申请后获得的密钥即为 `ZHIHU_OPENAPI_APP_SECRET`，与你的 `ZHIHU_OPENAPI_APP_KEY`（用户 Token）配对使用。

---

## 多个 Skill 复用同一套凭证

`ZHIHU_OPENAPI_APP_KEY` 和 `ZHIHU_OPENAPI_APP_SECRET` 是**知乎 OpenAPI 的通用鉴权凭证**，所有调用知乎开放平台 API 的 skill（媒体上传、内容发布等）均使用同一套值。

当前推荐口径：

- 长期复用：保存到 `~/.zhihu/openapi-credentials.json`。
- 临时覆盖：设置 `ZHIHU_OPENAPI_APP_KEY` / `ZHIHU_OPENAPI_APP_SECRET`。
- 其他知乎 skill 应读取共享凭证文件或 `ZHIHU_OPENAPI_*`。

MCP 配置中默认不需要写入密钥 env。只有需要临时覆盖共享文件时，才在 MCP env 中显式写入 `ZHIHU_OPENAPI_APP_KEY` / `ZHIHU_OPENAPI_APP_SECRET`。

---

## 安全提示

- `ZHIHU_OPENAPI_APP_SECRET` 是私密密钥，**不要分享给他人、不要提交到代码仓库**
- Agent 校验或汇报凭证状态时，不得把 `ZHIHU_OPENAPI_APP_SECRET` 输出给用户；最终回复、日志、request 文件和 response 文件都不能包含该值
- 凭证默认存储在本地共享凭证文件 `~/.zhihu/openapi-credentials.json`；如额外写入 MCP 配置文件，请确认该文件已加入 `.gitignore`
- 若凭证泄露，立即前往知乎开放平台重置 `ZHIHU_OPENAPI_APP_SECRET`
