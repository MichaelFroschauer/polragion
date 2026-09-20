
# PolarionProjectMetadata


## Properties

Name | Type
------------ | -------------
`id` | string
`contexts` | Array&lt;string&gt;
`documents` | [Array&lt;PolarionDocumentMetadata&gt;](PolarionDocumentMetadata.md)

## Example

```typescript
import type { PolarionProjectMetadata } from ''

// TODO: Update the object below with actual values
const example = {
  "id": null,
  "contexts": null,
  "documents": null,
} satisfies PolarionProjectMetadata

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as PolarionProjectMetadata
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


