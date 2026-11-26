# 检查：交付清单、美学纪律、构图与呈现门禁

本篇说明门禁分级、客观硬门禁阈值与验收排雷。跨语言数值常量以 `assets/lecture-template/src/contract.json` 为准。

## 门禁分级原则

- **P0（硬门禁，拦片）**：只管客观可证明的技术错（出界、字号越底限、对比度不足、字幕超宽/超速、音画不同步、枚举非法、主题物缺席、许可违规、开场第 0 帧空白）；当前路线不拦项记 P1。
- **P1（软提示，不拦）**：审美与结构建议（相邻同骨架/同版式、运镜意图与配额、缺 `$asks`、次要事实缺标注、手作未独立评审、叠层超 5%）。
- 全部结果统一写入 `renders/gates.json`（含 `gate`/`id`/`level`/`blocking`/`file`/`message`/`fix`）。同个 `✗` 连修两轮不通过时，停下把原文发给用户。

<a id="quality-checklist"></a>
## 1. 交付验收清单

1. **讲稿与评审卡**：`renders/report.md` 首屏显示评审状态（未评审标「未评审」）与成片摘要（镜数、运镜意图数、转场、分辨率与 P0/P1）；手作路线建议独立评审，组件路线按 [rubric.md](rubric.md) 可选执行。
2. **事实核对**：运行 `validate-facts <工程> --review` 逐条审读含数字/年份的未标注文本；主要事实缺出处停下问用户，次要事实缺出处记 P1。
3. **构建期全绿**：`renders/gates.json` 中 P0 归零，无 `did NOT run`。
4. **成片复核**：整片渲染前征得用户同意；成片自动通过 `validate-video`、`validate-motion-gaps.py`、`validate-silence.py` 与 `validate-opening.py --video`，附带 `renders/captions.srt` 与 `renders/poster.jpg`。
5. **开场与抽看**：0–1.5s 见主体与强证据、6s 内立出诚实核心问题并在 80% 前破案、结尾回扣闭合；渲染后人工抽看 0.5 / 2 / 4 / 8 / 10 秒及镜头边界/最长字幕/结尾帧（>60s 片联系表 ≥24 帧）。

**默认交付物**：讲稿与时间码分镜表（含骨架、介质、组件、运镜、anchor、beats）、`manifests/visual-assets.json`、词级时间戳中文旁白、`manifests/caption-cues.json` 与保护短语清单、默认 `--scale=1`（`2560×1440`；可选 `--scale=0.75` 输出 `1920×1080`）H.264/AAC MP4、联系表与可编辑源码工程。

<a id="official-aesthetic-system"></a>
## 2. 美学与视觉纪律

- 遵循 [draftpaper.md](draftpaper.md) 的「讲到哪、长到哪」草稿纸原则与动效契约。
- 亮底深墨：正文对比度 ≥ `4.5:1`（WCAG 2.2 SC 1.4.3），大字 ≥ `3.0:1`，仅用所选皮肤锁定色板（[themes/system.md](themes/system.md)）。
- 留 2–3 个锤子帧（`StampBanner` / `HandLettering` / `Seal`），全片直书页 ≤ 40%。

<a id="composition-gate"></a>
## 3. 构图与运镜门禁

| 脚本 | 检查内容 | 关键阈值（代码真源） | 等级 |
|---|---|---|---|
| `validate-shot-motion.py` | 镜头 anchor 出界、缩放预算、安全区占幅 | 含字 ≤ `TEXT_ZOOM_MAX`（1.35）、纯图形 ≤ `GRAPHIC_ZOOM_MAX`（1.6）、`ORBIT_ROT` 6°、`CAM_DUR` 30–45 帧；目标占幅 60–80%（`<45%` P0，纯文字降 P1） | 出界/超限/极空 P0；配额/留白 P1 |
| `validate-composition.py` | 活性组件、闭集枚举、import 完整性、beats 下标与多样性 | 无活性组件 / 非法入场转场介质 / 断导 / beats 越界均 P0（`auto` 路线跳过 `<Shot reveal>` 独占检查）；相邻同骨架等美学项 P1 | 客观 P0 / 审美 P1 |
| `validate-fusion.py` | `mode` 合法性、主题物出现、三层配比 | 非法 `mode` / 主题物全片缺席 P0；配比失衡 P1 | 合法性/主题物 P0；配比 P1 |
| `validate-opening.py` | 开场第 0 帧空白与前 3 秒节奏 | 成片第 0 帧空白 `O6` 为 P0；其余写法与像素变化（`O1–O5`/`O7`）为 P1 | `O6` P0 / 其余 P1 |
| `validate-treatment.py` | 导演层字段与招牌镜实动作（≥12% 推近或 ≥120px 位移） | 缺文件/`<<…>>` 占位/自相矛盾/招牌镜无动作（手作）P0；其余字段缺失 P1 | 按项分级 |

- **P1 多样性基准**：全片骨架 ≥3 种且相邻不同；非静止运镜意图 ≥3 种，每 12 秒（章节 ≥20s 时 ≥3 次）至少 1 次运镜；介质 ≥3 种、转场 ≥2 种、入场 ≥3 种；单镜 ≤10–12 秒，同指纹不隔镜重复。

<a id="render-gates"></a>
### 3.1 渲染期门禁（浏览器实时测量）

| 门禁 | 量什么 | 处理 |
|---|---|---|
| `CardFitGate` | 卡片内文字溢出 padding 盒 > 2px | 拦（`cancelRender`） |
| `OverlapGate` | 文字碰撞或被不透明元素遮挡（边界/节拍/关键帧强制抽样） | 拦 |
| `ClippingGate` | 图形越出裁切容器 | 拦 |
| `CaptionFitGate` | 字幕真字体宽度溢出安全区 | 拦 |
| `CanvasBoundsGate` | 文字墨迹越出画布 ≥ 6px | 成片报警 / 目录接触表拦 |
| `FillGate` | 信息元素下 1/4 填满度与横向空洞 | 报警 |
| `SlotGuard` | `StageFrame` 主槽占幅（目标 ≥60%，<35% 提示） | 报警 |
| `AssetGate` | 字体与媒体就绪前阻塞并报错定位 | 拦 |

- **有意覆盖与缩放框**：跨镜交接 `handoff` / `swap` / `value-swap` / `morph` / `glossary` / `sketch` 才可加 `data-gate-allow`；会放大溢出的取景容器须标 `data-fit-skip`。严禁调松阈值、改小 `anchor` 或滥用白名单掩盖碰撞。
- **被判「空」怎么修**：在空洞处补本镜主体信息层（标尺/刻度/引线批注/局部放大），`anchor` 如实框住；不放大卡片凑面积，不把后续元素预铺到开镜。

<a id="presentation-gate"></a>
## 4. 呈现效果与成片门禁

| 门禁项 | 精确阈值 | 级别 | 说明 |
|---|---|---|---|
| 字幕读速上限 | ≤ `CPS_MAX`（9.0）加权字/秒 | P0 | 无配音排时长基准另见 `READ_CPS`（4.5） |
| 字幕行宽 | ≤ `CAPTION_MAX_CHARS`（16）字（去句末标点逐字，ASCII 计 1） | P0 | `validate-caption-sync.py` 与 `CaptionFitGate` 同口径 |
| 节拍同步容差 | 不早于所属 cue `BEAT_SPOILER_FRAMES`（12）帧；不晚于句末 `BEAT_LATE_FRAMES`（8）帧 | P0 | 距上界 ≤4 帧（`BEAT_TIGHT_FRAMES`）报 P1 |
| 字号与对比度 | 源码绝对地板 `MIN_LABEL_FONT`（13px，标注 `FONT_LABEL_MIN` 16px）；auto 正文 `MIN_FONT` 32px；核心句 `CORE_FONT_FLOOR` 64px；墨色对比度 ≥ `4.5:1`；CJK 字体栈 | P0 / P1 | `validate-presentation.py` + `validate-glyphs.py` |
| 画面静止上限 | 普通镜 ≤ `DEFAULT_MAX_STATIC`（2.5s）；锤子镜 ≤ `HAMMER_MAX_STATIC`（3.0s） | P0 | `validate-motion-gaps.py` |
| 音效与静音 | 音效峰值 ≥ `-12 dBFS` 且 `sha256` 一致；无 BGM 时句间真静音 | P0 | `validate-audio-levels.py` / `validate-silence.py` |
| 屏幕叠层面积 | 字幕 + 角标常驻面积 ≤ 5%（超 5% 记 P1，超 30% 判 P0） | P1 / P0 | `check_overlay_budget` 核算 |

- **成片文件规格**（`notebook-video validate-video`）：默认 2560×1440（`--scale=1`；或 `--scale=0.75` 为 1920×1080）、30fps CFR 无卡顿；H.264 + AAC 48kHz 立体声、`av_offset ≤ 0.034s`；色彩 `tv / bt709 / bt709 / bt709`；响度约 `-16 LUFS`、真峰 ≤ `-1.5 dBTP`；帧级亮度 `YAVG ≥ 35` 无死黑/死白；旁白后至少留 `0.7s`（`END_TAIL_F` 42 帧）。
- **字幕整洁**：五套主题统一为底部单行居中 64 设计像素纯文字配纸色柔光晕（无实心框/侧标）；保护短语不跨行拆分；保留句中标点，去句末标点；音画同步 ≤ 80ms。

## 5. 包装验收与低质画面排雷

- **封面（`renders/poster.jpg`）**：明亮清晰、主体完整且与主题一致，杜绝大字报或模糊截帧。
- **低质红线（必避）**：1）PPT 纯静态卡堆砌、无生长推演；2）无意图频繁运镜、掉帧或超长静止；3）镜尾/片尾无呼吸戛然而止；4）系列选题高度同质化（套死同一骨架/布局/节奏）；5）单图配大段字幕与模板式轮播；6）机械生硬朗读加无消化搬运；7）音画脱节（画面未回答当镜 `$asks`）。

<a id="locked-surface"></a>
## 6. 锁定项与可改范围

- **锁定不改**：`C` 色板、`TYPE` 阶梯、`AESTHETIC`、纸影 `paperShadow`、`LineIcon`/`CheckBadge`、`Grade` 调色、运镜外层 Chrome 徽标及底部字幕几何。
- **单片可改**：`COPY`、`narration.txt`、保护短语、镜头表、`visual-assets.json`、`public/illustrations/` 与 `src/custom/` 专属件。不用 emoji 替代线条图标；不用全幅半透明蒙版洗背景；位图不烤字或图表；非活跃镜头须卸载（只挂载当前镜或交接双镜）；动画纯 `transform`/`opacity`/`clipPath` 驱动，不逐帧改布局几何。
