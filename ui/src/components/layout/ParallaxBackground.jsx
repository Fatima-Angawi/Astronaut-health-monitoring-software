import { useEffect, useRef } from "react";

/**
 * Scroll-linked Earth backdrop shared by every page using DashboardLayout.
 * Only the background layer receives style updates; scrolling never re-renders dashboard content.
 */
export default function ParallaxBackground() {
  const layerRef = useRef(null);

  useEffect(() => {
    const layer = layerRef.current;
    if (!layer) return undefined;

    // This app scrolls the document. Observe both root and window for browser consistency.
    const scroller = document.scrollingElement ?? document.documentElement;
    let frameId = null;

    const update = () => {
      frameId = null;
      const scrollRange = Math.max(0, scroller.scrollHeight - scroller.clientHeight);
      const progress = scrollRange ? Math.min(1, Math.max(0, scroller.scrollTop / scrollRange)) : 0;
      const styles = window.getComputedStyle(layer);
      const start = Number.parseFloat(styles.getPropertyValue("--parallax-start")) || 0;
      const travel = Number.parseFloat(styles.getPropertyValue("--parallax-travel")) || 0;
      layer.style.setProperty("--parallax-offset", `${(start - progress * travel).toFixed(2)}px`);
    };

    const scheduleUpdate = () => {
      if (frameId === null) frameId = window.requestAnimationFrame(update);
    };

    const motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const resizeObserver =
      typeof ResizeObserver === "undefined" ? null : new ResizeObserver(scheduleUpdate);
    resizeObserver?.observe(document.documentElement);

    update();
    scroller.addEventListener("scroll", scheduleUpdate, { passive: true });
    window.addEventListener("scroll", scheduleUpdate, { passive: true });
    window.addEventListener("resize", scheduleUpdate);
    motionPreference.addEventListener("change", scheduleUpdate);

    return () => {
      scroller.removeEventListener("scroll", scheduleUpdate);
      window.removeEventListener("scroll", scheduleUpdate);
      window.removeEventListener("resize", scheduleUpdate);
      motionPreference.removeEventListener("change", scheduleUpdate);
      resizeObserver?.disconnect();
      if (frameId !== null) window.cancelAnimationFrame(frameId);
    };
  }, []);

  return (
    <div className="parallax" aria-hidden="true">
      <div className="parallax__image" ref={layerRef} />
      <div className="parallax__scrim" />
    </div>
  );
}
