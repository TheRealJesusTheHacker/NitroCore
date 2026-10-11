"""Tests for the NitroCore exception hierarchy."""

import pytest
from source.utils.exceptions import (
    DiskCleanupLocked,
    NitroCoreError,
    RegistryAccessDenied,
    ServiceControlFailure,
)


def test_all_domain_errors_derive_from_base():
    for exc in (RegistryAccessDenied, ServiceControlFailure, DiskCleanupLocked):
        assert issubclass(exc, NitroCoreError)
        assert issubclass(exc, Exception)


@pytest.mark.parametrize(
    "exc",
    [NitroCoreError, RegistryAccessDenied, ServiceControlFailure, DiskCleanupLocked],
)
def test_raise_and_catch_as_base(exc):
    with pytest.raises(NitroCoreError):
        raise exc("test message")


def test_exception_message_preserved():
    try:
        raise RegistryAccessDenied("need admin rights")
    except NitroCoreError as caught:
        assert str(caught) == "need admin rights"
