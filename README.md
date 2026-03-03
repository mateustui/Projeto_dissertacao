# Orquestrador UR3 (Refatorado)

Este repositório mantém o arquivo original e adiciona uma versão modular para facilitar manutenção e evolução.

## Arquivos de entrada

- Original (inalterado): `19. GR-1.5 - Orquestrador.py`
- Refatorado: `orquestrador_refatorado.py`

## Estrutura

- `src/orquestrador/config.py`: configurações centralizadas (`Settings`)
- `src/orquestrador/domain/`: modelos de domínio (`ActionResult`, `RobotState`, enums)
- `src/orquestrador/core/`: utilitários puros (geometria)
- `src/orquestrador/adapters/sim/`: integração com Coppelia (UR3 e garra)
- `src/orquestrador/adapters/vision/`: visão estéreo + Gemini
- `src/orquestrador/services/`: regras de orquestração e execução de ações
- `src/orquestrador/adapters/gui/`: janela Tkinter e overlays
- `src/orquestrador/app/`: loop principal da simulação

## Executar

```bash
python3 orquestrador_refatorado.py
```

Se a cena nao estiver na raiz do projeto, configure no `.env`:

```bash
SCENE_PATH=/caminho/absoluto/para/experimento-ur3.ttt
```

## Testes

```bash
pytest
```

## Qualidade (sugerido)

```bash
ruff check .
black --check .
mypy src
```

## Notas de manutenção

- Novos comandos de alto nível devem ser adicionados em `services/orchestrator.py`.
- Alterações de cinemática e trajetória devem ficar em `adapters/sim/ur3.py`.
- Ajustes de visão/triangulação devem ficar em `adapters/vision/stereo.py` e `core/geometry.py`.
- Evite lógica de negócio na GUI; mantenha GUI como camada de apresentação.
