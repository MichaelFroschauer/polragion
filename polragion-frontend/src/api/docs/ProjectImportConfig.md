
# ProjectImportConfig


## Properties

Name | Type
------------ | -------------
`projectId` | string
`enabled` | boolean
`description` | string
`projectContext` | Array&lt;string&gt;
`documents` | [Array&lt;ProjectDocument&gt;](ProjectDocument.md)
`workItems` | [WorkItemImportConfig](WorkItemImportConfig.md)

## Example

```typescript
import type { ProjectImportConfig } from ''

// TODO: Update the object below with actual values
const example = {
  "projectId": null,
  "enabled": null,
  "description": null,
  "projectContext": null,
  "documents": null,
  "workItems": null,
} satisfies ProjectImportConfig

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as ProjectImportConfig
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


