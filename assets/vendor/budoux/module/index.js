/**
 * @license
 * Copyright 2021 Google LLC
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// 精简入口 —— 不是上游 module/index.js 的副本。
//
// 上游的 `loadDefaultSimplifiedChineseParser()` 返回的是 `HTMLProcessingParser`，它经
// `html_processor.js` → `dom.js` → `linkedom` 才能加载。本仓库只用它给**纯文本**做分词
// （字幕断句检查），走不到 DOM，却要为此额外 vendor 几 MB 的 linkedom。
//
// 所以这里直接组装上游的 `Parser` + 简体中文模型。上游 `parser.js` 与
// `data/models/zh-hans.js` 都是原样复制的，没有改动。
//
// 行为等价性不是猜的：对 cell 工程旁的 5 条真实字幕，`new Parser(model).parse(t)` 与
// `new HTMLProcessingParser(model).parse(t)` 输出逐字节相同。若将来要处理带 HTML 标签的
// 输入，这个入口不够用，得回到完整的 `node_modules/budoux`。
//
// 升级方式见同目录上一级的 README.md。

import {model} from './data/models/zh-hans.js';
import {Parser} from './parser.js';

const simplifiedChineseParser = new Parser(model);

/** 与上游同名同签名，方便调用方无感切换。 */
export const loadDefaultSimplifiedChineseParser = () => simplifiedChineseParser;

export {Parser};
export {model as zhHansModel};
