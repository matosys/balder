from multiprocessing import Process
from balder.exceptions import DeviceOverwritingError
from _balder.balder_session import BalderSession


def test_0_setup_inheritance_missing_device_inheritance(balder_working_dir):
    """
    This testcase executes a reduced version of the basic envtester environment. It only implements the `ScenarioA` and
    its related `SetupA` and a child class of the related `SetupA`.

    The child class define both devices, but inherits only from one device correctly.

    .. note::
        The `SetupAParent` class has a child (the `SetupAChild` class). This forbids the execution of the
        `SetupAParent` class.
    """
    proc = Process(target=processed, args=(balder_working_dir, ))
    proc.start()
    proc.join()
    assert proc.exitcode == 0, "the process terminates with an error"


def processed(env_dir):

    print("\n", flush=True)
    session = BalderSession(cmd_args=[], working_dir=env_dir)
    try:
        session.run()
        print("\n")
        assert False, "test session terminates without an error"
    except DeviceOverwritingError as exc:
        assert exc.args[0] == "the inner device class `SetupAChild.SetupDevice2` has the same name than the device " \
                              "`SetupAParent.SetupDevice2` - it should also inherit from it"

    assert session.executor_tree is None, "test session does not terminates before collector work was done"
