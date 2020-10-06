import pytest

import ev2


@pytest.mark.parametrize("attribute", ["__version__"])
def test_attribute(attribute):
    assert getattr(ev2, attribute)


def test_main():
    import ev2

    assert ev2
