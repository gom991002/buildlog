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

  return (
    <div className="layout">
      <header className="topbar">
        <NavLink to={user ? '/' : '/login'} className="brand">
          BuildLog
        </NavLink>
        <nav className="menu">
          {user ? (
            <>
              <NavLink to="/" end>
                홈
              </NavLink>
              <NavLink to="/account">계정 설정</NavLink>
              <button type="button" className="link-button" onClick={handleLogout}>
                로그아웃
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login">로그인</NavLink>
              <NavLink to="/signup">회원가입</NavLink>
            </>
          )}
        </nav>
      </header>
      {logoutError && <p className="alert alert-error">{logoutError}</p>}
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
