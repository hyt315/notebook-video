"""compose-story 行为锁：拆结构之前先把输出钉住。

`compose-story.py` 一个文件里同时做排版、字幕定时、相机、自动修。它只有
`test_reading_speed.py` 覆盖，而重构最怕的是"看起来一样、帧数差 2"——
那种偏差渲染一遍看不出来，上了成片才发现口型对不上。

这里拿 `examples/concept-hash-table.story.json` 跑一遍，把三份机器可读产物
（布局表 / 字幕 cues / 自修报告）跟快照逐字段比对：

- 只改结构、行为不变 → 本测试必须原样通过。
- 真要改行为 → 同时更新 `tests/fixtures/compose-golden/` 并在提交说明里讲清为什么。

为什么不用「重新渲染对比画面」当锁：太慢（整片 13 分钟），而且画面像素会被
墨迹噪声扰动，分辨不出「帧数错位」和「抖动不同」。JSON 是精确的。
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
STORY = SKILL / 'examples' / 'concept-hash-table.story.json'
GOLDEN = Path(__file__).resolve().parent / 'fixtures' / 'compose-golden'

# 产物相对路径 → 快照文件名（快照目录扁平存放，'/' 换成 '__'）
JSON_ARTIFACTS = {
    'report.json': 'report.json',
    'manifests/shots.json': 'manifests__shots.json',
    'manifests/caption-cues.json': 'manifests__caption-cues.json',
}

# 生成出来的源码与文本也逐字节锁住：`build()` 负责写它们，拆它时最容易
# 「JSON 一样、画面不一样」——场景文件里少一个 beat、相机少一个关键帧，都看不出来。
TEXT_ARTIFACTS = {
    'src/scenes.tsx': 'text__src_scenes.tsx',
    'src/film.ts': 'text__src_film.ts',
    'src/story.ts': 'text__src_story.ts',
    'manifests/semantic-caption-lines.txt': 'text__manifests_semantic-caption-lines.txt',
    'manifests/protected-caption-phrases.txt': 'text__manifests_protected-caption-phrases.txt',
}


def first_diff(want, got, path='$'):
    """返回第一处差异的可读描述；完全一致返回 None。"""
    if type(want) is not type(got):
        return f'{path}: 类型 {type(want).__name__} -> {type(got).__name__}'
    if isinstance(want, dict):
        if want.keys() != got.keys():
            missing = sorted(set(want) - set(got))
            extra = sorted(set(got) - set(want))
            return f'{path}: 键不同（少了 {missing[:4]} / 多了 {extra[:4]}）'
        for key in want:
            diff = first_diff(want[key], got[key], f'{path}.{key}')
            if diff:
                return diff
        return None
    if isinstance(want, list):
        if len(want) != len(got):
            return f'{path}: 长度 {len(want)} -> {len(got)}'
        for i, (a, b) in enumerate(zip(want, got)):
            diff = first_diff(a, b, f'{path}[{i}]')
            if diff:
                return diff
        return None
    if want != got:
        return f'{path}: {want!r} -> {got!r}'
    return None


class ComposeGoldenTest(unittest.TestCase):
    def test_output_matches_snapshot(self):
        if not STORY.is_file():
            self.skipTest(f'缺示例 story：{STORY}')

        with tempfile.TemporaryDirectory() as td:
            env = dict(os.environ, PYTHONIOENCODING='utf-8')
            result = subprocess.run(
                [sys.executable, str(SKILL / 'scripts' / 'compose-story.py'),
                 str(STORY), td, '--report', str(Path(td) / 'report.json')],
                capture_output=True, text=True, encoding='utf-8', errors='ignore', env=env,
            )
            self.assertEqual(result.returncode, 0,
                             f'compose-story 退出码 {result.returncode}\n{result.stderr[-800:]}')

            for rel, snapshot in JSON_ARTIFACTS.items():
                path = Path(td) / rel
                self.assertTrue(path.is_file(), f'没有产出 {rel}')
                got = json.loads(path.read_text(encoding='utf-8'))
                want = json.loads((GOLDEN / snapshot).read_text(encoding='utf-8'))
                diff = first_diff(want, got)
                self.assertIsNone(
                    diff,
                    f'{rel} 与快照不一致（第一处差异）：{diff}\n'
                    f'若这是有意的行为变更，请同时更新 tests/fixtures/compose-golden/{snapshot}',
                )

            for rel, snapshot in TEXT_ARTIFACTS.items():
                path = Path(td) / rel
                self.assertTrue(path.is_file(), f'没有产出 {rel}')
                got = path.read_text(encoding='utf-8')
                want = (GOLDEN / snapshot).read_text(encoding='utf-8')
                if got == want:
                    continue
                # 逐行定位第一处差异，比整段 diff 好读
                got_lines, want_lines = got.split('\n'), want.split('\n')
                where = next((i for i, (a, b) in enumerate(zip(want_lines, got_lines)) if a != b),
                             min(len(want_lines), len(got_lines)))
                self.fail(
                    f'{rel} 第 {where + 1} 行开始与快照不同：\n'
                    f'  期望：{want_lines[where] if where < len(want_lines) else "<文件结束>"}\n'
                    f'  实际：{got_lines[where] if where < len(got_lines) else "<文件结束>"}\n'
                    f'若这是有意的行为变更，请同时更新 tests/fixtures/compose-golden/{snapshot}',
                )


if __name__ == '__main__':
    unittest.main()
