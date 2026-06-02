"""Tests for lane discipline. The default posture is closed, and these pin it."""

import pytest

from noaos import Lane, LanePolicy, LaneViolation


def policy() -> LanePolicy:
    return LanePolicy.from_config(
        {
            "agents": {
                "scribe": [{"paths": ["logs/*"], "mode": "write"}],
                "curator": [
                    {"paths": ["knowledge/*"], "mode": "write"},
                    {"paths": ["decisions/*"], "mode": "append"},
                    {"paths": ["logs/*"], "mode": "read"},
                ],
            }
        }
    )


def test_write_inside_lane_is_allowed():
    policy().check("scribe", "logs/today", "write")


def test_write_outside_lane_is_denied():
    with pytest.raises(LaneViolation):
        policy().check("scribe", "knowledge/anything", "write")


def test_unknown_agent_is_denied_by_default():
    with pytest.raises(LaneViolation):
        policy().check("stranger", "logs/today", "write")


def test_append_lane_permits_append_but_not_write():
    p = policy()
    p.check("curator", "decisions/log", "append")
    with pytest.raises(LaneViolation):
        p.check("curator", "decisions/log", "write")


def test_read_lane_permits_read_but_not_append():
    p = policy()
    p.check("curator", "logs/today", "read")
    with pytest.raises(LaneViolation):
        p.check("curator", "logs/today", "append")


def test_write_lane_satisfies_a_read_action():
    # A write grant is more permissive than read, so reading is fine.
    policy().check("scribe", "logs/today", "read")


def test_most_permissive_matching_lane_wins():
    p = LanePolicy(
        [
            Lane("a", ("shared/*",), "read"),
            Lane("a", ("shared/*",), "write"),
        ]
    )
    assert p.permitted_mode("a", "shared/x") == "write"
