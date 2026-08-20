import { useState } from 'react'
import './App.css'
import Page from "@/Page.tsx";
import { HelloScreen } from "@/components/art/animated-calligraphy.tsx";
import { Chat } from "@/components/ai/chat.tsx";
import { GitHubAuthProvider } from "@/hooks/use-github-auth.tsx";
import {TooltipProvider} from "@/components/ui/tooltip.tsx";
import {ChatContextProvider} from "@/hooks/use-chat.tsx";
import {SettingsProvider} from "@/hooks/use-settings.tsx";

function App() {
    const [showIntro, setShowIntro] = useState(() => {
        const lastShown = localStorage.getItem("showIntroTimestamp")
        if (!lastShown) {
            return true;
        }
        const oneDay = 12 * 60 * 60 * 1000;
        return Date.now() - Number(lastShown) >= oneDay;
    });

    return (
        <TooltipProvider>
        <GitHubAuthProvider>
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
        </GitHubAuthProvider>
        </TooltipProvider>
    )
}

export default App
