import { describe, expect, it } from "vitest";
import { buildFormations } from "@/components/experience/formations";
import { makeSim } from "@/components/experience/sims";

describe("live sims", () => {
  for (const [w, h] of [[1440, 900], [390, 844]]) {
    it(`never produce NaN and keep agents near the field (${w}x${h})`, () => {
      const F = buildFormations(6500, w, h);
      F.forEach((f, fi) => {
        for (const arr of [f.x, f.y, f.z]) expect(arr.every(Number.isFinite), `formation ${fi} base`).toBe(true);
        const sim = makeSim(f, 11 + fi);
        if (!sim) return;
        let t = 0;
        for (let k = 0; k < 60 * 40; k++) { // 40 simulated seconds
          t += 1 / 60;
          sim.step(t, 1 / 60);
          for (const arr of [sim.ox, sim.oy, sim.oz, sim.sz]) {
            const bad = Array.from(arr).findIndex((v) => !Number.isFinite(v));
            if (bad >= 0) throw new Error(`formation ${fi} (${f.sim!.kind}) NaN at group ${bad}, t=${t.toFixed(2)}`);
          }
          const lim = Math.max(w, h) * 1.5;
          expect(Math.max(...Array.from(sim.ox).map(Math.abs)), `formation ${fi} ox bound`).toBeLessThan(lim);
        }
      });
    });
  }
});
