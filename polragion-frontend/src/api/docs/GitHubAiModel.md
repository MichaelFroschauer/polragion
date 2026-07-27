
# GitHubAiModel


## Properties

Name | Type
------------ | -------------
`id` | string
`name` | string
`publisher` | string
`registry` | string
`summary` | string
`htmlUrl` | string
`version` | string
`rateLimitTier` | string
`capabilities` | Array&lt;string&gt;
`supportedInputModalities` | Array&lt;string&gt;
`supportedOutputModalities` | Array&lt;string&gt;
`tags` | Array&lt;string&gt;

## Example

```typescript
import type { GitHubAiModel } from ''

// TODO: Update the object below with actual values
const example = {
  "id": null,
  "name": null,
  "publisher": null,
  "registry": null,
  "summary": null,
  "htmlUrl": null,
  "version": null,
  "rateLimitTier": null,
  "capabilities": null,
  "supportedInputModalities": null,
  "supportedOutputModalities": null,
  "tags": null,
} satisfies GitHubAiModel

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as GitHubAiModel
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


