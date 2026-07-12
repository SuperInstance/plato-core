"""Tests for plato_core.protocol — PLATO Wire Protocol v0.1 Python types."""

import json
import pytest
from plato_core.protocol import (
    DEFAULT_PORT,
    PROTOCOL_VERSION,
    TickResponse,
    HistoryResponse,
    AckResponse,
    AlarmEntry,
    AlarmListResponse,
    AlarmNotification,
    SubscribedResponse,
    UnsubscribedResponse,
    ByeResponse,
    WelcomeResponse,
    HelpResponse,
    ErrorResponse,
    parse_response,
    cmd_tick,
    cmd_history,
    cmd_actuator,
    cmd_alarm_list,
    cmd_alarm_set,
    cmd_subscribe,
    cmd_unsubscribe,
    cmd_help,
    cmd_quit,
)


class TestResponseParsing:
    def test_parse_tick(self):
        resp = parse_response(json.dumps({
            "type": "tick", "t": 1749234437.0, "seq": 42,
            "data": {"coolant_temp_c": 96.3, "rpm": 1790}
        }))
        assert isinstance(resp, TickResponse)
        assert resp.t == 1749234437.0
        assert resp.seq == 42
        assert resp.data["coolant_temp_c"] == 96.3
        assert resp.data["rpm"] == 1790

    def test_parse_history(self):
        resp = parse_response(json.dumps({
            "type": "history", "count": 2,
            "ticks": [
                {"t": 100.0, "seq": 1, "data": {"temp": 50.0}},
                {"t": 101.0, "seq": 2, "data": {"temp": 51.0}}
            ]
        }))
        assert isinstance(resp, HistoryResponse)
        assert resp.count == 2
        assert len(resp.ticks) == 2
        assert resp.ticks[0].seq == 1
        assert resp.ticks[1].data["temp"] == 51.0

    def test_parse_ack(self):
        resp = parse_response(json.dumps({
            "type": "ack", "command": "actuator", "name": "pump", "value": 1.0
        }))
        assert isinstance(resp, AckResponse)
        assert resp.command == "actuator"
        assert resp.name == "pump"
        assert resp.value == 1.0

    def test_parse_alarm_set_ack(self):
        resp = parse_response(json.dumps({
            "type": "ack", "command": "alarm_set", "id": "overheat"
        }))
        assert isinstance(resp, AckResponse)
        assert resp.command == "alarm_set"
        assert resp.id == "overheat"

    def test_parse_alarm_list(self):
        resp = parse_response(json.dumps({
            "type": "alarm_list",
            "alarms": [
                {"id": "overheat", "condition": "temp > 95", "cooldown_sec": 30,
                 "last_triggered": 1749234437.0, "state": "active"},
                {"id": "bilge", "condition": "bilge > 10", "cooldown_sec": 60,
                 "last_triggered": None, "state": "idle"}
            ]
        }))
        assert isinstance(resp, AlarmListResponse)
        assert len(resp.alarms) == 2
        assert resp.alarms[0].id == "overheat"
        assert resp.alarms[0].state == "active"
        assert resp.alarms[0].last_triggered == 1749234437.0
        assert resp.alarms[1].last_triggered is None
        assert resp.alarms[1].state == "idle"

    def test_parse_welcome(self):
        resp = parse_response(json.dumps({
            "type": "welcome", "room_id": "engine_room", "tick_hz": 0.2,
            "sensors": ["coolant_temp_c", "bilge_cm", "rpm"]
        }))
        assert isinstance(resp, WelcomeResponse)
        assert resp.room_id == "engine_room"
        assert resp.tick_hz == 0.2
        assert resp.sensors == ["coolant_temp_c", "bilge_cm", "rpm"]

    def test_parse_subscribed(self):
        resp = parse_response(json.dumps({"type": "subscribed", "tick_hz": 0.5}))
        assert isinstance(resp, SubscribedResponse)
        assert resp.tick_hz == 0.5

    def test_parse_help(self):
        resp = parse_response(json.dumps({"type": "help", "commands": ["tick", "quit"]}))
        assert isinstance(resp, HelpResponse)
        assert "tick" in resp.commands

    def test_parse_error(self):
        resp = parse_response(json.dumps({"type": "error", "message": "bad command"}))
        assert isinstance(resp, ErrorResponse)
        assert resp.message == "bad command"

    def test_parse_alarm_notification(self):
        """Spontaneous alarm notifications (spec §Spontaneous Messages)."""
        resp = parse_response(json.dumps({
            "type": "alarm", "id": "overheat", "triggered_at": 1749234437.0,
            "data": {"coolant_temp_c": 96.3, "bilge_cm": 7, "rpm": 1790}
        }))
        assert isinstance(resp, AlarmNotification)
        assert resp.id == "overheat"
        assert resp.triggered_at == 1749234437.0
        assert resp.data["coolant_temp_c"] == 96.3
        assert resp.data["rpm"] == 1790

    def test_parse_unsubscribed(self):
        resp = parse_response(json.dumps({"type": "unsubscribed"}))
        assert isinstance(resp, UnsubscribedResponse)

    def test_parse_bye(self):
        resp = parse_response(json.dumps({"type": "bye"}))
        assert isinstance(resp, ByeResponse)

    def test_parse_unknown_type(self):
        resp = parse_response(json.dumps({"type": "unknown_xyz"}))
        assert isinstance(resp, ErrorResponse)
        assert "unknown" in resp.message.lower()


class TestCommandBuilders:
    def test_cmd_tick(self):
        assert cmd_tick() == "tick"

    def test_cmd_history_default(self):
        assert cmd_history() == "history 10"

    def test_cmd_history_n(self):
        assert cmd_history(50) == "history 50"

    def test_cmd_actuator(self):
        assert cmd_actuator("pump", 1) == "actuator pump 1"
        assert cmd_actuator("throttle", 0.5) == "actuator throttle 0.5"

    def test_cmd_alarm_list(self):
        assert cmd_alarm_list() == "alarm list"

    def test_cmd_alarm_set(self):
        cmd = cmd_alarm_set("overheat", "temp > 95", 30)
        assert cmd == "alarm set overheat temp > 95 30"

    def test_cmd_subscribe(self):
        assert cmd_subscribe() == "subscribe"

    def test_cmd_unsubscribe(self):
        assert cmd_unsubscribe() == "unsubscribe"

    def test_cmd_help(self):
        assert cmd_help() == "help"

    def test_cmd_quit(self):
        assert cmd_quit() == "quit"


class TestConstants:
    def test_default_port(self):
        assert DEFAULT_PORT == 1234

    def test_protocol_version(self):
        assert PROTOCOL_VERSION == "0.1"
