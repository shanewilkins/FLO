"""FLO-owned color snapshot checked against mpi-theme 0.1.5.

Only values already shipped by FLO are centralized here. This is not an asset
redistribution or a general mpi-theme adapter; diagram role choices stay in FLO.
See docs/specs/render_themes.md for provenance and the update procedure.
"""

from types import MappingProxyType

MPI_THEME_VERSION = "0.1.5"
MPI_THEME_REVISION = "6d47087da8ffdd83c0252e7410155cc7ced4962d"
MPI_FONT_FAMILY = ("Source Sans 3", "system-ui", "sans-serif")
MPI_COLORS = MappingProxyType(
    {
        "canvas": "#F6F7F5",
        "surface": "#FFFFFF",
        "ink": "#1F2933",
        "muted": "#5B6870",
        "border": "#CDD5D5",
        "primary": "#0B5D5A",
        "warning": "#8A5A00",
        "danger": "#A43232",
        "info": "#1D5D88",
        "table-stripe": "#F1F4F3",
    }
)
