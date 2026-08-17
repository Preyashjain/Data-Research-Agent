from functools import cache
from typing import TypeAlias


from chromadb.auth import T
from langchain_community.chat_models import FakeListChatModel, tongyi
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_community.chat_models import ChatTongyi




from core.config import settings
from ai.models import (
    AllModelEnum,
    DeepseekModelName,
    FakeModelName,
    OllamaModelName,
    OpenAIModelName,
    TongYiModelName,

)

_MODEL_TABLE = {
    OpenAIModelName.GPT_4O_MINI: "gpt-4o-mini",
    OpenAIModelName.GPT_4O: "gpt-4o",
    DeepseekModelName.DEEPSEEK_CHAT: "deepseek-chat",
    OllamaModelName.OLLAMA_GENERIC: "ollama",
    FakeModelName.FAKE: "fake",
    TongYiModelName.QWEN_PLUS: "qwen-plus",


}


class FakeToolModel(FakeListChatModel):
    def __init__(self, responses: list[str]):
        super().__init__(responses=responses)

    def bind_tools(self, tools):
        return self

ModelT: TypeAlias = (
    ChatOpenAI | ChatOllama | ChatDeepSeek | FakeToolModel | ChatTongyi
)



@cache
def get_model(model_name: AllModelEnum | str | None, /) -> ModelT:
    """Create a model instance, falling back to a deterministic fake model when credentials are absent."""
    normalized = model_name or settings.DEFAULT_MODEL or FakeModelName.FAKE

    try:
        enum_name = model_name if isinstance(model_name, str) else normalized
        if isinstance(normalized, str) and normalized in {member.value for member in OpenAIModelName}:
            enum_value = OpenAIModelName(normalized)
        elif isinstance(normalized, str) and normalized in {member.value for member in DeepseekModelName}:
            enum_value = DeepseekModelName(normalized)
        elif isinstance(normalized, str) and normalized in {member.value for member in OllamaModelName}:
            enum_value = OllamaModelName(normalized)
        elif isinstance(normalized, str) and normalized in {member.value for member in FakeModelName}:
            enum_value = FakeModelName(normalized)
        elif isinstance(normalized, str) and normalized in {member.value for member in TongYiModelName}:
            enum_value = TongYiModelName(normalized)
        else:
            enum_value = FakeModelName.FAKE
    except ValueError:
        enum_value = FakeModelName.FAKE

    api_model_name = _MODEL_TABLE.get(enum_value)
    if not api_model_name:
        return FakeToolModel(responses=["This is a test response from the fake model."])

    if enum_value in OpenAIModelName:
        if not settings.OPENAI_API_KEY:
            return FakeToolModel(responses=["OpenAI key missing; using offline fallback response."])
        return ChatOpenAI(model=api_model_name, temperature=0.5, streaming=True, api_key=settings.OPENAI_API_KEY)

    if enum_value in DeepseekModelName:
        if not settings.DEEPSEEK_API_KEY:
            return FakeToolModel(responses=["DeepSeek key missing; using offline fallback response."])
        return ChatDeepSeek(
            model=api_model_name,
            temperature=0.5,
            streaming=True,
            api_key=settings.DEEPSEEK_API_KEY,
        )

    if enum_value in OllamaModelName:
        if settings.OLLAMA_BASE_URL:
            chat_ollama = ChatOllama(
                model=settings.OLLAMA_MODEL or "llama3.1",
                temperature=0.5,
                base_url=settings.OLLAMA_BASE_URL,
            )
        else:
            chat_ollama = ChatOllama(model=settings.OLLAMA_MODEL or "llama3.1", temperature=0.5)
        return chat_ollama

    if enum_value in FakeModelName:
        return FakeToolModel(responses=["This is a test response from the fake model."])

    if enum_value in TongYiModelName:
        return ChatTongyi(model=api_model_name, temperature=0.5, streaming=True)

    return FakeToolModel(responses=["This is a test response from the fake model."])
