import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router'
import { logout } from '../api/auth.js'
import { errorMessage } from '../api/client.js'
import { useAuth } from '../auth/context.js'

export default function Layout() {
  const { user, setUser } = useAuth()
  const navigate = useNavigate()
  const [logoutError, setLogoutError] = useState('')

  async function handleLogout() {
    const result = await logout()
    if (!result.ok) {
      setLogoutError(errorMessage(result))
      return
    }
    setLogoutError('')
    setUser(null)
    navigate('/login', { replace: true })
  }

  if (!user) {
    return (
      <div className="layout">
        <header className="topbar">
          <NavLink to="/login" className="brand">
            BuildLog
          </NavLink>
          <nav className="menu">
            <NavLink to="/login">로그인</NavLink>
            <NavLink to="/signup">회원가입</NavLink>
          </nav>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    )
  }

  // Logged-in screens use the sidebar from the Figma dashboard (node 2:12).
  // Menus for records that do not exist yet are added in their own Phase (plan.md Phase 12-9).
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink to="/" className="sidebar-brand">
          <span className="sidebar-brand-mark">b</span>
          BuildLog
        </NavLink>

        <p className="sidebar-label">MY WORKSPACE</p>
        <nav className="sidebar-menu">
          <NavLink to="/" end>
            <span className="sidebar-icon" aria-hidden="true">
              ▦
            </span>
            대시보드
          </NavLink>
          <NavLink to="/materials">
            <span className="sidebar-icon" aria-hidden="true">
              ▧
            </span>
            학습 자료함
          </NavLink>
        </nav>

        <div className="sidebar-account">
          <span className="sidebar-avatar" aria-hidden="true">
            {Array.from(user.nickname)[0]}
          </span>
          <div className="sidebar-account-label">
            <strong>{user.nickname}</strong>
            <NavLink to="/account">계정 설정 ›</NavLink>
          </div>
        </div>
        <button type="button" className="link-button sidebar-logout" onClick={handleLogout}>
          로그아웃
        </button>
      </aside>

      <main className="app-main">
        {logoutError && <p className="alert alert-error">{logoutError}</p>}
        <Outlet />
      </main>
    </div>
  )
}
