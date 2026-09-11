# 📦 Notebook Video / 手账风教学视频制作

<div align="center">

**把一句话变成一支 2K 中文教学视频：纯代码绘制场景、帧精确对齐配音、镜头语言由门禁托底。**

**Turn one sentence into a 2K Chinese explainer video: code-drawn scenes, frame-accurate TTS sync, camera language enforced by automated gates.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/hyt315/notebook-video?sort=semver)](https://github.com/hyt315/notebook-video/releases)
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
| **八道质量门禁** | 构建期 4：分镜→帧号解析、镜头出界证明、构图与密度、**帧参数名核对**；渲染期 4：字幕宽度、卡片溢出、**文字重叠与遮挡**、槽内溢出 | P0 不为 0 **拒绝渲染**；每次还打覆盖率，**「没报警」与「没运行」能区分开** |
| **实拍素材框** | 真实截图 / 官方图表装进锁定皮肤的墨线框（2.5px 描边 + 硬阴影），可缓慢推近到关键处；素材按 `visual-assets.json` + `asset-manifest.json` **双清单登记**（来源 / 授权 / 是否含文字 / 校验和） | 需要「这确实是官方 / 真实」的论据时用它；能用代码讲清的仍用画的 |
| **帧精确中文 TTS 同步** | 毫秒级词时间戳 → 语义断句 → 动画节拍；句末标点严格消除 | 告别字幕对不准、音画脱节 |
| **四套锁定皮肤** | `paper`（暖白手账，默认）/ `cel`（动漫赛璐璐）/ `sticker`（贴纸）/ `flat`（扁平几何） | 一套内容，四种气质 |
| **背景可读性契约** | 锁定背景位图**保持原样不改**；压在装饰上的内容坐在**半透明**羽化底托上（面板 88%、底托中心 76%） | 不靠「纯白挡板」换可读性，画面才不会变成白底 PPT |

---

---

## 🎨 视觉成片与画幅

![Notebook Video 成片演示](assets/demo/notebook-video-demo.webp)

▶️ [观看完整演示视频（MP4）](assets/demo/notebook-video-demo.mp4) · 主视觉参考：[hero.png](assets/demo/hero.png)

▶️ [组件库与动效演示（MP4）](assets/demo/notebook-video-components-demo.mp4) — 锁定图标集、代码窗 / 浏览器壳 / 连件 / 清单 / 计数 / 进度条 / 手绘标注、转场、文字动效、物理件与主题皮肤。

**画布**：锁定三种画布 —— 16:9（2560×1440）、4:3（1920×1440）、3:4 竖屏（1440×1920），均为原生 30fps。官方示例片按 **16:9 设计空间**编写；4:3 / 3:4 需要各自的版面重排（**不再用信箱化缩放冒充适配**），在做竖屏时按 `references/canvas-modes.md` 与 `references/portrait-illustration-system.md` 单独编写场景。

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
  ⑦ 渲染期门禁 + 交付 ─ CaptionFitGate / CardFitGate / OverlapGate / SlotGuard
                        → 2K MP4 + 24 帧接触表 + 可编辑源码 ZIP
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
- **确定性可复现**：纯代码驱动，所有动画都是帧号的纯函数（禁用 `Math.random`、禁用 CSS 动画与计时器）；
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
| **动手前** | `locked-style-contract.json` | 绑定令牌、坐标与禁用项（不可改） |
| **写场景前** | `scene-authoring.md` · `scene-skeletons.md` | 场景代码的标准形状、四种骨架、十个反复踩的坑 |
| **选组件前** | `media-routing.md` 的「修辞动作 → 组件」表 · `fxkit.md` | 这个动作该用哪一件、**何时别用**、`frame` 与 `f` 的命名陷阱 |
| **排分镜前** | `media-routing.md` · `shot-language.md` | 内容→介质路由、六个镜头意图、缩放与平移预算 |
| **写作前** | `narrative-hook.md` · `pacing-rhythm.md` | 前 3 秒怎么抓人、章节能量与呼吸 |
| **做完对照** | `composition-gate.md` · `quality-checklist.md` | 每道门禁的判据、失败怎么修、交付事实卡 |
| **配音与字幕** | `tts-audio.md` · `subtitle-timing.md` | 多音字规避、定速、词级时间戳、音效词汇 |
| **出问题** | `windows-compatibility.md` · `cross-platform-compatibility.md` · `performance-design.md` | 跨平台、路径、渲染性能 |

---

## 📁 文件结构

```
notebook-video/
├── SKILL.md                          # 核心技能定义与制作工作流
├── manifest.json                     # 技能元数据（版本号在此）
├── README.md / README.en.md          # 中英文说明
├── CHANGELOG.md                      # 版本发布记录（当前 v3.0.0）
├── assets/
│   ├── demo/                         # 成片与动图预览
│   ├── lecture-template/             # 官方模板（纯代码路线，含 8 镜示例片）
│   └── example-project/              # 经典路线示例（可选生图附加）
├── scripts/                          # 全部为 Python 标准库 / Node，零第三方依赖
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
stagekit.tsx       骨架 Stage：StageFrame + 状态机 + PhaseRail + Attach + SlotGuard
skeletons.tsx      骨架 Corridor / Split / Zoom
media.tsx          介质：ConsoleWindow / MetricGrid / StampBanner
fxkit.tsx          18 个动效构件（多时钟动效）
toolkit.tsx       修辞工具件：Callout(画圈标注)/Connector(关系箭头)/WaveText/JumpInText/CountUp/Checklist/CodeBlock/BrowserChrome …… 可直接 import
plates.tsx         实拍素材框 ShotPlate（真截图/官方图表 + 素材双清单登记）
kit.tsx            主题无关原子：PillTag / LineIcon / CheckBadge / TYPE
insert.tsx         B 场景插入镜头 + 5 式转场
overlap-gate.tsx   渲染期重叠/遮挡门禁
overlap-gate.tsx   渲染期重叠/遮挡门禁（事件帧抽样：镜头边界/节拍/相机关键帧）
showcase.tsx       组件接触表（6 页，供 AI 看图选型）
scenes.tsx         场景层（示例片 8 镜；换题材重写这一层）
```

***

---

## ❓ 常见问题 (FAQ)

- **Q：做视频要花钱调用生图 API 吗？**\
  A：不需要。默认路线 100% 用 React + SVG 代码绘制，零生图成本。

- **Q：怎么保证做出来不像 PPT？**\
  A：靠四层，而且都有门禁兜底：① 四种构图不同的骨架，**相邻场景不得同款**；② **每支片 ≥3 种视觉介质**、每个讲解场景至少一个会随旁白变状态的组件；③ 每章至少 3 次运镜（全片按片长配额），景别真的会变；④ 门禁 P0 不为 0 就**拒绝渲染**。

- **Q：怎么保证文字不会互相压、不会被盖住？**\
  A：渲染期有 `OverlapGate`（每 15 帧抽样，检测文字两两重叠与绘制顺序遮挡，用 `Range` 量真实字形矩形）与 `SlotGuard`（槽内内容超出可用宽）——它们会指出"哪一帧、哪两处、压了多少 px"。**有意的重叠**（镜头交接、标题滑变、数值替换）必须显式标 `data-gate-allow`，不允许用白名单掩盖两个不同信息互相压字。

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

本项目采用 [MIT 许可证](LICENSE) 开源。
