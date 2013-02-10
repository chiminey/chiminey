class ErrorBase(Exception):
    pass


class BadInputException(Exception):
    pass


class ContextKeyMissing(Exception):
    pass


class BadSpecificationError(Exception):
    pass


class InsufficientResourceError(Exception):
    pass


class MissingConfigurationError(Exception):
    pass