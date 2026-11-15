import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppStateProvider } from "./state/AppState";
import TrendsPage from "./pages/detail/TrendsPage";
import CrewSummaryPage from "./pages/detail/CrewSummaryPage";
import AlertsPage from "./pages/detail/AlertsPage";
import EnvironmentPage from "./pages/detail/EnvironmentPage";
import { PAGES } from "./data/detailPages";
import AstronautDashboard from "./pages/Astronaut/AstronautDashboard";
import MedicalOfficerDashboard from "./pages/MedicalOfficer/MedicalOfficerDashboard";
import FlightSurgeonDashboard from "./pages/FlightSurgeon/FlightSurgeonDashboard";

/**
 * Application routes.
 *
 * The three role dashboards share `components/layout/DashboardLayout`, so switching roles
 * only swaps the page content. `/astronaut` is the default landing dashboard.
 */
export default function App() {
  return (
    <AppStateProvider>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/astronaut" replace />} />
        <Route path="/astronaut" element={<AstronautDashboard />} />
        {["sleep", "reaction", "mood", "activity"].map((k) => (
          <Route key={k} path={`/astronaut/${k}`} element={<TrendsPage role="astronaut" {...PAGES[k]} />} />
        ))}
        <Route path="/astronaut/environment" element={<EnvironmentPage role="astronaut" />} />
        <Route path="/medical-officer/alerts" element={<AlertsPage role="medical-officer" />} />
        <Route path="/medical-officer/crew" element={<TrendsPage role="medical-officer" {...PAGES.crew} />} />
        <Route path="/medical-officer/environment" element={<EnvironmentPage role="medical-officer" />} />
        <Route path="/flight-surgeon/alerts" element={<AlertsPage role="flight-surgeon" />} />
        <Route path="/flight-surgeon/summary" element={<CrewSummaryPage role="flight-surgeon" />} />
        <Route path="/flight-surgeon/crew" element={<TrendsPage role="flight-surgeon" {...PAGES.crew} />} />
        <Route path="/flight-surgeon/environment" element={<EnvironmentPage role="flight-surgeon" />} />
        <Route path="/medical-officer" element={<MedicalOfficerDashboard />} />
        <Route path="/flight-surgeon" element={<FlightSurgeonDashboard />} />
        <Route path="*" element={<Navigate to="/astronaut" replace />} />
      </Routes>
    </BrowserRouter>
    </AppStateProvider>
  );
}
