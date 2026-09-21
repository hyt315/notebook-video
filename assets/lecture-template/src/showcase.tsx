import React from 'react';
import {AbsoluteFill, Series} from 'remotion';
import {THEME} from './theme/active';
import {SHOTKIT_VERSION, camAt, shotCam} from './shotkit';
import {PhaseRail, STAGEKIT_VERSION, useStageMachine} from './stagekit';
import {INSERT_VERSION, TRANSITIONS} from './insert';
import {ConsoleWindow, MEDIA_VERSION, MetricGrid} from './media';
import {Corridor, SKELETON_VERSION, SKELETONS, SplitStage, ZoomStage} from './skeletons';
import {
  ChatThread, DiffView, FitCard, Funnel, ProgressRing, SkeletonCard, StaggerList, StampSeal, Typewriter,
} from './fxkit';
import {Callout, Checklist, JumpInText, TOOLKIT_VERSION} from './toolkit';
import {Accordion, Chart, ClipReveal, COMPONENTS_VERSION, ControlStack, FitTextBox, GeoView, GlowFrame, HighlightCode, IconWall, MathBlock, MorphShape, NetworkGraph, NoiseJitter, OverlayFrame, PathDraw, PieDraw, QrCode, SankeyChart, SceneTransitions, ShapeDraw, SHAPES, ShimmerText, SketchFx, Tabs, TopicIcon, TreeView} from './components';

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
        <AbsoluteFill>
          <div style={{position: 'absolute', inset: 0}}>
            {[0, 1, 2, 3].map((k) => (
              <div key={k} style={{position: 'absolute', left: 70 + k * 150, top: 90 + (k % 2) * 130, width: 130, height: 96, borderRadius: 10, background: C.paper, border: `2px solid ${[C.blue, C.orange, C.green, C.gold][k]}`, boxShadow: THEME.paperShadow(0.2), display: 'grid', placeItems: 'center', fontSize: 20, fontWeight: 700}}>
                {kind === 'text' ? `样${k + 1}` : `0${k + 1}`}
              </div>
            ))}
          </div>
        </AbsoluteFill>
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
    {name: 'ProgressRing · 进度环', node: <div style={{display: 'flex', gap: 44}}><ProgressRing pct={0.92} label="Flash" color={C.green} start={0} frame={F} /><ProgressRing pct={0.62} label="Pro" color={C.blue} start={0} frame={F} /></div>},
    {name: 'StaggerList · 级联清单', node: <StaggerList x={0} y={50} w={760} frame={F} start={0} items={[{text: '性能更强', sub: '超过 Pro', color: C.green}, {text: '费用更低', sub: '账单更省', color: C.green}, {text: '速度更快', sub: '等待更短', color: C.green}]} />},
    {name: 'Chart · d3 图表（封装层）', node: <div style={{transform: 'scale(0.62)'}}><Chart f={F} startAt={0} width={1180} height={600} title="刻度由 d3 算，画还是我们画" data={[{label: 'A', value: 12}, {label: 'B', value: 34}, {label: 'C', value: 21}, {label: 'D', value: 48}]} /></div>},
  ];
  const p2 = [
    {name: 'ConsoleWindow · 控制台介质', node: <ConsoleWindow x={0} y={20} w={800} f={F} title="api.deepseek.com" rows={[{text: 'POST /v1/chat  model="v4-pro"', tone: 'cmd'}, {text: 'gateway: match rule #14', tone: 'info'}, {text: '→ routed to v4.1-flash', tone: 'info'}, {text: '✓ 200 OK  billing=v4.1-flash', tone: 'ok'}]} status={{text: 'ROUTED', tone: 'ok'}} />},
    {name: 'MetricGrid · 指标网格', node: <MetricGrid x={0} y={30} w={840} f={F} cols={4} cellH={150} items={[{label: '性能', before: '1.00×', after: '1.42×', win: true}, {label: '费用', before: '¥1.00', after: '¥0.31', win: true}, {label: '速度', before: '2.1s', after: '0.9s', win: true}, {label: '总用时', before: '3.4s', after: '1.6s', win: true}]} />},
    {name: 'DiffView · 补丁介质', node: <DiffView x={0} y={30} w={780} frame={F} title="client.py" lines={[{k: ' ', text: 'client = OpenAI(base_url=...)', at: 0}, {k: '-', text: 'model = "v4-pro"', at: 0}, {k: '+', text: 'model = "v4.1-flash"', at: 8}, {k: ' ', text: '# 账单按 Flash 计费', at: 16}]} />},
    {name: 'Typewriter · 逐字介质', node: <div style={{width: 780}}><div style={{fontSize: 32, lineHeight: 1.5}}><Typewriter frame={F} start={0} cps={0.4} text="你调的还是 V4 Pro，实际跑的是 V4.1 Flash" /></div><div style={{marginTop: 22, fontSize: 24, color: C.muted}}><Typewriter frame={F} start={60} cps={0.5} cursor={false} text="按 Flash 单价计费，无需改代码" /></div></div>},
  ];
  const p3 = [
    {name: 'FitCard · 防出格卡片', node: <FitCard x={40} y={40} w={700} h={220} frame={F} pad={26}><div style={{fontSize: 30, fontWeight: 700}}>卡片高度由 fitH() 算出</div><div style={{fontSize: 23, color: C.muted, marginTop: 12}}>CardFitGate 渲染期抓出任何溢出</div></FitCard>},
    {name: 'Funnel · 漏斗介质', node: <Funnel x={0} y={20} w={800} frame={F} start={0} rows={[{label: '调用 v4-pro', sub: '请求', count: '10,000', color: C.blue, ratio: 1}, {label: '自动路由', sub: '网关', count: '10,000', color: C.orange, ratio: 1}, {label: '按 Flash 计费', sub: '账单', count: '-69%', color: C.green, ratio: 0.31}]} />},
    {name: 'SkeletonCard · 占位→内容', node: <SkeletonCard x={40} y={30} w={680} h={240} frame={F} start={0} revealAt={30}><div style={{fontSize: 28, fontWeight: 700}}>等待路由结果</div><div style={{fontSize: 22, color: C.muted, marginTop: 10}}>先占位，落定再 pop 出真内容</div></SkeletonCard>},
    {name: 'StampSeal · 印章', node: <div style={{position: 'relative', width: 840, height: 400}}><StampSeal text="已完成" x={20} y={20} frame={F} start={0} color={C.green} /><StampSeal text="按 Flash 计费" x={20} y={190} size={130} frame={F} start={0} color={C.red} /></div>},
    {name: 'FitTextBox · 中文反推字号（封装层）', node: <div style={{background: C.paper, border: `2.5px solid ${C.ink}`, borderRadius: 10, padding: 24, width: 800}}><FitTextBox text="给容器宽度和行数上限，反推该用多大字号，并返回断好的行——卡片文字被裁这件事从源头消失。" maxLines={3} boxWidth={748} maxFontSize={40} showMeasure /></div>},
  ];
  const p4 = [
    {name: 'ChatThread · 对话气泡', node: <div style={{position: 'relative', width: 840, height: 380}}><ChatThread x={0} y={10} w={620} frame={F} msgs={[{side: 'l', text: '还在用旧版？', at: 0}, {side: 'r', text: '已升级 v3.1', at: 20}, {side: 'l', text: '账单呢？', at: 40}]} /></div>},
    {name: 'PhaseRail · 阶段状态轨', node: <div style={{position: 'relative', width: 840, height: 400}}><div style={{position: 'absolute', left: 10, top: 20}}><PhaseRail phases={PHASES} ctx={railCtx} /></div></div>},
    {name: 'Tabs · Radix 标签页（封装层）', node: <div style={{transform: 'scale(0.6)'}}><Tabs f={F} startAt={0} step={30} width={1180} height={620} tabs={[{key: 'a', label: '标签一', title: '激活项由帧号决定', body: '内容随帧更替，不做 CSS 过渡。', points: [{mark: '01', text: '要点一'}, {mark: '02', text: '要点二'}], verdict: '验证通过', tone: 'green'}, {key: 'b', label: '标签二', title: '第二个面板', body: '面板下半用要点行填满。', points: [{mark: '01', text: '要点三'}, {mark: '02', text: '要点四'}], verdict: '验证通过', tone: 'gold'}]} /></div>},
  ];

  // ⑦⑧⑨ 修辞工具件（v3.0.1 从 index.tsx 迁出到 toolkit.tsx；此前接触表**一页都没有**，
  // 于是 11 个组件虽然能 import 了，却谁也没被渲染过——接触表是"看见才会用"的唯一入口。
  const p7 = [
    {name: 'Callout · 画圈标注', node: <div style={{position: 'relative', width: 840, height: 400}}>
      <div style={{position: 'absolute', left: 80, top: 150, width: 420, height: 80, borderRadius: 10, background: C.paper, border: `2px solid ${C.line}`, display: 'grid', placeItems: 'center', fontFamily: 'Space,Kai', fontSize: 26, fontWeight: 700, color: C.muted}}>(没有远程仓库，只有本地)</div>
      <Callout x={62} y={136} w={456} h={108} frame={F} start={0} text="圈住症结，旁边写字" />
    </div>},
    {name: 'Checklist · 带完成态的清单', node: <div style={{position: 'relative', width: 840, height: 400}}>
      <div style={{position: 'absolute', left: 60, top: 40, fontSize: 25, fontWeight: 700, color: C.muted}}>第一次参与的路径</div>
      <div style={{position: 'absolute', left: 60, top: 104}}>
        <Checklist items={['读懂项目规则', '找一个最小改动', '提交并等评审']} start={0} frame={F} stagger={8} done={2} rowH={64} fontSize={30} />
      </div>
    </div>},
    {name: 'Accordion · Radix 手风琴（封装层）', node: <div style={{transform: 'scale(0.6)'}}><Accordion f={F} startAt={0} step={30} width={1180} rowH={96} bodyRows={2} items={[{title: '展开/收起由帧号驱动', body: '状态机与 ARIA 语义来自 Radix；高度用 fitH 算出。', tone: 'blue'}, {title: '皮肤只读 THEME', body: '边框、圆角、硬偏移投影与 cel 皮肤一致。', tone: 'orange'}, {title: '可复现', body: '展开进度是帧号的纯函数。', tone: 'green'}]} /></div>},
  ];
  const p9 = [
    {name: 'JumpInText · 逐字跳入', node: <div style={{width: 820, textAlign: 'center'}}>
      <JumpInText items={[{text: '代码不该', color: C.ink}, {text: '只躺在硬盘里', color: C.ink}]} fontSize={66} start={0} stagger={1.3} frame={F} />
    </div>},
    {name: 'ShimmerText · 文字闪光（封装层）', node: <div style={{width: 820, textAlign: 'center'}}><ShimmerText f={F} text="库给结构，我们给皮肤" fontSize={64} /></div>},
    {name: 'GlowFrame · 流光边框（封装层）', node: <GlowFrame f={F} durationInFrames={300} width={620} height={330} tone={C.blue}><span style={{fontFamily: 'Kai,sans-serif', fontSize: 34, fontWeight: 700, color: C.ink}}>conic-gradient + 帧号</span></GlowFrame>},
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
          <Page title="⑧ 字效与效果" note="JumpInText / ShimmerText / GlowFrame"><Grid4 items={p9} /></Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="⑨ 封装层 · 结构件（src/components）" note={`${COMPONENTS_VERSION} · 库提供结构，本层提供皮肤与帧驱动`}>
            <div style={{position: 'absolute', left: 20, top: 76, width: 900, height: 470}}>
              <Tile name="Accordion · Radix 手风琴">
                <div style={{transform: 'scale(0.6)'}}>
                  <Accordion
                    f={F}
                    startAt={0}
                    step={30}
                    width={1180}
                    rowH={96}
                    bodyRows={2}
                    items={[
                      {title: '展开/收起由帧号驱动', body: '状态机、焦点管理、ARIA 语义来自 Radix；高度用 fitH 算出。', tone: 'blue'},
                      {title: '皮肤只读 THEME', body: '边框、圆角、硬偏移投影与 cel 皮肤天然一致。', tone: 'orange'},
                      {title: '可复现', body: '展开进度是帧号的纯函数，同一帧渲染多次结果一致。', tone: 'green'},
                    ]}
                  />
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 76, width: 900, height: 470}}>
              <Tile name="Tabs · Radix 标签页">
                <div style={{transform: 'scale(0.6)'}}>
                  <Tabs
                    f={F}
                    startAt={0}
                    step={30}
                    width={1180}
                    height={620}
                    tabs={[
                      {key: 'a', label: '标签一', title: '激活项由帧号决定', body: '内容随帧更替，不做 CSS 过渡。', points: [{mark: '01', text: '要点一'}, {mark: '02', text: '要点二'}], verdict: '验证通过', tone: 'green'},
                      {key: 'b', label: '标签二', title: '第二个面板', body: '切换时内容淡入 + 上浮。', points: [{mark: '01', text: '要点三'}, {mark: '02', text: '要点四'}], verdict: '验证通过', tone: 'gold'},
                      {key: 'c', label: '标签三', title: '第三个面板', body: '面板下半用要点行填满，不留空洞。', points: [{mark: '01', text: '要点五'}, {mark: '02', text: '要点六'}], verdict: '验证通过', tone: 'blue'},
                    ]}
                  />
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 20, top: 576, width: 900, height: 470}}>
              <Tile name="Chart · d3-scale + d3-shape">
                <div style={{transform: 'scale(0.72)'}}>
                  <Chart
                    f={F}
                    startAt={0}
                    width={1100}
                    height={560}
                    title="刻度由 d3 算，画还是我们画"
                    data={[
                      {label: 'v2.8', value: 2},
                      {label: 'v2.9', value: 9},
                      {label: 'v3.0.1', value: 27},
                      {label: 'v3.1', value: 39},
                    ]}
                  />
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 576, width: 900, height: 470}}>
              <Tile name="HighlightCode · react-syntax-highlighter">
                <div style={{transform: 'scale(0.62)'}}>
                  <HighlightCode
                    f={F}
                    startAt={0}
                    lineStep={12}
                    width={1180}
                    height={720}
                    language="tsx"
                    title="TSX · 语法高亮 + 行号 + 逐行聚焦"
                    code={'import {Accordion, Chart} from \'./components\';\n\n// 库给结构，我们给皮肤 + 帧驱动\nexport const Scene = ({f}) => (\n  <Accordion f={f} items={items} startAt={18} step={58} />\n);'}
                  />
                </div>
              </Tile>
            </div>
          </Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="⑩ 封装层 · 效果与几何" note={`${COMPONENTS_VERSION} · 流光/倾斜/描线/参数化图形/中文反推字号`}>
            <div style={{position: 'absolute', left: 20, top: 76, width: 900, height: 470}}>
              <Tile name="GlowFrame · 流光边框（零依赖）">
                <GlowFrame f={F} durationInFrames={300} width={620} height={330} tone={C.blue}>
                  <span style={{fontFamily: 'Kai,sans-serif', fontSize: 34, fontWeight: 700, color: C.ink}}>conic-gradient + 帧号</span>
                </GlowFrame>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 76, width: 900, height: 470}}>
              <Tile name="ShapeDraw · 参数化几何（@remotion/shapes）">
                <div style={{display: 'flex', gap: 26, alignItems: 'center'}}>
                  <ShapeDraw f={F} shape={SHAPES.star()} startAt={0} size={190} label="五角星" tone={C.gold} />
                  <ShapeDraw f={F} shape={SHAPES.hexagon()} startAt={0} size={190} label="六边形" tone={C.blue} />
                  <ShapeDraw f={F} shape={SHAPES.spark()} startAt={0} size={190} label="星芒" tone={C.red} />
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 20, top: 576, width: 900, height: 470}}>
              <Tile name="FitTextBox · 中文反推字号（治卡片裁切）">
                <div style={{background: C.paper, border: `2.5px solid ${C.ink}`, borderRadius: 10, padding: 26, width: 800}}>
                  <FitTextBox
                    text="给容器宽度和行数上限，反推该用多大字号，并返回断好的行——卡片文字被裁这件事从源头消失。"
                    maxLines={3}
                    boxWidth={748}
                    maxFontSize={40}
                    showMeasure
                  />
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 576, width: 900, height: 470}}>
              <Tile name="IconWall · react-icons（仅 fa + fi 两套）">
                <IconWall f={F} startAt={0} step={2} names={['react', 'node', 'python', 'docker', 'git', 'github', 'terminal', 'cpu', 'database', 'cloud']} columns={5} tile={150} gap={16} />
              </Tile>
            </div>
          </Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="⑪ 封装层 · 路径与几何" note={`${COMPONENTS_VERSION} · 描线生长 / 形状变形 / 饼图 / 转场`}>
            <div style={{position: 'absolute', left: 20, top: 76, width: 900, height: 470}}>
              <Tile name="PathDraw · 描线生长 + 沿线运动点">
                <PathDraw f={F} path="M 0 180 C 160 40, 300 320, 460 180 S 760 30, 900 180" startAt={0} durationInFrames={60} width={820} height={330} viewBox="-40 0 980 360" showDot strokeWidth={11} />
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 76, width: 900, height: 470}}>
              <Tile name="MorphShape · 形状连续变形（方 → 圆）">
                <MorphShape f={F} fromPath="M 120 90 L 400 90 L 400 330 L 120 330 Z" toPath="M 260 90 A 120 120 0 1 1 259.9 90 Z" startAt={0} durationInFrames={80} width={520} height={420} viewBox="80 50 360 320" tone={C.green} />
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 20, top: 576, width: 900, height: 470}}>
              <Tile name="PieDraw · 饼图（自带 progress）">
                <div style={{display: 'flex', gap: 40, alignItems: 'center'}}>
                  <PieDraw f={F} startAt={110} durationInFrames={200} radius={110} tone={C.blue} />
                  <PieDraw f={F} startAt={80} durationInFrames={200} radius={110} spin tone={C.orange} />
                  <PieDraw f={F} startAt={50} durationInFrames={200} radius={110} tone={C.green} />
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 576, width: 900, height: 470}}>
              <Tile name="SceneTransitions · 官方转场串联（4 段 / 3 转场）">
                <div style={{position: 'relative', width: 820, height: 400}}>
                  <SceneTransitions durations={[20, 20, 20, 20]} transition="wipe" transitionDuration={10} width={820} height={400} direction="from-left">
                    {[C.blue, C.orange, C.green, C.gold].map((tone, i) => (
                      <AbsoluteFill key={i} style={{alignItems: 'center', justifyContent: 'center'}}>
                        <div style={{width: 520, height: 300, background: tone, border: `2.5px solid ${C.ink}`, borderRadius: 12, boxShadow: THEME.paperShadow(0.5), display: 'grid', placeItems: 'center', fontFamily: 'Space,monospace', fontSize: 54, fontWeight: 700, color: C.white}}>
                          {i + 1}
                        </div>
                      </AbsoluteFill>
                    ))}
                  </SceneTransitions>
                </div>
              </Tile>
            </div>
          </Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="⑫ 封装层 · 效果件" note={`${COMPONENTS_VERSION} · 控件状态 / 抖动 / 擦除 / 题材图标`}>
            <div style={{position: 'absolute', left: 20, top: 76, width: 900, height: 470}}>
              <Tile name="ControlStack · 控件状态随旁白变化（Radix 六个纯受控 primitive）">
                <div style={{transform: 'scale(0.64)', transformOrigin: 'center'}}>
                  <ControlStack
                    f={F}
                    width={1320}
                    rowH={100}
                    gap={12}
                    startAt={0}
                    step={10}
                    items={[
                      {kind: 'switch', label: '自动路由', note: '按请求复杂度选模型', tone: 'green', steps: [{at: 0, value: false}, {at: 40, value: true}]},
                      {kind: 'checkbox', label: '记录用量', note: '写入账单明细', tone: 'blue', steps: [{at: 0, value: false}, {at: 52, value: true}]},
                      {kind: 'radio', label: '回退策略', tone: 'red', options: ['报错', '降级', '重试'], steps: [{at: 0, value: 2}, {at: 64, value: 1}]},
                      {kind: 'segment', label: '计费周期', tone: 'blue', options: ['按次', '按周', '按月'], steps: [{at: 0, value: 0}, {at: 76, value: 1}]},
                      {kind: 'slider', label: '采样温度', min: 0, max: 1, tone: 'orange', steps: [{at: 0, value: 0.2}, {at: 88, value: 0.72}]},
                      {kind: 'progress', label: '迁移进度', tone: 'gold', steps: [{at: 0, value: 12}, {at: 100, value: 86}]},
                    ]}
                  />
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 76, width: 900, height: 470}}>
              <Tile name="NoiseJitter · 有机抖动（同种子同结果）">
                <div style={{display: 'flex', gap: 34}}>
                  {[0, 1, 2].map((i) => (
                    <NoiseJitter key={i} f={F} seed={`tile${i}`} amplitude={16}>
                      <div style={{width: 190, height: 190, background: C.paper, border: `2.5px solid ${C.ink}`, borderRadius: 12, boxShadow: THEME.paperShadow(0.5), display: 'grid', placeItems: 'center', fontFamily: 'Space,monospace', fontSize: 34, fontWeight: 700, color: C.ink}}>
                        {i + 1}
                      </div>
                    </NoiseJitter>
                  ))}
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 20, top: 576, width: 900, height: 470}}>
              <Tile name="ClipReveal · 遮罩擦除（逐条揭示）">
                <div style={{display: 'flex', flexDirection: 'column', gap: 20}}>
                  {[C.blue, C.orange, C.green, C.gold].map((tone, i) => (
                    <ClipReveal key={i} f={F + 300} from={i * 14} durationInFrames={30} direction="left" style={{width: 720}}>
                      <div style={{height: 74, background: tone, border: `2.5px solid ${C.ink}`, borderRadius: 10, display: 'flex', alignItems: 'center', paddingLeft: 24, fontFamily: 'Kai,sans-serif', fontSize: 28, fontWeight: 700, color: C.white}}>
                        第 {i + 1} 条
                      </div>
                    </ClipReveal>
                  ))}
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 576, width: 900, height: 470}}>
              <Tile name="TopicIcon · 题材性图标（react-icons：fa 品牌 + fi/lu 线条）">
                <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 34}}>
                  {(['react', 'node', 'python', 'github', 'terminal', 'database', 'brain', 'rocket'] as const).map((n) => (
                    <div key={n} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12}}>
                      <TopicIcon name={n} size={76} />
                      <span style={{fontFamily: 'Space,monospace', fontSize: 17, color: C.muted}}>{n}</span>
                    </div>
                  ))}
                </div>
              </Tile>
            </div>
          </Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="⑬ 封装层 · 结构化数据 → 图形" note={`${COMPONENTS_VERSION} · d3-hierarchy / d3-geo / d3-sankey / qrcode`}>
            <div style={{position: 'absolute', left: 20, top: 76, width: 900, height: 470}}>
              <Tile name="TreeView · 目录树（d3-hierarchy）">
                <TreeView f={F} startAt={0} width={800} height={380} nodeW={116} nodeH={34}
                  data={{name: 'notebook-video', children: [
                    {name: 'components', children: [{name: 'ui'}, {name: 'chart'}, {name: 'data'}]},
                    {name: 'theme', children: [{name: 'paper'}, {name: 'cel'}]},
                    {name: 'references'},
                  ]}} />
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 76, width: 900, height: 470}}>
              <Tile name="GeoView · 地球 / 经纬网（d3-geo）">
                <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%'}}>
                  <GeoView f={F} width={400} height={400} spin={0.35} startAt={0} tone={C.blue} />
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 20, top: 576, width: 900, height: 470}}>
              <Tile name="SankeyChart · 流量图（d3-sankey）">
                <SankeyChart f={F} startAt={0} width={800} height={380}
                  nodes={[{name: '新进 Issue', tone: C.blue}, {name: '待办', tone: C.orange}, {name: '已合并', tone: C.green}, {name: '关闭', tone: C.muted}]}
                  links={[{source: 0, target: 1, value: 15}, {source: 0, target: 3, value: 9}, {source: 1, target: 2, value: 6}, {source: 1, target: 3, value: 9}]} />
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 576, width: 900, height: 470}}>
              <Tile name="QrCode · 二维码（qrcode）">
                <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%'}}>
                  <QrCode text="https://github.com/hyt315/notebook-video" size={230} label={'收尾放一个\n"扫码看仓库"\n纯计算、不联网'} />
                </div>
              </Tile>
            </div>
          </Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="⑭ 封装层 · 手绘风与公式" note={`${COMPONENTS_VERSION} · roughjs / katex / d3-dsv 入口`}>
            <div style={{position: 'absolute', left: 20, top: 76, width: 900, height: 470}}>
              <Tile name="SketchFx · 手绘风（roughjs）">
                <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%'}}>
                  <div style={{display: 'flex', flexDirection: 'column', gap: 22, alignItems: 'center'}}>
                    {/* roughjs 的填充 = 手账风的招牌质感（只有空心描边会显得单薄）。
                        这里只放**确定性**的四种：'dots' 的填充器内部**无条件调 Math.random()**
                        （实测同一帧渲三次得到三个哈希，差异全落在 dots 那一格），
                        已从 `SketchStyle.fillStyle` 里移除。 */}
                    <div style={{display: 'flex', gap: 24}}>
                      {([['hachure', C.gold], ['cross-hatch', C.blue], ['dashed', C.green], ['zigzag', C.orange]] as const).map(([fs, tone]) => (
                        <div key={fs} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6}}>
                          <SketchFx f={F} width={150} height={130} startAt={0} draw={[{kind: 'rect', x: 14, y: 12, w: 122, h: 104}]} style={{fill: `${tone}55`, fillStyle: fs, stroke: C.ink}} />
                          <span style={{fontFamily: 'Space,monospace', fontSize: 14, color: C.muted}}>{fs}</span>
                        </div>
                      ))}
                    </div>
                    <SketchFx f={F} width={620} height={190} stagger={8} startAt={20} draw={[
                      {kind: 'ellipse', cx: 300, cy: 95, w: 480, h: 130},
                      {kind: 'line', x1: 60, y1: 168, x2: 560, y2: 172},
                    ]} style={{stroke: C.orange}} />
                  </div>
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 76, width: 900, height: 470}}>
              <Tile name="MathBlock · 数学公式（katex）">
                <div style={{display: 'flex', flexDirection: 'column', gap: 16, alignItems: 'center', justifyContent: 'center', height: '100%'}}>
                  <MathBlock f={F} startAt={0} tex={'\\int_0^\\infty e^{-x^2}\\,dx = \\frac{\\sqrt{\\pi}}{2}'} fontSize={44} />
                  <MathBlock f={F} startAt={20} tex={'O(n\\log n) \\ll O(n^2)'} fontSize={34} tone={C.blue} />
                  <MathBlock f={F} startAt={40} tex={'\\text{准确率} = \\frac{TP+TN}{TP+TN+FP+FN}'} fontSize={26} tone={C.green} />
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 20, top: 576, width: 900, height: 470}}>
              <Tile name="Chart · 直接喂 CSV（d3-dsv）">
                <div style={{transform: 'scale(0.78)'}}>
                  <Chart f={F} startAt={0} width={1000} height={520} title="真实数据直接进图表"
                    csv={'阶段,数量\n新进,24\n分流,9\n已合并,6\n已关闭,3'} />
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 576, width: 900, height: 470}}>
              <Tile name="budoux · 中文词组边界（辅助，非保证）">
                <div style={{display: 'flex', gap: 26, alignItems: 'flex-start'}}>
                  <div style={{background: C.paper, border: `2.5px solid ${C.ink}`, borderRadius: 10, padding: 22, width: 400}}>
                    <div style={{fontFamily: 'Space,monospace', fontSize: 15, color: C.green, marginBottom: 8}}>断行优先落 budoux 边界</div>
                    <FitTextBox text="给容器宽度和行数上限反推该用多大字号并返回断好的行" maxLines={3} boxWidth={356} maxFontSize={30} />
                  </div>
                  <div style={{fontFamily: 'Kai,sans-serif', fontSize: 19, color: C.ink, lineHeight: 1.7, maxWidth: 320}}>
                    断行现在优先落在 budoux 给的
                    <span style={{color: C.blue}}>词组边界</span>
                    上。<br />
                    <span style={{color: C.orange, fontWeight: 700}}>但它是辅助不是保证</span>
                    ——实测它对"反推"「并返回」也会切错，模型本身不够准。所以：标题可以依赖，正文别指望。
                  </div>
                </div>
              </Tile>
            </div>
          </Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="⑮ 封装层 · 图表变体（d3-shape 62 个导出，此前只用了 2 个）" note={`${COMPONENTS_VERSION} · 同一个 Chart，换 variant：面积 / 百分比堆叠 / 雷达 / 饼图`}>
            <div style={{position: 'absolute', left: 20, top: 76, width: 900, height: 470}}>
              <Tile name="Chart variant=area · 面积图（份额随时间）">
                <div style={{transform: 'scale(0.66)'}}>
                  <Chart f={F} variant="area" startAt={0} width={1300} height={600} title="面积图：趋势 + 体量一起看" unit="k"
                    data={[{label: 'Q1', value: 12}, {label: 'Q2', value: 28}, {label: 'Q3', value: 44}, {label: 'Q4', value: 61}]} />
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 76, width: 900, height: 470}}>
              <Tile name="Chart variant=stackExpand · 百分比堆叠">
                <div style={{transform: 'scale(0.66)'}}>
                  <Chart f={F} variant="stackExpand" startAt={0} width={1300} height={600} title="百分比堆叠：结构怎么变"
                    labels={['v2.8', 'v2.9', 'v3.0', 'v3.1']}
                    series={[
                      {name: '结构件', values: [4, 6, 9, 12]},
                      {name: '表意件', values: [9, 12, 13, 12]},
                      {name: '引擎件', values: [3, 4, 5, 6]},
                    ]} />
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 20, top: 576, width: 900, height: 470}}>
              <Tile name="Chart variant=radar · 雷达图（多维对比）">
                <div style={{transform: 'scale(0.68)'}}>
                  <Chart f={F} variant="radar" startAt={0} width={1240} height={640} title="雷达：四个维度的两种方案"
                    labels={['下载体积', '首次渲染', '可复现性', '组件覆盖']}
                    series={[
                      {name: '方案 A', values: [70, 55, 92, 60]},
                      {name: '方案 B', values: [45, 80, 88, 95], tone: C.orange},
                    ]} />
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 576, width: 900, height: 470}}>
              <Tile name="Chart variant=pie · 饼图 / 环形（面积 = 份额）">
                <div style={{transform: 'scale(0.7)'}}>
                  <Chart f={F} variant="pie" startAt={0} width={1220} height={580} title="份额：门禁拦住的问题分布"
                    labels={['构图', '帧参数', '裁切', '其他']}
                    series={[{name: '构图与活性', values: [34]}, {name: '帧参数名', values: [22]}, {name: '文字裁切', values: [26]}, {name: '其他', values: [18]}]} />
                </div>
              </Tile>
            </div>
          </Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="⑯ 封装层 · 层级与关系（d3-hierarchy 18 个导出 + d3-force）" note={`${COMPONENTS_VERSION} · 面积=数值的三种图 + 谁连着谁的力导向布局`}>
            <div style={{position: 'absolute', left: 20, top: 76, width: 900, height: 470}}>
              <Tile name="TreeView variant=treemap · 矩形树图">
                <TreeView f={F} variant="treemap" startAt={0} width={830} height={400}
                  data={{name: '技能本体', children: [
                    {name: '封装组件层', children: [{name: '界面结构件', value: 6}, {name: '图表与图形', value: 5}, {name: '手绘与公式', value: 3}]},
                    {name: '门禁脚本', children: [{name: '构图与活性', value: 4}, {name: '帧参数名', value: 3}, {name: '负向抽查', value: 2}]},
                    {name: '参考资料', children: [{name: '依赖政策', value: 3}, {name: '介质路由', value: 2}]},
                    {name: '四套皮肤', children: [{name: '暖米纸', value: 2}, {name: '赛璐璐', value: 2}]},
                  ]}} />
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 76, width: 900, height: 470}}>
              <Tile name="TreeView variant=pack · 圆形打包 / 气泡">
                <TreeView f={F} variant="pack" startAt={0} width={830} height={400}
                  data={{name: '技能本体', children: [
                    {name: '封装组件层', children: [{name: '界面结构件', value: 6}, {name: '图表与图形', value: 5}]},
                    {name: '门禁脚本', children: [{name: '构图与活性', value: 4}, {name: '帧参数名', value: 3}, {name: '负向抽查', value: 2}]},
                    {name: '参考资料', children: [{name: '依赖政策', value: 3}, {name: '介质路由', value: 2}]},
                    {name: '皮肤', children: [{name: '暖米纸', value: 2}]},
                  ]}} />
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 20, top: 576, width: 900, height: 470}}>
              <Tile name="TreeView variant=sunburst · 旭日图（partition + arc）">
                <TreeView f={F} variant="sunburst" startAt={0} width={830} height={400}
                  data={{name: '根', children: [
                    {name: '封装层', children: [{name: '结构件', value: 6}, {name: '图形', value: 5}]},
                    {name: '门禁', children: [{name: '构图', value: 4}, {name: '帧参数', value: 3}]},
                    {name: '参考', children: [{name: '政策', value: 3}, {name: '路由', value: 2}]},
                    {name: '皮肤', children: [{name: '米纸', value: 2}, {name: '赛璐璐', value: 2}]},
                  ]}} />
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 576, width: 900, height: 470}}>
              <Tile name="NetworkGraph · 关系网（d3-force，固定迭代 + 显式初值）">
                <NetworkGraph f={F} startAt={0} width={830} height={420} nodeR={56}
                  nodes={[
                    {id: 'cli', label: '命令行'},
                    {id: 'srv', label: '服务端'},
                    {id: 'db', label: '数据库'},
                    {id: 'cache', label: '缓存'},
                    {id: 'queue', label: '任务队列'},
                    {id: 'worker', label: '工作进程'},
                  ]}
                  links={[
                    {source: 'cli', target: 'srv'}, {source: 'srv', target: 'db'},
                    {source: 'srv', target: 'cache'}, {source: 'srv', target: 'queue'},
                    {source: 'queue', target: 'worker'}, {source: 'worker', target: 'db'},
                  ]} />
              </Tile>
            </div>
          </Page>
        </Series.Sequence>
        <Series.Sequence durationInFrames={PAGE}>
          <Page title="⑰ 封装层 · 弹层与形状（Radix 弹层 + @remotion/shapes 余量）" note={`${COMPONENTS_VERSION} · Portal 的 container 指到画面根；引线朝向由 getTangentAtLength 给`}>
            <div style={{position: 'absolute', left: 20, top: 76, width: 900, height: 470}}>
              <Tile name="OverlayFrame · Dialog 与 DropdownMenu">
                <div style={{position: 'relative', width: 860, height: 430}}>
                  <OverlayFrame f={F} kind="dialog" x={24} y={20} width={420} tone={C.orange}
                    steps={[{at: 0, open: true}]} title="确认升级" body="把 model 改成 v4.1-flash？账单会按 Flash 单价计。"
                    confirm="确定" cancel="取消" />
                  <OverlayFrame f={F} kind="menu" x={480} y={20} width={330} tone={C.blue}
                    steps={[{at: 0, open: true}]} title="选择计费周期"
                    items={[{text: '按次计费'}, {text: '按周计费'}, {text: '按月计费'}]}
                    selected={[{at: 0, value: 1}, {at: 80, value: 2}]} />
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 76, width: 900, height: 470}}>
              <Tile name="OverlayFrame · Popover 与 Tooltip（引线指向锚点）">
                <div style={{position: 'relative', width: 860, height: 430}}>
                  <div style={{position: 'absolute', left: 60, top: 150, width: 220, height: 76, background: C.mutedFill, border: `2.5px solid ${C.ink}`, borderRadius: 10, display: 'grid', placeItems: 'center', fontFamily: 'Space,Kai,monospace', fontSize: 22}}>auto_route</div>
                  <OverlayFrame f={F} kind="popover" x={60} y={232} width={360} tone={C.green}
                    steps={[{at: 0, open: true}]} title="这是什么" body="打开后按请求复杂度自动选模型。" pointer={{dx: 110, dy: 0, side: 'top'}} />
                  <div style={{position: 'absolute', left: 560, top: 190, width: 220, height: 76, background: C.mutedFill, border: `2.5px solid ${C.ink}`, borderRadius: 10, display: 'grid', placeItems: 'center', fontFamily: 'Space,Kai,monospace', fontSize: 22}}>temperature</div>
                  <OverlayFrame f={F} kind="tooltip" x={560} y={272} width={280} tone={C.gold}
                    steps={[{at: 0, open: true}]} title="越低越稳" body="0.2 稳定，1.0 发散。" pointer={{dx: 110, dy: 0, side: 'top'}} />
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 20, top: 576, width: 900, height: 470}}>
              <Tile name="SHAPES · callout / arrow / heart（@remotion/shapes 22 个导出，此前用 5 个）">
                <div style={{display: 'flex', gap: 24, alignItems: 'center', justifyContent: 'center'}}>
                  <ShapeDraw f={F} shape={SHAPES.callout(300, 200, 70)} startAt={0} size={230} label="callout 标注框" tone={C.blue} />
                  <ShapeDraw f={F} shape={SHAPES.arrow(320)} startAt={0} size={230} label="arrow 箭头" tone={C.orange} />
                  <ShapeDraw f={F} shape={SHAPES.heart(230)} startAt={0} size={200} label="heart 心形" tone={C.red} />
                </div>
              </Tile>
            </div>
            <div style={{position: 'absolute', left: 970, top: 576, width: 900, height: 470}}>
              <Tile name="PathDraw showArrow · 沿线朝向（getTangentAtLength）">
                <PathDraw f={F} path="M 40 340 C 200 60, 400 380, 600 150 S 780 90, 800 240" startAt={0} durationInFrames={250}
                  width={830} height={400} viewBox="0 0 850 420" showArrow strokeWidth={11} />
              </Tile>
            </div>
          </Page>
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};

export const SHOWCASE_PAGES = 17;
export const SHOWCASE_VERSION = 'showcase-v8 · 17 pages · 26 件旧件 + 新封装层 9 页 + v3.1 新能力 3 页';
