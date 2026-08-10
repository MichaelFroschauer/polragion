// Project ids start with a letter, so plain ranges such as "[0:1]" are not treated as references.
const PROJECT_ID = "[A-Za-z][A-Za-z0-9_.\\-]*"
const WORK_ITEM_ID = "[A-Za-z0-9_.\\-]*[A-Za-z0-9][A-Za-z0-9_.\\-]*"
const REFERENCE = `${PROJECT_ID}:${WORK_ITEM_ID}`

const polarion_url = import.meta.env.VITE_POLARION_WEB_URL

// Matches a whole reference group such as [Proj:WI-1] or [Proj:WI-1, Proj:WI-2],
// but never a markdown link (which is followed by "(" or "[").
const REFERENCE_GROUP = new RegExp(
    `\\[\\s*${REFERENCE}(?:\\s*,\\s*${REFERENCE})*\\s*\\](?![([])`,
    "g",
)

// Fenced code blocks and inline code spans must stay untouched.
const CODE_SEGMENT = /```[\s\S]*?(?:```|$)|`[^`\n]*`/g

function escapeMarkdown(value: string) {
    return value.replace(/([\\[\]])/g, "\\$1")
}

function linkifyGroup(group: string) {
    const references = group
        .slice(1, -1)
        .split(",")
        .map(reference => reference.trim())

    const links = references.map(reference => {
        const separator = reference.indexOf(":")
        const projectId = reference.slice(0, separator)
        const workItemId = reference.slice(separator + 1)
        const url = getWorkItemUrl(projectId, workItemId)

        if (url === "#") {
            return escapeMarkdown(reference)
        }

        return `[${escapeMarkdown(workItemId)}](${url} "${projectId}:${workItemId}")`
    })

    return `\\[${links.join(", ")}\\]`
}

/**
 * Returns the URL for a given work item in Polarion.
 */
export function getWorkItemUrl(projectId: string, workItemId: string) {

    if (polarion_url === undefined) {
        return "#"
    }
    return `${polarion_url}/polarion/#/project/${projectId}/workitem?id=${workItemId}`
}

/**
 * Turns work item references produced by the AI model, e.g.
 * `[ProjectId:WorkItemId]` or `[ProjectId1:WorkItemId1, ProjectId2:WorkItemId2]`,
 * into Markdown links pointing at the corresponding Polarion work items.
 */
export function linkifyWorkItemReferences(text: string): string {
    if (!text) {
        return text
    }

    let result = ""
    let lastIndex = 0

    CODE_SEGMENT.lastIndex = 0
    for (let match = CODE_SEGMENT.exec(text); match; match = CODE_SEGMENT.exec(text)) {
        result += text.slice(lastIndex, match.index).replace(REFERENCE_GROUP, linkifyGroup)
        result += match[0]
        lastIndex = match.index + match[0].length
    }

    result += text.slice(lastIndex).replace(REFERENCE_GROUP, linkifyGroup)

    return result
}
