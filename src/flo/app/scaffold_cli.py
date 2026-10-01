"""Click adapter for FLO starter-model scaffolding."""

from __future__ import annotations

import click

from flo.app.scaffold import SUPPORTED_TEMPLATES, create_model, model_path


@click.command("new")
@click.argument("path", required=False, type=click.Path(path_type=str))
@click.option(
    "--template",
    type=click.Choice(SUPPORTED_TEMPLATES),
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
@click.option(
    "--list-templates",
    is_flag=True,
    help="List maintained starter templates and exit.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview the normalized target without writing a file.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Explicitly replace an existing target file.",
)
def new_cmd(
    path: str | None,
    template: str,
    process_name: str,
    list_templates: bool,
    dry_run: bool,
    force: bool,
) -> None:
    """Create a valid starter .flo model without implicit overwrite."""
    if list_templates:
        if path is not None:
            raise click.UsageError("PATH cannot be used with --list-templates.")
        click.echo("\n".join(SUPPORTED_TEMPLATES))
        return
    if path is None:
        raise click.UsageError("PATH is required unless --list-templates is used.")
    target = model_path(path)
    if dry_run:
        click.echo(f"Would create {target}")
        return
    try:
        target = create_model(
            path,
            template=template,
            process_name=process_name,
            overwrite=force,
        )
    except FileExistsError as exc:
        raise click.ClickException(
            f"'{path}' already exists; choose another path."
        ) from exc
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Created {target}")
