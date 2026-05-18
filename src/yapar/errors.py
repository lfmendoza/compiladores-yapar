from __future__ import annotations


class YAParError(Exception):
    pass


class YAParSyntaxError(YAParError):
    def __init__(self, message: str, line: int = -1, column: int = -1) -> None:
        location = f" (line {line}, col {column})" if line >= 0 else ""
        super().__init__(f"{message}{location}")
        self.line = line
        self.column = column


class ConflictError(YAParError):
    def __init__(
        self,
        state: int,
        symbol: str,
        existing: object,
        incoming: object,
    ) -> None:
        super().__init__(
            f"SLR conflict in state {state} on '{symbol}': "
            f"{existing!r} vs {incoming!r}"
        )
        self.state = state
        self.symbol = symbol
        self.existing = existing
        self.incoming = incoming


class ParseError(YAParError):
    def __init__(
        self,
        state: int,
        token: object,
        line: int = -1,
        column: int = -1,
    ) -> None:
        location = f" at line {line}, col {column}" if line >= 0 else ""
        super().__init__(f"Unexpected '{token}' in state {state}{location}")
        self.state = state
        self.token = token
        self.line = line
        self.column = column
