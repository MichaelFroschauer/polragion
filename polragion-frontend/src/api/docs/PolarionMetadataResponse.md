
# PolarionMetadataResponse


## Properties

Name | Type
------------ | -------------
`projectIds` | Array&lt;string&gt;
`projectContexts` | Array&lt;string&gt;
`projectCategories` | Array&lt;string&gt;
`projects` | [Array&lt;PolarionProjectMetadata&gt;](PolarionProjectMetadata.md)

## Example

```typescript
import type { PolarionMetadataResponse } from ''

// TODO: Update the object below with actual values
const example = {
  "projectIds": null,
  "projectContexts": null,
  "projectCategories": null,
  "projects": null,
} satisfies PolarionMetadataResponse

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as PolarionMetadataResponse
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


