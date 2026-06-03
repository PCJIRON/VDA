from qwen_desktop.config.defaults import PROVIDERS


class ProviderConfig:
    def __init__(self, settings):
        self.settings = settings

    def get_provider_id(self) -> str:
        return self.settings.get("provider", "openrouter")

    def get_provider_info(self) -> dict:
        provider_id = self.get_provider_id()
        return PROVIDERS.get(provider_id, PROVIDERS["openrouter"])

    def get_api_key(self) -> str:
        return self.settings.get("api_key", "")

    def get_model(self) -> str:
        return self.settings.get("api_model", "")

    def get_base_url(self) -> str:
        return self.settings.get("api_base_url", "")

    def is_configured(self) -> bool:
        if self.get_provider_id() == "opencode":
            return bool(self.get_base_url())
        return bool(self.get_api_key() and self.get_base_url())

    def allows_anonymous(self) -> bool:
        return bool(self.get_provider_info().get("allow_anonymous", False))

    def get_free_models(self) -> list[str]:
        return list(self.get_provider_info().get("free_models", []))

    def get_models(self) -> list[str]:
        return list(self.get_provider_info().get("models", []))

    def get_docs_url(self) -> str:
        return self.get_provider_info().get("docs_url", "")

    def get_api_key_hint(self) -> str:
        return self.get_provider_info().get("api_key_hint", "")

    def get_provider_name(self) -> str:
        return self.get_provider_info().get("name", "Unknown")

    def save(self, provider_id: str, api_key: str, model: str, base_url: str) -> None:
        self.settings.set("provider", provider_id)
        self.settings.set("api_key", api_key)
        self.settings.set("api_model", model)
        self.settings.set("api_base_url", base_url)
        self.settings.save()

    @staticmethod
    def get_all_providers() -> dict[str, dict]:
        return dict(PROVIDERS)
