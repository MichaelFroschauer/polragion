import { CheckIcon, ChevronsUpDownIcon } from "lucide-react"
import { useEffect, useState } from "react"
import { gitHubModelsApi } from "@/api/client"
import {
  ModelSelector,
  ModelSelectorContent,
  ModelSelectorEmpty,
  ModelSelectorGroup,
  ModelSelectorInput,
  ModelSelectorItem,
  ModelSelectorList,
  ModelSelectorLogo,
  ModelSelectorName,
  ModelSelectorTrigger,
} from "@/components/ai/model-selector"
import { Button } from "@/components/ui/button"
import { useGitHubAuth } from "@/hooks/use-github-auth"
import type {CopilotModel} from "@/api";

const providerSlug = (publisher: string) => publisher.toLowerCase().replace(/\s+/g, "-")

export function ModelPicker() {
  const { isAuthenticated } = useGitHubAuth()
  const [open, setOpen] = useState(false)
  const [models, setModels] = useState<CopilotModel[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated) {
      setModels([])
      setSelectedId(null)
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
        setSelectedId(current?.id ?? available[0]?.id ?? null)
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

  const selected = models.find(model => model.id === selectedId)
  // const publishers = Array.from(new Set(models.map(model => model.publisher)))
  const publishers = Array.from(new Set(models.map(model => model.name)))

  const selectModel = async (model: CopilotModel) => {
    setSelectedId(model.id)
    setOpen(false)
    try {
      await gitHubModelsApi.setUserModel({ modelId: model.id })
    } catch {
      // Selection stays local when the backend rejects it.
    }
  }

  return (
    <ModelSelector onOpenChange={setOpen} open={open}>
      <ModelSelectorTrigger
        render={
          <Button
            className="w-[200px] justify-between"
            disabled={!isAuthenticated || models.length === 0}
            size="sm"
            variant="outline"
          />
        }
      >
        {selected ? (
          <>
            {/*<ModelSelectorLogo provider={providerSlug(selected.publisher)} />*/}
            <ModelSelectorLogo provider="github-copilot" />
            <ModelSelectorName>{selected.name}</ModelSelectorName>
          </>
        ) : (
          <ModelSelectorName>
            {isAuthenticated ? "No model available" : "Sign in to pick a model"}
          </ModelSelectorName>
        )}
        <ChevronsUpDownIcon className="size-4 opacity-50" />
      </ModelSelectorTrigger>
      <ModelSelectorContent>
        <ModelSelectorInput placeholder="Search models..." />
        <ModelSelectorList>
          <ModelSelectorEmpty>No models found.</ModelSelectorEmpty>
          {publishers.map(publisher => (
            <ModelSelectorGroup heading={publisher} key={publisher}>
              {models
                //.filter(model => model.publisher === publisher)
                .map(model => (
                  <ModelSelectorItem
                    key={model.id}
                    onSelect={() => void selectModel(model)}
                    value={model.id}
                  >
                    {/*<ModelSelectorLogo provider={providerSlug(model.name)} />*/}
                    {/*<ModelSelectorLogo provider="github-copilot" />*/}
                    <ModelSelectorLogo provider={model.name} />
                    <ModelSelectorName>{model.name}</ModelSelectorName>
                    {selectedId === model.id ? (
                      <CheckIcon className="ml-auto size-4" />
                    ) : (
                      <div className="ml-auto size-4" />
                    )}
                  </ModelSelectorItem>
                ))}
            </ModelSelectorGroup>
          ))}
        </ModelSelectorList>
      </ModelSelectorContent>
    </ModelSelector>
  )
}
