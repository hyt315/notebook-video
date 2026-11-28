# 皮肤系统（共享契约）

<a id="theme-system"></a>
## 1. 五套锁定皮肤

| 皮肤 | 路线 | 定位 | 详细契约 |
|---|---|---|---|
| `flat`（默认） | 组件 | 清爽现代科普插画，淡天空蓝/奶油底 + 纯白圆角卡片 | [flat.md](flat.md) |
| `cel` | 组件 | 明快漫画赛璐珞，粗描边 + 强对比强调块 | [cel.md](cel.md) |
| `journal` | 手作 | 博物手账纸面，水彩淡彩 + 钢笔批注 + 朱砂印 | [journal.md](journal.md) |
| `papercut` | 手作 | 纸艺分层剪纸，柔和纸影与折痕层次 | [papercut.md](papercut.md) |
| `archive` | 手作 | 历史档案灯台，冷白背光台面 + 纯白纸卡 + 放大镜与原版图版 | [archive.md](archive.md) |

## 2. 切换与锁定规则

- 建工程选定皮肤：`node scripts/notebook-video.mjs new-project <工程> --style=<皮肤>`；切换皮肤用 `python scripts/set-skin.py <工程> <皮肤>`。
- 填充用原色、`color:` 文字色一律用 `*Ink`（禁用 `orangeDeep` 当字色）；`gold`/`yellow` 底只放深墨字绝不放白字；禁止手改 `src/theme/active.ts`（用 `set-skin.py` 切）。
- 模板默认出厂 `src/theme/active.ts` 指向 `./flat`（由 `validate-skill-consistency.py` 强制守护）。
- **全片色调统一克制**：整片只锁一套皮肤色板，单镜高饱和强调色 ≤1 种，禁止过重滤镜、荧光失真或每镜乱换风格。
- **色板锁定**：正文必须使用 `C.ink`、`C.muted` 或 `C.*Ink` 安全色令牌，对比度 ≥ `4.5:1`（`validate-presentation.py` 强制校验）；禁止在场景里发明游离颜色。
- **背景库**：每套皮肤自带 `main` / `chapter` / `quiet` 锁定底图及可轮换背景库（手作 ≥8 张，组件 ≥4 张），亮底且字幕区对比度达标（`validate-backgrounds.py` 校验）。
- **仅读当前皮肤一篇**：选定皮肤后，代理只需读对应的 `references/themes/<皮肤>.md`，无需通读其余四篇。
