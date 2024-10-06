# API Integration Convention

This project utilizes a YAML-based configuration file to define the logic for integrating with external APIs. 
The configuration file specifies actions, responses, and performs, allowing for a flexible and reusable approach to API integration.
This convention promotes consistency and maintainability across different API integrations.

## Configuration Structure

### `api_integrator`
- **Version**: Specifies the version of the API integrator.

### `info`
- **title**: Title of the configuration.
- **version**: Version of the configuration.
- **description**: Description of the configuration.
- **contact**: Contact information for support.
- **lang**: Expected language in expressions like in log messages (e.g., python, javascript, etc.).

### `supplier_servers`
- **id**: Identifier for the server.
- **url**: URL of the server.
- **description**: Description of the server.

### `tags`
- **name**: Name of the tag.
- **description**: Description of the tag.

### `actions`
- **name**: Name of the action.
- **tags**: Tags associated with the action.
- **description**: Description of the action.
- **performs**: List of actions to perform.
  - **perform**: Commands to be performed.
    - **a**: The action to perform (e.g., `http.get`, `log.info`, `vars.set`, etc.).
    - **data**: Data required by the action to be performed.
  - **responses**: After an action is performed, a response is expected. Responses is a list of responses to handle.
    - **is_success**: Conditions for successful responses.
      - code: The expected HTTP status code for success.
    - **is_error**: Conditions for error responses.
      - code: The HTTP status code indicating an error.
    - **performs**: List of actions to perform based on the response.

### `response` object
- The response object is used to retrieve information about the response.
- It can be called in any part after a response is received.
- The general structure is:
  - response.{property}
  - where property follows the response structure (e.g., body, status_code, etc.).

### `perform commands`
- They are basic commands that can be performed by actions.
- They are used to perform actions like `http.{verb}`, `log.{level}`, `vars.set`, etc.
- They are executed by the implementation of the API integrator.
- Key commands include:
  - http.{verb}: Performs an HTTP request (e.g., http.get, http.post).
  - log.{level}: Logs a message at the specified level.
  - vars.set: Sets a variable in the vars section.

### `vars`
- Global variables that can be accessed by actions and overridden with parameters fed to actions.

### `constants`
- Global constants that can be accessed by actions, not overridable.

## Example Configuration

```yaml
api_integrator: 0.0.1
info:
  title: JSONPlaceholder Users API Integration
  version: 1.0.0
  description: Configuration for integrating with JSONPlaceholder Users API
  contact:
    name: Developer
    url: https://jsonplaceholder.typicode.com
    email: support@example.com
  lang: python
supplier_servers:
  - id: prod
    url: https://jsonplaceholder.typicode.com
    description: JSONPlaceholder production server
tags:
  - name: users
    description: Endpoints to manage users
actions:
  get_all_users:
    tags:
      - users
    description: Get all users
    performs:
      - perform:
          a: http.get
          data:
            path: '{{supplier_server.url}}/users'
        responses:
          - is_success:
              code: 200
            performs:
              - perform:
                  a: log.info
                  data: 'Successfully retrieved all users'
              - perform:
                  a: vars.set
                  data:
                    all_users: '{{response.body}}'
          - is_error:
              code: 400
            performs:
              - perform:
                  a: log.error
                  data: 'Error retrieving users: {{response.body}}'

vars:
  supplier_server:
    id: prod
  user_id: 1

constants:
  retry_trials: 3
```

## Generating API Integrator Configuration

This project now includes a feature to generate the API integrator configuration file from an OpenAPI specification. The generation process supports custom templates, custom output file names, and the ability to specify the input file path.

### Usage

To generate an API integrator configuration, use the following command:

```
python src/main.py --input-file /path/to/openapi_spec.yaml --template-file /path/to/api_integrator_template.yaml --output-file custom_config.yaml
```

- `--input-file`: Path to the OpenAPI specification file (required)
- `--template-file`: Path to the API Integrator configuration template file (optional, default template will be used if not specified)
- `--output-file`: Name of the output file (optional, default name will be used if not specified)

This command will generate the API Integrator configuration file using the specified input file, template file, and output file name.

### Future Enhancements

- **Schema Validation:** A mechanism for validating the configuration file against a schema.
- **Sophisticated Response Handling:** Advanced response handling capabilities, such as handling multiple responses, extracting data from responses, and handling errors.
- **Enhanced Error Handling:** Enhanced error handling capabilities, such as logging, retrying, and fallback actions.
- **Action Libraries:** Common actions encapsulated in action libraries, promoting code reusability and reducing redundancy.
- **Environment-Specific Variables:** A mechanism for defining environment-specific variables and constants to support different deployment environments.
