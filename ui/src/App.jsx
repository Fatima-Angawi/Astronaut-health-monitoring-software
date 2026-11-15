import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppStateProvider } from "./state/AppState";
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
        <Route path="/medical-officer" element={<MedicalOfficerDashboard />} />
        <Route path="/flight-surgeon" element={<FlightSurgeonDashboard />} />
        <Route path="*" element={<Navigate to="/astronaut" replace />} />
      </Routes>
    </BrowserRouter>
    </AppStateProvider>
  );
}
