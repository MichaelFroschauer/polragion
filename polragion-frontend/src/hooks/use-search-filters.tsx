import {createContext, useContext} from "react"
import type {PolarionMetadataResponse, WorkItemFilters} from "@/api"

interface SearchFiltersState {
    searchScopes: PolarionMetadataResponse | null
    filterStatus: "loading" | "error" | "ready"
    retry: () => void
    reset: () => void
    excluded: ReadonlySet<string>
    setOptionChecked: (id: string, checked: boolean) => void
    requestFilters: WorkItemFilters
}

export const SearchFiltersContext = createContext<SearchFiltersState | null>(null)

export function useSearchFilters() {
    const context = useContext(SearchFiltersContext)
    if (!context) throw new Error("useSearchFilters must be used within SearchFiltersProvider")
    return context
}
