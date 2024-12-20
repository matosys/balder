from __future__ import annotations
from typing import Type, Union, List, Dict, TYPE_CHECKING

from _balder.fixture_execution_level import FixtureExecutionLevel
from _balder.testresult import ResultState, BranchBodyResult
from _balder.utils import get_class_that_defines_method
from _balder.executor.basic_executable_executor import BasicExecutableExecutor
from _balder.executor.variation_executor import VariationExecutor
from _balder.previous_executor_mark import PreviousExecutorMark
from _balder.controllers.scenario_controller import ScenarioController

if TYPE_CHECKING:
    from _balder.scenario import Scenario
    from _balder.executor.setup_executor import SetupExecutor
    from _balder.fixture_manager import FixtureManager


class ScenarioExecutor(BasicExecutableExecutor):
    """
    A ScenarioExecutor can contain :meth:`VariationExecutor` as children.
    """
    fixture_execution_level = FixtureExecutionLevel.SCENARIO

    def __init__(self, scenario: Type[Scenario], parent: SetupExecutor):
        super().__init__()
        self._variation_executors: List[VariationExecutor] = []
        # check if instance already exists
        if hasattr(scenario, "_instance") and scenario._instance is not None and \
                isinstance(scenario._instance, scenario):
            self._base_scenario_class = scenario._instance
        else:
            self._base_scenario_class = scenario()
            scenario._instance = self._base_scenario_class
        self._parent_executor = parent
        self._fixture_manager = parent.fixture_manager

        # contains the result object for the BODY part of this branch
        self.body_result = BranchBodyResult(self)

        # if the related scenario class of this executor is decorated with ``@covered_by``, this property contains a
        # list with the :class:`ScenarioExecutor` or/and :class:`TestcaseExecutor` that covers this one
        self.covered_by_executors = None

    # ---------------------------------- STATIC METHODS ----------------------------------------------------------------

    # ---------------------------------- CLASS METHODS ----------------------------------------------------------------

    # ---------------------------------- PROPERTIES --------------------------------------------------------------------

    @property
    def all_child_executors(self) -> List[VariationExecutor]:
        return self._variation_executors

    @property
    def parent_executor(self) -> SetupExecutor:
        return self._parent_executor

    @property
    def base_instance(self) -> object:
        """
        returns the base class instance to which this executor instance belongs
        """
        return self.base_scenario_class

    @property
    def base_scenario_class(self) -> Scenario:
        """returns the :class:`Scenario` class that belongs to this executor"""
        return self._base_scenario_class

    @property
    def base_scenario_controller(self) -> ScenarioController:
        """returns the :class:`ScenarioController` for the setup object of this executor"""
        return ScenarioController.get_for(self.base_scenario_class.__class__)

    @property
    def fixture_manager(self) -> FixtureManager:
        """returns the current active fixture manager that belongs to this scenario executor"""
        return self._fixture_manager

    @property
    def all_run_tests(self):
        """returns a list of all test methods that are declared to `RUN` in their base :class:`Scenario` class"""
        return self._base_scenario_class.RUN

    @property
    def all_skip_tests(self):
        """returns a list of all test methods that are declared to `SKIP` in their base :class:`Scenario` class"""
        return self._base_scenario_class.SKIP

    @property
    def all_ignore_tests(self):
        """returns a list of all test methods that are declared to `IGNORE` in their base :class:`Scenario` class"""
        return self._base_scenario_class.IGNORE

    # ---------------------------------- PROTECTED METHODS -------------------------------------------------------------

    def _prepare_execution(self, show_discarded):
        print(f"  SCENARIO {self.base_scenario_class.__class__.__name__}")

    def _body_execution(self, show_discarded):
        for cur_variation_executor in self.get_variation_executors(return_discarded=show_discarded):
            if cur_variation_executor.has_runnable_tests(show_discarded):
                cur_variation_executor.execute(show_discarded=show_discarded)
            elif cur_variation_executor.prev_mark == PreviousExecutorMark.SKIP:
                cur_variation_executor.set_result_for_whole_branch(ResultState.SKIP)
            elif cur_variation_executor.prev_mark == PreviousExecutorMark.COVERED_BY:
                cur_variation_executor.set_result_for_whole_branch(ResultState.COVERED_BY)
            else:
                cur_variation_executor.set_result_for_whole_branch(ResultState.NOT_RUN)

    def _cleanup_execution(self, show_discarded):
        pass

    # ---------------------------------- METHODS -----------------------------------------------------------------------

    def get_variation_executors(self, return_discarded=False) -> List[VariationExecutor]:
        """
        :param return_discarded: True if the method should return discarded variations too

        :return: returns all variation executors that are child executor of this scenario executor
        """
        if not return_discarded:
            return [cur_executor for cur_executor in self._variation_executors
                    if cur_executor.prev_mark != PreviousExecutorMark.DISCARDED]
        return self._variation_executors

    def cleanup_empty_executor_branches(self, consider_discarded=False):
        """
        This method removes all sub executors that are empty and not relevant anymore.
        """
        to_remove_executor = []
        for cur_variation_executor in self.get_variation_executors(return_discarded=consider_discarded):
            if len(cur_variation_executor.get_testcase_executors()) == 0:
                # remove this whole executor because it has no children anymore
                to_remove_executor.append(cur_variation_executor)
        for cur_variation_executor in to_remove_executor:
            self._variation_executors.remove(cur_variation_executor)

    def get_covered_by_dict(self) -> Dict[Union[Type[Scenario], callable], List[Union[Type[Scenario], callable]]]:
        """
        This method returns the complete resolved ``@covered_by`` dictionary for this scenario. It automatically
        cleans up every inheritance of the covered_by decorators for every parent class of our scenario.
        """
        def determine_most_inherited_class(class_list):
            for cur_candidate in class_list:
                candidate_is_valid = True
                for cur_other_candidate in class_list:
                    if cur_candidate == cur_other_candidate:
                        pass
                    if not issubclass(cur_candidate, cur_other_candidate):
                        candidate_is_valid = False
                        break
                if candidate_is_valid:
                    return cur_candidate
            return None

        # all data will be inherited while ``@covered_by`` overwrites elements only if there is a new decorator at the
        # overwritten method
        #  -> we have to filter the dictionary and only return the value given for highest overwritten method
        relative_covered_by_dict = {}
        if hasattr(self.base_scenario_class, '_covered_by'):
            function_name_mapping = {}
            classes = []
            for cur_key in self.base_scenario_class._covered_by.keys():
                if issubclass(cur_key, Scenario):
                    # this is a covered_by definition for the whole class
                    classes.append(cur_key)
                else:
                    # this is a covered_by definition for one test method
                    if cur_key.__name__ in function_name_mapping.keys():
                        function_name_mapping[cur_key.__name__] = [cur_key]
                    else:
                        function_name_mapping[cur_key.__name__].append(cur_key)

            # determine the highest definition for class statement (only if necessary)
            if len(classes) > 0:
                most_inherited_class = determine_most_inherited_class(classes)
                # this is the most inherited child -> add this definition
                relative_covered_by_dict[most_inherited_class] = \
                    self.base_scenario_class._covered_by[most_inherited_class]

            # determine the highest definition for every test method
            for cur_function_name, cur_possible_candidates in function_name_mapping.items():
                classes = [get_class_that_defines_method(meth) for meth in cur_possible_candidates]
                most_inherited_class = determine_most_inherited_class(classes)
                most_inherited_test_method = cur_possible_candidates[classes.index(most_inherited_class)]
                # this is the most inherited test method -> add the definition of this one and replace the method with
                # this Scenario's one
                relative_covered_by_dict[getattr(self.base_scenario_class, cur_function_name)] = \
                    self.base_scenario_class._covered_by[most_inherited_test_method]
        else:
            pass
        return relative_covered_by_dict

    def get_covered_by_element(self) -> List[Union[Scenario, callable]]:
        """
        This method returns a list of elements where the whole scenario is covered from. This means, that the whole
        test methods in this scenario are already be covered from one of the elements in the list.
        """
        covered_by_dict_resolved = self.get_covered_by_dict()
        if self in covered_by_dict_resolved.keys():
            return covered_by_dict_resolved[self]
        return []

    def add_variation_executor(self, variation_executor: VariationExecutor):
        """
        This method adds a new VariationExecutor to the child element list of the tree
        """
        if not isinstance(variation_executor, VariationExecutor):
            raise TypeError("the given object `variation_executor` must be of type `VariationExecutor`")
        if variation_executor in self._variation_executors:
            raise ValueError("the given object `variation_executor` already exists in child list")
        self._variation_executors.append(variation_executor)

    def get_executor_for_device_mapping(self, device_mapping: dict) -> Union[VariationExecutor, None]:
        """
        This method searches for a VariationExecutor in the internal list for which the given device mapping is
        contained in

        :param device_mapping: the device_mapping dictionary for which the executor should be searched for

        :return: returns the associated VariationExecutor or None if no matching could be found
        """
        for cur_variation_executor in self._variation_executors:
            if cur_variation_executor.base_device_mapping == device_mapping:
                return cur_variation_executor
        # can not find some
        return None
