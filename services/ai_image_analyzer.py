"""
AI Image Analyzer Service - FIXED VERSION
Analyzes room/space images using Qwen2.5-VL via OpenRouter
"""
import os
import base64
import json
from typing import Dict
from dotenv import load_dotenv
load_dotenv()  # Add this line

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False
    print("⚠️ openai package not installed")

class AIImageAnalyzer:
    def __init__(self):
        """Initialize with OpenRouter API"""
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.client = None
        self.use_api = False

        if self.openrouter_api_key and len(self.openrouter_api_key) > 20 and OPENAI_AVAILABLE:
            try:
                # Clear any proxy environment variables that might interfere
                old_proxies = {}
                for proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
                    if proxy_var in os.environ:
                        old_proxies[proxy_var] = os.environ.pop(proxy_var)

                try:
                    # Create httpx client without base_url to avoid proxy issues
                    import httpx
                    http_client = httpx.Client(timeout=30.0)

                    self.client = OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=self.openrouter_api_key,
                        http_client=http_client
                    )
                    # Test connection with vision-capable model
                    test = self.client.chat.completions.create(
                        model="qwen/qwen2.5-vl-32b-instruct:free",
                        messages=[{"role": "user", "content": "Hi"}],
                        max_tokens=5
                    )
                    print("✅ OpenRouter API connected")
                    self.use_api = True
                finally:
                    # Restore proxy settings
                    for proxy_var, proxy_value in old_proxies.items():
                        os.environ[proxy_var] = proxy_value

            except Exception as e:
                print(f"❌ OpenRouter failed: {str(e)[:80]}")
                self.client = None
        else:
            print("⚠️ No OpenRouter API key found")

    def analyze_room_image(self, image_data: str, room_type: str = None):
        """Analyze a room image"""
        if self.use_api and self.client:
            return self._analyze_with_api(image_data, room_type)
        else:
            return self._get_fallback_analysis(room_type)

    def _analyze_with_api(self, image_data: str, room_type: str = None):
        """Analyze using vision-capable models via OpenRouter"""
        # Try multiple vision models in order of preference
        vision_models = [
            "qwen/qwen2.5-vl-32b-instruct:free",
            "meta-llama/llama-3.2-11b-vision-instruct:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "meta-llama/llama-3.2-11b-instruct:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "qwen/qwen2-vl-72b-instruct:free"
        ]

        for model in vision_models:
            try:
                print(f"[INFO] Trying vision model: {model}")

                prompt = """Analyze this room image and provide a JSON response with:
{
  "room_type": "room type",
  "room_size": "compact/medium/spacious/large",
  "room_shape": "rectangular/L-shaped/square",
  "architectural_details": {
    "walls": "description",
    "floor": "type",
    "ceiling": "height",
    "windows": "description",
    "doors": "description"
  },
  "current_style": {
    "primary_style": "style name",
    "style_elements": ["element1", "element2"],
    "color_palette": [
      {"name": "color", "hex": "#000000"}
    ]
  },
  "lighting_analysis": {
    "natural_light": "description",
    "artificial_light": "description",
    "recommendations": ["rec1", "rec2"]
  },
  "furniture_inventory": [
    {
      "item": "furniture name",
      "condition": "good",
      "style_match": "matches",
      "placement": "location"
    }
  ],
  "spatial_analysis": {
    "estimated_dimensions": "L × W × H",
    "traffic_flow": "description",
    "focal_points": ["point1"],
    "storage_assessment": "description"
  },
  "improvement_areas": ["area1", "area2"],
  "design_recommendations": ["rec1", "rec2"],
  "design_concept": {
    "suggested_theme": "theme",
    "mood": "mood",
    "target_audience": "audience"
  }
}

Analyze the room thoroughly and return ONLY valid JSON."""

                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                            }
                        ]
                    }],
                    max_tokens=2000,
                    temperature=0.7
                )

                result = response.choices[0].message.content
                print(f"[SUCCESS] Vision analysis completed using {model}")

                # Try to parse JSON
                try:
                    # Remove markdown code blocks if present
                    if "```json" in result:
                        result = result.split("```json")[1].split("```")[0].strip()
                    elif "```" in result:
                        result = result.split("```")[1].split("```")[0].strip()

                    analysis = json.loads(result)
                    return self._ensure_structure(analysis, room_type)
                except json.JSONDecodeError as e:
                    print(f"[WARNING] JSON parsing failed for {model}: {e}")
                    continue  # Try next model
                except Exception as e:
                    print(f"[WARNING] Error processing result from {model}: {e}")
                    continue  # Try next model

            except Exception as e:
                print(f"[WARNING] Model {model} failed: {str(e)[:100]}")
                continue  # Try next model

        print("[ERROR] All vision models failed, using fallback analysis")
        return self._get_fallback_analysis(room_type)

    def _ensure_structure(self, analysis, room_type: str = None):
        """Ensure analysis has all required fields"""
        defaults = {
            "room_type": room_type or "Unknown",
            "room_size": "medium",
            "room_shape": "rectangular",
            "architectural_details": {
                "walls": "Standard walls",
                "floor": "Standard flooring",
                "ceiling": "Standard height",
                "windows": "Standard windows",
                "doors": "Standard doors"
            },
            "current_style": {
                "primary_style": "Contemporary",
                "style_elements": ["Basic furnishings"],
                "color_palette": [{"name": "White", "hex": "#FFFFFF"}]
            },
            "lighting_analysis": {
                "natural_light": "Moderate natural light",
                "artificial_light": "Standard lighting",
                "recommendations": ["Add ambient lighting"]
            },
            "furniture_inventory": [{
                "item": "Basic furniture",
                "condition": "good",
                "style_match": "neutral",
                "placement": "standard"
            }],
            "spatial_analysis": {
                "estimated_dimensions": "Unknown",
                "traffic_flow": "Standard flow",
                "focal_points": ["Main area"],
                "storage_assessment": "Standard storage"
            },
            "improvement_areas": ["Lighting", "Color", "Layout"],
            "design_recommendations": [
                "Add ambient lighting",
                "Incorporate accent colors",
                "Optimize layout"
            ],
            "design_concept": {
                "suggested_theme": "Modern Comfort",
                "mood": "Welcoming",
                "target_audience": "General"
            }
        }

        # Merge with defaults
        for key, value in defaults.items():
            if key not in analysis:
                analysis[key] = value
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if subkey not in analysis[key]:
                        analysis[key][subkey] = subvalue

        return analysis

    def _get_fallback_analysis(self, room_type: str = None):
        """Return fallback analysis"""
        return self._ensure_structure({}, room_type)

    def test_image_analysis(self, image_data: str = None) -> Dict:
        """Test image analysis functionality"""
        print("[TEST] Testing image analysis...")

        if not self.use_api:
            return {
                'status': 'failed',
                'error': 'API not initialized',
                'message': 'OpenRouter API key not configured or invalid'
            }

        # Use a simple test image if none provided
        if not image_data:
            image_data = self._create_test_image_data()

        try:
            # Test with a simple prompt
            test_prompt = "Describe this image in one sentence and return as JSON: {'description': 'your description'}"

            response = self.client.chat.completions.create(
                model="qwen/qwen2.5-vl-32b-instruct:free",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": test_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                        }
                    ]
                }],
                max_tokens=100,
                temperature=0.7
            )

            result = response.choices[0].message.content

            return {
                'status': 'success',
                'message': 'Image analysis test passed',
                'model_used': 'qwen/qwen2.5-vl-32b-instruct:free',
                'response_length': len(result)
            }

        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)[:200],
                'message': 'Image analysis test failed'
            }

    def _create_test_image_data(self) -> str:
        """Create a simple test image for testing purposes"""
        try:
            from PIL import Image, ImageDraw
            import io

            # Create a simple test image
            img = Image.new('RGB', (100, 100), color='lightblue')
            draw = ImageDraw.Draw(img)
            draw.text((50, 50), "TEST", fill='black', anchor='mm')

            # Convert to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG')
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

            return img_base64

        except Exception as e:
            print(f"Error creating test image: {e}")
            return ""


# Create singleton instances
ai_analyzer = AIImageAnalyzer()
