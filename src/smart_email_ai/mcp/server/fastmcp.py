from typing import Any, Callable, TypeVar

T = TypeVar("T", bound=Callable[..., Any])

class FastMCP:
    """Light-weight fallback implementation of FastMCP.

    Only provides the subset of behaviour required by Smart Email AI:
    • Construction with a name.
    • The ``tool`` decorator that simply returns the wrapped callable.
    """

    def __init__(self, name: str) -> None:  # noqa: D401
        self.name: str = name

    # ---------------------------------------------------------------------
    # Decorators
    # ---------------------------------------------------------------------
    def tool(self) -> Callable[[T], T]:  # type: ignore[name-defined]
        """Return a no-op decorator so that ``@mcp.tool`` works without MCP."""

        def decorator(func: T) -> T:  # noqa: D401
            return func

        return decorator

    # ------------------------------------------------------------------
    # Callable behaviour
    # ------------------------------------------------------------------
    def __call__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        """Allow the instance to be called without side-effects."""
        return None