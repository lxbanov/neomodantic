![neomodel](https://raw.githubusercontent.com/neo4j-contrib/neomodel/master/doc/source/_static/neomodel-300.png)

An Object Graph Mapper (OGM) for the [neo4j](https://neo4j.com/) graph
database, built on the awesome
[neo4j_driver](https://github.com/neo4j/neo4j-python-driver)

If you need assistance with neomodel, please create an issue on the
GitHub repo found at <https://github.com/neo4j-contrib/neomodel/>.

-   Familiar class based model definitions with proper inheritance.
-   Powerful query API.
-   Schema enforcement through cardinality restrictions.
-   Full transaction support.
-   Thread safe.
-   Pre/post save/delete hooks.
-   Django integration via
    [django_neomodel](https://github.com/neo4j-contrib/django-neomodel)

[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=neo4j-contrib_neomodel&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=neo4j-contrib_neomodel)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=neo4j-contrib_neomodel&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=neo4j-contrib_neomodel)
[![Documentation Status](https://readthedocs.org/projects/neomodel/badge/?version=latest)](https://neomodel.readthedocs.io/en/latest/?badge=latest)

# Requirements

**For neomodel releases 5.x :**

-   Python 3.7+
-   Neo4j 5.x, 4.4 (LTS)

**For neomodel releases 4.x :**

-   Python 3.7 -\> 3.10
-   Neo4j 4.x (including 4.4 LTS for neomodel version 4.0.10)

# Documentation

Available on
[readthedocs](http://neomodel.readthedocs.org).

# Upcoming breaking changes notice - \>=5.3

Based on Python version [status](https://devguide.python.org/versions/),
neomodel will be dropping support for Python 3.7 in an upcoming release
(5.3 or later). This does not mean neomodel will stop working on Python 3.7, but
it will no longer be tested against it. Instead, we will try to add
support for Python 3.12.

Another source of upcoming breaking changes is the addition async support to
neomodel. No date is set yet, but the work has progressed a lot in the past weeks ;
and it will be part of a major release.
You can see the progress in [this branch](https://github.com/neo4j-contrib/neomodel/tree/task/async).

Finally, we are looking at refactoring some standalone methods into the
Database() class. More to come on that later.

# Installation

Install from pypi (recommended):

    $ pip install neomodel ($ source dev # To install all things needed in a Python3 venv)

    # Neomodel has some optional dependencies (including Shapely), to install these use:

    $ pip install neomodel['extras']

To install from github:

    $ pip install git+git://github.com/neo4j-contrib/neomodel.git@HEAD#egg=neomodel-dev

# Contributing

Ideas, bugs, tests and pull requests always welcome. Please use
GitHub\'s Issues page to track these.

If you are interested in developing `neomodel` further, pick a subject
from the Issues page and open a Pull Request (PR) for it. If you are
adding a feature that is not captured in that list yet, consider if the
work for it could also contribute towards delivering any of the existing
issues too.

## Running the test suite

Make sure you have a Neo4j database version 4 or higher to run the tests
on.:

    $ export NEO4J_BOLT_URL=bolt://<username>:<password>@localhost:7687 # check your username and password

Ensure `dbms.security.auth_enabled=true` in your database configuration
file. Setup a virtual environment, install neomodel for development and
run the test suite: :

    $ pip install -e '.[dev,pandas,numpy]'
    $ pytest

The tests in \"test_connection.py\" will fail locally if you don\'t
specify the following environment variables:

    $ export AURA_TEST_DB_USER=username
    $ export AURA_TEST_DB_PASSWORD=password
    $ export AURA_TEST_DB_HOSTNAME=url

If you are running a neo4j database for the first time the test suite
will set the password to \'test\'. If the database is already populated,
the test suite will abort with an error message and ask you to re-run it
with the `--resetdb` switch. This is a safeguard to ensure that the test
suite does not accidentally wipe out a database if you happen to not
have restarted your Neo4j server to point to a (usually named)
`debug.db` database.

If you have `docker-compose` installed, you can run the test suite
against all supported Python interpreters and neo4j versions: :

    # in the project's root folder:
    $ sh ./tests-with-docker-compose.sh

## Developing with async

### Transpiling async -> sync

We use [this great library](https://github.com/python-trio/unasync) to automatically transpile async code into its sync version.

In other words, when contributing to neomodel, only update the `async` code in `neomodel/async_`, then run : :

    bin/make-unasync
    isort .
    black .

Note that you can also use the pre-commit hooks for this.

### Specific async/sync code
This transpiling script mainly does two things :

- It removes the await keywords, and the Async prefixes in class names
- It does some specific replacements, like `adb`->`db`, `mark_async_test`->`mark_sync_test`

It might be that your code should only be run for `async`, or `sync` ; or you want different stubs to be run for `async` vs `sync`.
You can use the following utility function for this - taken from the official [Neo4j python driver code](https://github.com/neo4j/neo4j-python-driver) :

    # neomodel/async_/core.py
    from neomodel._async_compat.util import AsyncUtil

    # AsyncUtil.is_async_code is always True
    if AsyncUtil.is_async_code:
        # Specific async code
        # This one gets run when in async mode
        assert await Coffee.nodes.check_contains(2)
    else:
        # Specific sync code
        # This one gest run when in sync mode
        assert 2 in Coffee.nodes

You can check [test_match_api](test/async_/test_match_api.py) for some good examples, and how it's transpiled into sync.

