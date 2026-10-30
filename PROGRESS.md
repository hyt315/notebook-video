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

## P2 · 三层融合：线稿层 + 讲解层 + 配方（引擎完成，样张验收待跑）

### P2-1 线稿笔触在五个皮肤下都能用
- `theme/flat.tsx` / `theme/cel.tsx` 补 `craft` 声明（`inkLine` / `accent` / `handFamily` / `fibre: 0`）。
  以前只有手作皮肤声明 craft，`InkPath` / `HandNote` 在 flat 下读不到墨色。

### P2-2 `sketch` 数据结构与 7 个动词
- 新增 `src/linework/types.ts` + `sketch.tsx`：`lib:` / `shapes:` / `trace:`（trace 目前只给配方⑥做标注层）。
- 七个动词全部实现：`enter`（描出）/ `point`（点部位 + 外置手写标注）/ `drop`（脱离、旋转、落出）/
  `swap`（换态）/ `count`（复制 N 份）/ `mark`（勾叉圈）/ `exit`。
- `at` 支持本镜帧号、`@L1`（第 1 句开始）、`@L1.4`（第 1 句第 4 个字音），compose 换算成帧号。
- 有线稿的镜头**自动取消推近**（`cinema.path` 固定全景）：实测锤子帧的小火箭被 1.18× 推近顶出画框。

### P2-3 内置线稿库 30 个
- `src/linework/library.ts`：火箭 / 卫星 / 地球 / 灯泡 / 电池 / 手机 / 笔记本 / 服务器 / 芯片 / 云 /
  房子 / 汽车 / 钞票 / 硬币 / 购物车 / 钱包 / 人 / 人群 / 气泡 / 书 / 笔记 / 日历 / 钟表 / 放大镜 /
  锁 / 钥匙 / 文件 / 邮件 / 工厂 / 树。每个带 `fit` 包围盒、2–4 个部位。
- 按 a2e 的笔法重做：**三档线宽**（外壳 > 内部 > 细节，`detail: true` 走暖灰细线）、
  **连续剪影**（火箭/树/人都改成一条闭合 path，不再用 rect 叠积木）、
  **标注在线稿外侧**（细引线 + 起点圆点，≤6 字）、`wash` 降到 8%、主体填满方框。
- 样张实测（火箭 4 镜 + 手机/树/人 3 镜）逐帧看过：轮廓认得出、线不糊、标注不压物体。

### P2-4 八个融合配方
- `compose-story.py` 新增 `SKETCH_BOX` / `lay_recipe`：
  ① `sketch-readout` ② `component-annotated` ③ `scene-verdict` ④ `before-after`
  ⑤ `list-icons` ⑥ `photo-traced` ⑦ `data-with-object` ⑧ `hammer`。
- 前四个自带版面（不跑原版式，避免 `content.text` 必填项挡住弱模型）；后四个复用原版式 + 角落/右侧线稿。
- 讲解层 `annotate:[{target,kind,text}]`：圈注 / 下划线 / 箭头 / 手写小字，按元素矩形与句子帧号落位。

### P2-5 组件小改
- 组件级 `annotate` 通过镜头级叠加层实现（任意版式可用）；`unit_icon` / 每条一个图标仍是简版（配方⑤⑦当前给一块代表线稿）。

### 样例与门禁
- `examples/recipes/rocket-fusion.story.json`（①③④⑧ 四镜）、`annotated`（②）、`list-icons`（⑤）、
  `data-with-object`（⑦）；`examples/regress/rocket-components-only.story.json`（全组件，必须 P0）。
- 新增 `scripts/validate-fusion.py`：主题物从未出现 P0；纯组件 >30% / 含线稿 >60% 或 <30% /
  纯文字 >10% / 锤子帧 >3 / 自拼 >12 形 / `see` 写成文字，全部 P1 并给可复制修法。
- `tests/test_fusion_gate.py` 3 条；负向用例 `FUS1`。

### P2 未完成（下一轮）
- 30 线稿 × flat/journal 两张接触表 + 评审认出率 ≥27/30（要一次 30 帧渲染）。
- `photo-traced` 需要真实媒体样例；配方⑤⑦的「每条/每柱一个图标」仍是简版。
- 弱模型盲测（只给 SKILL + linework.md + recipes.md，写「什么是复利」3 镜）。

### 回归
```
pytest:        192 passed, 2 skipped, 5 subtests passed
selftest:      SELFTEST PASS (all 20 checks passed)
validate-skill: Skill-wide consistency validation passed
negative-gate: 合计：用例 109 · 断言 170 · 全部通过
```

## 3.6.0 · 方向修正：线稿降级，手账页上位

### 为什么改
P2 做完 30 个线稿 + 8 个配方后，与 cell 片（49 秒《细胞为什么叫细胞》）逐帧比对：
**线稿当解释图 = 剪贴画**，它能说明「这里有个火箭」，说不清「为什么这样」；
cell 的说服力来自「真图版 + 手写批注 + 印章 + 放大镜」——一个人在你面前研究给你看。
用户判断（两次确认）：讲解视频用手账页承载，线稿只适合 a2e 那种生词卡。

### 改了什么
1. **新增 `layout: "page"`（手账页版式）**，`content.page` = `plate` | `loupe`：
   - `plate`：装裱好的真图版（右，画宽 45%）+ 手写大字 + 朱红印章 + 手写说明，**整页不产生任何卡片框**；
   - `loupe`：同一张图版 + 放大镜，`look` 给镜心（0–1），`zoom` 默认 2.6（>3 糊，validate-media 拦）。
   - 渲染器 `auto.tsx` 新增 5 个元素类型：`archive` / `lettering` / `stamp` / `handnote` / `loupe`，
     全部复用 `src/craft/` 里既有道具（与 cell 工程逐字一致，无需另搬）。
2. **`validate-fusion.py` 换口径**（P0 一条 + P1 六条）：
   - P0 主题物从未出现（证据范围扩到：手账页图版说明 / 标本速写标签 / `see`）；
   - P1 手账页 <20%（没有承载）/ >75%（变图册）；组件 <25%（概念没讲）；
   - P1「文字 + 简笔线稿」>20% —— 这条直接编码了「乱加线稿更差」的实测结论。
3. **文档改主线**：`SKILL.md` 开篇改成「手账页承载 + 组件讲解」两栏表；
   新增 `references/journal-page.md`（六件要素、三种页型、配比、禁忌）；
   `references/recipes.md` 顶部加降级说明（八个线稿配方改为可选）。
4. **cell 归档为黄金样例**：`examples/cell-notebook/`（treatment + storyboard + narration + 复刻写法 + 它没做到的地方）。
5. **修素材表不同步**：`sync-render-inputs.cjs` 现在把 `manifests/media.json` 同步到 `src/media.json`。
   旧版没人同步，于是「素材明明加了，渲染报 id 不存在」——实测 3 条素材现在能正常读出。

### 实测样张（journal 皮肤 / 1440×810 出图）
- 三镜样例 `examples/recipes/cork-page.story.json`：plate → compare → loupe，18.5 秒，
  `validate-fusion` **P0=0 P1=0**（手账页 67% / 组件 33%）。
- 逐帧看过：图版页（1665 + 印章 + 「第十八篇 · 软木」）与放大镜页（镜内 3 倍格子）都成立，
  与 cell 原片的语法一致。

### 回归
```
pytest:        193 passed, 2 skipped, 5 subtests passed
selftest:      SELFTEST PASS (all 20 checks passed)
validate-skill: Skill-wide consistency validation passed
negative-gate: 合计：用例 109 · 断言 170 · 全部通过
```

### 未做（下一轮）
- `specimen` 页（标本速写 + Dimension 尺寸线）还没做成版式，目前要手写 `statement + sketch`。
- 组件的 journal 化：`compare` 在点阵纸上仍是「白卡片 + 圆角边框」，像贴上去的 PPT；
  需要给 panel / card 一套纸感变体（去边框、改纸条 / 墨框）。
- 素材获取链路（commons-search → media.json）还没在 journal 主线里跑通一遍完整样例。

## 3.6.1 · 线稿融入手账页（页内示意图）

用户澄清：不是二选一，而是**把 a2e 那套线稿技法融进手账页**——真手账里本来就会在文字旁边随手画个小图。

- 手账页新增可选字段 `content.figure`：`{"draw":"lib:book","label":"《显微图谱》","size":300}`。
  渲染器加 `case 'figure'` → 复用 `SketchLayer`（三档线宽 / 外置标注 / 包囲盒都沿用）。
- 尺寸硬压 360（画宽 ≤19%），固定在左下空白处：再大就退回「线稿当解释图」，那正是要避免的。
- 只当**速写**用：帮观众认出「说的是哪件东西」，不解释概念、不点名、不拆解。
- 样张实测（plate 页左下角一本简笔书）：不抢右侧真图版，像笔记里的随手插图。
- 文档：`references/journal-page.md` 新增「页内示意图」一节。

回归：pytest 193 passed / selftest 20 项 / validate-skill PASS / tsc 无错。
