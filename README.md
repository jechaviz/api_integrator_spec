## API Integration Convention
 
 This project utilizes a YAML-based configuration file to define the logic for integrating with external APIs. 
 The configuration file specifies actions, responses, and triggers, allowing for a flexible and reusable approach to API integration.
 This convention promotes consistency and maintainability across different API integrations.

## Configuration Structure

### `api_integrator`
- **Version**: Specifies the version of the API integrator.

### `info`
- **title**: Title of the configuration.
- **version**: Version of the configuration.
- **description**: Description of the configuration.
- **contact**: Contact information for support.
- **lang**: Expected language in expresions like in log messages (e.g., python, javascript, etc.).

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
- **performs**: List of actions to perform. Can be defined under main action section or as trigger of a response.
  - **perform**: Commands to be performed (e.g., `http.{verb}`, `action.{name}`, `action.{command}`, `log.{level}`, etc.).
  - **data**: Data required by the action to be performed.
  - **responses**: After an action be performed, is expected a response. Responses is a list of responses to handle.
    - **is_success**: Conditions for successful responses (all values are required to be considered true).
      - has_value: true if the response has the specified value.
      - boolean: true if the response matches the specified boolean expression.
      - contains: true if the response contains the specified value.
      - matches: true if the response matches the specified regex.
      - code: true if the response code is the specified value.
      - has_key: true if the response has the specified key.
      - has_keys: true if the response has all the specified keys.
    - **is_error**: When is_success is not true, conditions for handling different errors. Same keys as is_success.
    

### `perform commands`
- They are basic commands that can be performed by actions.
- They are used to perform actions like `http.{verb}`, `action.{name}`, `action.{command}`, `log.{level}`, etc.
- They are executed by the implementation of the API integrator.
- Implement at least the following commands:
  - http.{verb}(url, headers, body, query, files) is used to perform an HTTP request with a specific URL and files, where:
    - verb is the HTTP verb to use (e.g., get, post, put, delete, etc.).
    - url is the URL to perform the request.
    - headers is a dictionary of headers to include in the request.
    - body is the body of the request.
      - The body can be a string, a dictionary, or a list of dictionaries.
      - would be converted to application/{format} if the content-type is specified, otherwise application/json.
    - query is a dictionary of query parameters to include in the request.
    - files is a dictionary of files to include in the request converted to the specified format.
      - format is the format of the files (e.g., json, multipart, base64, etc.).
  - log.{level}(message) is used to log a message.
    - message will be interpreted as the language specific implementation expression.
      - e.g., in python a log debug action can be written in this specification like this directly in yml in this way: log.debug(f'response:{response.body}')
    - supported levels supported must be: debug, info, warning, error, critical.
  - action.{name} is used to call an action defined in the actions section, letting be chained.
  - action.{command} is used to call a command defined in the perform commands section.
    - action.var.{var_name} is used to get a variable from the vars section.
    - action.var.{var_name}={value} is used to set a variable in the vars section.
    - action.retry(trials, delay) is used to retry an action.
      - trials is the number of times to retry the action.
      - delay is the delay between retries in milliseconds.
    - more commands can be added as needed.

### `vars`
- Are global variables that can be accessed by actions, and override with parameters fed to actions.

### `constants`
- Are global constants that can be accessed by actions, not overridables.

### `parameters`
- Are represented with vars between brackets in actions. These parameters must be fed to actions when they are called.

## Example Configuration

 ```yaml
 api_integrator: 0.0.1
 info:
   title: Interaction Configuration with API from My Supplier to integrate with my app
   version: 1.0.0
   description: This is a sample configuration file for API integrator
   contact:
     name: Developer
     url: https://my.supplier.com
     email: support@my.supplier.com
 supplier_servers:
   - id: prod
     url: https://api.my.supplier.com
     description: My Supplier production server
   - id: sandbox
     url: https://sandbox.api.my.supplier.com
     description: My Supplier sandbox server
 tags:
   - name: items
     description: Supplier Endpoints to manage items
   - name: users
     description: Supplier Endpoints to manage users
 actions:
   auth:
     tags:
       - users
     description: The actions needed to authenticate
     performs:
     - perform: http.post
       data:
         path: {{supplier_server}}/auth/login
         body:
           user: '{{user}}'
           pass: '{{pass}}'
       responses:
         - is_success:
             code: 200
             contains: ok
           performs:
             - perform: action.var.session_token=response.token
             - perform: log.info('Successfully authenticated')
         - is_error:
             code: 400
           performs:
             - perform: log.debug(response.body)
             - perform: log.error('Error authenticating')
   get_item_part:
     tags:
       - items
     description: The actions needed to get item part
     performs:
     - perform: action.var.session_token
       responses:
         - is_error:
             has_value: false
           performs:
             - perform: action.auth
               responses:
                 - is_error:
                     has_value: false
                   triggers:
                     - perform: action.retry
                       data:
                         trials: 3
                         delay: 10
     - perform: http.get
       data:
         headers:
           Authorization: Bearer action.get_var.token
         path: {{supplier_server}}/items/part/{{id_item}}/part/{{id_part}}
       responses:
         - is_success:
             code: 200
             contains: ok
           performs:
             - perform: log.info('Successfully got item part')
             - perform: http.post
               data:
                 url: https://api.my.app.com/items/part/{{id}}
                 headers:
                   Authorization: Bearer env.my_app_api_token
                 body:
                   id: response.id
                   name: response.name
                   price: response.price
                   description: response.description
                   stock: response.stock
                   image: response.img
                   is_active: !response.is_discontinued
         - is_error:
             contains: error
             code: 400
           performs:
             - perform: log.error('Error getting item part' response.body)

 vars:
   session: 34
   is_demo: true
 constants:
   asset_codes:
     USDBTC: 1
```

### Future Enhancements

**Schema Validation:** A mechanism for validating the configuration file against a schema is provided.
**Sophisticated Response Handling:** Advanced response handling capabilities, such as handling multiple responses, extracting data from responses, and handling errors, are planned.
**Enhanced Error Handling:** Enhanced error handling capabilities, such as logging, retrying, and fallback actions, are planned.
**Action Libraries:** Common actions encapsulated in action libraries, promoting code reusability and reducing redundancy (planned an import keyword)
**Environment-Specific Variables:** A mechanism for defining environment-specific variables and constants is provided to support different deployment environments.