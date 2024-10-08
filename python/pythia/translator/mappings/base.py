"""Base classes and other overarching components required for mappings.

The main component of this file is the base class of mappings. It should be
implemented for defining mappings and used by the translator for translation.
See the documentation of this base class for further information about the
other components.
"""

import ast
from abc import ABC, abstractmethod
from typing import Any

from translator.context import Context


class BaseMapping(ABC):
    """Abstract base class for defining translator-mappings.

    This class serves as a blueprint for creating specific mappings that map
    specific types of `ast` nodes. Each mapping must therefore implement the
    `map` method.

    Each mapping should use the provided `Context` instance for adding lines,
    translating sub-nodes, generating unique information, …. Furthermore, the
    return value of the `map` method is only relevant for expressions ( do not
    take up whole lines, i.e. no statements). In case a non-fatal error is
    encountered, raise `MappingWarning`, and in case of a fatal error, raise
    `MappingError`.
    """

    @classmethod
    @abstractmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        """Map the given node to some resulting code.

        Args:
            node: The node to map.
            context: A `Context` instance helpful for translation.

        Raises:
            NotImplementedError: In case the `map` method was not overridden
                properly.
            MappingWarning: In case a non-fatal error is encountered during
                translation, the remaining translation may still continue.
            MappingError: In case a fatal error occurred during translation
                which requires the user's attention or invalidates the whole
                translation. In case of a non-fatal error, simply return the
                string representation of the node, highlighting a missing
                proper translation for this node in the resulting translation.

        Returns:
            In case the node represents a statement `None`, in case it
            represents an expression, the mapping.
        """
        raise NotImplementedError("Mapping method not implemented.")


class MappingWarning(Exception):
    """This represents a (non-fatal) warning during the translation process.

    Attributes:
        message: A message for the user explaining the (cause of the) warning.
    """

    def __init__(
        self,
        message: str = "Received a warning during translation.",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, *args, **kwargs)
        self.message = message


class MappingError(Exception):
    """This represents a fatal error during the translation process.

    Attributes:
        message: A message for the user explaining the (cause of the) error.
    """

    def __init__(
        self,
        message: str = "An error occured during translation.",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, *args, **kwargs)
        self.message = message
