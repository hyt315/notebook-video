// ============================================================================
// linework/library.ts · 内置线稿库（首批 30 个，3.5.0）
//
// 画法标准（references/linework.md）：轮廓剪影一眼认得出 → 加 1–2 个识别特征 → 停。
// 每个线稿 ≤10 个形；parts 是**外观分段**（火箭的一二级、房子的屋顶/墙），不是内部零件。
// 坐标统一在 0–100 的方框里；引擎按画面大小缩放。
// ============================================================================
import type {Fill, Prim, SketchDef} from './types';

const r = (x: number, y: number, w: number, h: number, rx = 0, fill: Fill = 'none'): Prim => ({k: 'rect', x, y, w, h, rx, fill});
const c = (cx: number, cy: number, rad: number, fill: Fill = 'none'): Prim => ({k: 'circle', cx, cy, r: rad, fill});
const l = (x1: number, y1: number, x2: number, y2: number): Prim => ({k: 'line', x1, y1, x2, y2});
const d = (path: string, fill: Fill = 'none'): Prim => ({k: 'path', d: path, fill});

export const SKETCHES: Record<string, SketchDef> = {
  rocket: {
    label: '运载火箭',
    fit: [33, 1, 34, 96],
    parts: {
      payload: {label: '卫星', anchor: [50, 13], detail: false,
        prims: [d('M50 2 C53.5 8 56 14 56 21 H44 C44 14 46.5 8 50 2 Z'),
                {k: 'circle', cx: 50, cy: 14, r: 3, fill: 'none'}]},
      stage2: {label: '第二级', anchor: [50, 30],
        prims: [d('M44 21 H56 V40 H44 Z'), l(44, 30.5, 56, 30.5)]},
      stage1: {label: '第一级', anchor: [50, 56],
        prims: [d('M44 40 H56 V68 L66 84 L56 79 V86 H44 V79 L34 84 L44 68 Z'),
                l(44, 68, 56, 68),
                d('M47 86 C48 90 49.2 93 50 96 C50.8 93 52 90 53 86 Z', 'accent')]},
    },
  },
  satellite: {
    label: '卫星',
    fit: [7, 28, 86, 32],
    parts: {
      body: {label: '星体', detail: true, prims: [r(42, 42, 16, 16, 2), d('M50 42 Q50 30 58 31')]},
      panelL: {label: '左翼', prims: [r(8, 44, 30, 12), l(18, 44, 18, 56), l(28, 44, 28, 56)]},
      panelR: {label: '右翼', prims: [r(62, 44, 30, 12), l(72, 44, 72, 56), l(82, 44, 82, 56)]},
    },
  },
  earth: {
    label: '地球',
    fit: [12, 12, 76, 76],
    parts: {
      globe: {label: '地球', prims: [c(50, 50, 32), d('M30 34 Q40 30 46 40 Q38 48 30 44 Z', 'wash'), d('M58 58 Q70 54 76 64 Q66 74 56 68 Z', 'wash')]},
      atmosphere: {label: '大气层', prims: [c(50, 50, 37)]},
    },
  },
  bulb: {
    label: '灯泡',
    fit: [27.6, 7, 44.8, 67],
    parts: {
      glass: {label: '灯泡', prims: [d('M50 8 A22 22 0 0 1 62 48 L58 58 H42 L38 48 A22 22 0 0 1 50 8 Z', 'wash')]},
      base: {label: '灯座', prims: [r(42, 58, 16, 10, 2), l(44, 68, 56, 68), l(45, 73, 55, 73)]},
      filament: {label: '灯丝', detail: true, prims: [d('M44 52 Q50 44 56 52')]},
    },
  },
  battery: {
    label: '电池',
    fit: [17, 29, 62, 42],
    parts: {
      body: {label: '电池', prims: [r(18, 30, 50, 40, 4), r(68, 40, 6, 20, 2)]},
      charge: {label: '电量', prims: [r(24, 50, 26, 8, 2, 'accent')]},
      terminal: {label: '电极', prims: [l(72, 44, 78, 44), l(72, 56, 78, 56)]},
    },
  },
  phone: {
    label: '手机',
    fit: [31, 7, 38, 86],
    parts: {
      body: {label: '手机', prims: [r(32, 8, 36, 84, 8)]},
      screen: {label: '屏幕', prims: [r(36, 14, 28, 64, 3, 'wash')]},
      button: {label: 'home 键', detail: true, prims: [c(50, 86, 3)]},
    },
  },
  laptop: {
    label: '笔记本电脑',
    fit: [15, 17, 70, 52],
    parts: {
      screen: {label: '屏幕', prims: [r(24, 18, 52, 36, 2), r(28, 22, 44, 28, 1, 'wash')]},
      base: {label: '键盘', prims: [d('M16 58 H84 L78 68 H22 Z', 'wash'), l(30, 62, 70, 62), r(44, 64, 12, 3)]},
    },
  },
  server: {
    label: '服务器',
    fit: [25, 11, 50, 78],
    parts: {
      rack: {label: '机柜', prims: [r(26, 12, 48, 76, 3)]},
      unit1: {label: '第一台', prims: [r(32, 18, 36, 14, 2, 'wash'), c(62, 25, 1.5)]},
      unit2: {label: '第二台', prims: [r(32, 36, 36, 14, 2), c(62, 43, 1.5)]},
      unit3: {label: '第三台', prims: [r(32, 54, 36, 14, 2), c(62, 61, 1.5)]},
    },
  },
  chip: {
    label: '芯片',
    fit: [29, 21, 42, 58],
    parts: {
      body: {label: '芯片', prims: [r(30, 30, 40, 40, 3, 'wash')]},
      pins: {label: '引脚', detail: true, prims: [l(34, 30, 34, 22), l(40, 30, 40, 22), l(46, 30, 46, 22), l(34, 70, 34, 78), l(40, 70, 40, 78), l(46, 70, 46, 78)]},
      core: {label: '核心', detail: true, prims: [r(42, 42, 16, 16, 2)]},
    },
  },
  cloud: {
    label: '云',
    fit: [19, 21, 62, 46],
    parts: {
      puffs: {label: '云', prims: [c(34, 50, 14, 'wash'), c(50, 40, 18, 'wash'), c(66, 50, 13, 'wash')]},
      base: {label: '云底', prims: [r(28, 50, 44, 16, 8)]},
    },
  },
  house: {
    label: '房子',
    fit: [13, 15, 74, 70],
    parts: {
      roof: {label: '屋顶', prims: [d('M14 46 L50 16 L86 46 Z', 'wash')]},
      body: {label: '墙', prims: [r(22, 46, 56, 38)]},
      door: {label: '门', prims: [r(44, 62, 12, 22)]},
      window: {label: '窗', detail: true, prims: [r(30, 54, 10, 10)]},
    },
  },
  car: {
    label: '汽车',
    fit: [11, 27, 78, 43],
    parts: {
      body: {label: '车身', prims: [d('M12 58 L18 44 Q22 38 34 38 H62 Q74 38 80 48 L88 58 Z', 'wash')]},
      cabin: {label: '车窗', prims: [d('M34 38 L40 28 H60 L68 38 Z')]},
      wheels: {label: '车轮', prims: [c(30, 62, 7), c(70, 62, 7)]},
    },
  },
  money: {
    label: '钞票',
    fit: [13, 31, 74, 40],
    parts: {
      note: {label: '纸币', prims: [r(14, 32, 72, 38, 3, 'wash'), r(20, 38, 60, 26, 2)]},
      mark: {label: '面额', detail: true, prims: [c(50, 51, 9), d('M50 45 V57 M46 48 H54 M46 54 H54')]},
    },
  },
  coin: {
    label: '硬币',
    fit: [19, 19, 62, 62],
    parts: {
      rim: {label: '硬币', prims: [c(50, 50, 30)]},
      face: {label: '币面', prims: [c(50, 50, 22, 'wash')]},
      slot: {label: '投币口', detail: true, prims: [r(46, 36, 8, 28, 4)]},
    },
  },
  cart: {
    label: '购物车',
    fit: [7, 21, 72, 53],
    parts: {
      basket: {label: '车筐', prims: [d('M22 34 H78 L70 58 H30 Z', 'wash')]},
      handle: {label: '把手', prims: [d('M22 34 L16 22 H8')]},
      wheels: {label: '轮子', prims: [c(34, 68, 5), c(64, 68, 5)]},
    },
  },
  wallet: {
    label: '钱包',
    fit: [17, 23, 74, 50],
    parts: {
      body: {label: '钱包', prims: [r(18, 32, 64, 40, 4)]},
      flap: {label: '翻盖', prims: [d('M18 32 H74 A8 8 0 0 1 82 40 V46 H18 Z', 'wash')]},
      card: {label: '卡', detail: true, prims: [r(26, 52, 24, 10, 1)]},
      button: {label: '扣', detail: true, prims: [c(70, 52, 3)]},
    },
  },
  person: {
    label: '人',
    fit: [33, 11, 34, 72],
    parts: {
      head: {label: '头', prims: [c(50, 22, 10)]},
      body: {label: '身体', prims: [r(44, 32, 12, 30, 6)]},
      arms: {label: '手臂', prims: [l(34, 42, 66, 42)]},
      legs: {label: '腿', prims: [l(50, 62, 40, 82), l(50, 62, 60, 82)]},
    },
  },
  crowd: {
    label: '人群',
    fit: [9, 17, 82, 68],
    parts: {
      one: {label: '第一个人', prims: [c(30, 30, 8), l(30, 38, 30, 64), l(22, 46, 38, 46)]},
      two: {label: '第二个人', prims: [c(50, 26, 9), l(50, 35, 50, 64), l(41, 44, 59, 44)]},
      three: {label: '第三个人', prims: [c(70, 30, 8), l(70, 38, 70, 64), l(62, 46, 78, 46)]},
      ground: {label: '地面', prims: [l(10, 84, 90, 84)]},
    },
  },
  bubble: {
    label: '对话气泡',
    fit: [11, 19, 78, 60],
    parts: {
      bubble: {label: '气泡', prims: [r(12, 20, 76, 44, 10, 'wash'), d('M34 64 L30 78 L46 64')]},
      line1: {label: '第一行', detail: true, prims: [l(24, 36, 76, 36)]},
      line2: {label: '第二行', detail: true, prims: [l(24, 48, 60, 48)]},
    },
  },
  book: {
    label: '书',
    fit: [19, 13, 62, 62],
    parts: {
      left: {label: '左页', prims: [d('M50 20 Q36 14 20 18 V72 Q36 68 50 74 Z', 'wash')]},
      right: {label: '右页', prims: [d('M50 20 Q64 14 80 18 V72 Q64 68 50 74 Z', 'wash')]},
      spine: {label: '书脊', detail: true, prims: [l(50, 20, 50, 74)]},
    },
  },
  notebook: {
    label: '笔记本',
    fit: [22, 13, 56, 78],
    parts: {
      cover: {label: '封面', prims: [r(26, 14, 48, 76, 4, 'wash')]},
      spiral: {label: '线圈', detail: true, prims: [c(26, 24, 3), c(26, 40, 3), c(26, 56, 3), c(26, 72, 3)]},
      lines: {label: '横线', detail: true, prims: [l(38, 32, 66, 32), l(38, 48, 66, 48), l(38, 64, 60, 64)]},
    },
  },
  calendar: {
    label: '日历',
    fit: [19, 13, 62, 72],
    parts: {
      body: {label: '日历', prims: [r(20, 22, 60, 62, 4)]},
      tabs: {label: '挂环', detail: true, prims: [r(32, 14, 6, 12, 2), r(62, 14, 6, 12, 2)]},
      header: {label: '月份', prims: [l(20, 40, 80, 40)]},
      dots: {label: '日期', detail: true, prims: [c(34, 52, 2), c(46, 52, 2), c(58, 52, 2), c(34, 64, 2), c(46, 64, 2)]},
    },
  },
  clock: {
    label: '钟表',
    fit: [17, 17, 66, 66],
    parts: {
      face: {label: '表盘', prims: [c(50, 50, 32), c(50, 50, 27, 'wash')]},
      hands: {label: '指针', detail: true, prims: [l(50, 50, 50, 30), l(50, 50, 64, 58)]},
      tick: {label: '刻度', detail: true, prims: [l(50, 20, 50, 24), l(80, 50, 76, 50), l(50, 80, 50, 76), l(20, 50, 24, 50)]},
    },
  },
  magnifier: {
    label: '放大镜',
    fit: [21, 19, 60, 60],
    parts: {
      lens: {label: '镜片', prims: [c(44, 42, 22), c(44, 42, 17, 'wash')]},
      handle: {label: '手柄', detail: true, prims: [l(60, 58, 80, 78)]},
    },
  },
  lock: {
    label: '锁',
    fit: [27, 19, 46, 66],
    parts: {
      body: {label: '锁体', prims: [r(28, 46, 44, 38, 4, 'wash')]},
      shackle: {label: '锁梁', prims: [d('M36 46 V34 A14 14 0 0 1 64 34 V46')]},
      keyhole: {label: '锁孔', detail: true, prims: [c(50, 60, 4), l(50, 64, 50, 72)]},
    },
  },
  key: {
    label: '钥匙',
    fit: [15, 35, 66, 30],
    parts: {
      bow: {label: '钥匙柄', prims: [c(30, 50, 14), c(30, 50, 6)]},
      shaft: {label: '钥匙杆', prims: [l(44, 50, 80, 50)]},
      teeth: {label: '齿', detail: true, prims: [l(70, 50, 70, 58), l(78, 50, 78, 56)]},
    },
  },
  file: {
    label: '文件',
    fit: [27, 11, 50, 78],
    parts: {
      page: {label: '纸', prims: [d('M28 12 H62 L76 26 V88 H28 Z', 'wash')]},
      fold: {label: '折角', detail: true, prims: [d('M62 12 V26 H76')]},
      lines: {label: '正文', detail: true, prims: [l(36, 42, 66, 42), l(36, 54, 66, 54), l(36, 66, 56, 66)]},
    },
  },
  mail: {
    label: '邮件',
    fit: [13, 29, 74, 46],
    parts: {
      envelope: {label: '信封', prims: [r(14, 30, 72, 44, 3, 'wash')]},
      flap: {label: '封口', prims: [d('M14 30 L50 58 L86 30')]},
      stamp: {label: '邮票', detail: true, prims: [r(66, 38, 10, 10, 1)]},
    },
  },
  factory: {
    label: '工厂',
    fit: [17, 5, 59, 76],
    parts: {
      building: {label: '厂房', prims: [d('M18 44 H50 V80 H18 Z', 'wash'), d('M18 44 L34 34 L50 44')]},
      chimney: {label: '烟囱', prims: [r(58, 24, 8, 56)]},
      smoke: {label: '烟', prims: [c(62, 18, 6), c(70, 11, 5)]},
      window: {label: '窗', prims: [r(24, 54, 8, 8)]},
    },
  },
  tree: {
    label: '树',
    fit: [18.7, 7, 66.7, 80],
    parts: {
      crown: {label: '树冠', prims: [d('M50 8 C62 8 72 18 72 30 C81 32 86 40 84 49 C82 58 73 63 64 61 C60 69 49 72 43 65 C35 69 25 63 25 53 C18 49 18 38 25 32 C25 20 38 8 50 8 Z', 'wash')]},
      trunk: {label: '树干', prims: [r(46, 60, 8, 24)]},
      ground: {label: '地面', prims: [l(24, 86, 76, 86)]},
    },
  },
  chiplog: {
    // 「节」那支片的主角：船尾抛出去的木板、绳上等距的结。
    // 三个 part 对应三个动作：船在走 / 绳在放 / 木板被水拖住——所以按 part 分段，不按零件分。
    label: '测速绳 · 木板与结',
    fit: [0, 0, 100, 82],
    parts: {
      hull: {label: '船尾', anchor: [86, 14], fit: [62, 0, 38, 34], prims: [d('M68 6 L100 2 L100 26 C92 31 84 31 76 26 Z', 'wash'), l(72, 10, 96, 7)]},
      line: {label: '绳与结', anchor: [48, 44], fit: [22, 22, 60, 38], prims: [d('M78 26 C62 40 44 46 26 58'),
                                                       c(69, 34, 2.2, 'accent'), c(60, 40, 2.2, 'accent'),
                                                       c(50, 45, 2.2, 'accent'), c(39, 51, 2.2, 'accent')]},
      plank: {label: '木板与水面', anchor: [20, 63], fit: [0, 48, 38, 32], prims: [d('M12 56 L30 54 L31 60 L13 62 Z', 'wash'),
                                                          d('M6 68 C12 65 18 71 25 67'), d('M4 74 C11 71 17 77 24 73')]},
    },
  },
};

export const SKETCH_NAMES = Object.keys(SKETCHES);
