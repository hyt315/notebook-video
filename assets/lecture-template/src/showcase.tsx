import React from 'react';
import {AbsoluteFill, Series} from 'remotion';
import {THEME} from './theme/active';
import {DepthLayers, SHOTKIT_VERSION, camAt, shotCam} from './shotkit';
import {Attach, PhaseRail, STAGEKIT_VERSION, useStageMachine} from './stagekit';
import {INSERT_VERSION, TRANSITIONS} from './insert';
import {ConsoleWindow, MEDIA_VERSION, MetricGrid} from './media';
import {Corridor, SKELETON_VERSION, SKELETONS, SplitStage, ZoomStage} from './skeletons';
import {
  BurstCallout, ChatThread, CompareBars, ConfettiPop, DiffView, FitCard, Funnel, MailScan,
  PayPop, ProgressRing, SkeletonCard, StaggerList, StampSeal, TimeRail, Typewriter,
} from './fxkit';
import {
  BrowserChrome, Callout, Checklist, CodeBlock, Connector, CountUp, JumpInText, Mascot,
  ProgressBar, RollDigit, TOOLKIT_VERSION, WaveText,
} from './toolkit';

// ============================================================================
// showcase · 组件接触表（Composition: NotebookVideoShowcase）
//
// 目的：让执行 AI **看见**库组件长什么样，而不是读文字描述。
// 这是「能力存在但不可达」的直接解法——此前零调用的组件在这里全部渲染一遍，
// 抽成接触表后，AI 用 Read 看图选型，比读 props 文档准确得多。
//
// 用法：
//   node scripts/notebook-video.mjs showcase <proj>          # 渲染接触表 mp4
//   node scripts/notebook-video.mjs showcase-sheet <proj>    # 抽 1fps 接触表 jpg
//
// 每页 30 帧（1 秒），共 SHOWCASE_PAGES 页；1fps 抽帧恰好一页一张图。
// 注：KenBurnsImg / EvidenceZoom 依赖位图素材，不进接触表（不给模板塞示例图片）。
// ============================================================================

const C = THEME.palette;
const F = 150; // 所有组件渲染在「已落定」帧，便于一眼看清形态
const PAGE = 30;

const Tile: React.FC<{name: string; children?: React.ReactNode}> = ({name, children}) => (
  <div style={{position: 'relative', overflow: 'hidden', background: C.paperWarm, border: `1px solid ${C.line}`, borderRadius: 10, height: '100%'}}>
    <div style={{position: 'absolute', left: 12, top: 6, zIndex: 200, fontFamily: 'Space,monospace', fontSize: 16, fontWeight: 700, color: C.muted}}>{name}</div>
    <div style={{position: 'absolute', left: 0, top: 30, width: 860, height: 430, transform: 'scale(0.98)', transformOrigin: '0 0', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      {children}
    </div>
  </div>
);

const Page: React.FC<{title: string; note?: string; children?: React.ReactNode}> = ({title, note, children}) => (
  <AbsoluteFill style={{background: C.paperBase, fontFamily: 'Kai,sans-serif', color: C.ink}}>
    <div style={{position: 'absolute', left: 24, top: 12, fontFamily: 'Space,Kai', fontSize: 26, fontWeight: 700}}>{title}</div>
    {note && <div style={{position: 'absolute', left: 24, top: 46, fontSize: 17, color: C.muted}}>{note}</div>}
    {children}
  </AbsoluteFill>
);

/** 4 格（2×2） */
const Grid4: React.FC<{items: {name: string; node: React.ReactNode}[]}> = ({items}) => (
  <>
    {items.map((it, i) => (
      <div key={it.name} style={{position: 'absolute', left: 20 + (i % 2) * 950, top: 76 + Math.floor(i / 2) * 500, width: 900, height: 470}}>
        <Tile name={it.name}>{it.node}</Tile>
      </div>
    ))}
  </>
);

// 六种镜头意图：同一内容、不同取景。每格显示该意图在 60 帧处的实际相机参数。
const IntentPlate: React.FC<{intent: Parameters<typeof shotCam>[0]; kind: 'text' | 'graphic'}> = ({intent, kind}) => {
  const keys = shotCam(intent, {
    duration: 120,
    x: 960,
    y: 540,
    to: intent === 'push-in' || intent === 'micro-orbit' ? 1.22 : intent === 'establish' ? 1.03 : 1.05,
    rotY: intent === 'micro-orbit' ? 5 : 0,
  });
  const c = camAt(keys, 60);
  return (
    <div style={{position: 'relative', width: 600, height: 380}}>
      <div style={{position: 'absolute', inset: 0, overflow: 'hidden', borderRadius: 12, background: C.paperWarm, border: `1.5px solid ${C.line}`}}>
        <DepthLayers
          keys={keys}
          f={60}
          overscan={0.1}
          far={<AbsoluteFill style={{background: `radial-gradient(circle at 30% 30%, ${C.skyTint}, transparent 62%), ${C.paperWarm}`}} />}
        >
          <div style={{position: 'absolute', inset: 0}}>
            {[0, 1, 2, 3].map((k) => (
              <div key={k} style={{position: 'absolute', left: 70 + k * 150, top: 90 + (k % 2) * 130, width: 130, height: 96, borderRadius: 10, background: C.paper, border: `2px solid ${[C.blue, C.orange, C.green, C.gold][k]}`, boxShadow: THEME.paperShadow(0.2), display: 'grid', placeItems: 'center', fontSize: 20, fontWeight: 700}}>
                {kind === 'text' ? `样${k + 1}` : `0${k + 1}`}
              </div>
            ))}
          </div>
        </DepthLayers>
      </div>
      <div style={{position: 'absolute', left: 10, top: 8, fontFamily: 'Space,monospace', fontSize: 17, fontWeight: 700, color: C.blue, background: `${C.paperWarm}DD`, padding: '2px 8px', borderRadius: 6}}>
        {intent} · s={c.s.toFixed(3)} x={c.x.toFixed(0)}
      </div>
    </div>
  );
};

const PHASES = [
  {at: 0, state: 'ingress', label: '请求进入'},
  {at: 40, state: 'gateway', label: '路由判定'},
  {at: 80, state: 'compute', label: '送往 Flash'},
  {at: 120, state: 'billing', label: '按 Flash 计费'},
  {at: 160, state: 'verdict', label: '结论'},
];

export const Showcase: React.FC = () => {
  const railCtx = useStageMachine(PHASES, 100);

  const p1 = [
    {name: 'CompareBars · 数据对比', node: <CompareBars x={0} y={0} w={760} f={F} frame={F} start={0} rows={[{label: 'V4 Pro', pct: 0.62, color: C.muted, value: '1.00×'}, {label: 'V4.1 Flash', pct: 0.94, color: C.green, value: '1.42×'}]} delta="性能 +42%" />},
    {name: 'ProgressRing · 进度环', node: <div style={{display: 'flex', gap: 44}}><ProgressRing pct={0.92} label="Flash" color={C.green} start={0} frame={F} /><ProgressRing pct={0.62} label="Pro" color={C.blue} start={0} frame={F} /></div>},
    {name: 'TimeRail · 时间轨', node: <TimeRail x={0} y={70} w={800} frame={F} ticks={[{t: '9/10', label: 'Flash 上线', color: C.blue, at: 0}, {t: '过渡期', label: '自动路由', color: C.orange, at: 30}, {t: 'Next', label: 'Pro 上线', color: C.muted, at: 60}]} />},
    {name: 'StaggerList · 级联清单', node: <StaggerList x={0} y={50} w={760} frame={F} start={0} items={[{text: '性能更强', sub: '超过 Pro', color: C.green}, {text: '费用更低', sub: '账单更省', color: C.green}, {text: '速度更快', sub: '等待更短', color: C.green}]} />},
  ];
  const p2 = [
    {name: 'ConsoleWindow · 控制台介质', node: <ConsoleWindow x={0} y={20} w={800} f={F} title="api.deepseek.com" rows={[{text: 'POST /v1/chat  model="v4-pro"', tone: 'cmd'}, {text: 'gateway: match rule #14', tone: 'info'}, {text: '→ routed to v4.1-flash', tone: 'info'}, {text: '✓ 200 OK  billing=v4.1-flash', tone: 'ok'}]} status={{text: 'ROUTED', tone: 'ok'}} />},
    {name: 'MetricGrid · 指标网格', node: <MetricGrid x={0} y={30} w={840} f={F} cols={4} cellH={150} items={[{label: '性能', before: '1.00×', after: '1.42×', win: true}, {label: '费用', before: '¥1.00', after: '¥0.31', win: true}, {label: '速度', before: '2.1s', after: '0.9s', win: true}, {label: '总用时', before: '3.4s', after: '1.6s', win: true}]} />},
    {name: 'DiffView · 补丁介质', node: <DiffView x={0} y={30} w={780} frame={F} title="client.py" lines={[{k: ' ', text: 'client = OpenAI(base_url=...)'}, {k: '-', text: 'model = "v4-pro"', at: 0}, {k: '+', text: 'model = "v4.1-flash"', at: 8}, {k: ' ', text: '# 账单按 Flash 计费', at: 16}]} />},
    {name: 'Typewriter · 逐字介质', node: <div style={{width: 780}}><div style={{fontSize: 32, lineHeight: 1.5}}><Typewriter frame={F} start={0} cps={0.4} text="你调的还是 V4 Pro，实际跑的是 V4.1 Flash" /></div><div style={{marginTop: 22, fontSize: 24, color: C.muted}}><Typewriter frame={F} start={60} cps={0.5} cursor={false} text="按 Flash 单价计费，无需改代码" /></div></div>},
  ];
  const p3 = [
    {name: 'FitCard · 防出格卡片', node: <FitCard x={40} y={40} w={700} h={220} frame={F} pad={26}><div style={{fontSize: 30, fontWeight: 700}}>卡片高度由 fitH() 算出</div><div style={{fontSize: 23, color: C.muted, marginTop: 12}}>CardFitGate 渲染期抓出任何溢出</div></FitCard>},
    {name: 'Funnel · 漏斗介质', node: <Funnel x={0} y={20} w={800} frame={F} start={0} rows={[{label: '调用 v4-pro', sub: '请求', count: '10,000', color: C.blue, ratio: 1}, {label: '自动路由', sub: '网关', count: '10,000', color: C.orange, ratio: 1}, {label: '按 Flash 计费', sub: '账单', count: '-69%', color: C.green, ratio: 0.31}]} />},
    {name: 'SkeletonCard · 占位→内容', node: <SkeletonCard x={40} y={30} w={680} h={240} frame={F} start={0} revealAt={30}><div style={{fontSize: 28, fontWeight: 700}}>等待路由结果</div><div style={{fontSize: 22, color: C.muted, marginTop: 10}}>先占位，落定再 pop 出真内容</div></SkeletonCard>},
    {name: 'StampSeal / BurstCallout / ConfettiPop', node: <div style={{position: 'relative', width: 840, height: 400}}><StampSeal text="已完成" x={20} y={20} frame={F} start={0} color={C.green} /><StampSeal text="按 Flash 计费" x={20} y={190} size={130} frame={F} start={0} color={C.red} /><div style={{position: 'absolute', left: 250, top: 20}}><BurstCallout x={220} y={80} size={140} text="省钱" frame={F} start={0} /></div><div style={{position: 'absolute', left: 220, top: 220}}><ConfettiPop x={90} y={70} n={24} frame={F} start={0} dur={55} /></div></div>},
  ];
  const p4 = [
    {name: 'ChatThread · 对话介质', node: <ChatThread x={0} y={30} w={800} frame={F} msgs={[{side: 'l', text: '还在用 v4-pro？', at: 0}, {side: 'r', text: '是的，没改代码', at: 30}, {side: 'l', text: '已经是 Flash 在跑了', at: 60}]} />},
    {name: 'MailScan · 邮件介质', node: <MailScan x={0} y={20} w={820} frame={F} start={0} rows={[{from: 'DeepSeek 开放平台', subject: '关于模型用量调整的通知', at: 0}, {from: 'billing@deepseek.com', subject: '账单已按 V4.1 Flash 计费', at: 26}]} />},
    {name: 'PayPop · 到账介质', node: <PayPop x={40} y={40} w={700} frame={F} start={0} app="账单" title="本月节省" amount="-69%" stampAt={30} stampText="已生效" />},
    {name: 'PhaseRail + Attach · 状态轨/附着信息', node: <div style={{position: 'relative', width: 840, height: 400}}><div style={{position: 'absolute', left: 10, top: 20}}><PhaseRail phases={PHASES} ctx={railCtx} /></div><Attach x={420} y={110} w={400} f={F} at={0} color={C.orange}><div style={{fontSize: 24, fontWeight: 700}}>附着信息：不新开卡片</div></Attach></div>},
  ];

  // ⑦⑧⑨ 修辞工具件（v3.0.1 从 index.tsx 迁出到 toolkit.tsx；此前接触表**一页都没有**，
  // 于是 11 个组件虽然能 import 了，却谁也没被渲染过——接触表是"看见才会用"的唯一入口。
  const p7 = [
    {name: 'Callout · 画圈标注', node: <div style={{position: 'relative', width: 840, height: 400}}>
      <div style={{position: 'absolute', left: 80, top: 150, width: 420, height: 80, borderRadius: 10, background: C.paper, border: `2px solid ${C.line}`, display: 'grid', placeItems: 'center', fontFamily: 'Space,Kai', fontSize: 26, fontWeight: 700, color: C.muted}}>(没有远程仓库，只有本地)</div>
      <Callout x={62} y={136} w={456} h={108} frame={F} start={0} text="圈住症结，旁边写字" />
    </div>},
    {name: 'Connector · 关系连线', node: <div style={{position: 'relative', width: 840, height: 400}}>
      <div style={{position: 'absolute', left: 90, top: 70, width: 190, height: 66, borderRadius: 12, background: C.paper, border: `2px solid ${C.ink}`, display: 'grid', placeItems: 'center', fontSize: 25, fontWeight: 700}}>本地仓库</div>
      <div style={{position: 'absolute', left: 500, top: 250, width: 240, height: 66, borderRadius: 12, background: C.paper, border: `2px solid ${C.ink}`, display: 'grid', placeItems: 'center', fontSize: 25, fontWeight: 700}}>全世界都能参与</div>
      <Connector from={{x: 284, y: 104}} to={{x: 496, y: 282}} bend={44} frame={F} label="push" flow />
    </div>},
    {name: 'Checklist · 带完成态的清单', node: <div style={{position: 'relative', width: 840, height: 400}}>
      <div style={{position: 'absolute', left: 60, top: 40, fontSize: 25, fontWeight: 700, color: C.muted}}>第一次参与的路径</div>
      <div style={{position: 'absolute', left: 60, top: 104}}>
        <Checklist items={['读懂项目规则', '找一个最小改动', '提交并等评审']} start={0} frame={F} stagger={8} done={2} rowH={64} fontSize={30} />
      </div>
    </div>},
  ];
  const p8 = [
    {name: 'CountUp · 数字滚动计数', node: <div style={{position: 'relative', width: 840, height: 400}}>
      <div style={{position: 'absolute', left: 60, top: 70, display: 'flex', alignItems: 'baseline', gap: 18}}>
        <CountUp to={69} prefix="-" suffix="%" start={0} frame={F} fontSize={104} color={C.green} />
        <span style={{fontSize: 26, fontWeight: 700, color: C.muted}}>账单降幅</span>
      </div>
      <div style={{position: 'absolute', left: 60, top: 240, display: 'flex', alignItems: 'baseline', gap: 18}}>
        <CountUp to={11} duration={40} start={0} frame={F} fontSize={76} color={C.blue} />
        <span style={{fontSize: 26, fontWeight: 700, color: C.muted}}>个修辞工具件</span>
      </div>
    </div>},
    {name: 'ProgressBar · 进度条', node: <div style={{position: 'relative', width: 840, height: 400}}>
      <div style={{position: 'absolute', left: 60, top: 80, width: 660}}>
        <ProgressBar v={0.86} label="发版进度" showPct color={C.green} />
        <div style={{height: 34}} />
        <ProgressBar v={0.42} label="Issue 分流" showPct color={C.blue} height={20} />
        <div style={{height: 34}} />
        <ProgressBar v={0.12} label="待复现" showPct color={C.orange} height={26} />
      </div>
    </div>},
    {name: 'RollDigit / BrowserChrome · 滚牌与页面载体', node: <div style={{position: 'relative', width: 840, height: 400}}>
      <div style={{position: 'absolute', left: 60, top: 24, display: 'flex', gap: 8}}>
        {['v', '4', '.', '1'].map((ch, i) => <RollDigit key={i} fromChar="0" toChar={ch} start={i * 5} frame={F} fontSize={92} colorFrom={C.muted} colorTo={C.ink} />)}
      </div>
      <div style={{position: 'absolute', left: 60, top: 190, width: 720}}>
        <BrowserChrome url="github.com/hyt315/notebook-video" lift={0.2} style={{position: 'relative', left: 0, top: 0, width: 700}}>
          <div style={{padding: '22px 26px'}}>
            <div style={{fontSize: 30, fontWeight: 700}}>notebook-video</div>
            <div style={{fontSize: 21, color: C.muted, marginTop: 10}}>把讲稿渲成 2K 讲解视频的技能</div>
          </div>
        </BrowserChrome>
      </div>
    </div>},
  ];
  const p9 = [
    {name: 'JumpInText · 逐字跳入', node: <div style={{width: 820, textAlign: 'center'}}>
      <JumpInText items={[{text: '代码不该', color: C.ink}, {text: '只躺在硬盘里', color: C.ink}]} fontSize={66} start={0} stagger={1.3} frame={F} />
    </div>},
    {name: 'WaveText · 波浪打字', node: <div style={{width: 820, textAlign: 'center'}}>
      <WaveText text="OPEN SOURCE" fontSize={72} colorFrom={C.muted} colorTo={C.blue} start={0} stagger={1.6} frame={F} />
    </div>},
    {name: 'Mascot · 系列吉祥物', node: <Mascot size={280} f={F} wave />},
    {name: 'CodeBlock · 终端代码窗', node: <CodeBlock title="快速开始" frame={F} stagger={6} style={{width: 780}} lines={[
      {text: 'npm i -g notebook-video', color: C.green},
      {text: 'notebook-video new my-film'},
      {text: '# 改讲稿 → 出 2K 讲解视频', color: C.muted},
    ]} />},
  ];

  return (
    <AbsoluteFill>
      <Series>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="① 数据 / 结论介质" note={SHOTKIT_VERSION}><Grid4 items={p1} /></Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="② 控制台 / 指标 / 代码 介质" note={MEDIA_VERSION}><Grid4 items={p2} /></Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="③ 卡片 / 漏斗 / 标注构件" note={STAGEKIT_VERSION}><Grid4 items={p3} /></Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="④ 对话 / 邮件 / 状态轨" note={INSERT_VERSION}><Grid4 items={p4} /></Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="⑤ 六种镜头意图（同一内容，不同取景）" note="每格显示 60 帧处的真实相机参数；s=缩放，x=注视点横坐标">
            {(['establish', 'push-in', 'pull-back', 'pan-follow', 'reveal', 'micro-orbit'] as const).map((it, i) => (
              <div key={it} style={{position: 'absolute', left: 40 + (i % 3) * 620, top: 90 + Math.floor(i / 3) * 460}}>
                <IntentPlate intent={it} kind={i % 2 === 0 ? 'text' : 'graphic'} />
              </div>
            ))}
          </Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="⑥ 场景骨架：Corridor / Split / Zoom / Stage" note={`骨架 ${SKELETONS.join(' / ')} · 转场 ${TRANSITIONS.join(' / ')}`}>
            <div style={{position: 'absolute', left: 40, top: 84, width: 1840, height: 300}}>
              <Corridor x={100} y={0} w={1720} f={F} laneY={60} stations={[{label: '发起请求', at: 0, detail: '调用方不用改代码'}, {label: '自动路由', at: 30, detail: '请求送往 Flash'}, {label: '按 Flash 结算', at: 60, detail: '账单只按 Flash 价'}]} startBanner={{at: 0, text: 'Corridor · 走廊骨架'}} />
            </div>
            <div style={{position: 'absolute', left: 40, top: 410, width: 900, height: 620}}>
              <div style={{position: 'absolute', left: 0, top: -28, fontFamily: 'Space,monospace', fontSize: 18, fontWeight: 700, color: C.muted}}>Split · 双栏对比</div>
              <SplitStage x={0} y={20} w={880} h={540} f={F} winner="right" winnerAt={0} left={{title: 'V4 Pro', sub: '旧旗舰', rows: ['价格高', '速度慢', '算力消耗大'], color: C.muted}} right={{title: 'V4.1 Flash', sub: '轻量快刀', rows: ['价格低', '速度更快', '算力更省'], color: C.green}} />
            </div>
            <div style={{position: 'absolute', left: 980, top: 410, width: 900, height: 620}}>
              <div style={{position: 'absolute', left: 0, top: -28, fontFamily: 'Space,monospace', fontSize: 18, fontWeight: 700, color: C.muted}}>Zoom · 整体→聚焦→标注→回整体</div>
              <ZoomStage x={0} y={20} w={880} h={540} f={F} focus={{fx: 0.28, fy: 0.62}} at={{focus: 0, annotate: 30, back: 999}} label="纯代码局部放大，不是图片">
                <div style={{position: 'absolute', inset: 0, padding: 30}}>
                  <div style={{fontSize: 26, fontWeight: 700, marginBottom: 16}}>控制台 · 路由日志</div>
                  {['POST /v1/chat model="v4-pro"', 'gateway: match rule #14', '→ routed to v4.1-flash', '✓ billing unit = flash', '✓ response 200 OK'].map((t, i) => (
                    <div key={i} style={{fontFamily: 'Space,monospace', fontSize: 22, marginBottom: 14, color: i === 2 ? C.orange : C.ink}}>{t}</div>
                  ))}
                </div>
              </ZoomStage>
            </div>
          </Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="⑦ 修辞工具件 · 圈 / 连 / 单" note={TOOLKIT_VERSION}><Grid4 items={p7} /></Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="⑧ 修辞工具件 · 数字 / 进度 / 载体" note="CountUp / ProgressBar / RollDigit / BrowserChrome"><Grid4 items={p8} /></Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="⑨ 修辞工具件 · 字效 / 吉祥物" note="JumpInText / WaveText / Mascot / CodeBlock"><Grid4 items={p9} /></Page>
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};

export const SHOWCASE_PAGES = 9;
export const SHOWCASE_VERSION = 'showcase-v2 · 9 pages · 30 components + 6 intents + 4 skeletons';
