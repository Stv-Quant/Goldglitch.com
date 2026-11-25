"""Editor-grade transitions ("let him cook" cuts), built frame by frame from the end of one scene and the start of
the next: zoom-through with radial blur, whip pans with motion blur, spin, drop with bounce, luxury slices and a gold
light leak. Every cut uses a speed ramp (slow-fast-slow) so the motion snaps on the beat.

make(a_frames, b_frames, kind, out_dir) -> number of frames written (30 fps, out_dir/0001.jpg…)."""
from __future__ import annotations

import math
import os

import numpy as np
from PIL import Image, ImageFilter

FPS = 30
N = 10                                   # 0.33 s per cut: long enough to read, short enough to snap
W, H = 1080, 1920
GOLD = np.array([231, 194, 90], dtype=np.float32)

KINDS = ("zoom", "whip_l", "spin", "drop", "slices", "leak", "whip_u", "punch")
LOOK_CUTS = {   # each luxury room has its own editing grammar
    "club": ("zoom", "whip_l", "leak", "slices", "punch", "whip_u"),
    "stmoritz": ("leak", "whip_l", "zoom", "drop", "whip_u"),
    "esmeralda": ("zoom", "spin", "whip_l", "slices", "punch", "drop"),
    "bbc": ("punch", "zoom", "spin", "whip_u", "slices", "whip_l"),
    "noche": ("leak", "zoom", "whip_u", "slices", "punch"),
}


def kind_for(look: str, i: int, seed: int = 0) -> str:
    seq = LOOK_CUTS.get(look, KINDS)
    return seq[(i + seed) % len(seq)]


def ramp(x: float) -> float:
    """Speed ramp: barely moves, then whips, then settles (smootherstep pushed harder)."""
    x = min(max(x, 0.0), 1.0)
    s = x * x * x * (x * (x * 6 - 15) + 10)
    return s ** 1.15 if s < .5 else 1 - (1 - s) ** 1.15


def _arr(im: Image.Image) -> np.ndarray:
    return np.asarray(im.convert("RGB").resize((W, H)), dtype=np.float32)


def _img(a: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def _zoom(a: np.ndarray, z: float) -> np.ndarray:
    """Scale around the centre, keeping the canvas (z>1 = push in)."""
    if abs(z - 1) < 1e-3:
        return a
    im = _img(a)
    if z > 1:
        cw, ch = W / z, H / z
        x0, y0 = (W - cw) / 2, (H - ch) / 2
        return _arr(im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch)))
    sw, sh = max(2, int(W * z)), max(2, int(H * z))
    out = Image.new("RGB", (W, H), (0, 0, 0))
    out.paste(im.resize((sw, sh), Image.BILINEAR), ((W - sw) // 2, (H - sh) // 2))
    return _arr(out)


def _zoom_blur(a: np.ndarray, z: float, strength: float) -> np.ndarray:
    """Radial (zoom) motion blur: average of several pushes around the target zoom."""
    if strength < .02:
        return _zoom(a, z)
    taps = [z * (1 + strength * .35 * k / 4) for k in range(5)]
    return sum(_zoom(a, t) for t in taps) / len(taps)


def _shift(a: np.ndarray, dx: int, dy: int) -> np.ndarray:
    out = np.zeros_like(a)
    xs, xd = (slice(0, W - dx), slice(dx, W)) if dx >= 0 else (slice(-dx, W), slice(0, W + dx))
    ys, yd = (slice(0, H - dy), slice(dy, H)) if dy >= 0 else (slice(-dy, H), slice(0, H + dy))
    if abs(dx) < W and abs(dy) < H:
        out[yd, xd] = a[ys, xs]
    return out


def _motion_blur(a: np.ndarray, dx: float, dy: float, taps: int = 7) -> np.ndarray:
    """Directional blur along (dx, dy) pixels."""
    if abs(dx) + abs(dy) < 2:
        return a
    return sum(_shift(a, int(dx * k / (taps - 1) - dx / 2), int(dy * k / (taps - 1) - dy / 2))
               for k in range(taps)) / taps


def _rotate(a: np.ndarray, deg: float, z: float = 1.0) -> np.ndarray:
    im = _img(_zoom(a, z)).rotate(deg, resample=Image.BILINEAR, fillcolor=(0, 0, 0))
    return _arr(im)


def _flash(a: np.ndarray, amt: float, warm: bool = True) -> np.ndarray:
    tint = GOLD if warm else np.array([255, 255, 255], dtype=np.float32)
    return a * (1 - amt) + (a * .35 + tint * .9) * amt


def _bloom(a: np.ndarray, amt: float) -> np.ndarray:
    if amt < .02:
        return a
    glow = _arr(_img(a).filter(ImageFilter.GaussianBlur(28)))
    return a + glow * amt * .8


def _chroma(a: np.ndarray, px: int) -> np.ndarray:
    """RGB split (the EGG gold glitch), strongest at the cut."""
    if px < 1:
        return a
    out = a.copy()
    out[..., 0] = _shift(a, -px, 0)[..., 0]
    out[..., 2] = _shift(a, px, 0)[..., 2]
    return out


def frame(A: np.ndarray, B: np.ndarray, kind: str, x: float) -> np.ndarray:
    """One transition frame at progress x in [0, 1]."""
    r = ramp(x)
    peak = math.sin(math.pi * x)                       # 0 → 1 (mid) → 0
    first = r < .5
    if kind == "zoom":                                 # push through A, land in B from a zoomed blur
        out = _zoom_blur(A, 1 + 2.2 * r * 2, peak) if first else _zoom_blur(B, 1 + 2.2 * (1 - r) * 2, peak)
        out = _flash(out, max(0, peak - .55) * 1.6)
    elif kind == "punch":                              # hard punch-in on the beat, B snaps back from 1.35
        out = _zoom(A, 1 + .5 * r * 2) if first else _zoom_blur(B, 1 + .35 * (1 - r) * 2, peak * .7)
        out = _flash(out, max(0, peak - .7) * 2.4, warm=False)
    elif kind in ("whip_l", "whip_u"):                # whip pan: A leaves, B arrives, both smeared
        horiz = kind == "whip_l"
        span, v = (W if horiz else H), peak * (.55 if horiz else .45)
        off = int(r * span)
        dA = (-off, 0) if horiz else (0, -off)
        dB = (span - off, 0) if horiz else (0, span - off)
        a = _shift(A, *dA)
        b = _shift(B, *dB)
        blur = (span * v, 0) if horiz else (0, span * v)
        out = _motion_blur(a + b, *blur)
    elif kind == "spin":                               # spin + zoom blur, 120° each side
        out = (_rotate(A, -120 * r * 2, 1 + .6 * r * 2) if first else _rotate(B, 120 * (1 - r) * 2, 1 + .6 * (1 - r) * 2))
        out = _zoom_blur(out, 1.0, peak * .6)
    elif kind == "drop":                               # A falls away, B drops in with a small bounce
        if first:
            out = _motion_blur(_shift(A, 0, int(H * r * 2)), 0, H * peak * .25)
        else:
            y = 1 - (r - .5) * 2
            bounce = math.sin((r - .5) * 2 * math.pi * 1.5) * math.exp(-(r - .5) * 6) * .06
            out = _motion_blur(_shift(B, 0, int(-H * (y * y) + H * bounce)), 0, H * peak * .25)
    elif kind == "slices":                             # 8 bands slide in alternating directions
        out = A.copy()
        bands = 8
        for k in range(bands):
            y0, y1 = H * k // bands, H * (k + 1) // bands
            lag = k / bands * .35
            p = ramp(min(max((x - lag) / .65, 0), 1))
            dx = int((1 - p) * W * (1 if k % 2 else -1))
            out[y0:y1] = _shift(B, dx, 0)[y0:y1] + _shift(A, dx - (W if k % 2 else -W), 0)[y0:y1] * (p > 0)
            if p == 0:
                out[y0:y1] = A[y0:y1]
        out = _motion_blur(out, W * peak * .08, 0, 5)
    else:                                              # leak: a gold light leak sweeps across and swaps the scene
        mix = ramp(min(max((x - .25) / .5, 0), 1))
        base = A * (1 - mix) + B * mix
        xs = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
        ys = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        c = -.3 + 1.6 * r
        band = np.exp(-(((xs + ys * .45) - c) ** 2) / .025)
        out = base + band * GOLD * 1.1 * peak
        out = _bloom(out, peak * .6)
    out = _chroma(out, int(10 * peak))
    return out


def make(a_frames: list[str], b_frames: list[str], kind: str, out_dir: str) -> int:
    """a_frames: the last N frames of scene A (paths); b_frames: the first N of scene B. Writes N frames."""
    os.makedirs(out_dir, exist_ok=True)
    for k in range(N):
        A = _arr(Image.open(a_frames[min(k, len(a_frames) - 1)]))
        B = _arr(Image.open(b_frames[min(k, len(b_frames) - 1)]))
        _img(frame(A, B, kind, k / (N - 1))).save(os.path.join(out_dir, f"{k + 1:04d}.jpg"), quality=88)
    return N
