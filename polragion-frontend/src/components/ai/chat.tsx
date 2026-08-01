import {Fragment, useEffect, useRef, useState} from "react"
import {LogInIcon, Minus, Plus} from "lucide-react"
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
import {Button} from "@/components/ui/button"
import {Tabs, TabsList, TabsTrigger} from "@/components/ui/tabs"
import {useGitHubAuth} from "@/hooks/use-github-auth"
import {type ChatContentType, type ChatMode, useChat} from "@/hooks/use-chat.tsx";
import {Marker, MarkerContent} from "@/components/ui/marker.tsx"
import type {WorkItemAskResponse, WorkItemSearchResponse} from "@/api";
import {WorkItemChatEntry} from "@/components/ai/work-item-chat-entry.tsx";
import {Collapsible, CollapsibleContent, CollapsibleTrigger} from "@/components/ui/collapsible.tsx";
import {Separator} from "@/components/ui/separator.tsx";
import {linkifyWorkItemReferences} from "@/lib/work-item-references.ts";


const placeholders: Record<ChatMode, string> = {
    ask: "Ask anything about your work items…",
    search: "Search work items by keyword or description…",
}

const loadingQuotes = [
    "Thinking about what I should cook tonight...",
    "Doing my paperwork...",
    "Consulting the office oracle...",
    "Pretending this is a very difficult question...",
    "Looking busy...",
    "Searching under the couch cushions...",
    "Asking the rubber duck...",
    "Converting coffee into answers...",
    "Rearranging some bits...",
    "Reading the fine print...",
    "Checking my notes...",
    "Running around in tiny circles...",
    "Waiting for inspiration to compile...",
    "Negotiating with the database...",
    "Counting backwards from infinity...",
    "Opening another browser tab...",
    "Blaming the network...",
    "Summoning the relevant information...",
    "Connecting the dots...",
    "Untangling some work items...",
    "Trying not to overthink this...",
    "Making it look professional...",
    "Consulting Stack Overflow... probably...",
    "Sharpening my pencils...",
    "Filling out form 27-B...",
    "Checking if anyone is watching...",
    "Putting the pieces together...",
    "Doing some very serious computing...",
    "Turning it off and on again...",
    "Preparing a suspiciously confident answer...",
]

export function Chat() {
    const {isAuthenticated, isLoading: isAuthLoading, login} = useGitHubAuth()
    const bottomRef = useRef<HTMLDivElement | null>(null)
    const {entries, status, mode, setMode, handleSubmit} = useChat()
    const [isOpen, setIsOpen] = useState(false)

    const [loadingQuote, setLoadingQuote] = useState(
        () => loadingQuotes[Math.floor(Math.random() * loadingQuotes.length)],
    )

    useEffect(() => {
        bottomRef.current?.scrollIntoView({behavior: "smooth", block: "end"})
    }, [entries, status])

    useEffect(() => {
        if (status === "submitted") {
            setLoadingQuote(loadingQuotes[Math.floor(Math.random() * loadingQuotes.length)])
        }
    }, [status])

    function getMessageResponse(contentType: ChatContentType, response: WorkItemSearchResponse | WorkItemAskResponse | string) {
        if (contentType === "ask") {
            const ask_response = response as WorkItemAskResponse;

            return (
                <>
                    <MessageResponse>{linkifyWorkItemReferences(ask_response.answer)}</MessageResponse>
                    <Collapsible
                        className="w-full mt-2 space-y-2"
                        open={isOpen}
                        onOpenChange={setIsOpen}
                    >
                        <CollapsibleTrigger className="flex items-center gap-2 font-medium text-sm hover:underline">
                            {isOpen ? (
                                <Minus className="h-4 w-4" />
                            ) : (
                                <Plus className="h-4 w-4" />
                            )}
                            {isOpen ? "Hide used work items" : "Show used work items"}
                        </CollapsibleTrigger>
                        <CollapsibleContent className="space-y-2">
                            {ask_response.workItems.map((wi, index) =>
                                    <div className="divide-y" key={wi.workItem.workItemId}>
                                        <Fragment>
                                            {index > 0 && <Separator />}
                                            <WorkItemChatEntry hit={wi} />
                                        </Fragment>
                                    </div>
                                )
                            }
                        </CollapsibleContent>
                    </Collapsible>
                </>
            )
        } else if (contentType === "search") {
            const search_response = response as WorkItemSearchResponse;
            return search_response.workItems.map((wi, index) =>
                <div className="divide-y">
                    <Fragment key={wi.workItem.workItemId}>
                        {index > 0 && <Separator />}
                        <WorkItemChatEntry hit={wi} />
                    </Fragment>
                </div>
            )
        } else if (contentType === "string") {
            return <MessageResponse>{linkifyWorkItemReferences(response as string)}</MessageResponse>
        }

        return <MessageResponse>Error: Unknown response content type</MessageResponse>
    }

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
                                        // <MessageResponse>{entry.content}</MessageResponse>
                                        getMessageResponse(entry.contentType, entry.content)
                                    ) : (
                                        <p className="whitespace-pre-wrap">{entry.content as string}</p>
                                    )}
                                </MessageContent>
                            </Message>
                        ))
                    )}
                    <div ref={bottomRef}/>
                </div>
            </div>

            <div className="shrink-0 px-4 pb-2">
                <div className="mx-auto w-full max-w-3xl">
                    {status !== "ready" && (
                        <Marker className="mb-2 ms-2" role="status">
                            <MarkerContent className="shimmer">{loadingQuote}</MarkerContent>
                        </Marker>
                    )}
                    {(!isAuthenticated && mode === "ask") && !isAuthLoading && (
                        <div
                            className="mb-2 flex items-center justify-between gap-3 rounded-lg border border-dashed px-3 py-2 text-sm text-muted-foreground">
                            <span>Sign in with GitHub to enable the chat.</span>
                            <Button onClick={login} size="sm">
                                <LogInIcon className="size-4"/>
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
