
# McpTokenInfo


## Properties

Name | Type
------------ | -------------
`id` | string
`userId` | string
`name` | string
`createdAt` | Date
`expiresAt` | Date
`revokedAt` | Date

## Example

```typescript
import type { McpTokenInfo } from ''

// TODO: Update the object below with actual values
const example = {
  "id": null,
  "userId": null,
  "name": null,
  "createdAt": null,
  "expiresAt": null,
  "revokedAt": null,
} satisfies McpTokenInfo

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as McpTokenInfo
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


