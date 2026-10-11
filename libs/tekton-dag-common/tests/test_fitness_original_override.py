"""The original override is transferred unchanged.

An incoming session always wins. A forwarder must not mint a new one.
"""

from tekton_dag_common.baggage_contract import incoming_session, outgoing_session


def test_incoming_override_wins_over_a_minted_session():
    assert incoming_session("originator", header="pr-73", session_value="minted") == "pr-73"
    assert incoming_session("forwarder", header="pr-73", session_value="minted") == "pr-73"


def test_forwarder_does_not_mint_when_nothing_arrived():
    assert outgoing_session("forwarder", context_value="pr-73", session_value="minted") == "pr-73"
    assert outgoing_session("forwarder", context_value=None, session_value="minted") is None
