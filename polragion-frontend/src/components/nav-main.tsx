import {
    SidebarGroup,
    SidebarGroupLabel,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from "@/components/ui/sidebar.tsx"
import {BookOpenIcon, Settings2Icon, SquarePen} from "lucide-react"
import {DocumentationDialog} from "@/components/documentation-dialog";
import {useChat} from "@/hooks/use-chat.tsx";
import {SettingsDialog} from "@/components/settings-dialog.tsx";


export function NavMain() {
    const { resetSession: newChat } = useChat()

    return (
        <SidebarGroup>
            <SidebarGroupLabel>Platform</SidebarGroupLabel>

            <SidebarMenu>
                <SidebarMenuItem>
                    <SidebarMenuButton onClick={newChat}><SquarePen />New chat</SidebarMenuButton>
                </SidebarMenuItem>

                <SidebarMenuItem>
                    <DocumentationDialog trigger={<SidebarMenuButton><BookOpenIcon />Documentation</SidebarMenuButton>}/>
                </SidebarMenuItem>

                <SidebarMenuItem>
                    <SettingsDialog
                        trigger={<SidebarMenuButton><Settings2Icon />Settings</SidebarMenuButton>}
                    />
                </SidebarMenuItem>
            </SidebarMenu>


        </SidebarGroup>
    )
}
