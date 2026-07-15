# tests/unit/integrations/betha/test_counter.py
from unittest.mock import AsyncMock, MagicMock, patch


async def test_counter_returns_incremented_value():
    """Verifica que next_n_dps retorna last_n+1."""
    counter_model = MagicMock()
    counter_model.last_n = 5

    mock_result = MagicMock()
    mock_result.scalar_one.return_value = counter_model

    session = MagicMock()
    session.execute = AsyncMock(return_value=mock_result)
    session.flush = AsyncMock()

    from app.integrations.betha.counter import next_n_dps

    with patch(
        "app.integrations.betha.counter.insert",
        return_value=MagicMock(on_conflict_do_nothing=lambda **kw: MagicMock()),
    ):
        result = await next_n_dps(session, "900")

    assert result == 6
    assert counter_model.last_n == 6
