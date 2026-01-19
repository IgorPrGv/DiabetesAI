"""
LLM Wrapper com Rate Limiting para Gemini
Aplica rate limiting automático antes de cada chamada ao LLM
"""

import time
from typing import Any, Optional
from crewai import LLM
from .rate_limiter import get_rate_limiter


class RateLimitedLLM:
    """
    Wrapper para LLM que aplica rate limiting automático
    Limita para 5 requisições por minuto (quota do Gemini Free Tier)
    """
    
    def __init__(self, base_llm: LLM, max_requests: int = 5, time_window: float = 60.0):
        """
        Args:
            base_llm: LLM base que será usado (ex: Gemini LLM)
            max_requests: Máximo de requisições por time_window
            time_window: Janela de tempo em segundos
        """
        # Copiar atributos do LLM base
        self._base_llm = base_llm
        self._rate_limiter = get_rate_limiter(max_requests=max_requests, time_window=time_window)
        
        # Copiar propriedades do LLM base
        for attr in ['model', 'temperature', 'api_key', 'base_url']:
            if hasattr(base_llm, attr):
                setattr(self, attr, getattr(base_llm, attr))
    
    def call(self, *args, **kwargs) -> Any:
        """Aplica rate limiting antes de chamar o LLM base"""
        # Aguardar se necessário para respeitar rate limit
        wait_time = self._rate_limiter.wait_if_needed()
        
        # Chamar LLM base
        return self._base_llm.call(*args, **kwargs)
    
    def invoke(self, *args, **kwargs) -> Any:
        """Método invoke também precisa de rate limiting"""
        wait_time = self._rate_limiter.wait_if_needed()
        if hasattr(self._base_llm, 'invoke'):
            return self._base_llm.invoke(*args, **kwargs)
        return self._base_llm.call(*args, **kwargs)
    
    def __getattr__(self, name: str) -> Any:
        """Delegar outros atributos/métodos para o LLM base"""
        if hasattr(self._base_llm, name):
            attr = getattr(self._base_llm, name)
            # Se for um método, criar wrapper com rate limiting
            if callable(attr) and name not in ['call', 'invoke']:
                def wrapper(*args, **kwargs):
                    wait_time = self._rate_limiter.wait_if_needed()
                    return attr(*args, **kwargs)
                return wrapper
            return attr
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


def create_rate_limited_llm(base_llm: LLM, max_requests: int = 5, time_window: float = 60.0) -> LLM:
    """
    Cria um LLM com rate limiting aplicado
    
    Args:
        base_llm: LLM base (ex: do llm_providers.get_llm())
        max_requests: Máximo de requisições por time_window (padrão: 5)
        time_window: Janela de tempo em segundos (padrão: 60s = 1 minuto)
    
    Returns:
        LLM com rate limiting aplicado
    """
    return RateLimitedLLM(base_llm, max_requests=max_requests, time_window=time_window)
