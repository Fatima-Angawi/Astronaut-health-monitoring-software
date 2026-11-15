import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import Navbar from "./Navbar";
import ParallaxBackground from "./ParallaxBackground";
import Sidebar from "./Sidebar";

/**
 * Shared page shell for all three dashboards: navbar, sidebar and the content area.
 *
 * The shell owns spacing, alignment and typography through the `.app-shell`, `.topbar`,
 * `.sidebar` and `main` rules in src/index.css, so every dashboard stays consistent and
 * responsive without repeating layout markup.
 *
 * It also owns the mobile navigation state: below 768px the sidebar is an off-canvas drawer
 * opened from the navbar and closed by the close button, the backdrop, Escape, or by following
 * a link (the drawer's links call `onClose`). From 768px up the drawer state has no effect on
 * the fixed rail.
 *
 * The Earth horizon background is mounted once here for all dashboards using this shared shell.
 */
export default function DashboardLayout({ brand, meta, title, children }) {
  const [navOpen, setNavOpen] = useState(false);
  const { pathname } = useLocation();

  useEffect(() => {
    if (!navOpen) return undefined;
    const onKeyDown = (event) => {
      if (event.key === "Escape") setNavOpen(false);
    };
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [navOpen]);

  return (
    <div className="app-shell">
      <ParallaxBackground />
      <Navbar brand={brand} meta={meta} navOpen={navOpen} onMenuToggle={() => setNavOpen((open) => !open)} />
      <Sidebar open={navOpen} onClose={() => setNavOpen(false)} />
      <main className="dashboard-main" key={pathname}>
        {title && <h1>{title}</h1>}
        {children}
      </main>
    </div>
  );
}
