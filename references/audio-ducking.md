# 音效与旁白的相对电平（P2-20 的剩余部分）

## 为什么这一条还没"做完"

清单里 P2-20 分两半：可机器保证的（变体轮换、同步门禁、盲听协议）已经做完；
剩下的是**随旁白的包络 ducking**，而它被刻意排在盲听之后——先听 seg1，确认"音效真的在掩字"，
再决定是压 ducking 还是调 gain 阶梯。没听就上 ducking，很可能压掉的是本来该有的强调音。

本文把「听完之后怎么执行」写死，避免下次又从头讨论参数。

## 判定：先量，再听

```bash
# 1) 音效命中点与旁白区间是否真的重叠（机器可判，不需要耳朵）
python scripts/validate-audio-levels.py assets/lecture-template
python scripts/validate-audio-levels.py PROJECT --explain   # 每条事件的 offsetMs 与所在旁白句

# 2) 重叠段的相对电平（旁白 RMS vs 音效 RMS，同一 200 ms 窗口）
ffmpeg -ss <t> -t 0.2 -i audio/narration.mp3 -af "astats=metadata=1:reset=1" -f null - 2>&1 | grep "RMS level"
ffmpeg -ss <t> -t 0.2 -i renders/film.mp4 -af "astats=metadata=1:reset=1" -f null - 2>&1 | grep "RMS level"
```

判据（来自 `references/sfx-library.md` 的既有口径）：

| 情况 | 处置 |
|---|---|
| 音效峰值 ≤ 旁白 RMS −12 dB | 不用 ducking，现状即可 |
| 落在 −12…−6 dB 之间，且音效 < 300 ms | 先调该事件的 gain（在 `sfx-manifest.json` 里降 3 dB），不要全局 duck |
| > −6 dB，或音效 > 300 ms 且压住整句 | 上 ducking（下面的命令） |

## ducking 参数（听完再改，别凭感觉调）

- 深度 **−6 dB**（0.5 线性）。再深会让音效"消失"，观众以为漏了一声。
- 淡入/淡出 **各 120 ms**，余弦。硬切在纸片音上会有可闻的咔哒。
- 只在**旁白句内**压；句间空隙恢复原电平（空隙本来就是音效的位置）。
- 不压 `narration` 自身，只压 sfx 总线。

## 现成命令（把 CUE_JSON 换成工程的 caption-cues.json）

```bash
# 1) 从 cues 生成「旁白区间」的 ffmpeg 表达式（半开区间，含 120 ms 斜坡）
python - <<'PY' > /tmp/duck-expr.txt
import json, sys
cues = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "manifests/caption-cues.json", encoding="utf-8"))["cues"]
f = 0.12
terms = []
for c in cues:
    a, b = c["start_ms"] / 1000, c["speech_end_ms"] / 1000
    terms.append(f"if(between(t,{a:.3f},{a + f:.3f}),1-0.5*(t-{a:.3f})/{f},"
                 f"if(between(t,{b - f:.3f},{b:.3f}),1-0.5*({b:.3f}-t)/{f},"
                 f"if(between(t,{a:.3f},{b:.3f}),0.5,1)))")
print(terms[0] if terms else "1")
PY

# 2) 把表达式套到音效总线上（音效单独一轨时才成立；混在成片里就只能整轨压，会连旁白一起压）
ffmpeg -i sfx.wav -af "volume='$(cat /tmp/duck-expr.txt)':eval=frame" sfx-ducked.wav
```

**注意**：当前流水线的音效由 Remotion 在渲染时与旁白一起混，**没有独立的 sfx 轨**。
所以上面这段在现有产物上跑不了——要做 ducking，先得让渲染同时输出一条 sfx-only 音轨
（`<Audio>` 分组 → 单独 composition 或 `--separate-audio-to`），这是实现 ducking 的前置工作，
不是参数问题。这条写在这里，免得下次以为"改个参数就行"。

## 还差什么（诚实清单）

- [ ] 盲听 seg1，按上表落一个判定（需要人，约 15 分钟）
- [ ] 若判定要 ducking：先加 sfx-only 音轨输出，再套上面的表达式
- [ ] 静音占位 vs 真人声的动态差：现在两者用同一套电平门限，真人声的句间呼吸会被当成"静音"，
      需要按 `narration.meta.json` 是否来自 TTS 分流
- [ ] 泵感检测（duck 过度会让音效忽大忽小）：目前没有指标，只能听
