import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { useAuth } from '@/auth/AuthContext'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import Onboarding from '@/pages/Onboarding'
import OAuthCallback from '@/pages/OAuthCallback'
import CustomerHome from '@/pages/CustomerHome'
import Properties from '@/pages/Properties'
import PropertyDetail from '@/pages/PropertyDetail'
import Jobs from '@/pages/Jobs'
import JobCreate from '@/pages/JobCreate'
import JobDetail from '@/pages/JobDetail'
import Account from '@/pages/Account'
import Security from '@/pages/Security'
import HealthRecords from '@/pages/HealthRecords'
import TechnicianJobs from '@/pages/TechnicianJobs'
import TechnicianApply from '@/pages/TechnicianApply'
import AdminDashboard from '@/pages/AdminDashboard'
import AdminDispatch from '@/pages/AdminDispatch'
import AdminTechnicians from '@/pages/AdminTechnicians'

function RoleHome() {
  const { user } = useAuth()
  if (['admin', 'super_admin', 'dispatcher', 'support'].includes(user?.role || '')) {
    return <Navigate to="/admin" replace />
  }
  if (user?.role === 'technician') return <Navigate to="/tech" replace />
  return <CustomerHome />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/auth/callback/:provider" element={<OAuthCallback />} />
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <Onboarding />
          </ProtectedRoute>
        }
      />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<RoleHome />} />
        <Route path="/properties" element={<Properties />} />
        <Route path="/properties/:id" element={<PropertyDetail />} />
        <Route path="/jobs" element={<Jobs />} />
        <Route path="/jobs/new" element={<JobCreate />} />
        <Route path="/jobs/:id" element={<JobDetail />} />
        <Route path="/health" element={<HealthRecords />} />
        <Route path="/account" element={<Account />} />
        <Route path="/security" element={<Security />} />
        <Route path="/tech-apply" element={<TechnicianApply />} />
        <Route path="/tech" element={<ProtectedRoute roles={['technician']}><TechnicianJobs /></ProtectedRoute>} />
        <Route
          path="/admin"
          element={
            <ProtectedRoute roles={['admin', 'super_admin', 'dispatcher', 'support']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/dispatch"
          element={
            <ProtectedRoute roles={['admin', 'super_admin', 'dispatcher']}>
              <AdminDispatch />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/technicians"
          element={
            <ProtectedRoute roles={['admin', 'super_admin', 'support']}>
              <AdminTechnicians />
            </ProtectedRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
