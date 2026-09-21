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
import {Field, FieldLabel} from "./ui/field";
import {Checkbox} from "@/components/ui/checkbox.tsx";

export function NavFilter({items,}: {
    items: {
        title: string
        icon: React.ReactNode
        isActive?: boolean
        items?: {
            title: string
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
                                                     render={<a />}
                                                >

                                                    {/*<FieldGroup className="mx-auto w-56">*/}
                                                        <Field orientation="horizontal">
                                                            <Checkbox id={subItem.title} name={subItem.title} />
                                                            <FieldLabel htmlFor={subItem.title}>
                                                                {subItem.title}
                                                            </FieldLabel>
                                                        </Field>
                                                    {/*</FieldGroup>*/}

                                                </SidebarMenuSubButton>
                                            </SidebarMenuSubItem>
                                        ))}
                                    </SidebarMenuSub>
                                </CollapsibleContent>
                            </>
                        ) : (
                            <SidebarMenuButton
                                tooltip={item.title}
                                render={<a />}
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
