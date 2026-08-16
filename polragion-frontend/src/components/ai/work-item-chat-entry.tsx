import {
    ExternalLinkIcon,
    LinkIcon,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import type { WorkItemSearchHit } from "@/api"
import {WorkItemDescription} from "@/components/ai/work-item-description.tsx";
import {getWorkItemUrl} from "@/lib/work-item-references.ts";

interface WorkItemProps {
    hit: WorkItemSearchHit
}

export function WorkItemChatEntry({ hit }: WorkItemProps) {
    const { workItem, score } = hit

    return (
        <div className="space-y-3 py-2">
            {/* Header */}
            <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                        <a
                            href={getWorkItemUrl(
                                workItem.projectId,
                                workItem.workItemId,
                            )}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 font-mono text-sm font-medium text-primary hover:underline"
                        >
                            {workItem.workItemId}
                            <ExternalLinkIcon className="size-3" />
                        </a>

                        <Badge variant="secondary">
                            {workItem.status}
                        </Badge>
                    </div>

                    <h3 className="font-medium leading-snug">
                        {workItem.title}
                    </h3>
                </div>
                <span className="shrink-0 text-xs text-muted-foreground">{Math.round(score * 100)}% match</span>
            </div>

            {/* Metadata */}
            <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
                <span>{workItem.workItemType}</span>
                <span>Project {workItem.projectId}</span>
                <span>Rev. {workItem.revision}</span>
            </div>

            {/* Description */}
            {workItem.description && (
                <WorkItemDescription markdown={workItem.description} />
            )}

            {/* Linked work items */}
            {workItem.linkedWorkItems?.length ? (
                <div className="flex flex-wrap items-center gap-2">
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <LinkIcon className="size-3.5" />
                        Linked
                    </div>

                    {workItem.linkedWorkItems.map(linked => (
                        <a
                            key={`${linked.role}-${linked.id}`}
                            href={getWorkItemUrl(
                                workItem.projectId,
                                linked.id,
                            )}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-1 font-mono text-xs transition-colors hover:bg-muted/80"
                        >
                            {linked.id}
                            <span className="font-sans text-muted-foreground">
                {linked.role}
              </span>
                        </a>
                    ))}
                </div>
            ) : null}
        </div>
    )
}
