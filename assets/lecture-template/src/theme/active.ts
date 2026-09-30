// 每个工程为全片选择一个连贯的基础视觉处理；new-project --style 会同步此入口与 shots.json。
// 可选值：./paper（默认） ./cel ./sticker ./flat；兼容的局部混合处理按内容克制使用。
// 注意：必须保持「先 import 再 export」两行形式，单行再导出在打包器下会失效。
import {THEME} from './paper';
export {THEME};
