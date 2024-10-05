<?php

namespace TuEmpresa\LaravelAiApiIntegration\Infrastructure\Services\OasParser;

use TuEmpresa\LaravelAiApiIntegration\Domain\Entities\ApiSpecification;
use TuEmpresa\LaravelAiApiIntegration\Domain\Exceptions\OasParserException;

class Oas31Parser extends AbstractOasParser {
    protected ?ApiSpecification $apiSpec = null;

    public function parse(string $oasFilePath = ''): ApiSpecification {
        if (!empty($oasFilePath)) {
            $this->loadData($oasFilePath);
        }
        if (empty($this->data)) {
            throw new OasParserException("No data to parse. Please provide a valid OAS file path or load data before parsing.");
        }

        $this->apiSpec = new ApiSpecification(
            $this->getApiName(),
            $this->getBaseUrl(),
            $this->getVersion(),
            $this->parseServers($this->data['servers'] ?? []),
            $this->data['info'] ?? []
        );

        $this->parsePaths($this->data['paths'] ?? []);
        $this->parseComponents($this->data['components'] ?? []);
        $this->parseWebhooks($this->data['webhooks'] ?? []);
        $this->apiSpec->setExternalDocs($this->data['externalDocs'] ?? []);
        $this->apiSpec->setTags($this->data['tags'] ?? []);

        return $this->apiSpec;
    }

    private function parseServers(array $servers): array {
        return array_map(function($server) {
            return [
                'url' => $server['url'],
                'description' => $server['description'] ?? null,
                'variables' => $server['variables'] ?? []
            ];
        }, $servers);
    }

    private function parsePaths(array $paths): void {
        foreach ($paths as $path => $methods) {
            foreach ($methods as $method => $operation) {
                $responses = $this->parseResponses($operation['responses'] ?? []);
                $this->apiSpec->addEndpoint([
                    'path' => $path,
                    'method' => strtoupper($method),
                    'operationId' => $operation['operationId'] ?? $this->generateOperationId($method, $path),
                    'summary' => $operation['summary'] ?? null,
                    'description' => $operation['description'] ?? null,
                    'parameters' => $operation['parameters'] ?? [],
                    'requestBody' => $operation['requestBody'] ?? null,
                    'responses' => $responses,
                    'tags' => $operation['tags'] ?? [],
                    'security' => $operation['security'] ?? [],
                ]);
            }
        }
    }

    private function parseResponses(array $responses): array {
        $parsedResponses = [];
        foreach ($responses as $statusCode => $response) {
            $parsedResponses[$statusCode] = [
                'description' => $response['description'] ?? '',
                'headers' => $response['headers'] ?? [],
                'content' => $this->parseResponseContent($response['content'] ?? []),
            ];
        }
        return $parsedResponses;
    }

    private function parseResponseContent(array $content): array {
        $parsedContent = [];
        foreach ($content as $mediaType => $mediaTypeObject) {
            $parsedContent[$mediaType] = [
                'schema' => $mediaTypeObject['schema'] ?? null,
                'examples' => $mediaTypeObject['examples'] ?? null,
            ];
        }
        return $parsedContent;
    }

    private function parseComponents(array $components): void {
        $componentTypes = [
            'schemas' => 'setSchemas',
            'responses' => 'setResponses',
            'parameters' => 'setParameters',
            'examples' => 'setExamples',
            'requestBodies' => 'setRequestBodies',
            'headers' => 'setHeaders',
            'securitySchemes' => 'setSecuritySchemes',
            'links' => 'setLinks',
            'callbacks' => 'setCallbacks',
            'pathItems' => 'setPathItems'
        ];

        foreach ($componentTypes as $type => $setter) {
            if (isset($components[$type])) {
                $this->apiSpec->$setter($components[$type]);
            }
        }

        // Parse additional OAS 3.1 specific components
        $this->parseSecurityRequirements();
        $this->parseServers($this->data['servers'] ?? []);
        $this->parseWebhooks();
    }

    private function parseSecurityRequirements(): void {
        if (isset($this->data['security'])) {
            $this->apiSpec->setSecurityRequirements($this->data['security']);
        }
    }

    private function parseWebhooks(): void {
        if (isset($this->data['webhooks'])) {
            $this->apiSpec->setWebhooks($this->data['webhooks']);
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
