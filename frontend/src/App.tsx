import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './contexts/AuthContext'
import { useAuth } from './contexts/auth-context-value'
import { ThemeProvider } from './contexts/ThemeContext'
import { Layout } from './components/Layout'
import { Login } from './pages/Login'
const Dashboard = lazy(() => import('./pages/Dashboard').then((m) => ({ default: m.Dashboard })))
const Devices = lazy(() => import('./pages/Devices').then((m) => ({ default: m.Devices })))
const DeviceDetail = lazy(() => import('./pages/DeviceDetail').then((m) => ({ default: m.DeviceDetail })))
const InterfaceDetail = lazy(() => import('./pages/InterfaceDetail').then((m) => ({ default: m.InterfaceDetail })))
const Traffic = lazy(() => import('./pages/Traffic').then((m) => ({ default: m.Traffic })))
const Alerts = lazy(() => import('./pages/Alerts').then((m) => ({ default: m.Alerts })))
const Reports = lazy(() => import('./pages/Reports').then((m) => ({ default: m.Reports })))
const Users = lazy(() => import('./pages/Users').then((m) => ({ default: m.Users })))
const Analytics = lazy(() => import('./pages/Analytics').then((m) => ({ default: m.Analytics })))
const Topology = lazy(() => import('./pages/Topology').then((m) => ({ default: m.Topology })))
const Settings = lazy(() => import('./pages/Settings').then((m) => ({ default: m.Settings })))
const Profile = lazy(() => import('./pages/Profile').then((m) => ({ default: m.Profile })))
const Incidents = lazy(() => import('./pages/Incidents').then((m) => ({ default: m.Incidents })))
const IncidentDetail = lazy(() => import('./pages/IncidentDetail').then((m) => ({ default: m.IncidentDetail })))
const Maintenance = lazy(() => import('./pages/Maintenance').then((m) => ({ default: m.Maintenance })))
const Wallboard = lazy(() => import('./pages/Wallboard').then((m) => ({ default: m.Wallboard })))

const queryClient = new QueryClient()

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Suspense fallback={<div className="min-h-screen grid place-items-center" role="status">Loading workspace…</div>}>
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="devices" element={<Devices />} />
        <Route path="devices/:id" element={<DeviceDetail />} />
        <Route path="interfaces/:id" element={<InterfaceDetail />} />
        <Route path="traffic" element={<Traffic />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="incidents" element={<Incidents />} />
        <Route path="incidents/:id" element={<IncidentDetail />} />
        <Route path="maintenance" element={<Maintenance />} />
        <Route path="reports" element={<Reports />} />
        <Route path="users" element={<Users />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="topology" element={<Topology />} />
        <Route path="settings" element={<Settings />} />
        <Route path="profile" element={<Profile />} />
      </Route>
      <Route path="/wallboard" element={<PrivateRoute><Wallboard /></PrivateRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    </Suspense>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
