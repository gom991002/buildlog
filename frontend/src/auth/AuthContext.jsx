import { useEffect, useState } from 'react'
import { fetchMe } from '../api/auth.js'
import { AuthContext } from './context.js'

// The login itself lives in an httpOnly cookie the page cannot read;
// this only remembers who /api/auth/me says is logged in.
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchMe().then((result) => {
      setUser(result.ok ? result.data : null)
      setIsLoading(false)
    })
  }, [])

  return <AuthContext.Provider value={{ user, setUser, isLoading }}>{children}</AuthContext.Provider>
}
