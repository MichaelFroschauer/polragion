import {Fragment, useEffect, useRef, useState} from "react"
import {Check, Copy, LogInIcon, Minus, Plus} from "lucide-react"
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
    "Excavating ancient work items...",
    "Asking Polragion nicely...",
    "Untangling some suspicious requirements...",
    "Searching for the work item everyone remembers but nobody can find...",
    "Searching across projects like I know what I'm doing...",
    "Turning work items into wisdom...",
    "Looking for the requirement behind the requirement...",
    "Finding three contradictory specifications...",
    "Determining which specification is the specification...",
    "Consulting the Polragion gods...",
    "Trying to remember where I put that answer...",
    "Asking the intern...",
    "Deleting the database...",
    "Ignoring several warning messages...",
    "Searching for the person who wrote this...",
    "Copying the question into Google...",
    "Asking another AI for help...",
    "Performing highly scientific clicking...",
    "Calculating an answer with unnecessary precision...",
    "Scheduling a meeting about the answer...",
    "Creating a PowerPoint about the problem...",
    "Interpreting the requirements creatively...",
    "Searching through ancient work items...",
    "Performing a controlled amount of panic...",
    "Turning requirements into floating-point numbers...",
    "Compressing years of engineering pain into a vector...",
    "Trying to save you from opening the document manually...",
    "Doing the reading so you don't have to...",
    "Translating Polragion-to-human...",
    "Running advanced bureaucracy retrieval...",
    "Trying not to hallucinate a work item...",
    "Putting the 'RAG' in PolRAGion...",
    "Opening 47 linked work items...",
    "Checking if the answer is hidden in a custom field...",
    "Crossing project boundaries without a visa...",
    "Trying to explain Polragion metadata to the vector database...",
    "Embedding knowledge into 1536 dimensions...",
    "Calculating cosine similarity between two questionable requirements...",
    "Verifying that the work items exist outside my imagination...",
    "Adding citations so nobody has to trust me...",
    "Converting chaos into markdown...",
    "Trying to fit 8 years of project history into one answer...",
    "Dusting off an old project context...",
    "Trying not to wake the legacy requirements...",
    "Waiting for answers from people who are currently on vacation...",
    "Finding the answer hidden in an attachment named image001.png...",
    "Searching smarter than Ctrl+F...",
]

function MessageFooterRight({
    message,
    usedCredits,
}: {
    message: string
    usedCredits: number | null
}) {
    const [copied, setCopied] = useState(false)

    const copyAnswer = async () => {
        await navigator.clipboard.writeText(message)
        setCopied(true)
        setTimeout(() => { setCopied(false)}, 2000)
    }

    if (!message) {
        return null
    }

    return (
        <div className="flex shrink-0 items-center gap-3 text-sm text-muted-foreground">
            {usedCredits !== null && (
                <span className="mr-2">
                    {usedCredits < 10
                        ? usedCredits.toFixed(1)
                        : usedCredits.toFixed(0)}{" "}
                    credits
                </span>
            )}

            <button
                type="button"
                onClick={copyAnswer}
                className="flex items-center gap-1 hover:text-foreground"
            >
                {copied ? (
                    <Check className="h-4 w-4" />
                ) : (
                    <Copy className="h-4 w-4" />
                )}
            </button>
        </div>
    )
}

function AskMessageResponse({response}: {response: WorkItemAskResponse}) {
    const [isOpen, setIsOpen] = useState(false)

    return (
        <>
            <MessageResponse>{linkifyWorkItemReferences(response.answer)}</MessageResponse>
            <Collapsible
                className="w-full mt-2 space-y-2"
                open={isOpen}
                onOpenChange={setIsOpen}
            >
                <div className={"flex items-center justify-between" +  (!isOpen ? " opacity-0 transition-opacity pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto" : "")}>
                    {response.workItems.length > 0 && (
                        <CollapsibleTrigger className="flex items-center gap-2 font-medium text-sm hover:underline">
                            {isOpen ? (
                                <Minus className="h-4 w-4" />
                            ) : (
                                <Plus className="h-4 w-4" />
                            )}
                            {isOpen ? "Hide used work items" : `Show ${response.workItems.length} used work item${response.workItems.length > 1 ? "s" : ""}`}
                        </CollapsibleTrigger>
                    )}
                    {response.workItems.length == 0 && (
                        <div className="flex items-center gap-2 font-medium text-sm hover:underline"></div>
                    )}
                    <MessageFooterRight message={response.answer} usedCredits={response.creditsSpent} />
                </div>
                <CollapsibleContent className="space-y-2">
                    {response.workItems.map((wi, index) =>
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
}

export function Chat() {
    const {isAuthenticated, isLoading: isAuthLoading, login} = useGitHubAuth()
    const bottomRef = useRef<HTMLDivElement | null>(null)
    const lastEntryRef = useRef<HTMLDivElement | null>(null)
    const {entries, status, mode, setMode, handleSubmit} = useChat()

    const [loadingQuote, setLoadingQuote] = useState(
        () => loadingQuotes[Math.floor(Math.random() * loadingQuotes.length)],
    )

    useEffect(() => {
        lastEntryRef.current?.scrollIntoView({behavior: "smooth", block: "start"})
    }, [entries, status])


    useEffect(() => {
        if (status === "ready") {
            return
        }

        const updateQuote = () => {
            setLoadingQuote(loadingQuotes[Math.floor(Math.random() * loadingQuotes.length)])
        }

        updateQuote() // Change immediately when loading starts
        const interval = setInterval(updateQuote, 4000) // Then change every 4 seconds

        return () => clearInterval(interval)
    }, [status])


    function getMessageResponse(contentType: ChatContentType, response: WorkItemSearchResponse | WorkItemAskResponse | string) {
        if (contentType === "ask") {
            const askResponse = response as WorkItemAskResponse;
            return <AskMessageResponse response={askResponse} />
        } else if (contentType === "search") {
            const searchResponse = response as WorkItemSearchResponse;
            return searchResponse.workItems.map((wi, index) =>
                <div className="divide-y" key={wi.workItem.workItemId}>
                    <Fragment>
                        {index > 0 && <Separator />}
                        <WorkItemChatEntry hit={wi} />
                    </Fragment>
                </div>
            )
        } else if (contentType === "string") {
            return <>
                <MessageResponse>{linkifyWorkItemReferences(response as string)}</MessageResponse>
                <div className="flex justify-end opacity-0 transition-opacity pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto">
                    <MessageFooterRight message={response as string} usedCredits={null} />
                </div>
            </>
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
                        entries.map((entry, index) => (
                            <div ref={index === entries.length - 1 ? lastEntryRef : null}>
                                <Message from={entry.role} key={entry.id}>
                                <MessageContent className={entry.role === "assistant" ? "w-full max-w-none" : undefined}>
                                    {entry.role === "assistant" ? (
                                        getMessageResponse(entry.contentType, entry.content)
                                    ) : (
                                        <p className="whitespace-pre-wrap">{entry.content as string}</p>
                                    )}
                                </MessageContent>
                                </Message>
                            </div>
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
