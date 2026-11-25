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
const nums=[...document.querySelectorAll('[data-m=num]')];
const fills=[...document.querySelectorAll('[data-m=fill]')];
fills.forEach(f=>f.style.transformOrigin='0 50%');
const q=s=>[...document.querySelectorAll('[data-m='+s+']')];
window.__egg=function(t,T){
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
 q('big').forEach(el=>{if(el.dataset.count){const p=cl((t-0.12)/0.95);el.textContent=Math.round(E(p)*(+el.dataset.n))+'%';
  el.style.transform='scale('+(0.6+0.4*B(cl((t-0.05)/0.5)))+')'}
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


def inject(html: str, look: str = "terminal") -> str:
    eng = f"<script>window.__look={look!r};</script>" + ENGINE
    return html.replace("</body>", eng + "</body>", 1) if "</body>" in html else html + eng


def scene_frames(pg, html: str, seconds: float, out_dir: str, look: str = "terminal") -> int:
    """Render one animated scene into out_dir/0001.jpg… Returns the number of frames."""
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir, exist_ok=True)
    pg.set_content(inject(html, look), wait_until="networkidle")
    pg.evaluate("document.fonts.ready.then(()=>1)")
    n = max(2, int(round(seconds * FPS)))
    for i in range(n):
        pg.evaluate(f"window.__egg({i / FPS:.4f},{seconds:.4f})")
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
            scene_frames(pg, h, s, d, look)
            dirs.append(d)
        b.close()
    return dirs


def enabled() -> bool:
    return os.environ.get("REDES_MOVIMIENTO", "1") != "0"
