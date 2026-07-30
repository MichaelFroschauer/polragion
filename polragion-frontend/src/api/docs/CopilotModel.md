
# CopilotModel


## Properties

Name | Type
------------ | -------------
`id` | string
`name` | string
`category` | string
`priceCategory` | string
`maxContextTokens` | number
`maxPromptTokens` | number
`maxOutputTokens` | number
`supportsVision` | boolean
`supportsReasoningEffort` | boolean
`adaptiveThinking` | string
`defaultReasoningEffort` | string
`supportedReasoningEfforts` | Array&lt;string&gt;
`policyState` | string
`isAuto` | boolean

## Example

```typescript
import type { CopilotModel } from ''

// TODO: Update the object below with actual values
const example = {
  "id": null,
  "name": null,
  "category": null,
  "priceCategory": null,
  "maxContextTokens": null,
  "maxPromptTokens": null,
  "maxOutputTokens": null,
  "supportsVision": null,
  "supportsReasoningEffort": null,
  "adaptiveThinking": null,
  "defaultReasoningEffort": null,
  "supportedReasoningEfforts": null,
  "policyState": null,
  "isAuto": null,
} satisfies CopilotModel

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as CopilotModel
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


