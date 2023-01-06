from _balder.balder_session import BalderSession
from _balder.exceptions import VDeviceOverwritingError, BalderException

from tests.test_utilities.base_0_envtester_class import Base0EnvtesterClass


class Test0OverwriteIllegallyBefsce(Base0EnvtesterClass):
    """
    This testcase is a modified version of the basic ENVTESTER environment. It is limited to the `ScenarioA` and the
    `SetupA` and uses a feature `FeatureOfRelevance` for testing the correct overwriting of VDevices BEFORE the feature
    is being instantiated in a SCENARIO.

    This test defines a new feature `FeatureOfRelevanceLvl1` with two vDevices. This feature will be overwritten by the
    direct child `FeatureOfRelevanceLvl2`, that will be used in our scenario and also be mapped to a vDevice. Instead,
    of made as in the test `test_0_overwrite_correctly_befsce`, not all vDevices are being overwritten here.
    Of course the setup device also implements a child class (`SetupFeatureOfRelevanceLvl3`) of it.

    The test should fail on collector level, because vDevices should not be overwritten or should always be overwritten
    together!
    """
    @property
    def expected_data(self) -> tuple:
        return ()

    @property
    def expected_exit_code(self) -> int:
        return 4

    @staticmethod
    def handle_balder_exception(exc: BalderException):
        assert isinstance(exc, VDeviceOverwritingError), 'unexpected exception type'
        assert exc.args[0] == "missing overwriting of parent VDevice class `FeatureOfRelevanceLvl1.VDeviceWithII` in " \
                              "feature class `FeatureOfRelevanceLvl2` - if you overwrite one or more VDevice(s) you " \
                              "have to overwrite all!"

    @staticmethod
    def validate_finished_session(session: BalderSession):
        assert session.executor_tree is None, "test session does not terminates before collector work was done"
