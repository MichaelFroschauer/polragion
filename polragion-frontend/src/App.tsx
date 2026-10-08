import { useState } from 'react'
import './App.css'
import Page from "@/Page.tsx";
import { ApplePolRAGionEffect, HelloScreen } from "@/components/art/animated-calligraphy.tsx";
import { Chat } from "@/components/ai/chat.tsx";
import { GitHubAuthProvider, useGitHubAuth } from "@/hooks/use-github-auth.tsx";
import {TooltipProvider} from "@/components/ui/tooltip.tsx";
import {ChatContextProvider} from "@/hooks/use-chat.tsx";
import {SettingsProvider} from "@/hooks/use-settings.tsx";
import { Button } from "@/components/ui/button.tsx";
import { LoaderCircleIcon, LogInIcon } from "lucide-react";

function AuthenticatedApp() {
    const [showIntro, setShowIntro] = useState(() => {
        const lastShown = localStorage.getItem("showIntroTimestamp")
        if (!lastShown) {
            return true;
        }
        const oneDay = 12 * 60 * 60 * 1000;
        return Date.now() - Number(lastShown) >= oneDay;
    });

    return (
        <SettingsProvider>
        <ChatContextProvider>
            {/* Is rendered directly without delay */}
            <Page>
                <Chat />
            </Page>

            {/* Only optical above the main site */}
            {showIntro && (
                <div>
                    <HelloScreen
                        fullScreen
                        textCol="black"
                        onComplete={() => {
                            setShowIntro(false);
                            localStorage.setItem("showIntroTimestamp", Date.now().toString());
                        }}
                    />
                    {/*<MagneticButtonDemo />*/}
                </div>
            )}
        </ChatContextProvider>
        </SettingsProvider>
    )
}

function AccessScreen({ denied }: { denied: boolean }) {
    const { login, switchAccount } = useGitHubAuth()
    const params = new URLSearchParams(window.location.search)
    const header = denied ? params.get("header") || "Access denied" : "Sign in required"
    const text = denied
        ? params.get("text") || "Your GitHub account is not authorized to access PolRAGion."
        : "PolRAGion is available to approved users only. Sign in with GitHub to continue."

    return (
        <main className="flex min-h-svh items-center justify-center bg-background px-6 py-12 text-foreground">
            <div className="flex w-full max-w-lg flex-col items-center text-center">
                <ApplePolRAGionEffect className="h-auto w-full max-w-sm" />
                <h1 className="mt-10 text-xl font-semibold">{header}</h1>
                <p className="mt-3 max-w-md text-sm leading-6 text-muted-foreground">{text}</p>
                <Button className="mt-8 h-auto min-h-9 max-w-full whitespace-normal py-2 text-center" size="lg" onClick={denied ? switchAccount : login}>
                    <LogInIcon className="size-4" />
                    {denied ? "Sign in with another GitHub account" : "Sign in with GitHub"}
                </Button>
            </div>
        </main>
    )
}

function AuthGate() {
    const { isAuthenticated, isLoading } = useGitHubAuth()
    if (isLoading) {
        return (
            <main className="flex min-h-svh items-center justify-center bg-background" role="status" aria-label="Checking sign-in status">
                <LoaderCircleIcon className="size-6 animate-spin text-muted-foreground" />
            </main>
        )
    }

    if (!isAuthenticated) {
        const params = new URLSearchParams(window.location.search)
        const denied = window.location.pathname === "/permission-denied" || (params.has("header") && params.has("text"))
        return <AccessScreen denied={denied} />
    }

    return <AuthenticatedApp />
}

function App() {
    return (
        <TooltipProvider>
        <GitHubAuthProvider>
            <AuthGate />
        </GitHubAuthProvider>
        </TooltipProvider>
    )
}

export default App
