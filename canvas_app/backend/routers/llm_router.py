"""
LLM Settings Router - API endpoints for LLM provider configuration.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from schemas.llm_schemas import (
    LLMProviderConfig,
    LLMSettingsConfig,
    CreateProviderRequest,
    UpdateProviderRequest,
    TestProviderRequest,
    TestProviderResponse,
    ProviderListResponse,
    ProviderPresetsResponse,
    PROVIDER_PRESETS,
)
from services.llm_settings_service import llm_settings_service

router = APIRouter(prefix="/api/llm", tags=["LLM Settings"])


@router.get("/providers", response_model=ProviderListResponse)
async def list_providers():
    """Get all configured LLM providers."""
    settings = llm_settings_service.get_settings()
    return ProviderListResponse(
        providers=settings.providers,
        default_provider_id=settings.default_provider_id
    )


@router.get("/providers/{provider_id}", response_model=LLMProviderConfig)
async def get_provider(provider_id: str):
    """Get a specific LLM provider configuration."""
    provider = llm_settings_service.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider not found: {provider_id}")
    return provider


@router.post("/providers", response_model=LLMProviderConfig)
async def create_provider(request: CreateProviderRequest):
    """Create a new LLM provider configuration."""
    provider = llm_settings_service.create_provider(request)
    return provider


@router.put("/providers/{provider_id}", response_model=LLMProviderConfig)
async def update_provider(provider_id: str, request: UpdateProviderRequest):
    """Update an existing LLM provider configuration."""
    provider = llm_settings_service.update_provider(provider_id, request)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider not found: {provider_id}")
    return provider


@router.delete("/providers/{provider_id}")
async def delete_provider(provider_id: str):
    """Delete an LLM provider configuration."""
    if provider_id == "demo":
        raise HTTPException(status_code=400, detail="Cannot delete the demo provider")
    
    success = llm_settings_service.delete_provider(provider_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Provider not found: {provider_id}")
    
    return {"success": True, "message": f"Deleted provider: {provider_id}"}


@router.post("/providers/{provider_id}/set-default")
async def set_default_provider(provider_id: str):
    """Set a provider as the default."""
    success = llm_settings_service.set_default_provider(provider_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Provider not found: {provider_id}")
    
    return {"success": True, "message": f"Set default provider: {provider_id}"}


@router.post("/providers/test", response_model=TestProviderResponse)
async def test_provider(request: TestProviderRequest):
    """Test an LLM provider connection."""
    if request.provider_id:
        result = llm_settings_service.test_provider(provider_id=request.provider_id)
    elif request.provider:
        # Build config dict from request
        config = {
            "provider": request.provider,
            "api_key": request.api_key,
            "base_url": request.base_url,
            "model": request.model,
        }
        result = llm_settings_service.test_provider(provider_config=config)
    else:
        raise HTTPException(status_code=400, detail="Either provider_id or provider config required")
    
    return TestProviderResponse(**result)


@router.get("/presets", response_model=ProviderPresetsResponse)
async def get_presets():
    """Get available provider presets for quick setup."""
    return ProviderPresetsResponse(presets=PROVIDER_PRESETS)


@router.post("/providers/from-preset/{preset_key}", response_model=LLMProviderConfig)
async def create_from_preset(
    preset_key: str,
    api_key: Optional[str] = None,
    custom_name: Optional[str] = None
):
    """Create a provider from a preset configuration."""
    provider = llm_settings_service.create_provider_from_preset(
        preset_key=preset_key,
        api_key=api_key,
        custom_name=custom_name
    )
    
    if not provider:
        raise HTTPException(status_code=404, detail=f"Unknown preset: {preset_key}")
    
    return provider


@router.post("/import-yaml")
async def import_from_yaml(settings_path: Optional[str] = None):
    """Import providers from a settings.yaml file."""
    count = llm_settings_service.import_from_settings_yaml(settings_path)
    return {
        "success": True,
        "message": f"Imported {count} providers from settings.yaml",
        "imported_count": count
    }


@router.get("/models")
async def get_available_models():
    """Get list of all available model names from enabled providers."""
    models = llm_settings_service.get_available_models()
    return {"models": models}


@router.get("/settings", response_model=LLMSettingsConfig)
async def get_settings():
    """Get the complete LLM settings configuration."""
    return llm_settings_service.get_settings()
