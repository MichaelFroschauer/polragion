import { LogInIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useGitHubAuth } from "@/hooks/use-github-auth"

export function GitHubAuthButton() {
  const { user, isLoading, login } = useGitHubAuth()

  if (isLoading) {
    return <Skeleton className="h-8 w-28 rounded-md" />
  }

  if (!user) {
    return (
      <Button onClick={login} size="sm" variant="outline">
        <LogInIcon className="size-4" />
        Sign in with GitHub
      </Button>
    )
  }

  //const initials = (user.name ?? user.login).slice(0, 2).toUpperCase()

  return (<></>

      // <Avatar className="size-8">
      //   {user.avatarUrl && <AvatarImage alt={user.login} src={user.avatarUrl} />}
      //   <AvatarFallback>{initials}</AvatarFallback>
      // </Avatar>

    // <DropdownMenu>
    //   {/*<DropdownMenuTrigger render={<Button className="size-8 rounded-full p-0" variant="ghost" onClick={() => {}} />}>*/}
    //   <DropdownMenuTrigger>
    //
    //   </DropdownMenuTrigger>
    //   <DropdownMenuContent align="end" className="min-w-52">
    //     <DropdownMenuLabel className="grid gap-0.5">
    //       <span className="truncate font-medium">{user.name ?? user.login}</span>
    //       <span className="truncate text-xs font-normal text-muted-foreground">
    //         {user.email ?? `@${user.login}`}
    //       </span>
    //     </DropdownMenuLabel>
    //     <DropdownMenuSeparator />
    //     <DropdownMenuItem onClick={() => void logout()}>
    //       <LogOutIcon />
    //       Log out
    //     </DropdownMenuItem>
    //   </DropdownMenuContent>
    // </DropdownMenu>
  )
}
