from __future__ import annotations

from .errors import YAParSyntaxError


def validate_grammar(raw: dict) -> list[str]:
    """Return a list of human-readable error messages for a raw grammar dict.

    An empty list means the grammar passed all checks.

    Checks performed, in order:
    1. At least one rule is defined.
    2. Every symbol in every production body is either a declared token
       or the LHS of some rule (i.e., a nonterminal).
    3. Every nonterminal is reachable from the start symbol (first rule key).
    """
    errors: list[str] = []
    tokens: set[str] = set(raw.get("tokens", []))
    rules: dict[str, list[list[str]]] = raw.get("rules", {})
    nonterminals: set[str] = set(rules.keys())

    if not rules:
        errors.append("Grammar defines no rules.")
        return errors

    start = next(iter(rules))

    for head, alternatives in rules.items():
        for alt in alternatives:
            for sym in alt:
                if sym not in tokens and sym not in nonterminals:
                    errors.append(
                        f"Undefined symbol '{sym}' in production '{head}' — "
                        f"declare it under TOKENS or as a rule head."
                    )

    reachable: set[str] = {start}
    changed = True
    while changed:
        changed = False
        for nt in list(reachable):
            for alt in rules.get(nt, []):
                for sym in alt:
                    if sym in nonterminals and sym not in reachable:
                        reachable.add(sym)
                        changed = True

    for nt in sorted(nonterminals - reachable):
        errors.append(
            f"Nonterminal '{nt}' is unreachable from start symbol '{start}'."
        )

    return errors


def check_grammar(raw: dict) -> None:
    """Raise YAParSyntaxError listing all validation errors, or return normally."""
    errors = validate_grammar(raw)
    if errors:
        raise YAParSyntaxError("; ".join(errors))
