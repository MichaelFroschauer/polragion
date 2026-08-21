import {createContext, type PropsWithChildren, useCallback, useContext, useEffect, useMemo, useState} from "react";
import type {ChatStatus} from "ai";
import {workItemsApi} from "@/api/client.ts";
import {useGitHubAuth} from "@/hooks/use-github-auth.tsx";
import type {PromptInputMessage} from "@/components/ai/prompt-input.tsx";
import {
    AnswerDetail,
    AnswerDetailFromJSON,
    type WorkItemAskResponse,
    type WorkItemSearchResponse
} from "@/api";
import {useSettings} from "@/hooks/use-settings.tsx";

export type ChatMode = "ask" | "search"

export type ChatContentType = ChatMode | "string"

export interface ChatEntry {
    id: string
    role: "user" | "assistant"
    mode: ChatMode
    contentType: ChatContentType
    content: WorkItemSearchResponse | WorkItemAskResponse | string
}

interface ChatContextValue {
    mode: ChatMode
    setMode: (mode: ChatMode) => void
    entries: ChatEntry[]
    status: ChatStatus
    handleSubmit: (msg: PromptInputMessage) => Promise<void>
    resetSession: () => Promise<void>
}

const ChatContext = createContext<ChatContextValue | null>(null);

export function ChatContextProvider({ children }: PropsWithChildren) {
    const { isAuthenticated } = useGitHubAuth()
    const { settings } = useSettings()

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
                        mode: "ask",
                        contentType: "string",
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
            const msg_mode = mode
            if (!prompt || (!isAuthenticated && msg_mode === "ask") || status !== "ready") {
                return
            }

            setEntries(current => [
                ...current,
                { id: `user-${Date.now()}`, role: "user", mode: msg_mode, contentType: "string", content: prompt },
            ])
            setStatus("submitted")

            try {
                const answer =
                    msg_mode === "ask"
                        ? await workItemsApi.askWorkItem({
                            prompt,
                            projectId: null,
                            limitWorkItemSearch: settings.workItemSearch.maxResults,
                            limitAiModelWorkItems: settings.aiSearch.maxResultsForAi,
                            scoreThreshold: settings.workItemSearch.minScore,
                            doReranking: settings.workItemSearch.doReranking,
                            userDefinedSystemPrompt: settings.customUserSystemPrompt,
                            answerDetail: AnswerDetailFromJSON(localStorage.getItem("answerDetailSelection")) ?? AnswerDetail.Auto,
                        })
                        : await workItemsApi.searchWorkItems({
                            prompt,
                            projectId: null,
                            limit: settings.workItemSearch.maxResults,
                            scoreThreshold: settings.workItemSearch.minScore,
                            doReranking: settings.workItemSearch.doReranking,
                        })
                        // : formatSearchHits(await workItemsApi.searchWorkItems({ prompt }))

                setEntries(current => [
                    ...current,
                    { id: `assistant-${Date.now()}`, role: "assistant", mode: msg_mode, contentType: msg_mode, content: answer },
                ])
                setStatus("ready")
            } catch {
                setEntries(current => [
                    ...current,
                    {
                        id: `error-${Date.now()}`,
                        role: "assistant",
                        mode: msg_mode,
                        contentType: "string",
                        content: "Something went wrong while contacting the backend. Please try again.",
                    },
                ])
                setStatus("error")
                setTimeout(() => setStatus("ready"), 1500)
            }
        },
        [isAuthenticated, mode, status, settings],
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
        <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
    )
}

export function useChat(): ChatContextValue {
    const context = useContext(ChatContext);
    if (!context) {
        throw new Error("useChat must be used within a ChatContextProvider");
    }
    return context;
}
