import {createContext, type PropsWithChildren, useCallback, useContext, useEffect, useMemo, useState} from "react";


interface WorkItemSearchSettings {
    maxResults: number
    minScore: number
}

interface AiSearchSettings {
    maxResultsForAi: number
}

export interface AppSettings {
    version: 1
    workItemSearch: WorkItemSearchSettings
    aiSearch: AiSearchSettings
    customUserSystemPrompt?: string
}

export const DEFAULT_SETTINGS: AppSettings = {
    version: 1,

    workItemSearch: {
        maxResults: 100,
        minScore: 0.3,
    },

    aiSearch: {
        maxResultsForAi: 50,
    },

    customUserSystemPrompt: undefined,
}

/**
 * Boundaries of every editable setting. They are the single source of truth for
 * the input constraints (min/max/step) *and* for the validation below, so a new
 * setting only has to be described once.
 */
export const SETTINGS_LIMITS = {
    workItemSearch: {
        maxResults: {min: 1, max: 500, step: 1, integer: true},
        minScore: {min: 0, max: 1, step: 0.01, integer: false},
    },
    aiSearch: {
        maxResultsForAi: {min: 1, max: 200, step: 1, integer: true},
    },
    customUserSystemPrompt: {maxLength: 500},
} as const

/** Dot-paths of all validatable settings. */
export type SettingsFieldPath =
    | "workItemSearch.maxResults"
    | "workItemSearch.minScore"
    | "aiSearch.maxResultsForAi"
    | "customUserSystemPrompt"

export type SettingsErrors = Partial<Record<SettingsFieldPath, string>>

interface NumberLimit {
    min: number
    max: number
    integer: boolean
}

function validateNumber(value: number, {min, max, integer}: NumberLimit): string | undefined {
    if (!Number.isFinite(value)) {
        return "Please enter a number."
    }
    if (integer && !Number.isInteger(value)) {
        return "Please enter a whole number."
    }
    if (value < min || value > max) {
        return `Must be between ${min} and ${max}.`
    }
    return undefined
}

/**
 * Validates a (draft) settings object. Add a new rule here whenever a new
 * setting is introduced - the dialog renders whatever it finds automatically.
 */
export function validateSettings(settings: AppSettings): SettingsErrors {
    const errors: SettingsErrors = {}

    const maxResultsError = validateNumber(
        settings.workItemSearch.maxResults,
        SETTINGS_LIMITS.workItemSearch.maxResults,
    )
    if (maxResultsError) {
        errors["workItemSearch.maxResults"] = maxResultsError
    }

    const minScoreError = validateNumber(
        settings.workItemSearch.minScore,
        SETTINGS_LIMITS.workItemSearch.minScore,
    )
    if (minScoreError) {
        errors["workItemSearch.minScore"] = minScoreError
    }

    const maxResultsForAiError = validateNumber(
        settings.aiSearch.maxResultsForAi,
        SETTINGS_LIMITS.aiSearch.maxResultsForAi,
    )
    if (maxResultsForAiError) {
        errors["aiSearch.maxResultsForAi"] = maxResultsForAiError
    } else if (
        !maxResultsError &&
        settings.aiSearch.maxResultsForAi > settings.workItemSearch.maxResults
    ) {
        errors["aiSearch.maxResultsForAi"] =
            `Cannot exceed the work item result limit (${settings.workItemSearch.maxResults}).`
    }

    if ((settings.customUserSystemPrompt?.length ?? 0) > SETTINGS_LIMITS.customUserSystemPrompt.maxLength) {
        errors.customUserSystemPrompt =
            `Must not be longer than ${SETTINGS_LIMITS.customUserSystemPrompt.maxLength} characters.`
    }

    return errors
}

const SETTINGS_STORAGE_KEY = "polragion.settings"

function loadSettings(): AppSettings {
    if (typeof window === "undefined") {
        return DEFAULT_SETTINGS
    }

    try {
        const raw = localStorage.getItem(SETTINGS_STORAGE_KEY)
        if (!raw) {
            return DEFAULT_SETTINGS
        }

        const stored = JSON.parse(raw) as Partial<AppSettings>
        return {
            ...DEFAULT_SETTINGS,
            ...stored,

            workItemSearch: {
                ...DEFAULT_SETTINGS.workItemSearch,
                ...stored.workItemSearch,
            },

            aiSearch: {
                ...DEFAULT_SETTINGS.aiSearch,
                ...stored.aiSearch,
            },

            version: 1,
        }
    } catch {
        return DEFAULT_SETTINGS
    }
}

interface SettingsContextValue {
    settings: AppSettings

    updateWorkItemSearch: (settings: Partial<WorkItemSearchSettings>) => void
    updateAiSearch: (settings: Partial<AiSearchSettings>) => void
    setCustomUserSystemPrompt: (prompt: string | undefined) => void
    updateSettings: (updater: (current: AppSettings) => AppSettings) => void
    replaceSettings: (settings: AppSettings) => void
    resetSettings: () => void
}

const SettingsContext = createContext<SettingsContextValue | null>(null)

export function SettingsProvider({ children }: PropsWithChildren) {

    const [settings, setSettings] = useState<AppSettings>(loadSettings)

    useEffect(() => {
        try {
            localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings))
        } catch {
            // Storage may be unavailable or blocked.
        }
    }, [settings])

    const updateWorkItemSearch = useCallback(
        (update: Partial<WorkItemSearchSettings>) => {
            setSettings((current) => ({
                ...current,

                workItemSearch: {
                    ...current.workItemSearch,
                    ...update,
                },
            }))
        },
        [],
    )

    const setCustomUserSystemPrompt = useCallback(
        (prompt: string | undefined) => {
            setSettings((current) => ({
                ...current,
                customUserSystemPrompt: prompt,
            }))
        },
        [],
    )

    const updateAiSearch = useCallback(
        (update: Partial<AiSearchSettings>) => {
            setSettings((current) => ({
                ...current,

                aiSearch: {
                    ...current.aiSearch,
                    ...update,
                },
            }))
        },
        [],
    )

    const updateSettings = useCallback(
        (updater: (current: AppSettings) => AppSettings) => {
            setSettings(updater)
        },
        [],
    )

    const replaceSettings = useCallback(
        (newSettings: AppSettings) => {
            setSettings({
                ...newSettings,
                workItemSearch: {
                    ...newSettings.workItemSearch,
                },
                aiSearch: {
                    ...newSettings.aiSearch,
                },
            })
        },
        [],
    )

    const resetSettings = useCallback(() => {
        setSettings(DEFAULT_SETTINGS)
    }, [])

    const value = useMemo<SettingsContextValue>(
        () => ({settings, updateWorkItemSearch, updateAiSearch, setCustomUserSystemPrompt, updateSettings, replaceSettings, resetSettings}),
        [settings, updateWorkItemSearch, updateAiSearch, setCustomUserSystemPrompt, updateSettings, replaceSettings, resetSettings]
    )

    return (
        <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
    )
}

export function useSettings(): SettingsContextValue {
    const context = useContext(SettingsContext)
    if (!context) {
        throw new Error("useSettings must be used within a SettingsProvider")
    }
    return context
}
