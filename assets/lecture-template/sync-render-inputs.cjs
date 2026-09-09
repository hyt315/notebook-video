const fs = require('node:fs');
const path = require('node:path');
const root = __dirname;
const pairs = [
  ['audio/narration.mp3', 'public/narration.mp3'],
  ['manifests/caption-cues.json', 'src/caption-cues.json'],
];
for (const rel of [...pairs.map(([from]) => from), 'audio/narration.mp3.json']) {
  const source = path.join(root, rel);
  if (!fs.existsSync(source) || !fs.statSync(source).isFile() || fs.statSync(source).size === 0) {
    throw new Error(`Required render input is missing or empty: ${source}`);
  }
}
for (const [from, to] of pairs) {
  const source = path.join(root, from), target = path.join(root, to);
  const data = fs.readFileSync(source);
  fs.mkdirSync(path.dirname(target), {recursive: true});
  if (!fs.existsSync(target) || !data.equals(fs.readFileSync(target))) fs.writeFileSync(target, data);
  if (!data.equals(fs.readFileSync(target))) throw new Error(`Render input sync failed: ${from} -> ${to}`);
}
console.log('Synchronized canonical render inputs. Run validate-project before final delivery.');
