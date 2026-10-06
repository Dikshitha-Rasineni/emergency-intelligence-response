import { Routes, Route } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import CommandCenter from './pages/CommandCenter'
import Pending from './pages/Pending'
import EmergencyReport from './pages/EmergencyReport'
import ActiveIncidents from './pages/ActiveIncidents'
import IncidentDetails from './pages/IncidentDetails'

/* Routes only. Screens live in pages/, layout in components/layout/. */
const later = [
  ['resources', 'Resource intelligence', '/api/resources/nearby'],
  ['map', 'Emergency map', '/api/dashboard/resources'],
  ['intelligence', 'Response intelligence', '/api/ai/response'],
  ['sensors', 'Sensor monitoring', '/api/iot/events'],
  ['analytics', 'Analytics', '/api/dashboard/analytics'],
  ['history', 'Incident history', '/api/incidents'],
  ['admin', 'Users', null],
  ['settings', 'Settings', null],
]

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<CommandCenter />} />
        <Route path="report" element={<EmergencyReport />} />
        <Route path="incidents" element={<ActiveIncidents />} />
        <Route path="incidents/:id" element={<IncidentDetails />} />
        {later.map(([path, title, endpoint]) => (
          <Route key={path} path={path} element={<Pending title={title} endpoint={endpoint} />} />
        ))}
      </Route>
    </Routes>
  )
}
