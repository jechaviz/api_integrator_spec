<?php

namespace TuEmpresa\LaravelAiApiIntegration\Infrastructure\Services\OasParser;

use TuEmpresa\LaravelAiApiIntegration\Domain\Entities\ApiSpecification;
use TuEmpresa\LaravelAiApiIntegration\Domain\Exceptions\OasParserException;

class Oas30Parser extends AbstractOasParser {
    public function parse(string $oasFilePath = ''): ApiSpecification {
        $this->loadData($oasFilePath);

        $apiSpecification = $this->createApiSpecification();

        $this->parsePaths($apiSpecification);
        $this->parseComponents($apiSpecification);
        $this->parseTags($apiSpecification);
        $this->parseExternalDocs($apiSpecification);

        return $apiSpecification;
    }

    private function createApiSpecification(): ApiSpecification {
        $name = $this->getApiName();
        $baseUrl = $this->getBaseUrl();
        $version = $this->getVersion();

        return new ApiSpecification($name, $baseUrl, $version, $this->data['servers'] ?? [], $this->data['info'] ?? []);
    }

    private function parsePaths(ApiSpecification $apiSpecification): void {
        if (!isset($this->data['paths'])) {
            return;
        }

        foreach ($this->data['paths'] as $path => $pathData) {
            foreach ($pathData as $method => $endpointData) {
                $endpoint = $this->createEndpoint($path, $method, $endpointData);
                $apiSpecification->addEndpoint($endpoint);
            }
        }
    }

    private function createEndpoint(string $path, string $method, array $endpointData): array {
        $endpoint = [
            'path' => $path,
            'method' => strtoupper($method),
            'operationId' => $endpointData['operationId'] ?? $this->generateOperationId($method, $path),
            'summary' => $endpointData['summary'] ?? null,
            'description' => $endpointData['description'] ?? null,
            'parameters' => $endpointData['parameters'] ?? [],
            'responses' => $endpointData['responses'] ?? [],
            'requestBody' => $endpointData['requestBody'] ?? null,
            'security' => $endpointData['security'] ?? [],
            'tags' => $endpointData['tags'] ?? [],
        ];

        $this->extractResponseExamples($endpoint);

        return $endpoint;
    }

    private function extractResponseExamples(array &$endpoint): void {
        foreach ($endpoint['responses'] as $statusCode => $responseData) {
            if (isset($responseData['content']['application/json']['examples'])) {
                $endpoint['responses'][$statusCode]['examples'] = $responseData['content']['application/json']['examples'];
            }
        }
    }

    private function parseComponents(ApiSpecification $apiSpecification): void {
        $componentTypes = [
            'schemas' => 'setSchemas',
            'responses' => 'setResponses',
            'parameters' => 'setParameters',
            'examples' => 'setExamples',
            'requestBodies' => 'setRequestBodies',
            'headers' => 'setHeaders',
            'securitySchemes' => 'setSecuritySchemes',
            'links' => 'setLinks',
            'callbacks' => 'setCallbacks'
        ];

        foreach ($componentTypes as $type => $setter) {
            if (isset($this->data['components'][$type])) {
                $apiSpecification->$setter($this->data['components'][$type]);
            }
        }

        // Parse additional OAS 3.0 specific components
        $this->parseSecurityRequirements($apiSpecification);
        $this->parseServers($apiSpecification);
    }

    private function parseSecurityRequirements(ApiSpecification $apiSpecification): void {
        if (isset($this->data['security'])) {
            $apiSpecification->setSecurityRequirements($this->data['security']);
        }
    }

    private function parseServers(ApiSpecification $apiSpecification): void {
        if (isset($this->data['servers'])) {
            $apiSpecification->setServers($this->data['servers']);
        }
    }

    private function parseTags(ApiSpecification $apiSpecification): void {
        if (isset($this->data['tags'])) {
            $apiSpecification->setTags($this->data['tags']);
        }
    }

    private function parseExternalDocs(ApiSpecification $apiSpecification): void {
        if (isset($this->data['externalDocs'])) {
            $apiSpecification->setExternalDocs($this->data['externalDocs']);
        }
    }

    public function getApiName(): string {
        return $this->data['info']['title'] ?? 'Unnamed API';
    }

    public function getBaseUrl(): string {
        return $this->data['servers'][0]['url'] ?? '';
    }

    public function getVersion(): string {
        return $this->data['info']['version'] ?? '1.0.0';
    }
}
