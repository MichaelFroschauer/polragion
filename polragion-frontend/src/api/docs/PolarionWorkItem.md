
# PolarionWorkItem

Validated domain representation of a Polarion work item.

## Properties

Name | Type
------------ | -------------
`projectId` | string
`workitemId` | string
`title` | string
`text` | string
`revision` | number
`status` | string
`linkedWorkitems` | [Array&lt;LinkedWorkItem&gt;](LinkedWorkItem.md)
`customFields` | [CustomFields](CustomFields.md)

## Example

```typescript
import type { PolarionWorkItem } from ''

// TODO: Update the object below with actual values
const example = {
  "projectId": null,
  "workitemId": null,
  "title": null,
  "text": null,
  "revision": null,
  "status": null,
  "linkedWorkitems": null,
  "customFields": null,
} satisfies PolarionWorkItem

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as PolarionWorkItem
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


