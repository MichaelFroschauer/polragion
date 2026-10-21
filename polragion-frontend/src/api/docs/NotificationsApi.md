# NotificationsApi

All URIs are relative to *https://localhost:8000/api*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**getUserNotifications**](NotificationsApi.md#getusernotifications) | **GET** /v1/notifications | Get User Notifications |



## getUserNotifications

> UserNotificationsResponse getUserNotifications()

Get User Notifications

### Example

```ts
import {
  Configuration,
  NotificationsApi,
} from '';
import type { GetUserNotificationsRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new NotificationsApi();

  try {
    const data = await api.getUserNotifications();
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

[**UserNotificationsResponse**](UserNotificationsResponse.md)

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

