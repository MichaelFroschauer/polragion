import type {PolarionMetadataResponse, WorkItemFilters} from "@/api"

export function filterOptionId(kind: string, ...values: string[]): string {
    return JSON.stringify([kind, ...values])
}

export function formatCategoryName(category: string): string {
    const cleaned = category.replace(/-specification|system-|product-|software-/g, "")
    return (cleaned.charAt(0).toUpperCase() + cleaned.slice(1)) + "s"
}

// Omit fully selected groups: the default includes work items without configured metadata too.
export function buildRequestFilters(metadata: PolarionMetadataResponse | null, excluded: ReadonlySet<string>): WorkItemFilters {
    if (!metadata) return {}
    function selected<T>(values: T[], id: (value: T) => string): T[] | undefined {
        return values.some(value => excluded.has(id(value)))
            ? values.filter(value => !excluded.has(id(value)))
            : undefined
    }
    const documents = metadata.projects.flatMap(project => project.documents.map(document => ({
        projectId: project.id, documentName: document.name,
    })))
    return {
        projectIds: selected(metadata.projectIds, value => filterOptionId("project", value)),
        projectContexts: selected(metadata.projectContexts, value => filterOptionId("context", value)),
        documentCategories: selected(metadata.projectCategories, value => filterOptionId("category", formatCategoryName(value))),
        documents: selected(documents, value => filterOptionId("document", value.projectId, value.documentName)),
    }
}
