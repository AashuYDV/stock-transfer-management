import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.test.utils import setup_test_environment, teardown_test_environment  # noqa: E402
from django.test.runner import DiscoverRunner  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def django_db_setup():
    setup_test_environment()
    runner = DiscoverRunner()
    old_config = runner.setup_databases()
    yield
    runner.teardown_databases(old_config)
    teardown_test_environment()


@pytest.fixture(autouse=True)
def _wrap_each_test_in_transaction():
    from django.db import transaction

    with transaction.atomic():
        sid = transaction.savepoint()
        yield
        transaction.savepoint_rollback(sid)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from main import app

    return TestClient(app)
