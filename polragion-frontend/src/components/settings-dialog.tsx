"use client"

import {type ComponentProps, type ReactElement, useMemo, useState} from "react"
import {RotateCcwIcon, SearchIcon, SparklesIcon} from "lucide-react"

import {Button} from "@/components/ui/button.tsx"
import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog.tsx"
import {Tabs, TabsContent, TabsList, TabsTrigger} from "@/components/ui/tabs.tsx"
import {
    type AppSettings,
    DEFAULT_SETTINGS,
    SETTINGS_LIMITS,
    type SettingsFieldPath,
    useSettings,
    validateSettings,
} from "@/hooks/use-settings.tsx"
import {
    NumberSetting,
    SettingsSection,
    SliderSetting,
    TextareaSetting,
} from "@/components/settings/setting-fields.tsx"

type SettingsDialogProps = ComponentProps<typeof Dialog> & {
    /**
     * Element that opens the dialog. It is rendered *as* the trigger instead of
     * being nested inside one, so passing a button (e.g. SidebarMenuButton)
     * does not produce invalid nested-button markup.
     * Omit it to drive the dialog with `open` / `onOpenChange`.
     */
    trigger?: ReactElement
}

/**
 * Categories shown in the side navigation. To add one, add an entry here and
 * render a matching `<TabsContent value="...">` below.
 */
const CATEGORIES = [
    {
        id: "work-items",
        label: "Work Item Search",
        icon: SearchIcon,
        /** Prefixes of the setting paths belonging to this category. */
        paths: ["workItemSearch."],
    },
    {
        id: "ai",
        label: "AI Assistant",
        icon: SparklesIcon,
        paths: ["aiSearch.", "customUserSystemPrompt"],
    },
] as const

export function SettingsDialog({
    trigger,
    open: openProp,
    onOpenChange,
    ...props
}: SettingsDialogProps) {
    const {settings, replaceSettings} = useSettings()

    const [uncontrolledOpen, setUncontrolledOpen] = useState(false)
    const open = openProp ?? uncontrolledOpen

    /** Pending changes - they only reach the app once "Save changes" is pressed. */
    const [draft, setDraft] = useState<AppSettings>(settings)
    const [activeCategory, setActiveCategory] = useState<string>(CATEGORIES[0].id)

    // Every time the dialog opens, editing starts from the persisted settings,
    // so a previously cancelled draft is discarded.
    const [wasOpen, setWasOpen] = useState(open)
    if (open !== wasOpen) {
        setWasOpen(open)
        if (open) {
            setDraft(settings)
        }
    }

    const errors = useMemo(() => validateSettings(draft), [draft])
    const errorPaths = Object.keys(errors) as SettingsFieldPath[]
    const isValid = errorPaths.length === 0

    const isDirty = useMemo(
        () => JSON.stringify(draft) !== JSON.stringify(settings),
        [draft, settings],
    )
    const isDefault = useMemo(
        () => JSON.stringify(draft) === JSON.stringify(DEFAULT_SETTINGS),
        [draft],
    )

    const handleOpenChange: NonNullable<SettingsDialogProps["onOpenChange"]> = (
        nextOpen,
        eventDetails,
    ) => {
        if (openProp === undefined) {
            setUncontrolledOpen(nextOpen)
        }
        onOpenChange?.(nextOpen, eventDetails)
    }

    const setWorkItemSearch = (patch: Partial<AppSettings["workItemSearch"]>) =>
        setDraft((current) => ({...current, workItemSearch: {...current.workItemSearch, ...patch}}))

    const setAiSearch = (patch: Partial<AppSettings["aiSearch"]>) =>
        setDraft((current) => ({...current, aiSearch: {...current.aiSearch, ...patch}}))

    /** Persists the draft. Closing is handled by the surrounding `DialogClose`. */
    const handleSave = () => {
        const prompt = draft.customUserSystemPrompt?.trim()
        replaceSettings({...draft, customUserSystemPrompt: prompt ? prompt : undefined})
    }

    const limits = SETTINGS_LIMITS

    return (
        <Dialog onOpenChange={handleOpenChange} open={open} {...props}>
            {trigger && <DialogTrigger render={trigger}/>}
            <DialogContent className="gap-0 p-0 sm:max-w-3xl">
                <DialogHeader className="px-6 pt-6 pb-4">
                    <DialogTitle>Settings</DialogTitle>
                    <DialogDescription>
                        Adjust how Polragion searches and answers.
                    </DialogDescription>
                </DialogHeader>

                <Tabs
                    className="min-h-0 flex-1 gap-0 border-t"
                    onValueChange={(value) => setActiveCategory(String(value))}
                    orientation="vertical"
                    value={activeCategory}
                >
                    <TabsList
                        className="h-auto w-52 shrink-0 gap-1 rounded-none border-r bg-transparent p-3"
                        variant="line"
                    >
                        {CATEGORIES.map((category) => {
                            const Icon = category.icon
                            const hasError = errorPaths.some((path) =>
                                category.paths.some((prefix) => path.startsWith(prefix)),
                            )

                            return (
                                <TabsTrigger
                                    className="h-8 w-full justify-start gap-2 rounded-md px-2 data-active:bg-muted"
                                    key={category.id}
                                    value={category.id}
                                >
                                    <Icon/>
                                    <span className="truncate">{category.label}</span>
                                    {hasError && (
                                        <span
                                            aria-label="This section contains invalid values"
                                            className="ml-auto size-1.5 rounded-full bg-destructive"
                                        />
                                    )}
                                </TabsTrigger>
                            )
                        })}
                    </TabsList>

                    <div className="max-h-[60vh] min-h-[22rem] flex-1 overflow-y-auto px-6 py-5">
                        <TabsContent value="work-items">
                            <SettingsSection
                                title="Work Item Search"
                                description="Controls how work items are retrieved from the index."
                            >
                                <NumberSetting
                                    error={errors["workItemSearch.maxResults"]}
                                    hint="Upper bound of work items loaded per search. Higher values give more context but make the search slower."
                                    id="work-item-max-results"
                                    label="Maximum results"
                                    max={limits.workItemSearch.maxResults.max}
                                    min={limits.workItemSearch.maxResults.min}
                                    onChange={(maxResults) => setWorkItemSearch({maxResults})}
                                    step={limits.workItemSearch.maxResults.step}
                                    unit="items"
                                    value={draft.workItemSearch.maxResults}
                                />

                                <SliderSetting
                                    description=""
                                    error={errors["workItemSearch.minScore"]}
                                    format={(value) => value.toFixed(2)}
                                    hint="Only results with at least this similarity score are returned. 0.00 keeps every match, 1.00 only near-identical ones. A good starting point is around 0.30."
                                    id="work-item-min-score"
                                    label="Minimum search score"
                                    max={limits.workItemSearch.minScore.max}
                                    min={limits.workItemSearch.minScore.min}
                                    onChange={(minScore) =>
                                        setWorkItemSearch({minScore: Number(minScore.toFixed(2))})
                                    }
                                    step={limits.workItemSearch.minScore.step}
                                    value={draft.workItemSearch.minScore}
                                />
                            </SettingsSection>
                        </TabsContent>

                        <TabsContent value="ai">
                            <SettingsSection
                                title="AI Assistant"
                                description="Controls what the assistant receives and how it behaves."
                            >
                                <NumberSetting
                                    error={errors["aiSearch.maxResultsForAi"]}
                                    hint="How many of the found work items are passed to the model as context. Cannot exceed the work item result limit."
                                    id="ai-max-results"
                                    label="Results sent to the AI"
                                    max={limits.aiSearch.maxResultsForAi.max}
                                    min={limits.aiSearch.maxResultsForAi.min}
                                    onChange={(maxResultsForAi) => setAiSearch({maxResultsForAi})}
                                    step={limits.aiSearch.maxResultsForAi.step}
                                    unit="items"
                                    value={draft.aiSearch.maxResultsForAi}
                                />

                                <TextareaSetting
                                    description=""
                                    error={errors.customUserSystemPrompt}
                                    hint="Additional instructions that are appended to the built-in system prompt. Use it for tone, language or domain rules.'"
                                    id="custom-user-system-prompt"
                                    label="Custom system prompt"
                                    maxLength={limits.customUserSystemPrompt.maxLength}
                                    onChange={(customUserSystemPrompt) =>
                                        setDraft((current) => ({...current, customUserSystemPrompt}))
                                    }
                                    placeholder="e.g. Always answer in German and keep responses short."
                                    value={draft.customUserSystemPrompt ?? ""}
                                />
                            </SettingsSection>
                        </TabsContent>
                    </div>
                </Tabs>

                <DialogFooter className="mx-0 mb-0 items-center rounded-b-xl px-6 py-4 sm:justify-between">
                    <Button
                        className="sm:mr-auto"
                        disabled={isDefault}
                        onClick={() => setDraft(DEFAULT_SETTINGS)}
                        type="button"
                        variant="ghost"
                    >
                        <RotateCcwIcon/>
                        Restore defaults
                    </Button>

                    <div className="flex items-center justify-end gap-2">
                        {!isValid ? (
                            <span className="mr-1 text-destructive text-xs">
                                Please fix the highlighted fields.
                            </span>
                        ) : (
                            isDirty && (
                                <span className="mr-1 text-muted-foreground text-xs">Unsaved changes</span>
                            )
                        )}

                        <DialogClose render={<Button type="button" variant="outline"/>}>
                            Cancel
                        </DialogClose>

                        <DialogClose
                            render={
                                <Button
                                    disabled={!isValid || !isDirty}
                                    onClick={handleSave}
                                    type="button"
                                />
                            }
                        >
                            Save changes
                        </DialogClose>
                    </div>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
