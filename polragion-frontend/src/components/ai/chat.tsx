import { useCallback, useEffect, useRef, useState } from "react"
import type { ChatStatus } from "ai"
import { LogInIcon } from "lucide-react"
import { workItemsApi } from "@/api/client"
import type { WorkItemSearchHitResponse } from "@/api"
import {
  Message,
  MessageContent,
  MessageResponse,
} from "@/components/ai/message"
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools,
} from "@/components/ai/prompt-input"
import type { PromptInputMessage } from "@/components/ai/prompt-input"
import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useGitHubAuth } from "@/hooks/use-github-auth"

type ChatMode = "ask" | "search"

interface ChatEntry {
  id: string
  role: "user" | "assistant"
  content: string
}

const placeholders: Record<ChatMode, string> = {
  ask: "Ask anything about your work items…",
  search: "Search work items by keyword or description…",
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

export function Chat() {
  const { isAuthenticated, isLoading: isAuthLoading, login } = useGitHubAuth()
  const [mode, setMode] = useState<ChatMode>("ask")
  const [entries, setEntries] = useState<ChatEntry[]>([])
  const [status, setStatus] = useState<ChatStatus>("ready")
  const bottomRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }, [entries, status])

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

  return (
      <div className="flex min-h-0 flex-1 flex-col">
        <div className="min-h-0 flex-1 overflow-y-auto">
          <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-6">
            {entries.length === 0 ? (
              <div className="flex flex-col items-center gap-2 py-24 text-center">
                <p className="text-lg font-medium">How can I help you?</p>
                <p className="max-w-sm text-sm text-muted-foreground">
                  {isAuthenticated
                    ? "Ask a question about your Polarion work items or search them directly."
                    : "Sign in with GitHub to start asking questions about your work items."}
                </p>
              </div>
            ) : (
              entries.map(entry => (
                <Message from={entry.role} key={entry.id}>
                  <MessageContent>
                    {entry.role === "assistant" ? (
                      <MessageResponse>{entry.content}</MessageResponse>
                    ) : (
                      <p className="whitespace-pre-wrap">{entry.content}</p>
                    )}
                  </MessageContent>
                </Message>
              ))
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        <div className="shrink-0 px-4 pb-2">
          <div className="mx-auto w-full max-w-3xl">
            {(!isAuthenticated && mode === "ask") && !isAuthLoading && (
              <div className="mb-2 flex items-center justify-between gap-3 rounded-lg border border-dashed px-3 py-2 text-sm text-muted-foreground">
                <span>Sign in with GitHub to enable the chat.</span>
                <Button onClick={login} size="sm">
                  <LogInIcon className="size-4" />
                  Sign in
                </Button>
              </div>
            )}
            <Tabs
              onValueChange={value => setMode(value as ChatMode)}
              value={mode}
            >
              <PromptInput onSubmit={handleSubmit}>
                <PromptInputBody>
                  <PromptInputTextarea
                    disabled={(!isAuthenticated && mode === "ask")}
                    placeholder={placeholders[mode]}
                  />
                </PromptInputBody>
                <PromptInputFooter>
                  <PromptInputTools>
                    <TabsList>
                      <TabsTrigger value="ask">Ask</TabsTrigger>
                      <TabsTrigger value="search">Search</TabsTrigger>
                    </TabsList>
                  </PromptInputTools>
                  <PromptInputSubmit
                    disabled={(!isAuthenticated && mode === "ask") || status !== "ready"}
                    status={status}
                  />
                </PromptInputFooter>
              </PromptInput>
            </Tabs>
          </div>
        </div>
      </div>
  )
}
