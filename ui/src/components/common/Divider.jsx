import { icons } from "../../data/icons";

/**
 * Hairline rule used between panel sections (replaces the ad-hoc divider image that was
 * referenced by a file which did not exist in the project).
 */
export default function Divider() {
  return (
    <div className="divider" aria-hidden="true">
      <img src={icons.divider} alt="" />
    </div>
  );
}
