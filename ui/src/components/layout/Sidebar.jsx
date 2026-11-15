import { NavLink } from "react-router-dom";
import { dashboardRoutes } from "../../data/navigation";

/**
 * Shared icon rail.
 *
 *  - the top group links the three role dashboards and marks the active one;
 *  - the bottom group is the in-page section navigation of the current dashboard.
 */
export default function Sidebar({ sections = [], activeSection, onSectionChange }) {
  return (
    <nav className="sidebar" aria-label="Main navigation">
      <div className="sidebar__group">
        {dashboardRoutes.map((route) => (
          <NavLink
            key={route.id}
            to={route.path}
            className={({ isActive }) => (isActive ? "sidebar__item active" : "sidebar__item")}
            aria-label={route.label}
            title={route.label}
          >
            <img src={route.icon} alt="" />
          </NavLink>
        ))}
      </div>

      
    </nav>
  );
}
