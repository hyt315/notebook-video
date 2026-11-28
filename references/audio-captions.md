# 旁白、字幕与音效

本篇规范旁白 TTS、字幕断句与时间同步、音效库及响度相对电平。读速与行宽常量统一以 `assets/lecture-template/src/contract.json` 为准。

<a id="tts-audio"></a>
## 1. 旁白 TTS 与声明式音频

- **成片硬要求**：交付整片（`--render`）必须有真实旁白 `audio/narration.mp3`。静音占位（`audio/.silent-placeholder`）仅供 `--stills` 与 `preview` 看画面；缺失真实旁白时 `make-video --render` 会在渲染前停止。
- **默认不加 BGM**：产品决策固定默认 `music.use: false`，依靠旁白节奏与稀疏语义音效推进，不铺旋律背景床。
- **生成命令**：
  - 默认 `edge-tts`：`node scripts/notebook-video.mjs tts <工程> --voice=zh-CN-YunxiNeural`
  - 自备录音：`audio/narration.mp3` 放好后跑 `node scripts/notebook-video.mjs tts <工程> --engine=file`（装有 `faster-whisper` 时按词级对齐，未装按字数均分）。
  - 商用 API（可选）：通过环境变量 `TTS_API_BASE`、`TTS_API_KEY`、`TTS_MODEL`、`TTS_VOICE` 传入，禁止把密钥写入工程文件。
- **多音字与换配音**：配音前跑 `python scripts/audition.py` 扫多音字，易错词一律在 `narration.txt`（每语义句一行）源头改写并同步画面文字，不事后打音频补丁；锁台词换音色用 `match-timing --lock` 或 `speed-post.py`。
- **重跑纪律**：改过 `story.json` 台词后，必须先重跑 `compose-story.py` 再跑 `tts`，否则音画错位；手写 `narration.txt` 需加 `--allow-stale`。
- **响度规范**：渲染输出统一规范到 `-16 LUFS`（母带真峰 `-2.6 dBTP`，门禁上限 `-1.8 dBTP`），可用 `NOTEBOOK_VIDEO_LUFS=-24` 回退旧电平。

<a id="subtitle-timing"></a>
## 2. 字幕断句与绝对帧契约

- **唯一真源**：`manifests/caption-cues.json` 与 `audio/narration.mp3.json` 必须一一对应，由 `scripts/validate-caption-sync.py` 硬校验。
- **行宽上限**：字幕只有一行，不超过 `CAPTION_MAX_CHARS`（16）字，去掉句末标点后**逐字符计**（ASCII 计 1，GitHub 占 6 格），`validate-caption-sync.py` 与 `CaptionFitGate` 同一口径；读速按**加权字计**（ASCII 计 0.5）。超长行由 `scripts/build-semantic-captions.py` 或 `compose-story.py` 在合法语义断点自动劈开。
- **读速双口径（勿混用）**：
  - **排时长基准读速**：`READ_CPS`（4.5）加权字/秒（无 TTS 时估算镜头时长；手作估算可用 `--cps=6.5`）。
  - **字幕读速硬门禁上限**：`CPS_MAX`（9.0）加权字/秒，由 `validate-presentation.py` 判 P0。
- **保护短语与语义断句**：
  - 专业术语、英文词、数字与 `protect` 列表里的词禁止跨 cue 切断。
  - `scripts/validate-semantic-breaks.py` 在交付路径强制携带 `--require-budoux`，使用随包 `assets/vendor/budoux/` 中文分词模型（工程有 `node_modules/budoux` 时优先用工程版本）。结论行若出现 `did NOT run` 视为门禁故障。
- **绝对帧同步**：所有画面节拍（`beats`）由 `resolve-shots.py` 绑定到字幕 cue 起止时间，再按 `FPS`（30）换算成绝对帧，禁止手算硬编码帧号。
- **交付字幕文件**：渲染后自动导出 `renders/captions.srt`（由 `scripts/export-srt.py` 生成）。

<a id="sfx-library"></a>
## 3. 语义音效库

- 音效只在**真实画面事件**触发（元素出现、数字落定、图表生长、关键词首次高亮、翻页转场），默认密度 `sfxDensity: "sparse"`，禁止为装饰乱加音效。
- 9 个合法事件名：`pop`/`chart`/`highlight`/`success`/`error`/`chapter`/`page`/`place`/`stamp`；单镜关闭写 `"sfx": "none"` 或 `"sfxAuto": false`。
- 随包音效位于模板 `public/sfx/lib/`，元数据与 `sha256`、`gain` 登记在 `public/sfx/sfx-manifest.json`。
- `scripts/validate-audio-levels.py` 强制检查：
  - 每个音效文件峰值不低于 `-12 dBFS`（过轻或损坏文件无法测量直接判错）；
  - 代码里的 `SFX_GAIN` 与 manifest 增益/提前量一致，文件 `sha256` 未被篡改。
- `scripts/validate-silence.py` 检查成片在 `music.use=false` 时，句间必须有真实安静区间，不允许残留持续底噪。

<a id="audio-ducking"></a>
## 4. 音效与旁白相对电平

- 音效与旁白在时间轴重叠时，旁白必须明显压过音效，避免听不清人声。
- 建议：语义点缀音效尽量落在句首或句间停顿；与人声重叠的翻页/落笔音效通过 manifest `gain` 压低至不影响人声清晰度的范围，成片统一经响度归一化输出。

### 4.1 音色轮换与命中点

- **音色轮换**：连续翻页同一纸声 3 次就机械。`page` 有三个同源微变体（`page.ogg` / `page-b.ogg` / `page-c.ogg`），`planSfx` 按出现次序轮换；变体登记在 `sfx-manifest.json` 的 `variants[]`，与主文件同一套质量口径。
- **命中点**：`offsetMs` = 文件开头到听感命中点的距离，量法是 **5 ms RMS 最大值**（不能用最大绝对值采样，chart / chapter 峰值在尾巴上会误报）。`validate-audio-levels.py` 逐文件对账，差 > 2 帧即报。
