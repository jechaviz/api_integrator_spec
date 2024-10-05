<?php

namespace TuEmpresa\LaravelAiApiIntegration\Domain\Entities;

use TuEmpresa\LaravelAiApiIntegration\Domain\Exceptions\EndpointNotFoundException;
use \cebe\openapi\spec\OpenApi;
class ApiSpecification extends OpenApi
{
    private string $name;
    private string $baseUrl;
    private array $endpoints = [];
    private array $schemas = [];
    private array $securitySchemes = [];
    private array $webhooks = [];
    private array $servers = [];
    private array $tags = [];
    private array $externalDocs = [];
    private string $version;
    private string $description = '';
    private array $info = [];
    private array $responses = [];
    private array $parameters = [];
    private array $examples = [];
    private array $requestBodies = [];
    private array $headers = [];
    private array $links = [];
    private array $callbacks = [];
    private array $pathItems = [];
    private array $securityRequirements = [];

    public function __construct(string $name, string $baseUrl, string $version, array $servers = [], array $info = []) {
        $this->name = $name;
        $this->baseUrl = $baseUrl;
        $this->version = $version;
        $this->servers = $servers;
        $this->info = $info;
    }

    public function getName(): string {
        return $this->name;
    }

    public function getBaseUrl(): string {
        return $this->baseUrl;
    }

    public function getVersion(): string {
        return $this->version;
    }

    public function getEndpoints(): array {
        return $this->endpoints;
    }

    public function addEndpoint(array $endpoint): void {
        $this->endpoints[] = $endpoint;
    }

    public function getEndpoint(string $path, string $method): ?array {
        foreach ($this->endpoints as $endpoint) {
            if ($endpoint['path'] === $path && $endpoint['method'] === $method) {
                return $endpoint;
            }
        }
        return null;
    }

    public function getSampleResponsesForEndpoint(string $path, string $method): array {
        $endpoint = $this->getEndpoint($path, $method);
        if ($endpoint && isset($endpoint['responses'])) {
            return $endpoint['responses'];
        }
        return [];
    }

    public function getResponseByStatusCode(string $path, string $method, string $statusCode): ?array {
        $endpoint = $this->getEndpoint($path, $method);
        if ($endpoint && isset($endpoint['responses'][$statusCode])) {
            return $endpoint['responses'][$statusCode];
        }
        return null;
    }

    public function getSchemas(): array {
        return $this->schemas;
    }

    public function setSchemas(array $schemas): void {
        $this->schemas = $schemas;
    }

    public function getSecuritySchemes(): array {
        return $this->securitySchemes;
    }

    public function setSecuritySchemes(array $securitySchemes): void {
        $this->securitySchemes = $securitySchemes;
    }

    public function getWebhooks(): array {
        return $this->webhooks;
    }

    public function setWebhooks(array $webhooks): void {
        $this->webhooks = $webhooks;
    }

    public function getServers(): array {
        return $this->servers;
    }

    public function setServers(array $servers): void {
        $this->servers = $servers;
    }

    public function getTags(): array {
        return $this->tags;
    }

    public function setTags(array $tags): void {
        $this->tags = $tags;
    }

    public function getExternalDocs(): array {
        return $this->externalDocs;
    }

    public function setExternalDocs(array $externalDocs): void {
        $this->externalDocs = $externalDocs;
    }

    public function getInfo(): array {
        return $this->info;
    }

    public function setResponses(array $responses): void {
        $this->responses = $responses;
    }

    public function setParameters(array $parameters): void {
        $this->parameters = $parameters;
    }

    public function setExamples(array $examples): void {
        $this->examples = $examples;
    }

    public function setRequestBodies(array $requestBodies): void {
        $this->requestBodies = $requestBodies;
    }

    public function setHeaders(array $headers): void {
        $this->headers = $headers;
    }

    public function setLinks(array $links): void {
        $this->links = $links;
    }

    public function setCallbacks(array $callbacks): void {
        $this->callbacks = $callbacks;
    }

    public function setPathItems(array $pathItems): void {
        $this->pathItems = $pathItems;
    }

    public function setSecurityRequirements(array $securityRequirements): void {
        $this->securityRequirements = $securityRequirements;
    }

    public function addRequestBodyToEndpoint(string $path, string $method, array $requestBody): void {
        $this->updateEndpoint($path, $method, ['requestBody' => $requestBody]);
    }

    public function addResponseToEndpoint(string $path, string $method, string $statusCode, array $response): void {
        $this->updateEndpoint($path, $method, ['responses' => [$statusCode => $response]]);
    }

    public function addSecurityToEndpoint(string $path, string $method, array $security): void {
        $this->updateEndpoint($path, $method, ['security' => $security]);
    }

    public function addTagToEndpoint(string $path, string $method, string $tag): void {
        $endpoint = $this->getEndpoint($path, $method);
        if ($endpoint === null) {
            throw new EndpointNotFoundException("Endpoint not found for path: $path and method: $method");
        }
        if (!in_array($tag, $endpoint['tags'])) {
            $endpoint['tags'][] = $tag;
            $this->updateEndpoint($path, $method, ['tags' => $endpoint['tags']]);
        }
    }

    public function setEndpointSummary(string $path, string $method, string $summary): void {
        $this->updateEndpoint($path, $method, ['summary' => $summary]);
    }

    public function setEndpointDescription(string $path, string $method, string $description): void {
        $this->updateEndpoint($path, $method, ['description' => $description]);
    }

    public function getSampleResponsesByStatusCode(string $path, string $method, string $statusCode): array {
        $endpoint = $this->getEndpoint($path, $method);
        if ($endpoint === null) {
            throw new EndpointNotFoundException("Endpoint not found for path: $path and method: $method");
        }

        if (!isset($endpoint['responses'][$statusCode])) {
            return [];
        }

        $response = $endpoint['responses'][$statusCode];
        return $response['examples'] ?? [];
    }

    private function updateEndpoint(string $path, string $method, array $data): void {
        $endpoint = $this->getEndpoint($path, $method);
        if ($endpoint === null) {
            throw new EndpointNotFoundException("Endpoint not found for path: $path and method: $method");
        }

        foreach ($data as $key => $value) {
            if (is_array($value) && isset($endpoint[$key]) && is_array($endpoint[$key])) {
                $endpoint[$key] = array_merge($endpoint[$key], $value);
            } else {
                $endpoint[$key] = $value;
            }
        }

        $this->endpoints = array_map(function ($e) use ($endpoint, $path, $method) {
            return ($e['path'] === $path && $e['method'] === $method) ? $endpoint : $e;
        }, $this->endpoints);
    }
}
