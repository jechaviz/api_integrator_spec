### API Integrator Specification README

# API Integrator Specification

## Overview

The **API Integrator** specification provides a structured way to define and manage API interactions, including HTTP requests, logging actions, and database updates. This specification is designed to facilitate the integration of various APIs into a single cohesive framework, enabling robust error handling and response processing.

## Features

- **Versioning**: Supports multiple versions of the API for backward compatibility.
- **Triggers**: Define actions based on responses to automate workflows.
- **Dynamic Variables**: Use dynamic variables within requests for flexibility.
- **Chained Actions**: Execute multiple actions in a sequence based on previous responses.
- **Detailed Documentation**: Each action and response is documented for clarity.

## YAML Structure

The YAML configuration is structured to include key elements from OpenAPI 3.1 for proper documentation generation. Below are the main components:

- **api_integrator**: Version of the API INTEGRATOR specification being used.
- **info**: Metadata about the API, including title, version, and description.
- **servers**: List of server URLs where the API is hosted.
- **tags**: Categorization of actions for better organization.
- **actions**: Defines the operations to be performed.

## Getting Started

To get started with the API Integrator, you need to have a basic understanding of YAML syntax and this new proposed specification.

### YAML Syntax
Actions are the core components of the API Integrator Specification.
Each action has a unique name, a description, and a set of parameters, 
which can be used to customize the behavior of the action.

An action starts with the paths of the API endpoints, to be called. 
So the servers property is used to define the base URL of the API you want to interact with.
We have a set of paths for each action, these paths are provided by the API provider.
Then after sending the request defined in the request property, we expect certain responses, 
that will be used to trigger one or more actions.

The response property is a list of actions that will be executed if the response matches the expected response.

### `save_products_per_category`

- **Description**: Authenticate the user and save products under the specified category.
- **Summary**: Chained action to authenticate and save products.

**Paths:**
1. **Authentication**
   - **Endpoint**: `/auth`
   - **Method**: `POST`
   - **Request Body**:
     ```json
     {
       "session": "{{session}}",
       "isDemo": "{{is_demo}}"
     }
     ```
   - **Responses**:
     - `200 OK`: Authentication successful.
     - `401 Unauthorized`: Authentication failed.

2. **Retrieve Products**
   - **Endpoint**: `/products`
   - **Method**: `GET`
   - **Headers**: `Authorization: Bearer {{token}}`
   - **Responses**:
     - `200 OK`: Products retrieved successfully.
     - `404 Not Found`: No products found.

## Trigger Use Cases

### Logging Actions
- **Log Success**: 
  ```yaml
  - perform: log.success
    data:
      message: 'Authentication successful'
  ```
- **Log Error**: 
  ```yaml
  - perform: log.error
    data:
      message: 'Authentication failed'
  ```
- **Log Warning**: 
  ```yaml
  - perform: log.warning
    data:
      message: 'No products found in the specified category.'
  ```

### HTTP Actions
- **HTTP POST**: 
  ```yaml
  perform: http.post
  ```
- **HTTP GET**: 
  ```yaml
  perform: http.get
  ```

### Database Actions
- **Update Database**: 
  ```yaml
  - perform: database.update
    data:
      source: response.data
      target: products[]
  ```

### Internal Actions
- **Trigger Internal Action**: 
  ```yaml
  - perform: action.save_products_per_category
  ```

## Conclusion

This API Integrator specification serves as a comprehensive guide for integrating and automating API interactions. By following this structured approach, developers can easily manage complex workflows, ensuring robust and maintainable code.