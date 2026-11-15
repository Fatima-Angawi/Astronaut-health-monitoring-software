import { NavLink, useLocation } from "react-router-dom";
import Icon from "../common/Icon";
import { icons } from "../../data/icons";
import { dashboardRoutes, sectionRoutes } from "../../data/navigation";

const linkClass = ({ isActive }) => (isActive ? "sidebar__item active" : "sidebar__item");

/**
 * Navigation rail with the detail pages of the current dashboard (sleep, reaction, alerts, ...).
 *
 * From 768px up this is the fixed icon rail of the Figma design. Below 768px the same markup
 * becomes an off-canvas drawer: the navbar menu button opens it, and the close button, the
 * backdrop or Escape closes it (the state lives in DashboardLayout).
 */
export default function Sidebar({ open = false, onClose }) {
  const { pathname } = useLocation();
  const role = dashboardRoutes.find((r) => pathname === r.path || pathname.startsWith(`${r.path}/`));
  const sections = role ? sectionRoutes[role.id] : [];

  return (
    <>
      <button
        type="button"
        className={open ? "sidebar-backdrop is-open" : "sidebar-backdrop"}
        tabIndex={-1}
        aria-label="Close navigation"
        onClick={onClose}
      />
      <nav id="app-sidebar" className={open ? "sidebar is-open" : "sidebar"} aria-label="Main navigation">
        <div className="sidebar__header">
          <span className="sidebar__title">Navigation</span>
          <button type="button" className="sidebar__close" onClick={onClose} aria-label="Close navigation">
            <Icon src={icons.close} size={20} tone="nav" />
          </button>
        </div>

        <div className="sidebar__group">
          {sections.map((s) => (
            <NavLink
              key={s.id}
              to={s.path}
              end={s.end}
              className={linkClass}
              aria-label={s.label}
              title={s.label}
              onClick={onClose}
            >
              <Icon src={s.icon} size={30} tone="nav" />
              <span className="sidebar__label">{s.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </>
  );
}
