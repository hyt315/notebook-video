# 📦 Notebook Video / 手账风教学视频制作

<div align="center">

**把一句话变成一支 2K 中文教学视频：纯代码绘制场景、帧精确对齐配音、镜头语言由门禁托底。**

**Turn one sentence into a 2K Chinese explainer video: code-drawn scenes, frame-accurate TTS sync, camera language enforced by automated gates.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/hyt315/notebook-video?sort=semver)](https://github.com/hyt315/notebook-video/releases)
[![Validate](https://github.com/hyt315/notebook-video/actions/workflows/validate.yml/badge.svg)](https://github.com/hyt315/notebook-video/actions/workflows/validate.yml)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-1f6feb)](SKILL.md)
[![GitHub Stars](https://img.shields.io/github/stars/hyt315/notebook-video?style=social)](https://github.com/hyt315/notebook-video/stargazers)

[English](README.en.md) | 中文

</div>

---

---

## 📖 这是什么？

这是一个给 AI 助手用的**视频生产系统**。你说一句「做一支讲 XX 的科普视频」，它负责把这件事从头做到尾：写口播稿 → 生成中文配音 → 取毫秒级词时间戳 → 切成语义断句的字幕 → 排分镜 → 画场景 → 跑门禁 → 渲染出 2K 成片，并同时交付可编辑的 Remotion 源码。

难点从来不是「能不能画出来」，而是画出来**像不像 PPT**、字幕**对不对得齐**、元素**会不会互相压**。这个技能把这三件事都做成**可被自动拒绝的门禁**：骨架必须换、视觉介质必须换、镜头必须真的动、字幕必须用真实字体实测放得下、文字不许互相压——**P0 不为 0 就拒绝渲染**。

画面全部由代码绘制（React + SVG + Remotion），默认**不依赖任何生图模型**；需要「这确实是官方界面 / 官方图表」这类论据时，也可以把真实截图装进实拍素材框。

---

---

## ✨ 核心特性

| 核心特性 | 功能说明 | 带来价值 |
| --- | --- | --- |
| **一句话成片** | 从主题到 2K MP4：写稿 → 配音 → 词级时间戳 → 语义断句字幕 → 分镜 → 场景 → 门禁 → 渲染 → 接触表验收 | 不用手工排帧、不用逐句对字幕 |
| **四种场景骨架** | `Stage`（一个主体演化）/ `Corridor`（对象沿轨道穿站）/ `Split`（双栏对比）/ `Zoom`（整体→聚焦→标注→回整体）；**相邻场景不得同款、全片 ≥3 种** | 从结构上消灭「四个 PPT 页」 |
| **内容 → 视觉介质路由** | 控制台窗 / 图表 / 代码补丁 / 大字 / 指标网格 / 概念图；**每支片 ≥3 种介质**，每个讲解场景至少一个**会随旁白变状态**的组件 | 画面不再只有「卡片 + 文字」一种介质 |
| **受限镜头语言** | 每镜 6 种意图 + `anchor` 出界证明 + 平移预算；**声明了运镜就必须真的动** | 有运镜但不失控：内容永远不会被推出画面 |
| **十四道质量门禁** | 构建期 6：分镜→帧号解析、镜头出界证明、构图与密度、**帧参数名核对**、**音效电平**、**呈现效果（讲与画对齐 / 字幕阅读预算 / 字号与对比度）**；渲染期 7：字幕宽度、卡片溢出、**文字重叠与遮挡**、**图形被裁**、**画布越界**、**下 1/4 实测密度**、**槽占用率**；成片后验 1：**画面到底动没动** | P0 不为 0 **拒绝渲染**；每次还打覆盖率，**「没报警」与「没运行」能区分开** |
| **实拍素材框** | 真实截图 / 官方图表装进锁定皮肤的墨线框（2.5px 描边 + 硬阴影），可缓慢推近到关键处；素材按 `visual-assets.json` + `asset-manifest.json` **双清单登记**（来源 / 授权 / 是否含文字 / 校验和） | 需要「这确实是官方 / 真实」的论据时用它；能用代码讲清的仍用画的 |
| **帧精确中文 TTS 同步** | 毫秒级词时间戳 → 语义断句 → 动画节拍；句末标点严格消除 | 告别字幕对不准、音画脱节 |
| **四套锁定皮肤** | `paper`（暖白手账，默认）/ `cel`（动漫赛璐璐）/ `sticker`（贴纸）/ `flat`（扁平几何） | 一套内容，四种气质 |
| **背景可读性契约** | 锁定背景位图**保持原样不改**；压在装饰上的内容坐在**半透明**羽化底托上（面板 88%、底托中心 76%） | 不靠「纯白挡板」换可读性，画面才不会变成白底 PPT |

---

---

## 🎨 视觉成片与画幅

![Notebook Video 成片演示](assets/demo/notebook-video-demo.webp)

▶️ [观看完整演示视频（MP4）](assets/demo/notebook-video-demo.mp4) · 主视觉参考：[hero.png](assets/demo/hero.png)

▶️ [组件接触表（MP4）](assets/demo/notebook-video-components-demo.mp4) — `NotebookVideoShowcase` 的组件接触表：18 页、每页 1 秒（抽帧用 select 滤镜按帧号取每页第 6/21 帧两张中段图，6×6=36 格一张 JPG），覆盖数据 / 控制台 / 卡片 / 对话 / 镜头意图 / 场景骨架 / 字效，以及 10 页封装层（图表变体、层级与关系、弹层与形状、手绘风与公式、注意力 FocusFx 四态轮转）。

> 接触表那支 MP4 是 **2560×1440**（对齐 16:9 锁定画布）：composition 原生画布是 1920×1080，交付渲染时按 4/3 放大；音轨是一条**静音 AAC**（该 composition 本身不挂音频，音轨由交付链路补上）。
> 想核对当前版本：在 `assets/lecture-template` 里 `npm install` 后跑 `npm run still`（抽帧）；**要出片请走交付链路** `node scripts/notebook-video.mjs render <工程> <输出>` —— 它会做色彩元数据回写与响度归一，而 `npm run render` **不做**这一步，产出的文件过不了 `validate-video` 的色彩断言。
> 接触表同理：`node scripts/notebook-video.mjs showcase <工程目录>` 现在**直接出交付规格**（2560×1440 / 静音 AAC / 色彩四项回写，与 `assets/demo/` 里那份一致）。`--scale` 只吃十进制字面量 —— `--scale=4/3` 会被 CLI 拒绝，要写 `1.3333333333333333`。

**画布**：锁定三种画布 —— 16:9（2560×1440）、4:3（1920×1440）、3:4 竖屏（1440×1920），均为原生 30fps。官方示例片按 **16:9 设计空间**编写；4:3 / 3:4 需要各自的版面重排（**不再用信箱化缩放冒充适配**），在做竖屏时按 [`references/canvas-modes.md`](references/canvas-modes.md) 与 [`references/portrait-illustration-system.md`](references/portrait-illustration-system.md) 单独编写场景。

***

---

## 📊 制作全流程

```
[输入：知识主题 / 文案脚本]
        │
  ① 锁内容 ── narration.txt + 语义字幕行（一行一条 cue）
        │
  ② 写分镜表 ── manifests/shots.json
        │    只声明「这一镜覆盖哪几句 cue」＋骨架/介质/活性组件/镜头意图/anchor
        │
  ③ 解析 ────── resolve-shots.py → src/shots.ts（帧号与相机关键帧全部自动生成）
        │
  ④ 写场景 ──── 四种骨架 + 介质组件；每镜用 ShotCamera(keys, anchor) 包裹
        │    元素出现帧绑定到「讲到它的那一句」，入场 22 帧缓动
        │
  ⑤ 构建期门禁 ─ validate-shot-motion.py（P0 必须 0）
        │        validate-composition.py（P0 必须 0）
        │
  ⑥ 渲染 ────── Remotion 渲染 + 响度归一（-16 LUFS / -1.5 dBTP）
        │
  ⑦ 渲染期门禁 + 交付 ─ CaptionFitGate / CardFitGate / OverlapGate / ClippingGate / CanvasBoundsGate / FillGate / SlotGuard
                        （成片之后还要跑 validate-motion-gaps：画面"真的没动"只有它抓得到）
                        → 2K MP4 + 18 页接触表 + 可编辑源码 ZIP
```

***

---

## 🚀 快速开始

这是一个标准的 AI Agent Skill —— 安装到你的 AI 助手后即可直接使用。

### 方式 A：把一句话发给任意 Agent（最推荐、最通用）

把下面这句话直接复制发送给你的 AI 助手，它会自动识别环境并克隆到正确的技能目录：

> 请安装 notebook-video 技能：克隆 `https://github.com/hyt315/notebook-video` 到你的 skills 目录（如 `~/.claude/skills/notebook-video` 或 `~/.agents/skills/notebook-video`），并确认安装成功。以后我要做「科普视频 / 手账风动画 / 产品宣传片 / 讲解概念」时，按 SKILL.md 的工作流制作 2K 视频。

### 方式 B：GitHub CLI 2.90+（一行命令）

```bash
gh skill install hyt315/notebook-video notebook-video --agent claude-code --scope user
```

### 方式 C：多平台手动安装

| 平台 | 用户级安装路径 | 项目级安装路径 |
| --- | --- | --- |
| **Claude Code** | `git clone https://github.com/hyt315/notebook-video.git ~/.claude/skills/notebook-video` | `.claude/skills/notebook-video` |
| **Codex** | `git clone https://github.com/hyt315/notebook-video.git ~/.codex/skills/notebook-video` | `.codex/skills/notebook-video` |
| **Cursor** | `git clone https://github.com/hyt315/notebook-video.git ~/.cursor/skills/notebook-video` | `.cursor/skills/notebook-video` |
| **通用 Agents** | `git clone https://github.com/hyt315/notebook-video.git ~/.agents/skills/notebook-video` | `.agents/skills/notebook-video` |

### 方式 D：本地回归自测（不渲染）

```bash
python scripts/selftest.py
```

---

---

## 📚 端到端实战演示

假设你要做一支《某个新模型值不值得切》的 3 分钟科普片。全程四条命令、零手改帧号：

```text
# ① 建工程（复制模板，锁定皮肤）
node scripts/notebook-video.mjs new-project ./my-video --style=cel

# ② 写旁白与字幕行（两份文件必须逐字互相还原；数字写成中文读法）
#    narration.txt          每行 = 一个语音段（= 一章）
#    manifests/semantic-caption-lines.txt   字幕行，拼接后等于旁白原文
python <模板>/scripts/tts-openai-compatible.py ./my-video     # 配音 + 词级时间戳
python <模板>/scripts/speed-post.py ./my-video 1.10           # 定速（不改音高，全时间轴同步缩放）
node scripts/notebook-video.mjs build-semantic-captions audio/narration.mp3.json manifests/semantic-caption-lines.txt manifests/caption-cues.json

# ③ 写分镜表（只写"这一镜覆盖哪几句旁白"，绝不写帧号）
#    manifests/shots.json → resolve-shots.py 推出帧号与相机关键帧

# ④ 跑门禁 → 渲染
python scripts/validate-frame-props.py ./my-video     # 帧参数名（最高频的静默事故）
python scripts/validate-shot-motion.py ./my-video     # 出界证明 / 平移预算 / 运镜配额
python scripts/validate-composition.py ./my-video     # 骨架 / 介质 / 枚举 / 节奏
python scripts/validate-audio-levels.py ./my-video    # 音效素材不能录太轻
node scripts/notebook-video.mjs render ./my-video out.mp4
```

渲染期还会自动拦下"文字互相压""卡片内容被裁""字幕超宽"——**P0 不为 0 就不会出片**，
而不是等你逐帧看图时才发现。

---

## ⚙️ 前置依赖

- **Node.js 18+**（Remotion 渲染引擎依赖）
- **ffmpeg**（抽帧、接触表、响度归一；做 QA 时需要）
- 首次渲染前用 `node scripts/notebook-video.mjs check-deps` 做环境体检与 Chromium 内核准备

常用命令（完整列表见 `--help`）：

```text
node scripts/notebook-video.mjs new-project   ./my-video --style=paper
node scripts/notebook-video.mjs resolve-shots ./my-video
python scripts/validate-frame-props.py        ./my-video
python scripts/validate-shot-motion.py        ./my-video
python scripts/validate-composition.py        ./my-video
node scripts/notebook-video.mjs showcase      ./my-video     # 组件接触表（看图选型）
node scripts/notebook-video.mjs render        ./my-video out.mp4
node scripts/notebook-video.mjs review-frames ./my-video r.mp4 0 570
```

---

---

## 🔒 安全与隐私原则

- **纯只读 / 先审后改**：依赖体检与前置校验默认只读测量，不擅自修改系统环境变量与系统配置；
- **零 Token 本地运行**：渲染与门禁全部在本机完成，不需要任何在线 API 额度；配音走你自己的 TTS 端点，密钥只从环境变量读取、不落盘；
- **确定性可复现**：纯代码驱动，所有动画都是帧号的纯函数（禁用 `Math.random`、禁用 CSS 动画与计时器）。**口径要说清**：**still / PNG 逐字节可复现**（同一帧渲两次哈希一致，接触表就是这么验的）；**长片段 mp4 不保证逐字节**——x264 在长片段上的多线程/前瞻决策会让连渲两次的 md5 不同，实测像素差只落在边缘少数点（最大 76、平均 0.12、95.2% 字节相同），属编码层噪声而非内容差异；
- **门禁优先**：能用算术在构建期证明的，就不留到渲染期；只有需要真实字体 / 布局测量的才放在浏览器内；
- **全源码完整交付**：成片不仅交付 MP4，同时交付整套干净的 Remotion React 源码包。

---

---

## 📥 下载与获取

| 方式 | 命令 / 链接 |
| --- | --- |
| **HTTPS** | `git clone https://github.com/hyt315/notebook-video.git` |
| **SSH** | `git clone git@github.com:hyt315/notebook-video.git` |
| **ZIP** | [下载 ZIP](https://github.com/hyt315/notebook-video/archive/refs/heads/main.zip) |
| **单文件** | `curl -O https://raw.githubusercontent.com/hyt315/notebook-video/main/SKILL.md` |
| **版本记录** | [CHANGELOG.md](CHANGELOG.md) |

---

---

## 📖 参考文档导读

`references/` 是按需加载的，不是一次读完。按 SKILL.md 的读取时机，最容易踩的顺序是这几份：

| 时机 | 文档 | 解决什么 |
|---|---|---|
| **动手前** | [`locked-style-contract.json`](references/locked-style-contract.json) | 绑定令牌、坐标与禁用项（不可改） |
| **写场景前** | [`scene-authoring.md`](references/scene-authoring.md) · [`scene-skeletons.md`](references/scene-skeletons.md) | 场景代码的标准形状、四种骨架、十个反复踩的坑 |
| **选组件前** | [`media-routing.md`](references/media-routing.md) 的「修辞动作 → 组件」表 · [`fxkit.md`](references/fxkit.md) | 这个动作该用哪一件、**何时别用**、`frame` 与 `f` 的命名陷阱 |
| **排分镜前** | [`media-routing.md`](references/media-routing.md) · [`shot-language.md`](references/shot-language.md) | 内容→介质路由、六个运镜意图（+ `still`）、缩放与平移预算 |
| **写作前** | [`narrative-hook.md`](references/narrative-hook.md) · [`pacing-rhythm.md`](references/pacing-rhythm.md) | 前 3 秒怎么抓人、章节能量与呼吸 |
| **做完对照** | [`composition-gate.md`](references/composition-gate.md) · [`quality-checklist.md`](references/quality-checklist.md) | 每道门禁的判据、失败怎么修、交付事实卡 |
| **配音与字幕** | [`tts-audio.md`](references/tts-audio.md) · [`subtitle-timing.md`](references/subtitle-timing.md) | 多音字规避、定速、词级时间戳、音效词汇 |
| **出问题** | [`windows-compatibility.md`](references/windows-compatibility.md) · [`cross-platform-compatibility.md`](references/cross-platform-compatibility.md) · [`performance-design.md`](references/performance-design.md) | 跨平台、路径、渲染性能 |

---

## 📁 文件结构

```
notebook-video/
├── SKILL.md                          # 核心技能定义与制作工作流
├── manifest.json                     # 技能元数据（版本号在此）
├── README.md / README.en.md          # 中英文说明
├── CHANGELOG.md                      # 版本发布记录（当前 v3.1.2）
├── assets/
│   ├── demo/                         # 成片与动图预览
│   ├── lecture-template/             # 官方模板（纯代码路线，含 8 镜示例片）
│   └── example-project/              # 经典路线示例（可选生图附加）
├── scripts/                          # 全部为 Python 标准库 / Node（本目录不引第三方包）
│   ├── notebook-video.mjs            # 跨平台统一启动器（含 showcase 等命令）
│   ├── resolve-shots.py              # 分镜表 → 帧号与相机关键帧
│   ├── validate-shot-motion.py       # 构建期：镜头出界证明 + 运镜配额
│   ├── validate-composition.py       # 构建期：骨架 / 活性组件 / 介质 / 密度
│   ├── validate-caption-sync.py      # 字幕与 TTS 词边界一致
│   ├── validate-semantic-breaks.py   # 保护短语不被切断
│   ├── selftest.py                   # 端到端回归自测
│   └── …                             # TTS 对齐、重定时、打包、依赖体检等
└── references/                       # 按需加载的规范与手册
    ├── scene-authoring.md            # ★ 场景编写说明书（照着抄）
    ├── shot-language.md              # 镜头意图、缩放预算、出界证明
    ├── scene-skeletons.md            # 四种骨架与分镜表结构
    ├── media-routing.md              # 内容→介质路由、A/B 场景、背景契约
    ├── composition-gate.md           # 全部门禁的判据与修法
    ├── motion-design.md              # 多时钟动效六律
    ├── theme-*.md / visual-system.md # 四套皮肤契约
    └── …                             # TTS、字幕、画布、性能与跨平台手册
```

模板内的源码分层（`assets/lecture-template/src/`）：

```
index.tsx          引擎：画布/字幕/章节卡/资产门/渲染期门禁 + 镜头边界交接
shotkit.tsx        镜头层：ShotCamera / 6 意图 / anchor 证明 / 景深 / 底托
stagekit.tsx       骨架 Stage：StageFrame + 状态机 + PhaseRail + SlotGuard（Attach 已删）
skeletons.tsx      骨架 Corridor / Split / Zoom
media.tsx          介质：ConsoleWindow / MetricGrid / StampBanner
fxkit.tsx          9 个动效构件（多时钟动效）
toolkit.tsx       修辞工具件：Callout(画圈标注)/Checklist(清单)/JumpInText(逐字跳入) …… 可直接 import
│   └── components/      封装组件层：Accordion/Tabs/HighlightCode/Chart/StatRow/GlowFrame/PathDraw/FitTextBox …… 场景从这里 import
kit.tsx            主题无关原子：PillTag / LineIcon / CheckBadge / TYPE
insert.tsx         B 场景插入镜头 + 3 式转场（cut / handoff / reveal）
overlap-gate.tsx   渲染期重叠/遮挡门禁（事件帧抽样：镜头边界/节拍/相机关键帧）
clipping-gate.tsx  渲染期图形被裁门禁（SVG 图元越出会裁切的祖先）
canvas-bounds-gate.tsx 渲染期画布越界门禁（含文字的叶元素，墨迹 rect 越出画布；接触表 block、片子 warn）
fill-gate.tsx      渲染期下 1/4 实测密度门禁（信息元素最低边 vs y=876）
showcase.tsx       组件接触表（18 页，供 AI 看图选型）
scenes.tsx         场景层（示例片 8 镜；换题材重写这一层）
```

***

---

## ❓ 常见问题 (FAQ)

- **Q：做视频要花钱调用生图 API 吗？**\
  A：不需要。默认路线 100% 用 React + SVG 代码绘制，零生图成本。

- **Q：那能用开源的 UI 组件库吗？**\
  A：能，而且鼓励。被禁的只有「按次付费、结果不可复现」的生成式模型；开源库随模板一次 `npm install` 装好就能直接 `import`，不需要额外授权。边界见 [references/dependency-policy.md](references/dependency-policy.md)。

- **Q：怎么保证做出来不像 PPT？**\
  A：靠四层，而且都有门禁兜底：① 四种构图不同的骨架，**相邻场景不得同款**；② **每支片 ≥3 种视觉介质**、每个讲解场景至少一个会随旁白变状态的组件；③ 每章至少 3 次运镜（全片按片长配额），景别真的会变；④ 门禁 P0 不为 0 就**拒绝渲染**。

- **Q：怎么保证文字不会互相压、不会被盖住？**\
  A：渲染期有 `OverlapGate`（每 15 帧抽样，检测文字两两重叠与绘制顺序遮挡，用 `Range` 量真实字形矩形）、`ClippingGate`（图形被 `overflow` 祖先或 `<svg>` 视口裁掉一块——文字门禁看不见这类"缺了半边的球"）、`CanvasBoundsGate`（**含文字的叶元素**的墨迹 rect 越出画布——管的是"整件被画布裁掉或被切掉一块"；接触表上硬拦、片子上只出声）、`FillGate`（下 1/4 到底填没填：量信息元素的最低边 vs y=876，构建期那条只查声明字段在不在）与 `SlotGuard`（量 `StageFrame` 的 main 槽**占用了百分之几**——槽给足了高度、内容却只留一行字，会报出「只用了 11%」）——它们会指出"哪一帧、哪两处、压了多少 px"。**有意的重叠**（镜头交接、标题滑变、数值替换）必须显式标 `data-gate-allow`，不允许用白名单掩盖两个不同信息互相压字。成片之后再跑 `validate-motion-gaps`：连续静止超过阈值（"画面上真的没动"）只有它能抓到。

- **Q：字幕为什么不会溢出或被裁？**\
  A：`CaptionFitGate` 在真实渲染浏览器里用**当前画布与当前主题**的真实字号/字重/字距测量每一条字幕；超过安全宽直接拒绝渲染。

- **Q：改动台词要重新对帧吗？**\
  A：不用。分镜表只写"这一镜覆盖哪几句"，帧号、镜头关键帧、音效钉帧都由 `resolve-shots.py` 从 TTS 词级时间戳推出。

- **Q：支持哪些平台？**\
  A：输出标准 H.264/AAC 的 2K MP4，原生适配 B站、YouTube、抖音、小红书、微信视频号。

***

---

## 🤝 参与贡献

欢迎提交 Issue 与 Pull Request！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。如果这个技能对你有帮助，欢迎在 GitHub 上点个 [Star ⭐](https://github.com/hyt315/notebook-video/stargazers)！

***

---

## 📄 开源协议

本项目采用 [Apache License 2.0](LICENSE) 开源。随包第三方素材（LXGW 楷体正文、音效、Remotion 依赖、TTS 提供方等）的授权与归属见 [NOTICE](NOTICE)，第三方依赖清单见 [DEPENDENCIES.md](DEPENDENCIES.md)。
