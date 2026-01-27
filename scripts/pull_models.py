#!/usr/bin/env python3
"""
Script to automatically pull required models from models.yaml before starting the API.
This ensures all models defined in the configuration are available in Ollama.
"""

import yaml
import httpx
import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelPuller:
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        self.ollama_base_url = ollama_base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(300.0))  # 5 minute timeout for pulls
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def wait_for_ollama(self, max_retries: int = 30, retry_delay: int = 2) -> bool:
        """Wait for Ollama service to be available."""
        logger.info("Waiting for Ollama service to be available...")
        
        for attempt in range(max_retries):
            try:
                response = await self.client.get(f"{self.ollama_base_url}/api/tags")
                if response.status_code == 200:
                    logger.info("Ollama service is available")
                    return True
            except Exception as e:
                logger.debug(f"Attempt {attempt + 1}/{max_retries}: {e}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
        
        logger.error("Ollama service is not available after maximum retries")
        return False
    
    async def get_available_models(self) -> Set[str]:
        """Get list of models already available in Ollama."""
        try:
            response = await self.client.get(f"{self.ollama_base_url}/api/tags")
            response.raise_for_status()
            
            data = response.json()
            models = set()
            
            for model in data.get("models", []):
                # Extract model name (remove :latest if present)
                model_name = model["name"].replace(":latest", "")
                models.add(model_name)
                
            logger.info(f"Available models: {sorted(models)}")
            return models
            
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return set()
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a single model from Ollama."""
        logger.info(f"Pulling model: {model_name}")
        
        try:
            async with self.client.stream(
                "POST", 
                f"{self.ollama_base_url}/api/pull",
                json={"name": model_name}
            ) as response:
                if response.status_code != 200:
                    logger.error(f"Failed to start pulling {model_name}: HTTP {response.status_code}")
                    return False
                
                # Track progress
                async for line in response.aiter_lines():
                    if line:
                        try:
                            import json
                            data = json.loads(line)
                            status = data.get("status", "")
                            
                            if "pulling" in status:
                                # Show progress for large downloads
                                if "total" in data and "completed" in data:
                                    total = data["total"]
                                    completed = data["completed"]
                                    if total > 0:
                                        progress = (completed / total) * 100
                                        logger.info(f"  {model_name}: {progress:.1f}% ({completed}/{total} bytes)")
                                else:
                                    logger.info(f"  {model_name}: {status}")
                            elif status == "success":
                                logger.info(f"Successfully pulled {model_name}")
                                return True
                                
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
        
        return True
    
    def load_models_config(self, config_path: Path) -> Dict[str, str]:
        """Load models configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            models = {}
            for alias, model_config in config.get("models", {}).items():
                if model_config.get("provider") == "ollama":
                    model_name = model_config.get("model_name")
                    if model_name:
                        models[alias] = model_name
            
            logger.info(f"Found {len(models)} Ollama models in configuration")
            return models
            
        except Exception as e:
            logger.error(f"Failed to load models configuration: {e}")
            return {}
    
    async def pull_missing_models(self, models_config: Dict[str, str]) -> bool:
        """Pull any models that are missing from Ollama."""
        if not models_config:
            logger.warning("No models configured")
            return True
        
        # Wait for Ollama to be available
        if not await self.wait_for_ollama():
            return False
        
        # Get available models
        available_models = await self.get_available_models()
        
        # Determine which models need to be pulled
        required_models = set(models_config.values())
        missing_models = required_models - available_models
        
        if not missing_models:
            logger.info("All required models are already available")
            return True
        
        logger.info(f"Missing models: {sorted(missing_models)}")
        
        # Pull missing models
        success = True
        for model_name in sorted(missing_models):
            if not await self.pull_model(model_name):
                success = False
        
        return success

async def main():
    """Main function to pull required models."""
    # Get the models.yaml path
    import os
    models_yaml_path = os.getenv("MODELS_CONFIG")
    if models_yaml_path:
        models_yaml_path = Path(models_yaml_path)
    else:
        script_dir = Path(__file__).parent
        models_yaml_path = script_dir.parent / "models.yaml"
    
    if not models_yaml_path.exists():
        logger.error(f"Models configuration not found: {models_yaml_path}")
        sys.exit(1)
    
    # Determine Ollama URL
    import os
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    logger.info(f"Using Ollama at: {ollama_base_url}")
    logger.info(f"Models configuration: {models_yaml_path}")
    
    async with ModelPuller(ollama_base_url) as puller:
        # Load models configuration
        models_config = puller.load_models_config(models_yaml_path)
        
        if not models_config:
            logger.error("No valid models found in configuration")
            sys.exit(1)
        
        # Pull missing models
        success = await puller.pull_missing_models(models_config)
        
        if success:
            logger.info("✅ All required models are available")
            sys.exit(0)
        else:
            logger.error("❌ Failed to pull some models")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())