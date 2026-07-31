# WorkItemsApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**askWorkItem**](WorkItemsApi.md#askworkitem) | **POST** /v1/work-items/ask | Ask Work Item |
| [**getChatHistory**](WorkItemsApi.md#getchathistory) | **GET** /v1/work-items/ask/history | Get Chat History |
| [**ingestWorkItems**](WorkItemsApi.md#ingestworkitems) | **POST** /v1/work-items/ingest | Ingest Work Items |
| [**ingestWorkItemsFromDataSource**](WorkItemsApi.md#ingestworkitemsfromdatasource) | **POST** /v1/work-items/ingest/import-json | Ingest Work Items From Data Source |
| [**resetUserSession**](WorkItemsApi.md#resetusersession) | **GET** /v1/work-items/reset | Reset User Session |
| [**searchWorkItems**](WorkItemsApi.md#searchworkitems) | **GET** /v1/work-items/search | Search Work Items |



## askWorkItem

> WorkItemAskResponse askWorkItem(prompt, projectId, limit, scoreThreshold)

Ask Work Item

### Example

```ts
import {
  Configuration,
  WorkItemsApi,
} from '';
import type { AskWorkItemRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new WorkItemsApi();

  const body = {
    // string
    prompt: prompt_example,
    // string (optional)
    projectId: projectId_example,
    // number (optional)
    limit: 56,
    // number (optional)
    scoreThreshold: 8.14,
  } satisfies AskWorkItemRequest;

  try {
    const data = await api.askWorkItem(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **prompt** | `string` |  | [Defaults to `undefined`] |
| **projectId** | `string` |  | [Optional] [Defaults to `undefined`] |
| **limit** | `number` |  | [Optional] [Defaults to `undefined`] |
| **scoreThreshold** | `number` |  | [Optional] [Defaults to `undefined`] |

### Return type

[**WorkItemAskResponse**](WorkItemAskResponse.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getChatHistory

> Array&lt;ChatHistoryMessage&gt; getChatHistory()

Get Chat History

### Example

```ts
import {
  Configuration,
  WorkItemsApi,
} from '';
import type { GetChatHistoryRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new WorkItemsApi();

  try {
    const data = await api.getChatHistory();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**Array&lt;ChatHistoryMessage&gt;**](ChatHistoryMessage.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## ingestWorkItems

> IngestResponse ingestWorkItems(polarionWorkItem)

Ingest Work Items

### Example

```ts
import {
  Configuration,
  WorkItemsApi,
} from '';
import type { IngestWorkItemsRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new WorkItemsApi();

  const body = {
    // Array<PolarionWorkItem>
    polarionWorkItem: ...,
  } satisfies IngestWorkItemsRequest;

  try {
    const data = await api.ingestWorkItems(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **polarionWorkItem** | `Array<PolarionWorkItem>` |  | |

### Return type

[**IngestResponse**](IngestResponse.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## ingestWorkItemsFromDataSource

> IngestResponse ingestWorkItemsFromDataSource(limit)

Ingest Work Items From Data Source

### Example

```ts
import {
  Configuration,
  WorkItemsApi,
} from '';
import type { IngestWorkItemsFromDataSourceRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new WorkItemsApi();

  const body = {
    // number (optional)
    limit: 56,
  } satisfies IngestWorkItemsFromDataSourceRequest;

  try {
    const data = await api.ingestWorkItemsFromDataSource(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **limit** | `number` |  | [Optional] [Defaults to `undefined`] |

### Return type

[**IngestResponse**](IngestResponse.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## resetUserSession

> any resetUserSession()

Reset User Session

### Example

```ts
import {
  Configuration,
  WorkItemsApi,
} from '';
import type { ResetUserSessionRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new WorkItemsApi();

  try {
    const data = await api.resetUserSession();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

**any**

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## searchWorkItems

> WorkItemSearchResponse searchWorkItems(prompt, projectId, limit, scoreThreshold)

Search Work Items

### Example

```ts
import {
  Configuration,
  WorkItemsApi,
} from '';
import type { SearchWorkItemsRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new WorkItemsApi();

  const body = {
    // string
    prompt: prompt_example,
    // string (optional)
    projectId: projectId_example,
    // number (optional)
    limit: 56,
    // number (optional)
    scoreThreshold: 8.14,
  } satisfies SearchWorkItemsRequest;

  try {
    const data = await api.searchWorkItems(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **prompt** | `string` |  | [Defaults to `undefined`] |
| **projectId** | `string` |  | [Optional] [Defaults to `undefined`] |
| **limit** | `number` |  | [Optional] [Defaults to `undefined`] |
| **scoreThreshold** | `number` |  | [Optional] [Defaults to `undefined`] |

### Return type

[**WorkItemSearchResponse**](WorkItemSearchResponse.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

