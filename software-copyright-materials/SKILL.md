---
name: software-copyright-materials
description: >
  Generate guided Chinese software copyright application materials from a real project.
  Use this skill when the user asks for 软件著作权, 软著申请资料, 软著代码材料,
  操作手册, 申请表信息, or wants Word/TXT materials for software copyright registration.
  The workflow analyzes the imported project, extracts real source code, creates Markdown
  drafts for user confirmation, then uses a pinned OfficeCLI backend to produce final
  Word documents and TXT.
metadata:
  short-description: 生成软著申请资料 Word/TXT
  author: Fokkyp
  version: "2.6"
  repository: https://github.com/Fokkyp/SoftwareCopyright-Skill
---

# 软著申请资料生成

这个 skill 生成可审阅、可追溯的软著申请资料。核心原则：

- 固定输出目录：当前工作目录下的 `软件著作权申请资料/`。不要默认写到 `/tmp`、`/private/tmp` 或其他临时目录。
- 只有测试 skill 自身时才允许显式指定临时目录；面向用户生成材料时必须写入当前目录。
- 先生成 Markdown 草稿，用户确认后再生成正式 Word/TXT。
- 正式 Word/TXT 只能写入 `软件著作权申请资料/正式资料/`，不要散落在输出目录根部。
- 正式 Word/TXT 的文字一律使用默认黑色字体，不生成蓝色超链接、主题色标题或其他彩色文字；Markdown 链接写入 Word 时必须转成普通文本。
- 正式资料中的软件名称必须与 `草稿/申请表信息.md` 的“软件全称”字段一致；正式生成时以已确认的申请表软件全称为准。
- 正式代码 Word 页眉中的版本号必须与 `草稿/申请表信息.md` 的“版本号”字段一致；正式生成时以已确认的申请表版本号为准。
- 代码材料必须来自真实项目源码，禁止 AI 编造代码。
- 写申请表和操作手册前，必须先形成模型研判后的 `草稿/业务理解.md/json`，理解软件业务、行业、目标用户、核心价值和操作流程。
- 脚本只能收集项目证据、校验字段和生成文件；行业判断、功能抽取、代码抽取选择、操作手册结构必须由模型阅读项目后决定，不得依赖脚本关键字表或固定范本。
- 优先抽取前端代码：入口、路由、页面、核心组件、接口封装、状态管理、工具函数。
- 生成代码材料前，必须先生成代码文件候选清单；模型理解项目后填写抽取文件和选择理由，再让用户确认或修改。
- 代码优先抽取模型和用户确认的、最能体现软件真实功能和运行逻辑的源码；不足 60 页时，从其他相关源码文件补充到 60 页；候选源码仍不足 60 页时，才生成全部代码文档。
- 源码发现不得依赖编程语言扩展名白名单。脚本默认扫描可读文本文件，并排除明确的文档、配置、媒体、压缩包、二进制、生成物和超大文件；未知扩展名源码同样进入候选清单，再由模型和用户确认是否抽取。
- 业务证据收集必须发现项目中的文本设计资料以及 DOCX、PDF、ODT、DOC、WPS 等文档；能自动提取正文时写入证据，无法提取时也必须登记路径并提示模型进一步阅读，不能因格式不在文本扩展名列表中而静默遗漏。
- 操作手册成稿应像真实软件随附的操作说明，而不是研发说明、功能清单或 AI 生成的汇总文。
- 操作手册草稿必须按传统软著操作手册骨架组织：相关文档、说明、功能特点、系统要求、按真实页面/流程逐章操作、常见问题解答、术语表。一级章节标题使用中文大写序号，例如 `一、相关文档`，不得使用 `(1)、相关文档`。相关文档必须用表格指向总体设计、详细设计、测试案例等配套文档。正文尽量使用连续段落，不使用项目符号列表或 `1. 2. 3.` 编号列表。
- 每个核心页面都要用普通用户视角说明页面用途、进入位置、用户可见内容、用户动作、输入限制或异常提示、结果反馈和截图预留。不得把章节写成“进入方式：/页面内容：/操作步骤：/操作规则：/操作结果与反馈：”这种字段模板；这些信息要自然合并到段落里。避免代码、框架、接口、状态管理、异步任务等技术化表达；撰写过程中由 agent 自行循环检查、扩写和修正，完整草稿完成后只向用户发起一次整体确认。
- 操作手册必须去除明显“AI 味”：避免空泛赞美、营销口号、万能句式、每章同一结构、头中尾固定结构、过度对称的排比、没有项目细节的正确废话、频繁使用“旨在、赋能、一站式、智能化、高效便捷、显著提升、强大能力、丰富功能”等套话。每段都应能回答“这个项目里这个功能具体做什么、用户看见什么、操作后有什么结果”。
- 操作手册生成必须同步输出 `草稿/操作手册自检记录.md` 和 `草稿/操作手册自检记录.json`，记录初稿、按项目流程扩写、去制式表达等自检轮次；如果前 3 轮仍发现问题，必须继续补写修正，直到问题清零或记录无法自动修复的原因后再停止。
- 截图方式只允许用户选择：Playwright CLI 自动截图或用户自行截图。用户选择自动截图后，先检查固定验证版本的 `playwright-cli` 是否可用；如果用户说现在不截图、先跳过截图或截图失败，操作手册仍必须保留清晰可见的截图预留位置，正式 Word 中也要能看到。
- 申请表信息中的硬件/系统环境必须让用户确认或填写，不能硬编码。
- Word 生成统一使用 OfficeCLI 后端；Python 只负责业务分析、代码抽取、门禁和命令编排，不直接解包、重打包或写入 DOCX 包。OfficeCLI 完成正文写入后，必须通过 `/theme` + `raw-set` 把主题字体统一为宋体（SimSun）和 Times New Roman，并重新读取主题确认 Calibri、Calibri Light、等线等默认主题字体已消失。
- OfficeCLI 固定验证版本为 `1.0.151`，运行时必须设置 `OFFICECLI_SKIP_UPDATE=1`，不得静默升级、静默安装或回退到 python-docx/Pandoc/.NET 工具包。
- OfficeCLI 的安装、批处理、分页与校验细节见 `references/officecli_backend.md`。

## 路径与按需参考

开始执行前，从当前已加载的 `SKILL.md` 位置取得本 skill 的绝对目录，记为 `<SKILL_DIR>`；找到可用的 Python 3.10+ 解释器，记为 `<PYTHON>`。下面命令中的尖括号是必须替换的占位符，不要依赖 `${CLAUDE_SKILL_DIR}` 等某个 agent 专属环境变量，也不要把占位符原样交给 shell。

按当前阶段读取对应参考资料，不要一次性把所有内容都塞入上下文：

- 填申请表前读 [application_fields.md](references/application_fields.md)。
- 研判业务前读 [business_understanding_rules.md](references/business_understanding_rules.md)。
- 选择和抽取代码前读 [code_selection_rules.md](references/code_selection_rules.md) 与 [copyright_material_rules.md](references/copyright_material_rules.md)。
- 写操作手册前读 [manual_structure.md](references/manual_structure.md)。
- 用户选择自动截图后读 [playwright_cli_screenshots.md](references/playwright_cli_screenshots.md)。
- 正式生成和校验 DOCX 前读 [officecli_backend.md](references/officecli_backend.md)。

## 强制人工门禁

凡是涉及用户选择、确认或补充信息的阶段，必须先停止当前执行，不得继续调用下一步脚本。即使处于自动审核、自动继续或无人值守模式，也必须把 `STOP_FOR_USER` 和 `NEXT_ACTION` 原样告知用户，并等待用户输入后再继续。

禁止使用“用户未选择则默认继续”的逻辑。用户回复确认后，先用确认脚本记录对应门禁，再进入下一阶段：

```bash
<PYTHON> "<SKILL_DIR>/scripts/confirm_stage.py" --workdir 软件著作权申请资料 --stage <阶段名> --note "<用户确认内容>"
```

必须停住的门禁：

- `environment`：OfficeCLI 缺失时必须由用户确认全局安装并在安装后重启 Codex；版本不匹配时，用户必须切换固定版本或明确承担使用未经验证版本的风险。
- `project`：存在多个项目候选目录时，用户必须指定项目目录。
- `business`：`草稿/业务理解.md` 生成后，用户必须确认行业、目标用户、核心功能和申请口径。
- `application-fields`：`草稿/申请表信息.md` 生成后，用户必须补全并确认硬件、系统环境、著作权人、日期等字段。
- `code-selection`：`草稿/代码文件选择.json` 生成后，用户必须确认或修改抽取文件。
- `screenshot-method`：操作手册截图前，用户必须在 Playwright CLI 自动截图、用户自行截图两种方式中选择一种；如果用户明确说“现在不截图/先跳过截图”，记录为 `skip`。
- `markdown`：全部 Markdown 草稿完成后，用户必须确认可以进入 Word/TXT 生成。

## 工作流

### 1. 启动环境检查

一开始先在当前工作目录创建输出目录并检查运行能力：

```bash
<PYTHON> "<SKILL_DIR>/scripts/check_environment.py" \
  --out-dir 软件著作权申请资料
```

输出：

- `软件著作权申请资料/环境检查.md`
- `软件著作权申请资料/环境检查.json`

环境检查必须告诉用户：

- 当前会在“当前目录/软件著作权申请资料”下生成材料。
- Markdown 草稿、TXT、OfficeCLI DOCX、OpenXML 校验和预览是否可用。
- 当前 OfficeCLI 路径、版本，以及是否等于固定验证版本 `1.0.151`。
- 如 OfficeCLI 缺失，询问用户是否使用官方命令全局安装；不得下载到项目目录或 skill 目录，也不得静默安装。
- 如官方全局安装已完成但当前进程尚未识别，必须要求用户重启 Codex，停止当前执行，重启后重新运行环境检查。

用户选择：

- 如果用户愿意安装，在 Windows PowerShell 中运行 `irm https://raw.githubusercontent.com/iOfficeAI/OfficeCLI/main/install.ps1 | iex`。安装完成后要求用户重启 Codex；不得在当前任务中假定 PATH 已刷新后继续执行。
- 重启后先运行 `officecli --version`，再重新运行环境检查。只使用 PATH 中的全局命令，不使用 `OFFICECLI_PATH`、`--officecli` 或项目内 `工具/officecli.exe`。
- 如果用户坚持使用其他版本，必须先记录 `environment` 门禁，正式生成时显式传入 `--allow-untested-officecli`。
- 没有可用 OfficeCLI 时只能继续生成/修改 Markdown 草稿和 TXT，不得生成伪成功的 DOCX。

用户回复后记录门禁：

```bash
<PYTHON> "<SKILL_DIR>/scripts/confirm_stage.py" \
  --workdir 软件著作权申请资料 \
  --stage environment \
  --note "<用户选择>"
```

不要等到最后验证阶段才发现 OfficeCLI 不可用；这个信息必须在流程开始时给出。

### 2. 定位项目

用户通常会把项目放在当前文件夹下。先扫描当前目录，避开本 skill、自身输出目录、`node_modules`、构建产物和隐藏目录，找到最可能的项目根目录。

如果有多个候选项目，必须停止并询问用户选择；如果只有一个明显候选项目，可以直接使用。

### 3. 分析项目

运行：

```bash
<PYTHON> "<SKILL_DIR>/scripts/analyze_project.py" \
  --project <项目目录> \
  --out 软件著作权申请资料/analysis/project.json
```

分析内容包括：

- `package.json`、README、脚本命令、依赖
- 前端框架和主要编程语言
- 入口文件、路由、页面、组件、接口、状态管理
- 源码文件数量和源程序行数
- 软件名称候选、主要功能候选、运行命令候选

### 4. 形成业务理解

在写申请表和操作手册前，先让脚本收集项目证据：

```bash
<PYTHON> "<SKILL_DIR>/scripts/generate_business_context.py" \
  --project <项目目录> \
  --analysis 软件著作权申请资料/analysis/project.json \
  --software-name "<软件全称>" \
  --out-dir 软件著作权申请资料/草稿
```

输出：

- `草稿/业务理解证据.md`
- `草稿/业务理解证据.json`
- `草稿/业务理解模型稿模板.json`

这一步只收集证据，不决定最终业务口径。接下来必须由模型阅读 `业务理解证据.md/json`、README、PRD/BRD、页面文案、路由、接口、必要源码和用户补充资料，自行判断：

- 应该重点读取哪些文档和源码
- 软件属于什么行业 / 领域
- 目标用户是谁
- 核心价值是什么
- 哪些功能应写入软著申请资料
- 典型操作流程如何组织
- 操作手册适合采用什么章节结构
- 申请表建议口径如何表达

模型不得用脚本关键字表决定行业、功能和结构；不得把用户给的范本文案、测试项目名称、测试项目流程写成通用规则。

模型完成研判后，生成一个业务理解模型稿 JSON，字段至少包含：

- `product_positioning`
- `industry`
- `target_users`
- `core_value`
- `business_features`
- `business_feature_details`
- `operation_flow`
- `application_purpose`
- `main_functions`
- `technical_characteristics`
- `manual_sections`
- `manual_modules`
- `system_requirements`
- `faq`
- `glossary`

其中 `manual_modules` 是操作手册的核心输入，必须按真实页面、导航入口或业务流程填写。脚本不得按 `auth/query/form` 等分类模板自动补入口、步骤或反馈；缺少 `manual_modules` 或关键字段时必须停止让模型回到项目证据中补写。每个模块必须包含：

- `title`：页面或流程名称。
- `evidence`：对应页面、路由、组件、需求文档或 README 证据。
- `purpose`：该页面在软件中的用途。
- `usage` 或 `usage_scenario`：用户在什么业务场景下会使用该页面，正在处理什么具体事务。缺少时不得生成操作手册。
- `entry`：用户从哪里进入该页面。
- `visible_elements`：用户实际能看到的输入框、按钮、列表、标签、状态或结果区域。
- `operation_steps`：按真实页面顺序写用户动作，不能写代码实现。
- `validation_rules`：必填项、长度限制、权限、额度、状态、异常提示等规则；没有则留空数组。
- `feedback`：操作完成后用户能看到的结果、提示或状态变化。
- `screenshot`：截图预留说明。

`manual_sections` 只允许补充当前软件本身的用途、业务场景、页面组织或用户流程，不要写“本操作手册用于……”“面向软著审核……”“不描述代码实现……”这类解释文档写作方式的元话语。最终操作手册应像真实软件说明书，而不是生成过程说明。

然后运行：

```bash
<PYTHON> "<SKILL_DIR>/scripts/generate_business_context.py" \
  --project <项目目录> \
  --analysis 软件著作权申请资料/analysis/project.json \
  --software-name "<软件全称>" \
  --out-dir 软件著作权申请资料/草稿 \
  --model-context <模型生成的业务理解JSON>
```

输出：

- `草稿/业务理解.md`
- `草稿/业务理解.json`

最终业务理解必须覆盖：

- 产品定位
- 面向领域 / 行业
- 目标用户
- 核心价值
- 主要业务功能
- 典型操作流程
- 申请表建议口径
- 证据来源
- 操作手册结构建议

如果项目材料不足、业务类型较新，或用户明确希望参考竞品，可联网搜索相近产品和行业资料；外部调研只用于理解行业表达，不能编造项目不存在的功能。调研摘要应写入业务理解草稿，并区分“项目证据”和“行业参考”。

生成 `业务理解.md/json` 后必须停止，等待用户确认或修改。业务理解确认前，不得生成申请表和操作手册。如果业务理解仍不充分，先请用户补充产品说明。用户确认后运行：

```bash
<PYTHON> "<SKILL_DIR>/scripts/confirm_stage.py" \
  --workdir 软件著作权申请资料 \
  --stage business \
  --note "<用户确认内容>"
```

### 5. 引导用户确认字段

先读取 [application_fields.md](references/application_fields.md)，严格按其中的官网字段顺序、枚举、长度和来源口径向用户确认。项目可推断字段可以先给建议值，著作权人、日期、软件全称、版本号和硬件/系统环境必须由用户明确确认；项目版本小于 V1.0 时，询问本次用 V1.0 还是项目当前版本。

特别注意：

- 软件全称和版本号最终以 `草稿/申请表信息.md` 为准，并统一用于文件名、页眉、标题和正文。
- 源程序量是登记软件全部源程序总行数，不是已选择代码材料的行数。
- 页数是实际提交的代码鉴别材料页数；前后各 30 页模式填 60，不足 60 页时填全部材料页数。
- 软件开发环境/开发工具不要写 React、Vite、TypeScript 等技术栈；字段格式和字符限制见参考文档。

此阶段先停止等待用户输入；收到回复后可整理为 `answers` JSON 传入申请表草稿生成。申请表字段的最终门禁在 `草稿/申请表信息.md` 生成后记录。

### 6. 确认代码文件选择

生成代码材料前，先运行候选文件分析：

```bash
<PYTHON> "<SKILL_DIR>/scripts/propose_code_selection.py" \
  --project <项目目录> \
  --analysis 软件著作权申请资料/analysis/project.json \
  --out-dir 软件著作权申请资料/草稿
```

输出：

- `草稿/代码文件候选清单.md`：给用户看的候选说明。
- `草稿/代码文件选择.json`：可编辑的选择文件。

脚本生成的候选清单只列证据，不默认选择文件。模型必须先阅读业务理解、候选文件、入口文件、页面文件和必要源码，判断哪些源码最能体现软件真实功能和运行逻辑，然后修改 `代码文件选择.json`：

- `selected: true` 表示抽取该文件。
- `selected: false` 表示不抽取该文件。
- `model_reason` 必须说明为什么选择该文件。

模型选择通常优先考虑前端入口、页面、核心组件、业务交互、数据请求、状态处理等能给审核员看懂软件功能的代码；如果相关前端代码不足 60 页，再补充后端服务、业务处理等相关源码。补充文件同样必须写入 `代码文件选择.json` 并由用户确认。不要默认抽取全量代码库。代码材料按完整文件抽取并去除纯空行，不支持只抽取某个文件的中间行段。用户确认并记录 `code-selection` 门禁后，代码抽取只读取 `代码文件选择.json` 中选中的完整文件。用户确认后运行：

```bash
<PYTHON> "<SKILL_DIR>/scripts/confirm_stage.py" \
  --workdir 软件著作权申请资料 \
  --stage code-selection \
  --note "<用户确认内容>"
```

### 7. 生成 Markdown 草稿

运行代码材料抽取：

```bash
<PYTHON> "<SKILL_DIR>/scripts/extract_code_material.py" \
  --project <项目目录> \
  --analysis 软件著作权申请资料/analysis/project.json \
  --selection 软件著作权申请资料/草稿/代码文件选择.json \
  --software-name "<软件全称>" \
  --version "<版本号>" \
  --out-dir 软件著作权申请资料/草稿
```

代码分页规则：

- 代码正文使用 8pt 字号、13pt 固定行距；源码行先按最多 90 显示列预折行，选材量默认按每页约 55 个物理行估算，以满足每页不少于 50 行的要求。Markdown 页分组不等于最终 DOCX 的硬分页边界，生成后必须由 OfficeCLI/Word 重新读取真实页数。
- 正式 DOCX 中所有代码段落连续写入，不插入人工分页符，由 Word 按 A4 页面、页边距、字体和行距自动换页。
- 总页数 `>= 60`：生成 `代码-前30页.md` 和 `代码-后30页.md`。
- 总页数 `< 60` 且候选源码已用尽：只生成 `代码-全部.md`。
- 总页数 `< 60` 但候选清单还有可补充源码：停止并要求用户在 `代码文件选择.json` 中继续选择补充文件。
- 不为大项目生成超大“全量备份 Word”。
- 同时生成 `代码提取清单.md` 和 `代码提取清单.json`，用于追溯代码来源。
- 每次重新抽取都会清理三种代码 Markdown 中与当前输出模式冲突的旧文件；后续步骤只能读取 `代码提取清单.json` 的 `outputs`，不得因为目录里残留旧文件而额外生成材料。

生成申请表信息草稿：

```bash
<PYTHON> "<SKILL_DIR>/scripts/generate_application_info.py" \
  --analysis 软件著作权申请资料/analysis/project.json \
  --code-manifest 软件著作权申请资料/草稿/代码提取清单.json \
  --business-context 软件著作权申请资料/草稿/业务理解.json \
  --software-name "<软件全称>" \
  --version "<版本号>" \
  --out-dir 软件著作权申请资料/草稿
```

生成后必须停止，让用户检查并补全 `草稿/申请表信息.md`。字段补全并确认后运行：

```bash
<PYTHON> "<SKILL_DIR>/scripts/confirm_stage.py" \
  --workdir 软件著作权申请资料 \
  --stage application-fields \
  --note "<用户确认内容>"
```

生成操作手册草稿：

```bash
<PYTHON> "<SKILL_DIR>/scripts/generate_manual_draft.py" \
  --analysis 软件著作权申请资料/analysis/project.json \
  --business-context 软件著作权申请资料/草稿/业务理解.json \
  --software-name "<软件全称>" \
  --version "<版本号>" \
  --out-dir 软件著作权申请资料/草稿
```

操作手册草稿不得照抄用户提供的范本文案或旧项目内容，但应吸收其结构特点：先写相关文档、说明、功能特点和系统要求，再按真实页面或核心流程逐章说明操作，最后写常见问题解答和术语表。一级章节标题使用中文大写序号；相关文档章节必须是表格；功能特点和页面操作章节必须以段落展开，不用项目符号和编号列表堆信息。必须基于模型写入 `草稿/业务理解.json` 的 `manual_modules` 组织章节；`manual_sections` 只用于补充说明性段落，不应用来反复插入同一批功能模块。各功能章节必须写清页面用途、进入位置、用户看到的控件和数据、实际操作、输入限制或异常提示、操作结果和截图预留。语言要面向普通用户，说明“这个页面是干嘛的、用户怎么进入、用户点什么/填什么、操作后看到什么”，不要写代码实现、框架名称、接口封装、状态管理、异步队列等技术细节。撰写时由 agent 自行检查章节是否完整、内容是否过薄、语言是否过于技术化，并在草稿内部完成必要补写；完整草稿完成后只让用户做一次整体确认，确认前不得进入正式 Word/TXT 生成。

生成脚本必须同时写出 `草稿/操作手册自检记录.md` 和 `草稿/操作手册自检记录.json`。自检记录至少包含：

- 第 1 轮：初稿生成，检查章节完整性、截图预留、模块内容厚度和技术化表达。
- 第 2 轮：按项目真实运行流程扩写模块说明，补足上下游衔接关系。
- 第 3 轮：去除制式表达和 AI 味，重点检查重复句式、统一套话、空泛赞美、营销口号、过度整齐的排比和没有项目细节的正确废话。
- 后续轮次：如果仍有问题，继续补写、去重、改写，不能把未修正的问题直接交给用户。

操作手册的模块写作必须从 `草稿/业务理解.json` 的行业、目标用户、核心价值、业务功能、典型操作流程和 `manual_modules` 出发。不同模块要写出各自的业务作用、入口、控件、规则和反馈，不能统一套用“进入页面、填写内容、提交按钮、查看结果”的固定句式，也不能使用“进入方式：/页面内容：/操作步骤：/操作规则：/操作结果与反馈：”这类字段标题；相近模块也要结合项目真实业务区分各自的操作目的和结果。自检时必须检查是否把同一批模块在多个章节中重复展开；如发现重复，改为每个真实页面或流程独立成章。不得把测试项目的功能名称、业务流程或示例文案写成通用规则。

### 8. 选择并获取截图

操作手册草稿完成后，先停止并让用户选择截图方式，必须给出两种选项：

1. Playwright CLI 自动截图：agent 启动或连接 Web 项目，按真实页面和操作流程控制浏览器，并把 PNG 截图直接保存到 `软件著作权申请资料/截图原始/`。
2. 用户自行截图：用户自己把 PNG/JPG/JPEG/WebP 图片放入 `软件著作权申请资料/用户截图/`，agent 只负责整理和引用。

如果用户明确说“现在不截图”“先跳过截图”“这次不截图”，也必须记录截图方式门禁，方法填 `skip`。跳过截图不阻塞正式资料生成，但操作手册中每个核心功能模块必须保留可见的截图预留文字，例如：`【截图预留：请在此处插入“项目管理”页面或操作结果截图。】`。不要使用 HTML 注释作为截图占位，因为正式 Word 中看不到。

用户选择后，先记录门禁：

```bash
<PYTHON> "<SKILL_DIR>/scripts/confirm_stage.py" \
  --workdir 软件著作权申请资料 \
  --stage screenshot-method \
  --method <playwright-cli|user-supplied|skip> \
  --note "<用户选择>"
```

然后按用户选择检查当前能力并执行：

- 选择 Playwright CLI 自动截图：必须先读取 [playwright_cli_screenshots.md](references/playwright_cli_screenshots.md)，运行其中的通用全局命令检查脚本，并按返回的可执行文件绝对路径、安装门禁、固定版本、后台服务、命名、浏览器会话和落盘校验规则执行。不得因裸命令不在 PATH 就要求重启 Codex，也不得改用只能把截图显示在会话中的浏览器工具冒充成功；每张截图都必须是 `截图原始/` 下可读取且非空的本地图片文件。
- 选择用户自行截图：创建 `软件著作权申请资料/用户截图/`，提示用户把截图文件放入该目录；用户按操作手册模块顺序给文件名添加数字前缀后，运行下面的整理命令，把图片复制到 `软件著作权申请资料/截图/` 并生成有序的 `截图清单.json`。数字前缀按数值排序，因此 `2-主页.png` 会排在 `10-设置.png` 前面。
- 选择跳过截图：不运行截图工具，继续保留操作手册中的可见截图预留文字；在生成报告中说明用户选择暂不截图，正式操作手册已预留截图位置。

截图文件准备好后必须运行整理脚本，生成正式构建会读取的 `截图/截图清单.json`。Playwright CLI 自动截图把 `--input-dir` 指向 `截图原始/`、`--method` 设为 `playwright-cli`；用户自行截图则指向 `用户截图/`：

```bash
<PYTHON> "<SKILL_DIR>/scripts/capture_screenshots.py" \
  --input-dir 软件著作权申请资料/用户截图 \
  --out-dir 软件著作权申请资料/截图 \
  --method user-supplied
```

截图成功后无需手工修改 `草稿/操作手册.md`：正式生成脚本会按 `截图清单.json` 中的顺序，把可用图片依次替换到操作手册的可见截图预留位置，再通过 OfficeCLI `picture` 元素写入 Word。图片少于预留位时保留未匹配提示；图片多于预留位、文件缺失或格式不支持时在生成报告中说明。截图失败或用户选择暂不提供截图时，继续生成带截图预留位的文字版。

### 9. 用户确认 Markdown

生成 Word 前，必须让用户确认 `软件著作权申请资料/草稿/` 下的 Markdown。

重点检查：

- 软件名称和版本号是否一致
- 代码材料前30页、后30页页眉软件名称是否与 `申请表信息.md` 的“软件全称”一致
- 代码材料前30页、后30页页眉版本号是否与 `申请表信息.md` 的“版本号”一致
- 操作手册 Word 页眉是否与代码材料页眉一致，均使用 `申请表信息.md` 的“软件全称”和“版本号”
- `业务理解.md` 是否准确反映软件真实业务、行业和目标用户
- `申请表信息.md` 中“待用户确认”的字段是否已确认
- 代码材料是否只来自用户确认的完整文件
- 操作手册是否符合审核员阅读场景，普通读者是否能看懂模块用途和操作方式
- 操作手册每个章节是否有段落内容，核心模块是否写清模块用途、操作过程和结果反馈，是否避免过度技术化语言
- 截图是否正确；若用户跳过截图，正式操作手册是否保留可见截图预留位置

用户确认后，必须记录 `markdown` 门禁；未记录时不得生成正式 Word/TXT。

确认脚本会为业务理解、代码选择、申请表和最终草稿记录内容指纹。任何已确认文件在确认后又发生修改，对应门禁立即失效，必须让用户查看变化并重新确认；不能沿用旧的确认布尔值。最终确认前还必须检查代码提取清单、当前代码 Markdown、申请表、操作手册和操作手册自检记录全部存在，且没有与当前代码输出模式冲突的旧草稿。

```bash
<PYTHON> "<SKILL_DIR>/scripts/confirm_stage.py" \
  --workdir 软件著作权申请资料 \
  --stage markdown \
  --note "<用户确认内容>"
```

### 10. 生成正式 Word/TXT

用户确认后运行：

```bash
<PYTHON> "<SKILL_DIR>/scripts/build_docx_from_md.py" \
  --workdir 软件著作权申请资料 \
  --software-name "<软件全称>" \
  --version "<版本号>"
```

正式生成脚本必须重新读取 `草稿/申请表信息.md` 中已确认的“软件全称”和“版本号”，并用它们生成正式资料文件名、代码 Word 页眉和操作手册 Word 页眉。操作手册页眉必须与代码材料页眉格式一致：左侧为“软件全称 版本号”，右侧为“第 <页码> 页”。若命令参数 `--software-name` / `--version` 与申请表字段不同，以申请表字段为准，并在 `正式资料/生成报告.md` 中记录提示。

生成脚本通过 OfficeCLI 原子 batch 写入 DOCX，并关闭自动更新与后台 resident。代码草稿中的每个物理行对应一个 Word 段落；超过 90 显示列的源码行在抽取阶段确定性折行，避免 Word 因代码宽度再次换行而造成页数漂移。所有代码段落连续写入正文，不设置 `pageBreakBefore`，最终分页由 Word 排版引擎自动完成；草稿中的页分组只用于选材量估算。不要启用 Word 自动行号替代源码行处理。

正式生成只处理 `草稿/代码提取清单.json` 的 `outputs` 中声明的代码 Markdown，并清理当前软件名下与本次模式冲突的旧代码 DOCX。不能遍历目录后把前 30 页、后 30 页和全部代码三种旧文件一起输出。

输出：

- `正式资料/申请表信息.txt`
- 代码达到或超过 60 页：
  - `正式资料/<软件全称>-代码(前30页).docx`
  - `正式资料/<软件全称>-代码(后30页).docx`
- 代码不足 60 页：
  - `正式资料/<软件全称>-代码(全部).docx`
- `正式资料/<软件全称>_操作手册.docx`
- `正式资料/生成报告.md`

### 11. 三轮验证

至少执行三轮验证并修复发现的问题：

1. 文件完整性：目标 Word/TXT 是否存在且非空。
2. 代码真实性：抽样检查代码片段能回溯到项目源码。
3. 业务真实性：申请表和操作手册中的行业、目标用户、主要功能、操作流程能回溯到 `业务理解.md` 和项目文档。
4. 一致性和格式：软件名称、版本号、页数规则、申请表字段、操作手册标题和截图引用是否一致。

可用命令：

```bash
<PYTHON> -m compileall -q "<SKILL_DIR>/scripts"
officecli validate <生成的docx> --json
officecli view <生成的docx> issues --json
officecli view <生成的代码docx> stats --page-count --json
officecli view <生成的docx> screenshot --grid auto --render auto -o <预览.png>
```

`validate` 只证明 OpenXML 结构可读，不能证明分页正确。Windows 且安装 Word 时由 OfficeCLI 使用 `stats --page-count` 读取自动分页后的真实页数；前 30 页/后 30 页文档必须分别正好 30 页，否则生成失败并要求重新校准选材量，不得改回人工固定分页。其他环境先用 OfficeCLI HTML 预览，再用 Word/WPS 打开最终文件复核页数。只使用 OfficeCLI 后端，不引入其他 DOCX 渲染依赖。

## 何时询问用户

以下场景必须询问并停止，等待用户输入后再继续：

- 多个项目候选目录需要选择。
- 启动环境检查发现 OfficeCLI 缺失时，询问用户是否全局安装；安装完成后要求重启 Codex 并停止，重启后再继续。版本不匹配时询问是否切换固定版本。
- 业务理解草稿生成后，请用户确认软件用途、行业、目标用户、核心功能和申请口径。
- 软件全称、著作权人、日期、硬件/系统环境等登记字段需要确认。
- 代码文件候选清单生成后，需要用户确认或修改 `代码文件选择.json`。
- 操作手册截图前，需要用户在 Playwright CLI 自动截图、用户自行截图两种方式中选择一种；选择自动截图后再检查固定验证版本是否可用。
- 用户是否确认 Markdown 草稿并进入 Word 生成。
