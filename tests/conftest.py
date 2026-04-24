"""
Shared fixtures for IxOSRestCallerModifier unit tests.

All fixtures return a MagicMock that mimics IxRestSession's interface.
Each test overrides only the methods it needs.
"""
import pytest
from unittest.mock import MagicMock


def _make_response(data):
    """Build a mock HTTP response with .data and .json() matching IxRestSession usage."""
    resp = MagicMock()
    resp.data = data
    resp.json = MagicMock(return_value=data)
    return resp


@pytest.fixture
def mock_session():
    """Bare IxRestSession mock — no methods configured."""
    return MagicMock()


@pytest.fixture
def linux_chassis_session():
    """
    Session mock representing a healthy Linux chassis with:
    - one card in slot 1
    - two ports (1/1 free, 1/2 owned)
    - one sensor reading
    - one license entry
    - perf counters available
    """
    session = MagicMock()

    session.get_chassis.return_value = _make_response([{
        "managementIp": "10.0.0.1",
        "serialNumber": "SN-001",
        "controllerSerialNumber": "CSN-001",
        "type": "Novus100GE8Q",
        "numberOfPhysicalCards": 1,
        "state": "Ready",
        "id": 1,
        "ixosApplications": [
            {"name": "IxOS", "version": "9.20.0"},
            {"name": "IxNetwork Protocols", "version": "9.20.0"},
            {"name": "IxOS REST", "version": "9.20.0"},
        ],
    }])

    session.get_perfcounters.return_value = _make_response([{
        "memoryInUseBytes": 2 * 1024**3,   # 2 GB
        "memoryTotalBytes": 8 * 1024**3,   # 8 GB
        "cpuUsagePercent": 15.5,
    }])

    session.get_cards.return_value = _make_response([{
        "cardNumber": 1,
        "serialNumber": "CARD-001",
        "type": "Novus100GE8Q",
        "state": "Up",
        "numberOfPorts": 2,
    }])

    session.get_ports.return_value = _make_response([
        {
            "id": 101,
            "cardNumber": 1,
            "portNumber": 1,
            "fullyQualifiedPortName": "1/1/1",
            "owner": "",          # empty → should become "Free"
            "linkState": "Down",
            "speed": "100GE",
            "phyMode": "fiber",
            "transceiverModel": "QSFP-100G-SR4",
            "transceiverManufacturer": "Finisar",
            "lldpPeerData": None,
            "extraField": "should_be_removed",
        },
        {
            "id": 102,
            "cardNumber": 1,
            "portNumber": 2,
            "fullyQualifiedPortName": "1/1/2",
            "owner": "testuser",
            "linkState": "Up",
            "speed": "100GE",
            "phyMode": "fiber",
            "transceiverModel": "QSFP-100G-SR4",
            "transceiverManufacturer": "Finisar",
            "lldpPeerData": {
                "portId": "Et1",
                "portDescription": "Ethernet1",
                "systemMac": "aa:bb:cc:dd:ee:ff",
                "systemIp": "192.168.1.1",
                "systemName": "peer-router",
            },
            "extraField": "should_be_removed",
        },
    ])

    session.get_sensors.return_value = _make_response([{
        "type": "Temperature",
        "unit": "Celsius",
        "name": "CPU Temp",
        "value": 42,
        "criticalValue": 90,
        "maxValue": 85,
        "minValue": 0,
        "parentId": 1,
        "id": 10,
        "adapterName": "adapter",
        "sensorSetName": "set1",
        "cpuName": "cpu0",
    }])

    session.get_license_activation.return_value = _make_response([{
        "hostId": "HOST-001",
        "partNumber": "M111111",
        "activationCode": "XXXX-YYYY-ZZZZ",
        "quantity": 1,
        "description": "IxNetwork License",
        "maintenanceDate": "2026-01-01",
        "expiryDate": "2027-01-01",
        "isExpired": False,
    }])

    return session


@pytest.fixture
def windows_chassis_session(linux_chassis_session):
    """
    Session mock for a Windows chassis: same as linux but get_perfcounters raises.
    """
    linux_chassis_session.get_perfcounters.side_effect = Exception("perf not available on Windows")
    return linux_chassis_session
