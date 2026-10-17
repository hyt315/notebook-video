import React from 'react';
import {Easing, interpolate} from 'remotion';
import {THEME} from './theme/active';
import {LineIcon, PillTag, TYPE} from './kit';
import {DiffView, FitCard, ProgressRing} from './fxkit';
import {ShotCamera} from './shotkit';
import {ConsoleWindow} from './media';
import {Corridor, SplitStage} from './skeletons';
import {RevealMask} from './insert';
import {KineticNumber, popIn} from './cinema';
import {Chart, HighlightCode, StatRow, TreeView, VerdictBar} from './components';
import {SHOTS} from './shots';

// ============================================================================
// v4.4 演示片 ·「一行缓存，五倍速度」（8 镜 / 60 秒 / 4 章）
// 这一版要证明的是「不像 PPT」：
//   · 引擎虚拟镜头：每镜默认缓推；分镜表 cinema.focus 讲到哪推到哪（S1 控制台、S2 慢柱、S3 两行代码、
//     S4 新增行、S5 缓存站 → 数据库站的横摇、S7 曲线 → 指标）；镜间 whip 甩镜 / 章节首镜 zoom 推穿；背景视差。
//   · 内容大：代码 36px、补丁 28px、关键数字 260–380px；每镜 anchor 占安全区 60–80%。
//   · 相邻镜头布局全不同：hero-number / chart-number / code-full / diff-split / rail / ring-tree / chart-metric / hero-verdict。
//   · 关键数字做动态排版（KineticNumber：计数 + 落定弹出 + 下划线扫入）。
// 内容区 [160,1760] × [180,870]：底边不越过 870，避开背景下方两角的角色与字幕条。
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
const Heading: React.FC<{f: number; at: number; text: string; sub?: string; x?: number; y?: number; size?: number}> = ({f, at, text, sub, x = 200, y = 200, size = 56}) => (
  <div style={{position: 'absolute', left: x, top: y, ...enterAt(f, at)}}>
    <div style={{fontSize: size, fontWeight: 700, color: C.ink, lineHeight: 1.1}}>{text}</div>
    {sub && <div style={{fontSize: TYPE.titleS, color: C.muted, marginTop: 10}}>{sub}</div>}
  </div>
);

// ── S1 · hero-number：一个巨大的「1.2 秒」+ 右侧控制台（镜头在第二句推近控制台）──────────
const S1: React.FC<{f: number}> = ({f}) => {
  const at = beatAt('S1');
  return (
    <Shot id="S1" f={f} entry="rise">
      <div style={{position: 'absolute', left: 200, top: 236, ...enterAt(f, at(0))}}>
        <PillTag text="GET /api/report" color={C.blue} bg={C.blueLight} fontSize={TYPE.titleS} />
      </div>
      <div style={{position: 'absolute', left: 200, top: 320}}>
        <KineticNumber f={f} at={at(0, 8)} to={1.2} decimals={1} dur={34} suffix="秒" size={300} color={C.orange} ink={C.ink} label="每次请求的平均等待" labelSize={44} />
      </div>
      <ConsoleWindow x={1000} y={250} w={720} f={f} start={at(0, 26)} rowGap={40} fontSize={30} title="curl · /api/report" status={{text: '1.21 s', tone: 'warn'}}
        rows={[
          {text: 'curl -w "%{time_total}" /api/report', tone: 'cmd'},
          {text: '200 OK · 48 KB', tone: 'out'},
          {text: 'time_total: 1.214 s', tone: 'warn'},
          {text: 'p95: 2.03 s · 用户在等', tone: 'warn'},
        ]} />
      <div style={{position: 'absolute', left: 1000, top: 650, display: 'flex', gap: 16, ...enterAt(f, at(2))}}>
        <PillTag text="每次点击 → 转圈 1.2 秒" color={C.orangeInk} bg={C.orangeLight} fontSize={TYPE.titleS} />
      </div>
    </Shot>
  );
};

// ── S2 · chart-number：整幅柱状图 + 右侧「92%」（镜头在第二拍推近那根慢柱）──────────────
const S2: React.FC<{f: number}> = ({f}) => {
  const at = beatAt('S2');
  return (
    <Shot id="S2" f={f} entry="fade">
      <Heading f={f} at={at(0)} text="先别怪数据库" sub="把每个接口的耗时画出来" y={196} />
      <div style={{position: 'absolute', left: 200, top: 340, ...enterAt(f, at(1))}}>
        <Chart f={f} variant="bar" highlight={2} startAt={at(1, 2)} width={1080} height={500} title="各接口平均耗时（毫秒）" unit="ms"
          data={[{label: '/login', value: 80}, {label: '/list', value: 140}, {label: '/report', value: 1210}, {label: '/search', value: 190}]} />
      </div>
      <div style={{position: 'absolute', left: 1360, top: 380, ...enterAt(f, at(2))}}>
        <StatRow f={f} startAt={at(2, 4)} width={360} height={220} items={[{value: 92, suffix: '%', label: '耗时在 /report', tone: C.orange}]} />
      </div>
      <div style={{position: 'absolute', left: 1360, top: 700, ...enterAt(f, at(2, 30))}}>
        <PillTag text="慢的只有一个" color={C.orangeInk} bg={C.orangeLight} fontSize={TYPE.titleM} />
      </div>
    </Shot>
  );
};

// ── S3 · code-full：36px 大代码，高亮钉在讲到的那一行，镜头先推到「查库」再推到「装饰器」──────
const CODE = 'from functools import lru_cache\n\n@lru_cache(maxsize=256)\ndef build_report(day: str) -> dict:\n    rows = db.query(SQL_REPORT, day)\n    return aggregate(rows)';
const S3: React.FC<{f: number}> = ({f}) => {
  const at = beatAt('S3');
  const active = f < at(2) ? 4 : 2;
  return (
    <Shot id="S3" f={f} entry="rise">
      <div style={{position: 'absolute', left: 200, top: 200, ...enterAt(f, at(0))}}>
        <HighlightCode f={f} startAt={at(0)} lineStep={20} active={f < at(1) ? undefined : active} width={1080} height={600} fontSize={36} language="python" title="report.py" code={CODE} />
      </div>
      <FitCard x={1330} y={230} w={390} h={250} pad={28} frame={f} borderColor={f < at(2) ? C.orange : C.blue} style={enterAt(f, at(1))}>
        <div style={{display: 'flex', alignItems: 'center', gap: 12}}><LineIcon kind={f < at(2) ? 'bug' : 'rocket'} size={36} color={f < at(2) ? C.orange : C.blue} /><span style={{fontSize: TYPE.titleL, fontWeight: 700}}>{f < at(2) ? '每次都查库' : '缓存装饰器'}</span></div>
        <div style={{fontSize: TYPE.bodyL, color: C.ink, marginTop: 16, lineHeight: 1.5}}>{f < at(2) ? '同一天的报表，每次请求都重算' : '同一天只算一次，之后直接复用'}</div>
      </FitCard>
      <div style={{position: 'absolute', left: 1330, top: 540, ...enterAt(f, at(3))}}>
        <PillTag text="@lru_cache · 标准库" color={C.green} bg={C.greenLight} fontSize={TYPE.titleS} />
      </div>
    </Shot>
  );
};

// ── S4 · diff-split：28px 大补丁 + 右侧巨大的「3 行」（镜头在第二句推近新增行）──────────────
const S4: React.FC<{f: number}> = ({f}) => {
  const at = beatAt('S4');
  return (
    <Shot id="S4" f={f} entry="zoom" reveal>
      <div style={enterAt(f, at(0))}>
        <DiffView x={200} y={220} w={1060} frame={f} title="add-cache.diff" startAt={at(0, 10)} step={10} fontSize={28}
          before={'def handler(req):\n    rows = db.query(SQL_REPORT, req.day)\n    return aggregate(rows)'}
          after={'@lru_cache(maxsize=256)\ndef build_report(day):\n    return aggregate(db.query(SQL_REPORT, day))\n\ndef handler(req):\n    return build_report(req.day)'} />
      </div>
      <div style={{position: 'absolute', left: 1360, top: 250}}>
        <KineticNumber f={f} at={at(1)} to={3} dur={20} suffix="行" size={280} color={C.green} ink={C.ink} label="真正的改动" labelSize={42} />
      </div>
      <div style={{position: 'absolute', left: 1360, top: 640, ...enterAt(f, at(2, 10))}}>
        <PillTag text="旧调用 → 缓存版本" color={C.blueInk} bg={C.blueLight} fontSize={TYPE.titleS} />
      </div>
    </Shot>
  );
};

// ── S5 · rail：三站链路（镜头从「缓存」横摇到「数据库」）──────────────────────────────
const S5: React.FC<{f: number}> = ({f}) => {
  const at = beatAt('S5');
  const t0 = at(0, 10);
  return (
    <Shot id="S5" f={f} entry="slide">
      <Heading f={f} at={at(0)} text="整条链路：三站" x={240} y={210} />
      <Corridor x={240} y={320} w={1440} f={f} laneY={96} from={t0} to={at(2, 20)}
        stations={[
          {at: t0, label: '请求', state: '进入', color: C.blue},
          {at: at(1), label: '缓存', state: '命中即返回', color: C.green},
          {at: at(2), label: '数据库', state: '仅未命中', color: C.orange},
        ]} />
      <div style={{position: 'absolute', left: 240, top: 630, width: 1440, ...enterAt(f, at(1, 20))}}>
        <SplitStage x={0} y={0} w={1440} h={190} f={f}
          left={{title: '缓存命中', rows: ['约 3 ms 返回']}}
          right={{title: '缓存未命中', rows: ['回源查库，再写入缓存']}}
          winner="left" winnerAt={at(2, 30)} />
      </div>
    </Shot>
  );
};

// ── S6 · ring-tree：巨大的 80% 进度环 + 结构树 ──────────────────────────────────────────
const S6: React.FC<{f: number}> = ({f}) => {
  const at = beatAt('S6');
  return (
    <Shot id="S6" f={f} entry="fade">
      <div style={{position: 'absolute', left: 230, top: 250, width: 560, display: 'flex', flexDirection: 'column', alignItems: 'center', ...popIn(f, at(0), {from: 'scale'})}}>
        <ProgressRing size={420} pct={0.8} label="命中率" color={C.green} start={at(0, 6)} duration={40} frame={f} />
        <div style={{marginTop: 20, fontSize: 44, fontWeight: 700, color: C.ink}}>缓存命中率</div>
      </div>
      <div style={{position: 'absolute', left: 880, top: 230, width: 840, height: 560, background: C.paper, border: `2.5px solid ${C.line}`, borderRadius: 16, padding: 26, ...popIn(f, at(1), {from: 'right'})}}>
        <div style={{fontSize: TYPE.titleS, fontWeight: 700, color: C.muted, marginBottom: 12}}>请求在哪一层被接住</div>
        <TreeView f={f} startAt={at(1, 6)} width={780} height={460} nodeW={190} nodeH={52} step={10}
          data={{name: 'API 服务', children: [
            {name: '缓存层', children: [{name: '命中 80%'}, {name: '未命中 20%'}]},
            {name: '数据库', children: [{name: '只处理未命中'}]},
          ]}} />
      </div>
    </Shot>
  );
};

// ── S7 · chart-metric：一周曲线 + 两个倒数的关键数字（镜头先看曲线，再推到指标）──────────────────
const S7: React.FC<{f: number}> = ({f}) => {
  const at = beatAt('S7');
  return (
    <Shot id="S7" f={f} entry="rise">
      <Heading f={f} at={at(0)} text="上线一周" sub="平均耗时 · 数据库负载" y={196} />
      <div style={{position: 'absolute', left: 200, top: 350, ...enterAt(f, at(0, 8))}}>
        <Chart f={f} variant="area" startAt={at(0, 12)} width={900} height={480} title="平均耗时（毫秒）" unit="ms"
          data={[{label: '周一', value: 1210}, {label: '周二', value: 620}, {label: '周三', value: 310}, {label: '周四', value: 260}, {label: '周五', value: 240}]} />
      </div>
      <div style={{position: 'absolute', left: 1180, top: 290}}>
        <KineticNumber f={f} at={at(1)} from={1.21} to={0.24} decimals={2} dur={36} suffix="秒" size={170} color={C.green} ink={C.ink} label="平均耗时 · 原 1.21 秒" labelSize={34} />
      </div>
      <div style={{position: 'absolute', left: 1180, top: 580}}>
        <KineticNumber f={f} at={at(2)} from={100} to={30} dur={30} suffix="%" size={170} color={C.blue} ink={C.ink} label="数据库负载 · 降七成" labelSize={34} />
      </div>
    </Shot>
  );
};

// ── S8 · hero-verdict：「5×」落定 + 结论条 ──────────────────────────────────────────
const S8: React.FC<{f: number}> = ({f}) => {
  const at = beatAt('S8');
  return (
    <Shot id="S8" f={f} entry="zoom">
      <div style={{position: 'absolute', left: 200, top: 250, width: 700, ...enterAt(f, at(0))}}>
        <div style={{fontSize: 96, fontWeight: 700, color: C.ink, lineHeight: 1.15}}>一行缓存</div>
        <div style={{fontSize: TYPE.titleL, color: C.muted, marginTop: 18}}>@lru_cache · 三行改动</div>
      </div>
      <div style={{position: 'absolute', left: 980, top: 210}}>
        <KineticNumber f={f} at={at(1)} from={1} to={5} dur={26} suffix="×" size={380} color={C.orange} ink={C.ink} label="更快" labelSize={52} />
      </div>
      <div style={{position: 'absolute', left: 200, top: 780}}>
        <VerdictBar f={f} delay={at(2)} tone={C.orange} tag="结论" width={1520} text="一行缓存，五倍速度" />
      </div>
    </Shot>
  );
};

export const SCENES: Record<keyof typeof SHOTS, React.FC<{f: number}>> = {S1, S2, S3, S4, S5, S6, S7, S8};
export const SCENES_VERSION = 'demo-scenes-v4.4 · 8 shots · cinema camera · kinetic numbers';
