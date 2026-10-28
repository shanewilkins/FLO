"""Pydantic-owned source shapes; canonical IR and graph rules remain separate."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Any, Literal

from pydantic import (
    AliasChoices,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    TypeAdapter,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError

from flo.process.contracts import (
    Extensions,
    HandoffRelation,
    Measurement,
    NonBlank,
    ReworkRelation,
    ValueClass,
)
from flo.process.field_applicability import inapplicable_fields


def _not_null(value: Any) -> Any:
    if value is None:
        raise ValueError("explicit null is not allowed")
    return value


type Authored[T] = Annotated[T | None, BeforeValidator(_not_null)]


class AdapterModel(BaseModel):
    """Compatibility envelope for the name/content YAML loader."""

    name: str
    content: str


class SourceModel(BaseModel):
    """Strict authored shapes preserve unknown annotations and scalar values."""

    model_config = ConfigDict(strict=True, extra="forbid")


class NamedIdentity(SourceModel):
    """An authored identity with a display name."""

    id: NonBlank
    name: NonBlank
    extensions: Extensions | None = None


class BusinessUnit(NamedIdentity):
    """Named process grouping without a lane-type classification."""


class SourceLane(NamedIdentity):
    """An optional authored responsibility classification."""

    type: Literal["role", "team", "system"] | None = None


class ProcessFields(SourceModel):
    """Process context shared by complete documents and include fragments."""

    version: int | str | None = None
    lead_time: Authored[Measurement] = None
    render: Authored[dict[Any, Any]] = None
    extensions: Authored[Extensions] = None
    owner: NamedIdentity | None = None
    business_units: list[BusinessUnit] | None = None
    items: Any = None
    resources: Any = None
    locations: Any = None


class SourceProcess(NamedIdentity, ProcessFields):
    """Complete process identity and context; quantity semantics remain IR-owned."""


class FragmentProcess(ProcessFields):
    """An include may supply only part of the process identity."""

    id: Authored[NonBlank] = None
    name: Authored[NonBlank] = None


class StepAttributes(SourceModel):
    """First-class authored step fields; kind applicability is checked below."""

    name: NonBlank | None = None
    description: NonBlank | None = None
    lane: NonBlank | None = None
    location: NonBlank | None = None
    consumes: list[NonBlank] | None = None
    produces: list[NonBlank] | None = None
    performed_by: list[NonBlank] | None = None
    uses: list[NonBlank] | None = None
    value_class: ValueClass | None = None
    cycle_time: Authored[Measurement] = None
    wait_time: Authored[Measurement] = None
    changeover_time: Authored[Measurement] = None
    extensions: Authored[Extensions] = None
    subprocess_parent: Authored[NonBlank] = None
    branch: Any = None
    outcomes: Any = None
    routes: Any = None


class ControlAttributes(SourceModel):
    """Temporary control-only overlay pending complete attrs removal in phase 4."""

    subprocess_parent: Authored[NonBlank] = None
    branch: Any = None
    outcomes: Any = None
    routes: Any = None


class SourceStep(StepAttributes):
    """Recursive authored steps; both supported child spellings retain their paths."""

    id: NonBlank
    kind: Literal[
        "start",
        "task",
        "system_task",
        "queue",
        "wait",
        "decision",
        "branch",
        "end",
        "subprocess",
        "parallel_split",
        "parallel_join",
    ]
    attrs: Authored[ControlAttributes] = None
    subnodes: Authored[list[SourceStep]] = None
    steps: Authored[list[SourceStep]] = None

    @model_validator(mode="before")
    @classmethod
    def check_child_and_kind_aliases(cls, value: Any) -> Any:
        """Reject ambiguous children and the unsupported type-only spelling."""
        if isinstance(value, dict):
            if "type" in value and "kind" not in value:
                raise PydanticCustomError(
                    "source_alias", "must use 'kind'; 'type' is not supported"
                )
            if "subnodes" in value and "steps" in value:
                raise PydanticCustomError(
                    "source_alias", "must use either subnodes or steps, not both"
                )
        return value

    @model_validator(mode="after")
    def check_child_owner(self) -> SourceStep:
        """Subnodes belong to a subprocess rather than an ordinary step."""
        if (
            self.subnodes is not None or self.steps is not None
        ) and self.kind != "subprocess":
            raise PydanticCustomError(
                "source_nested", "may declare nested steps only for kind 'subprocess'"
            )
        supplied = set(self.model_fields_set)
        if self.attrs is not None:
            supplied |= set(self.attrs.model_fields_set)
        forbidden = inapplicable_fields(self.kind, supplied)
        if forbidden:
            raise PydanticCustomError(
                "source_applicability",
                "{fields} cannot be declared on kind '{kind}'",
                {"fields": ", ".join(sorted(forbidden)), "kind": self.kind},
            )
        return self


class TransitionFields(SourceModel):
    """Optional transition evidence shared by explicit edges and named branches."""

    id: NonBlank | None = None
    label: NonBlank | None = None
    route: NonBlank | None = None
    outcome: NonBlank | bool | None = None
    handoff: HandoffRelation | None = None
    rework: ReworkRelation | None = None
    extensions: Extensions | None = None


class SourceTransition(TransitionFields):
    """Explicit source/target connection with no from/to aliases."""

    source: NonBlank
    target: NonBlank

    @model_validator(mode="before")
    @classmethod
    def reject_endpoint_aliases(cls, value: Any) -> Any:
        """Keep from/to aliases out of explicit source transitions."""
        if isinstance(value, dict) and ("from" in value or "to" in value):
            raise PydanticCustomError(
                "source_alias", "must use 'source' and 'target' keys"
            )
        return value


class OutcomeBranch(TransitionFields):
    """A named route accepts a target string or an annotated branch object."""

    target: NonBlank = Field(validation_alias=AliasChoices("target", "to"))

    @model_validator(mode="before")
    @classmethod
    def accept_target_shorthand(cls, value: Any) -> Any:
        """Validate string shorthand without rewriting the authored mapping."""
        return {"target": value} if isinstance(value, str) and value.strip() else value


class BranchConfig(SourceModel):
    """Authored branch selection mechanism and optional resource eligibility."""

    mode: Literal["dispatch", "probabilistic", "external", "unspecified"]
    policy: NonBlank | None = None
    eligible_resources: Annotated[list[NonBlank], Field(min_length=1)] | None = None

    @field_validator("eligible_resources")
    @classmethod
    def unique_resources(cls, value: list[str] | None) -> list[str] | None:
        """Eligibility names each resource at most once."""
        if value is not None and len(set(value)) != len(value):
            raise ValueError("must contain unique resource IDs")
        return value


class DocumentFields(SourceModel):
    """Shared source fields and aliases before and after composition."""

    transitions: Authored[list[SourceTransition]] = None
    lanes: list[SourceLane] | None = None
    include: NonBlank | None = None
    includes: Annotated[list[NonBlank], Field(min_length=1)] | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_document_aliases(cls, value: Any) -> Any:
        """Keep compiler aliases distinct from parser compatibility normalization."""
        if isinstance(value, dict):
            if "nodes" in value:
                raise PydanticCustomError(
                    "source_alias", "steps is required; nodes alias is not supported"
                )
            if "edges" in value:
                raise PydanticCustomError(
                    "source_alias",
                    "transitions must be used; edges alias is not supported",
                )
        return value


class SourceDocument(DocumentFields):
    """The strict compiler-facing source contract after include composition."""

    spec_version: Literal["0.1"]
    process: SourceProcess
    steps: Annotated[list[SourceStep], Field(min_length=1)]


class SourceFragment(DocumentFields):
    """Validate supplied fields without requiring a standalone process."""

    spec_version: Authored[Literal["0.1"]] = None
    process: Authored[FragmentProcess] = None
    steps: Authored[list[SourceStep]] = None


NamedPaths = TypeAdapter(
    Annotated[dict[NonBlank | bool, OutcomeBranch], Field(min_length=2)]
)


def validate_source_fragment(document: dict[str, Any]) -> None:
    """Validate supplied shapes before composition can conceal declarations."""
    validate_source_shape(SourceFragment, document)
    validate_source_collections(document)


def validate_source_collections(document: dict[str, Any]) -> None:
    """Reject malformed collection shapes even when another placement shadows them."""
    process = document.get("process")
    if not isinstance(process, dict):
        return
    for key in ("items", "resources", "locations"):
        if key in process:
            _validate_collection_shape(process[key], ("process", key))


def _validate_collection_shape(value: Any, path: tuple) -> None:
    if isinstance(value, list):
        for index, entry in enumerate(value):
            if not isinstance(entry, dict):
                raise SourceShapeError(
                    f"E1202: {source_path((*path, index))} must be an object",
                    (*path, index),
                )
        return
    if not isinstance(value, dict) or not any(key != "name" for key in value):
        raise SourceShapeError(
            f"E1201: {source_path(path)} must be a list or non-empty grouped object",
            path,
        )
    for key, child in value.items():
        if not isinstance(key, str) or not key.strip():
            raise SourceShapeError(
                f"E1201: {source_path(path)} group keys must be non-empty strings", path
            )
        if key == "name":
            if not isinstance(child, str) or not child.strip():
                raise SourceShapeError(
                    f"E1201: {source_path((*path, key))} must be a non-empty string",
                    (*path, key),
                )
        else:
            _validate_collection_shape(child, (*path, key))


class SourceShapeError(ValueError):
    """Compiler-compatible failure with an authored path for location enrichment."""

    def __init__(
        self, message: str, location: tuple[str | int, ...], *, code: str = "E0222"
    ) -> None:
        """Retain the typed path without exposing unrelated input values."""
        super().__init__(message)
        self.location = location
        self.code = code


def source_path(location: tuple) -> str:
    """Format a Pydantic path in the existing compiler field-path notation."""
    return "".join(
        f"[{part}]"
        if isinstance(part, int) and not isinstance(part, bool)
        else ("." if index else "") + str(part)
        for index, part in enumerate(location)
    )


def validate_source_shape(model: Any, value: Any, location: tuple = ()) -> Any:
    """Adapt Pydantic structural failures to stable FLO source diagnostics."""
    try:
        return (
            model.validate_python(value)
            if isinstance(model, TypeAdapter)
            else model.model_validate(value)
        )
    except ValidationError as exc:
        issue = exc.errors(include_url=False, include_input=False)[0]
        issue_location = _authored_error_location(value, issue["loc"])
        path = (*location, *issue_location)
        if path and path[-1] == "[key]":
            path = path[:-2]
        elif (
            len(path) > 1
            and path[-2] in {"version", "outcome"}
            and path[-1] in {"int", "str", "bool", "constrained-str"}
        ):
            path = path[:-1]
        if model is BranchConfig:
            message = _branch_shape_message(issue, path)
        elif model is NamedPaths:
            message = _named_shape_message(issue, path, location)
        else:
            message = (
                _transition_shape_message(issue, path)
                if path and path[0] == "transitions"
                else None
            )
            message = message or _shape_message(issue, path)
        code = {"extra_forbidden": "E0220", "missing": "E0221"}.get(
            issue["type"], "E0222"
        )
        raise SourceShapeError(message, path, code=code) from exc


def _authored_error_location(value: Any, location: tuple) -> tuple:
    """Remove union implementation markers while preserving authored key names."""
    path = []
    cursor = value
    for part in location:
        if (isinstance(cursor, dict) and part in cursor) or (
            isinstance(cursor, list)
            and isinstance(part, int)
            and 0 <= part < len(cursor)
        ):
            path.append(part)
            cursor = cursor[part]
        elif isinstance(part, str) and (
            part
            in {
                "MeasurementProfile",
                "MeasurementReference",
                "str",
                "int",
                "float",
                "bool",
                "constrained-str",
            }
            or part.startswith(("function-after[", "union[", "list[", "dict["))
        ):
            continue
        else:
            path.append(part)
    return tuple(path)


def _shape_message(issue: Mapping[str, Any], path: tuple) -> str:
    field = path[-1] if path else "source"
    rendered = source_path(path)
    kind = issue["type"]
    if kind in {"source_alias", "source_nested", "source_applicability"}:
        return f"{rendered} {issue['msg']}".strip()
    if kind == "value_error" and "explicit null" in issue["msg"]:
        return f"{rendered} explicit null is not allowed"
    if field == "spec_version":
        return "spec_version must be present and set to '0.1'"
    if field == "version":
        return f"{rendered} must be an integer or string when provided"
    if kind == "none_required":
        return f"{rendered} must be omitted or null"
    if kind == "too_short" and field == "steps":
        return f"{rendered} must contain at least one step"
    if kind == "extra_forbidden":
        return f"{rendered} is not supported"
    if field == "kind" and kind == "literal_error":
        return f"{rendered} must be one of: {issue['ctx']['expected']}"
    if kind in {"list_type", "too_short"} or field in {
        "steps",
        "subnodes",
        "transitions",
    }:
        return f"{rendered} must be a list"
    if kind in {"model_type", "dict_type"} or field in {"metadata", "attrs", "process"}:
        return f"{rendered} must be an object"
    if kind in {
        "missing",
        "string_type",
        "string_too_short",
        "string_pattern_mismatch",
    }:
        return f"{rendered} must be a non-empty string"
    if kind == "value_error":
        return f"{rendered} {issue['msg'].removeprefix('Value error, ')}"
    return f"{rendered} has an invalid value"


def _branch_shape_message(issue: Mapping[str, Any], path: tuple) -> str:
    field = "eligible_resources" if "eligible_resources" in path else str(path[-1])
    code = {"mode": "E0216", "policy": "E0217", "eligible_resources": "E0218"}.get(
        field, "E0215"
    )
    return f"{code}: {source_path(path)} {issue['msg']}"


def _named_shape_message(issue: Mapping[str, Any], path: tuple, root: tuple) -> str:
    rendered = source_path(path)
    field = root[-1]
    if path == root:
        code = "E0202" if field == "outcomes" else "E0212"
        return f"{code}: {rendered} must be an object with at least two branches"
    if "[key]" in issue["loc"]:
        code = "E0203" if field == "outcomes" else "E0213"
        return f"{code}: {rendered} branch names must be non-empty strings"
    if path[-1] in {"target", "to"}:
        return f"E0206: {rendered} must be a non-empty string"
    transition_message = _transition_shape_message(issue, path)
    if transition_message is not None:
        return transition_message
    if issue["type"] == "model_type":
        return f"E0205: {rendered} must name a target step or define a branch object"
    return _shape_message(issue, path)


def _transition_shape_message(issue: Mapping[str, Any], path: tuple) -> str | None:
    field = str(path[-1])
    code = {
        "id": "E0207",
        "label": "E0207",
        "route": "E0207",
        "outcome": "E0208",
        "handoff": "E0209",
        "rework": "E0209",
    }.get(field)
    if code is None:
        return None
    expected = "an object" if code == "E0209" else "a non-empty string"
    return f"{code}: {source_path(path)} must be {expected} when provided"
