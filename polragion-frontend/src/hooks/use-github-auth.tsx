import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"
import type { PropsWithChildren } from "react"
import { apiBasePath, gitHubAuthApi } from "@/api/client"

export interface GitHubUser {
  login: string
  name?: string | null
  email?: string | null
  avatarUrl?: string | null
}

interface GitHubAuthContextValue {
  user: GitHubUser | null
  isAuthenticated: boolean
  isLoading: boolean
  login: () => void
  logout: () => Promise<void>
  refresh: () => Promise<void>
}

const GitHubAuthContext = createContext<GitHubAuthContextValue | null>(null)

function normalizeUser(raw: unknown): GitHubUser | null {
  if (!raw || typeof raw !== "object") {
    return null
  }
  const data = raw as Record<string, unknown>
  const login = data.login ?? data.username ?? data.user_name
  if (typeof login !== "string" || login.length === 0) {
    return null
  }
  return {
    login,
    name: typeof data.name === "string" ? data.name : null,
    email: typeof data.email === "string" ? data.email : null,
    avatarUrl:
      typeof data.avatar_url === "string"
        ? data.avatar_url
        : typeof data.avatarUrl === "string"
          ? data.avatarUrl
          : null,
  }
}

export function GitHubAuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<GitHubUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refresh = useCallback(async () => {
    setIsLoading(true)
    try {
      setUser(normalizeUser(await gitHubAuthApi.me()))
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

  const value = useMemo<GitHubAuthContextValue>(
    () => ({ user, isAuthenticated: user !== null, isLoading, login, logout, refresh }),
    [user, isLoading, login, logout, refresh],
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
