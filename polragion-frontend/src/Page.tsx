import type { ReactNode } from "react"
import { AppSidebar } from "@/components/app-sidebar"
import { GitHubAuthButton } from "@/components/ai/github-auth-button"
import { ModelPicker } from "@/components/ai/model-picker"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"

interface PageProps {
    children: ReactNode
}

export default function Page({ children }: PageProps) {
    return (
        <SidebarProvider className="h-svh overflow-hidden">
            <AppSidebar />
            <SidebarInset className="min-h-0 overflow-hidden">
                <header className="flex h-14 shrink-0 items-center gap-2 px-4">
                    <SidebarTrigger className="-ml-1" />

                    <div className="ml-auto flex items-center gap-2">
                        <GitHubAuthButton />
                        <ModelPicker />
                    </div>
                </header>

                {children}
            </SidebarInset>
        </SidebarProvider>
    )
}
