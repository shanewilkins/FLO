"""Click adapter for FLO starter-model scaffolding."""

from __future__ import annotations

import click

from flo.app.scaffold import create_model


@click.command("new")
@click.argument("path", type=click.Path(path_type=str))
@click.option(
    "--template",
    type=click.Choice(["simple-process"]),
    default="simple-process",
    show_default=True,
    help="Maintained starter model to create.",
)
@click.option(
    "--name",
    "process_name",
    default="Simple Process",
    show_default=True,
    help="Process name; FLO derives a readable stable process ID.",
)
def new_cmd(path: str, template: str, process_name: str) -> None:
    """Create a valid starter .flo model without overwriting files."""
    try:
        target = create_model(
            path,
            template=template,
            process_name=process_name,
        )
    except FileExistsError as exc:
        raise click.ClickException(
            f"'{path}' already exists; choose another path."
        ) from exc
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Created {target}")
