"use client"

import * as React from "react"

import {NavMain} from "@/components/nav-main"
import {NavFilter} from "@/components/nav-filter.tsx"
import {NavSecondary} from "@/components/nav-secondary"
import {NavUser} from "@/components/nav-user"
import {SettingsDialog} from "@/components/settings-dialog.tsx"
import {APP_INFO, copyrightNotice} from "@/lib/app-info.ts"
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
    ListMinus,
    ListTodo,
    TableRowsSplit,
    MessageSquareTextIcon, LibraryBig,
} from "lucide-react"

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
    filter: [
        {
            title: "Projects",
            url: "#",
            icon: (
                <LibraryBig />
            ),
            isActive: false,
            items: [
                {
                    title: "Work in Progress",
                    url: "#",
                },
            ],
        },
        {
            title: "Documents",
            url: "#",
            icon: (
                <ListMinus/>
            ),
            isActive: false,
            items: [
                {
                    title: "Work in Progress",
                    url: "#",
                },
            ],
        },
        {
            title: "Properties",
            url: "#",
            icon: (
                <ListTodo/>
            ),
            isActive: false,
            items: [
                {
                    title: "Work in Progress",
                    url: "#",
                },
            ],
        },
        {
            title: "Category",
            url: "#",
            icon: (
                <TableRowsSplit/>
            ),
            isActive: false,
            items: [
                {
                    title: "Work in Progress",
                    url: "#",
                },
            ],
        },
    ],
}

export function AppSidebar({...props}: React.ComponentProps<typeof Sidebar>) {
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
                                <span className="truncate font-medium">Polragion</span>
                                <span className="truncate text-xs">Ask your work items</span>
                            </div>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarHeader>
            <SidebarContent>
                <NavMain />
                <NavFilter items={data.filter}/>
                <NavSecondary items={data.navSecondary} className="mt-auto"/>
            </SidebarContent>
            <SidebarFooter>
                <NavUser/>
            </SidebarFooter>
            <SettingsDialog
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
            />
        </Sidebar>
    )
}
