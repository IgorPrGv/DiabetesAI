#!/usr/bin/env python3
"""
Guia para configurar API Key tradicional do Gemini
"""

import os
import webbrowser
from dotenv import load_dotenv

load_dotenv()

def check_current_key():
    """Verifica a chave atual configurada"""
    print("🔍 VERIFICANDO CHAVE ATUAL")
    print("=" * 50)

    current_key = os.getenv("GEMINI_API_KEY", "")
    if not current_key:
        print("❌ Nenhuma chave GEMINI_API_KEY configurada no .env")
        return False

    print(f"Chave atual: {current_key[:20]}...")
    print(f"Comprimento: {len(current_key)} caracteres")

    if current_key.startswith("AIza"):
        print("✅ Formato correto: API Key tradicional")
        return True
    elif current_key.startswith("AQ."):
        print("⚠️  Formato OAuth2: Token efêmero (pode não funcionar)")
        return False
    else:
        print("❓ Formato desconhecido")
        return False


def guide_to_get_api_key():
    """Guia passo a passo para obter API Key"""
    print("\n📋 GUIA PARA OBTER API KEY TRADICIONAL")
    print("=" * 50)

    steps = [
        "1. Acesse: https://aistudio.google.com/app/apikey",
        "2. Faça login com sua conta Google",
        "3. Clique em 'Create API Key'",
        "4. Copie a chave gerada (formato: AIza...)",
        "5. Cole a chave no arquivo .env:",
        "   GEMINI_API_KEY=AIzaSy...sua_chave_aqui",
        "6. Execute este script novamente para testar"
    ]

    for step in steps:
        print(step)

    print("\n🔗 Abrindo navegador...")
    try:
        webbrowser.open("https://aistudio.google.com/app/apikey")
        print("✅ Navegador aberto. Siga os passos acima.")
    except:
        print("❌ Não foi possível abrir o navegador automaticamente.")
        print("   Acesse manualmente: https://aistudio.google.com/app/apikey")


def test_api_key(key):
    """Testa se a API key funciona"""
    print("\n🧪 TESTANDO API KEY")
    print("=" * 50)

    if not key.startswith("AIza"):
        print("❌ Chave não é uma API Key tradicional (deve começar com 'AIza')")
        return False

    try:
        # Usar a nova biblioteca recomendada
        import google.genai as genai

        print("🔄 Configurando API Key...")
        genai.configure(api_key=key)

        print("🔄 Testando chamada ao Gemini...")
        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents="Responda apenas: OK"
        )

        print("✅ Gemini funcionou!")
        print(f"   Resposta: {response.text.strip()}")

        return True

    except ImportError:
        print("⚠️  Biblioteca google.genai não encontrada, tentando google.generativeai...")
        try:
            import google.generativeai as genai

            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-flash-latest")
            response = model.generate_content("Responda apenas: OK")

            print("✅ Gemini funcionou!")
            print(f"   Resposta: {response.text.strip()}")

            return True

        except Exception as e:
            print(f"❌ Erro: {str(e)[:200]}")
            return False
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower():
            print("❌ Quota excedida - aguarde alguns minutos")
        elif "403" in error_str or "invalid" in error_str.lower():
            print("❌ API Key inválida")
        else:
            print(f"❌ Erro desconhecido: {error_str[:200]}")
        return False


def test_with_crewai(key):
    """Testa a API key com CrewAI"""
    print("\n🤖 TESTANDO COM CREWAI")
    print("=" * 50)

    try:
        from backend.llm_providers import get_llm

        print("🔄 Testando via llm_providers.py...")
        llm = get_llm(provider="gemini", temperature=0.7)

        print("✅ LLM criado com sucesso")

        # Teste rápido
        from crewai import Agent, Task, Crew, Process

        agent = Agent(
            role="Test Agent",
            goal="Responder OK",
            backstory="Teste simples",
            llm=llm,
            verbose=False,
        )

        task = Task(
            description="Responda apenas: OK",
            agent=agent,
            expected_output="OK",
        )

        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
        result = crew.kickoff()

        print("✅ CrewAI funcionou!")
        print(f"   Resultado: {str(result)[:100]}")

        return True

    except Exception as e:
        print(f"❌ Erro com CrewAI: {str(e)[:200]}")
        return False


def main():
    """Função principal"""
    print("🔑 CONFIGURAÇÃO DA API KEY DO GEMINI")
    print("=" * 50)

    # Verificar chave atual
    current_ok = check_current_key()

    if current_ok:
        print("\n✅ Chave atual parece estar correta")

        # Testar a chave atual
        current_key = os.getenv("GEMINI_API_KEY", "")
        api_test_ok = test_api_key(current_key)

        if api_test_ok:
            crewai_test_ok = test_with_crewai(current_key)

            if crewai_test_ok:
                print("\n🎉 Tudo funcionando! Sua configuração está correta.")
                return
            else:
                print("\n⚠️  API Key funciona, mas CrewAI tem problemas")
        else:
            print("\n❌ API Key atual não funciona")

    # Se chegou aqui, precisa de nova chave
    print("\n🔧 NECESSÁRIO OBTER NOVA API KEY")
    guide_to_get_api_key()

    print("\n💡 DICAS:")
    print("- As API Keys são gratuitas e têm quota generosa")
    print("- Não compartilhe sua API Key")
    print("- Se perder a chave, pode gerar uma nova no AI Studio")


if __name__ == "__main__":
    main()



