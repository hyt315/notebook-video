# 手作路线的黄金样例 = 模板自带的示例片

`examples/` 里另外四个 `*.story.json` 是**组件路线**的草稿样例（auto 引擎排版）。手作路线（`journal` / `papercut` / `archive`）没有单独的 story.json——它的黄金样例就是模板工程本身：

```bash
node scripts/notebook-video.mjs new-project ./my-video --style=journal
```

新建出来的工程里，这三份文件就是「导演层怎么填」的范例：

| 文件 | 看什么 |
|---|---|
| `manifests/treatment.json` | 隐喻怎么落到一个具体动作（`native_move`）、三个候选结构怎么写 `family`、`facts` 怎么给出处（url + 逐字引文）、`sound` 段每个字段的含义 |
| `manifests/shots.json` | 每镜的 `framing` / `move` 要和 `cameraIntent` 对得上；招牌镜头的 `camera.to` 要比 `from` 大 12% 以上 |
| `src/scenes.tsx` | 只用帧号驱动的写法；手作组件（`InkPath` / `WashBlob` / `HandLettering` / `Seal` / `ArchivePhoto` …）怎么组合 |

示例片讲的是「GitHub 新手三部曲」，主题可以整个换掉，但**结构别动**：换掉 `topic` / `metaphor` / `facts` / 分镜台词，保留 `$components` 的用法和每镜的运镜意图，再 `make-video --stills` 看静帧。

## 为什么示例片要自带出处

手作皮肤的 `validate-treatment.py` 把「导演层」当硬门禁：没有 `facts` 出处、没搜过 Commons、招牌镜头没真推 12%，都会以 P0 拦住渲染。这不是为难人——手作片的说服力来自「真材料 + 真出处」，模板先按这个标准写一遍，用户照着改就不会漏。

详细方法见 `references/director-method.md`。
