# v4.4 演示片 · 「一行缓存，五倍速度」（60 秒，8 镜，4 章）

这一版要证明的是「不像 PPT」：引擎虚拟镜头（缺省缓推、`cinema.focus` 讲到哪推到哪、S5 从缓存站横摇到数据库站、
镜间甩镜 / 章节首镜推穿、背景视差）、内容大（代码 36px、补丁 28px、关键数字 170–380px）、相邻 8 镜 8 种布局、
关键数字动态排版（`KineticNumber`）、字幕每行 ≤ 16 字、v4.4 重做的 pop / chart 音效。

无旁白（静音占位 narration.mp3），字幕时间由 `caption-cues.json` 直接给出（每字 170 ms）；音效全部由引擎按分镜表语义自动排。

复现（Windows 用 `scripts\notebook-video.cmd`，命令相同）：

1. `node scripts/notebook-video.mjs new-project nv-demo5 --style=flat`（或 `--style=cel`）
2. 本目录 `scenes.tsx` → `src/`；`shots.json`、`caption-cues.json` → `manifests/`（cues 也拷到 `src/`）；
   `protected-caption-phrases.txt` → `manifests/`；`narration.txt` → 根目录；`narration.mp3.json` → `audio/`
3. `src/index.tsx` 的 COPY：`chapterTitles:['慢在哪里','改一行代码','结构怎么变','结果']`、`chromeKicker:'NOTEBOOK-VIDEO 4.4'`、
   `header:'一行缓存 / CACHE'`、`headerSub:'CINEMA DEMO · 60s'`；`CHAPTER_SHOTS=['S1','S3','S5','S7']`
4. 60 秒静音：`ffmpeg -f lavfi -i anullsrc=r=48000:cl=mono -t 60 audio/narration.mp3`，然后 `node scripts/notebook-video.mjs sync nv-demo5`
5. `python scripts/resolve-shots.py nv-demo5`，然后
   `npx remotion render src/index.tsx NotebookVideoFilm out.mp4 --scale=0.75 --crf=20`（1920×1080）
