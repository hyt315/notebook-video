// ============================================================================
// craft/media.tsx · 真实素材「放进媒介里」（3.3.0）
//
//   ArchivePhoto  档案件：素材原样（真实比例、真实破损）躺在纸托 / 灯台上，下方编目签 = 署名
//   PinnedPhoto   贴进手账的照片：白边、胶带或图钉、微倾，可选做旧（sepia）/ 双色调
//   LoupeMedia    放大镜压在素材上：镜片里是原图放大（可切到 negative→positive 等「状态变化」）
//   MediaAudio    Commons / Openverse 的真实声音（拟音 / 历史录音），按帧放
//
// 署名：source:"web" 的素材**一定**在画面上显示署名（编目签 / 照片下沿小字），组件没有关掉它的参数；
//       validate-media 认得这些组件名，按字面量 w / h 量放大倍数（>1.5 倍会糊 → P0）。
// 素材从 manifests/media.json 读（commons-search.py add / prepare-media.py 写）。
// ============================================================================
import React from 'react';
import {Audio} from '@remotion/media';
import {Img, Sequence, staticFile} from 'remotion';
import {THEME} from '../theme/active';
import {MEDIA} from '../media-frame';
import {TapeStrip} from '../theme/craft-common';
import {Loupe, pickHandleAngle} from './lens';
import {prog, CRAFT_TYPE} from './ink';
import {MODES} from '../theme/canvas';

const C = THEME.palette;
const need = (id: string) => {
  const m = MEDIA[id];
  if (!m) throw new Error(`craft media: manifests/media.json 里没有 id="${id}"（先跑 commons-search.py add 或 prepare-media.py --add）`);
  return m;
};
/** 画面上的署名串（web 素材必显示）。 */
export const creditOf = (id: string) => {
  const m = need(id);
  return m.source === 'web' ? (m.credit || m.license || '') : '';
};

export type Treatment = 'none' | 'sepia' | 'duotone' | 'negative' | 'ink';
const filterOf = (t: Treatment) => ({
  none: 'none', sepia: 'sepia(0.55) contrast(1.05) brightness(1.02)', duotone: 'grayscale(1) contrast(1.15) sepia(0.35) hue-rotate(-10deg)',
  negative: 'invert(1) grayscale(1) contrast(1.1)', ink: 'grayscale(1) contrast(1.35) brightness(1.05)',
}[t]);

type Base = {f: number; id: string; x: number; y: number; w: number; h: number; at?: number; rot?: number; treatment?: Treatment};

/** 素材在 w×h 框里 contain 后的实际尺寸（真实比例，不裁、不拉伸）。 */
const fitBox = (id: string, w: number, h: number) => {
  const m = need(id); const iw = m.width ?? w, ih = m.height ?? h; const k = Math.min(w / iw, h / ih);
  return {dw: iw * k, dh: ih * k};
};

/** 编目签的宽度（side 版式固定；below 版式跟图同宽、至少 240）。 */
const SLIP_SIDE_W = 300, SLIP_GAP = 18;
/** 3.3.0 层级：图片区至少占纸托卡片（图 + 纸托边）面积的 70%——纸托边按这个比例自动收窄（不超过传入的 mount）。 */
export const ARCHIVE_MIN_IMAGE_FRAC = 0.7;
/** 3.3.0 层级：编目签（编号 / 名称）字号不超过图片区高度的 12%——签不能比文物还抢眼。署名字号不缩（CC BY 要可读）。 */
export const ARCHIVE_LABEL_MAX_FRAC = 0.12;
const LABEL_FONT_MAX = 30, CREDIT_FONT = 22;
/** 署名的字宽 / 行高估算：跟着 CREDIT_FONT 走，字号一改签高自动跟上（3.3.0 P1-10）。 */
const CREDIT_CHAR_W = 12, CREDIT_LINE_H = 27;   // 3.3.0 评审 P1-10：18/20 px 在手机上读不出，等于署名缺失
/** 编目签标题字号：≤ 30，且 ≤ 图高 × 12%（下限 12，再小就不是字了）。编号字号 = 标题 × 0.8。 */
export const archiveLabelFont = (dh: number) => Math.max(12, Math.min(LABEL_FONT_MAX, Math.floor(dh * ARCHIVE_LABEL_MAX_FRAC)));
/** 纸托边：满足 dw·dh ≥ 70%·(dw+2m)(dh+2m) 的最大 m（不超过 mount）。 */
export const archiveMount = (dw: number, dh: number, mount: number) => {
  const k = 1 / ARCHIVE_MIN_IMAGE_FRAC - 1; // (dw+2m)(dh+2m) ≤ dw·dh/0.7  ⇔  4m² + 2m(dw+dh) − k·dw·dh ≤ 0
  const mmax = (-2 * (dw + dh) + Math.sqrt(4 * (dw + dh) ** 2 + 16 * k * dw * dh)) / 8;
  return Math.max(0, Math.min(mount, Math.floor(mmax)));
};

/**
 * 3.3.0 组件规则：署名签不进字幕带。字幕框顶 = designH − subBottom − subH（16:9 为 934）；
 * 再让出 CAPTION_CLEAR，这样招牌镜头以画面中心推 12.5% 后签底也压不到字幕
 * （540 + (874 − 540) × 1.125 ≈ 916 < 934）。cell 演示片 S3/S4 的 Schem. XI 署名曾被 OCR 读进字幕带。
 */
export const CAPTION_CLEAR = 60;
const CANVAS = MODES['16:9'];
export const CREDIT_SAFE_BOTTOM = CANVAS.designH - CANVAS.subBottom - CANVAS.subH - CAPTION_CLEAR;
/** 放在设计坐标 y 处、框高 h 的档案件实际可用高度：底边不越过 CREDIT_SAFE_BOTTOM；最多让出一半框高（再多图就没了）。y 未知时不变。 */
export const archiveSafeH = (y: number | undefined, h: number) =>
  y === undefined ? h : Math.max(Math.round(h * 0.5), Math.min(h, Math.floor(CREDIT_SAFE_BOTTOM - y)));

/**
 * 档案件的版式：图（真实比例）+ 纸托 + 编目签，**一起**装进 w×h 框。
 *   below：签在图下（横图）；side：签在图右下（竖图放进横框时，签放下面会把图挤得很小）。
 *   auto（缺省）：两种都算，取图更大的那个。
 * 签高按字数估（署名在窄签里换行，不截断），图为它让出位置，签不会被挤出框外。
 * 传入 y（框在画面上的设计坐标）时，整件底边不越过 CREDIT_SAFE_BOTTOM（署名签不进字幕带）。
 * 3.3.0：纸托边按 ARCHIVE_MIN_IMAGE_FRAC 收窄、编目签字号按 ARCHIVE_LABEL_MAX_FRAC 封顶（见上面两个常量）。
 */
export type ArchiveLabel = 'auto' | 'below' | 'side';
export const archiveLayout = (id: string, w: number, frameH: number, mount: number, labelled: boolean, label: ArchiveLabel = 'auto', y?: number) => {
  const h = archiveSafeH(y, frameH); // 3.3.0：传入 y 时整件（图 + 签）收在字幕安全线以上
  const credit = creditOf(id);
  const has = labelled || Boolean(credit);
  const slipH = (sw: number, dh: number) => !has ? 0 : 17 + (labelled ? Math.ceil(archiveLabelFont(dh) * 1.2) : 0) + (credit ? 4 + CREDIT_LINE_H * Math.ceil((credit.length * CREDIT_CHAR_W) / Math.max(120, sw - 19)) : 0);
  // 每种版式三轮收敛：图尺寸 → 签高 / 纸托边 → 回头缩放图
  const solve = (mode: 'below' | 'side') => {
    let m = mount;
    let b = fitBox(id, w - m * 2 - (mode === 'side' && has ? SLIP_SIDE_W + SLIP_GAP : 0), h - m * 2);
    for (let k = 0; k < 3; k++) {
      m = archiveMount(b.dw, b.dh, mount);
      const sw = mode === 'side' ? SLIP_SIDE_W : Math.max(b.dw + m * 2, 240);
      b = mode === 'side'
        ? fitBox(id, w - m * 2 - (has ? SLIP_SIDE_W + SLIP_GAP : 0), h - m * 2)
        : fitBox(id, w - m * 2, h - m * 2 - (has ? 10 : 0) - slipH(sw, b.dh));
    }
    m = archiveMount(b.dw, b.dh, mount);
    const slipW = mode === 'side' ? SLIP_SIDE_W : Math.max(b.dw + m * 2, 240);
    return {mode, ...b, mount: m, slipW, slipH: slipH(slipW, b.dh)};
  };
  const below = solve('below');
  const side = solve('side');
  const pick = !has || label === 'below' ? below : label === 'side' ? side : (side.dw * side.dh > below.dw * below.dh * 1.15 ? side : below);
  const mt = pick.mount;
  const boxW = pick.dw + mt * 2, boxH = pick.dh + mt * 2;
  const totalW = pick.mode === 'side' && has ? boxW + SLIP_GAP + pick.slipW : boxW;
  const totalH = pick.mode === 'below' && has ? boxH + 10 + pick.slipH : Math.max(boxH, pick.slipH);
  const left = (w - totalW) / 2, top = (h - totalH) / 2;
  const labelFont = archiveLabelFont(pick.dh);
  return {...pick, left, top, imgX: left + mt, imgY: top + mt, labelFont, catalogueFont: Math.round(labelFont * 0.8), creditFont: CREDIT_FONT,
    slipX: pick.mode === 'side' ? left + boxW + SLIP_GAP : left, slipY: pick.mode === 'side' ? top + boxH - pick.slipH : top + boxH + 10};
};

/** 档案件：真实素材 + 纸托边 + 编目签（编号 / 名称 / 署名，署名不截断）。 */
export const ArchivePhoto: React.FC<Base & {catalogue?: string; title?: string; mount?: number; label?: ArchiveLabel}> =
  ({f, id, x, y, w, h, at = 0, rot = 0, treatment = 'none', catalogue, title, mount = 22, label = 'auto'}) => {
    const m = need(id);
    const p = prog(f, at, 14);
    if (p <= 0) return null;
    const credit = creditOf(id);
    const L = archiveLayout(id, w, h, mount, Boolean(catalogue || title), label, y);
    const drop = 24 * (1 - p);
    return <div style={{position: 'absolute', left: x, top: y - drop, width: w, height: h, opacity: Math.min(1, p * 2), transform: `rotate(${rot}deg)`}}>
      <div style={{position: 'absolute', left: L.left, top: L.top, background: C.paperWarm, padding: L.mount, border: '1px solid rgba(0,0,0,0.08)',
        boxShadow: `0 ${3 + 12 * (1 - p)}px ${8 + 14 * (1 - p)}px rgba(20,25,30,0.22)`}}>
        <Img src={staticFile(`media/${m.file}`)} style={{display: 'block', width: L.dw, height: L.dh, filter: filterOf(treatment)}} />
      </div>
      {(catalogue || title || credit) && <div style={{position: 'absolute', left: L.slipX, top: L.slipY, width: L.slipW, boxSizing: 'border-box', background: C.paper,
        padding: '8px 14px 9px', borderLeft: `5px solid ${THEME.craft?.accent ?? C.orange}`, boxShadow: '0 1px 3px rgba(0,0,0,0.12)'}}>
        {(catalogue || title) && <div style={{fontFamily: 'NotoSerifSC,Kai', fontWeight: 700, fontSize: L.labelFont, lineHeight: 1.2, color: C.ink, whiteSpace: 'nowrap'}}>
          {catalogue && <span style={{fontFamily: 'Space,Kai', fontSize: L.catalogueFont, letterSpacing: 3, color: C.orangeInk, marginRight: 12}}>{catalogue}</span>}{title}</div>}
        {/* 署名不截断（CC BY 要求完整署名）：窄签里换行，而不是省略号 */}
        {credit && <div style={{fontFamily: 'Space,Kai', fontSize: L.creditFont, color: C.ink, marginTop: 4, lineHeight: 1.25, overflowWrap: 'anywhere'}}>{credit}</div>}
      </div>}
    </div>;
  };

/** 贴进本子的照片：白边 + 胶带（或图钉），下沿手写说明 + 署名。 */
export const PinnedPhoto: React.FC<Base & {caption?: string; fix?: 'tape' | 'pin'}> = ({f, id, x, y, w, h, at = 0, rot = -2, treatment = 'none', caption, fix = 'tape'}) => {
  const m = need(id);
  const p = prog(f, at, 12);
  if (p <= 0) return null;
  const border = 18;
  const credit = creditOf(id);
  // 下沿：说明一行 + 署名（按宽度估行数，换行不截断）；图为它让位，整张照片装进 w×h。
  // 文字区宽度不随图缩小而塌（否则署名越换行图越小、图越小署名越窄——样张实测会塌成一条竖缝）：
  // 至少 280，或照片框宽的 70%；照片卡片宽 = max(图宽, 文字区宽)。
  const textW = Math.min(w - border * 2, Math.max(280, (w - border * 2) * 0.7));
  // 说明与署名之间留 20px：卡片是斜贴的（rot），渲染期 OverlapGate 量的是旋转后的外接矩形，
  // 紧贴的两行在 -2° 下外接框会互相压住（cell 演示片 S7 实测「今天的软木切片」压「Giovanna Canu et」被硬拦）
  const CAPTION_GAP = 24;
  const bottom = 14 + (caption ? 40 + CAPTION_GAP : 0) + (credit ? 26 * Math.ceil((credit.length * 10) / textW) : 0);
  const {dw, dh} = fitBox(id, w - border * 2, h - border - bottom);
  const cardW = Math.max(dw, textW) + border * 2;
  const top = y + Math.max(0, (h - (dh + border + bottom)) / 2);
  return <div style={{position: 'absolute', left: x + (w - cardW) / 2, top: top - 30 * (1 - p), width: cardW, boxSizing: 'border-box', opacity: Math.min(1, p * 2.5),
    transform: `rotate(${rot + 2 * (1 - p)}deg)`, background: '#fffdf8', padding: `${border}px ${border}px 0`, boxShadow: `0 ${2 + 12 * (1 - p)}px ${6 + 16 * (1 - p)}px rgba(60,40,15,0.25)`}}>
    <Img src={staticFile(`media/${m.file}`)} style={{display: 'block', width: dw, height: dh, margin: '0 auto', filter: filterOf(treatment)}} />
    <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '6px 0 8px'}}>
      {caption && <div style={{fontFamily: THEME.craft?.handFamily ?? 'Kai', fontWeight: 700, fontSize: 32, lineHeight: 1.2, color: C.ink, whiteSpace: 'nowrap'}}>{caption}</div>}
      {credit && <div style={{fontFamily: 'Space,Kai', fontSize: 20, color: C.ink, lineHeight: 1.25, overflowWrap: 'anywhere', marginTop: caption ? CAPTION_GAP : 0}}>{credit}</div>}
    </div>
    {fix === 'tape' ? <TapeStrip x={cardW / 2 - 70} y={-16} w={140} rot={-4} />
      : <div style={{position: 'absolute', left: cardW / 2 - 13, top: -8, width: 26, height: 26, borderRadius: 13, background: THEME.craft?.accent ?? C.red,
        boxShadow: '2px 5px 4px rgba(0,0,0,0.3), inset -3px -3px 0 rgba(0,0,0,0.2)'}} />}
  </div>;
};

/**
 * 放大镜压在素材上。镜片对准素材上的相对坐标 look（0–1）；inside 版本可以换处理（如 negative → none = 负片在镜里转正）。
 * 素材本身用 ArchivePhoto 的版式（真实比例 + 纸托 + 编目签署名）。
 */
export const LoupeMedia: React.FC<Base & {look: {x: number; y: number}; lensAt: number; r?: number; zoom?: number; lens?: {x: number; y: number};
  insideTreatment?: Treatment; catalogue?: string; title?: string; label?: ArchiveLabel; overlay?: (inside: boolean) => React.ReactNode}> =
  ({f, id, x, y, w, h, at = 0, rot = 0, treatment = 'none', look, lensAt, r = 220, zoom = 2.2, lens, insideTreatment, catalogue, title, label = 'auto', overlay}) => {
    const mount = 22;
    const A = archiveLayout(id, w, h, mount, Boolean(catalogue || title), label, y);
    const {dw, dh, imgX, imgY} = A;
    const ix = x + imgX, iy = y + imgY;
    const tgt = {x: ix + look.x * dw, y: iy + look.y * dh};
    const L = lens ?? tgt;
    // 3.3.0：手柄不许压署名（CC BY 署名必须完整可读）——按编目签的位置选手柄方向
    const slip = {left: x + A.slipX, top: y + A.slipY, right: x + A.slipX + A.slipW, bottom: y + A.slipY + A.slipH};
    const handleAngle = A.slipH > 0 ? pickHandleAngle(L.x, L.y, r, [slip]) : 45;
    return <Loupe f={f} x={L.x} y={L.y} r={r} zoom={zoom} target={tgt} at={lensAt} handleAngle={handleAngle}
      render={(inside) => <>
        <ArchivePhoto f={f} id={id} x={x} y={y} w={w} h={h} at={at} rot={rot} treatment={inside && insideTreatment ? insideTreatment : treatment} catalogue={catalogue} title={title} mount={mount} label={label} />
        {overlay?.(inside)}
      </>} />;
  };

/** 真实声音（kind:audio）。from = 起播帧；volume 线性（缺省 0.5，拟音放在音效阶梯附近）。 */
export const MediaAudio: React.FC<{id: string; from: number; volume?: number; durationInFrames?: number}> = ({id, from, volume = 0.5, durationInFrames}) => {
  const m = need(id);
  if (m.kind !== 'audio') throw new Error(`MediaAudio: ${id} 不是声音素材`);
  const start = Math.round(((m as any).trimStartSec ?? 0) * 30);
  const end = (m as any).trimEndSec != null ? Math.round((m as any).trimEndSec * 30) : undefined;
  return <Sequence from={from} durationInFrames={durationInFrames ?? (end != null ? end - start : undefined)} layout="none">
    <Audio src={staticFile(`media/${m.file}`)} volume={volume} trimBefore={start} trimAfter={end} />
  </Sequence>;
};

export {CRAFT_TYPE};
