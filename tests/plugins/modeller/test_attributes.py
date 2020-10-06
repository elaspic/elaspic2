import pytest

import tkpod.plugins.modeller


@pytest.mark.parametrize("attribute", ["__version__"])
def test_attribute(attribute):
    assert getattr(tkpod.plugins.modeller, attribute)


def test_main():
    import tkpod.plugins.modeller

    assert tkpod.plugins.modeller
