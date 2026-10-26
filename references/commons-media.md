# 真实素材：先搜 Wikimedia Commons / Openverse（3.3.0）

> 工具：`scripts/commons-search.py`（只用 Python 标准库；下载后的入库 / 转码复用 `prepare-media.py`）。
> 原则：**每个选题先搜一次**。1665 年的铜版画、第一张 X 光片、真实的显微照片、一段历史录音——真东西几乎总能让片子更好。
> 能找到就用；找不到也没关系，写清搜了什么（搜索记录会落进 `manifests/commons-log.json`，导演层门禁看它）。

## 两个源

| 源 | 规模 / 内容 | 接口 | 为什么用它 |
|---|---|---|---|
| [Wikimedia Commons](https://commons.wikimedia.org/) | 1 亿多个文件：图片、视频、声音；每个文件都有结构化许可元数据（`extmetadata`） | MediaWiki Action API `https://commons.wikimedia.org/w/api.php`，免 key | 首选：覆盖最大、元数据最规整、大量公有领域历史图版 |
| [Openverse](https://openverse.org/)（MIT，WordPress 基金会维护） | 聚合 Flickr、博物馆图片与 Freesound、Jamendo 等声音 | `https://api.openverse.org/v1/`，免 key | 补声音（Commons 的声音搜索大半是读音录音）与博物馆图；请求时只要 `cc0,pdm,by` |

没有引入 pywikibot（重、要配账号）或 mwclient（第三方依赖，违背"scripts 只用标准库"）：直接 HTTP 的薄客户端足够。

## 三条命令

```text
# 1) 搜。带 --project 会记搜索日志、缓存 API 响应（.cache/commons/，同一查询不重复打 API）
python scripts/commons-search.py search "Hooke Micrographia cork" --project ./my-video
python scripts/commons-search.py search "pencil writing" --type audio --project ./my-video
python scripts/commons-search.py search "cork cells microscope" --source openverse --project ./my-video

# 2) 选一条入库：查许可、写 url / license / credit / 结构化署名，走 prepare-media 转码与尺寸登记
python scripts/commons-search.py add ./my-video "File:Micrographia Schem 11.jpg" --id hooke-plate --width 2560
python scripts/commons-search.py add ./my-video "openverse:audio:<id>" --id scratch --trim 0 4

# 3) 交付前写成片署名清单（也给发布简介用）
python scripts/commons-search.py credits ./my-video     # → CREDITS.md
```

搜索结果每条给出：标题、尺寸、许可（已归一）、作者、页面链接；不合格的许可直接不列。

## 许可白名单

| 许可 | 默认 | 说明 |
|---|---|---|
| 公有领域（PD-*、PDM）、CC0 | ✓ | 不要求署名，本工具照样署名（好习惯，也方便核查） |
| CC BY 1.0–4.0 | ✓ | 必须署名：作者 + 许可 + 来源链接（TASL），自动生成并强制上屏 |
| CC BY-SA | ✗（`--allow-by-sa` 才收） | "相同方式共享"：用它做的改编作品（整条片子很可能算）须以 CC BY-SA 发布。短视频平台的发布条款通常与此冲突，缺省不用；收了会在 manifest 记 `shareAlike:true`，`validate-media` 提示一次，CREDITS.md 写明义务 |
| GFDL、FAL、NC、ND、无版本的 "Attribution"、Flickr 的 "No known restrictions"、未知 | ✗ | 一律排除（"无已知限制" ≠ 公有领域） |

## 放进画面：用 craft 组件，不要裸贴

| 素材 | 组件（[craft-kit.md](craft-kit.md)） |
|---|---|
| 历史图版、扫描件、手稿 | `ArchivePhoto`（纸托 + 编目签署名）；要"看近"用 `LoupeMedia` |
| 现代照片、标本照 | `PinnedPhoto`（白边 + 胶带 + 手写说明 + 署名） |
| 声音 | `MediaAudio`（按帧起播；拟音音量放在音效阶梯附近） |
| 界面截图 / 录屏 | 仍用 `MediaFrame`（[real-media.md](real-media.md)） |

署名规则：`source:"web"` 的素材**一定**在画面上显示署名；片尾 / 简介再放 `CREDITS.md` 全文。
清晰度：`validate-media` 按组件的字面量 `w` / `h` 与推近倍数算放大比，>1.5 倍会糊 → P0（用 `--width` 取更大的缩略图或缩小显示框）。

## API 礼仪

- 必带 User-Agent（项目地址 + 联系方式），可用环境变量 NOTEBOOK_VIDEO_UA 覆盖；
- 串行请求，相邻请求 ≥1 秒，`maxlag=5`；429 / 503 按 `Retry-After` 退避，最多重试 4 次；
- 缩略图走 Commons 的 `iiurlwidth`（服务器端缩放），不下原图大文件。

## 测试

`tests/test_commons.py`：离线夹具（`tests/fixtures/`）覆盖许可归一、BY-SA 排除、署名串、Openverse 结果解析、CREDITS 生成；不访问网络。
