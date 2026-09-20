
# PolarionWorkItem

Validated domain representation of a Polarion work item.

## Properties

Name | Type
------------ | -------------
`projectId` | string
`projectName` | string
`projectContext` | Array&lt;string&gt;
`workItemId` | string
`workItemType` | string
`documentName` | string
`documentCategory` | string
`title` | string
`description` | string
`revision` | number
`status` | string
`location` | string
`linkedWorkItems` | [Array&lt;LinkedWorkItem&gt;](LinkedWorkItem.md)
`additionalFields` | { [key: string]: any; }

## Example

```typescript
import type { PolarionWorkItem } from ''

// TODO: Update the object below with actual values
const example = {
  "projectId": null,
  "projectName": null,
  "projectContext": null,
  "workItemId": null,
  "workItemType": null,
  "documentName": null,
  "documentCategory": null,
  "title": null,
  "description": null,
  "revision": null,
  "status": null,
  "location": null,
  "linkedWorkItems": null,
  "additionalFields": null,
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


