"use client"

import * as React from "react"

import {NavMain} from "@/components/nav-main"
import {NavFilter, type FilterSection} from "@/components/nav-filter.tsx"
import {NavSecondary} from "@/components/nav-secondary"
import {NavUser} from "@/components/nav-user"

import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from "@/components/ui/sidebar.tsx"
import {
    MessageSquareTextIcon,  Book, BookCopy, FileText, TableProperties,
} from "lucide-react"
import {useSearchFilters} from "@/hooks/use-search-filters";
import {formatCategoryName} from "@/lib/search-filters";
import {polarionMetadataApi} from "@/api/client.ts";
import {useEffect, useState} from "react";
import type {PolarionImportStatus} from "@/api";


const data = {
    navSecondary: [
        // {
        //   title: "Support",
        //   url: "#",
        //   icon: (
        //     <LifeBuoyIcon />
        //   ),
        // },
        // {
        //   title: "Feedback",
        //   url: "#",
        //   icon: (
        //     <SendIcon />
        //   ),
        // },
    ],

}

export function AppSidebar({...props}: React.ComponentProps<typeof Sidebar>) {

    const {searchScopes, filterStatus, retry} = useSearchFilters()
    const [importStatus, setImportStatus] = useState<PolarionImportStatus | null | "loading" | "unavailable">("loading")

    useEffect(() => {
        const loadImportStatus = async () => {
            try {
                const status = await polarionMetadataApi.getPolarionImportStatus()
                setImportStatus(status)
            } catch (error) {
                setImportStatus("unavailable")
                console.error("Error fetching import status:", error)
            }
        }

        void loadImportStatus()
    }, [])

    const filters: FilterSection[] = [
        {
            id: "project-contexts",
            title: "Project Contexts",
            icon: <BookCopy />,
            emptyMessage: "No project contexts available.",
            items: (searchScopes?.projectContexts ?? []).map(context => ({
                id: JSON.stringify(["context", context]),
                title: context,
                projects: (searchScopes?.projects ?? [])
                    .filter(project => project.contexts.includes(context))
                    .map(project => project.id),
            })),
        },
        {
            id: "polarion-projects",
            title: "Polarion Projects",
            icon: <Book />,
            emptyMessage: "No projects available.",
            items: (searchScopes?.projectIds ?? []).map(id => ({
                id: JSON.stringify(["project", id]), title: id,
            })),
        },
        {
            id: "documents",
            title: "Documents",
            icon: <FileText />,
            emptyMessage: "No documents configured for the available projects.",
            items: [],
            groups: (searchScopes?.projects ?? [])
                .filter(project => project.documents.length > 0)
                .map(project => ({
                    id: project.id,
                    title: project.id,
                    items: project.documents.map(document => {
                        // The API provides a configured document path, not a separate display name.
                        const parts = document.name.split(/[/\\]/).filter(Boolean)
                        const title = parts.at(-1) || document.name
                        return {
                            id: JSON.stringify(["document", project.id, document.name]),
                            title,
                            path: document.name !== title ? document.name : undefined,
                        }
                    }),
                })),
        },
        {
            id: "category",
            title: "Category",
            icon: <TableProperties />,
            emptyMessage: "No categories available.",
            items: [...new Set(searchScopes?.projectCategories.map(formatCategoryName) ?? [])]
                .map(category => ({id: JSON.stringify(["category", category]), title: category})),
        },
    ]


    return (
        <Sidebar variant="floating" collapsible="offcanvas" {...props}>
            <SidebarHeader>
                <SidebarMenu>
                    <SidebarMenuItem>
                        <SidebarMenuButton size="lg" render={<a href="#"/>}>
                            <div
                                className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                                <MessageSquareTextIcon className="size-4"/>
                            </div>
                            <div className="grid flex-1 text-left text-sm leading-tight">
                                <span className="truncate font-medium">PolRAGion</span>
                                <span className="truncate text-xs">Ask your work items</span>
                            </div>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarHeader>
            <SidebarContent className="overflow-x-hidden">
                <NavMain />
                <NavFilter items={filters} status={filterStatus} onRetry={retry}/>
                <NavSecondary items={data.navSecondary} className="mt-auto"/>
            </SidebarContent>
            <SidebarFooter>
                <div className="px-2 py-1 text-xs text-sidebar-foreground/70">
                    <span className="block text-sidebar-foreground/50">Last Polarion import</span>
                    {importStatus === "loading" ? "Loading..." :
                        importStatus === "unavailable" ? "Status unavailable" :
                            importStatus === null ? "No completed import yet" : (
                                <>
                                    <time dateTime={importStatus.completedAt.toString()} className="block">
                                        {new Date(importStatus.completedAt).toLocaleString(undefined, {dateStyle: "medium", timeStyle: "short"})}
                                    </time>
                                    <span>{importStatus.processedItems} items processed</span>
                                </>
                            )}
                </div>
                <NavUser/>
            </SidebarFooter>
            {/* <SettingsDialog
                defaultCategory="about"
                trigger={
                    <button
                        className="px-4 text-left text-[0.6rem] text-sidebar-foreground/40 transition-colors hover:text-sidebar-foreground/80 group-data-[collapsible=icon]:hidden"
                        title={`About ${APP_INFO.name}`}
                        type="button"
                    >
                        {copyrightNotice()} · {APP_INFO.license}
                    </button>
                }
            /> */}
        </Sidebar>
    )
}
