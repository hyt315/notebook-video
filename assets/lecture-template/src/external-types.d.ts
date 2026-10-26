// ============================================================================
// external-types.d.ts — 「没有自带类型」的依赖的本地声明（world-atlas / topojson-client / flubber）
//
// 为什么手写而不是装 @types：
//   · `world-atlas` 是纯数据包（只发 JSON，无 main / 无 types）；
//     `topojson-client` 也没有自带 .d.ts。两者都是 ISC，登记在
//     references/dependency-policy.md §4.2。
//   · 本技能只放行了这两个包，**不再加 `@types/topojson-client`**——那是第三个包。
//   · `GeoJSON.*` 命名空间来自 `@types/geojson`，它是已声明的 `@types/d3-geo` 的
//     传递依赖（`{"@types/geojson":"*"}`），不额外装东西；d3-geo 自己的类型也是 import 它。
//
// 覆盖范围 = 本仓库真正用到的符号，不多写：`Topology` / `feature`。
// 将来真要用 `mesh` / `quantize` 再补声明，不要凭想象一次写全（写了没人用的类型 = 谎言）。
// ============================================================================
declare module 'world-atlas/land-110m.json' {
  import type {Topology} from 'topojson-client';
  const topology: Topology;
  export default topology;
}

declare module 'topojson-client' {
  import type {Feature, FeatureCollection} from 'geojson';

  /** TopoJSON 的几何对象。本仓库只用到 GeometryCollection（land-110m.json 的 objects.land 就是它）。 */
  export type TopoObject = {type: string; [key: string]: unknown};

  export interface Topology {
    type: 'Topology';
    objects: Record<string, TopoObject>;
    arcs: number[][][];
    bbox?: [number, number, number, number];
    transform?: {scale: [number, number]; translate: [number, number]};
  }

  /**
   * TopoJSON → GeoJSON。传 GeometryCollection 得 FeatureCollection，
   * 传单个几何得 Feature。返回的是**新对象**，不修改入参。
   */
  export function feature(topology: Topology, object: TopoObject): Feature | FeatureCollection;
}

// flubber（MIT）没有自带类型。只声明本仓库用到的 `interpolate`（MorphShape）。
declare module 'flubber' {
  export function interpolate(
    fromShape: string | [number, number][],
    toShape: string | [number, number][],
    options?: {maxSegmentLength?: number; string?: boolean}
  ): (t: number) => string;
}

// 3.3.0：opentype.js 2.x（MIT）不自带类型。只声明 craft/ink.tsx 的 HandLettering 用到的符号。
declare module 'opentype.js' {
  export interface PathCommand {type: 'M' | 'L' | 'Q' | 'C' | 'Z'; x?: number; y?: number; x1?: number; y1?: number; x2?: number; y2?: number}
  // toPathData 不再使用（2.0.0 的取整在浮点残差上会产出 NaN，见 craft/ink.tsx 的 glyphPathD）
  export interface Path {commands: PathCommand[]; toPathData(decimalPlaces?: number): string}
  export interface Font {
    getPath(text: string, x: number, y: number, fontSize: number): Path;
    getAdvanceWidth(text: string, fontSize: number): number;
  }
  export function parse(buffer: ArrayBuffer): Font;
}
