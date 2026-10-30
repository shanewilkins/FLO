"""Validation helpers for structural graph constraints in FLO IR."""

from __future__ import annotations

from collections.abc import Mapping

from flo.errors import ValidationError
from flo.process.graph import GraphFacts

from .models import IR


def validate_parallel_structure(
    obj: IR,
    incoming_counts: Mapping[str, int],
    outgoing_counts: Mapping[str, int],
    graph: GraphFacts,
) -> None:
    """Validate structural constraints for explicit parallel split/join nodes."""
    split_ids = [
        node.id for node in obj.nodes if (node.type or "").lower() == "parallel_split"
    ]
    join_ids = {
        node.id for node in obj.nodes if (node.type or "").lower() == "parallel_join"
    }

    if not split_ids and not join_ids:
        return

    _validate_parallel_splits(
        split_ids=split_ids,
        join_ids=join_ids,
        outgoing_counts=outgoing_counts,
        graph=graph,
    )
    _validate_parallel_joins(
        split_ids=split_ids,
        join_ids=join_ids,
        incoming_counts=incoming_counts,
        graph=graph,
    )


def _validate_parallel_splits(
    *,
    split_ids: list[str],
    join_ids: set[str],
    outgoing_counts: Mapping[str, int],
    graph: GraphFacts,
) -> None:
    for split_id in split_ids:
        if outgoing_counts.get(split_id, 0) < 2:
            raise ValidationError(
                f"E1011: parallel_split node '{split_id}' must have at least two outgoing edges"
            )

        reachable_from_split = graph.reachable([split_id])
        if not any(candidate in join_ids for candidate in reachable_from_split):
            raise ValidationError(
                f"E1012: parallel_split node '{split_id}' must reach at least one parallel_join node"
            )


def _validate_parallel_joins(
    *,
    split_ids: list[str],
    join_ids: set[str],
    incoming_counts: Mapping[str, int],
    graph: GraphFacts,
) -> None:
    for join_id in join_ids:
        if incoming_counts.get(join_id, 0) < 2:
            raise ValidationError(
                f"E1013: parallel_join node '{join_id}' must have at least two incoming edges"
            )

        upstream_for_join = graph.reachable([join_id], reverse=True)
        if not any(candidate in split_ids for candidate in upstream_for_join):
            raise ValidationError(
                f"E1014: parallel_join node '{join_id}' must be reachable from at least one parallel_split node"
            )
