import os
import urllib.request
from functools import lru_cache
from dukpy import JSInterpreter

_RUNTIME = os.path.join(os.path.dirname(__file__), "runtime.js")


@lru_cache(maxsize=32)
def _fetch_url(url: str, timeout: int = 10) -> str:
    """Fetch and cache URL content."""
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8")


def _get_content(source: str, timeout: int = 10) -> str:
    """Get content from URL or file path.

    Supports http://, https://, file:// URLs and local file paths.
    """
    if source.startswith(("http://", "https://")):
        return _fetch_url(source, timeout)

    if source.startswith("file://"):
        path = source[7:]  # Strip 'file://'
        with open(path, encoding="utf-8") as f:
            return f.read()

    # Local file path
    with open(source, encoding="utf-8") as f:
        return f.read()


class VirtualDomInterpreter:
    """Persistent JavaScript interpreter with an isolated virtual DOM."""

    def __init__(self):
        self._interpreter = JSInterpreter()
        with open(_RUNTIME, encoding="utf-8") as runtime:
            self._interpreter.evaljs(runtime)

    def evaljs(self, code, **kwargs):
        return self._interpreter.evaljs(code, **kwargs)

    def html(self):
        """Return the current virtual page as HTML."""
        return self.evaljs("document.documentElement.toHTML();")

    def reset(self):
        """Reset the virtual DOM to a fresh document; other globals survive."""
        self.evaljs("resetDocument(); undefined;")

    def snapshot(self):
        """Capture the current virtual DOM and return an opaque handle."""
        return self.evaljs("snapshotDocument();")

    def restore(self, snapshot):
        """Replace the virtual DOM with a previously captured snapshot.

        :param int snapshot: Handle returned by :meth:`snapshot`.
        """
        self.evaljs("restoreDocument(dukpy.snapshot); undefined;", snapshot=snapshot)

    def load_framework(self, *sources: str, timeout: int = 10) -> VirtualDomInterpreter:
        """Load one or more framework bundles from URLs or file paths.

        Always injects 'var self = globalThis;' for compatibility with
        frameworks that require it (like React's UMD wrapper).

        :param sources: One or more URLs or file paths to framework bundles.
                       Supports http://, https://, file://, and local paths.
        :param timeout: Timeout in seconds for URL fetches (default: 10).
        :return: self, for chaining.
        :raises ValueError: If a source cannot be loaded.

        Example::

            # Load React from unpkg
            interp.load_framework(
                "https://unpkg.com/react@18/umd/react.production.min.js",
                "https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"
            )

            # Load Vue from local file
            interp.load_framework("path/to/vue.global.prod.js")

            # Chain with other operations
            interp.load_framework("https://.../vue.js").evaljs("Vue.createApp({}).mount('#app')")
        """
        # Always inject shim for safety (harmless for Vue, required for React)
        self.evaljs("var self = globalThis;")

        for source in sources:
            try:
                content = _get_content(source, timeout)
                self.evaljs(content)
            except Exception as e:
                raise ValueError(f"Failed to load {source}: {e}") from e

        return self
