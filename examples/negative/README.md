# 负例（故意过不了门禁）

这个目录里的 story **故意**违反某道硬门禁，用来证明门禁真的会拦。**不要照着它们做片，也不要"修好"它们**——修好了，对应门禁就失去了实证。

`scripts/dev/check-examples.py`（CI「Every positive example passes the gates」一步）对这里的每个文件反向检查：`make-video` 必须 rc≠0，且输出里必须出现下表登记的判据关键字。新增负例时在表里加一行；关键字取该门禁 P0 文案里稳定的一段。

| 文件 | 预期拦下的判据关键字 | 说明 |
|---|---|---|
| `rocket-components-only.story.json` | `全片没被点名` | 全组件片，主题物「火箭」在任何镜头的 `see` / `title` 里都没被点名 → `validate-fusion` P0。正例对照：`examples/recipes/rocket-fusion.story.json`。也被 `tests/test_fusion_gate.py` 与 `scripts/negative-gate-check.py` 当夹具使用。 |

`examples/` 下其余所有 `*.story.json` 都是正例，CI 要求它们全部过完整构建期硬门禁（新建工程 → compose → 门禁 → tsc）。
