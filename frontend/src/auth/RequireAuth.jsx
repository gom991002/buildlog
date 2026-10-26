import { Navigate, Outlet } from 'react-router'
import { useAuth } from './context.js'

// Screens behind this need a login; without one, go to the login screen.
// The server checks every request on its own as well.
export default function RequireAuth() {
  const { user, isLoading } = useAuth()

  if (isLoading) return <p className="muted">불러오는 중입니다.</p>
  if (!user) return <Navigate to="/login" replace />
  return <Outlet />
}
