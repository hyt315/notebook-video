import {Composition, registerRoot} from 'remotion';
import CONTRACT from './contract.json';
import {THEME} from './theme/active';
import {AssetGate, FontFaces} from './fonts';
import {CanvasBoundsGate} from './canvas-bounds-gate';
import {Showcase, SHOWCASE_PAGES} from './showcase';
import {CraftSheet, CRAFT_SHEET_FRAMES} from './craft-sheet';

// 样张入口（`notebook-video showcase`）：组件接触表与 craft 样张单独打包，成片入口 index.tsx 不带它们的依赖。
// 只挂 CanvasBoundsGate，用 block（片子是 warn）：格子里的件被 Tile 的 overflow:hidden 裁住是有意的取景框，
// 越出画布则是件看不见或被切掉，接触表是「看见才会用」的入口（references/media.md#component-index），不能缺件。
const C = THEME.palette;
const ShowcaseComposition = () => <><FontFaces bg={C.paperBase} /><Showcase /><CanvasBoundsGate mode="block" /></>;
const CraftSheetComposition = () => <><FontFaces bg={C.paperBase} /><AssetGate /><CraftSheet /><CanvasBoundsGate mode="block" /></>;

registerRoot(() => <>
  {/* 接触表：每页 30 帧，抽每页第 6 / 21 帧拼 6×6 */}
  <Composition id="NotebookVideoShowcase" component={ShowcaseComposition} durationInFrames={SHOWCASE_PAGES * 30} fps={CONTRACT.FPS} width={1920} height={1080} />
  <Composition id="NotebookVideoCraftSheet" component={CraftSheetComposition} durationInFrames={CRAFT_SHEET_FRAMES} fps={CONTRACT.FPS} width={1920} height={1080} />
</>);
