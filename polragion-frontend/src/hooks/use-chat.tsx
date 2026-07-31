import {createContext, type PropsWithChildren, useCallback, useContext, useEffect, useMemo, useState} from "react";
import type {ChatStatus} from "ai";
import {workItemsApi} from "@/api/client.ts";
import {useGitHubAuth} from "@/hooks/use-github-auth.tsx";
import type {PromptInputMessage} from "@/components/ai/prompt-input.tsx";
import type {WorkItemSearchHitResponse} from "@/api";

export type ChatMode = "ask" | "search"

export interface ChatEntry {
    id: string
    role: "user" | "assistant"
    content: string
}

interface ChatContextValue {
    mode: ChatMode
    setMode: (mode: ChatMode) => void
    entries: ChatEntry[]
    status: ChatStatus
    handleSubmit: (msg: PromptInputMessage) => Promise<void>
    resetSession: () => Promise<void>
}

function formatSearchHits(hits: WorkItemSearchHitResponse[]) {
    if (hits.length === 0) {
        return "No matching work items found."
    }

    return hits
        .map(hit => {
            const item = hit.workItem
            const score = Math.round(hit.score * 100)
            return `**${item.workitemId} — ${item.title}**\n\n${item.status} · ${item.projectId} · ${score}% match\n\n${item.text}`
        })
        .join("\n\n---\n\n")
}

const UseChat = createContext<ChatContextValue | null>(null);

export function ChatContextProvider({ children }: PropsWithChildren) {
    const { isAuthenticated } = useGitHubAuth()
    const [mode, setMode] = useState<ChatMode>("ask")
    const [entries, setEntries] = useState<ChatEntry[]>([])
    const [status, setStatus] = useState<ChatStatus>("ready")

    useEffect(() => {
        if (!isAuthenticated) {
            setEntries([])
            return
        }

        let cancelled = false

        void (async () => {
            try {
                const history = await workItemsApi.getChatHistory()
                if (cancelled) {
                    return
                }
                setEntries(
                    history.map((message, index) => ({
                        id: message.messageId ?? `history-${index}`,
                        role: message.role === "user" ? "user" : "assistant",
                        content: message.content,
                    })),
                )
            } catch {
                // No history available yet.
            }
        })()

        return () => {
            cancelled = true
        }
    }, [isAuthenticated])

    const handleSubmit = useCallback(
        async (message: PromptInputMessage) => {
            const prompt = message.text.trim()
            if (!prompt || !isAuthenticated || status !== "ready") {
                return
            }

            setEntries(current => [
                ...current,
                { id: `user-${Date.now()}`, role: "user", content: prompt },
            ])
            setStatus("submitted")

            try {
                const answer =
                    mode === "ask"
                        ? await workItemsApi.askWorkItem({ prompt })
                        : formatSearchHits(await workItemsApi.searchWorkItems({ prompt }))

                setEntries(current => [
                    ...current,
                    { id: `assistant-${Date.now()}`, role: "assistant", content: answer },
                ])
                setStatus("ready")
            } catch {
                setEntries(current => [
                    ...current,
                    {
                        id: `error-${Date.now()}`,
                        role: "assistant",
                        content: "Something went wrong while contacting the backend. Please try again.",
                    },
                ])
                setStatus("error")
                setTimeout(() => setStatus("ready"), 1500)
            }
        },
        [isAuthenticated, mode, status],
    )

    const resetSession = useCallback(async () => {
        setEntries([])
        setStatus("ready")
        try {
            await workItemsApi.resetUserSession()
        } catch (error) {
            console.error("Failed to reset session", error)
        }
    }, [])

    const value = useMemo<ChatContextValue>(
        () => ({ mode, entries, status, handleSubmit, resetSession, setMode }),
        [mode, entries, status, handleSubmit, resetSession, setMode],
    )

    return (
        <UseChat.Provider value={value}>{children}</UseChat.Provider>
    )
}

export function useChat(): ChatContextValue {
    const context = useContext(UseChat);
    if (!context) {
        throw new Error("useChat must be used within a ChatContextProvider");
    }
    return context;
}
