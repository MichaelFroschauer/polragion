import {notificationsApi} from "@/api/client.ts";
import {toast} from "@/components/ui/toast.tsx";


export async function loadAndDisplayNotifications(shouldIgnore: () => boolean): Promise<void> {

    const { notifications } = await notificationsApi.getUserNotifications();
    if (shouldIgnore()) return;

    // TODO: Consider using a more robust storage mechanism (like IndexedDB) for larger datasets
    const storageKey = "hidden-notifications";
    const hiddenIds = new Set<string>(JSON.parse(localStorage.getItem(storageKey) ?? "[]"));

    for (const notification of notifications) {
        const notificationId = String(notification.id);

        // Skip notifications that have been hidden by the user
        if (hiddenIds.has(notificationId)) continue;

        const id = toast.add({
            title: notification.title,
            description: notification.description,
            timeout: 0,

            actionProps: {
                children: "Do not show again",
                onClick() {
                    hiddenIds.add(notificationId);

                    localStorage.setItem(
                        storageKey,
                        JSON.stringify([...hiddenIds])
                    );

                    toast.close(id);
                },
            },
        });
    }
}
