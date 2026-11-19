import { createFilm } from "./world.js";
const q = new URLSearchParams(location.search);
const W = +q.get("w") || 1920, H = +q.get("h") || 1080;
const canvas = document.getElementById("c");
window.film = createFilm(canvas, W, H);
window.grab = (t, type = "image/jpeg", quality = 0.95) => { window.film.renderAt(t); return canvas.toDataURL(type, quality); };
window.ready = true;
