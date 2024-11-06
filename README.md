# API Integration Specification (AIS)

[... previous content ...]

### Configuration Validation

The API Integrator now includes built-in configuration validation using `pykwalify`. This ensures that your configuration files adhere to a strict schema before processing.

#### Validation Features
- Semantic version checking
- URL format validation
- Required field enforcement
- Nested structure validation
- Type checking

#### Custom Schema Validation

You can provide a custom schema when initializing the ApiIntegrator:

```python
# Uses default schema if not specified
integrator = ApiIntegrator('config.yml')

# Or specify a custom schema
integrator = ApiIntegrator('config.yml', schema_path='path/to/custom_schema.yml')
```

#### Schema Validation Checks
- Validates API Integrator version
- Checks configuration structure
- Enforces required fields
- Validates contact information formats
- Ensures consistent action and response definitions

### Error Handling

If your configuration fails validation, a `ValueError` will be raised with detailed error messages.

```python
try:
    integrator = ApiIntegrator('invalid_config.yml')
except ValueError as e:
    print(f"Configuration error: {e}")
    # Handle configuration validation failure
```

[... rest of the README remains the same ...]
