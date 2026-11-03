# 模板示例片：导演层怎么填

`examples/` 里的 `*.story.json` 是 **auto 路线**的样例（`recipes/` 下 4 个是配方样例）。手写场景路线没有 story.json，它的参照是模板工程自带的示例片：

```bash
node scripts/notebook-video.mjs new-project ./my-video --style=journal
```

这支示例片讲「GitHub 新手三部曲」，镜头内容是一支**组件片**（`ConsoleWindow` / `StampBanner` / `Callout` / `StatRow` / `DiffView` …），没有用到手作原语（`InkPath` / `WashBlob` / `HandLettering` 等的写法见 `references/craft-kit.md`）。它示范的是三件事：

| 文件 | 看什么 |
|---|---|
| `manifests/treatment.json` | 隐喻怎么落到一个具体动作（`native_move`）、三个候选结构怎么写 `family`、`facts` 怎么给出处（url + 逐字引文）、`sound` 段每个字段的含义 |
| `manifests/shots.json` | 每镜的 `framing` / `move` 要和 `cameraIntent` 对得上；招牌镜头的 `camera.to` 要比 `from` 大 12% 以上 |
| `src/scenes.tsx` | 只用帧号驱动；每个元素用 `enterAt(f, at(n))` 绑到讲到它的那一句，按出现规则长出来（见 `references/reveal-rules.md`） |

换主题时：换掉 `topic` / `metaphor` / `facts` / 分镜台词，保留每镜的运镜意图和「元素绑到句子」的写法，再 `make-video --stills` 看静帧。

## 为什么示例片要自带出处

手作皮肤的 `validate-treatment.py` 把「导演层」当硬门禁：没有 `facts` 出处、没搜过 Commons、招牌镜头没真推 12%，都会以 P0 拦住渲染。这不是为难人——手作片的说服力来自「真材料 + 真出处」，模板先按这个标准写一遍，用户照着改就不会漏。

详细方法见 `references/director-method.md`。

手作皮肤 + 手账页的完整参考片是 [examples/cell-notebook](cell-notebook/README.md)（auto 路线，看它的 storyboard.md 学「讲到哪长到哪」）。
