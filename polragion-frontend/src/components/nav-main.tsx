import {
    SidebarGroup,
    SidebarGroupLabel,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from "@/components/ui/sidebar.tsx"
import {BookOpenIcon, Info, Settings2Icon, SquarePen} from "lucide-react"
import {
    AlertDialog, AlertDialogAction, AlertDialogContent,
    AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger
} from "@/components/ui/alert-dialog.tsx";
import {useState} from "react";
import {useChat} from "@/hooks/use-chat.tsx";


export function NavMain() {
    const [open, setOpen] = useState(false)
    const { resetSession: newChat } = useChat()

    return (
        <SidebarGroup>
            <SidebarGroupLabel>Platform</SidebarGroupLabel>

            <SidebarMenu>
                <SidebarMenuItem>
                    <SidebarMenuButton onClick={newChat}><SquarePen />New chat</SidebarMenuButton>
                </SidebarMenuItem>

                <SidebarMenuItem>
                    <SidebarMenuButton onClick={() => setOpen(true)}><BookOpenIcon />Documentation</SidebarMenuButton>
                </SidebarMenuItem>

                <SidebarMenuItem>
                    <SidebarMenuButton onClick={() => setOpen(true)}><Settings2Icon />Settings</SidebarMenuButton>
                </SidebarMenuItem>
            </SidebarMenu>

            <AlertDialog open={open} onOpenChange={setOpen}>
                <AlertDialogTrigger>
                </AlertDialogTrigger>

                <AlertDialogContent>
                    <AlertDialogHeader>
                        <div className="flex items-center gap-2">
                            <Info className="size-5 text-blue-500" />
                            <AlertDialogTitle>Work in Progress...</AlertDialogTitle>
                        </div>
                        <AlertDialogDescription>
                            This action is currently unfinished and will be available in a future release.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogAction onClick={() => setOpen(false)}>Ok</AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </SidebarGroup>
    )
}
