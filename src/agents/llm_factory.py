"""
LLM Factory for creating LLM instances.
Supports Groq and OpenAI providers.
"""
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    try:
        from langchain_community.chat_models import ChatOpenAI
    except ImportError:
        ChatOpenAI = None

from groq import Groq
from src.config.settings import settings
import structlog
from typing import Any, List

logger = structlog.get_logger()


class GroqChatWrapper:
    """Wrapper for Groq API to work with LangChain ChatModel interface."""
    
    def __init__(self, groq_api_key: str, model_name: str, temperature: float = 0.3):
        self.client = Groq(api_key=groq_api_key)
        self.model_name = model_name
        self.temperature = temperature
    
    def invoke(self, messages):
        """Invoke Groq API and return response."""
        try:
            # Handle both string prompts and message lists
            if isinstance(messages, str):
                groq_messages = [{"role": "user", "content": messages}]
            elif isinstance(messages, list):
                groq_messages = []
                for msg in messages:
                    if hasattr(msg, 'content'):
                        role = "user"
                        if hasattr(msg, 'type'):
                            if msg.type == "ai" or msg.type == "assistant":
                                role = "assistant"
                        groq_messages.append({"role": role, "content": msg.content})
                    elif isinstance(msg, dict):
                        groq_messages.append(msg)
                if not groq_messages:
                    groq_messages = [{"role": "user", "content": str(messages)}]
            else:
                groq_messages = [{"role": "user", "content": str(messages)}]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=groq_messages,
                temperature=self.temperature,
            )
            
            # Return response in a format compatible with LangChain
            class AIMessage:
                def __init__(self, content):
                    self.content = content
                    self.type = "ai"
            
            return AIMessage(response.choices[0].message.content)
        except Exception as e:
            logger.error("Groq API error", error=str(e))
            raise


def create_llm(temperature: float = 0.3, provider: str = None):
    """
    Create an LLM instance based on configuration.
    
    Args:
        temperature: Temperature for generation
        provider: Override provider ("groq" or "openai")
    
    Returns:
        LLM instance
    """
    provider = provider or settings.llm_provider
    
    # Auto-detect provider based on model name and available keys
    model_name = settings.openai_model if provider.lower() == "openai" else settings.groq_model
    
    # If model name contains "gpt" and OpenAI key exists, use OpenAI
    if "gpt" in model_name.lower() and settings.openai_api_key:
        provider = "openai"
        logger.info("Auto-detected OpenAI provider for GPT model", model=model_name)
    # If model name contains "llama" or provider is groq, use Groq
    elif ("llama" in model_name.lower() or "mixtral" in model_name.lower() or "gemma" in model_name.lower()) and settings.groq_api_key:
        provider = "groq"
        logger.info("Auto-detected Groq provider for Llama/Mixtral model", model=model_name)
    # Fallback: if Groq key not available but OpenAI is, use OpenAI
    elif provider.lower() == "groq" and not settings.groq_api_key and settings.openai_api_key:
        provider = "openai"
        logger.info("Falling back to OpenAI (Groq key not available)")
    
    if provider.lower() == "groq":
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when using Groq provider")
        try:
            llm = GroqChatWrapper(
                groq_api_key=settings.groq_api_key,
                model_name=settings.groq_model,
                temperature=temperature,
            )
            logger.info("Groq LLM created", model=settings.groq_model, temperature=temperature)
            return llm
        except Exception as e:
            logger.error("Failed to create Groq LLM", error=str(e))
            raise
    
    elif provider.lower() == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required when using OpenAI provider")
        try:
            # Use OpenAI SDK directly (more reliable than LangChain wrapper)
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
            
            class OpenAIWrapper:
                def __init__(self, client, model, temperature):
                    self.client = client
                    self.model = model
                    self.temperature = temperature
                
                def invoke(self, messages):
                    """Invoke OpenAI API and return response."""
                    if isinstance(messages, str):
                        messages_list = [{"role": "user", "content": messages}]
                    elif isinstance(messages, list):
                        messages_list = []
                        for msg in messages:
                            if hasattr(msg, 'content'):
                                role = "user"
                                if hasattr(msg, 'type'):
                                    if msg.type == "ai" or msg.type == "assistant" or getattr(msg, '__class__', {}).__name__ == "AIMessage":
                                        role = "assistant"
                                    elif msg.type == "system" or getattr(msg, '__class__', {}).__name__ == "SystemMessage":
                                        role = "system"
                                messages_list.append({"role": role, "content": msg.content})
                            elif isinstance(msg, dict):
                                messages_list.append(msg)
                            else:
                                messages_list.append({"role": "user", "content": str(msg)})
                        if not messages_list:
                            messages_list = [{"role": "user", "content": str(messages)}]
                    else:
                        messages_list = [{"role": "user", "content": str(messages)}]
                    
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages_list,
                        temperature=self.temperature,
                    )
                    
                    class AIMessage:
                        def __init__(self, content):
                            self.content = content
                            self.type = "ai"
                    
                    return AIMessage(response.choices[0].message.content)
            
            llm = OpenAIWrapper(client, settings.openai_model, temperature)
            logger.info("OpenAI LLM created", model=settings.openai_model, temperature=temperature)
            return llm
        except Exception as e:
            logger.error("Failed to create OpenAI LLM", error=str(e))
            raise
    
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Use 'groq' or 'openai'")

