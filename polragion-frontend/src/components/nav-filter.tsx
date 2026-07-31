"use client"
import {
    SidebarGroup,
    SidebarGroupLabel,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem, SidebarMenuSub, SidebarMenuSubButton, SidebarMenuSubItem,
} from "@/components/ui/sidebar.tsx"
import {ArrowUpNarrowWide, ChevronRightIcon} from "lucide-react"
import {Collapsible, CollapsibleContent, CollapsibleTrigger} from "@/components/ui/collapsible.tsx";

export function NavFilter({items,}: {
    items: {
        title: string
        url: string
        icon: React.ReactNode
        isActive?: boolean
        items?: {
            title: string
            url: string
        }[]
    }[]
}) {

    return (
        <SidebarGroup>
            <SidebarGroupLabel>Filters</SidebarGroupLabel>
            <SidebarMenuButton tooltip="Reset Filter" className="[&[data-panel-open]>svg:last-child]:rotate-90"><ArrowUpNarrowWide />Reset</SidebarMenuButton>

            <SidebarMenu>
                {items.map((item) => (
                    <Collapsible
                        key={item.title}
                        defaultOpen={item.isActive}
                        render={<SidebarMenuItem/>}
                    >
                        {item.items?.length ? (
                            <>
                                <CollapsibleTrigger
                                    render={
                                        <SidebarMenuButton
                                            tooltip={item.title}
                                            className="[&[data-panel-open]>svg:last-child]:rotate-90"
                                        />
                                    }
                                >
                                    {item.icon}
                                    <span>{item.title}</span>
                                    <ChevronRightIcon className="ml-auto transition-transform duration-200"/>
                                </CollapsibleTrigger>

                                <CollapsibleContent>
                                    <SidebarMenuSub>
                                        {item.items.map((subItem) => (
                                            <SidebarMenuSubItem key={subItem.title}>
                                                <SidebarMenuSubButton
                                                    render={<a href={subItem.url}/>}
                                                >
                                                    <span>{subItem.title}</span>
                                                </SidebarMenuSubButton>
                                            </SidebarMenuSubItem>
                                        ))}
                                    </SidebarMenuSub>
                                </CollapsibleContent>
                            </>
                        ) : (
                            <SidebarMenuButton
                                tooltip={item.title}
                                render={<a href={item.url}/>}
                            >
                                {item.icon}
                                <span>{item.title}</span>
                            </SidebarMenuButton>
                        )}
                    </Collapsible>
                ))}
            </SidebarMenu>
        </SidebarGroup>
    )
}
