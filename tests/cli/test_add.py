"""Tests for gaia add command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from gaia.cli._registry import RegistryVersion
from gaia.cli.main import app

runner = CliRunner()

MOCK_VERSION = RegistryVersion(
    version="4.0.5",
    repo="https://github.com/kunyuan/GalileoFallingBodies.gaia",
    git_tag="v4.0.5",
    git_sha="dac84fc722bf81398a7e77c830a60b2b068de18a",
    ir_hash="sha256:abc123",
)


@patch("gaia.cli.commands.add.resolve_package", return_value=MOCK_VERSION)
@patch("gaia.cli.commands.add._run_uv")
def test_add_installs_with_git_url(mock_uv, mock_resolve):
    mock_uv.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["add", "galileo-falling-bodies-gaia"])
    assert result.exit_code == 0, f"Failed: {result.output}"
    mock_resolve.assert_called_once()
    uv_args = mock_uv.call_args[0][0]
    assert "git+" in uv_args[2]
    assert "dac84fc7" in uv_args[2]


@patch("gaia.cli.commands.add.resolve_package", return_value=MOCK_VERSION)
@patch("gaia.cli.commands.add._run_uv")
def test_add_with_version(mock_uv, mock_resolve):
    mock_uv.return_value = MagicMock(returncode=0)
    result = runner.invoke(app, ["add", "galileo-falling-bodies-gaia", "--version", "4.0.5"])
    assert result.exit_code == 0
    mock_resolve.assert_called_once_with(
        "galileo-falling-bodies-gaia",
        version="4.0.5",
        registry="SiliconEinstein/gaia-registry",
    )


@patch("gaia.cli.commands.add.resolve_package")
def test_add_not_found(mock_resolve):
    from gaia.cli._packages import GaiaCliError

    mock_resolve.side_effect = GaiaCliError("Not found in registry: packages/no-such/Package.toml")
    result = runner.invoke(app, ["add", "no-such-gaia"])
    assert result.exit_code != 0
    assert "Not found" in result.output
