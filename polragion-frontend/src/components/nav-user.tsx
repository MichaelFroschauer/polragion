"use client"

import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar.tsx"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu.tsx"
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar.tsx"
import {
  ChevronsUpDownIcon,
  LogOutIcon,
  LogInIcon, SquarePen, ArrowLeftRight
} from "lucide-react"
import {useGitHubAuth} from "@/hooks/use-github-auth.tsx";
import {Skeleton} from "@/components/ui/skeleton.tsx";

export function NavUser() {
  const { isMobile } = useSidebar()

  const { user, isLoading, login, logout, switchAccount } = useGitHubAuth()

  if (isLoading) {
    return <Skeleton className="h-8 w-28 rounded-md" />
  }

  if (!user) {
    return (
        // <Button onClick={login} size="sm" variant="outline">
        //   <LogInIcon className="size-4" />
        //   Sign in with GitHub
        // </Button>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton onClick={login} size="lg" className="aria-expanded:bg-muted"><LogInIcon className="size-4" />Sign in with GitHub</SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
    )
  }

  const initials = user.username.slice(0, 2).toUpperCase()

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <SidebarMenuButton size="lg" className="aria-expanded:bg-muted" />
            }
          >
            <Avatar className="size-8">
              {user.avatarUrl && <AvatarImage alt={user.username} src={user.avatarUrl} />}
              <AvatarFallback>{initials}</AvatarFallback>
            </Avatar>
            <div className="grid flex-1 text-left text-sm leading-tight">
              <span className="truncate font-medium">{user.username}</span>
              {/*<span className="truncate text-xs">{user.email}</span>*/}
            </div>
            <ChevronsUpDownIcon className="ml-auto size-4" />
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="min-w-56 rounded-lg"
            side={isMobile ? "bottom" : "right"}
            align="end"
            sideOffset={4}
          >
            <DropdownMenuGroup>
              <DropdownMenuLabel className="p-0 font-normal">
                <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                  <Avatar className="size-8">
                    {user.avatarUrl && <AvatarImage alt={user.username} src={user.avatarUrl} />}
                    <AvatarFallback>{initials}</AvatarFallback>
                  </Avatar>

                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-medium">{user.username}</span>
                    {/*<span className="truncate text-xs">{user.email}</span>*/}
                  </div>
                </div>
              </DropdownMenuLabel>
            </DropdownMenuGroup>
            {/*<DropdownMenuSeparator />*/}
            {/*<DropdownMenuGroup>*/}
            {/*  <DropdownMenuItem>*/}
            {/*    <SparklesIcon*/}
            {/*    />*/}
            {/*    Upgrade to Pro*/}
            {/*  </DropdownMenuItem>*/}
            {/*</DropdownMenuGroup>*/}
            {/*<DropdownMenuSeparator />*/}
            {/*<DropdownMenuGroup>*/}
            {/*  <DropdownMenuItem>*/}
            {/*    <BadgeCheckIcon*/}
            {/*    />*/}
            {/*    Account*/}
            {/*  </DropdownMenuItem>*/}
            {/*  <DropdownMenuItem>*/}
            {/*    <CreditCardIcon*/}
            {/*    />*/}
            {/*    Billing*/}
            {/*  </DropdownMenuItem>*/}
            {/*  <DropdownMenuItem>*/}
            {/*    <BellIcon*/}
            {/*    />*/}
            {/*    Notifications*/}
            {/*  </DropdownMenuItem>*/}
            {/*</DropdownMenuGroup>*/}
            <DropdownMenuItem>
              <SquarePen />
              New chat
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={switchAccount}>
              <ArrowLeftRight />
              Switch account
            </DropdownMenuItem>
            <DropdownMenuItem onClick={logout}>
              <LogOutIcon />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
