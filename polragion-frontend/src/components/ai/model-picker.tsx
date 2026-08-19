import {BrainIcon, CheckIcon, ChevronsUpDownIcon, EyeIcon, Layers2, LockIcon} from "lucide-react"
import { useCallback, useEffect, useState } from "react"
import {AnswerDetail, AnswerDetailToJSON, type CopilotModel, type CopilotModelSelection} from "@/api"
import { gitHubModelsApi } from "@/api/client"
import {
  ModelSelector,
  ModelSelectorContent,
  ModelSelectorEmpty,
  ModelSelectorGroup,
  ModelSelectorInput,
  ModelSelectorItem,
  ModelSelectorList,
  ModelSelectorName,
  ModelSelectorTrigger,
} from "@/components/ai/model-selector"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { useGitHubAuth } from "@/hooks/use-github-auth"
import * as React from "react";

const CATEGORY_ORDER = ["powerful", "versatile", "lightweight"] as const

const CATEGORY_LABELS: Record<string, string> = {
  powerful: "Powerful",
  versatile: "Versatile",
  lightweight: "Lightweight",
}

const PRICE_LABELS: Record<string, string> = {
  low: "$",
  medium: "$$",
  high: "$$$",
  very_high: "$$$$",
}

const EFFORT_LABELS: Record<string, string> = {
  none: "None",
  minimal: "Minimal",
  low: "Low",
  medium: "Medium",
  high: "High",
  xhigh: "Extra high",
  max: "Max",
}

function formatTokens(tokens?: number | null) {
  if (!tokens) {
    return null
  }
  if (tokens >= 1_000_000) {
    return `${Number((tokens / 1_000_000).toFixed(1))}M`
  }
  if (tokens >= 1_000) {
    return `${Math.round(tokens / 1_000)}K`
  }
  return String(tokens)
}

function effortLabel(effort: string) {
  return EFFORT_LABELS[effort] ?? effort
}

function responseLengthLabel(responseLength: string) {
    switch (responseLength) {
      case "short":
        return "Short"
      case "standard":
        return "Standard"
      case "detailed":
        return "Detailed"
      default:
        // case "auto":
        return "Automatic"
    }
}

function isBlockedByPolicy(model: CopilotModel) {
  return model.policyState != null && model.policyState !== "enabled"
}

function groupLabel(model: CopilotModel) {
  if (model.isAuto) {
    return "Automatic"
  }
  return CATEGORY_LABELS[model.category ?? ""] ?? "Other"
}

/** Compact capability summary shown underneath the model name. */
function ModelSpecs({ model }: { model: CopilotModel }) {
  const context = formatTokens(model.maxContextTokens)
  const output = formatTokens(model.maxOutputTokens)

  const specs = [
    context ? `${context} context` : null,
    output ? `${output} output` : null,
  ].filter(Boolean)

  if (specs.length === 0) {
    return null
  }

  return <span className="text-xs text-muted-foreground">{specs.join(" · ")}</span>
}

export function ModelPicker() {
  const { isAuthenticated } = useGitHubAuth()
  const [open, setOpen] = useState(false)
  const [models, setModels] = useState<CopilotModel[]>([])
  const [selection, setSelection] = useState<CopilotModelSelection | null>(null)
  const [answerDetailSelection, setAnswerDetailSelection] = useState<AnswerDetail | null>(AnswerDetail.Auto)

  useEffect(() => {
    if (!isAuthenticated) {
      setModels([])
      setSelection(null)
      return
    }

    let cancelled = false

    void (async () => {
      try {
        const [available, current] = await Promise.all([
          gitHubModelsApi.getUserModels(),
          gitHubModelsApi.getModel().catch(() => null),
        ])
        if (cancelled) {
          return
        }
        setModels(available)
        setSelection(current ?? (available[0] ? { model: available[0] } : null))
      } catch {
        if (!cancelled) {
          setModels([])
        }
      }
    })()

    return () => {
      cancelled = true
    }
  }, [isAuthenticated])

  useEffect(() => {
    localStorage.setItem("answerDetailSelection", AnswerDetailToJSON(answerDetailSelection) ?? "");
  }, [answerDetailSelection]);

  const applySelection = useCallback(
    async (model: CopilotModel, reasoningEffort: string | null) => {

      let appliedReasoningEffort: string | undefined = reasoningEffort ?? undefined
      if (!appliedReasoningEffort) {
        appliedReasoningEffort = model.defaultReasoningEffort ?? undefined
      }
      if (!appliedReasoningEffort && model.supportedReasoningEfforts?.length) {
        const middleIndex = Math.floor((model.supportedReasoningEfforts.length - 1) / 2)
        appliedReasoningEffort = model.supportedReasoningEfforts[middleIndex] ?? undefined
      }

      // Optimistic update, the backend response is authoritative.
      setSelection({ model, reasoningEffort: appliedReasoningEffort })
      try {
        setSelection(
          await gitHubModelsApi.setUserModel({
            modelId: model.id,
            reasoningEffort: appliedReasoningEffort,
          }),
        )
      } catch {
        // Keep the optimistic value when the backend rejects it.
      }
    },
    [],
  )

  const selected = selection?.model
  const efforts = selected?.supportedReasoningEfforts ?? []
  const supportsEffort = Boolean(selected?.supportsReasoningEffort) && efforts.length > 0

  const categories = Array.from(new Set(models.map(groupLabel))).sort((a, b) => {
    const order = ["Automatic", ...CATEGORY_ORDER.map(key => CATEGORY_LABELS[key]), "Other"]
    return order.indexOf(a) - order.indexOf(b)
  })

  function CapabilityTooltip({label, children}: { label: React.ReactNode, children: React.ReactNode }) {
    return (
      <Tooltip>
        <TooltipTrigger
          render={
            <span className="inline-flex">
              {children}
            </span>
          }
        />
        <TooltipContent>{label}</TooltipContent>
      </Tooltip>
    )
  }

  return (
    <div className="flex items-center gap-2">

      <Select
        items={Object.values(AnswerDetail).map(detail => ({ label: responseLengthLabel(detail), value: detail }))}
        onValueChange={(value) => setAnswerDetailSelection(value as AnswerDetail)}
        value={answerDetailSelection ?? AnswerDetail.Auto}
      >
        <Tooltip>
          <TooltipTrigger
            render={
              <SelectTrigger aria-label="Reasoning effort" size="sm">
                <Layers2 className="size-3.5 text-muted-foreground" />
                <SelectValue />
              </SelectTrigger>
            }
          />
          <TooltipContent>Model response length</TooltipContent>
        </Tooltip>
        <SelectContent>
          {Object.values(AnswerDetail).map(detail => (
            <SelectItem key={detail} value={detail}>
              {responseLengthLabel(detail)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {supportsEffort && (
        <Select
          items={efforts.map(effort => ({ label: effortLabel(effort), value: effort }))}
          onValueChange={value => {
            if (selected && typeof value === "string") {
              void applySelection(selected, value)
            }
          }}
          value={
              selection?.reasoningEffort ??
              selected?.defaultReasoningEffort ??
              selected?.supportedReasoningEfforts?.at((selected?.supportedReasoningEfforts.length - 1) / 2)
              ?? null
          }
        >
          <Tooltip>
            <TooltipTrigger
              render={
                <SelectTrigger aria-label="Reasoning effort" size="sm">
                  <BrainIcon className="size-3.5 text-muted-foreground" />
                  <SelectValue />
                </SelectTrigger>
              }
            />
            <TooltipContent>Reasoning effort</TooltipContent>
          </Tooltip>
          <SelectContent align="end" alignItemWithTrigger={false} className="min-w-[9rem]">
            {efforts.map(effort => (
              <SelectItem key={effort} value={effort}>
                {effortLabel(effort)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      <ModelSelector onOpenChange={setOpen} open={open}>
        <ModelSelectorTrigger
          render={
            <Button
              className="w-[210px] justify-between"
              disabled={!isAuthenticated || models.length === 0}
              size="sm"
              variant="outline"
            />
          }
        >
          <ModelSelectorName>
            {selected?.name ??
              (isAuthenticated ? "No model available" : "Sign in to pick a model")}
          </ModelSelectorName>
          <ChevronsUpDownIcon className="size-4 opacity-50" />
        </ModelSelectorTrigger>
        <ModelSelectorContent className="sm:max-w-xl">
          <ModelSelectorInput placeholder="Search models..." />
          <ModelSelectorList className="max-h-[420px]">
            <ModelSelectorEmpty>No models found.</ModelSelectorEmpty>
            {categories.map(category => (
              <ModelSelectorGroup heading={category} key={category}>
                {models
                  .filter(model => groupLabel(model) === category)
                  .map(model => {
                    const blocked = isBlockedByPolicy(model)

                    return (
                      <ModelSelectorItem
                          className={`items-start gap-3 py-2 ${
                              blocked ? "cursor-not-allowed opacity-50" : ""
                          }`}
                        key={model.id}
                        onSelect={() => {
                          if (blocked) {
                            return
                          }
                          void applySelection(model, null)
                          setOpen(false)
                        }}
                        value={`${model.name} ${model.id}`}
                      >
                        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                          <div className="flex items-center gap-2">
                            <ModelSelectorName>{model.name}</ModelSelectorName>
                            {model.supportsVision && (
                                <CapabilityTooltip label={"Supports image input"}>
                                  <EyeIcon className="size-3.5 shrink-0 text-muted-foreground" />
                                </CapabilityTooltip>
                            )}
                            {model.supportsReasoningEffort && (
                                <CapabilityTooltip
                                    label={"Reasoning effort: " +
                                        (model.supportedReasoningEfforts ?? []).map(effortLabel).join(", ")}>
                                  <BrainIcon className="size-3.5 shrink-0 text-muted-foreground" />
                                </CapabilityTooltip>
                            )}
                            {blocked && (
                              <Tooltip>
                                <TooltipTrigger
                                  render={
                                    <LockIcon className="size-3.5 shrink-0 text-muted-foreground" />
                                  }
                                />
                                <TooltipContent>
                                  Blocked by your organization policy
                                </TooltipContent>
                              </Tooltip>
                            )}
                          </div>
                          <ModelSpecs model={model} />
                        </div>
                        <div className="min-w-13">
                        {model.priceCategory && (
                            <CapabilityTooltip label={"Relative cost: " + model.priceCategory.replace("_", " ")}>
                              <Badge className="shrink-0 font-mono" variant="secondary">
                                {PRICE_LABELS[model.priceCategory] ?? model.priceCategory}
                              </Badge>
                            </CapabilityTooltip>
                        )}
                        </div>

                        {selected?.id === model.id ? (
                          <CheckIcon className="size-4 shrink-0" />
                        ) : (
                          <div className="size-4 shrink-0" />
                        )}
                      </ModelSelectorItem>
                    )
                  })}
              </ModelSelectorGroup>
            ))}
          </ModelSelectorList>
        </ModelSelectorContent>
      </ModelSelector>
    </div>
  )
}
