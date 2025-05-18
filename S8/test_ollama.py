import requests
import json

def check_ollama_version():
    """Check the Ollama version and available API endpoints."""
    try:
        # Check if Ollama is running and get version
        response = requests.get("http://localhost:11434/api/version")
        if response.status_code == 200:
            version_info = response.json()
            print(f"Ollama version: {version_info.get('version', 'unknown')}")
        else:
            print(f"Failed to get Ollama version: HTTP {response.status_code}")
            return False

        # List available models
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            print("\nAvailable models:")
            for model in models:
                print(f"- {model.get('name')}")
        else:
            print(f"Failed to list models: HTTP {response.status_code}")
        
        # Check which endpoints are available
        endpoints = [
            "/api/generate",
            "/api/chat",
            "/api/embeddings"
        ]
        
        print("\nChecking API endpoints:")
        for endpoint in endpoints:
            try:
                # Just send a minimal request to see if endpoint exists
                # This will fail with 400 (bad request) if endpoint exists but params are wrong
                # Or 404 if endpoint doesn't exist
                response = requests.post(f"http://localhost:11434{endpoint}", json={})
                if response.status_code == 400:
                    print(f"✅ {endpoint} (available but requires parameters)")
                elif response.status_code == 404:
                    print(f"❌ {endpoint} (not available)")
                else:
                    print(f"? {endpoint} (unknown status: {response.status_code})")
            except Exception as e:
                print(f"❌ {endpoint} (error: {e})")
        
        return True
    except requests.exceptions.ConnectionError:
        print("Failed to connect to Ollama service. Is it running?")
        return False

if __name__ == "__main__":
    check_ollama_version()