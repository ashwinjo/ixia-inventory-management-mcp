"""
Unit tests for IxOSRestCallerModifier.

All tests use mock IxRestSession objects — no real chassis required.
Run with: pytest tests/ -v
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

import IxOSRestCallerModifier as caller


class TestGetChassisInformation:
    def test_linux_chassis_happy_path(self, linux_chassis_session):
        result = caller.get_chassis_information(linux_chassis_session)

        assert result["chassisSerial#"] == "SN-001"
        assert result["controllerSerial#"] == "CSN-001"
        assert result["chassisType"] == "Novus100GE8Q"
        assert result["physicalCards#"] == "1"
        assert result["chassisStatus"] == "Ready"
        assert result["os"] == "Linux"
        assert result["IxOS"] == "9.20.0"
        assert result["IxNetwork Protocols"] == "9.20.0"
        # perf counters should be populated
        assert result["mem_bytes"] != "NA"
        assert result["cpu_pert_usage"] == 15.5

    def test_windows_chassis_falls_back_gracefully(self, windows_chassis_session):
        result = caller.get_chassis_information(windows_chassis_session)

        assert result["os"] == "Windows"
        assert result["mem_bytes"] == "NA"
        assert result["cpu_pert_usage"] == "NA"
        # other fields should still be populated from get_chassis()
        assert result["chassisSerial#"] == "SN-001"

    def test_ixia_vm_chassis_has_empty_serial(self, linux_chassis_session):
        linux_chassis_session.get_chassis.return_value.data = [{
            "managementIp": "10.0.0.1",
            "serialNumber": "",
            "controllerSerialNumber": "CSN-001",
            "type": "Ixia_Virtual_Test_Appliance",
            "numberOfPhysicalCards": 1,
            "state": "Ready",
            "id": 1,
            "ixosApplications": [],
        }]
        result = caller.get_chassis_information(linux_chassis_session)
        assert result["chassisSerial#"] == "IxiaVM"

    def test_raises_on_get_chassis_failure(self, mock_session):
        mock_session.get_chassis.side_effect = Exception("connection refused")
        with pytest.raises(Exception, match="connection refused"):
            caller.get_chassis_information(mock_session)


class TestGetChassisCardsInformation:
    def test_returns_cards_sorted_by_number(self, linux_chassis_session):
        # Add a second card out of order
        linux_chassis_session.get_cards.return_value.data = [
            {"cardNumber": 3, "serialNumber": "C3", "type": "TypeA", "state": "Up", "numberOfPorts": 4},
            {"cardNumber": 1, "serialNumber": "C1", "type": "TypeB", "state": "Down", "numberOfPorts": 2},
        ]
        result = caller.get_chassis_cards_information(linux_chassis_session, "10.0.0.1", "")
        assert result[0]["cardNumber"] == 1
        assert result[1]["cardNumber"] == 3

    def test_card_fields_mapped_correctly(self, linux_chassis_session):
        result = caller.get_chassis_cards_information(linux_chassis_session, "10.0.0.1", "")
        card = result[0]
        assert card["cardNumber"] == 1
        assert card["serialNumber"] == "CARD-001"
        assert card["cardType"] == "Novus100GE8Q"
        assert card["cardState"] == "Up"
        assert card["numberOfPorts"] == 2
        assert card["chassisIp"] == "10.0.0.1"

    def test_raises_on_session_failure(self, mock_session):
        mock_session.get_cards.side_effect = Exception("timeout")
        with pytest.raises(Exception):
            caller.get_chassis_cards_information(mock_session, "10.0.0.1", "")


class TestGetChassisPortsInformation:
    def test_empty_owner_becomes_free(self, linux_chassis_session):
        result = caller.get_chassis_ports_information(linux_chassis_session, "10.0.0.1", "")
        port1 = next(p for p in result if p["portNumber"] == 1)
        assert port1["owner"] == "Free"

    def test_owned_port_preserves_owner(self, linux_chassis_session):
        result = caller.get_chassis_ports_information(linux_chassis_session, "10.0.0.1", "")
        port2 = next(p for p in result if p["portNumber"] == 2)
        assert port2["owner"] == "testuser"

    def test_aggregate_statistics_correct(self, linux_chassis_session):
        result = caller.get_chassis_ports_information(linux_chassis_session, "10.0.0.1", "")
        assert result[0]["totalPorts"] == 2
        assert result[0]["ownedPorts"] == 1
        assert result[0]["freePorts"] == 1

    def test_extra_fields_removed(self, linux_chassis_session):
        result = caller.get_chassis_ports_information(linux_chassis_session, "10.0.0.1", "")
        for port in result:
            assert "extraField" not in port
            assert "id" not in port

    def test_chassis_ip_appended_to_each_port(self, linux_chassis_session):
        result = caller.get_chassis_ports_information(linux_chassis_session, "10.0.0.1", "")
        for port in result:
            assert port["chassisIp"] == "10.0.0.1"

    def test_empty_port_list_returns_empty(self, mock_session):
        mock_session.get_ports.return_value.data = []
        result = caller.get_chassis_ports_information(mock_session, "10.0.0.1", "")
        assert result == []

    def test_raises_on_session_failure(self, mock_session):
        mock_session.get_ports.side_effect = Exception("network error")
        with pytest.raises(Exception):
            caller.get_chassis_ports_information(mock_session, "10.0.0.1", "")


class TestGetSensorInformation:
    def test_strips_internal_keys(self, linux_chassis_session):
        result = caller.get_sensor_information(linux_chassis_session, "10.0.0.1", "")
        for sensor in result:
            assert "criticalValue" not in sensor
            assert "maxValue" not in sensor
            assert "minValue" not in sensor
            assert "parentId" not in sensor
            assert "id" not in sensor
            assert "adapterName" not in sensor
            assert "sensorSetName" not in sensor
            assert "cpuName" not in sensor

    def test_keeps_value_fields(self, linux_chassis_session):
        result = caller.get_sensor_information(linux_chassis_session, "10.0.0.1", "")
        sensor = result[0]
        assert sensor["type"] == "Temperature"
        assert sensor["unit"] == "Celsius"
        assert sensor["name"] == "CPU Temp"
        assert sensor["value"] == 42

    def test_appends_chassis_metadata(self, linux_chassis_session):
        result = caller.get_sensor_information(linux_chassis_session, "10.0.0.1", "TypeX")
        sensor = result[0]
        assert sensor["chassisIp"] == "10.0.0.1"
        assert sensor["typeOfChassis"] == "TypeX"
        assert "lastUpdatedAt_UTC" in sensor


class TestGetLicenseActivation:
    def test_happy_path_maps_fields(self, linux_chassis_session):
        result = caller.get_license_activation(linux_chassis_session, "10.0.0.1", "")
        assert len(result) == 1
        lic = result[0]
        assert lic["hostId"] == "HOST-001"
        assert lic["partNumber"] == "M111111"
        assert lic["activationCode"] == "XXXX-YYYY-ZZZZ"
        assert lic["isExpired"] is False
        assert lic["chassisIp"] == "10.0.0.1"

    def test_returns_na_on_exception(self, mock_session):
        mock_session.get_license_activation.side_effect = Exception("license server down")
        result = caller.get_license_activation(mock_session, "10.0.0.1", "")
        assert len(result) == 1
        assert result[0]["activationCode"] == "NA"
        assert result[0]["chassisIp"] == "10.0.0.1"

    def test_polls_until_activation_code_present(self, mock_session):
        """First call returns incomplete data; second call returns complete data."""
        incomplete = MagicMock()
        incomplete.json.return_value = [{}]  # no activationCode key

        complete = MagicMock()
        complete.json.return_value = [{
            "hostId": "H1",
            "partNumber": "P1",
            "activationCode": "CODE-123",
            "quantity": 1,
            "description": "Test",
            "maintenanceDate": "2026-01-01",
            "expiryDate": "2027-01-01",
            "isExpired": False,
        }]

        mock_session.get_license_activation.side_effect = [incomplete, complete]

        with patch("time.sleep"):  # skip actual sleep in tests
            result = caller.get_license_activation(mock_session, "10.0.0.1", "")

        assert result[0]["activationCode"] == "CODE-123"


class TestGetPerfMetrics:
    def test_calculates_memory_utilization(self, linux_chassis_session):
        result = caller.get_perf_metrics(linux_chassis_session, "10.0.0.1")
        # 2GB / 8GB = 25%
        assert abs(result["mem_utilization"] - 25.0) < 0.01
        assert result["cpu_utilization"] == 15.5
        assert result["chassisIp"] == "10.0.0.1"

    def test_returns_zeros_on_perf_failure(self, mock_session):
        mock_session.get_perfcounters.side_effect = Exception("no perf")
        result = caller.get_perf_metrics(mock_session, "10.0.0.1")
        assert result["mem_utilization"] == 0
        assert result["cpu_utilization"] == 0
        assert result["chassisIp"] == "10.0.0.1"

    def test_zero_total_memory_avoids_division_error(self, mock_session):
        mock_session.get_perfcounters.return_value.data = [{
            "memoryInUseBytes": 0,
            "memoryTotalBytes": 0,
            "cpuUsagePercent": 0,
        }]
        result = caller.get_perf_metrics(mock_session, "10.0.0.1")
        assert result["mem_utilization"] == 0
