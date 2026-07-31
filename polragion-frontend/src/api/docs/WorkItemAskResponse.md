
# WorkItemAskResponse


## Properties

Name | Type
------------ | -------------
`answer` | string
`tokensSpent` | number
`workItems` | [Array&lt;WorkItemSearchHit&gt;](WorkItemSearchHit.md)

## Example

```typescript
import type { WorkItemAskResponse } from ''

// TODO: Update the object below with actual values
const example = {
  "answer": null,
  "tokensSpent": null,
  "workItems": null,
} satisfies WorkItemAskResponse

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as WorkItemAskResponse
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


