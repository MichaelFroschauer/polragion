import type {ReactElement} from "react"
import {BookOpenIcon} from "lucide-react"
import {
    AlertDialog, AlertDialogCancel, AlertDialogContent, AlertDialogDescription,
    AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog"

/** Shared entry point until the dedicated documentation area is available. */
export function DocumentationDialog({trigger}: {trigger: ReactElement}) {
    return <AlertDialog>
        <AlertDialogTrigger render={trigger}/>
        <AlertDialogContent>
            <AlertDialogHeader>
                <AlertDialogTitle className="flex items-center gap-2"><BookOpenIcon/>Documentation</AlertDialogTitle>
                <AlertDialogDescription>
                    The documentation area is being prepared. For now, the MCP Server tab in Settings contains the client configuration examples.
                </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter><AlertDialogCancel variant="default">Close</AlertDialogCancel></AlertDialogFooter>
        </AlertDialogContent>
    </AlertDialog>
}
