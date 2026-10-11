import numpy as np
import pandas as pd
import pytest

from semaforo import backtest, journal, messages
from semaforo.config import Config, load_config
from semaforo.data import CSVSource, DemoSource, Quote
from semaforo.engine import Semaforo, parse_direction
from semaforo.indicators import rsi
from semaforo.telegram_bot import _chunks, handle_command


@pytest.fixture()
def sem(tmp_path):
    cfg = Config()
    cfg.general.source = "demo"
    cfg.general.journal_file = str(tmp_path / "registro.csv")
    return Semaforo(cfg, DemoSource())


def test_evaluate_default_levels(sem):
    ev = sem.evaluate("XAUUSD", "compra")
    assert ev.color in {"VERDE", "AMARILLO", "ROJO"}
    assert 0 <= ev.estimate.p_low <= ev.estimate.p_high <= 1
    assert 0 < ev.estimate.p_win < 1
    assert ev.sl < ev.entry < ev.tp
    assert ev.rr == pytest.approx(1.5)
    assert ev.estimate.breakeven == pytest.approx(0.4)


def test_evaluate_rejects_inverted_levels(sem):
    entry = sem.source.quote("XAUUSD").ask
    with pytest.raises(ValueError):
        sem.evaluate("XAUUSD", "compra", entry, entry + 5, entry + 10)
    with pytest.raises(ValueError):
        sem.evaluate("XAUUSD", "venta", entry, entry - 5, entry - 10)


def test_huge_spread_is_red(sem):
    sem.source.quote = lambda symbol: Quote(bid=2400.0, ask=2410.0)
    ev = sem.evaluate("XAUUSD", "compra")
    assert ev.color == "ROJO"
    assert any("spread" in b for b in ev.blockers)


def test_green_needs_evidence(sem):
    sem.cfg.semaforo.min_samples = 10_000
    evals, _ = sem.panorama()
    assert all(e.color != "VERDE" for e in evals)


def test_parse_direction():
    assert parse_direction("Compra") == 1
    assert parse_direction("sell") == -1
    with pytest.raises(ValueError):
        parse_direction("arriba")


def test_rsi_extremes():
    up = pd.Series(np.arange(1, 60, dtype=float))
    assert rsi(up).iloc[-1] == pytest.approx(100)
    flat = pd.Series(np.full(30, 5.0))
    assert rsi(flat).iloc[-1] == pytest.approx(50)


def test_ranking_runs_one_trade_at_a_time(sem):
    stats, errors = backtest.ranking(sem)
    assert not errors
    assert [s.symbol for s in stats] and stats == sorted(stats, key=lambda s: s.expectancy_low, reverse=True)
    for s in stats:
        assert s.trades > 0
        # Nunca más operaciones que velas disponibles / duración mínima de 1 vela
        assert s.trades <= sem.cfg.general.history_bars


def test_commands_return_text(sem):
    for command in ("/panorama", "/senales", "/ranking", "/ayuda", "/evaluar XAUUSD venta"):
        text = handle_command(sem, command)
        assert text and "Traceback" not in text
    assert "Uso:" in handle_command(sem, "/evaluar XAUUSD")
    assert "⚠️" in handle_command(sem, "/evaluar XAUUSD arriba")


def test_manual_evaluation_is_journaled_and_resolved(sem):
    q = sem.source.quote("EURUSD")
    text = handle_command(sem, f"/evaluar EURUSD compra {q.ask:.5f} {q.ask - 0.002:.5f} {q.ask + 0.003:.5f}")
    assert "EURUSD COMPRA" in text
    df = journal.load(sem.cfg.general.journal_file)
    assert len(df) == 1 and df.loc[0, "origin"] == "manual"
    # La señal es de la última vela: todavía no hay velas posteriores, sigue abierta.
    handle_command(sem, "/resultados")
    df = journal.load(sem.cfg.general.journal_file)
    assert df.loc[0, "outcome"] == journal.OPEN


def test_resolve_trade_on_known_bars():
    idx = pd.date_range("2026-01-05 10:00", periods=4, freq="15min")
    bars = pd.DataFrame(
        {"high": [100, 100.5, 102.5, 101], "low": [100, 99.5, 100.2, 100], "spread": 0.1}, index=idx
    )
    assert journal.resolve_trade(bars, idx[0], "COMPRA", 99, 102)[0] == journal.WIN
    assert journal.resolve_trade(bars, idx[0], "COMPRA", 99.6, 102)[0] == journal.LOSS
    # Venta: se cierra al ask; el mínimo 99.5 + spread 0.1 = 99.6 no alcanza un TP en 99.55
    assert journal.resolve_trade(bars, idx[0], "VENTA", 103, 99.55)[0] == journal.OPEN
    assert journal.resolve_trade(bars, idx[0], "VENTA", 103, 99.6)[0] == journal.WIN


def test_summary_by_color():
    df = pd.DataFrame({
        "color": ["VERDE", "VERDE", "ROJO"],
        "outcome": [journal.WIN, journal.LOSS, journal.LOSS],
        "outcome_r": [1.5, -1.0, -1.0],
        "p_win": [0.6, 0.6, 0.3],
    })
    rows = {r["color"]: r for r in journal.summary(df)}
    assert rows["VERDE"]["win_rate"] == 0.5
    assert rows["VERDE"]["avg_r"] == pytest.approx(0.25)
    assert "acierto real 50%" in messages.journal_summary(journal.summary(df))


def test_csv_source_reads_mt5_export(tmp_path):
    lines = ["<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>"]
    for i in range(3):
        lines.append(f"2026.01.05\t10:{15 * i:02d}:00\t2650.10\t2651.20\t2649.05\t2650.55\t100\t0\t25")
    (tmp_path / "XAUUSD_M15.csv").write_text("\n".join(lines))
    src = CSVSource(tmp_path, "M15")
    bars = src.bars("XAUUSD", "M15", 10)
    assert len(bars) == 3
    assert bars.index[1] == pd.Timestamp("2026-01-05 10:15")
    assert bars["spread"].iloc[0] == pytest.approx(0.25)
    assert src.meta("XAUUSD").digits == 2
    assert src.quote("XAUUSD").ask == pytest.approx(2650.80)


def test_config_rejects_typos(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('[general]\nsimbolos = ["XAUUSD"]\n')
    with pytest.raises(ValueError, match="simbolos"):
        load_config(path)


def test_example_config_is_valid():
    cfg = load_config("config.example.toml")
    assert cfg.general.symbols


def test_long_messages_are_split():
    chunks = _chunks("\n".join("x" * 100 for _ in range(100)))
    assert len(chunks) == 3 and all(len(c) <= 4000 for c in chunks)


class FakeTelegram:
    def __init__(self, batches):
        self.batches = list(batches)
        self.sent = []

    def __call__(self, token):
        return self

    def send(self, chat_id, text):
        self.sent.append((chat_id, text))

    def updates(self, offset, timeout):
        if not self.batches:
            raise KeyboardInterrupt  # termina el bucle del bot
        return self.batches.pop(0)


def _msg(update_id, chat_id, text):
    return {"update_id": update_id, "message": {"chat": {"id": chat_id}, "text": text}}


def test_bot_answers_only_the_owner(sem, monkeypatch):
    from semaforo import telegram_bot

    sem.cfg.telegram.chat_id = "111"
    fake = FakeTelegram([[_msg(1, 111, "/ayuda"), _msg(2, 999, "/panorama")], [_msg(3, 111, "/evaluar XAUUSD compra")]])
    monkeypatch.setattr(telegram_bot, "TelegramClient", fake)
    with pytest.raises(KeyboardInterrupt):
        telegram_bot.run_bot(sem)
    chats = [chat for chat, _ in fake.sent]
    assert "999" not in chats
    texts = [text for _, text in fake.sent]
    assert any("Semáforo encendido" in t for t in texts)
    assert any("/senales" in t for t in texts)          # respuesta a /ayuda
    assert any("XAUUSD COMPRA" in t for t in texts)     # respuesta a /evaluar


def test_bot_without_chat_id_tells_you_yours(sem, monkeypatch):
    from semaforo import telegram_bot

    sem.cfg.telegram.chat_id = ""
    fake = FakeTelegram([[_msg(1, 555, "hola")]])
    monkeypatch.setattr(telegram_bot, "TelegramClient", fake)
    with pytest.raises(KeyboardInterrupt):
        telegram_bot.run_bot(sem)
    assert fake.sent == [("555", "Tu chat_id es <code>555</code>. Ponlo en config.toml y reinicia.")]
