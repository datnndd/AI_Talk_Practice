import sys
import types

import pytest

from app.modules.translations.services.translation import TranslationService


class FakeTranslated:
    text = "Xin chao"


class FakeTranslator:
    calls = []
    init_kwargs = []

    def __init__(self, **kwargs):
        self.init_kwargs.append(kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def translate(self, text, dest):
        self.calls.append((text, dest))
        return FakeTranslated()


@pytest.mark.asyncio
async def test_translate_uses_googletrans(monkeypatch):
    fake_module = types.SimpleNamespace(Translator=FakeTranslator)
    monkeypatch.setitem(sys.modules, "googletrans", fake_module)
    FakeTranslator.calls = []
    FakeTranslator.init_kwargs = []

    translated = await TranslationService.translate("Hello", "vi")

    assert translated == "Xin chao"
    assert FakeTranslator.calls == [("Hello", "vi")]
    assert FakeTranslator.init_kwargs
    assert "timeout" in FakeTranslator.init_kwargs[0]


@pytest.mark.asyncio
async def test_translate_raises_when_googletrans_returns_no_text(monkeypatch):
    class EmptyTranslator(FakeTranslator):
        async def translate(self, text, dest):
            return types.SimpleNamespace(text="")

    fake_module = types.SimpleNamespace(Translator=EmptyTranslator)
    monkeypatch.setitem(sys.modules, "googletrans", fake_module)

    with pytest.raises(Exception, match="Failed to translate text"):
        await TranslationService.translate("Hello", "vi")
