from __future__ import annotations

import json
import time
from typing import Any

import numpy as np
from google import genai
from google.genai import types

from orquestrador.adapters.log_system import LogSystem
from orquestrador.adapters.sim.gripper import Garra
from orquestrador.adapters.sim.ur3 import UR3
from orquestrador.adapters.vision.stereo import StereoVision
from orquestrador.config import settings
from orquestrador.domain.models import ActionResult
from orquestrador.prompts import ROBOT_API_SCHEMA


class LLMOrchestrator:
    def __init__(
        self,
        robot: UR3,
        garra: Garra,
        vision: StereoVision,
        logger: LogSystem,
        client: Any | None = None,
    ):
        self.robot = robot
        self.garra = garra
        self.vision = vision
        self.logger = logger
        self.client = client or genai.Client(api_key=settings.google_api_key)

        self._action_queue: list[dict[str, Any]] = []
        self._waiting = False
        self._wait_until = 0.0
        self._mem_pos: dict[str, np.ndarray] = {}

    def parse_command(self, command: str) -> dict[str, Any] | None:
        try:
            prompt = ROBOT_API_SCHEMA.format(command=command)
            resp = self.client.models.generate_content(
                model=settings.model_id,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            text = resp.text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                return None
            return parsed
        except Exception as exc:
            self.logger.error(f"Erro ao interpretar: {exc}")
            return None

    def queue_actions(self, actions: list[dict[str, Any]]) -> None:
        self._action_queue.extend(actions)

    def execute_action(self, action: dict[str, Any]) -> ActionResult:
        func_name = str(action.get("funcao", ""))
        args = action.get("args", {})

        try:
            if func_name == "move_to_position":
                return self.robot.move_to_position(
                    args.get("x", 0),
                    args.get("y", 0),
                    args.get("z", 0.2),
                    args.get("high", True),
                )

            if func_name == "move_to_pose":
                return self.robot.move_to_pose(
                    args.get("x", 0),
                    args.get("y", 0),
                    args.get("z", 0.2),
                    args.get("rx", -90),
                    args.get("ry", 0),
                    args.get("rz", 0),
                )

            if func_name == "move_joint":
                return self.robot.move_joint(args.get("joint", 0), args.get("delta", 0))

            if func_name == "go_home":
                return self.robot.go_home()

            if func_name == "open_gripper":
                return self.garra.abrir()

            if func_name == "close_gripper":
                return self.garra.fechar()

            if func_name == "detect_objects":
                result = self.vision.detectar()
                if result.success and result.data:
                    self.logger.vision(result.message)
                return result

            if func_name == "locate_object":
                result = self.vision.localizar(args.get("name", ""))
                if result.success:
                    self.logger.vision(result.message)
                return result

            if func_name == "pick_object":
                obj_name = args.get("object_name", "")
                self.logger.action(f"Localizando '{obj_name}'...")
                result = self.vision.localizar(obj_name)
                if not result.success:
                    return result
                self.logger.vision(result.message)
                return self.robot.iniciar_pegar(result.data)

            if func_name == "place_at_position":
                def f(v: Any, default: float) -> float:
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        return float(default)

                x = f(args.get("x", 0.0), 0.0)
                y = f(args.get("y", 0.0), 0.0)
                z = f(args.get("z", 0.1), 0.1)
                pos = np.array([x, y, z], dtype=np.float64)
                return self.robot.iniciar_depositar(pos)

            if func_name == "place_on_object":
                target_name = args.get("target_name", "")
                self.logger.action(f"Localizando destino '{target_name}'...")
                result = self.vision.localizar(target_name)
                if not result.success:
                    return result
                self.logger.vision(result.message)
                return self.robot.iniciar_depositar(result.data)

            if func_name == "get_robot_state":
                state = self.robot.get_state()
                pos = state.position
                ori = state.orientation
                q = state.joint_angles

                msg = (
                    "Estado atual do robo:\n"
                    "-------------------------------------\n"
                    f"  Posicao (m):    [{pos[0]:+.4f}, {pos[1]:+.4f}, {pos[2]:+.4f}]\n"
                    f"  Orientacao (graus): [{ori[0]:+.1f}, {ori[1]:+.1f}, {ori[2]:+.1f}]\n"
                    "  Juntas (graus):\n"
                    f"     Base:     {q[0]:+.1f}\n"
                    f"     Ombro:    {q[1]:+.1f}\n"
                    f"     Cotovelo: {q[2]:+.1f}\n"
                    f"     Punho1:   {q[3]:+.1f}\n"
                    f"     Punho2:   {q[4]:+.1f}\n"
                    f"     Punho3:   {q[5]:+.1f}\n"
                    "-------------------------------------\n"
                    f"  Garra: {'Fechada' if self.garra.fechada else 'Aberta'}\n"
                    f"  Status: {state.status.value}"
                )
                return ActionResult(True, msg)

            if func_name == "wait":
                seconds = float(args.get("seconds", 1.0))
                self._waiting = True
                self._wait_until = time.time() + seconds
                return ActionResult(True, f"Aguardando {seconds}s...")

            if func_name == "save_object_position":
                name = args.get("name", "")
                key = args.get("key", "") or name
                result = self.vision.localizar(name)
                if not result.success:
                    return result
                self._mem_pos[key] = np.array(result.data, dtype=np.float64)
                self.logger.vision(f"Posicao salva: {key} = {self._mem_pos[key]}")
                return ActionResult(True, f"Posicao do '{name}' salva em '{key}'")

            if func_name == "place_at_saved":
                key = args.get("key", "")
                if key not in self._mem_pos:
                    return ActionResult(False, f"Posicao '{key}' nao encontrada na memoria. Salve primeiro.")
                pos = np.array(self._mem_pos[key], dtype=np.float64)
                return self.robot.iniciar_depositar(pos)

            return ActionResult(False, f"Funcao desconhecida: {func_name}")

        except Exception as exc:
            return ActionResult(False, f"Erro ao executar {func_name}: {exc}")

    def update(self) -> str | None:
        if self._waiting:
            if time.time() >= self._wait_until:
                self._waiting = False
            else:
                return None

        if self.robot.ocupado:
            return None

        if not self._action_queue:
            return None

        action = self._action_queue.pop(0)
        result = self.execute_action(action)
        func_name = action.get("funcao", "")

        if func_name in ["detect_objects", "locate_object", "get_robot_state"]:
            if result.success:
                if func_name == "get_robot_state":
                    self.logger.robot(result.message)
                return f"{func_name} concluido"
            self._action_queue.clear()
            return f"{func_name}: {result.message}"

        if result.success:
            return f"{func_name}: {result.message}"

        self._action_queue.clear()
        return f"{func_name}: {result.message}"

    @property
    def busy(self) -> bool:
        return bool(self._action_queue) or self._waiting or self.robot.ocupado
