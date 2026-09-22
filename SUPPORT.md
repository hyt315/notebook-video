# Support

## Where to ask

| What | Where |
|---|---|
| Usage questions, ideas, showing what you made | [Discussions](https://github.com/hyt315/notebook-video/discussions) |
| A reproducible bug | [New issue → Bug report](https://github.com/hyt315/notebook-video/issues/new?template=bug_report.yml) |
| A feature request | [New issue → Feature request](https://github.com/hyt315/notebook-video/issues/new?template=feature_request.yml) |
| A security vulnerability | [Private vulnerability reporting](https://github.com/hyt315/notebook-video/security/advisories/new) — never a public issue, see [SECURITY.md](SECURITY.md) |

Blank issues are disabled on purpose: the templates ask for the details needed to reproduce a problem in a frame-driven renderer.

## What to include in a bug report

- **Version** — the release tag (for example `v3.1.0`) or the commit SHA
- **OS and Node version**, plus the output of `ffmpeg -version`
- **The exact command you ran** and the full error text
- **The frame number**, when the problem is visible in one specific frame
- Whether it still reproduces with the bundled template (`assets/lecture-template`) unmodified

## Before opening an issue

1. `node scripts/notebook-video.mjs check-deps`
2. `python scripts/selftest.py`
3. The build-time gates for your project — a non-zero P0 is a real finding, not a setup problem

## Scope and response

This is a single-maintainer project and there is **no support SLA**. Security reports are acknowledged within five business days per [SECURITY.md](SECURITY.md). Questions about third-party services (Remotion, TTS providers, image generation) belong with those vendors.

---

# 支持

## 去哪儿问

| 事项 | 去处 |
|---|---|
| 用法问题、想法、晒作品 | [Discussions](https://github.com/hyt315/notebook-video/discussions) |
| 可复现的缺陷 | [新建 issue → Bug report](https://github.com/hyt315/notebook-video/issues/new?template=bug_report.yml) |
| 功能建议 | [新建 issue → Feature request](https://github.com/hyt315/notebook-video/issues/new?template=feature_request.yml) |
| 安全漏洞 | [私密漏洞上报](https://github.com/hyt315/notebook-video/security/advisories/new)——**不要开公开 issue**，见 [SECURITY.md](SECURITY.md) |

空白 issue 是刻意关闭的：模板会问清"复现一个帧驱动渲染问题"所必需的信息。

## 报缺陷请带上

- **版本**：发布 tag（如 `v3.1.0`）或 commit SHA
- **系统与 Node 版本**，以及 `ffmpeg -version` 的输出
- **你执行的完整命令**与完整报错原文
- **帧号**（如果是某一帧上的画面问题）
- 用自带模板（`assets/lecture-template`）原样跑是否也能复现

## 提问前先跑三步

1. `node scripts/notebook-video.mjs check-deps`
2. `python scripts/selftest.py`
3. 你工程的构建期门禁——P0 不为 0 是**真发现**，不是环境问题

## 范围与响应

单维护者项目，**没有支持 SLA**；安全报告按 [SECURITY.md](SECURITY.md) 在五个工作日内确认。Remotion、TTS 提供方、生图服务这类第三方问题，请找对应厂商。
