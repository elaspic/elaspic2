import pytest

import tkpod.plugins.rosetta_ddg


@pytest.mark.parametrize("attribute", ["__version__"])
def test_attribute(attribute):
    assert getattr(tkpod.plugins.rosetta_ddg, attribute)


def test_main():
    import tkpod.plugins.rosetta_ddg

    assert tkpod.plugins.rosetta_ddg
