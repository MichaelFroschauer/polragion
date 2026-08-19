import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"
import type { PropsWithChildren } from "react"
import { apiBasePath, gitHubAuthApi } from "@/api/client"
import type {User} from "@/api";


interface GitHubAuthContextValue {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: () => void
  logout: () => Promise<void>
  switchAccount: () => void
  refresh: () => Promise<void>
}

const GitHubAuthContext = createContext<GitHubAuthContextValue | null>(null)

export function GitHubAuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refresh = useCallback(async () => {
    setIsLoading(true)
    try {
      setUser(await gitHubAuthApi.me())
    } catch {
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const login = useCallback(() => {
    // Full page redirect, the backend handles the OAuth dance and redirects back.
    window.location.href = `${apiBasePath}/auth/github/login`
    console.log(`${apiBasePath}/auth/github/login`)
  }, [])

  const logout = useCallback(async () => {
    try {
      await gitHubAuthApi.logout()
    } finally {
      setUser(null)
    }
  }, [])

  const switchAccount = useCallback(() => {
    // Full page redirect, the backend handles the OAuth dance and redirects back.
    window.location.href = `${apiBasePath}/auth/github/switch-account`
    console.log(`${apiBasePath}/auth/github/switch-account`)
  }, [])

  const value = useMemo<GitHubAuthContextValue>(
    () => ({ user, isAuthenticated: user !== null, isLoading, login, logout, switchAccount, refresh }),
    [user, isLoading, login, logout, switchAccount, refresh],
  )

  return <GitHubAuthContext.Provider value={value}>{children}</GitHubAuthContext.Provider>
}

export function useGitHubAuth(): GitHubAuthContextValue {
  const context = useContext(GitHubAuthContext)
  if (!context) {
    throw new Error("useGitHubAuth must be used within a GitHubAuthProvider")
  }
  return context
}
