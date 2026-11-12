<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Live subtitles — stage</title>
<style>
:root { --font-size: 52px; --bottom: 5vh; }
* { box-sizing: border-box; }
html, body { height:100%; margin:0; background:#000; overflow:hidden; }
body.transparent { background:transparent; }
#caption { position:fixed; bottom:var(--bottom); left:4vw; right:4vw;
 display:none; text-align:center; color:white; font:600 var(--font-size)/1.25 Arial,sans-serif;
 text-shadow:0 2px 10px rgba(0,0,0,.95); overflow-wrap:anywhere; }
#caption span { display:inline; padding: .12em .35em; background:rgba(0,0,0,.82);
 box-decoration-break:clone; -webkit-box-decoration-break:clone; }
body.transparent #caption span { background:rgba(0,0,0,.68); }
</style></head>
<body><div id="caption" role="status" aria-live="polite"><span id="text"></span></div>
<script>
const params = new URLSearchParams(location.search);
if (params.get('transparent') === '1') document.body.classList.add('transparent');
const font = Math.max(20, Math.min(120, Number(params.get('size')) || 52));
document.documentElement.style.setProperty('--font-size', font + 'px');
const bottom = Math.max(0, Math.min(40, Number(params.get('bottom')) || 5));
document.documentElement.style.setProperty('--bottom', bottom + 'vh');
const caption = document.getElementById('caption');
const content = document.getElementById('text');
let lastSeq = -1, lastOk = Date.now();
async function refresh() {
  try {
    const response = await fetch('/api/state', {cache:'no-store'});
    if (!response.ok) throw new Error('Offline');
    const state = await response.json();
    lastOk = Date.now();
    if (state.sequence !== lastSeq) {
      lastSeq = state.sequence;
      content.textContent = state.text || '';
      caption.style.display = state.visible && state.text ? 'block' : 'none';
    }
  } catch (_) {
    if (Date.now() - lastOk > 5000) caption.style.display = 'none';
  }
}
refresh();
setInterval(refresh, 300);
</script></body></html>
