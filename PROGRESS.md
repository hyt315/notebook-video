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
