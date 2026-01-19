"""
LLM Provider Helper - Suporta múltiplos provedores gratuitos
Permite alternar entre Gemini, Groq, Ollama, Together AI, etc.
Suporta API Keys tradicionais e OAuth2 tokens para Gemini.
"""

import os
from typing import Optional
from crewai import LLM
from dotenv import load_dotenv

load_dotenv()

# Import Google Auth Library para suporte OAuth2
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google.auth import load_credentials_from_file
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False


def get_llm(provider: Optional[str] = None, temperature: float = 0.7) -> LLM:
    """
    Retorna um LLM configurado baseado no provedor especificado.
    
    Provedores suportados:
    - 'gemini' ou None: Google Gemini (padrão)
    - 'groq': Groq API (muito rápido, tier gratuito generoso)
    - 'ollama': Ollama local (totalmente gratuito, requer instalação local)
    - 'together': Together AI (tier gratuito)
    - 'huggingface': Hugging Face (modelos gratuitos)
    
    Args:
        provider: Nome do provedor ou None para usar variável de ambiente
        temperature: Temperatura do modelo (0.0-1.0)
    
    Returns:
        LLM configurado
    """
    # Se não especificado, usa variável de ambiente ou padrão
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    provider = provider.lower()
    
    if provider == "groq":
        return _get_groq_llm(temperature)
    elif provider == "ollama":
        return _get_ollama_llm(temperature)
    elif provider == "together":
        return _get_together_llm(temperature)
    elif provider == "huggingface":
        return _get_huggingface_llm(temperature)
    else:
        # Padrão: Gemini
        return _get_gemini_llm(temperature)


def _get_gemini_llm(temperature: float) -> LLM:
    """
    Configura Gemini LLM com suporte para API Key e OAuth2 tokens.
    Aplica rate limiting automático (5 req/min para Free Tier).
    
    Suporta:
    - API Key tradicional (formato AIza...)
    - OAuth2 token (formato AQ.xxx)
    - Service Account JSON (arquivo de credenciais)
    """
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    api_key_or_token = os.getenv("GEMINI_API_KEY", "").strip()
    
    if not api_key_or_token:
        raise ValueError(
            "GEMINI_API_KEY não configurada. "
            "Configure GEMINI_API_KEY no .env com uma API key (AIza...) "
            "ou token OAuth2 (AQ.xxx)"
        )
    
    # Detectar tipo de autenticação
    auth_type = _detect_gemini_auth_type(api_key_or_token)
    
    if auth_type == "oauth2":
        # Token OAuth2 (formato AQ.xxx)
        return _get_gemini_llm_oauth2(api_key_or_token, gemini_model, temperature)
    elif auth_type == "service_account":
        # Service Account JSON file
        return _get_gemini_llm_service_account(api_key_or_token, gemini_model, temperature)
    else:
        # API Key tradicional (formato AIza...)
        os.environ["GEMINI_API_KEY"] = api_key_or_token

        # FORÇAR modelo gemini-flash-latest independente da configuração
        forced_model = "gemini-flash-latest"
        print(f"🔄 Usando modelo forçado: {forced_model} (configurado: {gemini_model})")

        # Criar LLM base
        base_llm = LLM(
            model=f"gemini/{forced_model}",
            api_key=api_key_or_token,
            temperature=temperature,
        )
        
        # Aplicar rate limiting usando wrapper
        try:
            from llm_with_rate_limit import create_rate_limited_llm
            print("🔒 Aplicando rate limiting: máximo 10 requisições/minuto (otimizado para Gemini)")
            return create_rate_limited_llm(base_llm, max_requests=10, time_window=60.0)
        except Exception as e:
            print(f"⚠️  Não foi possível aplicar rate limiting: {e}")
            print("   Continuando sem rate limiting...")
            return base_llm


def _detect_gemini_auth_type(api_key_or_token: str) -> str:
    """
    Detecta o tipo de autenticação baseado no formato da chave/token.
    
    Returns:
        "api_key" - API Key tradicional (AIza...)
        "oauth2" - OAuth2 token (AQ.xxx)
        "service_account" - Caminho para arquivo JSON de Service Account
    """
    if not api_key_or_token:
        return "api_key"
    
    # Verifica se é caminho para arquivo Service Account JSON
    if api_key_or_token.endswith(".json") and os.path.isfile(api_key_or_token):
        return "service_account"
    
    # Verifica se começa com "AQ." (formato OAuth2)
    if api_key_or_token.startswith("AQ."):
        return "oauth2"
    
    # Padrão: API Key tradicional
    return "api_key"


def _get_gemini_llm_oauth2(oauth2_token: str, model: str, temperature: float) -> LLM:
    """
    Configura Gemini LLM com token OAuth2 (formato AQ.xxx).
    
    O token OAuth2 é usado como Bearer token no header Authorization.
    No entanto, o CrewAI/LiteLLM pode não suportar diretamente OAuth2.
    Esta implementação tenta configurar via variável de ambiente.
    """
    if not GOOGLE_AUTH_AVAILABLE:
        raise ImportError(
            "google-auth library não está instalada. "
            "Para suportar OAuth2, instale: pip install google-auth"
        )
    
    try:
        # Criar credentials a partir do token OAuth2
        # O token OAuth2 pode ser usado diretamente como access_token
        credentials = Credentials(token=oauth2_token)
        
        # Verificar se o token precisa ser renovado
        if credentials.expired:
            request = Request()
            credentials.refresh(request)
            oauth2_token = credentials.token
        
        # Configurar variável de ambiente para o token
        # Nota: O CrewAI/LiteLLM pode não suportar OAuth2 diretamente,
        # mas vamos tentar configurar o token como se fosse API key
        # e deixar o Google SDK usar o Authorization header
        os.environ["GEMINI_API_KEY"] = oauth2_token
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ""  # Limpar se existir
        
        # Tentar usar o token diretamente como API key
        # O Gemini API pode aceitar OAuth2 tokens no lugar de API keys
        # em alguns casos específicos
        return LLM(
            model=f"gemini/{model}",
            api_key=oauth2_token,  # Tentar usar como API key
            temperature=temperature,
        )
        
    except Exception as e:
        raise ValueError(
            f"Erro ao configurar OAuth2 para Gemini: {str(e)}\n"
            "Nota: O CrewAI/LiteLLM pode não suportar tokens OAuth2 diretamente.\n"
            "Considere usar uma API key tradicional (AIza...) ou configurar Service Account."
        ) from e


def _get_gemini_llm_service_account(credentials_path: str, model: str, temperature: float) -> LLM:
    """
    Configura Gemini LLM com Service Account JSON.
    
    Args:
        credentials_path: Caminho para o arquivo JSON de Service Account
        model: Nome do modelo Gemini
        temperature: Temperatura do modelo
    """
    if not GOOGLE_AUTH_AVAILABLE:
        raise ImportError(
            "google-auth library não está instalada. "
            "Para suportar Service Account, instale: pip install google-auth"
        )
    
    if not os.path.isfile(credentials_path):
        raise FileNotFoundError(
            f"Arquivo de Service Account não encontrado: {credentials_path}"
        )
    
    try:
        # Carregar credentials do arquivo JSON
        credentials, project = load_credentials_from_file(credentials_path)
        
        # Configurar variável de ambiente para Application Default Credentials
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        # O CrewAI/LiteLLM pode usar Application Default Credentials
        # se GOOGLE_APPLICATION_CREDENTIALS estiver configurado
        # Mas pode ser necessário configurar via Vertex AI ao invés de API key
        # Por enquanto, tentamos usar sem api_key para que use ADC
        return LLM(
            model=f"gemini/{model}",
            api_key=None,  # Deixar None para usar Application Default Credentials
            temperature=temperature,
        )
        
    except Exception as e:
        raise ValueError(
            f"Erro ao configurar Service Account para Gemini: {str(e)}\n"
            "Verifique se o arquivo JSON é válido e tem as permissões corretas."
        ) from e


def _get_groq_llm(temperature: float) -> LLM:
    """
    Configura Groq LLM - Muito rápido e com tier gratuito generoso
    Requer: GROQ_API_KEY no .env
    Modelos disponíveis: llama-3.1-8b-instant, mixtral-8x7b-32768, etc.
    
    Nota: CrewAI pode não suportar Groq diretamente. 
    Use via litellm ou openai-compatible endpoint.
    """
    groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    
    if not groq_api_key:
        raise ValueError(
            "GROQ_API_KEY não configurada. "
            "Obtenha uma chave gratuita em: https://console.groq.com/"
        )
    
    # CrewAI usa litellm internamente, então podemos usar formato openai
    # Groq tem endpoint compatível com OpenAI
    try:
        # Tenta usar via litellm (se suportado)
        return LLM(
            model=f"groq/{groq_model}",
            api_key=groq_api_key,
            temperature=temperature,
        )
    except Exception:
        # Fallback: usa OpenAI-compatible endpoint
        return LLM(
            model=f"openai/{groq_model}",
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            temperature=temperature,
        )


def _get_ollama_llm(temperature: float) -> LLM:
    """
    Configura Ollama LLM - Totalmente gratuito, roda localmente
    Requer: Ollama instalado e rodando localmente
    Modelos disponíveis: llama3.2, mistral, etc.
    """
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    return LLM(
        model=f"ollama/{ollama_model}",
        base_url=ollama_base_url,
        temperature=temperature,
    )


def _get_together_llm(temperature: float) -> LLM:
    """
    Configura Together AI LLM - Tier gratuito disponível
    Requer: TOGETHER_API_KEY no .env
    Modelos disponíveis: meta-llama/Llama-3-8b-chat-hf, etc.
    
    Nota: Usa endpoint OpenAI-compatible da Together AI
    """
    together_model = os.getenv("TOGETHER_MODEL", "meta-llama/Llama-3-8b-chat-hf")
    together_api_key = os.getenv("TOGETHER_API_KEY", "")
    
    if not together_api_key:
        raise ValueError(
            "TOGETHER_API_KEY não configurada. "
            "Obtenha uma chave gratuita em: https://api.together.xyz/"
        )
    
    # Together AI tem endpoint OpenAI-compatible
    return LLM(
        model=together_model,
        api_key=together_api_key,
        base_url="https://api.together.xyz/v1",
        temperature=temperature,
    )


def _get_huggingface_llm(temperature: float) -> LLM:
    """
    Configura Hugging Face LLM - Modelos gratuitos
    Requer: HUGGINGFACE_API_KEY no .env (gratuita)
    Modelos disponíveis: meta-llama/Llama-3-8b-chat-hf, etc.
    """
    hf_model = os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-3-8b-chat-hf")
    hf_api_key = os.getenv("HUGGINGFACE_API_KEY", "")
    
    if not hf_api_key:
        raise ValueError(
            "HUGGINGFACE_API_KEY não configurada. "
            "Obtenha uma chave gratuita em: https://huggingface.co/settings/tokens"
        )
    
    return LLM(
        model=f"huggingface/{hf_model}",
        api_key=hf_api_key,
        temperature=temperature,
    )


# Função helper para verificar qual provedor está disponível
def get_available_providers() -> list:
    """Retorna lista de provedores disponíveis baseado nas chaves configuradas"""
    available = []
    
    if os.getenv("GEMINI_API_KEY"):
        available.append("gemini")
    if os.getenv("GROQ_API_KEY"):
        available.append("groq")
    if os.getenv("TOGETHER_API_KEY"):
        available.append("together")
    if os.getenv("HUGGINGFACE_API_KEY"):
        available.append("huggingface")
    
    # Ollama sempre disponível se estiver rodando (não precisa de API key)
    available.append("ollama")
    
    return available

