import {useEffect, useState} from "react"
import {BookOpenIcon, CheckIcon, CopyIcon, ExternalLinkIcon, KeyRoundIcon} from "lucide-react"
import {apiBasePath, mcpTokensApi} from "@/api/client"
import {DocumentationDialog} from "@/components/documentation-dialog"
import {InputGroup, InputGroupAddon, InputGroupButton, InputGroupInput} from "@/components/ui/input-group"
import {Tabs, TabsContent, TabsList, TabsTrigger} from "@/components/ui/tabs"
import {Button} from "@/components/ui/button"
import {Input} from "@/components/ui/input"
import {Label} from "@/components/ui/label"
import {useGitHubAuth} from "@/hooks/use-github-auth"
import {getApiErrorMessage} from "@/lib/api-error"
import type {IssuedToken, TokenOverview} from "@/api";

function date(value: string) {
    return new Date(value).toLocaleString()
}

export function McpServerSettings() {
    const {user} = useGitHubAuth()
    return user ? <PersonalMcpTokens key={user.id}/> :
        <p className="text-muted-foreground text-sm">Sign in to manage your MCP tokens.</p>
}

function PersonalMcpTokens() {
    const [overview, setOverview] = useState<TokenOverview | null>(null)
    const [tokenName, setTokenName] = useState("PolRAGion MCP Server")
    const [issued, setIssued] = useState<IssuedToken | null>(null)
    const [error, setError] = useState("")
    const [busy, setBusy] = useState(false)
    const [copied, setCopied] = useState(false)
    const [now, setNow] = useState(Date.now)


    useEffect(() => {
        const controller = new AbortController()
        const loadTokens = async () => {
            try {
                const result = await mcpTokensApi.listMcpTokens({signal: controller.signal, cache: "no-store"})
                if (!controller.signal.aborted) setOverview(result)
            } catch (reason) {
                if (!controller.signal.aborted) setError(await getApiErrorMessage(reason))
            }
        }
        void loadTokens()
        const timer = window.setInterval(() => setNow(Date.now()), 30_000)
        return () => {controller.abort(); window.clearInterval(timer)}
    }, [])

    async function create() {
        setBusy(true); setError(""); setCopied(false)
        try {
            const result = await mcpTokensApi.createMcpToken({createToken: {name: tokenName.trim() || undefined}})
            setIssued(result)
            setOverview(current => current ? {...current, tokens: [result.info, ...current.tokens]} : current)
        } catch (reason) {
            setError(await getApiErrorMessage(reason))
        } finally {setBusy(false)}
    }

    async function copy() {
        if (!issued) return
        try {
            await navigator.clipboard.writeText(issued.token)
            setCopied(true)
        } catch {setError("Copy failed. Select and copy the token manually.")}
    }

    async function revoke(id: string | undefined) {
        if (!id) return
        setBusy(true); setError("")
        try {
            await mcpTokensApi.revokeMcpToken({ tokenId: id })
            setOverview(current => current ? {...current,
                tokens: current.tokens.map(token => token.id === id ? {...token, revokedAt: new Date()} : token),
            } : current)
            if (issued?.info.id === id) setIssued(null)
        } catch (reason) {
            setError(await getApiErrorMessage(reason))
        } finally {setBusy(false)}
    }

    return <div className="min-w-0 space-y-7">
        <div className="space-y-2">
            <h3 className="font-medium">PolRAGion MCP Server</h3>
            <p className="max-w-prose text-muted-foreground text-sm">Create a personal token to search Polarion work items from your IDE, then add the configuration below.</p>
            {overview && !overview.enabled && <p className="text-sm">The MCP server is currently disabled.</p>}
            <form className="max-w-xl space-y-2 pt-3" onSubmit={event => {event.preventDefault(); if (!busy && overview?.enabled && !issued) void create()}}>
                <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
                    <Label htmlFor="mcp-token-name">Token name</Label>
                    {overview && <span className="text-xs text-muted-foreground">Valid for {overview.lifetimeDays} days</span>}
                </div>
                <div className="flex flex-col gap-2 sm:flex-row">
                    <Input id="mcp-token-name" value={tokenName} maxLength={100}
                        className="h-9 min-w-0 flex-1"
                        placeholder="PolRAGion MCP Server" disabled={busy || issued !== null}
                        onChange={event => setTokenName(event.target.value)}/>
                    <Button type="submit" disabled={busy || !overview?.enabled || issued !== null}
                        className="h-9 shrink-0">
                        <KeyRoundIcon/> {busy ? "Creating…" : "Create token"}
                    </Button>
                </div>
            </form>
        </div>
        {error && <p role="alert" className="text-destructive text-sm">{error}</p>}
        {!overview && !error && <p role="status" className="text-muted-foreground text-sm">Loading tokens…</p>}
        {issued && <div className="space-y-3 rounded-lg border p-4">
            <p className="font-medium text-sm">Your new token</p>
            <p className="text-muted-foreground text-sm">Copy it now. The secret is only displayed once and cannot be retrieved after leaving this tab or closing Settings.</p>
            <InputGroup className="h-10">
                <InputGroupInput aria-label="New MCP bearer token" readOnly value={issued.token}
                    className="min-w-0 font-mono text-xs" onFocus={event => event.currentTarget.select()}/>
                <InputGroupAddon align="inline-end">
                    <InputGroupButton aria-label={copied ? "Token copied" : "Copy token"}
                        onClick={() => void copy()} size="sm" className="shrink-0">
                        {copied ? <CheckIcon/> : <CopyIcon/>}<span className="hidden sm:inline">{copied ? "Copied" : "Copy token"}</span>
                    </InputGroupButton>
                </InputGroupAddon>
            </InputGroup>
            <span role="status" className="sr-only">{copied ? "Token copied to clipboard" : ""}</span>
            <p className="text-sm">Valid until: <time dateTime={issued.info.expiresAt.toISOString()}>{date(issued.info.expiresAt.toString())}</time></p>
        </div>}
        <McpClientSetup/>
        <div className="space-y-3 border-t pt-5">
            <h4 className="font-medium text-sm">Your tokens</h4>
            {overview?.tokens.length === 0 && <p className="text-muted-foreground text-sm">No tokens yet.</p>}
            {overview?.tokens.map(token => {
                const expired = token.expiresAt.getTime() <= now
                const status = token.revokedAt ? "Revoked" : expired ? "Expired" : "Active"
                return <div key={token.id} className="space-y-1 rounded-lg border p-3 text-sm">
                    <div className="flex items-center justify-between gap-2"><span className="font-medium">{token.name}</span><span>{status}</span></div>
                    <p className="text-muted-foreground">Created: {token.createdAt?.toLocaleString()}</p>
                    <p>Valid until: <time dateTime={token.expiresAt.toISOString()}>{date(token.expiresAt.toString())}</time></p>
                    {!token.revokedAt && <Button type="button" size="sm" variant="outline" disabled={busy} onClick={() => void revoke(token.id)}>Revoke token</Button>}
                </div>
            })}
        </div>
    </div>
}


function McpClientSetup() {
    const [copiedConfiguration, setCopiedConfiguration] = useState("")
    const [copyError, setCopyError] = useState("")
    const serverUrl = new URL(`${apiBasePath.replace(/\/+$/, "")}/mcp/`, window.location.origin).href
    const connection = {url: serverUrl, headers: {Authorization: "Bearer YOUR_TOKEN"}}
    const clients = [
        {id: "vscode", label: "VS Code", hint: "Add to .vscode/mcp.json, replace YOUR_TOKEN, and start the server.",
         url: "https://code.visualstudio.com/docs/agents/reference/mcp-configuration",
         config: {mcpServers: {"PolRAGion-MCP": {type: "http", ...connection}}}},
        {id: "jetbrains", label: "JetBrains", hint: "Settings → Tools → AI Assistant → MCP → Add → HTTP. Paste this configuration and replace YOUR_TOKEN.",
         url: "https://www.jetbrains.com/help/ai-assistant/mcp.html",
         config: {mcpServers: {"PolRAGion-MCP": connection}}},
    ]

    async function copyConfiguration(value: string) {
        setCopyError("")
        try {
            await navigator.clipboard.writeText(value)
            setCopiedConfiguration(value)
        } catch {setCopyError("Copy failed. Select and copy the configuration manually.")}
    }

    return <section className="min-w-0 space-y-3 border-t pt-5" aria-labelledby="mcp-client-setup">
        <div className="flex flex-wrap items-center justify-between gap-2">
            <h4 id="mcp-client-setup" className="font-medium text-sm">Connect your IDE</h4>
            <DocumentationDialog trigger={<Button type="button" variant="outline" size="sm"><BookOpenIcon/>Documentation</Button>}/>
        </div>
        <Tabs defaultValue="vscode" className="min-w-0">
            <TabsList aria-label="IDE configuration" className="!h-9 !flex-row">
                <TabsTrigger value="vscode" className="!w-auto !justify-center">VS Code</TabsTrigger>
                <TabsTrigger value="jetbrains" className="!w-auto !justify-center">JetBrains</TabsTrigger>
            </TabsList>
            {clients.map(client => {
                const configuration = JSON.stringify(client.config, null, 2)
                const copied = copiedConfiguration === configuration
                return <TabsContent key={client.id} value={client.id} className="min-w-0 space-y-3">
                    <p className="text-muted-foreground text-sm">{client.hint}</p>
                    <div className="min-w-0 overflow-hidden rounded-lg border">
                        <div className="flex items-center justify-between gap-2 border-b bg-muted/40 px-3 py-1.5">
                            <span className="text-muted-foreground text-xs">JSON configuration</span>
                            <Button type="button" size="sm" variant="ghost" onClick={() => void copyConfiguration(configuration)}>
                                {copied ? <CheckIcon/> : <CopyIcon/>}{copied ? "Copied" : "Copy config"}
                            </Button>
                        </div>
                        <pre tabIndex={0} aria-label={`${client.label} MCP configuration`} className="max-w-full overflow-x-auto p-3 text-xs leading-5"><code>{configuration}</code></pre>
                    </div>
                    <a href={client.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-muted-foreground underline underline-offset-4 hover:text-foreground">
                        {client.label} setup reference<ExternalLinkIcon className="size-3"/>
                    </a>
                </TabsContent>
            })}
        </Tabs>
        <p className="text-xs text-muted-foreground">Keep tokens private. If a token expires, create a new one here and replace it in your IDE.</p>
        <span role="status" className="sr-only">{copiedConfiguration ? "Configuration copied to clipboard" : ""}</span>
        {copyError && <p role="alert" className="text-destructive text-sm">{copyError}</p>}
    </section>
}
