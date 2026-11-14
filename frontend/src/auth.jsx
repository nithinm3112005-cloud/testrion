import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api, getToken, setToken, setUnauthorizedHandler } from './api.js'

const Ctx = createContext(null)
export const useAuth = () => useContext(Ctx)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(!!getToken())

  const clear = useCallback(() => { setToken(null); setUser(null) }, [])

  useEffect(() => {
    setUnauthorizedHandler(clear)
    if (!getToken()) return
    api.me().then(setUser).catch(clear).finally(() => setLoading(false))
  }, [clear])

  const accept = (r) => { setToken(r.token); setUser(r.user) }
  const value = {
    user,
    loading,
    login: async (email, password) => accept(await api.login({ email, password })),
    signup: async (name, email, password) => accept(await api.signup({ name, email, password })),
    logout: async () => { try { await api.logout() } catch {} clear() },
  }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
