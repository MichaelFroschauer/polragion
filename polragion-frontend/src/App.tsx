import { useEffect, useState } from 'react'
import { healthApi } from './api/client'
import './App.css'
import Page from "@/Page.tsx";
import {HelloString} from "@/components/art/animated-calligraphy.tsx";
import MessageDemo from "@/components/ai/message.tsx";
import ModelSelectorDemo from "@/components/ai/model-selector.tsx";
import PromptInputDemo from "@/components/ai/prompt-input.tsx";
import {MagneticButtonDemo} from "@/components/ui/magnetic.tsx";

function App() {
  // const [count, setCount] = useState(0)
  // const [health, setHealth] = useState<string>('checking…')

  // useEffect(() => {
  //   healthApi
  //     .liveness()
  //     .then((res) => setHealth(res.status))
  //     .catch(() => setHealth('unreachable'))
  // }, [])

    const [showIntro, setShowIntro] = useState(true)

    return (
        <>
            {/* Is rendered directly without delay */}
            <Page>
                <div>
                    <MessageDemo />
                    <PromptInputDemo />
                    {/*<ModelSelectorDemo />*/}
                </div>
            </Page>

            {/* Only optical above the main site */}
            {showIntro && (
                <div>
                    <HelloString
                        fullScreen
                        textCol="black"
                        onComplete={() => setShowIntro(false)}
                    />
                    <MagneticButtonDemo />
                </div>
            )}
        </>
    )
}

export default App
