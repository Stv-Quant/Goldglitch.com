"use client";

import { useEffect } from "react";

/** Adds .is-in to every .reveal-on-enter section once it scrolls into view. */
export function RevealObserver() {
  useEffect(() => {
    const els = document.querySelectorAll(".reveal-on-enter");
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add("is-in");
          io.unobserve(e.target);
        }
      }),
      { rootMargin: "0px 0px -20% 0px" },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);
  return null;
}
