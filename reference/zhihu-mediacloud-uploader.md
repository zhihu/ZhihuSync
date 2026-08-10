# zhihu-mediacloud-uploader 安装引导

本文档只用于在当前发布流程需要媒体上传时，引导安装或启用 `zhihu-mediacloud-uploader` skill。

不要在本文档维护上传参数、凭证配置、MCP 配置、工具调用规则、错误处理或上传结果字段映射。安装或确认该 skill 可用后，立即加载 `zhihu-mediacloud-uploader` 的 `SKILL.md`，并以它及其 `references/` 文档作为唯一详细来源。

## 依赖来源

媒体上传依赖 skill：

```text
npx skills add zhihu/zhihu-mediacloud-uploader.git -g
```

## 安装流程

1. 如果当前 Agent 已能加载 `zhihu-mediacloud-uploader` skill，直接加载该 skill 的 `SKILL.md`，按其中流程继续。
2. 如果当前 Agent 尚未安装该 skill，优先调用可用的 skill 安装能力，从上述 Git 地址安装 `zhihu-mediacloud-uploader`。
3. 只有当前宿主不支持自动安装、需要用户授权、或安装步骤必须由用户完成时，才提示用户手动安装该 skill。
4. 安装完成后，重新加载 `zhihu-mediacloud-uploader` 的 `SKILL.md`，按它的初始化、凭证、MCP、工具参数和返回字段说明执行。

## 流程边界

- 本文档只解决“如何获得并加载 `zhihu-mediacloud-uploader` skill”。
- 不复制 `zhihu-mediacloud-uploader` 中的工具参数和响应字段说明。
- 不绕过该 skill 直接运行它的源码、MCP server 或临时客户端。
- 如果 `zhihu-mediacloud-uploader` 的初始化流程要求重启 Agent，停止当前发布流程，提示用户重启后重新发起发布或上传请求。
