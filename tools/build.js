// Сборка сайта: node tools/build.js [папка_вывода]
// Берёт data/words.json и tools/template.html, встраивает шрифты и пишет index.html, sw.js, manifest.json, иконки.
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');
const outDir = path.resolve(process.argv[2] || root);
const data = fs.readFileSync(path.join(root, 'data', 'words.json'), 'utf8');

// шрифты: только кириллица и латиница (цифры, знаки), встроены в страницу — работает без сети
function fontCss(pkg, family, subsets) {
  const dir = path.dirname(require.resolve(pkg + '/package.json'));
  const css = fs.readFileSync(path.join(dir, 'wght.css'), 'utf8');
  return css.split('/*').slice(1).map(block => {
    const name = block.slice(0, block.indexOf('*/')).trim();
    if (!subsets.some(s => name.endsWith(`-${s}-wght-normal`) && !name.includes(`-ext-`) || name.endsWith(`${family.toLowerCase().replace(/ /g, '-')}-${s}-wght-normal`))) return '';
    const weight = block.match(/font-weight:\s*([^;]+);/)[1], range = block.match(/unicode-range:\s*([^;]+);/)[1];
    const file = block.match(/url\(\.\/files\/([^)]+\.woff2)\)/)[1];
    const b64 = fs.readFileSync(path.join(dir, 'files', file)).toString('base64');
    return `@font-face{font-family:"${family}";font-style:normal;font-display:swap;font-weight:${weight};src:url(data:font/woff2;base64,${b64}) format("woff2");unicode-range:${range}}`;
  }).join('\n');
}
const fonts = [
  fontCss('@fontsource-variable/golos-text', 'Golos Text', ['cyrillic', 'latin']),
  fontCss('@fontsource-variable/literata', 'Literata', ['cyrillic']),
].join('\n');

let html = fs.readFileSync(path.join(__dirname, 'template.html'), 'utf8')
  .replace('/*FONTS*/', () => fonts)
  .replace('/*DATA*/', () => data.trim().replace(/<\//g, '<\\/'));
fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, 'index.html'), html);

const ver = Date.now().toString(36);
fs.writeFileSync(path.join(outDir, 'sw.js'), `const C='egeru-${ver}';const F=['./','index.html','manifest.json','icon-192.png','icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(F)));self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))));self.clients.claim();});
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(C).then(c=>c.put(e.request,cp));return r;}).catch(()=>caches.match(e.request,{ignoreSearch:true})));});
`);
fs.writeFileSync(path.join(outDir, 'manifest.json'), JSON.stringify({
  name: 'Запоминалка: русский язык, ЕГЭ', short_name: 'Запоминалка', lang: 'ru', start_url: './', scope: './', display: 'standalone',
  background_color: '#ffffff', theme_color: '#ffffff',
  icons: [{ src: 'icon-192.png', sizes: '192x192', type: 'image/png' }, { src: 'icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' }],
}, null, 2));

// иконка: буква «а» со знаком ударения
const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" fill="#15171c"/>
<text x="256" y="372" font-family="DejaVu Serif, Georgia, serif" font-size="300" fill="#fff" text-anchor="middle">а</text>
<rect x="262" y="88" width="26" height="78" rx="12" fill="#8a9bff" transform="rotate(24 275 166)"/></svg>`;
(async () => {
  let sharp; try { sharp = require('sharp'); } catch (e) {}
  if (sharp) for (const s of [192, 512]) await sharp(Buffer.from(svg)).resize(s, s).png().toFile(path.join(outDir, `icon-${s}.png`));
  else console.warn('sharp не установлен — иконки не пересобраны');
  console.log(`готово: ${path.join(outDir, 'index.html')} (${(html.length / 1024).toFixed(0)} КБ)`);
})();
