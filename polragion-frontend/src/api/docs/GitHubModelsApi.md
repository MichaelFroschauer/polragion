# GitHubModelsApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**getModel**](GitHubModelsApi.md#getmodel) | **GET** /ai/github/model | Get Model |
| [**getUserModels**](GitHubModelsApi.md#getusermodels) | **GET** /ai/github/models | Get User Models |
| [**setUserModel**](GitHubModelsApi.md#setusermodel) | **PUT** /ai/github/model | Set User Model |



## getModel

> CopilotModelSelection getModel()

Get Model

### Example

```ts
import {
  Configuration,
  GitHubModelsApi,
} from '';
import type { GetModelRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new GitHubModelsApi();

  try {
    const data = await api.getModel();
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

[**CopilotModelSelection**](CopilotModelSelection.md)

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


## getUserModels

> Array&lt;CopilotModel&gt; getUserModels()

Get User Models

### Example

```ts
import {
  Configuration,
  GitHubModelsApi,
} from '';
import type { GetUserModelsRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new GitHubModelsApi();

  try {
    const data = await api.getUserModels();
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

[**Array&lt;CopilotModel&gt;**](CopilotModel.md)

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


## setUserModel

> CopilotModelSelection setUserModel(modelId, reasoningEffort)

Set User Model

### Example

```ts
import {
  Configuration,
  GitHubModelsApi,
} from '';
import type { SetUserModelRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new GitHubModelsApi();

  const body = {
    // string
    modelId: modelId_example,
    // string (optional)
    reasoningEffort: reasoningEffort_example,
  } satisfies SetUserModelRequest;

  try {
    const data = await api.setUserModel(body);
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
| **modelId** | `string` |  | [Defaults to `undefined`] |
| **reasoningEffort** | `string` |  | [Optional] [Defaults to `undefined`] |

### Return type

[**CopilotModelSelection**](CopilotModelSelection.md)

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

