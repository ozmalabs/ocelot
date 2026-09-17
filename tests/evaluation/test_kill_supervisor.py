from evaluation.p0a.control import RunControl
from evaluation.p0a.supervisor import CgroupSupervisor, LocalSupervisor
from conftest import FakeCgroupController


def test_cgroup_supervisor_timeout_kills_controller_once_and_is_terminal():
    controller = FakeCgroupController()
    scope = controller.create_scope("run")
    supervisor = CgroupSupervisor("run", scope, control=RunControl("run", last_heartbeat_ms=10))
    assert supervisor.expire_if_stale(21, 10) == "killed"
    assert controller.kills == ["heartbeat_expired"]
    assert supervisor.expire_if_stale(22, 10) == "killed"
    assert controller.kills == ["heartbeat_expired"]


def test_cgroup_supervisor_stop_kills_whole_scope_once():
    controller = FakeCgroupController()
    scope = controller.create_scope("run")
    supervisor = CgroupSupervisor("run", scope)
    assert supervisor.stop("operator_kill") == "killed"
    assert supervisor.stop("operator_kill") == "killed"
    assert controller.kills == ["operator_kill"]


def test_local_supervisor_remains_logical_dev_helper():
    supervisor = LocalSupervisor("run")
    assert supervisor.stop("operator_kill") == "killed"
