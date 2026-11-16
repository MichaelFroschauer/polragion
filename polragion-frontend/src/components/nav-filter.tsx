"use client"

import {useId, type ReactNode} from "react"
import {ChevronRightIcon, CircleHelpIcon, RotateCcwIcon} from "lucide-react"
import {
    SidebarGroup, SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem,
} from "@/components/ui/sidebar.tsx"
import {Collapsible, CollapsibleContent, CollapsibleTrigger} from "@/components/ui/collapsible.tsx"
import {useSearchFilters} from "@/hooks/use-search-filters"
import {Checkbox} from "@/components/ui/checkbox.tsx"
import {Tooltip, TooltipContent, TooltipTrigger} from "@/components/ui/tooltip.tsx"

export interface FilterOption {
    id: string
    title: string
    projects?: string[]
    path?: string
}

export interface FilterSection {
    id: string
    title: string
    icon: ReactNode
    items: FilterOption[]
    groups?: {id: string; title: string; items: FilterOption[]}[]
    emptyMessage: string
}

function FilterRow({item, checked, onCheckedChange}: {
    item: FilterOption
    checked: boolean
    onCheckedChange: (checked: boolean) => void
}) {
    const id = useId()
    return (
        <li className="min-w-0 rounded-md has-data-checked:bg-sidebar-accent/60">
            <label htmlFor={id} className="flex min-w-0 cursor-pointer items-start gap-2 rounded-md px-2 py-1 text-[14px] hover:bg-sidebar-accent focus-within:bg-sidebar-accent">
                <Checkbox id={id} checked={checked} onCheckedChange={onCheckedChange} className="mt-0.5" />
                <span className="min-w-0 flex-1">
                    <span className="block leading-[20px] [overflow-wrap:anywhere]">{item.title}</span>
                    {item.projects && (
                        <span className="mt-0.5 block text-[12px] leading-[16px] text-muted-foreground [overflow-wrap:anywhere]">
                            <span className="sr-only">Projects: </span>
                            {item.projects.length ? item.projects.join(" · ") : "No projects assigned"}
                        </span>
                    )}
                </span>
            </label>
            {item.path && (
                <details className="group/path min-w-0 pb-1 pl-8 pr-2 text-[12px] text-muted-foreground">
                    <summary className="flex cursor-pointer list-none items-center gap-1 rounded-sm py-0.5 hover:text-sidebar-foreground focus-visible:outline-2 focus-visible:outline-ring [&::-webkit-details-marker]:hidden">
                        <ChevronRightIcon aria-hidden="true" className="size-3 shrink-0 transition-transform group-open/path:rotate-90 motion-reduce:transition-none" />
                        <span className="shrink-0">Path</span>
                        <span className="min-w-0 truncate group-open/path:hidden">{item.path}</span>
                    </summary>
                    <p className="pt-1 leading-relaxed text-sidebar-foreground [overflow-wrap:anywhere]">{item.path}</p>
                </details>
            )}
        </li>
    )
}

export function NavFilter({items, status = "ready", onRetry}: {
    items: FilterSection[]
    status?: "loading" | "error" | "ready"
    onRetry?: () => void
}) {
    const {excluded, setOptionChecked, reset} = useSearchFilters()
    const optionIds = new Set(items.flatMap(section => section.groups
        ? section.groups.flatMap(group => group.items.map(item => item.id))
        : section.items.map(item => item.id)))
    const hasChanges = [...excluded].some(id => optionIds.has(id))
    const renderCount = (options: FilterOption[]) => {
        const selected = options.filter(option => !excluded.has(option.id)).length
        return (
            <span className="shrink-0 text-[12px] tabular-nums text-muted-foreground">
                <span aria-hidden="true">{selected}/{options.length}</span>
                <span className="sr-only">{selected} of {options.length} selected</span>
            </span>
        )
    }
    const renderOptions = (options: FilterOption[]) => (
        <ul className="min-w-0">
            {options.map(item => (
                <FilterRow key={item.id} item={item} checked={!excluded.has(item.id)} onCheckedChange={checked => setOptionChecked(item.id, checked)} />
            ))}
        </ul>
    )

    return (
        <SidebarGroup>
            <div className="flex items-center justify-between gap-2 pr-2">
                <SidebarGroupLabel className="gap-1">
                    Filters
                    <Tooltip>
                        <TooltipTrigger type="button" aria-label="How filters work"
                            className="flex size-5 items-center justify-center rounded-sm text-muted-foreground hover:text-sidebar-foreground focus-visible:outline-2 focus-visible:outline-ring">
                            <CircleHelpIcon aria-hidden="true" className="size-3.5" />
                        </TooltipTrigger>
                        <TooltipContent side="right" align="start" className="block max-w-64 space-y-2 leading-relaxed">
                            <p>Uncheck anything you want to leave out of Search and Ask.</p>
                            <p>Select several options in one group to include any of them. Use other groups to narrow the results further.</p>
                        </TooltipContent>
                    </Tooltip>
                </SidebarGroupLabel>
                <button type="button" onClick={reset} disabled={!hasChanges}
                    className="flex items-center gap-1 rounded-sm px-1 py-1 text-xs text-muted-foreground hover:text-sidebar-foreground focus-visible:outline-2 focus-visible:outline-ring disabled:cursor-default disabled:opacity-50">
                    <RotateCcwIcon aria-hidden="true" className="size-3" />Reset
                </button>
            </div>
            {status === "loading" ? (
                <div role="status" className="space-y-3 px-2 py-3">
                    <span className="sr-only">Loading filters…</span>
                    {items.map(item => <div key={item.id} className="h-5 rounded bg-sidebar-accent motion-safe:animate-pulse" />)}
                </div>
            ) : status === "error" ? (
                <div role="status" className="px-2 py-3 text-xs leading-relaxed text-muted-foreground">
                    <p>Filters could not be loaded.</p>
                    <button type="button" onClick={onRetry} className="mt-2 rounded-sm text-sidebar-foreground underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-ring">Try again</button>
                </div>
            ) : (
                <SidebarMenu>
                    {items.map(section => {
                        const options = section.groups?.flatMap(group => group.items) ?? section.items
                        const count = options.length
                        return (
                            <Collapsible key={section.id} render={<SidebarMenuItem className="min-w-0" />}>
                                <CollapsibleTrigger render={<SidebarMenuButton className="[&[data-panel-open]>svg:last-child]:rotate-90" />}>
                                    {section.icon}
                                    <span className="min-w-0 flex-1 truncate">{section.title}</span>
                                    {renderCount(options)}
                                    <ChevronRightIcon aria-hidden="true" className="transition-transform duration-200 motion-reduce:transition-none" />
                                </CollapsibleTrigger>
                                <CollapsibleContent className="min-w-0">
                                    <div className="mb-2 ml-3 min-w-0 border-l border-sidebar-border pl-2">
                                        {count === 0 ? <p className="px-2 py-3 text-xs leading-relaxed text-muted-foreground">{section.emptyMessage}</p>
                                            : section.groups ? section.groups.map(group => (
                                                <Collapsible key={group.id} defaultOpen className="min-w-0 py-1">
                                                    <CollapsibleTrigger className="flex w-full min-w-0 items-start gap-1.5 rounded-md px-2 py-1 text-left text-[12px] font-medium text-muted-foreground hover:bg-sidebar-accent focus-visible:outline-2 focus-visible:outline-ring [&[data-panel-open]>svg]:rotate-90">
                                                        <ChevronRightIcon aria-hidden="true" className="mt-0.5 size-3 shrink-0 transition-transform motion-reduce:transition-none" />
                                                        <span className="min-w-0 flex-1 [overflow-wrap:anywhere]">{group.title}</span>
                                                        {renderCount(group.items)}
                                                    </CollapsibleTrigger>
                                                    <CollapsibleContent>{renderOptions(group.items)}</CollapsibleContent>
                                                </Collapsible>
                                            )) : renderOptions(section.items)}
                                    </div>
                                </CollapsibleContent>
                            </Collapsible>
                        )
                    })}
                </SidebarMenu>
            )}
        </SidebarGroup>
    )
}
