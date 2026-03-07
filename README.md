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

## Comando por voz (STT local)

Instale as dependencias opcionais de voz:

```bash
pip install ".[stt]"
```

Na GUI, use o botao `MIC`:
- 1 clique inicia a gravacao.
- 2 clique para e transcreve localmente.
- O texto transcrito e enviado como comando normal ao Gemini Robotics.

Variaveis opcionais no `.env`:

```bash
MIC_SAMPLE_RATE=16000
MIC_CHANNELS=1
STT_LANGUAGE=pt
STT_MODEL_SIZE=base
STT_DEVICE=cpu
STT_COMPUTE_TYPE=int8
STT_BEAM_SIZE=1
STT_VAD_FILTER=false
```

Para reduzir latencia de transcricao:
- Use `STT_MODEL_SIZE=base` (ou `tiny` para max velocidade).
- Mantenha `STT_BEAM_SIZE=1`.
- Deixe `STT_VAD_FILTER=false` se o ambiente for silencioso.
- A primeira inicializacao ja pre-carrega o modelo em background.

Para maior qualidade de transcricao em CPU potente:
- Use `STT_MODEL_SIZE=large-v3`.
- Mantenha `STT_COMPUTE_TYPE=int8_float32`.
- Use `STT_BEAM_SIZE=3` (ou 5 se quiser maximizar precisao).

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


## Comandos que funcionam
- inverta a posicao dos cubos vermelho e verde usando o circulo verde como posicao temporaria