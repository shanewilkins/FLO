"""Adapt strict local contracts at the explicit canonical IR validation boundary."""

from typing import Any, Literal

from pydantic import TypeAdapter
from pydantic import ValidationError as ContractError

from flo.errors import ValidationError
from flo.process.contracts import (
    BranchConfig,
    HandoffRelation,
    NonBlank,
    ReworkRelation,
    ValueClass,
)

from .models import IR

_RELATIONS = TypeAdapter(list[NonBlank], config={"strict": True})
_VALUE_CLASS = TypeAdapter(ValueClass, config={"strict": True})
_PROCESS_IDENTITY = TypeAdapter(
    dict[Literal["process_id", "process_name"], NonBlank], config={"strict": True}
)


def validate_process_identity(metadata: Any) -> None:
    """Reject retired semantic metadata in internal identity context."""
    if metadata is not None:
        try:
            _PROCESS_IDENTITY.validate_python(metadata)
        except ContractError as exc:
            raise ValidationError(
                "E1201: process_metadata accepts only process_id/process_name; use first-class process fields and extensions"
            ) from exc


def validate_node_relations(obj: IR) -> None:
    """Check local list/classification constraints using the shared contracts."""
    for node in obj.nodes:
        for field in ("consumes", "produces", "performed_by", "uses"):
            try:
                _RELATIONS.validate_python(getattr(node, field))
            except ContractError as exc:
                code = "E1310" if exc.errors()[0]["type"] == "list_type" else "E1311"
                raise ValidationError(
                    f"{code}: node '{node.id}' {field} must be a list of non-empty strings"
                ) from exc
        if node.value_class is not None:
            try:
                _VALUE_CLASS.validate_python(node.value_class)
            except ContractError as exc:
                raise ValidationError(
                    f"E1320: node '{node.id}' value_class must be VA, RNVA, NVA or unknown"
                ) from exc


def validate_edge_relations(obj: IR) -> None:
    """Check supplied structured relation shapes without rewriting evidence."""
    for edge in obj.edges:
        for field, contract in (
            ("handoff", HandoffRelation),
            ("rework", ReworkRelation),
        ):
            value = getattr(edge, field)
            if value is not None:
                try:
                    contract.model_validate(value)
                except ContractError as exc:
                    raise ValidationError(
                        f"E1401: edge '{edge.source}' -> '{edge.target}' {field} must be a valid structured relation"
                    ) from exc


def validate_branch_config(node_id: str, config: Any) -> None:
    """Use the authored branch contract for direct canonical input too."""
    try:
        BranchConfig.model_validate(config)
    except ContractError as exc:
        issue = exc.errors()[0]
        code = "E1030" if issue["loc"] == ("mode",) else "E1029"
        raise ValidationError(
            f"{code}: branch node '{node_id}' must declare a valid branch.mode and configuration"
        ) from exc
