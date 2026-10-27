/**
 * 一次性：生成 readable.txt / sentences.txt / auto_selected.json（静音）
 * 在项目 output 目录内运行: node _bootstrap_analysis.js
 */
const fs = require('fs');
const path = require('path');

const transDir = path.join(__dirname, '..', '1_转录');
const wordsPath = path.join(transDir, 'subtitles_words.json');
const data = JSON.parse(fs.readFileSync(wordsPath, 'utf8'));

// 5.1 readable
const readableLines = [];
data.forEach((w, i) => {
  if (w.isGap) {
    const dur = (w.end - w.start).toFixed(2);
    if (parseFloat(dur) >= 0.2) {
      readableLines.push(`${i}|[静${dur}s]|${w.start.toFixed(2)}-${w.end.toFixed(2)}`);
    }
  } else {
    readableLines.push(`${i}|${w.text}|${w.start.toFixed(2)}-${w.end.toFixed(2)}`);
  }
});
fs.writeFileSync(path.join(__dirname, 'readable.txt'), readableLines.join('\n'), 'utf8');

// 5.3 sentences
const sentences = [];
let curr = { text: '', startIdx: -1, endIdx: -1 };
data.forEach((w, i) => {
  const isLongGap = w.isGap && (w.end - w.start) >= 0.5;
  if (isLongGap) {
    if (curr.text.length > 0) sentences.push({ ...curr });
    curr = { text: '', startIdx: -1, endIdx: -1 };
  } else if (!w.isGap) {
    if (curr.startIdx === -1) curr.startIdx = i;
    curr.text += w.text;
    curr.endIdx = i;
  }
});
if (curr.text.length > 0) sentences.push(curr);
const sentLines = sentences.map((s, i) => `${i}|${s.startIdx}-${s.endIdx}|${s.text}`);
fs.writeFileSync(path.join(__dirname, 'sentences.txt'), sentLines.join('\n'), 'utf8');

// 5.4 静音预选
const selected = [];
data.forEach((w, i) => {
  if (w.isGap && (w.end - w.start) >= 0.2) selected.push(i);
});
fs.writeFileSync(path.join(__dirname, 'auto_selected.json'), JSON.stringify(selected, null, 2), 'utf8');

// 5.5 极简：相邻句首字相同≥5 → 整句 idx 并入（保守，可网页上再改）
function addRange(set, a, b) {
  for (let k = a; k <= b; k++) set.add(k);
}
const idxSet = new Set(selected);
for (let si = 0; si < sentences.length - 1; si++) {
  const A = sentences[si].text.replace(/\s/g, '');
  const B = sentences[si + 1].text.replace(/\s/g, '');
  if (A.length < 5 || B.length < 5) continue;
  const preA = A.slice(0, 5);
  const preB = B.slice(0, 5);
  if (preA === preB) {
    const shorter = A.length <= B.length ? si : si + 1;
    const s = sentences[shorter];
    addRange(idxSet, s.startIdx, s.endIdx);
  }
}
const merged = [...idxSet].sort((a, b) => a - b);
fs.writeFileSync(path.join(__dirname, 'auto_selected.json'), JSON.stringify(merged, null, 2), 'utf8');

let md = '# 口误分析（自动）\n\n';
md += `- 静音 ≥0.2s：${selected.length} 处\n`;
md += `- 相邻句首 5 字相同整句删除：已合并进 auto_selected\n`;
md += `- 更细口误请在审核页人工勾选\n`;
fs.writeFileSync(path.join(__dirname, '口误分析.md'), md, 'utf8');

console.log('readable.txt lines:', readableLines.length);
console.log('sentences:', sentences.length);
console.log('auto_selected count:', merged.length);
