import aic


def test_import_aic() -> None:
    assert aic.__version__
    assert isinstance(aic.__version__, str)
