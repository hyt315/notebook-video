// ============================================================================
// 定制画面注册表（3.2.0 的「逃生口」）
//
// 组件不是万能的：讲「请求怎么穿过缓存」时，最清楚的往往是一张为这个题目手画的图，
// 而不是硬套一个通用件。写法（照抄 RequestLane.tsx）：
//   1. 在本目录新建 MyVisual.tsx，导出 `const MyVisual: React.FC<CustomProps>`；
//   2. 在下面 CUSTOM 里注册；
//   3. story.json 里这一镜写 layout:"custom"，content.component:"MyVisual"，
//      content.elements 列出画面上能被台词点名的部件（id + 设计坐标 x/y/w/h + label）。
// 你得到的（不用自己写）：摄影机（关键词推近 / 视线连续 / 微漂移）、主题色板 C、
// 入场进度 el(id).in、关键词强调 el(id).hi、第 i 句的帧 line(i)、释义气泡、音效、全部门禁。
// 纪律：只用帧 f 驱动；文字 ≥ 32px；文字色用 C.*Ink / C.ink / C.muted；强调用底色+描边+加粗，不只靠颜色。
// ============================================================================
import type React from 'react';
import type {CustomProps} from '../auto';
import {RequestLane} from './RequestLane';

export const CUSTOM: Record<string, React.FC<CustomProps>> = {
  RequestLane,
};
