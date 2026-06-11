import logging

import keyring

from vda.config.defaults import PROVIDERS

logger = logging.getLogger(__name__)

_KEYRING_SERVICE = "VDA-Desktop"
_KEYRING_ACCOUNT = "api_key"


class ProviderConfig:
    def __init__(self, settings):
        self.settings = settings

    def get_provider_id(self) -> str:
        return self.settings.get("provider", "openrouter")

    def get_provider_info(self) -> dict:
        provider_id = self.get_provider_id()
        return PROVIDERS.get(provider_id, PROVIDERS["openrouter"])

    def get_api_key(self) -> str:
        provider_id = self.get_provider_id()
        try:
            # Prefer the key saved for the CURRENT provider (new format)
            keyring_key = keyring.get_password(_KEYRING_SERVICE, f"api_key:{provider_id}")
            if keyring_key:
                logger.debug(f"API key read from keyring for provider '{provider_id}'")
                return keyring_key
        except Exception as e:
            logger.debug(f"Keyring read failed: {e}")

        # If the current provider allows anonymous access and the user has not
        # stored a key for it, do NOT fall back to a legacy keyring key — that
        # key may belong to a previous (different) provider and would be sent
        # to the wrong API, causing spurious 401 errors.
        if self.allows_anonymous() and not self.settings.get("api_key", ""):
            return ""

        # Fall back to the legacy unsuffixed key for backward compatibility
        # (only used when a real key is required and the new slot is empty).
        try:
            legacy_key = keyring.get_password(_KEYRING_SERVICE, _KEYRING_ACCOUNT)
            if legacy_key:
                logger.debug(f"API key read from legacy keyring slot (provider '{provider_id}')")
                return legacy_key
        except Exception:
            pass

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
        if api_key:
            try:
                # Save under a provider-specific key so switching providers does not
                # leak the previous provider's credentials into the new request.
                keyring.set_password(_KEYRING_SERVICE, f"api_key:{provider_id}", api_key)
                # Migrate / clear the legacy unsuffixed key to avoid confusion.
                try:
                    keyring.delete_password(_KEYRING_SERVICE, _KEYRING_ACCOUNT)
                except keyring.errors.PasswordDeleteError:
                    pass
                logger.debug(f"API key saved to keyring for provider '{provider_id}'")
            except Exception as e:
                logger.warning(f"Failed to save API key to keyring: {e}")

    @staticmethod
    def get_all_providers() -> dict[str, dict]:
        return dict(PROVIDERS)
