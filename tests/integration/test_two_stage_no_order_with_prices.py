"""Integration test: stage 2 has order_type=不下单 but entry_price is non-null."""
from __future__ import annotations

import copy
from unittest.mock import MagicMock

from tests.fixtures.validators import schema_test_validator
from pa_agent.ai.router import route_strategy_files
from pa_agent.orchestrator.two_stage import TwoStageOrchestrator
from pa_agent.util.threading import CancelToken, OrchestratorEvent

from .conftest import VALID_STAGE1, VALID_STAGE2, make_reply


def test_no_order_with_non_null_price_is_normalized(
    frame, pending_writer, assembler, exp_reader,
) -> None:
    """Productable normalization: 不下单 + non-null price is cleared, not fatal."""
    bad_s2 = copy.deepcopy(VALID_STAGE2)
    bad_s2["decision"]["order_type"] = "不下单"
    bad_s2["decision"]["entry_price"] = 0

    client = MagicMock()
    client.stream_chat.side_effect = [
        make_reply(VALID_STAGE1),
        make_reply(bad_s2),
    ]

    orchestrator = TwoStageOrchestrator(
        client=client,
        assembler=assembler,
        router=route_strategy_files,
        validator=schema_test_validator(),
        pending_writer=pending_writer,
        exp_reader=exp_reader,
    )

    events: list[OrchestratorEvent] = []
    record = orchestrator.submit(
        frame=frame,
        cancel_token=CancelToken(),
        on_event=events.append,
    )

    assert OrchestratorEvent.Stage2Done in events
    assert OrchestratorEvent.Stage2Failed not in events
    decision = (record.stage2_decision or {}).get("decision") or {}
    assert decision.get("entry_price") is None
    assert decision.get("order_type") == "不下单"
    pending_writer.save_full.assert_called()
