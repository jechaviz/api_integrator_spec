<?php

namespace TuEmpresa\LaravelAiApiIntegration\Infrastructure\Services\OasParser;

use TuEmpresa\LaravelAiApiIntegration\Domain\Interfaces\OasParserInterface;
use TuEmpresa\LaravelAiApiIntegration\Domain\Entities\ApiSpecification;
use Symfony\Component\Yaml\Yaml;
use TuEmpresa\LaravelAiApiIntegration\Domain\Exceptions\OasParserException;

abstract class AbstractOasParser implements OasParserInterface {
    protected array $data = [];

    protected function loadData(string $oasFilePath): void {
        try {
            $content = file_get_contents($oasFilePath);

            if ($content === false) {
                throw new OasParserException("Unable to read file: $oasFilePath");
            }

            $extension = pathinfo($oasFilePath, PATHINFO_EXTENSION);
            
            if ($extension === 'json') {
                $this->data = json_decode($content, true, 512, JSON_THROW_ON_ERROR);
            } elseif ($extension === 'yaml' || $extension === 'yml') {
                $this->data = Yaml::parse($content);
            } else {
                throw new OasParserException("Unsupported file format: $extension");
            }

            if (empty($this->data)) {
                throw new OasParserException("Failed to parse file content as " . strtoupper($extension));
            }

            if (!isset($this->data['openapi'])) {
                throw new OasParserException("Invalid OpenAPI specification: 'openapi' version not found.");
            }
        } catch (\JsonException $e) {
            throw new OasParserException("Failed to parse JSON: " . $e->getMessage());
        } catch (\Symfony\Component\Yaml\Exception\ParseException $e) {
            throw new OasParserException("Failed to parse YAML: " . $e->getMessage());
        }
    }

    abstract public function parse(string $oasFilePath = ''): ApiSpecification;

    abstract protected function getApiName(): string;
    abstract protected function getBaseUrl(): string;
    abstract protected function getVersion(): string;

    protected function generateOperationId(string $method, string $path): string {
        $parts = explode('/', ltrim($path, '/'));
        $parts = array_filter($parts, fn($part) => !preg_match('/^ {.*}$/', $part));
        $operationId = strtolower($method) . ucfirst(implode('', array_map('ucfirst', $parts)));
        return lcfirst($operationId);
    }
}
