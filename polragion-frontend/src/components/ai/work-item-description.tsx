import {useEffect, useRef, useState} from "react"
import {ChevronDownIcon, ChevronUpIcon} from "lucide-react"
import {Streamdown} from "streamdown"

export function WorkItemDescription({markdown}: { markdown: string }) {
    const [expanded, setExpanded] = useState(false)
    const [overflowing, setOverflowing] = useState(false)
    const clipRef = useRef<HTMLDivElement>(null)
    const contentRef = useRef<HTMLDivElement>(null)

    // Only measurable while collapsed; the expanded container always fits its content.
    useEffect(() => {
        const clip = clipRef.current
        const content = contentRef.current
        if (expanded || !clip || !content) return

        const observer = new ResizeObserver(() => {
            setOverflowing(clip.scrollHeight > clip.clientHeight)
        })
        observer.observe(content)
        return () => observer.disconnect()
    }, [markdown, expanded])

    return (
        <div className="space-y-2">
            <div ref={clipRef} className={`overflow-hidden ${expanded ? "" : "max-h-30"}`}>
                <div ref={contentRef}>
                    <Streamdown
                        parseIncompleteMarkdown={false}
                        className="
                            text-sm text-muted-foreground

                            [&>*:first-child]:mt-0
                            [&>*:last-child]:mb-0

                            [&_h1]:text-base
                            [&_h2]:text-sm
                            [&_:is(h1,h2,h3,h4)]:text-foreground

                            [&_strong]:font-medium
                            [&_strong]:text-foreground

                            [&_pre]:max-w-full
                            [&_pre]:overflow-x-auto
                            [&_pre]:text-xs
                        "
                    >
                        {markdown}
                    </Streamdown>
                </div>
            </div>

            {overflowing && (
                <button
                    type="button"
                    onClick={() => setExpanded(value => !value)}
                    className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
                >
                    {expanded ? (
                        <><ChevronUpIcon className="size-3"/> Show less</>
                    ) : (
                        <><ChevronDownIcon className="size-3"/>Show more</>
                    )}
                </button>
            )}
        </div>
    )
}
