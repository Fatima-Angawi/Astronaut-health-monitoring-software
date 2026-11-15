import DashboardLayout from "../../components/layout/DashboardLayout";
import MissionControls from "../../components/layout/MissionControls";
import { brands } from "../../data/navigation";

/** Shared frame of every detail page: the role's navbar and sidebar, a title and a short intro. */
export default function DetailShell({ role, title, intro, showAstronaut = true, children }) {
  return (
    <DashboardLayout brand={brands[role]} title={title} meta={<MissionControls showAstronaut={showAstronaut} />}>
      {intro && <p className="detail-intro">{intro}</p>}
      {children}
    </DashboardLayout>
  );
}
