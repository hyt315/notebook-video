// ============================================================================
// external-types.d.ts — 两个「没有自带类型」的依赖的本地声明
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
