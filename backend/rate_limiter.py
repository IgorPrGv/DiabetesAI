"""
Rate Limiter para Gemini API
Limita requisições para no máximo 5 por minuto (quota do tier gratuito)
"""

import time
from threading import Lock
from typing import Optional
from collections import deque


class GeminiRateLimiter:
    """
    Rate limiter para Gemini API Free Tier
    Limite: 5 requisições por minuto
    """
    
    def __init__(self, max_requests: int = 5, time_window: float = 60.0):
        """
        Args:
            max_requests: Número máximo de requisições permitidas
            time_window: Janela de tempo em segundos (padrão: 60 segundos = 1 minuto)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_times = deque()
        self.lock = Lock()
        print(f"🔒 Rate Limiter configurado: {max_requests} requisições por {time_window}s")
    
    def wait_if_needed(self) -> float:
        """
        Aguarda se necessário para respeitar o limite de rate.
        
        Returns:
            Tempo de espera em segundos (0 se não precisou esperar)
        """
        with self.lock:
            current_time = time.time()
            
            # Remove requisições antigas (fora da janela de tempo)
            while self.request_times and current_time - self.request_times[0] > self.time_window:
                self.request_times.popleft()
            
            # Se já atingiu o limite, calcula quanto tempo aguardar
            if len(self.request_times) >= self.max_requests:
                oldest_request_time = self.request_times[0]
                wait_time = self.time_window - (current_time - oldest_request_time) + 1  # +1 para margem de segurança
                
                if wait_time > 0:
                    print(f"⏳ Rate limit atingido. Aguardando {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    current_time = time.time()
                    # Limpar requisições antigas após esperar
                    while self.request_times and current_time - self.request_times[0] > self.time_window:
                        self.request_times.popleft()
                    return wait_time
            
            # Registrar nova requisição
            self.request_times.append(current_time)
            return 0.0
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do rate limiter"""
        with self.lock:
            current_time = time.time()
            # Remove requisições antigas
            while self.request_times and current_time - self.request_times[0] > self.time_window:
                self.request_times.popleft()
            
            remaining = max(0, self.time_window - (current_time - self.request_times[0])) if self.request_times else 0
            return {
                "requests_in_window": len(self.request_times),
                "max_requests": self.max_requests,
                "time_window": self.time_window,
                "remaining_time_until_oldest_expires": remaining if self.request_times else 0,
            }


# Instância global do rate limiter
_rate_limiter: Optional[GeminiRateLimiter] = None


def get_rate_limiter(max_requests: int = 5, time_window: float = 60.0) -> GeminiRateLimiter:
    """Obtém a instância global do rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = GeminiRateLimiter(max_requests=max_requests, time_window=time_window)
    return _rate_limiter


def wait_for_rate_limit():
    """Função helper para aguardar rate limit"""
    limiter = get_rate_limiter()
    return limiter.wait_if_needed()


