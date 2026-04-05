import click
import json
import os
from datetime import date, datetime
from palinode.core.config import config
from palinode.cli._format import print_result, get_default_format, OutputFormat


def _resolve_memory_path(file_path: str) -> tuple[str, str]:
    """Resolve a relative memory path without allowing traversal outside memory_dir."""
    if "\x00" in file_path:
        raise click.ClickException("Null bytes are not allowed in paths")
    if os.path.isabs(file_path):
        raise click.ClickException("Absolute paths are not allowed")

    base_dir = os.path.realpath(config.memory_dir)
    resolved = os.path.realpath(os.path.join(base_dir, file_path))
    try:
        within_root = os.path.commonpath([base_dir, resolved]) == base_dir
    except ValueError as exc:
        raise click.ClickException("Invalid path") from exc
    if not within_root:
        raise click.ClickException("Path traversal rejected")
    return base_dir, resolved


@click.command()
@click.argument("file_path")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default=None, help="Output format")
@click.option("--meta/--no-meta", default=False, help="Include YAML frontmatter metadata as structured JSON")
def read(file_path, fmt, meta):
    """Read a specific memory file.

    FILE_PATH is relative to the memory directory (e.g., "people/peter.md", "decisions/cli-pivot.md").

    Examples:

        palinode read people/peter.md

        palinode read projects/palinode-status.md --meta --format json
    """
    _, full_path = _resolve_memory_path(file_path)

    if not os.path.exists(full_path):
        if not file_path.endswith(".md"):
            file_path = f"{file_path}.md"
            _, full_path = _resolve_memory_path(file_path)
        if not os.path.exists(full_path):
            raise click.ClickException(f"File not found: {file_path}")

    with open(full_path, "r") as f:
        content = f.read()

    if meta:
        # Parse frontmatter
        frontmatter = {}
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    import yaml
                    frontmatter = yaml.safe_load(parts[1]) or {}
                except Exception:
                    pass
                body = parts[2].strip()

        result = {
            "file": file_path,
            "path": full_path,
            "frontmatter": frontmatter,
            "content": body,
            "size_bytes": os.path.getsize(full_path),
        }
        effective_fmt = OutputFormat(fmt) if fmt else get_default_format()
        if effective_fmt == OutputFormat.JSON:
            click.echo(json.dumps(result, indent=2, default=_json_default))
        else:
            click.echo(_format_with_meta(result))
    else:
        if fmt == "json":
            result = {
                "file": file_path,
                "content": content,
                "size_bytes": os.path.getsize(full_path),
            }
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(content)


def _json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)


def _format_with_meta(result):
    lines = []
    if result.get("frontmatter"):
        lines.append("── Frontmatter ──")
        for k, v in result["frontmatter"].items():
            lines.append(f"  {k}: {v}")
        lines.append("")
    lines.append("── Content ──")
    lines.append(result["content"])
    return "\n".join(lines)
