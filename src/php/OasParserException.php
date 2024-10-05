<?php

namespace TuEmpresa\LaravelAiApiIntegration\Domain\Exceptions;

class OasParserException extends \Exception {
    public const INVALID_OAS_FORMAT = 1;
    public const UNSUPPORTED_OAS_VERSION = 2;
    public const FILE_NOT_FOUND = 3;
    public const INVALID_FILE_CONTENT = 4;

    private int $errorCode;

    public function __construct(string $message = "OAS Parser error", int $code = 0, \Throwable $previous = null, int $errorCode = 0) {
        parent::__construct($message, $code, $previous);
        $this->errorCode = $errorCode;
    }

    public function getErrorCode(): int {
        return $this->errorCode;
    }
}
