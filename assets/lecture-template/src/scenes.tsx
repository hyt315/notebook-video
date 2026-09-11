import React from 'react';
import {Easing, interpolate} from 'remotion';
import {THEME} from './theme/active';
import {CheckBadge, LineIcon, PillTag, TYPE} from './kit';
import {ChatThread, DiffView, FitCard, Funnel, ProgressRing, SkeletonCard, StaggerList, StampSeal, Typewriter} from './fxkit';
import {ShotCamera, CoverPanel, ambientBreath} from './shotkit';
import {StageFrame, PhaseRail} from './stagekit';
import {ConsoleWindow, MetricGrid, StampBanner} from './media';
import {Corridor, SplitStage, ZoomStage} from './skeletons';
import {RevealMask} from './insert';
import {SHOTS} from './shots';

// ============================================================================
// 官方模板场景层 · 「GitHub 开源三部曲 EP0」（8 镜 / 4 骨架 / 5 种镜头意图）
//
// 这一层是**标准答案**：结构照抄，内容替换。形状与判据见
// references/scene-authoring.md、scene-skeletons.md、shot-language.md。
//
// 两条时序铁律：
//   1. 元素出现帧绑定到"讲到它的那一句"（SHOTS.Sx.beats），禁止开头一次性铺完；
//   2. 入场统一 enterAt()：22 帧 easeOut + 上浮 + 微缩放。
//
// 几何：内容留在 [80,1840] × [80,930]；带平移的镜头再内缩平移预算。
// ============================================================================

const C = THEME.palette;
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const easeOut = (f: number, a: number, b: number, from = 0, to = 1) => interpolate(f, [a, Math.max(a + 1, b)], [from, to], {...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1)});
const easeIO = (f: number, a: number, b: number, from = 0, to = 1) => interpolate(f, [a, Math.max(a + 1, b)], [from, to], {...clamp, easing: Easing.inOut(Easing.cubic)});

const IN = 22;
/** 入场：22 帧 easeOut + 22px 上浮 + 0.975→1 微缩放。所有元素统一用它。 */
const enterAt = (f: number, at: number): React.CSSProperties => {
  const p = easeOut(f, at, at + IN);
  return {opacity: p, transform: `translateY(${(1 - p) * 22}px) scale(${0.975 + 0.025 * p})`};
};
const exitAt = (f: number, duration: number): number => 1 - easeIO(f, duration - 18, duration);

type Entry = 'rise' | 'slide' | 'fade' | 'zoom';
const useEntry = (f: number, entry: Entry) => {
  const p = easeOut(f, 0, IN);
  const dx = entry === 'slide' ? (1 - p) * 70 : 0;
  const dy = entry === 'rise' ? (1 - p) * 26 : 0;
  const sc = entry === 'zoom' ? 0.965 + 0.035 * p : 1;
  const op = entry === 'fade' ? easeIO(f, 0, IN) : p;
  return {opacity: op, transform: `translateX(${dx}px) translateY(${dy}px) scale(${sc})`};
};

/** 每镜外壳：受限相机 + 入场 + 可选揭示转场 + 片尾干净淡出 + 羽化底托（负 z）。 */
const Shot: React.FC<{id: keyof typeof SHOTS; f: number; entry: Entry; reveal?: boolean; children: React.ReactNode}> = ({id, f, entry, reveal, children}) => {
  const s = SHOTS[id];
  const e = useEntry(f, entry);
  // 不再在镜末淡到全透明：那会在镜头边界留下 1–2 个空帧（逐帧审计实测）。
  // 交接由 index.tsx 的 FinalDemo 负责——下一镜开始时把上一镜的末帧叠在上面淡出。
  const body = (
    <div style={{position: 'absolute', inset: 0, opacity: e.opacity, transform: e.transform}}>
      <CoverPanel
        x={70} y={92} w={1780} h={846} tone="wash" z={-1} pad={0}
        style={{boxShadow: 'none', borderRadius: 0, transform: `scale(${ambientBreath(f)})`, transformOrigin: '50% 50%',
                background: `radial-gradient(125% 118% at 50% 50%, ${C.paperBase}F5 58%, ${C.paperBase}D6 82%, ${C.paperBase}00 100%)`}}
      />
      {children}
    </div>
  );
  return <ShotCamera keys={s.keys} f={f} anchor={s.anchor}>{reveal ? <RevealMask f={f} at={0} dur={22}>{body}</RevealMask> : body}</ShotCamera>;
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
    <Shot id="S1" f={f} entry="rise">
      <StageFrame
        x={210} y={176} w={1500} h={710} f={f} phases={phases} railW={380}
        header={() => (
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <PillTag text="GITHUB 新手三部曲" color={C.blue} bg={C.blueLight} />
            <span style={{fontFamily: 'Space,Kai', fontWeight: 700, fontSize: TYPE.titleS, color: C.ink}}>你写的代码，还躺在硬盘里吗？</span>
          </div>
        )}
        rail={(ctx) => (
          <div style={{position: 'relative', height: '100%'}}>
            <PhaseRail phases={phases} ctx={ctx} />
            <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, padding: '14px 16px', borderRadius: 12, background: C.paperBase, border: `1.5px solid ${C.line}`, ...enterAt(f, at(1))}}>
              <div style={{fontSize: 20, fontWeight: 700, color: C.muted, marginBottom: 10}}>本地 → 远程</div>
              <div style={{fontSize: 20, fontWeight: 700, color: C.ink, lineHeight: 1.6}}>只有你能看到<br />→ 全世界都能参与</div>
            </div>
          </div>
        )}
        stamp={() => <StampBanner x={0} y={0} w={1000} f={f} at={at(2, 40)} text="代码不该只躺在硬盘里" color={C.orange} />}
      >
        {() => (
          <div style={{position: 'relative', height: '100%'}}>
            <ConsoleWindow x={0} y={0} w={1000} h={280} f={f} title="terminal" rows={rows} rowGap={62} />
            <div style={{position: 'absolute', left: 0, top: 352, display: 'flex', gap: 14}}>
              {chips.map((x) => (
                <div key={x.k} style={{width: 324, height: 148, borderRadius: 12, background: C.paper, border: `2.5px solid ${x.c}`, boxShadow: `3px 3px 0 ${C.ink}`, padding: '16px 18px', ...enterAt(f, x.at)}}>
                  <div style={{fontSize: 20, fontWeight: 700, color: C.muted}}>{x.k}</div>
                  <div style={{fontSize: 24, fontWeight: 700, color: x.c, marginTop: 10}}>{x.v}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </StageFrame>
    </Shot>
  );
};

// ── S2 · Corridor：入场三步（213–286）──────────────────────────────────
const S2ThreeSteps: React.FC<{f: number}> = ({f}) => {
  const b = SHOTS.S2.beats;
  const t0 = b[0] ?? 0;
  const steps = [
    {label: '参与', detail: '做别人的项目', color: C.orange},
    {label: '发布', detail: '整理自己的仓库', color: C.blue},
    {label: '运营', detail: '分流 · 审查 · 发版', color: C.green},
  ];
  const stations = steps.map((s, i) => ({...s, at: t0 + i * 24, state: `第 ${i + 1} 步`}));
  return (
    <Shot id="S2" f={f} entry="rise">
      <Corridor x={360} y={210} w={1200} f={f} laneY={84} from={t0} to={t0 + 52} stations={stations} />
      <div style={{position: 'absolute', left: 300, top: 690, width: 1320, textAlign: 'center', ...enterAt(f, t0 + 30)}}>
        <div style={{fontSize: TYPE.titleM, fontWeight: 700, color: C.muted}}>想入场，其实只要三步</div>
      </div>
      <div style={{position: 'absolute', left: 1360, top: 640, ...enterAt(f, t0 + 48)}}><StampSeal text="三步" x={0} y={0} size={130} frame={f} start={t0 + 48} color={C.orange} /></div>
    </Shot>
  );
};

// ── S3 · Zoom：第一步 · 交出第一个 PR（286–416）────────────────────────
const S3FirstPr: React.FC<{f: number}> = ({f}) => {
  const b = SHOTS.S3.beats;
  const at = (i: number, d = 0) => (b[Math.min(i, b.length - 1)] ?? 0) + d;
  return (
    <Shot id="S3" f={f} entry="zoom" reveal>
      <ZoomStage x={210} y={200} w={1000} h={600} f={f} focus={{fx: 0.44, fy: 0.5}} zoom={1.34}
        contentW={944} contentH={420}
        at={{focus: at(1), annotate: at(1) + 30, back: at(1) + 90}} label="第一个 PR 不必大">
        <div style={{position: 'absolute', inset: 0, padding: 26, background: C.paper}}>
          <CardHead icon="branch" text="pull-request.diff" right={<PillTag text="EP 1" color={C.orange} bg={C.orangeLight} />} />
          <div style={enterAt(f, at(0))}>
            <DiffView x={30} y={92} w={944} frame={f} title="docs/typo.patch"
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
      <FitCard x={1250} y={240} w={510} h={300} f={f} pad={24} frame={f} borderColor={C.orange} style={enterAt(f, at(1, 10))}>
        <div style={{fontSize: TYPE.labelL, fontWeight: 700, color: C.muted}}>第一次参与的路径</div>
        <div style={{marginTop: 16, display: 'flex', flexDirection: 'column', gap: 12}}>
          {['读懂项目规则', '找一个最小改动', '提交并等评审'].map((t, i) => (
            <div key={t} style={{display: 'flex', alignItems: 'center', gap: 10, fontSize: TYPE.bodyM, fontWeight: 700, ...enterAt(f, at(1, 20 + i * 12))}}>
              <CheckBadge size={24} />{t}
            </div>
          ))}
        </div>
      </FitCard>
      <div style={{position: 'absolute', left: 1250, top: 648, width: 510, ...enterAt(f, at(1, 60))}}>
        <Typewriter frame={f} start={at(1, 60)} cps={0.45} text="小改动，也是有效贡献" fontSize={TYPE.titleXS} color={C.orange} cursor={false} />
      </div>
    </Shot>
  );
};

// ── S4 · Split：第二步 · 专业的开源仓库（416–532）──────────────────────
const S4ProRepo: React.FC<{f: number}> = ({f}) => {
  const b = SHOTS.S4.beats;
  const at = (i: number, d = 0) => (b[Math.min(i, b.length - 1)] ?? 0) + d;
  return (
    <Shot id="S4" f={f} entry="slide">
      <SplitStage
        x={240} y={196} w={1440} h={416} f={f} winner="right" winnerAt={at(1)}
        left={{title: '随手放上去', sub: '别人不知道这是什么', rows: ['没有说明文档', '没有许可证', '没有自动化检查'], color: C.muted}}
        right={{title: '专业的开源仓库', sub: '别人愿意用、敢用', rows: ['README 讲清楚', 'LICENSE 讲授权', 'CI 守住质量'], color: C.green}}
      />
      <FitCard x={240} y={654} w={880} h={196} f={f} pad={24} frame={f} borderColor={C.blue} style={enterAt(f, at(1, 20))}>
        <div style={{fontSize: TYPE.labelL, fontWeight: 700, color: C.muted}}>标准三件套</div>
        <div style={{marginTop: 14, display: 'flex', gap: 26}}>
          {['README.md', 'LICENSE', 'CI / Actions'].map((t, i) => (
            <div key={t} style={{display: 'flex', alignItems: 'center', gap: 10, fontSize: TYPE.bodyM, fontWeight: 700, ...enterAt(f, at(1, 30 + i * 12))}}>
              <CheckBadge size={24} />{t}
            </div>
          ))}
        </div>
      </FitCard>
      <div style={{position: 'absolute', left: 1180, top: 690, width: 520}}>
        <StaggerList x={0} y={0} w={520} frame={f} start={at(1, 60)} stagger={6} items={[
          {text: '让人一眼看懂', sub: 'README', color: C.blue},
          {text: '让人放心使用', sub: 'LICENSE', color: C.green},
        ]} />
      </div>
    </Shot>
  );
};

// ── S5 · Stage：第三步 · 运营（532–682）────────────────────────────────
const S5Ops: React.FC<{f: number}> = ({f}) => {
  const b = SHOTS.S5.beats;
  const at = (i: number, d = 0) => (b[Math.min(i, b.length - 1)] ?? 0) + d;
  const phases = [
    {at: at(0), state: 'triage', label: 'Issue 分流'},
    {at: at(1), state: 'review', label: 'PR 审查'},
    {at: at(1, 60), state: 'release', label: '按时发版'},
  ];
  return (
    <Shot id="S5" f={f} entry="fade">
      <StageFrame
        x={230} y={176} w={1460} h={710} f={f} phases={phases} railW={350}
        header={() => <span style={{fontFamily: 'Space,Kai', fontWeight: 700, fontSize: TYPE.titleS}}>第三步 · 学会运营</span>}
        rail={(ctx) => <PhaseRail phases={phases} ctx={ctx} />}
        stamp={() => <StampBanner x={0} y={0} w={1060} f={f} at={at(1, 70)} text="按时发版，仓库才有人气" color={C.green} />}
      >
        {({index}) => (
          <div style={{position: 'relative', height: '100%'}}>
            <div style={{fontSize: TYPE.titleXS, fontWeight: 700, color: C.muted, ...enterAt(f, at(0))}}>一个活跃仓库的日常</div>
            <div style={{position: 'absolute', left: 0, top: 52}}>
              <Funnel x={0} y={0} w={1040} frame={f} start={at(0, 16)} stagger={6} rows={[
                {label: '新 Issue', sub: '需要分流', count: '24', color: C.blue, ratio: 1},
                {label: '可复现 / 待办', sub: '进入里程碑', count: '9', color: C.orange, ratio: 0.38},
                {label: '本周已合并', sub: '并发布 v1.1', count: '6', color: C.green, ratio: 0.25},
              ]} />
            </div>
            <div style={{position: 'absolute', left: 0, top: 372, display: 'flex', alignItems: 'center', gap: 28, ...enterAt(f, at(1, 40))}}>
              <ProgressRing pct={0.86} label="发版进度" color={C.green} start={at(1, 40)} frame={f} size={128} />
              <div style={{fontSize: TYPE.bodyL, fontWeight: 700, color: C.ink, lineHeight: 1.6}}>
                v1.0 → v1.1<br /><span style={{color: C.green}}>按时发布，才有节奏</span>
              </div>
            </div>
            <div style={{position: 'absolute', left: 0, top: 372, opacity: index >= 2 ? 1 : 0}} />
          </div>
        )}
      </StageFrame>
    </Shot>
  );
};

// ── S6 · Corridor：三个 AI 技能（682–803）──────────────────────────────
const S6Skills: React.FC<{f: number}> = ({f}) => {
  const b = SHOTS.S6.beats;
  const t0 = b[0] ?? 0;
  const skills = [
    {label: 'github-oss-contribute', detail: '参与别人的项目', color: C.orange},
    {label: 'github-oss-prep', detail: '发布自己的作品', color: C.blue},
    {label: 'github-oss-ops', detail: '运营与持续发版', color: C.green},
  ];
  const stations = skills.map((s, i) => ({...s, at: t0 + i * 26}));
  return (
    <Shot id="S6" f={f} entry="rise">
      <Corridor x={360} y={196} w={1200} f={f} laneY={84} from={t0} to={t0 + 56} stations={stations} labelSize={22} />
      <div style={{position: 'absolute', left: 300, top: 676, width: 1320, textAlign: 'center', ...enterAt(f, t0 + 30)}}>
        <div style={{fontSize: TYPE.titleM, fontWeight: 700, color: C.muted}}>这三步，我做成了三个 AI 技能</div>
      </div>
      <div style={{position: 'absolute', left: 1380, top: 620, ...enterAt(f, t0 + 52)}}><StampSeal text="三个技能" x={0} y={0} size={130} frame={f} start={t0 + 52} color={C.blue} /></div>
    </Shot>
  );
};

// ── S7 · Zoom：让智能体陪你走完（803–919）──────────────────────────────
const S7Agent: React.FC<{f: number}> = ({f}) => {
  const b = SHOTS.S7.beats;
  const at = (i: number, d = 0) => (b[Math.min(i, b.length - 1)] ?? 0) + d;
  return (
    <Shot id="S7" f={f} entry="zoom" reveal>
      <ZoomStage x={210} y={220} w={1000} h={560} f={f} focus={{fx: 0.5, fy: 0.5}} zoom={1.24}
        contentW={920} contentH={340}
        at={{focus: at(0), annotate: at(0) + 40, back: at(0) + 96}} label="让智能体陪你走完全程">
        <div style={{position: 'absolute', inset: 0, padding: 30, background: C.paper}}>
          <CardHead icon="user" text="与智能体协作" />
          <div style={{position: 'absolute', left: 30, top: 92}}>
            <ChatThread x={0} y={0} w={920} frame={f} msgs={[
              {side: 'l', text: '我想给这个项目提一个 PR', at: at(0)},
              {side: 'r', text: '先读贡献指南，再找最小改动', at: at(0, 26)},
              {side: 'l', text: '改好了，帮我检查一遍', at: at(0, 56)},
            ]} />
          </div>
        </div>
      </ZoomStage>
      <div style={{position: 'absolute', left: 1250, top: 320, width: 510}}>
        <SkeletonCard x={0} y={0} w={510} h={200} frame={f} start={at(0, 20)} revealAt={at(0, 80)} rows={2}>
          <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
            <CheckBadge size={28} />
            <div>
              <div style={{fontSize: TYPE.titleXS, fontWeight: 700}}>全程有人带</div>
              <div style={{fontSize: TYPE.labelL, fontWeight: 700, color: C.muted, marginTop: 8}}>读规则 · 改代码 · 走流程</div>
            </div>
          </div>
        </SkeletonCard>
      </div>
    </Shot>
  );
};

// ── S8 · Stage：三期视频，一期一步（919–1150）──────────────────────────
const S8Series: React.FC<{f: number}> = ({f}) => {
  const b = SHOTS.S8.beats;
  const at = (i: number, d = 0) => (b[Math.min(i, b.length - 1)] ?? 0) + d;
  const phases = [
    {at: at(0), state: 'ep1', label: '第一期 · 参与'},
    {at: at(1), state: 'ep2', label: '第二期 · 发布'},
    {at: at(2), state: 'ep3', label: '第三期 · 运营'},
  ];
  return (
    <Shot id="S8" f={f} entry="fade">
      <StageFrame
        x={260} y={190} w={1400} h={700} f={f} phases={phases}
        header={() => <span style={{fontFamily: 'Space,Kai', fontWeight: 700, fontSize: TYPE.titleS}}>三期视频，一期一步</span>}
        stamp={() => <StampBanner x={0} y={0} w={1348} f={f} at={at(2, 20)} text="主页搜 hyt315，现在出发" color={C.orange} />}
      >
        {() => (
          <div style={{position: 'relative', height: '100%'}}>
            <MetricGrid x={0} y={0} w={1348} f={f} cols={3} cellH={200} start={at(0, 10)} stagger={6} title="三期视频，一期一步"
              items={[
                {label: 'EP 1 · 参与', before: '不会', after: '会提 PR', win: true, color: C.orange},
                {label: 'EP 2 · 发布', before: '本地项目', after: '专业仓库', win: true, color: C.blue},
                {label: 'EP 3 · 运营', before: '无人问津', after: '持续发版', win: true, color: C.green},
              ]}
            />
            <div style={{position: 'absolute', left: 0, top: 380, display: 'flex', alignItems: 'center', gap: 14, ...enterAt(f, at(2, 40))}}>
              <CheckBadge size={28} />
              <span style={{fontSize: TYPE.titleXS, fontWeight: 700, color: C.ink}}>三个技能已开源，让智能体陪你走完全程</span>
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
