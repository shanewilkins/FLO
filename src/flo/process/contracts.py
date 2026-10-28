"""Pydantic boundary contracts for FLO-owned process semantics."""

from __future__ import annotations

import json
import math
from typing import Annotated, Any, Literal, TypeGuard

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    TypeAdapter,
    model_validator,
)

from .field_applicability import inapplicable_fields

NonBlank = Annotated[str, StringConstraints(pattern=r"\S")]
NonNegativeNumber = Annotated[int | float, Field(ge=0)]
PositiveInteger = Annotated[int, Field(gt=0)]

MeasurementBasis = Literal["observed", "simulated", "estimated", "planned", "target"]
CoreMeasurementMethod = Literal[
    "count",
    "sum",
    "minimum",
    "maximum",
    "mean",
    "median",
    "mode",
    "percentile",
    "standard_deviation",
]
NamespacedMeasurementMethod = Annotated[
    str, StringConstraints(pattern=r"^[a-z][a-z0-9_.-]*:[a-z][a-z0-9_.-]*$")
]
ValueClass = Literal["VA", "RNVA", "NVA", "unknown"]
HandoffType = Literal[
    "responsibility",
    "information",
    "material",
    "system",
    "location",
    "mixed",
]


class ContractModel(BaseModel):
    """Strict FLO contract object with no implicit extension fields."""

    model_config = ConfigDict(strict=True, extra="forbid")


def _is_finite_number(value: object) -> TypeGuard[int | float]:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _json_extensions(value: Any) -> Any:
    """Require portable JSON annotations, including finite nested numbers."""
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("extensions must contain finite JSON data") from exc
    return value


type Extensions = Annotated[dict[str, JsonValue], BeforeValidator(_json_extensions)]


class MeasurementResult(ContractModel):
    """One named statistical result within a measurement profile."""

    method: CoreMeasurementMethod | NamespacedMeasurementMethod
    value: NonNegativeNumber | NonBlank | list[Any]
    unit: NonBlank
    parameters: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_value(self) -> MeasurementResult:
        """Reject non-finite numeric evidence and incomplete percentiles."""
        if isinstance(self.value, (int, float)) and not _is_finite_number(self.value):
            raise ValueError("value must be finite and nonnegative")
        if self.method == "percentile":
            percentile = (self.parameters or {}).get("percentile")
            if not _is_finite_number(percentile) or not 0 <= percentile <= 100:
                raise ValueError(
                    "percentile results require parameters.percentile between 0 and 100"
                )
        return self


class MeasurementProfile(ContractModel):
    """A supplied measurement profile with explicit evidence and selectors."""

    basis: MeasurementBasis
    results: Annotated[dict[NonBlank, MeasurementResult], Field(min_length=1)]
    primary: NonBlank
    analysis_input: NonBlank | None = None
    observation_count: PositiveInteger | None = None
    observation_unit: NonBlank | None = None
    cohort: NonBlank | None = None
    aggregation_level: NonBlank | None = None
    observation_window: NonBlank | None = None
    evidence_ref: NonBlank | None = None
    extensions: Extensions | None = None

    @model_validator(mode="after")
    def validate_selectors(self) -> MeasurementProfile:
        """Require presentation and analysis selectors to resolve by name."""
        if self.primary not in self.results:
            raise ValueError("primary must reference a named result")
        if self.analysis_input is not None and self.analysis_input not in self.results:
            raise ValueError("analysis_input must reference a named result")
        if (self.observation_count is None) != (self.observation_unit is None):
            raise ValueError(
                "observation_count and observation_unit must be supplied together"
            )
        return self


class MeasurementReference(ContractModel):
    """A reference to a measurement owned by another process step."""

    ref: Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_.-]+\.[a-z_]+$")]


type Measurement = MeasurementProfile | MeasurementReference
MEASUREMENT_ADAPTER = TypeAdapter(Measurement)


class HandoffRelation(ContractModel):
    """An explicit transfer of responsibility, information, or custody."""

    type: HandoffType | None = None
    extensions: Extensions | None = None


class ReworkFrequency(ContractModel):
    """Observed rework frequency with an explicit denominator."""

    basis: MeasurementBasis
    numerator: NonNegativeNumber
    denominator: PositiveInteger
    observation_unit: NonBlank
    evidence_ref: NonBlank | None = None

    @model_validator(mode="before")
    @classmethod
    def finite_counts(cls, value: Any) -> Any:
        """Reject overflow before Pydantic attempts numeric union conversion."""
        if isinstance(value, dict):
            for key in ("numerator", "denominator"):
                count = value.get(key)
                if isinstance(count, (int, float)) and not _is_finite_number(count):
                    raise ValueError("frequency counts must be finite numbers")
        return value

    @model_validator(mode="after")
    def validate_fraction(self) -> ReworkFrequency:
        """Require the affected count not to exceed its population."""
        if not _is_finite_number(self.numerator) or not _is_finite_number(
            self.denominator
        ):
            raise ValueError("frequency counts must be finite")
        if self.numerator > self.denominator:
            raise ValueError("numerator must not exceed denominator")
        return self


class ReworkRelation(ContractModel):
    """An explicit correction or repetition relationship."""

    reason: NonBlank | None = None
    frequency: ReworkFrequency | None = None
    note: NonBlank | None = None
    extensions: Extensions | None = None


class CanonicalNodeContract(ContractModel):
    """Generated-schema boundary for one flattened canonical node."""

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
    name: NonBlank | None = None
    description: NonBlank | None = None
    lane: NonBlank | None = None
    location: NonBlank | None = None
    subprocess_parent: NonBlank | None = None
    branch: dict[str, Any] | None = None
    consumes: list[NonBlank] | None = None
    produces: list[NonBlank] | None = None
    performed_by: list[NonBlank] | None = None
    uses: list[NonBlank] | None = None
    value_class: ValueClass | None = None
    cycle_time: Measurement | None = None
    wait_time: Measurement | None = None
    changeover_time: Measurement | None = None
    extensions: Extensions | None = None

    @model_validator(mode="after")
    def validate_applicability(self) -> CanonicalNodeContract:
        """Apply the same semantic field matrix to canonical exchange input."""
        forbidden = inapplicable_fields(self.kind, set(self.model_fields_set))
        if forbidden:
            raise ValueError(
                f"{', '.join(sorted(forbidden))} cannot be declared on kind '{self.kind}'"
            )
        return self


class CanonicalEdgeContract(ContractModel):
    """Generated-schema boundary for one canonical transition."""

    source: NonBlank
    target: NonBlank
    id: NonBlank | None = None
    outcome: NonBlank | None = None
    route: NonBlank | None = None
    label: NonBlank | None = None
    handoff: HandoffRelation | None = None
    rework: ReworkRelation | None = None
    extensions: Extensions | None = None


class CanonicalIdentityContract(ContractModel):
    """Named identity used by process context and lanes."""

    id: NonBlank
    name: NonBlank
    type: Literal["role", "team", "system"] | None = None
    extensions: Extensions | None = None


class CountQuantity(ContractModel):
    """An integral count of indivisible entities."""

    kind: Literal["count"]
    value: PositiveInteger
    unit: Literal["each"] | None = None
    qualifier: str | None = None


class MeasureQuantity(ContractModel):
    """A measured amount; dimensional equivalence remains domain-owned."""

    kind: Literal["measure"]
    value: Annotated[int | float, Field(gt=0, allow_inf_nan=False)]
    unit: NonBlank
    canonical_value: Annotated[int | float, Field(gt=0, allow_inf_nan=False)] | None = (
        None
    )
    canonical_unit: NonBlank | None = None


type Quantity = Annotated[CountQuantity | MeasureQuantity, Field(discriminator="kind")]


class EntityContract(ContractModel):
    """Common identity and optional supplied amount for declared entities."""

    id: NonBlank
    name: NonBlank
    quantity: Quantity | None = None
    extensions: Extensions | None = None


class ItemContract(EntityContract):
    """A material or information object flowing through work."""

    kind: Literal["material", "information"]


class ResourceContract(EntityContract):
    """A person or equipment resource used by work."""

    kind: Literal["person", "equipment"]


class SpatialContract(ContractModel):
    """Coordinates whose physical unit compatibility is domain-owned."""

    x: Annotated[int | float, Field(allow_inf_nan=False)]
    y: Annotated[int | float, Field(allow_inf_nan=False)]
    unit: NonBlank | None = None


class LocationMetadata(ContractModel):
    """Existing explicit spatial container, pending compatibility removal."""

    spatial: SpatialContract | None = None


class LocationContract(EntityContract):
    """A named operational place with optional spatial evidence."""

    kind: NonBlank | None = None
    metadata: LocationMetadata | None = None
    x: Annotated[int | float, Field(allow_inf_nan=False)] | None = None
    y: Annotated[int | float, Field(allow_inf_nan=False)] | None = None
    unit: NonBlank | None = None


class EntityGroup[T](BaseModel):
    """A labeled group containing nested groups or entity lists."""

    model_config = ConfigDict(strict=True, extra="allow")
    # Pydantic's documented typed-extra hook narrows BaseModel's writable Any slot.
    __pydantic_extra__: dict[str, list[T] | EntityGroup[T]] = Field(init=False)  # ty: ignore[invalid-mutable-override]
    name: NonBlank | None = None

    @model_validator(mode="after")
    def validate_children(self) -> EntityGroup[T]:
        """Require actual collections and nonblank group keys."""
        if not self.__pydantic_extra__ or any(
            not key.strip() for key in self.__pydantic_extra__
        ):
            raise ValueError(
                "groups require at least one collection with a nonblank key"
            )
        return self


type EntityCollection[T] = list[T] | EntityGroup[T]


class CanonicalProcessContract(ContractModel):
    """Canonical process identity and typed process-level evidence."""

    id: NonBlank
    name: NonBlank
    version: int | str | None = None
    owner: dict[str, Any] | None = None
    business_units: list[dict[str, Any]] | None = None
    lead_time: MeasurementProfile | None = None
    items: EntityCollection[ItemContract] | None = None
    resources: EntityCollection[ResourceContract] | None = None
    locations: EntityCollection[LocationContract] | None = None
    render: dict[str, Any] | None = None
    extensions: Extensions | None = None


class CanonicalIRContract(ContractModel):
    """Generated canonical exchange contract."""

    process: CanonicalProcessContract
    nodes: Annotated[list[CanonicalNodeContract], Field(min_length=1)]
    edges: list[CanonicalEdgeContract]
    lanes: list[CanonicalIdentityContract] | None = None


__all__ = [
    "MEASUREMENT_ADAPTER",
    "CanonicalEdgeContract",
    "CanonicalIRContract",
    "CanonicalIdentityContract",
    "CanonicalNodeContract",
    "CanonicalProcessContract",
    "ContractModel",
    "HandoffRelation",
    "HandoffType",
    "Measurement",
    "MeasurementBasis",
    "MeasurementProfile",
    "MeasurementReference",
    "MeasurementResult",
    "NonBlank",
    "ReworkFrequency",
    "ReworkRelation",
    "ValueClass",
]
