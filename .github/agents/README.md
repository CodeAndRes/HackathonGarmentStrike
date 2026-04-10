# Build Agents vs Game Agents

Este proyecto separa dos familias de agentes para evitar mezclar responsabilidades.

## 1) Agentes constructores (Copilot custom agents)

Ubicacion: `.github/agents/`

- `constructor-proyecto.agent.md` -> Rol PM (SupplyPM)
- `supply-dev.agent.md` -> Rol Dev (SupplyDev)

Objetivo: construir y mantener el software del proyecto (codigo, pruebas, documentacion y handoff entre sesiones).

## 2) Agentes del juego (estrategia de participantes)

Ubicacion: `agentes/<equipo>/agent.md`

Objetivo: definir estrategia de juego para partidas/torneos. Estos manifiestos se inyectan en prompts de juego y no son agentes constructores de Copilot.

## Convencion recomendada

- PM: define alcance, prioridad, criterios de aceptacion y handoff.
- Dev: implementa cambios tecnicos y valida con pruebas.
- QA (futuro, opcional): valida regresiones, cobertura y calidad de release.

Con esto, puedes asignar un chat al rol PM y otro chat al rol Dev sin confundir contexto ni objetivos.
