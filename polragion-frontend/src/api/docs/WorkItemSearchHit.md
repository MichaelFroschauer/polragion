
# WorkItemSearchHit


## Properties

Name | Type
------------ | -------------
`workItem` | [PolarionWorkItem](PolarionWorkItem.md)
`score` | number
`pointId` | string

## Example

```typescript
import type { WorkItemSearchHit } from ''

// TODO: Update the object below with actual values
const example = {
  "workItem": null,
  "score": null,
  "pointId": null,
} satisfies WorkItemSearchHit

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as WorkItemSearchHit
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


