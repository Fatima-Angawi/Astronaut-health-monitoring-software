import { useEffect, useRef, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { ChevronDown } from "lucide-react";
import Icon from "../common/Icon";
import { dashboardRoutes } from "../../data/navigation";
import { icons } from "../../data/icons";

/**
 * Shared app identity, dashboard switcher and dashboard-specific read-outs.
 */
export default function Navbar({ brand, meta, navOpen = false, onMenuToggle }) {
  const { pathname } = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const switcherRef = useRef(null);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  const activeRoute = dashboardRoutes.find(
    (route) => pathname === route.path || pathname.startsWith(`${route.path}/`),
  );
  const brandMark = activeRoute?.brandMark ?? (brand.logo ? "logo" : "icon");
  const brandIcon = activeRoute?.brandIcon ?? brand.icon ?? icons.logo;
  const brandTone = activeRoute?.brandTone ?? "nav";
  const brandTitle = activeRoute?.label ?? brand.title;
  const brandSubtitle = activeRoute?.subtitle ?? brand.subtitle;

  const closeMenu = (restoreFocus = false) => {
    setMenuOpen(false);
    if (restoreFocus) triggerRef.current?.focus();
  };

  useEffect(() => {
    if (!menuOpen) return undefined;

    const onPointerDown = (event) => {
      if (!switcherRef.current?.contains(event.target)) setMenuOpen(false);
    };
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        setMenuOpen(false);
        triggerRef.current?.focus();
      }
    };

    menuRef.current?.querySelector('[aria-checked="true"]')?.focus();
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [menuOpen]);

  const onMenuKeyDown = (event) => {
    if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
    const items = [...(menuRef.current?.querySelectorAll('[role="menuitemradio"]') ?? [])];
    if (!items.length) return;

    event.preventDefault();
    const currentIndex = items.indexOf(document.activeElement);
    if (event.key === "Home") items[0].focus();
    else if (event.key === "End") items[items.length - 1].focus();
    else {
      const direction = event.key === "ArrowDown" ? 1 : -1;
      const nextIndex = (currentIndex + direction + items.length) % items.length;
      items[nextIndex].focus();
    }
  };

  return (
    <header className="topbar">
      <button
        type="button"
        className="menu-toggle"
        onClick={onMenuToggle}
        aria-label={navOpen ? "Close navigation" : "Open navigation"}
        aria-expanded={navOpen}
        aria-controls="app-sidebar"
      >
        <Icon src={icons.menu} size={22} tone="nav" />
      </button>

      <div className="dashboard-switcher" ref={switcherRef}>
        <button
          type="button"
          className="brand brand-trigger"
          ref={triggerRef}
          onClick={() => setMenuOpen((open) => !open)}
          aria-expanded={menuOpen}
          aria-haspopup="menu"
          aria-controls="dashboard-switcher-menu"
        >
          {brandMark === "logo" ? (
            <span className="logo-wrap">
              <img src={brandIcon} alt="" />
            </span>
          ) : (
            <span className="brand__icon-wrap">
              <Icon className="brand__mark" src={brandIcon} size={44} tone={brandTone} />
            </span>
          )}
          <span className="brand__copy">
            <strong>{brandTitle}</strong>
            <span>{brandSubtitle}</span>
          </span>
          <ChevronDown className="brand__chevron" size={18} aria-hidden="true" />
        </button>

        <div
          className="dashboard-switcher__menu"
          id="dashboard-switcher-menu"
          role="menu"
          aria-label="Switch dashboard"
          aria-orientation="vertical"
          hidden={!menuOpen}
          ref={menuRef}
          onKeyDown={onMenuKeyDown}
        >
          <span className="dashboard-switcher__eyebrow" role="presentation">Switch dashboard</span>
          {dashboardRoutes.map((route) => {
            const isActive = activeRoute?.id === route.id;
            return (
              <NavLink
                key={route.id}
                to={route.path}
                role="menuitemradio"
                aria-checked={isActive}
                aria-current={isActive ? "page" : undefined}
                className={isActive ? "dashboard-switcher__option is-active" : "dashboard-switcher__option"}
                onClick={() => closeMenu()}
              >
                <Icon src={route.icon} size={22} tone={route.iconTone ?? "nav"} />
                <span>{route.label}</span>
                {isActive && <Icon src={icons.check} size={16} tone="success" className="dashboard-switcher__check" />}
              </NavLink>
            );
          })}
        </div>
      </div>

      <div className="mission-meta">
        <div className="mission-info">{meta}</div>
        <div className="mission-actions">
          <button className="icon-button" type="button" aria-label="Notifications">
            <Icon src={icons.bell} size={24} tone="nav" />
          </button>
        </div>
      </div>
    </header>
  );
}
