# API Integration Specification (AIS)

This project utilizes a YAML-based configuration file to define the logic for integrating with external APIs. 
The configuration file specifies actions, responses, and performs, allowing for a flexible and reusable approach to API integration.
This convention promotes consistency and maintainability across different API integrations.

## Configuration Structure

[... previous content remains the same ...]

### Advanced Request Options

The API Integrator now supports advanced request handling with the following new capabilities:

#### Async Requests
You can now perform asynchronous HTTP requests by adding the `async: true` flag to your request configuration.

```yaml
performs:
  - perform:
      action: http.get
      data:
        path: '{{supplier_server.url}}/users'
        async: true  # Enable async request
```

#### Bulk Requests
Bulk requests allow you to send multiple requests concurrently using either threading or async methods.

```yaml
performs:
  - perform:
      action: http.post
      data:
        path: '{{supplier_server.url}}/users'
        type: bulk  # Enable bulk request
        async: true  # Optional: use async method (default is threading)
        wrapper: user  # Optional: wrap each item in a specific key
        body:
          - {name: "John Doe", job: "Developer"}
          - {name: "Jane Doe", job: "Designer"}
```

#### Request Configuration Options
- `async`: Enable asynchronous request processing
- `type: bulk`: Perform bulk requests
- `wrapper`: Wrap each item in a specific key for bulk requests
- `max_workers`: Control the number of concurrent threads (default: 10)

### Bulk Request Response Handling
After a bulk request, responses are stored in `vars.bulk_responses` for further processing.

```yaml
performs:
  - perform:
      action: http.post
      data:
        type: bulk
        # ... bulk request configuration
    responses:
      - is_success:
          code: 201
        performs:
          - perform:
              action: vars.set
              data:
                successful_users: '{{vars.bulk_responses}}'
```

### Performance and Concurrency

The API Integrator now supports:
- Asynchronous HTTP requests using `aiohttp`
- Threaded bulk requests using `ThreadPoolExecutor`
- Configurable maximum concurrent workers
- Fallback mechanisms between async and threaded requests

### Initialization Options

When creating an `ApiIntegrator`, you can specify the maximum number of workers:

```python
# Default is 10 workers
integrator = ApiIntegrator('config.yml', max_workers=20)
```

### Future Enhancements

[... previous future enhancements remain the same ...]

- **Advanced Concurrency Controls:** More granular control over request concurrency and retry mechanisms.
- **Enhanced Async Support:** More sophisticated async request handling and error management.
