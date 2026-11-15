import { icons } from "../../data/icons";

/**
 * Shared top bar: brand block on the left, dashboard-specific read-outs on the right.
 *
 * All three dashboards render this same component, so positioning and styling stay
 * identical. `brand.logo` marks the mission logo, which keeps the original mirrored
 * logo treatment; the other dashboards pass a plain role icon.
 */
export default function Navbar({ brand, meta }) {
  return (
    <header className="topbar">
      <div className="brand">
        {brand.logo ? (
          <div className="logo-wrap">
            <img src={brand.icon} alt="" />
          </div>
        ) : (
          <img className="brand__icon" src={brand.icon} alt="" />
        )}
        <div>
          <strong>{brand.title}</strong>
          <span>{brand.subtitle}</span>
        </div>
      </div>

      <div className="mission-meta">
        {meta}
        <button type="button" aria-label="Notifications">
          <img src={icons.bell} alt="" />
        </button>
        <button className="user-button" type="button" aria-label="User profile">
          <img src={icons.user} alt="" />
        </button>
      </div>
    </header>
  );
}
