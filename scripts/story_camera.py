"""story_camera.py — compose-story 的取景计算。

从 `compose-story.py` 里切出来的第一块。那个文件同时管排版、字幕定时、相机、自动修，
其中最"纯"的一组函数就是取景：给它一镜的元素盒子和一块要看清的区域，它算出
「推近多少倍、往哪儿看」，并保证推近之后没有任何文字被安全框切断。

先切这一块的理由：它没有 IO、没有全局状态、没有副作用，切出去行为不可能变；
而它又是最容易写错的部分（回退搜索 + 两档倍率校验），单独成文件才测得动。

坐标系：设计坐标 1920×1080。`SAFE` 是推近后元素必须完整落进去的屏幕安全框
（顶部 178 有遮罩，底部留给字幕）。
"""
import math

# 屏幕安全框：推近后元素必须完整落在这里（顶 178 有遮罩、底是字幕）
SAFE = (130, 196, 1790, 862)
ZOOM_MAX = 1.32

def to_screen(r, look, s):
    return ((r["x"] - look[0]) * s + 960, (r["y"] - look[1]) * s + 540, r["w"] * s, r["h"] * s)


def clamp_look(x, y, s):
    hx, hy = 960 / s, 540 / s
    return (min(1920 - hx, max(hx, x)), min(1080 - hy, max(hy, y)))


def partial_clips(look, s, els):
    """取景窗（屏幕安全框）会切断哪些文字元素：一部分在框内、一部分在框外。"""
    bad = []
    for e in els:
        if e["kind"] in ("arrow", "codebox"):
            continue
        x, y, w, h = to_screen(e, look, s)
        inside = x >= SAFE[0] - 2 and y >= SAFE[1] - 2 and x + w <= SAFE[2] + 2 and y + h <= SAFE[3] + 2
        # 顶部遮罩：y < 140 完全隐去，140–178 是羽化带 → 文字底边必须在 150 以上才算「完全在框外」
        outside = x + w <= 0 or x >= 1920 or y + h <= 150 or y >= 1080
        if not inside and not outside:
            bad.append(e["id"])
    return bad


def frame_rect(r, els, max_s=ZOOM_MAX, min_s=1.0):
    """把矩形 r 取进安全框：先按 r 求最大推近，再逐级回退，直到没有任何文字元素被取景窗切断。"""
    pad = 36
    rw, rh = r["w"] + 2 * pad, r["h"] + 2 * pad
    sw, sh = SAFE[2] - SAFE[0], SAFE[3] - SAFE[1]
    s = max(min_s, min(max_s, 0.92 * min(sw / rw, sh / rh)))
    cx, cy = r["x"] + r["w"] / 2, r["y"] + r["h"] / 2
    scy = (SAFE[1] + SAFE[3]) / 2  # 安全框中心在 529，略高于画面中心
    tries = []
    offs = sorted(range(-480, 481, 40), key=abs)
    offy = sorted(range(-300, 301, 30), key=abs)
    while s >= min_s - 1e-9:
        seen = set()
        for dy in offy:
            for dx in offs:
                look = clamp_look(cx + dx / s, cy - (scy - 540) / s + dy / s, s)
                key = (round(look[0]), round(look[1]))
                if key in seen:
                    continue
                seen.add(key)
                sx, sy, sw_, sh_ = to_screen(r, look, s)
                if sx < SAFE[0] - 1 or sy < SAFE[1] - 1 or sx + sw_ > SAFE[2] + 1 or sy + sh_ > SAFE[3] + 1:
                    continue
                # 运行时还有 ≤3.5% 的慢推 + 微漂移：两个倍数都要不切字
                if not partial_clips(look, s, els) and not partial_clips(look, s * 1.035, els):
                    return {"x": round(look[0], 1), "y": round(look[1], 1), "s": round(s, 3)}, tries
        tries.append(round(s, 3))
        s -= 0.03
    return {"x": 960.0, "y": 540.0, "s": 1.0}, tries


def union(els):
    xs = [e["x"] for e in els]; ys = [e["y"] for e in els]
    x2 = [e["x"] + e["w"] for e in els]; y2 = [e["y"] + e["h"] for e in els]
    return {"x": min(xs), "y": min(ys), "w": max(x2) - min(xs), "h": max(y2) - min(ys)}


def move_frames(a, b):
    """速度上限：屏幕位移 ≤ 28 px/帧、缩放 ≤ 0.012/帧；至少 16 帧、至多 34 帧。"""
    dist = math.hypot((a["x"] - b["x"]) * max(a["s"], b["s"]), (a["y"] - b["y"]) * max(a["s"], b["s"]))
    return int(max(16, min(34, max(dist / 28, abs(a["s"] - b["s"]) / 0.012))))
