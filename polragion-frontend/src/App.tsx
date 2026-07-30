import { useState } from 'react'
import './App.css'
import Page from "@/Page.tsx";
import { HelloString } from "@/components/art/animated-calligraphy.tsx";
import { Chat } from "@/components/ai/chat.tsx";
import { GitHubAuthProvider } from "@/hooks/use-github-auth.tsx";
import {TooltipProvider} from "@/components/ui/tooltip.tsx";

function App() {
    const [showIntro, setShowIntro] = useState(true)

    return (
        <TooltipProvider>
        <GitHubAuthProvider>
            {/* Is rendered directly without delay */}
            <Page>
                <Chat />
            </Page>

            {/* Only optical above the main site */}
            {showIntro && (
                <div>
                    <HelloString
                        fullScreen
                        textCol="black"
                        onComplete={() => setShowIntro(false)}
                    />
                    {/*<MagneticButtonDemo />*/}
                </div>
            )}
        </GitHubAuthProvider>
        </TooltipProvider>
    )
}

export default App
