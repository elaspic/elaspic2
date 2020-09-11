import pytest

import elaspic_v2


@pytest.mark.parametrize("attribute", ["__version__"])
def test_attribute(attribute):
    assert getattr(elaspic_v2, attribute)


def test_main():
    import elaspic_v2

    assert elaspic_v2
