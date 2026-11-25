"""EGG motion identity — "Gold Glitch Noir": a luxury live-data terminal.

Every video scene is the same HTML the renderer already builds, brought to life frame by frame in a real browser:
  depth   five layers that move at different speeds: the painted art (slow push-in), a gold perspective grid floor
          running toward the camera, floating gold particles (big = close = fast), the 3D content stage that sways,
          and a HUD in front (corner brackets, live-feed tag, scene progress line)
  data    the numbers are the hero: percentages count up, bars fill, shirts fly in and lock, words rise in 3D
  brand   a gold glitch on every cut, an intro sting ("EGG") and an outro that says who we are and asks to follow

Deterministic (time is set, not played), so every frame is sharp and the length matches the voice exactly.
    REDES_MOVIMIENTO=0   back to the flat video     REDES_FPS=30   smoother (24 by default, lighter)
"""
from __future__ import annotations

import os
import shutil

FPS = int(os.environ.get("REDES_FPS", "24"))

ENGINE = r"""
<style>
.m-grid{position:absolute;left:-30%;right:-30%;bottom:-6%;height:46%;transform:perspective(900px) rotateX(74deg);transform-origin:50% 100%;
 background-image:linear-gradient(rgba(212,175,55,.55) 2px,transparent 2px),linear-gradient(90deg,rgba(212,175,55,.40) 2px,transparent 2px);
 background-size:120px 120px;opacity:.16;-webkit-mask-image:linear-gradient(0deg,#000 10%,transparent 85%);mask-image:linear-gradient(0deg,#000 10%,transparent 85%);pointer-events:none}
.m-p{position:absolute;border-radius:50%;background:radial-gradient(circle,#ffe7a3 0%,#d4af37 40%,rgba(212,175,55,0) 70%);pointer-events:none}
.m-sweep{position:absolute;top:-20%;height:140%;width:260px;background:linear-gradient(90deg,transparent,rgba(255,231,163,.10),transparent);transform:rotate(14deg);pointer-events:none;mix-blend-mode:screen}
.m-scan{position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.025) 0 2px,transparent 2px 5px);pointer-events:none}
.m-br{position:absolute;width:86px;height:86px;border-color:#d4af37;border-style:solid;opacity:.85;pointer-events:none}
.m-tag{position:absolute;right:66px;top:150px;font-family:'JetBrains Mono',monospace;font-size:22px;letter-spacing:.18em;color:#d4af37;opacity:.9}
.m-tag i{display:inline-block;width:12px;height:12px;border-radius:50%;background:#ff3b5c;margin-right:10px;vertical-align:1px;box-shadow:0 0 14px #ff3b5c}
.m-prog{position:absolute;left:66px;right:66px;bottom:46px;height:4px;background:rgba(212,175,55,.18);border-radius:9px;overflow:hidden}
.m-prog b{display:block;height:100%;background:linear-gradient(90deg,#a77c18,#ffe7a3);transform-origin:0 50%}
.m-w{display:inline-block;transform-origin:50% 100%;backface-visibility:hidden}
.wrap{perspective:1700px}
.m-story{position:absolute;left:40px;right:40px;top:22px;display:flex;gap:8px;z-index:9}
.m-story i{flex:1;height:7px;border-radius:9px;background:rgba(255,255,255,.28);overflow:hidden}
.m-story i b{display:block;height:100%;background:#ffe7a3;transform-origin:0 50%}
body.l-diario .m-story i,body.l-cuaderno .m-story i,body.l-album .m-story i{background:rgba(0,0,0,.18)}
body.l-diario .m-story i b,body.l-cuaderno .m-story i b{background:#15120d}
.m-foil{position:absolute;z-index:8;border-radius:22px;background:linear-gradient(115deg,#8a6a1c,#f8e6a0 22%,#b8902a 40%,#fff3c4 55%,#9c7a22 72%,#e8cf7a);
 display:flex;align-items:center;justify-content:center;font-family:'Big Shoulders Display',Anton,sans-serif;font-weight:900;font-size:64px;letter-spacing:.08em;color:rgba(70,50,10,.55);
 box-shadow:0 10px 40px rgba(0,0,0,.45)}
.m-cf{position:absolute;width:16px;height:26px;z-index:9;pointer-events:none;border-radius:3px}
body.l-marcador .m-grid,body.l-tablero .m-grid,body.l-editorial .m-grid,body.l-editorial .m-p,body.l-editorial .m-br,
body.l-editorial .m-tag,body.l-editorial .m-scan,body.l-ultima_hora .m-br{display:none}
body.l-marcador [data-m=big]{color:#ffb627!important;-webkit-text-stroke:0}
.m-dots{position:absolute;inset:0;background-image:radial-gradient(rgba(0,0,0,.42) 38%,transparent 40%);background-size:8px 8px;pointer-events:none}
.m-beam{position:absolute;top:-10%;width:520px;height:120%;background:linear-gradient(180deg,rgba(255,236,180,.20),transparent 70%);
 clip-path:polygon(45% 0,55% 0,100% 100%,0 100%);transform-origin:50% 0;mix-blend-mode:screen;pointer-events:none}
.m-tick{position:absolute;left:0;right:0;bottom:190px;height:86px;background:#c8102e;display:flex;align-items:center;overflow:hidden;
 box-shadow:0 0 40px rgba(200,16,46,.6)}
.m-tick span{white-space:nowrap;font-family:'Big Shoulders Display',Anton,sans-serif;font-weight:900;font-size:50px;letter-spacing:.04em;color:#fff}
.m-flag{position:absolute;left:66px;top:150px;background:#c8102e;color:#fff;font-family:'Big Shoulders Display',Anton,sans-serif;font-weight:900;
 font-size:40px;padding:6px 22px;letter-spacing:.06em}
body.l-ultima_hora [data-m=kick]{background:#c8102e!important;border-color:#c8102e!important;color:#fff!important}
body.l-neon .m-grid{background-image:linear-gradient(rgba(0,229,255,.7) 2px,transparent 2px),linear-gradient(90deg,rgba(255,45,149,.6) 2px,transparent 2px);opacity:.22}
body.l-neon .m-p{background:radial-gradient(circle,#b9fbff 0%,#00e5ff 40%,rgba(0,229,255,0) 70%)}
body.l-neon .m-br{border-color:#ff2d95}
body.l-neon [data-m=big]{color:#f3fbff!important}
.m-box{position:absolute;left:0;right:0;height:84px;background:#000;pointer-events:none;z-index:5}
.m-grain{position:absolute;inset:0;opacity:.10;pointer-events:none;background-image:radial-gradient(rgba(255,255,255,.5) 1px,transparent 1.2px);background-size:5px 5px}
.m-pitch{position:absolute;left:6%;right:6%;top:18%;height:64%;pointer-events:none;opacity:.20}
[data-m=stage]{transform-style:preserve-3d;will-change:transform}
</style>
<script>
(function(){
const W=innerWidth,H=innerHeight,cl=x=>Math.max(0,Math.min(1,x)),E=x=>1-Math.pow(1-cl(x),3),
B=x=>{x=cl(x);const c1=1.55,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2)};
let seed=7;const R=()=>{seed=(seed*16807)%2147483647;return seed/2147483647};
const add=(c,h)=>{const d=document.createElement('div');d.className=c;if(h)d.innerHTML=h;document.body.appendChild(d);return d};
const art=document.querySelector('[data-m=art]');
const grid=add('m-grid');
const parts=[];for(let i=0;i<26;i++){const z=R();const p=add('m-p');const s=6+z*30;p.style.width=p.style.height=s+'px';
 p.style.filter='blur('+((1-z)*3+(z>.8?2:0))+'px)';parts.push({el:p,x:R()*W,y:R()*H,z,sp:30+z*120,ph:R()*6.28});}
const sweep=add('m-sweep');add('m-scan');
[['left:46px;top:46px','border-width:5px 0 0 5px'],['right:46px;top:46px','border-width:5px 5px 0 0'],
 ['left:46px;bottom:70px','border-width:0 0 5px 5px'],['right:46px;bottom:70px','border-width:0 5px 5px 0']].forEach(([p,b])=>{const d=add('m-br');d.style.cssText+=p+';'+b});
const L=window.__look||'terminal';document.body.classList.add('l-'+L);
const tag=add('m-tag','<i></i>'+({marcador:'EN VIVO · MARCADOR EGG',ultima_hora:'EGG · AL MINUTO',neon:'EGG · NIGHT DATA',tablero:'EGG · PIZARRA'}[L]||'EGG · DATA FEED'));
const prog=add('m-prog','<b></b>').firstChild;
const SC=window.__scene||[0,1];const story=add('m-story',Array.from({length:SC[1]},(_,i)=>'<i><b style="transform:scaleX('+(i<SC[0]?1:0)+')"></b></i>').join(''));
const storyNow=story.children[SC[0]]?story.children[SC[0]].firstChild:null;
const cd=document.querySelector('[data-countdown]');
let beams=[],tick=null,pitch=null;
if(L==='marcador'){add('m-dots');beams=[add('m-beam'),add('m-beam')];beams[0].style.left='-6%';beams[1].style.right='-6%'}
if(L==='ultima_hora'){add('m-flag','ÚLTIMA HORA');tick=add('m-tick','<span>'+'ÚLTIMA HORA · EL DATO DE HOY · EGG GOLDGLITCH STATS · '.repeat(6)+'</span>').firstChild}
if(L==='editorial'){const a=add('m-box');a.style.top='0';const b=add('m-box');b.style.bottom='0';add('m-grain')}
if(L==='tablero'){pitch=add('m-pitch','<svg viewBox="0 0 680 1050" width="100%" height="100%" fill="none" stroke="#fff" stroke-width="5">'+
 '<rect x="20" y="20" width="640" height="1010" rx="6"/><line x1="20" y1="525" x2="660" y2="525"/><circle cx="340" cy="525" r="92"/>'+
 '<rect x="150" y="20" width="380" height="165"/><rect x="150" y="865" width="380" height="165"/><path d="M200 700 C 300 560, 420 520, 470 380" stroke="#d4af37" stroke-width="9"/>'+
 '<path d="M470 380 l-34 6 m34 -6 l-6 34" stroke="#d4af37" stroke-width="9"/></svg>');
 pitch.querySelectorAll('rect,line,circle,path').forEach(e=>{const l=e.getTotalLength?e.getTotalLength():800;e.style.strokeDasharray=l;e.style.strokeDashoffset=l;e.dataset.l=l})}
const slow=L==='editorial'?1.7:1;
const words=[];document.querySelectorAll('[data-m=big]').forEach(el=>{
 const txt=el.textContent.trim();const m=txt.match(/^(\d{1,3})%$/);
 if(m){el.dataset.n=m[1];el.dataset.count='1';return}
 const chars=el.dataset.split==='chars';
 el.innerHTML=(chars?[...txt]:txt.split(/\s+/)).map(w=>'<span class="m-w">'+w.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</span>').join(chars?'':' ');
 el.querySelectorAll('.m-w').forEach(s=>words.push(s));});
let foil=null,conf=[],landed=null;
const hero=document.querySelector('[data-m=big][data-count]');
if(hero){foil=add('m-foil','RASPÁ');foil.dataset.ready='0'}
for(let i=0;i<46;i++){const c=add('m-cf');c.style.background=['#d4af37','#fff3c4','#ff2e88','#00e5a0','#ffffff'][i%5];c.style.opacity=0;
 conf.push({el:c,a:R()*6.283,v:700+R()*900,r:R()*720,d:R()*0.25})}
const nums=[...document.querySelectorAll('[data-m=num]')];
const fills=[...document.querySelectorAll('[data-m=fill]')];
fills.forEach(f=>f.style.transformOrigin='0 50%');
const q=s=>[...document.querySelectorAll('[data-m='+s+']')];
window.__egg=function(t,T){
 if(storyNow)storyNow.style.transform='scaleX('+cl(t/T)+')';
 if(cd){const k=Math.floor(t/0.4);cd.textContent=k<3?String(3-k):'¡AHÍ VA!';const ph=(t%0.4)/0.4;
  cd.style.transform='scale('+(k<3?1.35-0.35*E(ph/0.5):1+0.15*Math.sin(t*20)*Math.exp(-(t-1.2)*4))+')';cd.style.opacity=k<3?1-0.5*Math.max(0,ph-0.7)/0.3:1}
 if(hero&&foil){if(foil.dataset.ready==='0'){const r=hero.getBoundingClientRect();if(r.width>10){foil.style.left=(r.left-40)+'px';foil.style.top=(r.top-20)+'px';
   foil.style.width=(r.width+80)+'px';foil.style.height=(r.height+40)+'px';foil.dataset.ready='1';foil.dataset.cx=r.left+r.width/2;foil.dataset.cy=r.top+r.height/2}}
  const p=cl((t-0.25)/0.55);let pts=[];const N=14;for(let i=0;i<=N;i++){const y=i/N*100;pts.push(((p*130-30)+(i%2?8:-8)*(1-p))+'% '+y+'%')}
  foil.style.clipPath=p<=0?'none':p>=1?'polygon(0 0,0 0,0 0)':'polygon('+pts.join(',')+',100% 100%,100% 0)';
  const tl=1.35;conf.forEach(c=>{const u=t-tl-c.d;if(u<0||u>1.4){c.el.style.opacity=0;return}
   const x=+foil.dataset.cx+Math.cos(c.a)*c.v*u,y=+foil.dataset.cy+Math.sin(c.a)*c.v*u+900*u*u;
   c.el.style.opacity=1-u/1.4;c.el.style.transform='translate('+x+'px,'+y+'px) rotate('+(c.r*u)+'deg)'})}
 beams.forEach((b,i)=>{b.style.transform='rotate('+((i?-1:1)*(14+Math.sin(t*0.9+i)*7))+'deg)'});
 if(tick)tick.style.transform='translateX('+(-t*260)+'px)';
 if(pitch)pitch.querySelectorAll('[data-l]').forEach((e,i)=>{e.style.strokeDashoffset=(+e.dataset.l)*(1-E((t-0.1*i)/1.1))});
 if(L==='ultima_hora')q('stage').forEach(()=>{});
 if(art)art.style.transform='scale('+(1.16-0.11*E(t/T))+') translateY('+(-26*t/T)+'px)';
 grid.style.backgroundPosition='0 '+(t*140)+'px';
 parts.forEach(p=>{const y=((p.y-t*p.sp)%H+H)%H;const x=p.x+Math.sin(t*0.8+p.ph)*18*p.z;
  p.el.style.transform='translate('+x+'px,'+y+'px)';p.el.style.opacity=(0.25+0.55*p.z)*(0.6+0.4*Math.sin(t*2+p.ph))});
 sweep.style.left=(-500+(t/T)*(W+900))+'px';
 tag.style.opacity=(Math.floor(t*2)%2?0.55:0.95);
 prog.style.transform='scaleX('+cl(t/T)+')';
 q('stage').forEach(s=>{const k=E(t/(0.6*slow));const sh=L==='ultima_hora'&&t<0.3?Math.sin(t*90)*14*(0.3-t)/0.3:0;
  s.style.transform='translateX('+sh+'px) rotateX('+((1-k)*16+Math.sin(t*1.1/slow)*2.2)+'deg) rotateY('+(Math.sin(t*0.7/slow)*3.2)+'deg) translateZ('+((1-k)*-160)+'px)'});
 q('kick').forEach(k=>{const p=cl(t/0.35);k.style.opacity=p;k.style.transform='translateY('+(-34*(1-E(p)))+'px)'});
 words.forEach((w,i)=>{const p=cl((t-0.12*slow-0.055*slow*i)/(0.45*slow));w.style.opacity=Math.min(1,p*2.2);
  w.style.transform='translateY('+((1-B(p))*95)+'px) rotateX('+((1-E(p))*-78)+'deg)'});
 q('big').forEach(el=>{if(el.dataset.count){const p=cl((t-0.55)/0.8);el.textContent=Math.round(E(p)*(+el.dataset.n))+'%';
  const bump=t>1.35?0.18*Math.exp(-(t-1.35)*6)*Math.cos((t-1.35)*18):0;el.style.transform='scale('+(1+bump)+')'}
  const g=t<0.14&&L!=='editorial'?(0.14-t)*90:0;const glow=L==='marcador'?',0 0 34px #ffb627,0 0 80px #ff8a00aa':L==='neon'?',0 0 30px #00e5ff,0 0 70px #ff2d95aa':'';
  el.style.textShadow=(g?(g+'px 0 0 #ff2d55cc,'+(-g)+'px 0 0 #00e5ffcc,'):'')+'0 18px 60px rgba(0,0,0,.75)'+glow});
 q('small').forEach(el=>{const p=cl((t-0.42)/0.45);el.style.opacity=p;el.style.filter='blur('+((1-p)*12)+'px)';el.style.transform='translateY('+(24*(1-E(p)))+'px)'});
 q('badges').forEach(b=>{const c=b.children;if(c.length<3)return;const p=cl((t-0.04)/0.55),v=cl((t-0.38)/0.3);
  c[0].style.transform='translateX('+(-(1-B(p))*560)+'px) rotateY('+((1-E(p))*70)+'deg)';
  c[2].style.transform='translateX('+((1-B(p))*560)+'px) rotateY('+(-(1-E(p))*70)+'deg)';
  c[1].style.transform='scale('+(0.2+0.8*B(v))+')';c[1].style.opacity=v});
 fills.forEach((f,i)=>{const p=cl((t-0.45-0.14*i)/0.8);f.style.transform='scaleX('+E(p)+')'});
 nums.forEach((n,i)=>{const p=cl((t-0.45-0.14*i)/0.8);n.textContent=Math.round(E(p)*(+n.dataset.v))+'%'});
 q('echo').forEach(e=>{e.style.transform='translate(calc(-50% - '+(t*36)+'px),-50%) scale(1.9)'});
};
window.__egg(0,1);
})();
</script>
"""


def inject(html: str, look: str = "terminal", scene: tuple[int, int] = (0, 1)) -> str:
    eng = (f"<script>window.__look={look!r};window.__scene=[{scene[0]},{scene[1]}];</script>" + ENGINE
           + (SOUL if look in SOUL_LOOKS else "") + (LUX if look in LUX_LOOKS else ""))
    return html.replace("</body>", eng + "</body>", 1) if "</body>" in html else html + eng


def scene_frames(pg, html: str, seconds: float, out_dir: str, look: str = "terminal", scene: tuple[int, int] = (0, 1)) -> int:
    """Render one animated scene into out_dir/0001.jpg… Returns the number of frames."""
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir, exist_ok=True)
    pg.set_content(inject(html, look, scene), wait_until="networkidle")
    pg.evaluate("document.fonts.ready.then(()=>1)")
    fps = fps_for(look)
    n = max(2, int(round(seconds * fps)))
    for i in range(n):
        pg.evaluate(f"window.__egg({i / fps:.4f},{seconds:.4f});window.__soul&&window.__soul({i / fps:.4f},{seconds:.4f},{i});window.__lux&&window.__lux({i / fps:.4f},{seconds:.4f})")
        pg.screenshot(path=os.path.join(out_dir, f"{i + 1:04d}.jpg"), type="jpeg", quality=84)
    return n


def render_scenes(htmls: list[str], seconds: list[float], base_dir: str, look: str = "terminal") -> list[str]:
    """All scenes of a video, one browser. Returns the frame folders (ffmpeg pattern dir/%04d.jpg)."""
    from playwright.sync_api import sync_playwright
    dirs = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        for i, (h, s) in enumerate(zip(htmls, seconds)):
            d = os.path.join(base_dir, f"s{i + 1:02d}")
            scene_frames(pg, h, s, d, look, (i, len(htmls)))
            dirs.append(d)
        b.close()
    return dirs


def fps_for(look: str) -> int:
    return SOUL_FPS if look in SOUL_LOOKS else FPS


def enabled() -> bool:
    return os.environ.get("REDES_MOVIMIENTO", "1") != "0"


# ------------------------------------------------------------------ "Alma": hand-made, printed, from the stands
# The glossy dark-gold terminal looked like every AI template. These looks come from football culture instead:
#   diario    the sports paper's front page: newsprint, halftone photo, ink slightly off-register, red marker
#   cuaderno  the analyst's notebook: graph paper, highlighter, handwriting, arrows and circles drawn live
#   trapo     the barra's painted flag: fabric weave, hand-painted letters, the cloth waves
#   cartel    the neighbourhood party poster: fluorescent blocks, chunky letters, screen-print misregistration
#   album     the sticker album: the match as a collectible card with gold foil that catches the light
# All animate "on twos" (12 drawings per second) with lines that boil a little: stop-motion, made by hand.
SOUL_LOOKS = ("diario", "cuaderno", "trapo", "cartel", "album")
SOUL_FPS = int(os.environ.get("REDES_FPS_ALMA", "12"))

SOUL = r"""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Caveat+Brush&family=Bungee&family=Oswald:wght@500;700&family=Rubik+Mono+One&display=block">
<svg width="0" height="0" style="position:absolute"><defs>
 <filter id="rough"><feTurbulence id="rough-t" type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="1"/><feDisplacementMap in="SourceGraphic" scale="5"/></filter>
 <filter id="ink"><feTurbulence id="ink-t" type="fractalNoise" baseFrequency="0.9" numOctaves="1" seed="3"/><feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -1.4 1.25"/><feComposite in="SourceGraphic" operator="in"/></filter>
</defs></svg>
<style>
body.soul .m-grid,body.soul .m-p,body.soul .m-sweep,body.soul .m-scan,body.soul .m-br,body.soul .m-tag,body.soul .grain,body.soul .streak,
body.soul [data-m=echo],body.soul [data-m=shade]{display:none!important}
body.soul .wrap{text-shadow:none!important}
body.soul [data-m=big],body.soul [data-m=small]{text-shadow:none!important}
.s-paper{position:absolute;inset:0;pointer-events:none;mix-blend-mode:multiply;opacity:.55;
 background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .45  0 0 0 0 .4  0 0 0 0 .32  0 0 0 .55 0'/></filter><rect width='300' height='300' filter='url(%23n)'/></svg>")}
.s-anno{position:absolute;inset:0;pointer-events:none;z-index:6}
.s-anno path{fill:none;stroke-linecap:round;stroke-linejoin:round}
/* diario */
body.l-diario{background:#ece3cf!important}
body.l-diario [data-m=art]{filter:grayscale(1) contrast(1.5) brightness(1.08);mix-blend-mode:multiply;opacity:.42;inset:14% 6% 34% 6%!important;
 -webkit-mask-image:radial-gradient(#000 0.9px,transparent 1.3px);-webkit-mask-size:7px 7px;mask-image:radial-gradient(#000 0.9px,transparent 1.3px);mask-size:7px 7px}
body.l-diario .wrap{color:#15120d}
body.l-diario [data-m=big]{color:#15120d!important;font-family:Oswald,'Big Shoulders Display',sans-serif!important;font-weight:700!important;letter-spacing:-.01em!important;
 text-shadow:4px 3px 0 rgba(215,38,61,.55)!important;filter:url(#rough)}
body.l-diario [data-m=small]{color:#2d271e!important;font-family:Georgia,'Times New Roman',serif!important;font-style:italic;font-weight:700!important}
body.l-diario [data-m=kick]{background:#d7263d!important;color:#fff!important;border:0!important;border-radius:0!important;transform:rotate(-2deg)}
body.l-diario .top,body.l-diario .top *{color:#15120d!important}
body.l-diario .foot,body.l-diario .foot *{color:#5a5044!important}
body.l-diario [data-m=num]{color:#d7263d!important}
body.l-diario [data-m=fill]{background:repeating-linear-gradient(-45deg,#15120d 0 6px,transparent 6px 11px)!important;box-shadow:none!important}
body.l-diario div:has(> [data-m=fill]){background:rgba(21,18,13,.10)!important;border:2px solid #15120d}
.s-mast{position:absolute;left:66px;right:66px;top:178px;border-top:6px solid #15120d;border-bottom:2px solid #15120d;padding:8px 0;display:flex;
 justify-content:space-between;font-family:Oswald,sans-serif;font-weight:700;font-size:30px;letter-spacing:.12em;color:#15120d;z-index:4}
/* cuaderno */
body.l-cuaderno{background:#fbfaf4!important}
body.l-cuaderno::before{content:'';position:absolute;inset:0;background-image:linear-gradient(rgba(40,110,200,.16) 2px,transparent 2px),linear-gradient(90deg,rgba(40,110,200,.16) 2px,transparent 2px);background-size:54px 54px}
body.l-cuaderno::after{content:'';position:absolute;top:0;bottom:0;left:118px;width:3px;background:rgba(215,38,61,.55)}
body.l-cuaderno [data-m=art]{opacity:.0}
body.l-cuaderno .wrap{color:#1b2a4a}
body.l-cuaderno [data-m=big]{color:#1b2a4a!important;font-family:'Permanent Marker',cursive!important;text-transform:none!important;filter:url(#rough)}
body.l-cuaderno [data-m=small]{color:#1b2a4a!important;font-family:'Caveat Brush',cursive!important;font-size:66px!important;font-weight:400!important}
body.l-cuaderno [data-m=kick]{background:#ffe94a!important;color:#1b2a4a!important;border:0!important;font-family:'Caveat Brush',cursive!important;font-size:44px!important;letter-spacing:0!important;text-transform:none!important}
body.l-cuaderno .top *,body.l-cuaderno .foot,body.l-cuaderno .foot *{color:#1b2a4a!important}
body.l-cuaderno [data-m=num]{color:#d7263d!important;font-family:'Permanent Marker',cursive}
body.l-cuaderno [data-m=fill]{background:#ffe94a!important;box-shadow:none!important;opacity:.95}
body.l-cuaderno div:has(> [data-m=fill]){background:transparent!important;border:3px solid #1b2a4a;border-radius:6px!important}
/* trapo */
body.l-trapo{background:#7a0f1c!important}
body.l-trapo::before{content:'';position:absolute;inset:0;background-image:repeating-linear-gradient(0deg,rgba(0,0,0,.10) 0 2px,transparent 2px 4px),repeating-linear-gradient(90deg,rgba(255,255,255,.05) 0 2px,transparent 2px 5px)}
body.l-trapo [data-m=art]{opacity:.22;filter:grayscale(1) contrast(1.3);mix-blend-mode:luminosity}
body.l-trapo [data-m=big]{color:#fff6e0!important;font-family:'Permanent Marker',cursive!important;filter:url(#rough);text-shadow:0 0 1px #fff6e0,3px 4px 0 rgba(0,0,0,.35)!important}
body.l-trapo [data-m=small]{color:#ffd451!important;font-family:'Caveat Brush',cursive!important;font-size:64px!important}
body.l-trapo [data-m=kick]{background:#ffd451!important;color:#7a0f1c!important;border:0!important}
body.l-trapo .top *,body.l-trapo .foot *{color:#fff6e0!important}
body.l-trapo [data-m=fill]{background:#ffd451!important;box-shadow:none!important}
.s-fold{position:absolute;inset:0;pointer-events:none;background:linear-gradient(90deg,rgba(0,0,0,.28),rgba(255,255,255,.06) 20%,rgba(0,0,0,.22) 40%,rgba(255,255,255,.07) 62%,rgba(0,0,0,.26) 82%,rgba(255,255,255,.05));mix-blend-mode:overlay}
/* cartel */
body.l-cartel{background:#0d0d0d!important}
body.l-cartel [data-m=art]{opacity:.18;filter:grayscale(1) contrast(1.6)}
body.l-cartel [data-m=big]{font-family:Bungee,'Rubik Mono One',sans-serif!important;color:#ffe600!important;line-height:1.05!important;
 text-shadow:6px 6px 0 #ff2e88,12px 12px 0 #00c2ff!important}
body.l-cartel [data-m=small]{display:inline-block;background:#ff2e88;color:#fff!important;padding:10px 22px;font-family:'Rubik Mono One',sans-serif!important;font-size:40px!important;transform:rotate(-1.5deg)}
body.l-cartel [data-m=kick]{background:#00e676!important;color:#0d0d0d!important;border:0!important;font-family:'Rubik Mono One',sans-serif!important}
body.l-cartel [data-m=num]{color:#ffe600!important}
body.l-cartel [data-m=fill]{box-shadow:none!important}
.s-burst{position:absolute;width:300px;height:300px;z-index:0;pointer-events:none;opacity:.9}
/* album */
body.l-album{background:#1f6f43!important}
body.l-album::before{content:'';position:absolute;inset:0;background-image:radial-gradient(rgba(255,255,255,.08) 2px,transparent 2.5px);background-size:26px 26px}
body.l-album [data-m=art]{opacity:0}
body.l-album [data-m=stage]{background:#fbf6e8;border-radius:34px;padding:56px 44px;margin:0 10px;border:14px solid #d4af37;
 box-shadow:0 0 0 6px #fbf6e8,0 30px 60px rgba(0,0,0,.45);position:relative;overflow:hidden}
body.l-album [data-m=big]{color:#1a1a1a!important;font-family:Oswald,sans-serif!important;font-weight:700!important}
body.l-album [data-m=small]{color:#3a3a3a!important}
body.l-album [data-m=kick]{background:#d4af37!important;color:#1a1a1a!important;border:0!important}
body.l-album .top *,body.l-album .foot *{color:#fbf6e8!important}
.s-foil{position:absolute;top:-30%;bottom:-30%;width:180px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.75),rgba(255,236,170,.6),transparent);transform:rotate(18deg);mix-blend-mode:overlay;pointer-events:none}
</style>
<script>
(function(){
const L=window.__look;const S=['diario','cuaderno','trapo','cartel','album'];if(!S.includes(L))return;
document.body.classList.add('soul');
const W=innerWidth,H=innerHeight,cl=x=>Math.max(0,Math.min(1,x)),E=x=>1-Math.pow(1-cl(x),3);
const add=(c,h,parent)=>{const d=document.createElement('div');d.className=c;if(h)d.innerHTML=h;(parent||document.body).appendChild(d);return d};
add('s-paper');
if(L==='diario'){const d=new Date();add('s-mast','<span>EL DATO</span><span>EDICIÓN DEL DÍA</span><span>EGG</span>')}
if(L==='trapo')add('s-fold');
let foil=null;if(L==='album'){const st=document.querySelector('[data-m=stage]');if(st)foil=add('s-foil','',st)}
let bursts=[];if(L==='cartel'){[[-70,240,'#ff2e88'],[W-250,120,'#00c2ff']].forEach(([x,y,c])=>{const b=add('s-burst','<svg viewBox="0 0 100 100"><polygon fill="'+c+'" points="50,0 61,30 95,20 72,46 100,62 66,68 72,100 50,78 28,100 34,68 0,62 28,46 5,20 39,30"/></svg>');b.style.left=x+'px';b.style.top=y+'px';bursts.push(b)})}
// hand-drawn marks around the hero element, drawn live
const anno=add('s-anno','<svg width="'+W+'" height="'+H+'"></svg>').firstChild;
const ink={diario:'#d7263d',cuaderno:'#d7263d',trapo:'#ffd451',cartel:'#00e676',album:'#d7263d'}[L];
const marks=[];
const hero=document.querySelector('[data-m=big]');
function mark(d,w){const p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',d);p.setAttribute('stroke',ink);
 p.setAttribute('stroke-width',w||11);p.setAttribute('filter','url(#rough)');anno.appendChild(p);const l=p.getTotalLength();p.style.strokeDasharray=l;p.style.strokeDashoffset=l;marks.push([p,l]);return p}
setTimeout(()=>{},0);
function plan(){if(!hero||L==='album')return;const r=hero.getBoundingClientRect();if(r.width<10)return;
 const cx=r.left+r.width/2,cy=r.top+r.height/2,rx=r.width/2+46,ry=r.height/2+38;
 if(hero.dataset.count||r.width<W*.5){let d='';for(let i=0;i<=36;i++){const a=-1.9+i/36*6.9,k=1+0.06*Math.sin(i*1.7);d+=(i?'L':'M')+(cx+Math.cos(a)*rx*k).toFixed(1)+' '+(cy+Math.sin(a)*ry*k).toFixed(1)}mark(d)}
 else{const y=r.bottom+16;mark('M'+(r.left+10)+' '+y+' C '+(r.left+r.width*.3)+' '+(y+14)+', '+(r.left+r.width*.6)+' '+(y-10)+', '+(r.right-6)+' '+(y+6),12);
  if(L==='cuaderno')mark('M'+(r.left+20)+' '+(y+30)+' C '+(r.left+r.width*.4)+' '+(y+44)+', '+(r.left+r.width*.7)+' '+(y+20)+', '+(r.right-60)+' '+(y+34),8)}
 const sm=document.querySelector('[data-m=small]');if(sm&&(L==='cuaderno'||L==='diario')){const s=sm.getBoundingClientRect();if(s.width>10&&s.left>170){
  const x=s.left-70,y=s.top+s.height/2;mark('M'+(x-90)+' '+(y-120)+' Q '+(x-40)+' '+(y-10)+' '+x+' '+y+' M '+(x-30)+' '+(y-26)+' L '+x+' '+y+' L '+(x-36)+' '+(y+12),9)}}}
let planned=false;
const rt=document.getElementById('rough-t');
window.__soul=function(t,T,f){
 if(!planned&&t>0.5){plan();planned=true}
 marks.forEach(([p,l],i)=>{p.style.strokeDashoffset=l*(1-E((t-0.55-0.25*i)/0.55))});
 if(rt)rt.setAttribute('seed',1+Math.floor(f/2)%7);
 // stop-motion jitter: everything drawn by hand moves a hair every drawing
 const j=(k)=>((Math.sin(f*12.9898+k*78.233)*43758.5453)%1);
 document.querySelectorAll('[data-m=big],[data-m=kick]').forEach((el,i)=>{el.style.translate=(j(i)*3).toFixed(1)+'px '+(j(i+9)*3).toFixed(1)+'px';el.style.rotate=(j(i+4)*0.6).toFixed(2)+'deg'});
 if(L==='trapo')document.querySelectorAll('[data-m=stage]').forEach(s=>{s.style.transform+=' skewY('+(Math.sin(t*2.2)*1.6)+'deg)'});
 if(L==='diario'){const st=document.querySelector('[data-m=stage]');if(st){const k=E(t/0.35);st.style.transform='scale('+(1.25-0.25*k)+') rotate('+((1-k)*-6)+'deg)'}}
 if(L==='cartel')bursts.forEach((b,i)=>{b.style.transform='rotate('+(t*(i?-30:24))+'deg) scale('+(0.6+0.4*E(t/0.4))+')'});
 if(foil)foil.style.left=(-300+((t*0.55)%1.6)*900)+'px';
 if(L==='album'){const st=document.querySelector('[data-m=stage]');if(st){const k=E(t/0.5);st.style.transform='perspective(1400px) rotateY('+((1-k)*-80+Math.sin(t*1.3)*6)+'deg) rotateX('+(Math.sin(t)*3)+'deg)'}}
};
})();
</script>
"""


# ------------------------------------------------------------------ "Members Club": quiet luxury with a voice of its own
# EGG as a private members' data club: emerald velvet, champagne gold, Didone numbers, a wax-seal monogram, the calm of
# St. Moritz and the swagger of streetwear luxury. Smooth, slow, expensive motion (24 fps), never loud.
#   club       emerald velvet, double champagne hairline frame, rotating EGG seal, gold-foil glint on the numbers
#   stmoritz   ivory card, navy ink, racing-green heritage ribbon, snow drifting, postcard-of-the-Alps calm
#   esmeralda  green marble with gold veins, Didone numerals in gold foil, glass panel
#   bbc        streetwear luxury: black, electric green, diamonds that sparkle, chunky rounded type
#   noche      black lacquer, emerald rim light, champagne serif: the private lounge after midnight
LUX_LOOKS = ("club", "stmoritz", "esmeralda", "bbc", "noche")

LUX = r"""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700;1,900&family=Cormorant+Garamond:ital,wght@0,500;0,700;1,600&family=Unbounded:wght@600;900&family=Pinyon+Script&display=block">
<svg width="0" height="0" style="position:absolute"><defs>
 <filter id="marble"><feTurbulence type="fractalNoise" baseFrequency="0.006 0.018" numOctaves="4" seed="11"/>
  <feColorMatrix values="0 0 0 0 0.83  0 0 0 0 0.71  0 0 0 0 0.42  0 0 0 -9 4.2"/></filter>
 <filter id="velvet"><feTurbulence type="fractalNoise" baseFrequency="0.7" numOctaves="2" seed="5"/><feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 .16 0"/></filter>
</defs></svg>
<style>
body.lux .m-grid,body.lux .m-p,body.lux .m-sweep,body.lux .m-scan,body.lux .m-br,body.lux .m-tag,body.lux .grain,body.lux .streak,
body.lux [data-m=echo],body.lux .m-prog{display:none!important}
body.lux .wrap{text-shadow:none!important}
body.lux [data-m=kick]{background:none!important;border:0!important;border-radius:0!important;padding:0 0 0 0!important;letter-spacing:.42em!important;
 font-family:'Cormorant Garamond',serif!important;font-weight:700!important;font-size:30px!important;display:flex!important;align-items:center;justify-content:center;gap:22px}
body.lux [data-m=kick]::before,body.lux [data-m=kick]::after{content:'';width:90px;height:1px;background:currentColor;opacity:.7}
body.lux [data-m=big]{font-family:'Playfair Display',serif!important;font-weight:900!important;text-transform:none!important;letter-spacing:-.01em!important;
 line-height:1.02!important;text-shadow:none!important}
body.lux [data-m=big] .m-w,body.lux [data-m=big][data-count],body.lux [data-m=big][data-countdown]{background-image:var(--gold)!important;background-size:260% 100%!important;
 -webkit-background-clip:text!important;background-clip:text!important;color:transparent!important;padding:0 .04em}
body.lux [data-m=small]{font-family:'Cormorant Garamond',serif!important;font-style:italic;font-weight:600!important;font-size:60px!important}
body.lux [data-m=fill]{height:8px!important;box-shadow:none!important;border-radius:0!important}
body.lux div:has(> [data-m=fill]){height:8px!important;border-radius:0!important;background:rgba(255,255,255,.12)!important}
body.lux .foot,body.lux .foot *{font-family:'Cormorant Garamond',serif!important;letter-spacing:.2em;text-transform:uppercase;font-size:24px!important}
.x-frame{position:absolute;inset:34px;border:1.5px solid var(--g);pointer-events:none;z-index:3}
.x-frame::after{content:'';position:absolute;inset:12px;border:1px solid var(--g);opacity:.55}
.x-seal{position:absolute;left:50%;top:150px;width:170px;height:170px;margin-left:-85px;z-index:4;pointer-events:none}
.x-glint{position:absolute;inset:0;pointer-events:none;z-index:7;mix-blend-mode:screen}
.x-vel{position:absolute;inset:0;pointer-events:none;filter:url(#velvet)}
.x-dia{position:absolute;pointer-events:none;z-index:6}
.x-snow{position:absolute;border-radius:50%;background:#fff;pointer-events:none;z-index:2}
.x-ribbon{position:absolute;left:0;right:0;height:46px;background:linear-gradient(180deg,#1f5c3a 0 33%,#14213d 33% 66%,#1f5c3a 66%);pointer-events:none;z-index:3}
.x-marble{position:absolute;inset:0;pointer-events:none;opacity:.55}
/* club */
body.l-club{--g:#d8c08a;background:radial-gradient(1200px 900px at 50% 35%,#13553f,#062a1e 70%,#031a12)!important;color:#efe6cf}
body.l-club [data-m=art]{filter:grayscale(1) sepia(.6) hue-rotate(60deg) brightness(.55);opacity:.35}
body.l-club{--gold:linear-gradient(100deg,#a88a4a 0%,#f6e7b8 18%,#c9a55a 32%,#fff6d6 46%,#b8924c 60%,#e9d39a 80%,#a88a4a 100%)} body.l-club [data-m=big]{}
body.l-club [data-m=kick]{color:#d8c08a!important} body.l-club [data-m=small]{color:#efe6cf!important}
body.l-club [data-m=fill]{background:linear-gradient(90deg,#b8924c,#f6e7b8)!important} body.l-club [data-m=num]{color:#d8c08a!important}
body.l-club .top *,body.l-club .foot,body.l-club .foot *{color:#d8c08a!important}
/* stmoritz */
body.l-stmoritz{--g:#14213d;background:#f4efe4!important;color:#14213d}
body.l-stmoritz [data-m=art]{filter:grayscale(.2) contrast(1.05) brightness(1.05);opacity:.9;inset:26% 9% 40% 9%!important;border:10px solid #fff;
 box-shadow:0 20px 50px rgba(20,33,61,.25)}
body.l-stmoritz{--gold:linear-gradient(100deg,#14213d 0%,#14213d 40%,#3b5b9a 50%,#14213d 60%,#14213d 100%)} body.l-stmoritz [data-m=big]{}
body.l-stmoritz [data-m=kick]{color:#1f5c3a!important} body.l-stmoritz [data-m=small]{color:#14213d!important}
body.l-stmoritz [data-m=fill]{background:#1f5c3a!important} body.l-stmoritz [data-m=num]{color:#1f5c3a!important}
body.l-stmoritz div:has(> [data-m=fill]){background:rgba(20,33,61,.12)!important}
body.l-stmoritz .wrap{color:#14213d} body.l-stmoritz .top *,body.l-stmoritz .foot,body.l-stmoritz .foot *{color:#14213d!important}
/* esmeralda */
body.l-esmeralda{--g:#e2c87e;background:linear-gradient(160deg,#0e4d36,#0a3a29 45%,#062418)!important;color:#f3ead2}
body.l-esmeralda [data-m=art]{opacity:.0}
body.l-esmeralda{--gold:linear-gradient(100deg,#9c7a2e 0%,#ffeeb3 20%,#d4b062 36%,#fffbe6 50%,#c39a45 64%,#f1d98f 82%,#9c7a2e 100%)} body.l-esmeralda [data-m=big]{;
 filter:drop-shadow(0 6px 18px rgba(0,0,0,.45))}
body.l-esmeralda [data-m=stage]{background:rgba(255,255,255,.06);border:1px solid rgba(226,200,126,.45);border-radius:6px;padding:46px 34px;backdrop-filter:blur(10px)}
body.l-esmeralda [data-m=kick]{color:#e2c87e!important} body.l-esmeralda [data-m=small]{color:#f3ead2!important}
body.l-esmeralda [data-m=fill]{background:linear-gradient(90deg,#c39a45,#ffeeb3)!important} body.l-esmeralda [data-m=num]{color:#e2c87e!important}
body.l-esmeralda .top *,body.l-esmeralda .foot,body.l-esmeralda .foot *{color:#e2c87e!important}
/* bbc */
body.l-bbc{--gold:linear-gradient(180deg,#ffffff 0%,#d8ffc4 30%,#7dff3c 55%,#3fae12 80%,#cfffb0 100%);--g:#7dff3c;background:radial-gradient(900px 700px at 50% 40%,#0f1a0b,#050705 70%)!important;color:#eaffde}
body.l-bbc [data-m=art]{filter:grayscale(1) contrast(1.3) brightness(.5) sepia(1) hue-rotate(50deg) saturate(2.4);opacity:.28}
body.l-bbc [data-m=big]{font-family:Unbounded,sans-serif!important;text-transform:uppercase!important;letter-spacing:-.02em!important;
 filter:drop-shadow(0 0 22px rgba(125,255,60,.45)) drop-shadow(4px 6px 0 #0b2a05)}
body.l-bbc [data-m=small]{font-family:Unbounded,sans-serif!important;font-style:normal;font-size:40px!important;color:#eaffde!important;letter-spacing:.02em}
body.l-bbc [data-m=kick]{color:#7dff3c!important;font-family:Unbounded,sans-serif!important;font-size:24px!important;letter-spacing:.3em!important}
body.l-bbc [data-m=fill]{background:#7dff3c!important;box-shadow:0 0 18px #7dff3c!important} body.l-bbc [data-m=num]{color:#7dff3c!important}
body.l-bbc .top *,body.l-bbc .foot,body.l-bbc .foot *{color:#b9ff95!important}
/* noche */
body.l-noche{--g:#c9b37e;background:#050605!important;color:#efe6cf;box-shadow:inset 0 0 260px rgba(16,120,80,.55)}
body.l-noche [data-m=art]{filter:grayscale(1) brightness(.45);opacity:.5}
body.l-noche{--gold:linear-gradient(100deg,#8f7a4c 0%,#efe2bd 22%,#b39a62 40%,#fff4d8 52%,#a48a55 66%,#e3d3a6 84%,#8f7a4c 100%)} body.l-noche [data-m=big]{;
 filter:drop-shadow(0 0 30px rgba(16,160,100,.35))}
body.l-noche [data-m=kick]{color:#3ddc97!important} body.l-noche [data-m=small]{color:#efe6cf!important}
body.l-noche [data-m=fill]{background:linear-gradient(90deg,#1f8f62,#3ddc97)!important} body.l-noche [data-m=num]{color:#c9b37e!important}
body.l-noche .top *,body.l-noche .foot,body.l-noche .foot *{color:#c9b37e!important}
</style>
<script>
(function(){
const L=window.__look;if(!['club','stmoritz','esmeralda','bbc','noche'].includes(L))return;
document.body.classList.add('lux');
const W=innerWidth,H=innerHeight,cl=x=>Math.max(0,Math.min(1,x)),E=x=>1-Math.pow(1-cl(x),3),S=x=>{x=cl(x);return x*x*(3-2*x)};
const add=(c,h)=>{const d=document.createElement('div');d.className=c;if(h)d.innerHTML=h;document.body.appendChild(d);return d};
let seed=19;const R=()=>{seed=(seed*16807)%2147483647;return seed/2147483647};
if(L==='esmeralda')add('x-marble','<svg width="'+W+'" height="'+H+'" fill="none" stroke="#e2c87e" stroke-linecap="round">'+
 '<path d="M-20 300 C 220 360, 380 260, 560 420 S 900 520, 1120 470" stroke-width="2.2" opacity=".55"/>'+
 '<path d="M-20 1220 C 180 1150, 420 1290, 640 1180 S 960 1080, 1120 1160" stroke-width="1.6" opacity=".4"/>'+
 '<path d="M300 -20 C 340 300, 240 520, 330 760" stroke-width="1.2" opacity=".35"/>'+
 '<path d="M820 1940 C 760 1700, 900 1520, 860 1300" stroke-width="1.4" opacity=".4"/></svg>');
if(L==='club'||L==='noche')add('x-vel');
if(L!=='bbc')add('x-frame');
if(L==='stmoritz'){const a=add('x-ribbon');a.style.top='96px';const b=add('x-ribbon');b.style.bottom='110px'}
const ink=getComputedStyle(document.body).getPropertyValue('--g').trim()||'#d8c08a';
let seal=null;
if(L!=='bbc'){seal=add('x-seal','<svg viewBox="0 0 200 200" width="170" height="170"><defs><path id="ring" d="M100,100 m-74,0 a74,74 0 1,1 148,0 a74,74 0 1,1 -148,0"/></defs>'+
 '<circle cx="100" cy="100" r="96" fill="none" stroke="'+ink+'" stroke-width="2"/><circle cx="100" cy="100" r="56" fill="none" stroke="'+ink+'" stroke-width="1.2"/>'+
 '<text font-family="Cormorant Garamond,serif" font-weight="700" font-size="15" letter-spacing="4.2" fill="'+ink+'"><textPath href="#ring">MEMBERS · DATA · CLUB · EST · MMXXVI · CALI · </textPath></text>'+
 '<text x="100" y="114" text-anchor="middle" font-family="Playfair Display,serif" font-weight="900" font-style="italic" font-size="40" fill="'+ink+'">EGG</text></svg>')}
const glint=add('x-glint','<div style="position:absolute;top:-20%;width:220px;height:140%;transform:rotate(18deg);background:linear-gradient(90deg,transparent,rgba(255,250,230,.22),transparent)"></div>').firstChild;
const dias=[];if(L==='bbc'){for(let i=0;i<14;i++){const d=add('x-dia','<svg viewBox="0 0 40 40" width="100%" height="100%"><path d="M20 0 L24 16 L40 20 L24 24 L20 40 L16 24 L0 20 L16 16 Z" fill="#eaffde"/></svg>');
 const s=18+R()*44;d.style.width=d.style.height=s+'px';d.style.left=(R()*(W-60))+'px';d.style.top=(140+R()*(H-360))+'px';dias.push({el:d,ph:R()*6.28,sp:1.5+R()*2.5})}}
const snow=[];if(L==='stmoritz'){for(let i=0;i<60;i++){const z=R();const f=add('x-snow');const s=3+z*9;f.style.width=f.style.height=s+'px';f.style.opacity=.35+z*.5;
 f.style.filter='blur('+((1-z)*1.5)+'px)';snow.push({el:f,x:R()*W,y:R()*H,z,sp:30+z*90,ph:R()*6.28})}}
const bigs=[...document.querySelectorAll('[data-m=big]')];
window.__lux=function(t,T){
 bigs.forEach(b=>{const pos=(100-((t*22)%200))+'% 0';b.style.backgroundPosition=pos;b.querySelectorAll('.m-w').forEach(w=>w.style.backgroundPosition=pos)});
 if(seal){seal.style.transform='rotate('+(t*9)+'deg) scale('+(0.6+0.4*S(t/0.9))+')';seal.style.opacity=S(t/0.7)}
 glint.style.left=(-400+((t/T))*(W+800))+'px';
 dias.forEach(d=>{const k=Math.max(0,Math.sin(t*d.sp+d.ph));d.el.style.opacity=k*k;d.el.style.transform='scale('+(0.4+0.8*k*k)+') rotate('+(t*40)+'deg)'});
 snow.forEach(f=>{const y=(f.y+t*f.sp)%H;const x=f.x+Math.sin(t*0.6+f.ph)*22*f.z;f.el.style.transform='translate('+x+'px,'+y+'px)'});
 // quieter, more expensive motion: slow down the stage sway set by the base engine
 document.querySelectorAll('[data-m=stage]').forEach(s=>{const k=S(t/1.0);s.style.transform='translateY('+((1-k)*40)+'px) scale('+(0.97+0.03*k)+')';s.style.opacity=S(t/0.6)});
};
})();
</script>
"""
