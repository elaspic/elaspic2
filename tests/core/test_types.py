import pytest
from kmtools.structure_tools import DomainMutation as Mutation


@pytest.mark.parametrize("mutation_str, mutation_obj_", [("M1A", Mutation(0, "", "M", 1, "A"))])
def test_mutation_from_string(mutation_str, mutation_obj_):
    mutation_obj = Mutation.from_string(mutation_str)
    assert mutation_obj == mutation_obj_
