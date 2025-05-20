import requests
import json
import sys

def check_model_capabilities(model_name):
    """Check if a specific model supports image inputs."""
    try:
        # Check if model exists and get details
        response = requests.get(f"http://localhost:11434/api/show", 
                               params={"name": model_name})
        
        if response.status_code != 200:
            print(f"Failed to get model details: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        model_info = response.json()
        print(f"\nModel: {model_name}")
        print(f"Size: {model_info.get('size', 'unknown')}")
        print(f"Modified: {model_info.get('modified_at', 'unknown')}")
        
        # Check if model supports vision/images
        supports_vision = False
        if "details" in model_info:
            details = model_info["details"]
            if "vision" in details:
                supports_vision = details["vision"]
            elif "supports_vision" in details:
                supports_vision = details["supports_vision"]
            elif "capabilities" in details:
                supports_vision = "vision" in details["capabilities"]
        
        if supports_vision:
            print("✅ This model SUPPORTS vision/image inputs")
        else:
            print("❌ This model DOES NOT support vision/image inputs")
            
            # Suggest alternatives
            print("\nChecking for alternative models with vision support...")
            all_models_response = requests.get("http://localhost:11434/api/tags")
            if all_models_response.status_code == 200:
                models = all_models_response.json().get("models", [])
                vision_models = []
                
                for model in models:
                    model_name = model.get("name")
                    try:
                        model_details = requests.get(f"http://localhost:11434/api/show", 
                                                  params={"name": model_name}).json()
                        if "details" in model_details:
                            details = model_details["details"]
                            if (("vision" in details and details["vision"]) or 
                                ("supports_vision" in details and details["supports_vision"]) or
                                ("capabilities" in details and "vision" in details["capabilities"])):
                                vision_models.append(model_name)
                    except:
                        continue
                
                if vision_models:
                    print("\nModels that support vision:")
                    for model in vision_models:
                        print(f"- {model}")
                    print("\nTry using one of these models instead.")
                else:
                    print("\nNo models with vision support found.")
                    print("Try pulling a model with vision capabilities:")
                    print("  ollama pull llava")
                    print("  ollama pull moondream")
                    print("  ollama pull bakllava")
            
        return supports_vision
        
    except requests.exceptions.ConnectionError:
        print("Failed to connect to Ollama service. Is it running?")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        model_name = sys.argv[1]
    else:
        model_name = "gemma3:latest"  # Default model
        
    check_model_capabilities(model_name)