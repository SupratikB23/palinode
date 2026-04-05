from click.testing import CliRunner

from palinode.cli import main


class FakeProcess:
    created_targets = []

    def __init__(self, target, daemon):
        self.target = target
        self.daemon = daemon
        self.started = False
        FakeProcess.created_targets.append(target)

    def start(self):
        self.started = True

    def join(self, timeout=None):
        return None

    def is_alive(self):
        return False

    def terminate(self):
        return None


def test_start_without_services_returns_cleanly():
    runner = CliRunner()
    result = runner.invoke(main, ["start", "--no-api", "--no-watcher"])
    assert result.exit_code == 0
    assert "No services specified" in result.output


def test_start_uses_existing_service_entrypoints(monkeypatch):
    FakeProcess.created_targets = []
    monkeypatch.setattr("multiprocessing.Process", FakeProcess)

    runner = CliRunner()
    result = runner.invoke(main, ["start", "--api", "--no-watcher"])

    assert result.exit_code == 0
    assert "Starting API server" in result.output
    assert len(FakeProcess.created_targets) == 1
    assert FakeProcess.created_targets[0].__module__ == "palinode.api.server"
