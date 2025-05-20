import os
import json
import yaml
import boto3
import httpx
import requests
from pathlib import Path
from google import genai
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import asyncio

load_dotenv()

from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[5]  # This gets /Users/ravi/EAG-TheShadowCloneAI/S8
print(ROOT)
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# Import required components for AI Layer integration
from src.core.agent.common.schema.custom_llm_payload import CustomPayload
from src.common.logger.logger import get_logger

MODELS_JSON = ROOT / "src" / "common" / "config" / "models.json"
PROFILE_YAML = ROOT / "src" / "common" / "config" / "profiles.yaml"

logger = get_logger()

class ModelManager:
    def __init__(self):
        self.config = json.loads(MODELS_JSON.read_text())
        self.profile = yaml.safe_load(PROFILE_YAML.read_text())

        self.text_model_key = self.profile["llm"]["text_generation"]
        self.model_info = self.config["models"][self.text_model_key]
        self.model_type = self.model_info["type"]

        # Initialize different clients based on model type
        if self.model_type == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            self.client = genai.Client(api_key=api_key)
        
        elif self.model_type == "bedrock":
            self.bedrock_client = boto3.client(
                service_name='bedrock-runtime',
                region_name=os.getenv(self.model_info["aws_region"]),
                aws_access_key_id=os.getenv(self.model_info["aws_access_key"]),
                aws_secret_access_key=os.getenv(self.model_info["aws_secret_key"])
            )
            logger.info("Initialized AWS Bedrock client")
        
        # For AI-Layer, we'll initialize the client during request time
        
    async def generate_text(self, 
                           prompt: str, 
                           max_tokens: int = 1000, 
                           temperature: float = 0.7, 
                           top_p: float = 0.95, 
                           domain: str = "general",
                           system_prompt: str = "") -> str:
        """
        Generate text using the configured model.
        
        Parameters:
        -----------
        prompt : str
            The input prompt for text generation
        max_tokens : int, optional
            Maximum number of tokens to generate
        temperature : float, optional
            Controls randomness in generation (0.0-1.0)
        top_p : float, optional
            Nucleus sampling parameter (0.0-1.0)
        domain : str, optional
            Domain/context for the response
        system_prompt : str, optional
            Additional system instructions for the model
            
        Returns:
        --------
        str
            The generated text response
        """
        if self.model_type == "gemini":
            return self._gemini_generate(prompt)
        
        elif self.model_type == "ollama":
            return self._ollama_generate(prompt)
        
        elif self.model_type == "bedrock":
            return await self._bedrock_generate(
                prompt, max_tokens, temperature, system_prompt
            )
        
        elif self.model_type == "endpoint" and self.text_model_key == "ai-layer":
            return await self._ai_layer_generate(
                prompt, max_tokens, temperature, top_p, domain, system_prompt
            )
        
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
        
    def _gemini_generate(self, prompt: str) -> str:
        """Generate text using Google's Gemini API"""
        response = self.client.models.generate_content(
            model=self.model_info["model"],
            contents=prompt
        )
        # Safely extract response text
        try:
            return response.text.strip()
        except AttributeError:
            return str(response)
        
    def _ollama_generate(self, prompt: str) -> str:
        """Generate text using Ollama local model"""
        response = requests.post(
            self.model_info["url"]["generate"],
            json={"model": self.model_info["model"], "prompt": prompt, "stream": False}
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    
    async def _bedrock_generate(self, 
                               prompt: str, 
                               max_tokens: int = 1000,
                               temperature: float = 0.7,
                               system_prompt: str = "") -> str:
        """Generate text using AWS Bedrock service"""
        try:
            # Format the request for Claude
            request = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": f"System: {system_prompt}\n\nUser: {prompt}" if system_prompt else prompt
                            }
                        ]
                    }
                ]
            }
            
            logger.debug(f"Sending request to Bedrock: {json.dumps(request)[:200]}...")
            
            # Invoke the model
            response = self.bedrock_client.invoke_model(
                modelId=self.model_info["model"],
                body=json.dumps(request)
            )
            
            # Parse the response
            response_body = json.loads(response["body"].read())
            generated_text = response_body["content"][0]["text"]
            
            # Clean up any thinking blocks if they appear
            if "<think>" in generated_text and "</think>" in generated_text:
                generated_text = generated_text.split("</think>")[1].strip()
            
            logger.info("Successfully generated text using Bedrock")
            return generated_text
            
        except Exception as e:
            logger.error(f"Bedrock generation error: {str(e)}")
            raise Exception(f"Bedrock generation error: {str(e)}")
    
    async def _ai_layer_generate(self,
                                prompt: str,
                                max_tokens: int = 1000,
                                temperature: float = 0.7,
                                top_p: float = 0.95,
                                domain: str = "general",
                                addition_system_prompt: str = "") -> str:
        """Generate text using the AI Layer API"""
        try:
            # Create a custom payload for the AI Layer
            custom_payload = CustomPayload(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                provider=self.model_info["url"]["generate"].get("provider", "bedrock"),
                top_p=top_p,
                domain=domain,
                addition_system_prompt=addition_system_prompt
            )
            
            # Get API credentials from environment variables
            headers = {
                "username": os.getenv(self.model_info["username"]),
                "X-API-Key": os.getenv(self.model_info["api_key_env"]),
            }
            
            # Get the API endpoint URL
            api_url = os.getenv(self.model_info["url"]["generate"]["url"])
            
            logger.info(f"Sending request to AI Layer-> model: '{custom_payload.provider}'  max_tokens: {custom_payload.max_tokens}  temperature: {custom_payload.temperature}")
            
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    api_url,
                    json=custom_payload.model_dump(),
                    headers=headers,
                )

                response.raise_for_status()
                return response.json()["generated_text"]
                
        except Exception as e:
            logger.error(f"AI Layer invoke failed: {str(e)}")
            raise RuntimeError(f"AI Layer invoke failed: {str(e)}")

    # Add embedding functionality if needed
    async def get_embeddings(self, text: str) -> list:
        """
        Get vector embeddings for the provided text
        
        Parameters:
        -----------
        text : str
            The text to convert to embeddings
            
        Returns:
        --------
        list
            Vector embeddings as a list of floats
        """
        # Implementation would depend on which embedding model is configured
        # This is placeholder - implement based on your embedding requirements
        pass