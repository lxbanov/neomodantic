import builtins
from test._async_compat import mark_async_test

import pytest
from neo4j.exceptions import ClientError as CypherError
from numpy import ndarray
from pandas import DataFrame, Series

from neomodantic import AsyncStructuredNode, StringProperty, adb
from neomodantic._async_compat.util import AsyncUtil


class User2(AsyncStructuredNode):
    name = StringProperty()
    email = StringProperty()


class UserPandas(AsyncStructuredNode):
    name = StringProperty()
    email = StringProperty()


class UserNP(AsyncStructuredNode):
    name = StringProperty()
    email = StringProperty()


@pytest.fixture
def hide_available_pkg(monkeypatch, request):
    import_orig = builtins.__import__

    def mocked_import(name, *args, **kwargs):
        if name == request.param:
            raise ImportError()
        return import_orig(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mocked_import)


@mark_async_test
async def test_cypher():
    """
    test result format is backward compatible with earlier versions of neomodel
    """

    jim = await User2(email="jim1@test.com").save()
    data, meta = await jim.cypher(
        f"MATCH (a) WHERE {await adb.get_id_method()}(a)=$self RETURN a.email"
    )
    assert data[0][0] == "jim1@test.com"
    assert "a.email" in meta

    data, meta = await jim.cypher(
        f"""
            MATCH (a) WHERE {await adb.get_id_method()}(a)=$self
            MATCH (a)<-[:USER2]-(b)
            RETURN a, b, 3
        """
    )
    assert "a" in meta and "b" in meta


@mark_async_test
async def test_cypher_syntax_error():
    jim = await User2(email="jim1@test.com").save()
    try:
        await jim.cypher(
            f"MATCH a WHERE {await adb.get_id_method()}(a)={{self}} RETURN xx"
        )
    except CypherError as e:
        assert hasattr(e, "message")
        assert hasattr(e, "code")
    else:
        assert False, "CypherError not raised."


@mark_async_test
@pytest.mark.parametrize("hide_available_pkg", ["pandas"], indirect=True)
async def test_pandas_not_installed(hide_available_pkg):
    # We run only the async version, because this fails on second run
    # because import error is thrown only when pandas.py is imported
    if not AsyncUtil.is_async_code:
        pytest.skip("This test is async only")
    with pytest.raises(ImportError):
        with pytest.warns(
            UserWarning,
            match="The neomodel.integration.pandas module expects pandas to be installed",
        ):
            from neomodantic.integration.pandas import to_dataframe

            _ = to_dataframe(await adb.cypher_query("MATCH (a) RETURN a.name AS name"))


@mark_async_test
async def test_pandas_integration():
    from neomodantic.integration.pandas import to_dataframe, to_series

    jimla = await UserPandas(email="jimla@test.com", name="jimla").save()
    jimlo = await UserPandas(email="jimlo@test.com", name="jimlo").save()

    # Test to_dataframe
    df = to_dataframe(
        await adb.cypher_query(
            "MATCH (a:UserPandas) RETURN a.name AS name, a.email AS email ORDER BY name"
        )
    )

    assert isinstance(df, DataFrame)
    assert df.shape == (2, 2)
    assert df["name"].tolist() == ["jimla", "jimlo"]

    # Also test passing an index and dtype to to_dataframe
    df = to_dataframe(
        await adb.cypher_query(
            "MATCH (a:UserPandas) RETURN a.name AS name, a.email AS email ORDER BY name"
        ),
        index=df["email"],
        dtype=str,
    )

    assert df.index.inferred_type == "string"

    # Next test to_series
    series = to_series(
        await adb.cypher_query(
            "MATCH (a:UserPandas) RETURN a.name AS name ORDER BY name"
        )
    )

    assert isinstance(series, Series)
    assert series.shape == (2,)
    assert df["name"].tolist() == ["jimla", "jimlo"]


@mark_async_test
@pytest.mark.parametrize("hide_available_pkg", ["numpy"], indirect=True)
async def test_numpy_not_installed(hide_available_pkg):
    # We run only the async version, because this fails on second run
    # because import error is thrown only when numpy.py is imported
    if not AsyncUtil.is_async_code:
        pytest.skip("This test is async only")
    with pytest.raises(ImportError):
        with pytest.warns(
            UserWarning,
            match="The neomodel.integration.numpy module expects numpy to be installed",
        ):
            from neomodantic.integration.numpy import to_ndarray

            _ = to_ndarray(
                await adb.cypher_query("MATCH (a) RETURN a.name AS name ORDER BY name")
            )


@mark_async_test
async def test_numpy_integration():
    from neomodantic.integration.numpy import to_ndarray

    jimly = await UserNP(email="jimly@test.com", name="jimly").save()
    jimlu = await UserNP(email="jimlu@test.com", name="jimlu").save()

    array = to_ndarray(
        await adb.cypher_query(
            "MATCH (a:UserNP) RETURN a.name AS name, a.email AS email ORDER BY name"
        )
    )

    assert isinstance(array, ndarray)
    assert array.shape == (2, 2)
    assert array[0][0] == "jimlu"
