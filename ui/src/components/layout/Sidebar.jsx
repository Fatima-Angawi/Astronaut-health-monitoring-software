import { NavLink, useLocation } from "react-router-dom";
import { dashboardRoutes, sectionRoutes } from "../../data/navigation";

const linkClass = ({ isActive }) => (isActive ? "sidebar__item active" : "sidebar__item");

/**
 * Left rail with two groups:
 *  - the three screens (astronaut, medical officer, flight surgeon);
 *  - the detail pages of the screen you are on (sleep, reaction, mood, ...).
 */
export default function Sidebar() {
  const { pathname } = useLocation();
  const role = dashboardRoutes.find((r) => pathname === r.path || pathname.startsWith(`${r.path}/`));
  const sections = role ? sectionRoutes[role.id] : [];

  return (
    <nav className="sidebar" aria-label="Main navigation">
      <div className="sidebar__group">
        {dashboardRoutes.map((route) => (
          <NavLink key={route.id} to={route.path} className={() => (role?.id === route.id ? "sidebar__item active" : "sidebar__item")} aria-label={route.label} title={route.label}>
            <img src={route.icon} alt="" />
          </NavLink>
        ))}
      </div>
      <span className="sidebar__divider" role="separator" />
      <div className="sidebar__group">
        {sections.map((s) => (
          <NavLink key={s.id} to={s.path} end={s.end} className={linkClass} aria-label={s.label} title={s.label}>
            <img src={s.icon} alt="" />
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
