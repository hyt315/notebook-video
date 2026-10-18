import React from 'react';
import {interpolate} from 'remotion';
import type {CustomProps} from '../auto';

// 定制画面示例：请求从「应用」出发，先到「缓存」，命中就原路返回，没命中才继续走到「数据库」。
// story.json 里声明的元素：app / cache / db（矩形 = 设计坐标）。台词说到 {{缓存}} 时引擎自动推近 cache。
// 这张图只为这个题目而画——这正是定制画面存在的理由。
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};

export const RequestLane: React.FC<CustomProps> = ({f, el, line, C}) => {
  const app = el('app'), cache = el('cache'), db = el('db');
  if (!app.el || !cache.el || !db.el) return null;
  const node = (n: typeof app, title: string, sub: string, accent: string) => (
    <div style={{position: 'absolute', left: n.el!.x, top: n.el!.y, width: n.el!.w, height: n.el!.h, opacity: n.in, transform: `translateY(${(1 - n.in) * 14}px)`}}>
      <div style={{position: 'absolute', inset: -8, borderRadius: 26, background: C.orangeLight, border: `3px solid ${C.orange}`, opacity: n.hi}} />
      <div style={{position: 'absolute', inset: 0, borderRadius: 22, background: C.paper, border: `2px solid ${C.line}`, borderTop: `8px solid ${accent}`, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: 10}}>
        <div style={{fontSize: 46, fontWeight: 700, color: C.ink}}>{title}</div>
        <div style={{fontSize: 34, color: C.muted}}>{sub}</div>
      </div>
    </div>
  );
  const y = app.el.y + app.el.h / 2;
  const x0 = app.el.x + app.el.w, x1 = cache.el.x, x2 = cache.el.x + cache.el.w, x3 = db.el.x;
  // 请求点：每 40 帧发一个；第 2 句之后 4 个里只有 1 个穿过缓存（命中率 75%+）
  const start = line(0) + 20;
  const dots: React.ReactNode[] = [];
  for (let k = 0; k < 14; k++) {
    const t0 = start + k * 40;
    const local = f - t0;
    if (local < 0 || local > 70) continue;
    const miss = f < line(1) ? true : k % 4 === 0;
    const go = interpolate(local, [0, 24], [x0 + 10, x1 - 14], clamp);
    const back = miss ? interpolate(local, [24, 52], [x2 + 14, x3 - 14], clamp) : interpolate(local, [24, 48], [x1 - 14, x0 + 10], clamp);
    const x = local < 24 ? go : back;
    const o = interpolate(local, [0, 4, 62, 70], [0, 1, 1, 0], clamp);
    dots.push(<div key={k} style={{position: 'absolute', left: x - 10, top: y - 10, width: 20, height: 20, borderRadius: 10, background: miss && local >= 24 ? C.orange : C.green, opacity: o}} />);
  }
  return <>
    <div style={{position: 'absolute', left: x0, top: y - 2, width: x1 - x0, height: 4, background: C.mutedBar, opacity: cache.in}} />
    <div style={{position: 'absolute', left: x2, top: y - 2, width: x3 - x2, height: 4, background: C.mutedBar, opacity: db.in}} />
    {node(app, '应用', '收到请求', C.blue)}
    {node(cache, '缓存', '算过就直接给', C.green)}
    {node(db, '数据库', '慢，但总是对的', C.orange)}
    {dots}
  </>;
};
