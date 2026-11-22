"""Ilustración vectorial de los personajes del universo EGG (retratos estilo editorial, sombras y luces suaves).

Todo es SVG: se ve nítido a cualquier tamaño (4K incluido). Personajes originales; ninguno copia un personaje existente.
    portrait("egg", 300, "smug")   # moods: smug | wink | shock | laugh | neutral
"""
from __future__ import annotations

import hashlib

# name: hair, hair light, skin, skin shadow, outfit, outfit light, accent bg, iris, female?, extras
CHARACTERS = {
    "egg": dict(hair="#2a1710", hair2="#6b3f22", skin="#f0c09a", shade="#c98c66", top="#c9a227", top2="#f3d77a",
                bg=("#3b2a08", "#0a0704"), iris="#7a4a1c", female=True, extra={"hoops", "necklace", "vneck", "highlights"}),
    "mateo": dict(hair="#2e1b10", hair2="#5a3a22", skin="#c98d64", shade="#9c6644", top="#15803d", top2="#4ade80",
                  bg=("#0b3b20", "#04110a"), iris="#3b2414", female=False, extra={"cap", "stubble", "jersey"}),
    "santiago": dict(hair="#121212", hair2="#3a3a3a", skin="#d39a72", shade="#a8714e", top="#1e3a8a", top2="#3b5bc9",
                     bg=("#0d1d45", "#03070f"), iris="#2b1a10", female=False, extra={"beard", "suit"}),
    "valeria": dict(hair="#9f1d4a", hair2="#e0487a", skin="#f3cdb0", shade="#d09a7c", top="#f59e0b", top2="#fcd34d",
                    bg=("#4a0f25", "#12030a"), iris="#4a2a14", female=True, extra={"studs", "highlights"}),
    "sofia": dict(hair="#b8894f", hair2="#e6c38b", skin="#f3cfae", shade="#d1a080", top="#f3ecdc", top2="#ffffff",
                  bg=("#2c2620", "#0a0806"), iris="#3f6b4a", female=True, extra={"hoops", "highlights"}),
    "martina": dict(hair="#0e0a07", hair2="#3a2a20", skin="#dca27e", shade="#b27a58", top="#111111", top2="#3a3a3a",
                    bg=("#262016", "#080604"), iris="#3b2414", female=True, extra={"studs", "vneck"}),
    "diego": dict(hair="#0d0d0d", hair2="#333333", skin="#b8774f", shade="#8d5536", top="#166534", top2="#22c55e",
                  bg=("#0d2414", "#030a05"), iris="#2b1a10", female=False, extra={"stubble"}),
}
ALIASES = {"egg": "egg", "mateo": "mateo", "el profe": "mateo", "profe": "mateo", "santiago": "santiago", "el tiburon": "santiago",
           "el tiburón": "santiago", "tiburon": "santiago", "tiburón": "santiago", "valeria": "valeria", "sofia": "sofia",
           "sofía": "sofia", "martina": "martina", "diego": "diego"}


def character(who: str) -> dict:
    k = ALIASES.get(str(who or "").strip().lower().replace("'", "").replace('"', ""), "")
    if k:
        return CHARACTERS[k]
    h = int(hashlib.md5(str(who or "parce").lower().encode()).hexdigest(), 16)   # stable look for any friend's name
    skins = [("#f3cdb0", "#d09a7c"), ("#e2ac86", "#b97f5c"), ("#c98d64", "#9c6644"), ("#a8693f", "#7c4a2a"), ("#7d4b2d", "#5a321c")]
    hairs = [("#141414", "#3a3a3a"), ("#3b2416", "#6b4226"), ("#6b4226", "#9a6a43"), ("#b8894f", "#e6c38b"), ("#2a1710", "#5a3a22")]
    tops = [("#dc2626", "#f87171"), ("#2563eb", "#60a5fa"), ("#7c3aed", "#a78bfa"), ("#ea580c", "#fb923c"), ("#0d9488", "#2dd4bf"),
            ("#be123c", "#fb7185"), ("#16a34a", "#4ade80")]
    s, hr, t = skins[h % 5], hairs[(h // 5) % 5], tops[(h // 25) % 7]
    female = (h // 175) % 2 == 0
    extra = {"cap"} if (h // 350) % 3 == 0 and not female else ({"stubble"} if not female and (h // 350) % 3 == 1 else set())
    return dict(hair=hr[0], hair2=hr[1], skin=s[0], shade=s[1], top=t[0], top2=t[1], bg=("#20242c", "#07080a"),
                iris="#3b2414", female=female, extra=extra | ({"studs"} if female else set()))


def _eyes(c: dict, mood: str, uid: str) -> str:
    lash = 5 if c["female"] else 3.4
    out = []
    for cx, side in ((168, -1), (232, 1)):
        closed = mood == "laugh" or (mood == "wink" and side == 1)
        if closed:   # happy closed eye
            out.append(f"<path d='M{cx - 15} 172 Q{cx} {158} {cx + 15} 172' fill='none' stroke='#2a1710' stroke-width='{lash}' stroke-linecap='round'/>")
            continue
        ry = 12.5 if mood == "shock" else 9.5
        out.append(f"<ellipse cx='{cx}' cy='171' rx='15' ry='{ry}' fill='#fbf7f2'/>")
        out.append(f"<circle cx='{cx + side * 1.5}' cy='171' r='{8.6 if mood != 'shock' else 7.5}' fill='url(#iris{uid})'/>")
        out.append(f"<circle cx='{cx + side * 1.5}' cy='171' r='4' fill='#120a06'/>")
        out.append(f"<circle cx='{cx + side * 1.5 + 3}' cy='167.5' r='2.4' fill='#ffffff'/>")
        if mood == "smug":   # heavy lids: cover the top of the eye with skin
            out.append(f"<path d='M{cx - 17} 160 L{cx + 17} 160 L{cx + 17} 168 Q{cx} 163 {cx - 17} 168 Z' fill='{c['skin']}'/>")
            out.append(f"<path d='M{cx - 16} 168 Q{cx} 162 {cx + 16} 168' fill='none' stroke='#2a1710' stroke-width='{lash}' stroke-linecap='round'/>")
        else:
            top = 171 - ry
            out.append(f"<path d='M{cx - 16} 172 Q{cx} {top - 3} {cx + 16} 172' fill='none' stroke='#2a1710' stroke-width='{lash}' stroke-linecap='round'/>")
        if c["female"]:
            out.append(f"<path d='M{cx + side * 15} 169 l{side * 6} -5' stroke='#2a1710' stroke-width='3' stroke-linecap='round'/>")
    # brows
    lift = -7 if mood == "shock" else 0
    brow = 7 if not c["female"] else 5
    smug = mood == "smug"
    out.append(f"<path d='M150 {150 + lift} Q168 {140 + lift} {187} {148 + lift}' fill='none' stroke='{c['hair']}' stroke-width='{brow}' stroke-linecap='round'/>")
    out.append(f"<path d='M213 {148 + lift - (5 if smug else 0)} Q232 {138 + lift - (6 if smug else 0)} 250 {148 + lift}' fill='none' stroke='{c['hair']}' "
               f"stroke-width='{brow}' stroke-linecap='round'/>")
    return "".join(out)


def _mouth(c: dict, mood: str) -> str:
    lip = "#b4475a" if c["female"] else "#a0584f"
    if mood == "shock":
        return "<ellipse cx='201' cy='233' rx='10' ry='13' fill='#4a1a20'/><ellipse cx='201' cy='240' rx='6' ry='4' fill='#c25a68'/>"
    if mood == "laugh":
        return ("<path d='M176 222 Q201 258 226 222 Z' fill='#4a1a20'/><path d='M180 223 Q201 232 222 223 L222 226 Q201 235 180 226 Z' fill='#ffffff'/>"
                f"<path d='M176 222 Q201 258 226 222' fill='none' stroke='{lip}' stroke-width='3'/>")
    if mood in ("smug", "wink"):
        return (f"<path d='M180 230 Q196 236 210 232 Q220 229 228 221' fill='none' stroke='{lip}' stroke-width='{5 if c['female'] else 4}' stroke-linecap='round'/>"
                f"<path d='M184 233 Q200 241 214 235' fill='none' stroke='{c['shade']}' stroke-width='2' opacity='.5'/>")
    return (f"<path d='M181 229 Q191 224 201 227 Q211 224 221 229 Q211 236 201 236 Q191 236 181 229 Z' fill='{lip}'/>"
            "<path d='M183 229 Q201 232 219 229' stroke='#6e2a35' stroke-width='1.6' fill='none'/>")


def portrait(who: str = "egg", size: int = 300, mood: str = "smug", ring: bool = True) -> str:
    """Round bust portrait, vector (crisp at 4K)."""
    c = character(who)
    uid = hashlib.md5(f"{who}{mood}{size}".encode()).hexdigest()[:8]
    ex, fem = c["extra"], c["female"]
    hair_back = ("<path d='M92 175 C86 92 148 52 205 55 C272 58 318 106 310 182 C306 252 320 302 340 352 "
                 "C296 372 252 342 242 306 L160 306 C150 342 106 372 60 352 C82 302 96 252 92 175 Z' fill='url(#hair" + uid + ")'/>") if fem else ""
    face = ("<path d='M130 152 C130 100 165 80 201 80 C240 80 272 104 272 154 C272 206 252 250 222 268 "
            "C209 276 193 276 180 268 C150 250 130 206 130 152 Z' fill='url(#skin" + uid + ")'/>")
    face_shade = (f"<path d='M246 112 C268 132 274 170 266 206 C258 238 240 258 222 268 C240 240 252 200 250 160 C249 140 248 124 246 112 Z' "
                  f"fill='{c['shade']}' opacity='.35'/>")
    ears = "" if fem else (f"<ellipse cx='130' cy='175' rx='9' ry='15' fill='{c['skin']}'/><ellipse cx='272' cy='175' rx='9' ry='15' fill='{c['shade']}'/>")
    if fem:
        fringe = ("<path d='M124 168 C114 96 160 60 210 62 C262 64 292 104 284 170 C276 128 252 104 214 108 "
                  "C190 110 166 124 154 148 C146 140 132 150 124 168 Z' fill='url(#hair" + uid + ")'/>")
    else:
        fringe = ("<path d='M126 160 C118 92 162 62 204 62 C252 62 286 94 278 160 C272 128 252 108 216 104 "
                  "C186 102 156 112 140 134 C134 140 129 150 126 160 Z' fill='url(#hair" + uid + ")'/>")
    strands = (f"<path d='M170 76 C150 96 140 120 138 150' fill='none' stroke='{c['hair2']}' stroke-width='4' opacity='.55' stroke-linecap='round'/>"
               f"<path d='M222 70 C252 80 270 104 276 140' fill='none' stroke='{c['hair2']}' stroke-width='5' opacity='.45' stroke-linecap='round'/>")
    if fem and "highlights" in ex:
        strands += (f"<path d='M104 200 C100 250 108 300 90 340' fill='none' stroke='{c['hair2']}' stroke-width='6' opacity='.45' stroke-linecap='round'/>"
                    f"<path d='M300 210 C302 260 300 300 318 344' fill='none' stroke='{c['hair2']}' stroke-width='6' opacity='.4' stroke-linecap='round'/>")
    beard = (f"<path d='M134 182 C138 236 166 272 201 276 C236 272 264 236 268 182 C262 214 246 236 230 244 "
             f"C218 230 184 230 172 244 C156 236 140 214 134 182 Z' fill='{c['hair']}' opacity='.92'/>") if "beard" in ex else ""
    stubble = (f"<path d='M140 200 C148 244 172 268 201 272 C230 268 254 244 262 200 C252 236 230 256 201 258 C172 256 150 236 140 200 Z' "
               f"fill='{c['hair']}' opacity='.18'/>") if "stubble" in ex else ""
    cap = (f"<g transform='translate(0,-22)'><path d='M118 140 C118 80 160 52 204 52 C250 52 288 82 288 140 Z' fill='url(#top{uid})'/>"
           f"<path d='M118 140 C170 128 246 128 330 150 C300 160 250 156 200 150 C170 148 140 146 118 140 Z' fill='{c['top']}'/>"
           f"<circle cx='204' cy='54' r='6' fill='{c['top2']}'/></g>") if "cap" in ex else ""
    neck = (f"<path d='M172 252 L230 252 L238 314 Q201 334 164 314 Z' fill='{c['shade']}'/>"
            f"<path d='M172 262 Q201 286 230 262 L232 276 Q201 296 170 276 Z' fill='#000' opacity='.12'/>")
    body = "<path d='M38 400 C52 330 112 300 201 300 C290 300 350 330 364 400 Z' fill='url(#top" + uid + ")'/>"
    if "vneck" in ex:
        body += f"<path d='M168 302 L201 352 L234 302 Q201 318 168 302 Z' fill='{c['shade']}'/>"
    if "suit" in ex:
        body += ("<path d='M170 302 L201 380 L232 302 Q201 316 170 302 Z' fill='#f5f5f4'/><path d='M195 318 L207 318 L212 372 L201 386 L190 372 Z' fill='#7f1d1d'/>"
                 f"<path d='M150 306 L201 392 L178 400 L120 400 C126 352 136 322 150 306 Z' fill='{c['top2']}' opacity='.35'/>"
                 f"<path d='M252 306 L201 392 L224 400 L282 400 C276 352 266 322 252 306 Z' fill='#000' opacity='.18'/>")
    if "jersey" in ex:
        body += (f"<path d='M176 302 Q201 322 226 302' fill='none' stroke='#f5f5f4' stroke-width='8'/>"
                 f"<path d='M60 400 C70 360 92 336 120 324' fill='none' stroke='#f5f5f4' stroke-width='10' opacity='.8'/>"
                 f"<path d='M342 400 C332 360 310 336 282 324' fill='none' stroke='#f5f5f4' stroke-width='10' opacity='.8'/>")
    jewels = ""
    if "hoops" in ex:
        jewels += ("<circle cx='134' cy='206' r='11' fill='none' stroke='#e9c46a' stroke-width='4'/>"
                   "<circle cx='268' cy='206' r='11' fill='none' stroke='#c9a227' stroke-width='4'/>")
    if "studs" in ex:
        jewels += "<circle cx='136' cy='196' r='4.5' fill='#f5e6b8'/><circle cx='266' cy='196' r='4.5' fill='#e9d9a8'/>"
    if "necklace" in ex:
        jewels += ("<path d='M164 300 Q201 336 238 300' fill='none' stroke='#f3d77a' stroke-width='3'/>"
                   "<path d='M201 330 l7 10 l-7 10 l-7 -10 Z' fill='#f3d77a'/>")
    nose = (f"<path d='M203 180 Q198 200 192 207 Q201 213 211 207' fill='none' stroke='{c['shade']}' stroke-width='3.2' "
            f"stroke-linecap='round' opacity='.85'/>")
    blush = (f"<ellipse cx='154' cy='206' rx='15' ry='8' fill='#f08a8a' opacity='{.32 if fem else .14}' filter='url(#blur{uid})'/>"
             f"<ellipse cx='248' cy='206' rx='15' ry='8' fill='#f08a8a' opacity='{.32 if fem else .14}' filter='url(#blur{uid})'/>")
    bg0, bg1 = c["bg"]
    ring_css = (f"box-shadow:0 0 0 {max(3, size // 34)}px #d4af37,0 0 0 {max(4, size // 26)}px #5a4510,0 {size // 12}px {size // 5}px #000b;"
                if ring else "")
    return f"""<svg width='{size}' height='{size}' viewBox='0 0 400 400' style='flex:none;border-radius:50%;{ring_css}' xmlns='http://www.w3.org/2000/svg'>
<defs>
 <radialGradient id='bg{uid}' cx='50%' cy='35%' r='75%'><stop offset='0' stop-color='{bg0}'/><stop offset='1' stop-color='{bg1}'/></radialGradient>
 <linearGradient id='skin{uid}' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='{c['skin']}'/><stop offset='1' stop-color='{c['shade']}'/></linearGradient>
 <linearGradient id='hair{uid}' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='{c['hair2']}'/><stop offset='.45' stop-color='{c['hair']}'/><stop offset='1' stop-color='{c['hair']}'/></linearGradient>
 <linearGradient id='top{uid}' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='{c['top2']}'/><stop offset='1' stop-color='{c['top']}'/></linearGradient>
 <radialGradient id='iris{uid}' cx='40%' cy='35%' r='70%'><stop offset='0' stop-color='#ffffff' stop-opacity='.35'/><stop offset='.35' stop-color='{c['iris']}'/><stop offset='1' stop-color='#120a06'/></radialGradient>
 <radialGradient id='glow{uid}' cx='30%' cy='20%' r='60%'><stop offset='0' stop-color='#fff4c9' stop-opacity='.35'/><stop offset='1' stop-color='#fff4c9' stop-opacity='0'/></radialGradient>
 <filter id='blur{uid}'><feGaussianBlur stdDeviation='4'/></filter>
 <clipPath id='clip{uid}'><circle cx='200' cy='200' r='200'/></clipPath>
</defs>
<g clip-path='url(#clip{uid})'>
 <rect width='400' height='400' fill='url(#bg{uid})'/>
 <circle cx='320' cy='70' r='120' fill='#d4af37' opacity='.08'/>
 {hair_back}{body}{jewels if 'necklace' in ex else ''}{neck}{ears}{face}{face_shade}{stubble}{beard}{blush}
 {_eyes(c, mood, uid)}{nose}{_mouth(c, mood)}{fringe}{strands}{cap}{jewels if 'necklace' not in ex else jewels.replace(jewels[jewels.find("<path d='M164"):], '')}
 <rect width='400' height='400' fill='url(#glow{uid})'/>
</g></svg>"""
