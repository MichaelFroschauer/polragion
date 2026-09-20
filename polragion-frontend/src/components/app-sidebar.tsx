"use client"

import * as React from "react"

import {NavMain} from "@/components/nav-main"
import {NavFilter} from "@/components/nav-filter.tsx"
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
import {polarionMetadataApi} from "@/api/client.ts";
import {useEffect, useState} from "react";
import type {PolarionMetadataResponse} from "@/api";


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
            id: "project-contexts",
            title: "Project Contexts",
            icon: (
                <BookCopy />
            ),
            isActive: false,
            items: [
                {
                    title: "Work in Progress",
                },
            ],
        },
        {
            id: "polarion-projects",
            title: "Polarion Projects",
            icon: (
                <Book />
            ),
            isActive: false,
            items: [
                {
                    title: "Work in Progress",
                },
            ],
        },
        {
            id: "documents",
            title: "Documents",
            icon: (
                <FileText />
            ),
            isActive: false,
            items: [
                {
                    title: "Work in Progress",
                },
            ],
        },
        {
            id: "category",
            title: "Category",
            icon: (
                <TableProperties />
            ),
            isActive: false,
            items: [
                {
                    title: "Work in Progress",
                },
            ],
        },
        // {
        //     title: "Properties",
        //     url: "#",
        //     icon: (
        //         <ListTodo/>
        //     ),
        //     isActive: false,
        //     items: [
        //         {
        //             title: "Work in Progress",
        //             url: "#",
        //         },
        //     ],
        // },
    ],
}

export function AppSidebar({...props}: React.ComponentProps<typeof Sidebar>) {

    const [searchScopes, setSearchScopes] = useState<PolarionMetadataResponse | null>(null)

    useEffect(() => {
        const loadSearchScopes = async () => {
            try {
                const scopes = await polarionMetadataApi.getPolarionSearchScopes()
                setSearchScopes(scopes)
            } catch (error) {
                console.error("Error fetching search scopes:", error)
            }
        }

        void loadSearchScopes()
    }, [])

    function capitalizeFirstLetter(str: string): string {
        if (str.length === 0) {
            return str;
        }
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    function formatCategoryName(category: string): string {
        // Remove the specified pre- and postfixes
        const cleanedCategory = category.replace(/-specification|system-|product-|software-/g, "");
        return capitalizeFirstLetter(cleanedCategory) + "s";
    }

    const filters = data.filter.map(filter => {
        switch (filter.id) {
            case "project-contexts":
                return {
                    ...filter,
                    items: searchScopes?.projectContexts.map(context => ({
                        title: context,
                    })) ?? [],
                }

            case "polarion-projects":
                return {
                    ...filter,
                    items: searchScopes?.projectIds.map(projectId => ({
                        title: projectId,
                    })) ?? [],
                }

            case "category": {
                const uniqueCategories = [
                    ...new Set(
                        searchScopes?.projectCategories.map(formatCategoryName) ?? []
                    ),
                ]

                return {
                    ...filter,
                    items: uniqueCategories.map(category => ({
                        title: category,
                    })),
                }
            }

            default:
                return filter
        }
    })


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
                <NavFilter items={filters}/>
                <NavSecondary items={data.navSecondary} className="mt-auto"/>
            </SidebarContent>
            <SidebarFooter>
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
