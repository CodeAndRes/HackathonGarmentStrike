"""
core/validator.py
─────────────────
Validador de Agentes: asegura que las estrategias y almacenes cumplen las reglas.
"""
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from core.tournament import AgentConfig
from core.engine import AlmacenParser, Board

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    word_count: int
    ship_count: int
    ship_sizes: List[int]

class AgentValidator:
    def __init__(self, word_limit: int = 500):
        self.word_limit = word_limit

    def validate(self, agent: AgentConfig, board_size: int, expected_ships: List[int]) -> ValidationResult:
        errors = []
        
        # 1. Validar Estrategia (agent.md)
        try:
            content = agent.load_agent_md()
            words = content.split()
            word_count = len(words)
            if word_count > self.word_limit:
                errors.append(f"Exceso de palabras en estrategia: {word_count} (máximo {self.word_limit})")
        except Exception as e:
            errors.append(f"Error al leer agent.md: {e}")
            word_count = 0

        # 2. Validar Almacén (almacen_*.md)
        ship_count = 0
        actual_sizes = []
        try:
            # Pasamos los tamaños esperados para que el parser valide correctamente
            ships = AlmacenParser.parse(agent.almacen_path, size=board_size, ship_sizes=expected_ships)
            ship_count = len(ships)
            actual_sizes = sorted([s.size for s in ships], reverse=True)
            
            # Validar contra los tamaños esperados
            expected_sorted = sorted(expected_ships, reverse=True)
            if actual_sizes != expected_sorted:
                errors.append(f"Configuración de pedidos incorrecta. Esperado {expected_sorted}, recibido {actual_sizes}")
            
            # Intentar crear un Board para disparar validaciones de solapamiento y límites
            try:
                Board(size=board_size, ships=ships, ship_sizes=expected_ships)
            except ValueError as ve:
                errors.append(f"Error de tablero: {ve}")
                
        except Exception as e:
            errors.append(f"Error crítico en almacén: {e}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            word_count=word_count,
            ship_count=ship_count,
            ship_sizes=actual_sizes
        )
