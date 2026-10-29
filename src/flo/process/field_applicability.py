"""Book-aligned applicability shared by source and exchange boundaries."""

COMMON_FIELDS = frozenset(
    {"id", "kind", "name", "description", "lane", "subprocess_parent", "extensions"}
)
WORK_FIELDS = frozenset(
    {
        "location",
        "consumes",
        "produces",
        "performed_by",
        "uses",
        "value_class",
        "cycle_time",
        "wait_time",
        "changeover_time",
    }
)
WORK_KINDS = frozenset({"task", "system_task", "subprocess"})
WAIT_KINDS = frozenset({"queue", "wait"})
NODE_FIELDS = {
    **dict.fromkeys(WORK_KINDS, COMMON_FIELDS | WORK_FIELDS),
    **{kind: COMMON_FIELDS | {"wait_time", "location"} for kind in WAIT_KINDS},
    **dict.fromkeys(("start", "end", "parallel_split", "parallel_join"), COMMON_FIELDS),
    "decision": COMMON_FIELDS | {"outcomes"},
    "branch": COMMON_FIELDS | {"branch", "routes"},
}
SOURCE_ONLY_FIELDS = frozenset({"steps"})


def inapplicable_fields(kind: str, supplied: set[str]) -> set[str]:
    """Return supplied semantic fields unsupported by a node kind."""
    allowed = NODE_FIELDS.get(kind, COMMON_FIELDS)
    if kind == "subprocess":
        allowed = allowed | {"steps"}
    return supplied - allowed
