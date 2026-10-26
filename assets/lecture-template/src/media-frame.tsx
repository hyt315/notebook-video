// 3.2.0 真实素材：截图 / 录屏 / 动图放进与默认组件风格同一套卡片语言里（THEME.Paper + 主题色），帧驱动。
//
//   素材登记在 manifests/media.json（prepare-media.py 会同步一份到 src/media.json），文件放 public/media/。
//   <MediaFrame f={f} id="pr-page" x={200} y={200} w={1100} h={620} chrome="browser" focus="diff" focusAt={b[1]} />
//
// 纪律：
//   · 只用帧号 f 驱动（入场、区域推近、高亮框都是 interpolate）；视频走 <OffthreadVideo>，起止帧由 trimStartSec/trimEndSec 推出。
//   · 缺省静音；manifest 里 muted:false 才出声（validate-media 会提示）。
//   · source:"web" 的素材**一定**在画面上显示署名徽章（没有关掉它的参数）。
//   · 推近到截图某块：focus = 区域 id（区域坐标是 0–1 的相对坐标）；也可以同时在镜头表 cinema.focus 里推近整个 MediaFrame。
import React from 'react';
import {Freeze, Img, OffthreadVideo, Sequence, interpolate, Easing, staticFile, useCurrentFrame} from 'remotion';
import {THEME} from './theme/active';
import MEDIA_DOC from './media.json';

const C = THEME.palette;
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const ease = Easing.bezier(0.16, 1, 0.3, 1);

export type MediaRegion = {id: string; x: number; y: number; w: number; h: number};
export type MediaEntry = {
  id: string; file: string; kind: 'image' | 'video' | 'gif' | 'audio'; source: 'user' | 'web';
  url?: string; license?: string; credit?: string; width?: number; height?: number;
  trimStartSec?: number; trimEndSec?: number; durationSec?: number; focusRegions?: MediaRegion[]; muted?: boolean;
};
export const MEDIA: Record<string, MediaEntry> = Object.fromEntries(((MEDIA_DOC as any).items ?? []).map((m: MediaEntry) => [m.id, m]));

type Callout = {region: string; text: string; at: number; side?: 'top' | 'bottom'};
export type MediaFrameProps = {
  f: number; id: string; x: number; y: number; w: number; h: number;
  /** 外壳：browser（地址栏）/ window（三个圆点）/ device（手机圆角边框）/ none（只有卡片） */
  chrome?: 'browser' | 'window' | 'device' | 'none';
  fit?: 'contain' | 'cover';
  at?: number;             // 入场帧
  focus?: string;          // 推近到哪个区域
  focusAt?: number; focusUntil?: number; focusZoom?: number;
  highlight?: readonly string[]; highlightAt?: number;   // 只描框不推近
  callouts?: readonly Callout[];
  label?: string;          // browser 地址栏文字（缺省用 manifest 的 url）
};

const CHROME_H = {browser: 46, window: 40, device: 0, none: 0} as const;

export const MediaFrame: React.FC<MediaFrameProps> = ({f, id, x, y, w, h, chrome = 'browser', fit = 'contain', at = 0, focus, focusAt = 0, focusUntil, focusZoom, highlight = [], highlightAt = 0, callouts = [], label}) => {
  const m = MEDIA[id];
  if (!m) throw new Error(`MediaFrame: manifests/media.json 里没有 id="${id}"（先跑 prepare-media）`);
  const inP = interpolate(f, [at, at + 18], [0, 1], {...clamp, easing: ease});
  const ch = CHROME_H[chrome];
  const pad = chrome === 'device' ? 18 : 0;
  const vw = w - pad * 2, vh = h - ch - pad * 2;              // 视口
  // 素材在视口里的尺寸（contain / cover）
  const iw = m.width ?? vw, ih = m.height ?? vh;
  const k = fit === 'cover' ? Math.max(vw / iw, vh / ih) : Math.min(vw / iw, vh / ih);
  const dw = iw * k, dh = ih * k, ox = (vw - dw) / 2, oy = (vh - dh) / 2;
  const R = (rid: string) => {
    const r = (m.focusRegions ?? []).find((q) => q.id === rid);
    if (!r) throw new Error(`MediaFrame: 素材 ${id} 没有区域 "${rid}"`);
    return {x: ox + r.x * dw, y: oy + r.y * dh, w: r.w * dw, h: r.h * dh};
  };
  // 区域推近（帧驱动）：缩放让区域占视口 ~80%，注视点钳在素材内，绝不露出素材外的空白
  let s = 1, tx = 0, ty = 0;
  if (focus) {
    const r = R(focus);
    const zIn = interpolate(f, [focusAt, focusAt + 20], [0, 1], {...clamp, easing: ease});
    const zOut = focusUntil != null ? interpolate(f, [focusUntil, focusUntil + 24], [1, 0], {...clamp, easing: ease}) : 1;
    const z = Math.min(zIn, zOut);
    const target = Math.max(1, Math.min(focusZoom ?? 0.8 * Math.min(vw / r.w, vh / r.h), 2.4));
    s = 1 + (target - 1) * z;
    const cx = Math.min(Math.max(r.x + r.w / 2, vw / 2 / s), vw - vw / 2 / s);
    const cy = Math.min(Math.max(r.y + r.h / 2, vh / 2 / s), vh - vh / 2 / s);
    tx = (vw / 2 - cx * s) * z;
    ty = (vh / 2 - cy * s) * z;
  }
  const fps = 30;
  const src = staticFile(`media/${m.file}`);
  const muted = m.muted !== false;
  // 场景是按本镜本地帧 f 挂载的（不是 <Sequence>），所以视频时间轴要自己对齐：从入场帧 at 开始播，播完停在最后一帧。
  const abs = useCurrentFrame();
  const t0 = Math.round((m.trimStartSec ?? 0) * fps);
  const t1 = m.trimEndSec != null ? Math.round(m.trimEndSec * fps) : m.durationSec ? Math.floor(m.durationSec * fps) : Infinity;
  const vid = <OffthreadVideo src={src} muted={muted} startFrom={t0} endAt={Number.isFinite(t1) ? t1 : undefined} style={{width: dw, height: dh, display: 'block'}} />;
  const media = m.kind === 'video'
    ? (f - at >= t1 - t0 - 1
      ? <Sequence from={abs - f + at} layout="none"><Freeze frame={t1 - t0 - 1}>{vid}</Freeze></Sequence>
      : <Sequence from={abs - f + at} layout="none">{vid}</Sequence>)
    : <Img src={src} style={{width: dw, height: dh, display: 'block'}} />;
  const hiBoxes = [...highlight, ...(focus ? [focus] : [])];
  const hiW = interpolate(f, [Math.min(highlightAt, focusAt) + 6, Math.min(highlightAt, focusAt) + 16], [0, 1], clamp);
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, opacity: inP, transform: `translateY(${(1 - inP) * 14}px)`}}>
      <THEME.Paper style={{position: 'absolute', inset: 0, overflow: 'hidden', padding: 0, borderRadius: chrome === 'device' ? 44 : THEME.aesthetic.paperRadius}}>
        {chrome === 'browser' || chrome === 'window' ? (
          <div style={{position: 'absolute', left: 0, top: 0, right: 0, height: ch, background: C.paperWarm, borderBottom: `2px solid ${C.line}`, display: 'flex', alignItems: 'center', gap: 10, padding: '0 18px', boxSizing: 'border-box'}}>
            {[C.orange, C.gold, C.green].map((c, i) => <div key={i} style={{width: 13, height: 13, borderRadius: 7, background: c}} />)}
            {chrome === 'browser' && <div style={{marginLeft: 14, flex: 1, height: 28, borderRadius: 14, background: C.paper, border: `2px solid ${C.line}`, fontFamily: 'Space,Kai', fontSize: 16, lineHeight: '24px', color: C.muted, padding: '0 14px', overflow: 'hidden', whiteSpace: 'nowrap'}}>{label ?? m.url ?? ''}</div>}
          </div>
        ) : null}
        <div style={{position: 'absolute', left: pad, top: ch + pad, width: vw, height: vh, overflow: 'hidden', borderRadius: chrome === 'device' ? 30 : 0, background: C.paperBase}}>
          <div style={{position: 'absolute', left: 0, top: 0, width: vw, height: vh, transformOrigin: '0 0', transform: `translate(${tx}px, ${ty}px) scale(${s})`}}>
            <div style={{position: 'absolute', left: ox, top: oy}}>{media}</div>
          </div>
          {/* 3.2.0 区域高亮（默认组件风格的描边 + 轻抬升，画在视口坐标里：线宽恒定 4px、不随区域推近变粗变细）：
              ① 区域外压一层淡暗幕（0.16），让被点名的区域「亮出来」——以前只有一圈细框，缩小看几乎看不见；
              ② 橙色 4px 描边 + 2px 白内圈（任何截图底色上都看得清）+ 抬升阴影，并上移 3px；
              ③ 区域在视口里露出 < 90% 时（例如推近别的区域把它挤到边上）不画，免得出现被视口切掉的半个框。 */}
          {(() => {
            const vis = hiBoxes.map((rid) => {
              const r = R(rid), x0 = tx + r.x * s - 8, y0 = ty + r.y * s - 8, x1 = tx + (r.x + r.w) * s + 8, y1 = ty + (r.y + r.h) * s + 8;
              const iw2 = Math.max(0, Math.min(vw, x1) - Math.max(0, x0)), ih2 = Math.max(0, Math.min(vh, y1) - Math.max(0, y0));
              return {rid, x0, y0, w: x1 - x0, h: y1 - y0, ok: (iw2 * ih2) / ((x1 - x0) * (y1 - y0)) >= 0.9};
            }).filter((b) => b.ok);
            if (!vis.length || hiW <= 0.01) return null;
            const mid = `mf-hi-${id}`;
            return <>
              <svg width={vw} height={vh} style={{position: 'absolute', left: 0, top: 0, opacity: hiW}}>
                <defs><mask id={mid}><rect width={vw} height={vh} fill="#fff" />{vis.map((b) => <rect key={b.rid} x={b.x0} y={b.y0} width={b.w} height={b.h} rx={12} fill="#000" />)}</mask></defs>
                <rect width={vw} height={vh} fill="rgba(28,32,36,0.16)" mask={`url(#${mid})`} />
              </svg>
              {vis.map((b) => <div key={b.rid} data-media-highlight={b.rid} style={{position: 'absolute', left: b.x0, top: b.y0, width: b.w, height: b.h, boxSizing: 'border-box', borderRadius: 12, border: `4px solid ${C.orange}`, boxShadow: `inset 0 0 0 2px rgba(255,255,255,0.9), 0 10px 28px rgba(0,0,0,${0.18 * hiW})`, opacity: hiW, transform: `translateY(${-3 * hiW}px)`}} />)}
            </>;
          })()}
          {callouts.map((c, i) => {
            const r = R(c.region); const p = interpolate(f, [c.at, c.at + 14], [0, 1], {...clamp, easing: ease});
            const cx = tx + r.x * s, cy = ty + (c.side === 'top' ? r.y * s - 64 : (r.y + r.h) * s + 14);
            return <div key={i} style={{position: 'absolute', left: Math.max(8, Math.min(vw - 420, cx)), top: Math.max(8, Math.min(vh - 56, cy)), maxWidth: 420, opacity: p, background: C.blueInk, color: C.white, fontFamily: 'Kai', fontWeight: 700, fontSize: 28, padding: '8px 18px', borderRadius: 999}}>{c.text}</div>;
          })}
        </div>
        {m.source === 'web' && (
          <div data-media-credit={id} style={{position: 'absolute', right: 14, bottom: 12, background: 'rgba(28,32,36,0.72)', color: '#fff', fontFamily: 'Space,Kai', fontSize: 16, padding: '4px 12px', borderRadius: 999, whiteSpace: 'nowrap'}}>
            {`© ${m.credit ?? ''} · ${m.license ?? ''}`}
          </div>
        )}
      </THEME.Paper>
    </div>
  );
};
