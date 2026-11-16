import assert from "node:assert/strict"
import {test} from "node:test"
import {buildRequestFilters, filterOptionId} from "../src/lib/search-filters.ts"

const metadata = {
    projectIds: ["A", "B"],
    projectContexts: ["vehicle", "safety"],
    projectCategories: ["system-requirement-specification", "software-requirement-specification", "product-test-specification"],
    projects: [
        {id: "A", contexts: ["vehicle"], documents: [{name: "Space/Shared", category: "system-specification"}]},
        {id: "B", contexts: ["safety"], documents: [{name: "Space/Shared", category: "software-specification"}]},
    ],
}

test("all selected omits all restrictions, including before metadata loads", () => {
    assert.deepEqual(JSON.parse(JSON.stringify(buildRequestFilters(metadata, new Set()))), {})
    assert.deepEqual(buildRequestFilters(null, new Set()), {})
})

test("partial and empty groups stay distinct from unrestricted", () => {
    const excluded = new Set([filterOptionId("project", "A"), filterOptionId("context", "vehicle"), filterOptionId("context", "safety")])
    const filters = buildRequestFilters(metadata, excluded)
    assert.deepEqual(filters.projectIds, ["B"])
    assert.deepEqual(filters.projectContexts, [])
    assert.equal(filters.documentCategories, undefined)
})

test("documents retain project identity and the entire path", () => {
    const filters = buildRequestFilters(metadata, new Set([filterOptionId("document", "A", "Space/Shared")]))
    assert.deepEqual(filters.documents, [{projectId: "B", documentName: "Space/Shared"}])
})

test("category labels are mapped back to every original backend category", () => {
    const filters = buildRequestFilters(metadata, new Set([filterOptionId("category", "Requirements")]))
    assert.deepEqual(filters.documentCategories, ["product-test-specification"])
    assert.deepEqual(buildRequestFilters(metadata, new Set([filterOptionId("category", "Tests")] )).documentCategories,
        ["system-requirement-specification", "software-requirement-specification"])
})

test("a submitted snapshot does not change when the selection changes", () => {
    const excluded = new Set([filterOptionId("project", "A")])
    const snapshot = buildRequestFilters(metadata, excluded)
    excluded.clear()
    assert.deepEqual(snapshot.projectIds, ["B"])
    assert.equal(buildRequestFilters(metadata, excluded).projectIds, undefined)
})
