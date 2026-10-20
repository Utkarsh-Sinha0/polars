import pytest

import polars as pl
from polars.testing import assert_series_equal


def test_extend() -> None:
    a = pl.Series("a", [1, 2])
    b = pl.Series("b", [8, 9, None])

    result = a.extend(b)

    expected = pl.Series("a", [1, 2, 8, 9, None])
    assert_series_equal(a, expected)
    assert_series_equal(result, expected)
    assert a.n_chunks() == 1


def test_extend_self() -> None:
    a = pl.Series("a", [1, 2])

    a.extend(a)

    expected = pl.Series("a", [1, 2, 1, 2])
    assert_series_equal(a, expected)
    assert a.n_chunks() == 1


def test_extend_bad_input() -> None:
    a = pl.Series("a", [1, 2])
    b = a.to_frame()

    with pytest.raises(
        TypeError,
        match=r"expected `other` .*to be a 'Series'.* not 'DataFrame'",
    ):
        a.extend(b)  # type: ignore[arg-type]

    with pytest.raises(
        TypeError,
        match=r"expected `other` .*to be a 'Series'.* not 'LazyFrame'",
    ):
        a.extend(b.lazy())  # type: ignore[arg-type]


def test_extend_with_null_series() -> None:
    a = pl.Series("a", [1, 2], pl.Int64)
    b = pl.Series("b", [None, None], pl.Null)

    result = a.extend(b)

    expected = pl.Series("a", [1, 2, None, None], pl.Int64)
    assert_series_equal(a, expected)
    assert_series_equal(result, expected)
    assert a.n_chunks() == 1


def test_extend_sliced_12968() -> None:
    assert pl.Series(["a", "b"]).slice(0, 1).extend(pl.Series(["c"])).to_list() == [
        "a",
        "c",
    ]


@pytest.mark.parametrize("offset", [0, 1, 8, 61, 64])
@pytest.mark.parametrize("values", [[False, True, False], [False, None, True]])
@pytest.mark.parametrize("extra", [[], [False], [None, True]])
@pytest.mark.parametrize("shared", [False, True])
def test_extend_boolean_offset_slice_30105(
    offset: int,
    values: list[bool | None],
    extra: list[bool | None],
    shared: bool,
) -> None:
    parent = pl.Series("a", [True] * offset + values, dtype=pl.Boolean)
    result = parent.slice(offset)
    if not shared:
        del parent

    result.extend(pl.Series(extra, dtype=pl.Boolean))

    assert_series_equal(result, pl.Series("a", values + extra, dtype=pl.Boolean))
    if shared:
        assert parent.to_list() == [True] * offset + values
