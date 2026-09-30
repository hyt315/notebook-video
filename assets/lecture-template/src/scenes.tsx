import React from 'react';
import {Easing, interpolate} from 'remotion';
import {THEME} from './theme/active';
import {CheckBadge, LineIcon, PillTag, TYPE} from './kit';
import {ChatThread, DiffView, FitCard, Funnel, ProgressRing, SkeletonCard, StaggerList, StampSeal, Typewriter} from './fxkit';
import {ShotCamera, CoverPanel} from './shotkit';
import {StageFrame, PhaseRail} from './stagekit';
import {ConsoleWindow, MetricGrid, StampBanner} from './media';
import {Corridor, SplitStage, ZoomStage} from './skeletons';
import {RevealMask} from './insert';
import {Callout, Checklist} from './toolkit';
import {FitTextBox, StatRow, VerdictBar} from './components';
import {SHOTS} from './shots';
import {useCanvas} from './theme/canvas';

// ============================================================================
// Official template example: an 8-shot explainer. Layouts and motion are examples,
// not quotas; use only what serves the topic and its visual explanation.
//
// Treat this as an editable starting point, not a mandatory visual formula.
// Authoring and validation notes: scene-authoring.md, scene-skeletons.md,
// composition-gate.md, and shot-language.md.
//
// Timing guidance:
//   - Bind a visual change to a cue only when the change explains that cue.
//   - Reading/reasoning holds and static diagrams are valid.
//   - Entrance effects are opt-in; do not animate a frame merely to avoid stillness.
//
// Geometry: keep essential content in the safe canvas; moving cameras receive
// additional anchor/bounds checks.
// ============================================================================

const C = THEME.palette;
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const easeOut = (f: number, a: number, b: number, from = 0, to = 1) => interpolate(f, [a, Math.max(a + 1, b)], [from, to], {...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1)});
const easeIO = (f: number, a: number, b: number, from = 0, to = 1) => interpolate(f, [a, Math.max(a + 1, b)], [from, to], {...clamp, easing: Easing.inOut(Easing.cubic)});

const IN = 22;
/** Optional entrance helper: 22-frame easeOut + rise + slight scale. */
const enterAt = (f: number, at: number): React.CSSProperties => {
  const p = easeOut(f, at, at + IN);
  return {opacity: p, transform: `translateY(${(1 - p) * 22}px) scale(${0.975 + 0.025 * p})`};
};
// 原来这里还有一个 exitAt()，本文件从未调用（tsc TS6133）：各镜的离场要么交给
// RevealMask/ShotCamera，要么写成行内表达式，没有一处用得上它。
type Entry = 'none' | 'rise' | 'slide' | 'fade' | 'zoom';
const useEntry = (f: number, entry: Entry) => {
  if (entry === 'none') return {opacity: 1, transform: 'none'};
  const p = easeOut(f, 0, IN);
  const dx = entry === 'slide' ? (1 - p) * 70 : 0;
  const dy = entry === 'rise' ? (1 - p) * 26 : 0;
  const sc = entry === 'zoom' ? 0.965 + 0.035 * p : 1;
  const op = entry === 'fade' ? easeIO(f, 0, IN) : p;
  return {opacity: op, transform: `translateX(${dx}px) translateY(${dy}px) scale(${sc})`};
};

/** Shot wrapper: optional camera/entrance/reveal and a backing panel. */
const Shot: React.FC<{id: keyof typeof SHOTS; f: number; entry?: Entry; reveal?: boolean; children: React.ReactNode}> = ({id, f, entry = 'none', reveal, children}) => {
  const {canvas} = useCanvas();
  const s = SHOTS[id];
  const cover = canvas === '16:9' ? {x: 70, y: 92, w: 1780, h: 846}
    : canvas === '4:3' ? {x: 50, y: 160, w: 1340, h: 760}
    : {x: 40, y: 160, w: 1000, h: 1080};
  const e = useEntry(f, entry);
  // 镜末不淡出：下一镜在精确边界直接替换当前镜，不会产生空帧。
  // 默认 cut 是硬切；只有当前镜明确声明 handoff，FinalDemo 才短暂叠加上一镜末帧。
  const body = (
    <div style={{position: 'absolute', inset: 0, opacity: e.opacity, transform: e.transform}}>
      <CoverPanel
        {...cover} tone="wash" z={-1} pad={0}
        style={{boxShadow: 'none', borderRadius: 0,
                background: `radial-gradient(125% 118% at 50% 50%, ${C.paperBase}F5 58%, ${C.paperBase}D6 82%, ${C.paperBase}00 100%)`}}
      />
      {children}
    </div>
  );
  return <ShotCamera keys={s.keys} f={f} anchor={s.anchor ?? undefined}>{reveal ? <RevealMask f={f} at={0} dur={22}>{body}</RevealMask> : body}</ShotCamera>;
};

const CardHead: React.FC<{icon: Parameters<typeof LineIcon>[0]['kind']; text: string; right?: React.ReactNode}> = ({icon, text, right}) => (
  <div style={{position: 'absolute', left: 34, top: 22, display: 'flex', alignItems: 'center', gap: 12}}>
    <LineIcon kind={icon} size={30} color={C.blue} />
    <span style={{fontSize: TYPE.titleS, fontWeight: 700}}>{text}</span>
    {right}
  </div>
);

// ── S1 · Stage：代码不再孤独（0–213）────────────────────────────────────
const S1Lonely: React.FC<{f: number}> = ({f}) => {
  const {canvas} = useCanvas();
  const wide = canvas === '16:9';
  const fourThree = canvas === '4:3';
  const portrait = canvas === '3:4';
  const frame = wide ? {x: 210, y: 176, w: 1500, h: 710, railW: 380, pad: 26}
    : fourThree ? {x: 60, y: 180, w: 1320, h: 710, railW: 320, pad: 26}
    : {x: 40, y: 180, w: 1000, h: 1030, railW: 0, pad: 24};
  const mainW = wide ? 1000 : fourThree ? 930 : 952;
  const b = SHOTS.S1.beats;
  const at = (i: number, d = 0) => (b[Math.min(i, b.length - 1)] ?? 0) + d;
  const phases = [
    {at: at(0), state: 'local', label: '代码躺在硬盘里'},
    {at: at(1), state: 'push', label: '接上 GitHub'},
    {at: at(2), state: 'world', label: '全世界一起造'},
  ];
  const rows = [
    {text: '$ git remote -v', tone: 'cmd' as const, at: at(0)},
    {text: '(没有远程仓库，只有本地)', tone: 'warn' as const, at: at(0, 22)},
    {text: '$ git push origin main', tone: 'cmd' as const, at: at(1)},
    {text: '✓ 已推送 · 全世界的开发者都能看到', tone: 'ok' as const, at: at(2)},
  ];
  const chips = [
    {k: '仓库', v: 'Repository', c: C.blue, at: at(2, 20)},
    {k: '协作', v: 'Star · Fork · PR', c: C.orange, at: at(2, 38)},
    {k: '结果', v: '一起造软件', c: C.green, at: at(2, 56)},
  ];
  return (
    <Shot id="S1" f={f}>
      <StageFrame
        x={frame.x} y={frame.y} w={frame.w} h={frame.h} f={f} phases={phases} railW={frame.railW} railH={portrait ? 300 : undefined} railPlacement={portrait ? 'bottom' : 'side'} pad={frame.pad}
        header={() => (
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <PillTag text="GITHUB 新手三部曲" color={C.blue} bg={C.blueLight} fontSize={wide ? undefined : 23} />
            <span style={{fontFamily: 'Space,Kai', fontWeight: 700, fontSize: wide ? TYPE.titleS : 31, color: C.ink}}>你写的代码，还躺在硬盘里吗？</span>
          </div>
        )}
        rail={(ctx) => {
          const relation = <div style={{padding: '14px 16px', borderRadius: 12, background: C.paperBase, border: `1.5px solid ${C.line}`, ...enterAt(f, at(1))}}>
            <div style={{fontSize: wide ? 20 : fourThree ? 30 : 24, fontWeight: 700, color: C.muted, marginBottom: wide ? 10 : 8}}>本地 → 远程</div>
            <FitTextBox text={'只有你能看到\n→ 全世界都能参与'} maxLines={2} boxWidth={portrait ? mainW - 32 : frame.railW - 32} maxFontSize={wide ? 20 : portrait ? 30 : fourThree ? 32 : 26} fontWeight={700} color={C.ink} lineHeight={wide ? 1.6 : 1.5} />
          </div>;
          if (portrait) return <div style={{position: 'relative', height: '100%', display: 'flex', flexDirection: 'column', gap: 16}}>
            <PhaseRail phases={phases} ctx={ctx} w={mainW} orientation="horizontal" fontSize={28} dotSize={28} />
            {relation}
          </div>;
          return <div style={{position: 'relative', height: '100%'}}>
            <PhaseRail phases={phases} ctx={ctx} w={wide ? undefined : frame.railW} fontSize={wide ? 21 : fourThree ? 31 : 26} />
            <div style={{position: 'absolute', left: 0, right: 0, bottom: 0}}>{relation}</div>
          </div>;
        }}
        stamp={() => <StampBanner x={0} y={0} w={mainW} f={f} at={at(2, 40)} text="代码不该只躺在硬盘里" color={C.orange} fontSize={wide ? 28 : 32} />}
      >
        {() => (
          <div style={{position: 'relative', height: '100%'}}>
            <ConsoleWindow x={0} y={0} w={mainW} h={280} f={f} title="terminal" rows={rows} rowGap={wide ? 62 : 56} fontSize={wide ? 22 : 27} headerFontSize={wide ? 13 : 17} />
            {/* 圈住症结那一行 + 手写标注：先说"没有远程"，再点破"就是躺在硬盘里"。
                Callout 自带 data-gate-allow，不会被 OverlapGate 判成遮挡物。 */}
            <Callout x={14} y={124} w={296} h={40} frame={f} start={at(0, 44)} text="还躺在硬盘里" textDx={330} textDy={0} color={C.orange} />
            {/* 三张"标签 / 值"卡片 = 指标行的形状，交给封装层 StatRow，不再手写卡片 */}
            <div style={{position: 'absolute', left: 0, top: 352}}>
              <StatRow f={f} startAt={chips[0].at} width={mainW} height={148} gap={14} valueFontSize={wide ? TYPE.displayXS : 38} labelFontSize={wide ? TYPE.labelS : fourThree ? 32 : 28} items={chips.map((x) => ({value: x.v, label: x.k, tone: x.c}))} />
            </div>
          </div>
        )}
      </StageFrame>
    </Shot>
  );
};

// ── S2 · Corridor：入场三步（213–286）──────────────────────────────────
const S2ThreeSteps: React.FC<{f: number}> = ({f}) => {
  const {canvas} = useCanvas();
  const wide = canvas === '16:9';
  const fourThree = canvas === '4:3';
  const b = SHOTS.S2.beats;
  const t0 = b[0] ?? 0;
  const steps = [
    {label: '参与', detail: '做别人的项目', color: C.orangeInk},
    {label: '发布', detail: '整理自己的仓库', color: C.blueInk},
    {label: '运营', detail: '分流 · 审查 · 发版', color: C.greenInk},
  ];
  const stations = steps.map((s, i) => ({...s, at: t0 + i * 24, state: `第 ${i + 1} 步`}));
  const route = wide ? {x: 360, y: 210, w: 1200, h: 460, orientation: 'horizontal' as const, laneY: 84}
    : fourThree ? {x: 170, y: 190, w: 1100, h: 460, orientation: 'horizontal' as const, laneY: 96}
    : {x: 120, y: 190, w: 840, h: 760, orientation: 'vertical' as const, laneY: 96};
  const heading = wide ? {x: 300, y: 690, w: 1320} : fourThree ? {x: 120, y: 610, w: 1200} : {x: 120, y: 1010, w: 840};
  const seal = wide ? {x: 1360, y: 640} : fourThree ? {x: 655, y: 700} : {x: 475, y: 1090};
  return (
    <Shot id="S2" f={f}>
      <Corridor {...route} f={f} from={t0} to={t0 + 52} stations={stations} labelSize={wide ? 28 : fourThree ? 34 : 30} detailSize={wide ? 21 : fourThree ? 32 : 27} stateSize={fourThree ? 30 : undefined} />
      <div style={{position: 'absolute', left: heading.x, top: heading.y, width: heading.w, textAlign: 'center', ...enterAt(f, t0 + 30)}}>
        <div style={{fontSize: wide ? TYPE.titleM : fourThree ? 34 : 32, fontWeight: 700, color: C.muted}}>想入场，其实只要三步</div>
      </div>
      <div style={{position: 'absolute', left: seal.x, top: seal.y, ...enterAt(f, t0 + 48)}}><StampSeal text="三步" x={0} y={0} size={130} frame={f} start={t0 + 48} color={C.orange} /></div>
    </Shot>
  );
};

// ── S3 · Zoom：第一步 · 交出第一个 PR（286–416）────────────────────────
const S3FirstPr: React.FC<{f: number}> = ({f}) => {
  const {canvas} = useCanvas();
  const wide = canvas === '16:9';
  const fourThree = canvas === '4:3';
  const b = SHOTS.S3.beats;
  const at = (i: number, d = 0) => (b[Math.min(i, b.length - 1)] ?? 0) + d;
  const zoom = wide ? {x: 210, y: 200, w: 1000, h: 600, contentW: 944, contentH: 420, diffW: 944}
    : fourThree ? {x: 60, y: 180, w: 820, h: 500, contentW: 760, contentH: 420, diffW: 760}
    : {x: 60, y: 180, w: 960, h: 520, contentW: 900, contentH: 420, diffW: 900};
  const fit = wide ? {x: 1250, y: 240, w: 510, h: 300, listFont: TYPE.bodyM, listGap: 42}
    : fourThree ? {x: 920, y: 166, w: 460, h: 300, listFont: 36, listGap: 50}
    : {x: 60, y: 730, w: 960, h: 275, listFont: 30, listGap: 44};
  const conclusion = wide ? {x: 1250, y: 648, w: 510} : fourThree ? {x: 920, y: 520, w: 460} : {x: 60, y: 1035, w: 960};
  return (
    <Shot id="S3" f={f}>
      <ZoomStage x={zoom.x} y={zoom.y} w={zoom.w} h={zoom.h} f={f} focus={{fx: 0.44, fy: 0.5}} zoom={1.34}
        contentW={zoom.contentW} contentH={zoom.contentH}
        at={{focus: at(1), annotate: at(1) + 30, back: at(1) + 90}} label="第一个 PR 不必大">
        <div style={{position: 'absolute', inset: 0, padding: 26, background: C.paper}}>
          <CardHead icon="branch" text="pull-request.diff" right={<PillTag text="EP 1" color={C.orange} bg={C.orangeLight} />} />
          <div style={enterAt(f, at(0))}>
            <DiffView x={30} y={92} w={zoom.diffW} frame={f} title="docs/typo.patch"
              lines={[
                {k: ' ', text: '#### 安装', at: at(0)},
                {k: '-', text: 'npm i notebook-vido', at: at(0, 24)},
                {k: '+', text: 'npm i notebook-video', at: at(0, 40)},
                {k: ' ', text: '# 只要改对一处拼写，就是一个有效 PR', at: at(1)},
              ]}
            />
          </div>
        </div>
      </ZoomStage>
      {/* 这里原来多传了一个 `f={f}`：FitCard 不认这个 prop（它要的是 frame/start），
          React 会把未知 prop 静默丢掉 —— tsc TS2322 才把它翻出来。 */}
      <FitCard x={fit.x} y={fit.y} w={fit.w} h={fit.h} pad={24} frame={f} borderColor={C.orange} style={enterAt(f, at(1, 10))}>
        <div style={{fontSize: wide ? TYPE.labelL : fourThree ? 34 : 30, fontWeight: 700, color: fourThree ? C.ink : C.muted}}>第一次参与的路径</div>
        {/* 三步路径＝一份清单，交给 Checklist（带序号圆牌），不再手写行 */}
        <Checklist items={['读懂项目规则', '找一个最小改动', '提交并等评审']} start={at(1, 20)} stagger={12} rowH={fit.listGap} fontSize={fit.listFont} frame={f} style={{marginTop: 12}} />
      </FitCard>
      <div style={{position: 'absolute', left: conclusion.x, top: conclusion.y, width: conclusion.w, ...enterAt(f, at(1, 60))}}>
        <Typewriter frame={f} start={at(1, 60)} cps={0.45} text="小改动，也是有效贡献" fontSize={wide ? TYPE.titleXS : fourThree ? 29 : 31} color={C.orange} cursor={false} />
      </div>
    </Shot>
  );
};

// ── S4 · Split：第二步 · 专业的开源仓库（416–532）──────────────────────
const S4ProRepo: React.FC<{f: number}> = ({f}) => {
  const {canvas} = useCanvas();
  const wide = canvas === '16:9';
  const fourThree = canvas === '4:3';
  const b = SHOTS.S4.beats;
  const at = (i: number, d = 0) => (b[Math.min(i, b.length - 1)] ?? 0) + d;
  const split = wide ? {x: 240, y: 196, w: 1440, h: 416}
    : fourThree ? {x: 80, y: 190, w: 1280, h: 390}
    : {x: 60, y: 200, w: 960, h: 470};
  const evidence = wide ? {x: 240, y: 654, w: 880, h: 196, gap: 26, font: 26}
    : fourThree ? {x: 80, y: 620, w: 760, h: 220, gap: 20, font: 32}
    : {x: 60, y: 720, w: 960, h: 190, gap: 28, font: 30};
  const explanations = wide ? {x: 1180, y: 690, w: 520, font: 28, sub: 26}
    : fourThree ? {x: 880, y: 646, w: 480, font: 32, sub: 30}
    : {x: 60, y: 950, w: 960, font: 30, sub: 28};
  return (
    <Shot id="S4" f={f}>
      <SplitStage
        {...split} f={f} winner="right" winnerAt={at(1)} titleSize={wide ? 31 : fourThree ? 31 : 32} subSize={wide ? 30 : fourThree ? 30 : 27} rowSize={wide ? 34 : fourThree ? 34 : 29}
        left={{title: '随手放上去', sub: wide ? '难以理解' : '别人不知道这是什么', rows: ['没有说明文档', '没有许可证', '没有自动化检查'], color: C.muted}}
        right={{title: '专业的开源仓库', sub: wide ? '可信、可用' : '别人愿意用、敢用', rows: ['README 讲清楚', 'LICENSE 讲授权', 'CI 守住质量'], color: C.greenInk}}
      />
      <FitCard x={evidence.x} y={evidence.y} w={evidence.w} h={evidence.h} pad={24} frame={f} borderColor={C.blue} style={enterAt(f, at(1, 20))}>
        <div style={{fontSize: wide ? 28 : fourThree ? 32 : 29, fontWeight: 700, color: C.muted}}>标准三件套</div>
        <div style={{marginTop: 14, display: 'flex', gap: evidence.gap, flexWrap: 'wrap'}}>
          {['README.md', 'LICENSE', 'CI / Actions'].map((t, i) => (
            <div key={t} style={{display: 'flex', alignItems: 'center', gap: 10, fontSize: evidence.font, fontWeight: 700, ...enterAt(f, at(1, 20 + i * 4))}}>
              <CheckBadge size={24} />{t}
            </div>
          ))}
        </div>
      </FitCard>
      <div style={{position: 'absolute', left: explanations.x, top: explanations.y, width: explanations.w}}>
        <StaggerList x={0} y={0} w={explanations.w} frame={f} start={at(1, 32)} stagger={6} fontSize={explanations.font} subFontSize={explanations.sub} items={[
          {text: '让人一眼看懂', sub: 'README', color: C.blueInk},
          {text: '让人放心使用', sub: 'LICENSE', color: C.greenInk},
        ]} />
      </div>
    </Shot>
  );
};

// ── S5 · Stage：第三步 · 运营（532–682）────────────────────────────────
const S5Ops: React.FC<{f: number}> = ({f}) => {
  const {canvas} = useCanvas();
  const wide = canvas === '16:9';
  const fourThree = canvas === '4:3';
  const portrait = canvas === '3:4';
  const b = SHOTS.S5.beats;
  const at = (i: number, d = 0) => (b[Math.min(i, b.length - 1)] ?? 0) + d;
  const phases = [
    {at: at(0), state: 'triage', label: 'Issue 分流'},
    {at: at(1), state: 'review', label: 'PR 审查'},
    {at: at(1, 60), state: 'release', label: '按时发版'},
  ];
  const frame = wide ? {x: 230, y: 176, w: 1460, h: 710, railW: 350, railH: undefined, placement: 'side' as const, pad: 26}
    : fourThree ? {x: 90, y: 180, w: 1260, h: 730, railW: 270, railH: undefined, placement: 'side' as const, pad: 26}
    : {x: 48, y: 180, w: 984, h: 1040, railW: 0, railH: 150, placement: 'top' as const, pad: 26};
  const mainW = wide ? 1040 : fourThree ? 920 : 900;
  const ring = wide ? {y: 372, size: 128, text: TYPE.bodyL, value: 22, label: 13}
    : fourThree ? {y: 350, size: 132, text: 32, value: 28, label: 30}
    : {y: 340, size: 120, text: 30, value: 28, label: 24};
  return (
    <Shot id="S5" f={f}>
      <StageFrame
        x={frame.x} y={frame.y} w={frame.w} h={frame.h} f={f} phases={phases} railW={frame.railW} railH={frame.railH} railPlacement={frame.placement} pad={frame.pad}
        header={() => <span style={{fontFamily: 'Space,Kai', fontWeight: 700, fontSize: wide ? TYPE.titleS : 32}}>第三步 · 学会运营</span>}
        rail={(ctx) => <PhaseRail phases={phases} ctx={ctx} w={portrait ? frame.w - frame.pad * 2 : fourThree ? frame.railW : undefined} orientation={portrait ? 'horizontal' : 'vertical'} fontSize={portrait ? 28 : fourThree ? 32 : 21} dotSize={portrait ? 28 : fourThree ? 26 : 22} />}
        stamp={() => <StampBanner x={0} y={0} w={mainW} f={f} at={at(1, 70)} text="按时发版，仓库才有人气" color={C.green} fontSize={wide ? 28 : 32} />}
      >
        {() => (
          <div style={{position: 'relative', height: '100%'}}>
            <div style={{fontSize: wide ? TYPE.titleXS : 30, fontWeight: 700, color: C.muted, ...enterAt(f, at(0))}}>一个活跃仓库的日常</div>
            <div style={{position: 'absolute', left: 0, top: 52}}>
              <Funnel x={0} y={0} w={mainW} frame={f} start={at(0, 16)} stagger={6} labelSize={wide ? undefined : fourThree ? 36 : 29} subSize={wide ? undefined : fourThree ? 32 : 27} countSize={wide ? undefined : fourThree ? 36 : 32} showDrops={!fourThree} rows={[
                {label: '新 Issue', sub: '需要分流', count: '24', color: C.blueInk, ratio: 1},
                {label: '可复现 / 待办', sub: '进入里程碑', count: '9', color: C.orangeInk, ratio: 0.38},
                {label: '本周已合并', sub: '并发布 v1.1', count: '6', color: C.greenInk, ratio: 0.25},
              ]} />
            </div>
            <div style={{position: 'absolute', left: 0, top: ring.y, display: 'flex', alignItems: 'center', gap: wide ? 28 : 20, ...enterAt(f, at(1, 40))}}>
              <ProgressRing pct={0.86} label="发版进度" color={C.green} start={at(1, 40)} frame={f} size={ring.size} valueSize={ring.value} labelSize={ring.label} />
              <div style={{fontSize: ring.text, fontWeight: 700, color: C.ink, lineHeight: 1.6}}>
                v1.0 → v1.1<br /><span style={{color: C.greenInk}}>按时发布，才有节奏</span>
              </div>
            </div>
          </div>
        )}
      </StageFrame>
    </Shot>
  );
};

// ── S6 · Corridor：三个 AI 技能（682–803）──────────────────────────────
const S6Skills: React.FC<{f: number}> = ({f}) => {
  const {canvas} = useCanvas();
  const wide = canvas === '16:9';
  const fourThree = canvas === '4:3';
  const b = SHOTS.S6.beats;
  const t0 = b[0] ?? 0;
  const skills = [
    {label: 'github-oss-contribute', detail: '参与别人的项目', color: C.orangeInk},
    {label: 'github-oss-prep', detail: '发布自己的作品', color: C.blueInk},
    {label: 'github-oss-ops', detail: '运营与持续发版', color: C.greenInk},
  ];
  const stations = skills.map((s, i) => ({...s, at: t0 + i * 26}));
  const route = wide ? {x: 360, y: 196, w: 1200, h: 460, orientation: 'horizontal' as const, laneY: 84}
    : fourThree ? {x: 400, y: 180, w: 202, h: 520, orientation: 'vertical' as const}
    : {x: 120, y: 190, w: 840, h: 760, orientation: 'vertical' as const, laneY: 96};
  const statement = wide ? {x: 300, y: 676, w: 1320, size: TYPE.titleM} : fourThree ? {x: 120, y: 720, w: 1200, size: 34} : {x: 70, y: 980, w: 940, size: 32};
  const seal = wide ? {x: 1380, y: 620} : fourThree ? {x: 1180, y: 805} : {x: 475, y: 1080};
  return (
    <Shot id="S6" f={f}>
      <Corridor {...route} f={f} from={t0} to={t0 + 56} stations={stations} labelSize={wide ? 22 : fourThree ? 36 : 24} detailSize={wide ? 21 : fourThree ? 34 : 28} labelWidth={fourThree ? 440 : undefined} stateSize={fourThree ? 28 : undefined} />
      <div style={{position: 'absolute', left: statement.x, top: statement.y, width: statement.w, textAlign: 'center', ...enterAt(f, t0 + 30)}}>
        <div style={{fontSize: statement.size, fontWeight: 700, color: C.muted}}>这三步，我做成了三个 AI 技能</div>
      </div>
      <div style={{position: 'absolute', left: seal.x, top: seal.y, ...enterAt(f, t0 + 52)}}><StampSeal text="三个技能" x={0} y={0} size={130} frame={f} start={t0 + 52} color={C.blue} /></div>
    </Shot>
  );
};

// ── S7 · Zoom：让智能体陪你走完（803–919）──────────────────────────────
const S7Agent: React.FC<{f: number}> = ({f}) => {
  const {canvas} = useCanvas();
  const wide = canvas === '16:9';
  const fourThree = canvas === '4:3';
  const b = SHOTS.S7.beats;
  const at = (i: number, d = 0) => (b[Math.min(i, b.length - 1)] ?? 0) + d;
  const zoom = wide ? {x: 210, y: 220, w: 1000, h: 560, contentW: 920, contentH: 340, chatW: 920}
    : fourThree ? {x: 60, y: 180, w: 800, h: 600, contentW: 720, contentH: 420, chatW: 720}
    : {x: 50, y: 180, w: 980, h: 600, contentW: 900, contentH: 420, chatW: 900};
  const helper = wide ? {x: 1250, y: 320, w: 510, h: 200, title: TYPE.titleXS, detail: TYPE.labelL}
    : fourThree ? {x: 900, y: 350, w: 480, h: 210, title: 30, detail: 26}
    : {x: 50, y: 800, w: 980, h: 210, title: 32, detail: 28};
  return (
    <Shot id="S7" f={f}>
      <ZoomStage x={zoom.x} y={zoom.y} w={zoom.w} h={zoom.h} f={f} focus={{fx: 0.5, fy: 0.5}} zoom={1.24}
        contentW={zoom.contentW} contentH={zoom.contentH}
        at={{focus: at(0), annotate: at(0) + 40, back: at(0) + 96}} label="让智能体陪你走完全程">
        <div style={{position: 'absolute', inset: 0, padding: 30, background: C.paper}}>
          <CardHead icon="user" text="与智能体协作" />
          <div style={{position: 'absolute', left: 30, top: 92}}>
            <ChatThread x={0} y={0} w={zoom.chatW} frame={f} fontSize={wide ? TYPE.labelL : fourThree ? 28 : 30} msgs={[
              {side: 'l', text: '我想给这个项目提一个 PR', at: at(0)},
              {side: 'r', text: '先读贡献指南，再找最小改动', at: at(0, 26)},
              {side: 'l', text: '改好了，帮我检查一遍', at: at(0, 56)},
            ]} />
          </div>
        </div>
      </ZoomStage>
      <div style={{position: 'absolute', left: helper.x, top: helper.y, width: helper.w}}>
        <SkeletonCard x={0} y={0} w={helper.w} h={helper.h} frame={f} start={at(0, 20)} revealAt={at(0, 80)} rows={2}>
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <CheckBadge size={28} />
            <div>
              <div style={{fontSize: helper.title, fontWeight: 700}}>全程有人带</div>
              <div style={{fontSize: helper.detail, fontWeight: 700, color: C.muted, marginTop: 8}}>读规则 · 改代码 · 走流程</div>
            </div>
          </div>
        </SkeletonCard>
      </div>
    </Shot>
  );
};

// ── S8 · Stage：三期视频，一期一步（919–1150）──────────────────────────
const S8Series: React.FC<{f: number}> = ({f}) => {
  const {canvas} = useCanvas();
  const wide = canvas === '16:9';
  const fourThree = canvas === '4:3';
  const b = SHOTS.S8.beats;
  const at = (i: number, d = 0) => (b[Math.min(i, b.length - 1)] ?? 0) + d;
  const phases = [
    {at: at(0), state: 'ep1', label: '第一期 · 参与'},
    {at: at(1), state: 'ep2', label: '第二期 · 发布'},
    {at: at(2), state: 'ep3', label: '第三期 · 运营'},
  ];
  const frame = wide ? {x: 260, y: 190, w: 1400, h: 700, pad: 26}
    : fourThree ? {x: 60, y: 180, w: 1320, h: 730, pad: 26}
    : {x: 50, y: 180, w: 980, h: 1040, pad: 26};
  const contentW = frame.w - frame.pad * 2;
  const cols = wide || fourThree ? 3 : 1;
  const cellH = wide ? 200 : 184;
  const verdictTop = wide ? 372 : fourThree ? 360 : 650;
  const textSize = wide ? {title: 24, label: 22, before: 30, after: 38, verdict: TYPE.titleXS, tag: TYPE.microL}
    : fourThree ? {title: 32, label: 30, before: 34, after: 42, verdict: 30, tag: 24}
    : {title: 34, label: 32, before: 36, after: 44, verdict: 32, tag: 26};
  return (
    <Shot id="S8" f={f}>
      <StageFrame
        x={frame.x} y={frame.y} w={frame.w} h={frame.h} f={f} phases={phases} pad={frame.pad}
        header={() => <span style={{fontFamily: 'Space,Kai', fontWeight: 700, fontSize: wide ? TYPE.titleS : 32}}>三期视频，一期一步</span>}
        stamp={() => <StampBanner x={0} y={0} w={contentW} f={f} at={at(2, 20)} text="主页搜 hyt315，现在出发" color={C.orange} fontSize={wide ? 28 : 32} />}
      >
        {() => (
          <div style={{position: 'relative', height: '100%'}}>
            <MetricGrid x={0} y={0} w={contentW} f={f} cols={cols} cellH={cellH} start={at(0, 10)} stagger={6} title="三期视频，一期一步" titleFontSize={textSize.title} labelFontSize={textSize.label} beforeFontSize={textSize.before} afterFontSize={textSize.after}
              items={[
                {label: 'EP 1 · 参与', before: '不会', after: '会提 PR', win: true, color: C.orangeInk},
                {label: 'EP 2 · 发布', before: '本地项目', after: '专业仓库', win: true, color: C.blueInk},
                {label: 'EP 3 · 运营', before: '无人问津', after: '持续发版', win: true, color: C.greenInk},
              ]}
            />
            {/* 收尾改用全宽结论条，比一行内联文字更有收束感 */}
            <div style={{position: 'absolute', left: 0, top: verdictTop}}>
              <VerdictBar f={f} delay={at(2, 40)} tone={C.orange} tag="出发" width={contentW} fontSize={textSize.verdict} tagFontSize={textSize.tag} text="三个技能已开源，让智能体陪你走完全程" />
            </div>
          </div>
        )}
      </StageFrame>
    </Shot>
  );
};

/** 场景注册表：由 index.tsx 按 SHOTS 的区间挂载（只挂活动场景）。 */
export const SCENES: Record<keyof typeof SHOTS, React.FC<{f: number}>> = {
  S1: S1Lonely,
  S2: S2ThreeSteps,
  S3: S3FirstPr,
  S4: S4ProRepo,
  S5: S5Ops,
  S6: S6Skills,
  S7: S7Agent,
  S8: S8Series,
};

export const SCENES_VERSION = 'template-scenes-v1 · 8 shots · 4 skeletons · cue-bound entrances';
