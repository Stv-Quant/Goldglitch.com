# Película del recorrido (landing)

Vuelo de cámara continuo por 6 escenarios nocturnos (ruido → fútbol → MLB → NBA → NHL → la señal), renderizado
con Three.js en Chrome headless. Costo $0, determinista: `renderAt(t)` siempre produce el mismo cuadro.

```bash
cd film && npm i three@0.170 esbuild puppeteer-core@23
npx esbuild src/entry.js --bundle --format=iife --outfile=bundle.js
node render.mjs 1920 1080 24 36 frames-d   # escritorio 16:9 (~20 min en 2 núcleos)
node render.mjs 720 1280 24 36 frames-m    # móvil 9:16 nativo
```

Encode (2 pasadas; el grano por cuadro obliga a denoise + bitrate fijo para quedar < 25 MB por archivo de Workers):

```bash
ffmpeg -framerate 24 -i frames-d/f%05d.jpg -vf hqdn3d=6:5:8:6 -c:v libx264 -preset slow -b:v 4800k -maxrate 6000k \
  -bufsize 9600k -pass 1 -pix_fmt yuv420p -g 8 -keyint_min 8 -sc_threshold 0 -an -f mp4 /dev/null
# …-pass 2 … -movflags +faststart ../next/public/film/recorrido.mp4   (móvil: -b:v 2200k, -g 4 → recorrido-m.mp4)
```

Capítulos del scroll en `next/components/landing/FilmScrub.tsx` (`CHAPTERS[].at`, fracción del video).
