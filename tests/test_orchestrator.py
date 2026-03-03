from __future__ import annotations

import numpy as np

from orquestrador.domain.models import ActionResult
from orquestrador.services.orchestrator import LLMOrchestrator


class DummyLogger:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def error(self, msg: str) -> None:
        self.messages.append(("error", msg))

    def vision(self, msg: str) -> None:
        self.messages.append(("vision", msg))

    def action(self, msg: str) -> None:
        self.messages.append(("action", msg))

    def robot(self, msg: str) -> None:
        self.messages.append(("robot", msg))


class DummyRobot:
    def __init__(self) -> None:
        self.ocupado = False
        self.last_deposit: np.ndarray | None = None

    def iniciar_depositar(self, pos: np.ndarray) -> ActionResult:
        self.last_deposit = pos
        return ActionResult(True, "ok")

    def get_state(self):
        class S:
            position = np.array([0.0, 0.0, 0.0])
            orientation = np.array([0.0, 0.0, 0.0])
            joint_angles = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

            class status:
                value = "IDLE"

        return S()


class DummyGarra:
    fechada = False

    def abrir(self) -> ActionResult:
        return ActionResult(True, "aberta")

    def fechar(self) -> ActionResult:
        return ActionResult(True, "fechada")


class DummyVision:
    def localizar(self, name: str) -> ActionResult:
        return ActionResult(True, "ok", np.array([1.0, 2.0, 3.0]))

    def detectar(self) -> ActionResult:
        return ActionResult(True, "ok", [])


class DummyClient:
    pass


def test_place_at_position_coerces_inputs_to_float() -> None:
    robot = DummyRobot()
    orch = LLMOrchestrator(robot, DummyGarra(), DummyVision(), DummyLogger(), client=DummyClient())

    result = orch.execute_action(
        {
            "funcao": "place_at_position",
            "args": {"x": "1.2", "y": "bad", "z": None},
        }
    )

    assert result.success is True
    assert robot.last_deposit is not None
    assert np.allclose(robot.last_deposit, np.array([1.2, 0.0, 0.1]))


def test_wait_action_sets_orchestrator_busy_temporarily() -> None:
    orch = LLMOrchestrator(DummyRobot(), DummyGarra(), DummyVision(), DummyLogger(), client=DummyClient())

    result = orch.execute_action({"funcao": "wait", "args": {"seconds": 0.05}})
    assert result.success is True
    assert orch.busy is True


def test_unknown_function_returns_error() -> None:
    orch = LLMOrchestrator(DummyRobot(), DummyGarra(), DummyVision(), DummyLogger(), client=DummyClient())

    result = orch.execute_action({"funcao": "nao_existe", "args": {}})
    assert result.success is False
    assert "Funcao desconhecida" in result.message
