const fs = require('node:fs');
const path = require('node:path');

const root = __dirname;
const pairs = [
  ['audio/narration.mp3', 'public/narration.mp3'],
  ['manifests/caption-cues.json', 'src/caption-cues.json'],
];
for (const [from, to] of pairs) {
  const source = path.join(root, from);
  const target = path.join(root, to);
  if (!fs.existsSync(source) || fs.statSync(source).size === 0) {
    throw new Error(`Required render input is missing or empty: ${source}`);
  }
  fs.mkdirSync(path.dirname(target), {recursive: true});
  fs.copyFileSync(source, target);
  if (!fs.readFileSync(source).equals(fs.readFileSync(target))) {
    throw new Error(`Render input sync failed: ${from} -> ${to}`);
  }
}
console.log('Synchronized canonical render inputs into public/ and src/.');
