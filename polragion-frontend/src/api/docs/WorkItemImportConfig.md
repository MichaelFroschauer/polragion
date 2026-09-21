
# WorkItemImportConfig


## Properties

Name | Type
------------ | -------------
`query` | string
`commonFields` | Array&lt;string&gt;
`fieldsByType` | { [key: string]: Array&lt;string&gt;; }
`relations` | [RelationsConfig](RelationsConfig.md)

## Example

```typescript
import type { WorkItemImportConfig } from ''

// TODO: Update the object below with actual values
const example = {
  "query": null,
  "commonFields": null,
  "fieldsByType": null,
  "relations": null,
} satisfies WorkItemImportConfig

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as WorkItemImportConfig
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


