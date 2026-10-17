import React from 'react';
import {Easing, interpolate} from 'remotion';
import {THEME} from './theme/active';
import {LineIcon, PillTag, TYPE} from './kit';
import {DiffView, FitCard} from './fxkit';
import {ShotCamera} from './shotkit';
import {ConsoleWindow, MetricGrid} from './media';
import {Corridor, SplitStage, ZoomStage} from './skeletons';
import {RevealMask} from './insert';
import {Checklist} from './toolkit';
import {Chart, HighlightCode, IconWall, MorphShape, SHAPES, StatRow, TreeView, VerdictBar} from './components';
import {SHOTS} from './shots';

// ============================================================================
// v4.3 组件演示片 ·「一行缓存，五倍速度」（7 镜 / 约 60 秒）
// 展示：Shiki 代码高亮、jsdiff 补丁、visx 图表、lucide/simple-icons 图标墙、
//       flubber 形状变形、d3-hierarchy 结构树、Corridor/Split/Zoom 骨架、章节背景、语义音效。
// 内容区 [160,1760] × [130,860]：卡片底边不越过 860，避开背景下方两角的角色。
// ============================================================================

const C = THEME.palette;
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const easeOut = (f: number, a: number, b: number) => interpolate(f, [a, Math.max(a + 1, b)], [0, 1], {...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1)});
const IN = 22;
const enterAt = (f: number, at: number): React.CSSProperties => {
  const p = easeOut(f, at, at + IN);
  return {opacity: p, transform: `translateY(${(1 - p) * 22}px) scale(${0.975 + 0.025 * p})`};
};
type Entry = 'rise' | 'slide' | 'fade' | 'zoom';
const Shot: React.FC<{id: keyof typeof SHOTS; f: number; entry: Entry; reveal?: boolean; children: React.ReactNode}> = ({id, f, entry, reveal, children}) => {
  const s = SHOTS[id];
  const p = easeOut(f, 0, IN);
  const tr = entry === 'slide' ? `translateX(${(1 - p) * 70}px)` : entry === 'rise' ? `translateY(${(1 - p) * 26}px)` : entry === 'zoom' ? `scale(${0.965 + 0.035 * p})` : 'none';
  const body = <div style={{position: 'absolute', inset: 0, opacity: p, transform: tr}}>{children}</div>;
  return <ShotCamera keys={s.keys} f={f} anchor={s.anchor}>{reveal ? <RevealMask f={f} at={0} dur={22}>{body}</RevealMask> : body}</ShotCamera>;
};
const beatAt = (id: keyof typeof SHOTS) => (i: number, d = 0) => {
  const b = SHOTS[id].beats as readonly number[];
  return (b[Math.min(i, b.length - 1)] ?? 0) + d;
};
const Title: React.FC<{f: number; at: number; text: string; sub?: string; x?: number; y?: number}> = ({f, at, text, sub, x = 200, y = 196}) => (
  <div style={{position: 'absolute', left: x, top: y, ...enterAt(f, at)}}>
    <div style={{fontSize: TYPE.titleM, fontWeight: 700, color: C.ink}}>{text}</div>
    {sub && <div style={{fontSize: TYPE.bodyM, color: C.muted, marginTop: 6}}>{sub}</div>}
  </div>
);

// ── S1 · 慢在哪里：控制台 + 技术栈图标墙 ─────────────────────────────
const S1: React.FC<{f: number}> = ({f}) => {
  const at = beatAt('S1');
  return (
    <Shot id="S1" f={f} entry="rise">
      <Title f={f} at={at(0)} text="一个接口，平均 1.2 秒" sub="GET /api/report · 生产环境实测" />
      <ConsoleWindow x={200} y={300} w={820} f={f} start={at(0, 10)} title="curl · /api/report" status={{text: '1.21 s', tone: 'warn'}}
        rows={[
          {text: 'curl -w "%{time_total}" /api/report', tone: 'cmd'},
          {text: '200 OK · 48 KB', tone: 'out'},
          {text: 'time_total: 1.214 s', tone: 'warn'},
          {text: 'p95: 2.03 s · 用户在等', tone: 'warn'},
        ]} />
      <div style={{position: 'absolute', left: 1090, top: 300, ...enterAt(f, at(0, 30))}}>
        <div style={{fontSize: TYPE.labelL, fontWeight: 700, color: C.muted, marginBottom: 14}}>技术栈</div>
        <IconWall f={f} startAt={at(0, 36)} step={5} names={['python', 'database', 'server', 'docker', 'git', 'cloud']} columns={3} tile={170} gap={18} />
      </div>
    </Shot>
  );
};

// ── S2 · 画出耗时：柱状图 + 指标行 ─────────────────────────────────
const S2: React.FC<{f: number}> = ({f}) => {
  const at = beatAt('S2');
  return (
    <Shot id="S2" f={f} entry="fade">
      <Title f={f} at={at(0)} text="先别怪数据库" sub="把每个接口的耗时画出来" />
      <div style={{position: 'absolute', left: 200, top: 290, ...enterAt(f, at(1))}}>
        <Chart f={f} startAt={at(1, 4)} width={980} height={540} title="各接口平均耗时（毫秒）" unit="ms"
          data={[{label: '/login', value: 80}, {label: '/list', value: 140}, {label: '/report', value: 1210}, {label: '/search', value: 190}]} />
      </div>
      <div style={{position: 'absolute', left: 1230, top: 300, ...enterAt(f, at(2))}}>
        <StatRow f={f} startAt={at(2, 4)} width={470} height={150} items={[
          {value: 1, label: '慢接口', tone: C.orange},
          {value: 92, suffix: '%', label: '耗时占比', tone: C.blue},
        ]} />
        <FitCard x={0} y={190} w={470} h={200} pad={24} frame={f} borderColor={C.orange} style={enterAt(f, at(2, 20))}>
          <div style={{fontSize: TYPE.labelL, fontWeight: 700, color: C.orangeInk}}>慢的只有一个</div>
          <div style={{fontSize: TYPE.bodyM, color: C.ink, marginTop: 10, lineHeight: 1.5}}>/report 每次都重新聚合整张表</div>
        </FitCard>
      </div>
    </Shot>
  );
};

// ── S3 · 改一行代码：Shiki 代码高亮 ────────────────────────────────
const S3: React.FC<{f: number}> = ({f}) => {
  const at = beatAt('S3');
  return (
    <Shot id="S3" f={f} entry="rise">
      <div style={{position: 'absolute', left: 200, top: 210, ...enterAt(f, at(0))}}>
        <HighlightCode f={f} startAt={at(0, 6)} lineStep={14} width={1000} height={600} language="python" title="report.py"
          code={'from functools import lru_cache\n\n@lru_cache(maxsize=256)\ndef build_report(day: str) -> dict:\n    rows = db.query(SQL_REPORT, day)\n    return aggregate(rows)\n\ndef handler(req):\n    return build_report(req.day)'} />
      </div>
      <FitCard x={1260} y={210} w={460} h={250} pad={26} frame={f} borderColor={C.blue} style={enterAt(f, at(1))}>
        <div style={{display: 'flex', alignItems: 'center', gap: 10}}><LineIcon kind="rocket" size={28} color={C.blue} /><span style={{fontSize: TYPE.labelL, fontWeight: 700}}>缓存装饰器</span></div>
        <div style={{fontSize: TYPE.bodyM, color: C.ink, marginTop: 14, lineHeight: 1.5}}>同一天的报表只算一次，之后直接复用结果</div>
      </FitCard>
      <div style={{position: 'absolute', left: 1260, top: 500, ...enterAt(f, at(2))}}>
        <PillTag text="@lru_cache · 标准库自带" color={C.green} bg={C.greenLight} />
      </div>
    </Shot>
  );
};

// ── S4 · 三行 diff：Zoom + jsdiff ───────────────────────────────────
const S4: React.FC<{f: number}> = ({f}) => {
  const at = beatAt('S4');
  return (
    <Shot id="S4" f={f} entry="zoom" reveal>
      <ZoomStage x={200} y={180} w={1000} h={620} f={f} focus={{fx: 0.42, fy: 0.45}} zoom={1.3} contentW={860} contentH={460}
        at={{focus: at(1), annotate: at(1) + 26, back: at(2) + 40}} label="改动只有三行">
        <div style={{position: 'absolute', inset: 0, padding: 26, background: C.paper}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 12, ...enterAt(f, at(0))}}>
            <LineIcon kind="branch" size={30} color={C.blue} /><span style={{fontSize: TYPE.titleS, fontWeight: 700}}>add-cache.diff</span>
          </div>
          <div style={enterAt(f, at(0, 6))}>
            <DiffView x={0} y={30} w={800} frame={f} title="report.py" startAt={at(0, 14)} step={12}
              before={'def handler(req):\n    rows = db.query(SQL_REPORT, req.day)\n    return aggregate(rows)'}
              after={'@lru_cache(maxsize=256)\ndef build_report(day):\n    return aggregate(db.query(SQL_REPORT, day))\n\ndef handler(req):\n    return build_report(req.day)'} />
          </div>
        </div>
      </ZoomStage>
      <FitCard x={1250} y={220} w={470} h={300} pad={24} frame={f} borderColor={C.green} style={enterAt(f, at(1, 6))}>
        <div style={{fontSize: TYPE.labelL, fontWeight: 700, color: C.muted}}>合并前检查</div>
        <Checklist items={['单元测试通过', '缓存键只含日期', '设置容量上限']} start={at(1, 20)} stagger={14} rowH={44} fontSize={TYPE.bodyM} frame={f} style={{marginTop: 12}} />
      </FitCard>
    </Shot>
  );
};

// ── S5 · 结构怎么变：flubber 形状变形 + 结构树 ─────────────────────
const S5: React.FC<{f: number}> = ({f}) => {
  const at = beatAt('S5');
  const from = SHAPES.circle(150);
  const to = SHAPES.star(70, 150);
  return (
    <Shot id="S5" f={f} entry="rise">
      <Title f={f} at={at(0)} text="以前 vs 现在" sub="请求在哪一层被接住" />
      <div style={{position: 'absolute', left: 200, top: 300, width: 560, height: 520, ...enterAt(f, at(0, 8))}}>
        <div style={{position: 'absolute', left: 0, top: 0, width: 560, height: 520, background: C.paper, border: `2.5px solid ${C.line}`, borderRadius: 14}} />
        <div style={{position: 'absolute', left: 80, top: 30}}>
          <MorphShape f={f} fromPath={from.path} toPath={to.path} startAt={at(1)} durationInFrames={40} width={400} height={380}
            viewBox={`-20 -20 ${from.width + 40} ${from.height + 40}`} tone={C.orange} fill={`${C.orange}22`} />
        </div>
        <div style={{position: 'absolute', left: 0, top: 440, width: 560, textAlign: 'center', fontSize: TYPE.labelL, fontWeight: 700, color: f < at(1) + 20 ? C.muted : C.orangeInk}}>
          {f < at(1) + 20 ? '每次都查库' : '命中缓存，直接返回'}
        </div>
      </div>
      <div style={{position: 'absolute', left: 820, top: 300, width: 900, height: 520, background: C.paper, border: `2.5px solid ${C.line}`, borderRadius: 14, padding: 24, ...enterAt(f, at(0, 24))}}>
        <div style={{fontSize: TYPE.labelL, fontWeight: 700, color: C.muted, marginBottom: 10}}>服务结构</div>
        <TreeView f={f} startAt={at(0, 30)} width={840} height={420} nodeW={150} nodeH={40}
          data={{name: 'API 服务', children: [
            {name: '缓存层', children: [{name: '命中 80%'}, {name: '未命中'}]},
            {name: '数据库', children: [{name: '只处理未命中'}]},
          ]}} />
      </div>
    </Shot>
  );
};

// ── S6 · 三站链路：Corridor 骨架 ───────────────────────────────────
const S6: React.FC<{f: number}> = ({f}) => {
  const at = beatAt('S6');
  const t0 = at(0, 8);
  return (
    <Shot id="S6" f={f} entry="rise">
      <Title f={f} at={at(0)} text="整条链路：三站" x={360} y={196} />
      <Corridor x={360} y={300} w={1200} f={f} laneY={84} from={t0} to={t0 + 60}
        stations={[
          {at: t0, label: '请求', state: '进入', color: C.blue},
          {at: t0 + 30, label: '缓存', state: '命中即返回', color: C.green},
          {at: t0 + 60, label: '数据库', state: '仅未命中', color: C.orange},
        ]} />
      <div style={{position: 'absolute', left: 360, top: 610, width: 1200, ...enterAt(f, at(1))}}>
        <SplitStage x={0} y={0} w={1200} h={170} f={f}
          left={{title: '缓存命中', rows: ['约 3 ms 返回']}}
          right={{title: '缓存未命中', rows: ['回源查库，再写入缓存']}}
          winner="left" winnerAt={at(2)} />
      </div>
    </Shot>
  );
};

// ── S7 · 结果：前后对比图 + 指标 + 结论条 ──────────────────────────
const S7: React.FC<{f: number}> = ({f}) => {
  const at = beatAt('S7');
  return (
    <Shot id="S7" f={f} entry="fade">
      <Title f={f} at={at(0)} text="上线一周" sub="平均耗时 · 数据库负载" />
      <div style={{position: 'absolute', left: 200, top: 290, ...enterAt(f, at(0, 8))}}>
        <Chart f={f} variant="area" startAt={at(0, 12)} width={860} height={420} title="平均耗时（毫秒）" unit="ms"
          data={[{label: '周一', value: 1210}, {label: '周二', value: 620}, {label: '周三', value: 310}, {label: '周四', value: 260}, {label: '周五', value: 240}]} />
      </div>
      <div style={{position: 'absolute', left: 1110, top: 290}}>
        <MetricGrid x={0} y={0} w={610} f={f} cols={2} cellH={230} start={at(1)} stagger={10}
          items={[
            {label: '平均耗时', before: '1.21s', after: '0.24s', win: true, color: C.greenInk},
            {label: '数据库负载', before: '100%', after: '30%', win: true, color: C.blueInk},
          ]} />
      </div>
      <div style={{position: 'absolute', left: 200, top: 750}}>
        <VerdictBar f={f} delay={at(2)} tone={C.orange} tag="结论" width={1520} text="一行缓存，五倍速度" />
      </div>
    </Shot>
  );
};

export const SCENES: Record<keyof typeof SHOTS, React.FC<{f: number}>> = {S1, S2, S3, S4, S5, S6, S7};
export const SCENES_VERSION = 'demo-scenes-v4.3 · 7 shots · cache 5x';
