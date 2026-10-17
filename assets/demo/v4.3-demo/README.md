# v4.3 组件演示片 · 「一行缓存，五倍速度」（60 秒，7 镜，4 章）

无旁白（静音占位 narration.mp3），中文字幕由 `caption-cues.json` 直接给出时间；音效全部由引擎按分镜表语义自动排（预制音效库）。
展示：Shiki 代码高亮（S3）、jsdiff 补丁 + ZoomStage（S4）、visx 柱/面积图 + StatRow + MetricGrid（S2/S7）、
lucide + simple-icons 图标墙（S1）、flubber 形状变形 + d3-hierarchy 结构树（S5）、Corridor + SplitStage（S6）、
章节背景（每章首镜自动 chapter 变体）。

复现：

1. `node scripts/notebook-video.mjs new-project nv-demo --style=flat`（或 `--style=cel`）
2. 把本目录的 `scenes.tsx` → `src/`，`shots.json`、`caption-cues.json` → `manifests/`（cues 也拷到 `src/`），`narration.txt` → 根目录
3. `src/index.tsx` 的 COPY：`chapterTitles:['慢在哪里','改一行代码','结构怎么变','结果']`、`chromeKicker:'NOTEBOOK-VIDEO 4.3'`、
   `header:'一行缓存 / CACHE'`、`headerSub:'COMPONENT DEMO · 60s'`；`CHAPTER_SHOTS=['S1','S3','S5','S7']`
4. 60 秒静音：`ffmpeg -f lavfi -i anullsrc=r=48000:cl=mono -t 60 audio/narration.mp3`；`audio/narration.mp3.json` = 所有 cue 的 words 拼接
5. `python scripts/resolve-shots.py nv-demo`，然后
   `remotion render src/index.tsx NotebookVideoFilm out.mp4 --scale=0.75 --crf=22`（1920×1080）
