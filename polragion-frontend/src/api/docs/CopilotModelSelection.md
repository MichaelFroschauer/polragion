
# CopilotModelSelection

The model a user has selected plus the reasoning effort applied to it.

## Properties

Name | Type
------------ | -------------
`model` | [CopilotModel](CopilotModel.md)
`reasoningEffort` | string

## Example

```typescript
import type { CopilotModelSelection } from ''

// TODO: Update the object below with actual values
const example = {
  "model": null,
  "reasoningEffort": null,
} satisfies CopilotModelSelection

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as CopilotModelSelection
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


