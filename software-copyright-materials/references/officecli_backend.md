# OfficeCLI DOCX 后端

## 固定版本与边界

- 已验证版本：`1.0.151`。
- 官方发布页：https://github.com/iOfficeAI/OfficeCLI/releases/tag/v1.0.151
- 本仓库不复制 OfficeCLI 源码或二进制；OfficeCLI 继续按其 Apache-2.0 许可证独立分发。
- OfficeCLI 必须全局安装，不下载到被分析项目、本 skill 或输出目录，也不使用项目内 `工具/` 文件夹保存二进制。
- Python 保留项目分析、业务草稿、代码选择、物理行折行、选材量估算和门禁逻辑；OfficeCLI 负责 DOCX 创建、编辑、校验和预览，最终分页由 Word 排版引擎自动完成。
- 运行时设置 `OFFICECLI_SKIP_UPDATE=1` 和 `OFFICECLI_NO_AUTO_RESIDENT=1`，避免版本漂移、后台文件锁和延迟落盘。

## 全局安装与检测

Windows PowerShell 使用官方安装命令：

```powershell
irm https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.ps1 | iex
```

官方脚本默认安装到 `%LOCALAPPDATA%\OfficeCLI` 并写入用户 PATH。安装完成后，必须重启 Codex，让新进程读取更新后的 PATH；重启后运行 `officecli --version` 和环境检查，再继续工作流。不得要求用户设置 `OFFICECLI_PATH`，不得通过 `--officecli` 指定项目内或任意文件夹中的可执行文件。

运行时只从当前进程 PATH 查找全局 `officecli` / `officecli.exe`。如果 Windows 官方安装目录中已有二进制、但当前进程 PATH 尚未识别，环境检查必须报告“需要重启 Codex”并停止，不得把该文件当作项目便携版直接绕过重启。

版本缺失或不等于 `1.0.151` 时，环境检查必须停止。只有用户明确接受兼容性风险后，正式生成才允许传入 `--allow-untested-officecli`。

## 写入策略

- 每个 DOCX 先 `create --force --locale zh-CN`，再用一个原子 `batch --stop-on-error` 写入主要内容。
- A4、页边距、默认字体、黑色文字、页眉和页码全部写入文档，不依赖模板文件。
- 主要内容完成后读取 `/theme`，把 major/minor 的拉丁、东亚和复杂文字字体统一为 Times New Roman / SimSun，再通过 OfficeCLI `raw-set` 整体替换主题根节点；不使用 Python 直接改写 DOCX 压缩包。
- 页眉左侧为软件全称和版本号，右侧为 PAGE 字段。
- 操作手册先展开 OfficeCLI Markdown 子集，再统一设置中文正文格式；本地 Markdown 图片会通过 picture 元素嵌入。用户选择截图时，生成脚本读取 `截图/截图清单.json`，按清单顺序把可用图片依次替换到可见截图预留位置，再由 OfficeCLI 插入 Word；图片不足时保留未匹配提示，图片过多、缺失或格式不支持时写入生成报告。远程图片仍保留可见提示。
- 代码材料不使用 Word 自动行号。抽取脚本先按最多 90 显示列折行（全角字符按 2 列），正文使用 8pt 字号和 13pt 固定行距，并按每页约 55 个物理行估算前后 30 页的选材量。每个物理行写成一个固定行距段落，所有段落连续流入正文，不设置 `pageBreakBefore`；Word 根据页面可用高度自动换页，OfficeCLI 再读取真实页数。
- 正式生成只读取当前 `代码提取清单.json` 的 `outputs`。重新抽取或生成时清理同一软件名下与当前模式冲突的旧代码草稿和旧代码 DOCX，避免“前后 30 页”和“全部代码”同时残留。

## 校验策略

1. `officecli validate <file> --json`：OpenXML 结构错误必须为 0，否则生成失败。
2. 重新读取 `/theme`，确认六个主题字体槽均为 Times New Roman / SimSun，避免 WPS 因默认的 Calibri、Calibri Light、等线主题字体提示缺失字体。
3. `officecli view <file> issues --json`：内容/格式提示写入生成报告，不能把它误当成结构校验。
4. Windows 且安装 Microsoft Word 时，对代码材料执行 `view stats --page-count --json`，把自动分页后的真实页数写入报告。Word 不可用时改用 `wps writer info <file> --json` 返回的 `pages`，该数字是 WPS 文字组件的分页统计，不是 HTML 估算。Markdown 页分组只代表选材估算；但前 30 页/后 30 页文档的 Word 或 WPS 实际页数必须分别为 30，否则正式生成失败并要求重新校准选材量。WPS 命令缺失、WPS 未安装或返回里没有页数时，仍保留“无法取得 Word 原生页数，请用 Word/WPS 人工复核”的提示。
5. 生成全页联系表预览用于快速目检。OfficeCLI 的 HTML 渲染不能替代 Word/WPS 的最终分页复核。

用户确认会记录内容指纹。业务理解、代码选择、申请表或最终草稿被修改后，正式生成必须拒绝沿用旧确认，待用户重新核对并记录对应门禁。

## 常用命令

```bash
officecli --version
officecli validate output.docx --json
officecli view output.docx issues --json
officecli view output.docx stats --page-count --json
officecli view output.docx screenshot --grid auto --render auto -o preview.png
```
