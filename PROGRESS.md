# PROGRESS · notebook-video 3.5.0

> 按《notebook-video-改进方案.md》执行。每阶段一个提交：`3.5.0-Px: <一句话>`。
> 回归三件套：`pytest -q tests` / `python scripts/selftest.py` / `node scripts/notebook-video.mjs validate-skill`。

## P0 · 修掉已复现的缺陷 ✅

### P0-1 sweep 量不到
- 应用 `nbv-sweep-fix.patch`（两处：`renderStill` 改用 `render --frames=N-N --sequence --image-format=png`；
  FillGate 对推近镜头照量横向覆盖、只免「下 1/4」判据）。
- 新增 `tests/test_sweep_e2e.py`：复制模板 → 链依赖 → 补静音旁白 → `sweep --json`，断言
  `rows == shots`、`missing == []`、`failed == []`。没依赖时 skip 并写明原因。
- 实测（模板工程 8 镜，`sweep --json --scale=0.5`）：

```
{'picks': 8, 'skipped': 0, 'missing': 0, 'failed': 0, 'rows': 8, 'sheet': '...\\renders\\sweep-sheet.jpg'}
```

- `tests/test_sweep_e2e.py` 实跑：`1 passed in 72.19s`。

### P0-2 未注册定制组件必须拦
- `compose-story.py` 新增 `registered_customs()` / `check_customs()`：解析 `src/custom/index.ts`
  的 `CUSTOM = {…}` 花括号层，story 引用了未注册的组件名 → **P0 停止**，信息含组件名、镜号、
  注册文件路径、照抄哪个范例。
- `auto.tsx`：删掉红字顶替，换成 `MissingCustom`（`cancelRender`）——绕过构建直接渲染也不出片。
- `validate-visual-plan.py` 增加同一检查（手改 `src/story.ts` 的路径也拦）。
- 负向用例：`CW1` 拦、`CW2` 注册后放行。
- 用用户那部火箭片实测：`✗ S12: 定制组件 StageStack 未注册 …`（原片 74 秒处的红字就是这么来的）。

### P0-3 代码卡中文豆腐块
- 根因（不是"字体没加载"）：`CODE_FONT` 写成 `…,monospace,Kai`。CSS 里**泛型族之后的名字一律被忽略**，
  所以 Kai 从未参与回退；Linux 渲染机没有 Consolas/Menlo，`monospace` 落到无 CJK 字面的 DejaVu Sans Mono。
- 修法：`'JetBrains Mono','DejaVu Sans Mono',Consolas,Menlo,Kai,monospace`（Kai 在泛型族之前）。
- 新门禁 `scripts/validate-glyphs.py`：扫所有字面字体栈，(1) 必须有一个带 CJK 字面的族
  （Kai / NotoSerifSC / fonts.tsx 里 `cjkFallbackFaces` 补过 unicode-range 的族），(2) 泛型族必须最后。
  接入 `make-video`（硬门禁）、CLI `validate-glyphs`、selftest（正 + 负各一条）。
- 实测：模板 155 条字体栈 PASS；负向 GL0（只写 monospace）/ GL1（Kai 写在 monospace 之后）都被拦。
- 弱模型样例第 120 帧重渲：`# 输出：0.30000000000000004` / `# 输出：False` 均正常。

### P0-4 数字与柱标签
- `clean_unit()`：`unit` 只接受单位符号（`%` / `公斤` / `GB` / `万次` …）。`"占比 %"` → `"%"`；
  `"公斤燃料 / 公斤干重"` → `"公斤"`；`"吨级"` → `"吨"`。每次降级报 P1 并说明改法。
- 柱顶标签 >8 汉字 → P1；标签 `white-space: nowrap`，不再折行压到柱子上。
- 火箭样例实测三条 P1：
  `unit='公斤燃料 / 公斤干重' … 收敛为 '公斤'`、`unit='吨级' … '吨'`、`unit='占比 %' … '%'`。

### P0-5 字幕
- `captions.mode`：`line`（默认）/ `typewriter`；compose 写进 `film.ts` 的 `CAPTION_REVEAL`。
- 空胶囊：`Subtitle` 在 `cue/targetChars/words` 任一为空时直接不画（3.3.0 已有，本轮保持并复验）。
- 弱模型样例第 120 帧：字幕从「但 0.1 +」变成整行「但 0.1 + 0.2 = = 0.3 会」。

### P0-6 手作样例 treatment 矛盾
- `new-project` 换皮肤时同时换 `medium.why`（五段，各自为 flat / cel / journal / papercut / archive 辩护）。
- `validate-treatment.py` 新增 P1：`why` 里出现别的皮肤名且同句是推荐语气（更/不如/适合/优于/胜过/比）。
- 实测：`new-project --style=journal` 后 `medium.why` 是手账辩护段。

### P0-7 小项
- `validate-composition` 变异系数：比较与显示都取两位小数，不再出现「0.35 < 0.35」。
- 模板结尾「主页搜 hyt315」→「主页搜【你的账号】」；cues / 词级时间 / 保护短语 / storyboard 同步；
  compose 对「主页搜」+未加括号的账号报 P1。

### P0 回归
```
pytest:        182 passed, 2 skipped, 5 subtests passed in 22.24s
selftest:      SELFTEST PASS (all 20 checks passed)   # 18 → 20
validate-skill: Skill-wide consistency validation passed
negative-gate: 合计：用例 107 · 断言 166 · 全部通过
```

## P1 · 声音：TTS 为主线，少量音效，默认无 BGM ✅（成片实测并入 P4）

### P1-1 关掉音乐床
- `sync-render-inputs.cjs` 从 `manifests/treatment.json` 生成 `src/audio-config.ts`（`MUSIC_ON`）；
  `index.tsx` 只在 `MUSIC_ON` 为真时加载 `bed.ogg`。没有 treatment / `use=false` → 不加载（默认）。
- 文档：`SKILL.md`、`references/director-method.md` 改成「默认无 BGM」口径。
- 新门禁 `scripts/validate-silence.py`：music 关闭时，按字幕句间空隙（≥0.4 s）跑
  `silencedetect=n=-45dB:d=0.4`，要求检测到的静音段 ≥ 空隙数 − 1；接进 make-video 成片门禁（硬拦）。
- `tests/test_silence.py`：静音轨通过 / 持续正弦音（模拟配乐）P0 / `music.use=true` 跳过。

### P1-2 TTS 成为正式步骤
- 新命令 `notebook-video tts <工程> [--engine=edge|file] [--voice=…] [--rate=…]`（`scripts/tts.py`）：
  - `edge`：edge-tts，`boundary="WordBoundary"` 取词级时间；标点按源文本补回（否则每条 cue 都少句号）；
  - `file`：用户自备录音，按字数均分时间并标 `estimated=true`；
  - 失败 rc=3，信息含两条路（装 edge-tts / 换 `--engine=file`），不会悄悄退回静音。
- `compose-story.py`：检测 `audio/narration.meta.json` 后按词级时间**重排 cues 与镜头起点**；
  对不上就整体放弃并报 P1（不半套对齐）。实测弱模型样例：15 句 / 171 字音，`validate-caption-sync` PASS。
- `make-video`：旁白已存在就绝不覆盖；没有旁白才生成静音占位并写 `.silent-placeholder`；
  `--render` 时若仍是占位 → rc=3 停在渲染前（负向用例 TTS1）。
- 实测 edge 合成：`tts：15 句 / 171 个字音 · 引擎 edge`（之前 0 字音是因为 edge-tts 7.x 默认
  `SentenceBoundary`，已显式改 `WordBoundary`）。断网 / 未装模块两条路径都实测报两条替代路径。

### P1-3 音效：少而准
- `sfxDensity` 缺省已是 `sparse`；`validate-audio-levels` 新增一行统计：
  `音效 N 个 / 每 10 秒最多 M 个 / 最近人声 X ms / 混音余量 Y dB`，`M>4` 或 `Y<6` 报 P1。
- 最响的一记（chapter 0.522 → 0.49）落到人声下方 6.2 dB；manifest 与 `SFX_GAIN` 同步。

### P1 回归
```
pytest:        189 passed, 2 skipped, 5 subtests passed in 22.99s
selftest:      SELFTEST PASS (all 20 checks passed)
validate-skill: Skill-wide consistency validation passed
negative-gate: 合计：用例 108 · 断言 168 · 全部通过
```
