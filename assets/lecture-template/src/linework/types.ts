// ============================================================================
// linework/types.ts · 线稿层的轻量数据结构（3.5.0）
//
// 一条线稿 = 一个 0–100 的方框 + 若干「部位」。每个部位是一小组基本形
// （path / rect / circle / line）。引擎负责缩放、描出、强调、脱落、换态、复制、打标。
// 纪律（references/linework.md）：轮廓剪影一眼认得出 → 加 1–2 个识别特征 → 停。
// 单个线稿 ≤10 个形；不画剖面、内部结构、零件拆解。
// ============================================================================

export type Fill = 'none' | 'wash' | 'ink' | 'accent' | 'paper';

export type Prim =
  | {k: 'path'; d: string; fill?: Fill; sw?: number}
  | {k: 'rect'; x: number; y: number; w: number; h: number; rx?: number; fill?: Fill; sw?: number}
  | {k: 'circle'; cx: number; cy: number; r: number; fill?: Fill; sw?: number}
  | {k: 'line'; x1: number; y1: number; x2: number; y2: number; sw?: number};

export type SketchPart = {
  /** 被点名时手写标注用的名字（「第一级」），不是内部零件名 */
  label: string;
  prims: Prim[];
  /** swap 的另一态（满→空、贵→便宜）。没写就只是换色 */
  alt?: Prim[];
  /** 引线落点（0–100）；不写就取部位包围盒中心 */
  anchor?: [number, number];
  /** 细节件（窗、按钮、指示灯）：线更细、颜色偏暖灰（三档线的第三档） */
  detail?: boolean;
  /** 单部位特写时的取景框；不写就沿用整图 fit（多部位组合也始终用整图 fit）。 */
  fit?: [number, number, number, number];
};

export type SketchDef = {
  label: string;
  /** 内容包围盒 [x,y,w,h]（0–100）。引擎拿它当 viewBox，线稿就会填满方框而不是缩在一角。 */
  fit?: [number, number, number, number];
  parts: Record<string, SketchPart>;
  /** 可选装饰（火焰、地面线），不参与点名/脱落 */
  base?: Prim[];
};

export type SketchAct = {
  at: number;
  do: 'enter' | 'point' | 'drop' | 'swap' | 'count' | 'mark' | 'exit';
  target?: string;
  /** count 的份数 */
  n?: number;
  /** mark 的形状 */
  mark?: 'check' | 'cross' | 'circle';
  /** point 时显示的手写小字；缺省用 part.label */
  text?: string;
};

export type SketchSpec = {
  id: string;
  draw: string;            // lib:<名字> | shapes:[...] | trace:<media id>
  label?: string;
  /** Record = point 标注的自定义名；string[] = 只画这些部位（墨图页用）。两种含义不能混在一个结构里。 */
  parts?: Record<string, string> | string[];
  acts?: Array<{at: string | number; do: SketchAct['do']; target?: string; n?: number; mark?: SketchAct['mark']; text?: string}>;
  place?: 'left' | 'right' | 'center' | 'corner';
  keep?: boolean;
  /** compose 填的：本镜内的绝对帧 */
  frames?: SketchAct[];
  /** compose 填的：上一镜 keep 下来的线稿（已入场） */
  persist?: boolean;
};
