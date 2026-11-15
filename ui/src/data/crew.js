/**
 * MOCK crew roster, shared by the Medical Officer and Flight Surgeon dashboards.
 *
 * `tone` is a presentation hint only — it mirrors the severity the backend Rules
 * Engine (engine/rules.py) assigns to each crew member's worst active alert.
 * No severity is calculated in the frontend.
 *
 * Replace with `GET /crew` (see src/services/apiClient.js) when it exists.
 */
export const crew = [
  { code: "A1", name: "Fatima Angawi", role: "Commander", status: "Normal", tone: "green", sleep7dH: 6.4 },
  { code: "A2", name: "Ahmed Kamal", role: "Flight Engineer", status: "Red", tone: "red", sleep7dH: 4.8 },
  { code: "A3", name: "Talal Alomyri", role: "Specialist 1", status: "Yellow", tone: "yellow", sleep7dH: 6.3 },
  { code: "A4", name: "Afnan Alsharif", role: "Specialist 1", status: "Normal", tone: "green", sleep7dH: 6.5 },
];
