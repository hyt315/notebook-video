import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {THEME} from './theme/active';
import {MEDIA} from './media-frame';
import {
  ArchivePhoto, CRAFT_TYPE, CutPaper, HandLettering, HandNote, InkCircle, InkPath, Loupe, LoupeMedia, PaperSheet, PinnedPhoto,
  Seal, Underline, WashBlob, prog,
} from './craft';

// ============================================================================
// craft-sheet · craft 组件样张（Composition: NotebookVideoCraftSheet，3.3.0）
//
// 一页 4×3 = 12 格，把 src/craft/ 的组件全部摆出来，用当前皮肤的纸面与颜色。
// 用途：改 craft 组件 / 换皮肤后**看一眼**——墨线粗细、晕染边缘、剪纸切口、放大镜、署名签是否好看。
//   node scripts/notebook-video.mjs craft-sheet <proj> [OUT.png]     # 第 72 帧（全部落定）
//   node scripts/notebook-video.mjs craft-sheet <proj> OUT.png --frame=18   # 动作进行中
// 真实素材格（PinnedPhoto / ArchivePhoto / LoupeMedia）用 manifests/media.json 里的前两张图；
// 工程里还没有图时画虚线占位并写明怎么加（commons-search.py add）。
// ============================================================================

export const CRAFT_SHEET_FRAMES = 90;
const C = THEME.palette;
const TW = 440, TH = 320, GAP = 20, X0 = 50, Y0 = 40;
const tile = (i: number) => ({x: X0 + (i % 4) * (TW + GAP), y: Y0 + Math.floor(i / 4) * (TH + GAP)});

const Label: React.FC<{i: number; name: string; note: string}> = ({i, name, note}) => {
  const {x, y} = tile(i);
  return <div style={{position: 'absolute', left: x + 18, top: y + TH - 50, fontFamily: 'Kai', fontWeight: 700, fontSize: 32, color: C.ink, whiteSpace: 'nowrap'}}>
    {name}<span style={{fontSize: 24, color: C.muted, marginLeft: 12, fontWeight: 400}}>{note}</span>
  </div>;
};

const Frame: React.FC<{i: number}> = ({i}) => {
  const {x, y} = tile(i);
  return <div style={{position: 'absolute', left: x, top: y, width: TW, height: TH, border: `1.5px dashed ${C.line}`, borderRadius: 6}} />;
};

// 一格「格子纸」：给 Loupe 演示用（镜外是空格子，镜里格子被刷成房间）
const Boxes: React.FC<{x: number; y: number; filled: boolean; f: number}> = ({x, y, filled, f}) => {
  const cells = [];
  for (let r = 0; r < 4; r++) for (let c = 0; c < 6; c++) {
    const cx = x + c * 52 + (r % 2) * 14, cy = y + r * 44;
    cells.push(<div key={`${r}-${c}`} style={{position: 'absolute', left: cx, top: cy, width: 46, height: 38, borderRadius: 7,
      border: `3px solid ${C.ink}`, background: filled ? `rgba(79,125,149,${0.18 + 0.22 * prog(f, 30 + (r + c) * 2, 14)})` : 'transparent'}} />);
  }
  return <>{cells}</>;
};

const Placeholder: React.FC<{i: number; what: string}> = ({i, what}) => {
  const {x, y} = tile(i);
  return <div style={{position: 'absolute', left: x + 40, top: y + 50, width: TW - 80, height: TH - 130, display: 'grid', placeItems: 'center', textAlign: 'center',
    border: `2px dashed ${C.muted}`, fontFamily: 'Kai', fontSize: 26, color: C.muted, lineHeight: 1.3, padding: 12}}>
    {what}<br />commons-search.py add
  </div>;
};

export const CraftSheet: React.FC = () => {
  const f = useCurrentFrame();
  const images = Object.values(MEDIA).filter((m) => m.kind === 'image');
  const plate = images[0]?.id, photo = (images[1] ?? images[0])?.id;
  const t = tile;
  const holes = (cx: number, cy: number) => [0, 1, 2].map((k) => {
    const hx = cx + (k - 1) * 92, r = 26;
    return `M ${hx - r} ${cy} a ${r} ${r} 0 1 0 ${2 * r} 0 a ${r} ${r} 0 1 0 ${-2 * r} 0 Z`;
  }).join(' ');
  return <AbsoluteFill>
    <THEME.Background variant="quiet" />
    {Array.from({length: 12}, (_, i) => <Frame key={i} i={i} />)}

    {/* 0 InkPath：压感墨线，起笔尖、收笔尖 */}
    <InkPath d={`M ${t(0).x + 40} ${t(0).y + 190} C ${t(0).x + 140} ${t(0).y + 70}, ${t(0).x + 260} ${t(0).y + 250}, ${t(0).x + 400} ${t(0).y + 110}`}
      p={prog(f, 4, 30)} size={12} seed="sheet-ink" />
    <InkPath d={`M ${t(0).x + 50} ${t(0).y + 230} L ${t(0).x + 390} ${t(0).y + 215}`} p={prog(f, 20, 20)} size={6} thinning={0.1} seed="sheet-ink2" color={C.blueInk} />
    <Label i={0} name="InkPath" note="压感墨线" />

    {/* 1 Underline + InkCircle */}
    <div style={{position: 'absolute', left: t(1).x + 40, top: t(1).y + 70, fontFamily: 'NotoSerifSC,Kai', fontWeight: 700, fontSize: CRAFT_TYPE.title, color: C.ink, whiteSpace: 'nowrap'}}>小盒子</div>
    <div style={{position: 'absolute', left: t(1).x + 280, top: t(1).y + 70, fontFamily: 'NotoSerifSC,Kai', fontWeight: 700, fontSize: CRAFT_TYPE.title, color: C.ink, whiteSpace: 'nowrap'}}>房间</div>
    <Underline x={t(1).x + 36} y={t(1).y + 166} w={200} p={prog(f, 10, 18)} />
    <InkCircle cx={t(1).x + 344} cy={t(1).y + 112} rx={96} ry={62} p={prog(f, 26, 22)} />
    <Label i={1} name="Underline · InkCircle" note="划线 / 圈注" />

    {/* 2 HandNote：引线长到标本上，再写字 */}
    <WashBlob f={f} at={0} dur={14} cx={t(2).x + 110} cy={t(2).y + 150} rx={64} color={C.green} opacity={0.5} seed="note-spec" />
    <HandNote f={f} at={14} x={t(2).x + 200} y={t(2).y + 56} text="一间小房间" to={{x: t(2).x + 150, y: t(2).y + 140}} />
    <Label i={2} name="HandNote" note="引线 + 钢笔批注" />

    {/* 3 HandLettering：字沿轮廓被写出来 */}
    <HandLettering f={f} at={6} text="细胞" x={t(3).x + 90} y={t(3).y + 40} size={CRAFT_TYPE.hero} perChar={14} />
    <Label i={3} name="HandLettering" note="字形描墨再填墨" />

    {/* 4 PaperSheet：毛边纸 + 撕边纸 + 胶带 */}
    <PaperSheet f={f} at={4} x={t(4).x + 40} y={t(4).y + 50} w={220} h={170} rot={-3} edge="deckle" tape seed="ps1" />
    <PaperSheet f={f} at={14} x={t(4).x + 200} y={t(4).y + 80} w={200} h={150} rot={4} edge="torn" color={C.paperWarm} seed="ps2">
      <div style={{position: 'absolute', left: 24, top: 46, fontFamily: 'Kai', fontWeight: 700, fontSize: 36, color: C.ink, whiteSpace: 'nowrap'}}>撕下一角</div>
    </PaperSheet>
    <Label i={4} name="PaperSheet" note="毛边 / 撕边 / 胶带" />

    {/* 5 WashBlob：三遍叠色，边缘积深 */}
    <WashBlob f={f} at={2} dur={30} cx={t(5).x + 160} cy={t(5).y + 130} rx={110} color={C.blue} opacity={0.45} seed="w1" />
    <WashBlob f={f} at={16} dur={30} cx={t(5).x + 290} cy={t(5).y + 150} rx={90} color={C.orange} opacity={0.38} seed="w2" sweep={1} />
    <Label i={5} name="WashBlob" note="水彩晕开" />

    {/* 6 CutPaper：剪纸，洞即是线，双轮廓 + 背光 */}
    <CutPaper f={f} at={6} id="sheet-cut" inset={9} backlit={0.5}
      d={`M ${t(6).x + 60} ${t(6).y + 50} H ${t(6).x + 380} V ${t(6).y + 230} H ${t(6).x + 60} Z ${holes(t(6).x + 220, t(6).y + 140)}`} />
    <Label i={6} name="CutPaper" note="镂空 · 双轮廓 · 背光" />

    {/* 7 Seal：按下去的一方印 */}
    <Seal f={f} at={20} x={t(7).x + 70} y={t(7).y + 60} size={150} text="胡克" />
    <Seal f={f} at={30} x={t(7).x + 270} y={t(7).y + 80} size={110} text="细" rot={6} />
    <Label i={7} name="Seal" note="三帧按下" />

    {/* 8 Loupe：镜外空格子，镜里被刷成房间 */}
    <Loupe f={f} x={t(8).x + 290} y={t(8).y + 120} r={88} zoom={1.9} target={{x: t(8).x + 150, y: t(8).y + 110}} at={18} handle
      render={(inside) => <Boxes x={t(8).x + 30} y={t(8).y + 40} filled={inside} f={f} />} />
    <Label i={8} name="Loupe" note="镜里换了状态" />

    {/* 9 PinnedPhoto */}
    {photo ? <PinnedPhoto f={f} id={photo} x={t(9).x + 50} y={t(9).y + 24} w={340} h={236} at={8} caption="今天的软木" />
      : <Placeholder i={9} what="PinnedPhoto 需要一张图" />}
    <Label i={9} name="PinnedPhoto" note="贴照 + 署名" />

    {/* 10 ArchivePhoto */}
    {plate ? <ArchivePhoto f={f} id={plate} x={t(10).x + 20} y={t(10).y + 8} w={400} h={232} at={4} catalogue="No.18" title="Schem. XI" mount={12} />
      : <Placeholder i={10} what="ArchivePhoto 需要一张图" />}
    <Label i={10} name="ArchivePhoto" note="纸托 + 编目签" />

    {/* 11 LoupeMedia：负片在镜里转正 */}
    {plate ? <LoupeMedia f={f} id={plate} x={t(11).x + 20} y={t(11).y + 8} w={400} h={240} at={2} treatment="negative" insideTreatment="none"
      look={{x: 0.5, y: 0.45}} lensAt={22} r={66} zoom={2.2} />
      : <Placeholder i={11} what="LoupeMedia 需要一张图" />}
    <Label i={11} name="LoupeMedia" note="负片→镜里转正" />
  </AbsoluteFill>;
};
