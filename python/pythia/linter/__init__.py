r"""A linter for probabilistic programs.

This module provides a general purpose linter class which may be used with
custom rules for a spectrum of use-cases. Default implementations and a
CLI-interface are provided which may be used to lint code conforming to the
specifications of the _PyThia_ Meta-Probabilistic-Programming-Language.

Usage:
    This module provides a default implementation. Moreover, the `Linter` class
    may be used to lint code with custom rules.

Attributes:
    Linter: This class represents a general-purpose linter. By specifying
        mappings and other potential dependencies, the linter may be suited to
        the required use-case.
    default_probabilistic_program_linter: This provides the default linter for
        the _PyThia_ Meta-Probabilistic-Programming-Language.
    ExitCode: An enumeration representing the different possible exit codes.
    Diagnostic: A class representing a diagnostic generated by the linter.
    Severity: An enumeration of the possible severities of a diagnostic.

Examples:
    ```py
    tree = ast.parse(code)
    linter = default_probabilistic_program_linter()
    diagnostics = linter.lint(tree)
    ```

Author: L. Kaufmann <e12002221@student.tuwien.ac.at>
Version: 0.1.0
Status: In Development
"""

from .diagnostic import *
from .main import *
