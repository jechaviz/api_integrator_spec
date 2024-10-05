class OasParserException(Exception):
    INVALID_OAS_FORMAT = 1
    UNSUPPORTED_OAS_VERSION = 2
    FILE_NOT_FOUND = 3
    INVALID_FILE_CONTENT = 4

    def __init__(self, message: str = "OAS Parser error", code: int = 0, error_code: int = 0):
        super().__init__(message, code)
        self.error_code = error_code

    def get_error_code(self) -> int:
        return self.error_code
