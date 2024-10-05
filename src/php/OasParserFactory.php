<?php

namespace TuEmpresa\LaravelAiApiIntegration\Infrastructure\Services\OasParser;

use TuEmpresa\LaravelAiApiIntegration\Domain\Interfaces\OasParserInterface;
use TuEmpresa\LaravelAiApiIntegration\Domain\Exceptions\OasParserException;
use Symfony\Component\Yaml\Yaml;

class OasParserFactory {
    public static function create(string $filePath): OasParserInterface {
        $extension = pathinfo($filePath, PATHINFO_EXTENSION);
        
        if (!in_array($extension, ['json', 'yaml', 'yml'])) {
            throw new OasParserException("Unsupported file format: $extension");
        }

        try {
            $content = file_get_contents($filePath);
            if ($content === false) {
                throw new OasParserException("Unable to read file: $filePath");
            }

            $data = self::parseContent($content, $extension);
            return self::createParserByVersion($data);
        } catch (\Exception $e) {
            throw new OasParserException("Error creating OAS parser: " . $e->getMessage(), 0, $e);
        }
    }

    private static function parseContent(string $content, string $extension): array {
        if ($extension === 'json') {
            $data = json_decode($content, true, 512, JSON_THROW_ON_ERROR);
        } else {
            $data = Yaml::parse($content);
        }

        if (!is_array($data)) {
            throw new OasParserException("Invalid OpenAPI specification: file content is not a valid JSON/YAML.");
        }

        if (!isset($data['openapi']) || !is_string($data['openapi'])) {
            throw new OasParserException("Invalid OpenAPI specification: 'openapi' version not found or invalid.");
        }

        return $data;
    }

    private static function createParserByVersion(array $data): OasParserInterface {
        $version = $data['openapi'];
        if (strpos($version, '3.0') === 0) {
            return new Oas30Parser();
        } elseif (strpos($version, '3.1') === 0) {
            return new Oas31Parser();
        } else {
            throw new OasParserException("Unsupported OpenAPI version: $version");
        }
    }
}
