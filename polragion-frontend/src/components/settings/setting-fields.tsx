import {type ComponentProps, type ReactNode, useState} from "react"
import {InfoIcon} from "lucide-react"

import {cn} from "@/lib/utils.ts"
import {Input} from "@/components/ui/input.tsx"
import {Slider} from "@/components/ui/slider.tsx"
import {Switch} from "@/components/ui/switch.tsx"
import {Textarea} from "@/components/ui/textarea.tsx"
import {Tooltip, TooltipContent, TooltipTrigger} from "@/components/ui/tooltip.tsx"
import {
    Field,
    FieldContent,
    FieldDescription,
    FieldError,
    FieldGroup,
    FieldLabel,
} from "@/components/ui/field.tsx"

/**
 * Building blocks for the settings dialog.
 *
 * Every control follows the same contract: it is fully controlled through
 * `value` / `onChange` and reports its validation message through `error`.
 * Adding a new kind of setting means adding one more small component here.
 */

interface SettingsSectionProps {
    title: string
    description?: string
    children: ReactNode
}

export function SettingsSection({title, description, children}: SettingsSectionProps) {
    return (
        <section className="flex flex-col gap-5">
            <header className="flex flex-col gap-1">
                <h3 className="font-medium text-sm">{title}</h3>
                {description && (
                    <p className="text-muted-foreground text-xs">{description}</p>
                )}
            </header>
            <FieldGroup>{children}</FieldGroup>
        </section>
    )
}

function InfoHint({hint}: { hint: string }) {
    return (
        <Tooltip>
            <TooltipTrigger
                render={
                    <span
                        aria-label="More information"
                        className="inline-flex cursor-help text-muted-foreground transition-colors hover:text-foreground"
                        tabIndex={0}
                    />
                }
            >
                <InfoIcon className="size-3.5"/>
            </TooltipTrigger>
            <TooltipContent>{hint}</TooltipContent>
        </Tooltip>
    )
}

interface SettingRowProps {
    id: string
    label: string
    /** Short explanation rendered underneath the label. */
    description?: string
    /** Longer explanation shown in a tooltip next to the label. */
    hint?: string
    error?: string
    /** Right hand side of the row - the actual control. */
    children: ReactNode
    controlClassName?: string
}

export function SettingRow({
    id,
    label,
    description,
    hint,
    error,
    children,
    controlClassName,
}: SettingRowProps) {
    return (
        <Field data-invalid={Boolean(error)} orientation="responsive">
            <FieldContent>
                <FieldLabel htmlFor={id} className="font-normal">
                    {label}
                    {hint && <InfoHint hint={hint}/>}
                </FieldLabel>
                {description && <FieldDescription>{description}</FieldDescription>}
                <FieldError>{error}</FieldError>
            </FieldContent>
            <div className={cn("w-full shrink-0 @md/field-group:w-56!", controlClassName)}>
                {children}
            </div>
        </Field>
    )
}

type NumberSettingProps = Omit<SettingRowProps, "children" | "controlClassName"> & {
    value: number
    onChange: (value: number) => void
    min: number
    max: number
    step?: number
    unit?: string
}

/**
 * Numeric input. Keeps the raw text locally so intermediate states such as an
 * empty field stay editable, while reporting `NaN` upwards so validation can
 * flag it.
 */
export function NumberSetting({value, onChange, min, max, step, unit, ...row}: NumberSettingProps) {
    const [text, setText] = useState(() => (Number.isFinite(value) ? String(value) : ""))

    // Adopt values that changed from the outside (dialog reopened, defaults restored, ...)
    // without discarding what the user is currently typing.
    const [lastValue, setLastValue] = useState(value)
    if (!Object.is(value, lastValue)) {
        setLastValue(value)
        if (Number(text) !== value) {
            setText(Number.isFinite(value) ? String(value) : "")
        }
    }

    return (
        <SettingRow {...row}>
            <div className="relative">
                <Input
                    aria-invalid={Boolean(row.error)}
                    autoComplete="off"
                    className={cn(unit && "pr-12")}
                    id={row.id}
                    max={max}
                    min={min}
                    onChange={(event) => {
                        const next = event.target.value
                        setText(next)
                        onChange(next.trim() === "" ? Number.NaN : Number(next))
                    }}
                    step={step}
                    type="numeric"
                    value={text}
                />
                {unit && (
                    <span className="-translate-y-1/2 pointer-events-none absolute top-1/2 right-2.5 text-muted-foreground text-xs">
                        {unit}
                    </span>
                )}
            </div>
        </SettingRow>
    )
}

type SliderSettingProps = Omit<SettingRowProps, "children" | "controlClassName"> & {
    value: number
    onChange: (value: number) => void
    min: number
    max: number
    step?: number
    /** Formats the value shown next to the slider. */
    format?: (value: number) => string
}

export function SliderSetting({
    value,
    onChange,
    min,
    max,
    step = 1,
    format = (current) => String(current),
    ...row
}: SliderSettingProps) {
    const safeValue = Number.isFinite(value) ? Math.min(Math.max(value, min), max) : min

    return (
        <SettingRow {...row}>
            <div className="flex items-center gap-3">
                <Slider
                    className="flex-1"
                    id={row.id}
                    max={max}
                    min={min}
                    onValueChange={(next) => onChange(Array.isArray(next) ? next[0] : next)}
                    step={step}
                    value={[safeValue]}
                />
                <span className="w-8 shrink-0 text-right text-muted-foreground text-xs tabular-nums">
                    {format(safeValue)}
                </span>
            </div>
        </SettingRow>
    )
}

type SwitchSettingProps = Omit<SettingRowProps, "children" | "controlClassName"> & {
    checked: boolean
    onChange: (checked: boolean) => void
}

export function SwitchSetting({checked, onChange, ...row}: SwitchSettingProps) {
    return (
        <SettingRow controlClassName="@md/field-group:w-auto!" {...row}>
            <Switch checked={checked} id={row.id} onCheckedChange={(next) => onChange(next)} />
        </SettingRow>
    )
}

type TextareaSettingProps = Omit<SettingRowProps, "children" | "controlClassName"> & {
    value: string
    onChange: (value: string) => void
    maxLength: number
    placeholder?: string
    rows?: ComponentProps<typeof Textarea>["rows"]
}

export function TextareaSetting({
    value,
    onChange,
    maxLength,
    placeholder,
    rows = 5,
    ...row
}: TextareaSettingProps) {
    const remaining = maxLength - value.length

    return (
        <Field data-invalid={Boolean(row.error)}>
            <FieldLabel htmlFor={row.id} className="font-normal">
                {row.label}
                {row.hint && <InfoHint hint={row.hint}/>}
            </FieldLabel>
            {row.description && <FieldDescription>{row.description}</FieldDescription>}
            <Textarea
                aria-invalid={Boolean(row.error)}
                className="min-h-24 resize-none"
                id={row.id}
                onChange={(event) => onChange(event.target.value)}
                placeholder={placeholder}
                rows={rows}
                value={value}
            />
            <div className="flex items-start justify-between gap-4">
                <FieldError>{row.error}</FieldError>
                <span
                    className={cn(
                        "ml-auto shrink-0 text-muted-foreground text-xs tabular-nums",
                        remaining < 0 && "text-destructive",
                    )}
                >
                    {remaining} characters left
                </span>
            </div>
        </Field>
    )
}
