import {useState} from "react"
import {ChevronDownIcon, ChevronUpIcon} from "lucide-react"
import DOMPurify from "dompurify"

export function WorkItemDescription({html}: { html: string }) {
    const [expanded, setExpanded] = useState(false)

    return (
        <div className="space-y-2">
            <div className={`overflow-hidden ${expanded ? "" : "max-h-30"}`}>
                <div className="
                    prose prose-sm max-w-none
                    text-muted-foreground

                    prose-headings:mb-2
                    prose-headings:mt-4
                    prose-headings:text-foreground

                    prose-h1:text-base
                    prose-h2:text-sm

                    prose-p:my-2

                    prose-strong:font-medium
                    prose-strong:text-foreground

                    prose-blockquote:my-3
                    prose-blockquote:border-l-2
                    prose-blockquote:pl-3

                    prose-li:my-0

                    prose-table:my-3
                    prose-th:px-2
                    prose-th:py-1
                    prose-td:px-2
                    prose-td:py-1

                    prose-pre:max-w-full
                    prose-pre:overflow-x-auto
                    prose-pre:text-xs
                    "
                    dangerouslySetInnerHTML={{
                        __html: DOMPurify.sanitize(html),
                    }}
                />
            </div>

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
        </div>
    )
}
