import {useCallback, useEffect, useMemo, useState, type PropsWithChildren} from "react"
import {polarionMetadataApi} from "@/api/client"
import type {PolarionMetadataResponse} from "@/api"
import {SearchFiltersContext} from "@/hooks/use-search-filters"
import {buildRequestFilters} from "@/lib/search-filters"

function useFilterState() {
    const [searchScopes, setSearchScopes] = useState<PolarionMetadataResponse | null>(null)
    const [filterStatus, setFilterStatus] = useState<"loading" | "error" | "ready">("loading")
    const [loadAttempt, setLoadAttempt] = useState(0)
    // Exceptions to the default keep newly loaded options selected automatically.
    const [excluded, setExcluded] = useState<Set<string>>(new Set())

    useEffect(() => {
        let cancelled = false
        void polarionMetadataApi.getPolarionSearchScopes().then(scopes => {
            if (!cancelled) {
                setSearchScopes(scopes)
                setFilterStatus("ready")
            }
        }).catch(error => {
            if (!cancelled) setFilterStatus("error")
            console.error("Error fetching search scopes:", error)
        })
        return () => { cancelled = true }
    }, [loadAttempt])

    const retry = useCallback(() => {
        setFilterStatus("loading")
        setLoadAttempt(attempt => attempt + 1)
    }, [])
    const reset = useCallback(() => setExcluded(new Set()), [])
    const setOptionChecked = useCallback((id: string, checked: boolean) => {
        setExcluded(previous => {
            const next = new Set(previous)
            if (checked) next.delete(id)
            else next.add(id)
            return next
        })
    }, [])
    const requestFilters = useMemo(() => buildRequestFilters(searchScopes, excluded), [searchScopes, excluded])
    return {searchScopes, filterStatus, retry, reset, excluded, setOptionChecked, requestFilters}
}

export function SearchFiltersProvider({children}: PropsWithChildren) {
    const value = useFilterState()
    return <SearchFiltersContext.Provider value={value}>{children}</SearchFiltersContext.Provider>
}

