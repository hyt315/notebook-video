# assets/vendor —— 随技能一起分发的第三方代码

这里放的东西有一个共同点：**技能自己要用，但不能靠 `npm install` 拿到**。
（其余第三方库都由 `assets/lecture-template/package.json` 声明、装进工程的 `node_modules`，
本仓库不分发，见 `NOTICE` 与 `references/dependency-policy.md`。）

---

## budoux/ —— 字幕断句的分词模型

**为什么在这里。** `validate-semantic-breaks.py` 有一条短语规则：字幕的断行必须落在分词边界上，
否则会出现「程 / 序员」这种把人名或专有名词劈开的断法，而这类错误人工列清单列不全。
它需要 BudouX 的模型。技能不发行 `node_modules`，所以在 3.9.0 之前，新克隆的仓库里这条规则
**永远报 `SKIPPED`** —— 而 `SKIPPED` 和 `passed` 在报告里长得几乎一样，等于没验。

**里面有什么。** 只有简体中文这一条路径，约 80 KB：

| 文件 | 来源 | 是否改动 |
|---|---|---|
| `budoux/LICENSE` | Apache-2.0 全文，版权行填 Google LLC | 换掉原文末尾那段示例版权行 |
| `budoux/module/parser.js` | `budoux@0.9.2` 的 `module/parser.js` | **原样复制** |
| `budoux/module/data/models/zh-hans.js` | 同上，`module/data/models/zh-hans.js` | **原样复制** |
| `budoux/module/package.json` | 同上，内容就是 `{"type":"module"}` | 原样复制 |
| `budoux/module/index.js` | **本项目自己写的入口**（5 行有效代码） | 不是上游的 index.js |

**为什么入口要自己写。** 上游 `loadDefaultSimplifiedChineseParser()` 返回 `HTMLProcessingParser`，
它经 `html_processor.js` → `dom.js` → `linkedom` 才能加载。我们只给**纯文本**分词，走不到 DOM，
却要为此多 vendor 几 MB。新入口直接组装上游的 `Parser` + 模型，行为等价性不是猜的：
对 5 条真实字幕，`new Parser(model).parse(t)` 与 `new HTMLProcessingParser(model).parse(t)`
输出逐字节相同（见 `tests/test_bundled_budoux.py`）。

**升级方式。** 换版本时只做三件事，别整个目录覆盖：

```bash
# 1. 从工程依赖里拷新版的原样文件（不要拷上游的 index.js）
cp <某工程>/node_modules/budoux/module/parser.js            assets/vendor/budoux/module/
cp <某工程>/node_modules/budoux/module/data/models/zh-hans.js assets/vendor/budoux/module/data/models/

# 2. 确认上游 Parser 的构造签名没变（新版若改成对象参数，自写入口要跟着改）
grep -n "constructor" <某工程>/node_modules/budoux/module/parser.js

# 3. 跑守护测试：分词必须无损、兜底必须命中
python -m unittest tests.test_bundled_budoux -v
```

版本号记在 `NOTICE` 第 11 条里，升级时一起改。

**它覆盖不到什么。** 需要处理带 HTML 标签的输入时（上游的 `HTMLProcessor`），这个切片不够用。
那种场景不在本技能的路径上；真需要就 `npm ci` 后传 `--budoux-dir <工程>/node_modules`，
显式指定的目录优先级高于这里。
