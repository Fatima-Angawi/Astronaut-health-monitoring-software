import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

/**
 * Shared page shell for all three dashboards: navbar, sidebar and the content area.
 *
 * The shell owns spacing/alignment/typography through the `.app-shell`, `.topbar`,
 * `.sidebar` and `main` rules in src/index.css, so every dashboard stays consistent
 * and responsive without repeating layout markup.
 */
export default function DashboardLayout({
  brand,
  meta,
  title,
  children,
}) {
  return (
    <div className="app-shell">
      <Navbar brand={brand} meta={meta} />
      <Sidebar />
      <main className="dashboard-main">
        {title && <h1>{title}</h1>}
        {children}
      </main>
    </div>
  );
}
