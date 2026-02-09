# services/design_generator.py - OPENROUTER + OFFLINE DESIGN GENERATION
"""
Design Generator Service - Uses OpenRouter API and intelligent offline fallbacks
"""
import os
from typing import Dict, List, Any
import base64
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Import Image Generator (with lazy loading to avoid circular imports)
OPENROUTER_AVAILABLE = False
gemini_image_generator = None

def _get_image_generator():
    """Lazy load image generator to avoid circular imports"""
    global gemini_image_generator, OPENROUTER_AVAILABLE
    if gemini_image_generator is None:
        try:
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            services_dir = os.path.join(parent_dir, 'services')

            if services_dir not in sys.path:
                sys.path.insert(0, services_dir)

            from gemini_image_generator import gemini_image_generator
            OPENROUTER_AVAILABLE = True
            print("[SUCCESS] Image Generator loaded successfully")
        except ImportError as e:
            try:
                from ..services.gemini_image_generator import gemini_image_generator
                OPENROUTER_AVAILABLE = True
                print("[SUCCESS] Image Generator loaded with relative import")
            except ImportError:
                try:
                    from services.gemini_image_generator import gemini_image_generator
                    OPENROUTER_AVAILABLE = True
                    print("[SUCCESS] Image Generator loaded with direct import")
                except ImportError as e2:
                    print(f"[WARNING] Image Generator not available: {e2}")
                    OPENROUTER_AVAILABLE = False
    return gemini_image_generator

# Try to import OpenAI for OpenRouter API
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False
    print("[WARNING] OpenAI package not available")

class DesignGenerator:
    def __init__(self):
        """Initialize with OpenRouter API for text generation"""
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.client = None
        self.use_openrouter = False

        if self.openrouter_api_key and len(self.openrouter_api_key) > 20 and OPENAI_AVAILABLE:
            try:
                old_proxies = {}
                for proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
                    if proxy_var in os.environ:
                        old_proxies[proxy_var] = os.environ.pop(proxy_var)

                try:
                    import httpx
                    http_client = httpx.Client(timeout=60.0)

                    self.client = OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=self.openrouter_api_key,
                        http_client=http_client
                    )

                    test_response = self.client.chat.completions.create(
                        model="google/gemma-3-27b-it:free",
                        messages=[{"role": "user", "content": "Test"}],
                        max_tokens=10
                    )
                    
                    self.use_openrouter = True
                    self.model = "google/gemma-3-27b-it:free"
                    print("[SUCCESS] OpenRouter Design Generator initialized")
                    
                finally:
                    for proxy_var, proxy_value in old_proxies.items():
                        os.environ[proxy_var] = proxy_value

            except Exception as e:
                print(f"[WARNING] OpenRouter text generation failed: {str(e)[:80]}")
                self.client = None
        else:
            print("[INFO] Using offline design generation only")

    def generate_design_suggestions(self, room_analysis: Dict[str, Any],
                                preferences: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generate design suggestions using OpenRouter or offline fallbacks"""
        if self.use_openrouter and self.client:
            return self._generate_with_openrouter(room_analysis, preferences)
        else:
            return self._get_fallback_designs(room_analysis)

    def _generate_with_openrouter(self, room_analysis: Dict, preferences: Dict = None) -> List[Dict]:
        """Generate designs using OpenRouter API"""
        try:
            room_type = room_analysis.get('room_type', 'Room')
            budget = preferences.get('budget', 'moderate') if preferences else 'moderate'
            style_pref = preferences.get('style', 'modern') if preferences else 'modern'

            prompt = f"""Create 3 detailed interior design concepts for this {room_type}.

USER PREFERENCES:
- Budget Level: {budget}
- Preferred Style: {style_pref}

ROOM ANALYSIS:
- Room Type: {room_type}
- Room Size: {room_analysis.get('room_size', 'medium')}
- Current Style: {room_analysis.get('current_style', {}).get('primary_style', 'basic')}

Return a JSON array with exactly 3 design concepts. Each design must include:
- design_name: A catchy, descriptive name
- style: The design style (modern, minimalist, traditional, etc.)
- description: 2-3 sentences describing the design concept
- color_palette: Array of 4-5 hex color codes
- key_elements: Array of 5 furniture/decor elements
- lighting_plan: Description of lighting approach
- budget_estimate: Budget-friendly/Moderate/Premium
- implementation_steps: Array of 4-5 practical steps

Example format:
[
  {{
    "design_name": "Modern Minimalist Haven",
    "style": "Minimalist",
    "description": "Clean lines and neutral palette create a serene, functional space.",
    "color_palette": ["#FFFFFF", "#F5F5F5", "#333333", "#E67E22"],
    "key_elements": ["Platform bed", "Floating shelves", "LED strips", "Abstract art", "Indoor plants"],
    "lighting_plan": "Layered lighting with dimmers",
    "budget_estimate": "Moderate",
    "implementation_steps": ["Declutter space", "Paint neutral", "Add minimal furniture", "Install lighting", "Add plants"]
  }}
]

Return ONLY valid JSON array, no other text."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.8
            )

            result = response.choices[0].message.content
            print("[SUCCESS] OpenRouter design generation completed")

            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()

            designs = json.loads(result)
            return designs if isinstance(designs, list) else [designs]

        except Exception as e:
            print(f"[WARNING] OpenRouter design generation failed: {str(e)[:100]}")
            return self._get_fallback_designs(room_analysis)

    def _get_fallback_designs(self, room_analysis: Dict) -> List[Dict]:
        """Generate context-aware fallback designs based on room analysis"""
        room_type = room_analysis.get('room_type', 'room').lower()
        room_size = room_analysis.get('room_size', 'medium').lower()

        base_designs = [
            {
                "template": "modern_minimalist",
                "name": "Modern Minimalist Haven",
                "style": "Minimalist",
                "description": "Clean lines and neutral palette create a serene, functional space.",
                "colors": ["#FFFFFF", "#F5F5F5", "#333333", "#E67E22"],
                "elements": ["Platform sofa", "Floating shelves", "LED strips", "Abstract art", "Indoor plants"],
                "lighting": "Layered lighting with dimmers",
                "budget": "Moderate",
                "steps": ["Declutter", "Paint neutral", "Add minimal furniture", "Install lighting", "Add plants"]
            },
            {
                "template": "scandinavian_cozy",
                "name": "Cozy Scandinavian Retreat",
                "style": "Scandinavian",
                "description": "Warm woods and soft textiles create an inviting atmosphere.",
                "colors": ["#F5F5DC", "#8B7355", "#FFFFFF", "#4A6F5C"],
                "elements": ["Light wood furniture", "Wool textiles", "Warm lighting", "Natural materials", "Simple decor"],
                "lighting": "Warm ambient with task lighting",
                "budget": "Budget-friendly",
                "steps": ["Choose wood pieces", "Layer textiles", "Add warm bulbs", "Natural elements", "Keep simple"]
            },
            {
                "template": "contemporary_elegant",
                "name": "Contemporary Elegance",
                "style": "Contemporary",
                "description": "Sophisticated blend of modern and classic with luxe touches.",
                "colors": ["#2C3E50", "#ECF0F1", "#E67E22", "#95A5A6"],
                "elements": ["Statement furniture", "Metallic accents", "Large artwork", "Designer lighting", "Plush textiles"],
                "lighting": "Dramatic with accent lights",
                "budget": "Premium",
                "steps": ["Select statement pieces", "Add metallics", "Invest in art", "Install fixtures", "Layer textiles"]
            }
        ]

        customized_designs = []
        for design in base_designs:
            custom_design = design.copy()
            custom_design["design_name"] = design["name"]
            custom_design["color_palette"] = design["colors"]
            custom_design["key_elements"] = design["elements"]
            custom_design["lighting_plan"] = design["lighting"]
            custom_design["budget_estimate"] = design["budget"]
            custom_design["implementation_steps"] = design["steps"]

            if room_type == "bedroom":
                custom_design["design_name"] = f"Bedroom - {design['name']}"
                custom_design["description"] = f"Transform your bedroom into a {design['style'].lower()} sanctuary."
                custom_design["key_elements"] = [elem.replace("sofa", "bed").replace("Platform sofa", "Platform bed") for elem in design["elements"]]
            elif room_type == "kitchen":
                custom_design["design_name"] = f"Kitchen - {design['name']}"
                custom_design["description"] = f"Create a functional and stylish {design['style'].lower()} kitchen space."
                custom_design["key_elements"] = [elem.replace("sofa", "island").replace("Platform sofa", "Kitchen island") for elem in design["elements"]]
            elif room_type == "living_room" or room_type == "living room":
                custom_design["design_name"] = f"Living Room - {design['name']}"
                custom_design["description"] = f"Design a comfortable {design['style'].lower()} living space."
            elif room_type == "office":
                custom_design["design_name"] = f"Office - {design['name']}"
                custom_design["description"] = f"Create a productive {design['style'].lower()} workspace."
                custom_design["key_elements"] = [elem.replace("sofa", "desk").replace("Platform sofa", "Standing desk") for elem in design["elements"]]

            if room_size == "compact" or room_size == "small":
                custom_design["key_elements"] = custom_design["key_elements"][:3]
                custom_design["description"] += " Optimized for smaller spaces."
            elif room_size == "spacious" or room_size == "large":
                custom_design["key_elements"].append("Statement pieces")
                custom_design["key_elements"].append("Area rugs")

            customized_designs.append(custom_design)

        return customized_designs

    def generate_designs_offline(self, room_analysis: Dict, preferences: Dict = None) -> List[Dict]:
        """Generate designs completely offline without any API calls"""
        print("[INFO] Generating designs in offline mode...")
        return self._get_fallback_designs(room_analysis)

    def force_fallback_mode(self) -> List[Dict]:
        """Force fallback mode for testing"""
        print("[INFO] Forcing fallback mode for design generation...")
        return self._get_fallback_designs({"room_type": "living_room"})

    def test_design_generation(self) -> Dict:
        """Test design generation functionality"""
        print("[TEST] Testing design generation...")

        test_room_analysis = {
            "room_type": "living_room",
            "room_size": "medium",
            "current_style": {"primary_style": "basic"}
        }

        try:
            if self.use_openrouter:
                print("[TEST] Testing OpenRouter-based generation...")
                designs = self.generate_design_suggestions(test_room_analysis)
                return {
                    'status': 'success',
                    'message': f'Generated {len(designs)} designs using OpenRouter',
                    'designs_count': len(designs),
                    'generation_method': 'openrouter'
                }
            else:
                print("[TEST] Testing fallback generation...")
                designs = self._get_fallback_designs(test_room_analysis)
                return {
                    'status': 'success',
                    'message': f'Generated {len(designs)} fallback designs',
                    'designs_count': len(designs),
                    'generation_method': 'fallback'
                }

        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)[:200],
                'message': 'Design generation test failed'
            }

    def generate_designs_with_images(self, room_analysis: Dict[str, Any],
                                    preferences: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generate design suggestions with OpenRouter-generated images"""
        design_concepts = self.generate_design_suggestions(room_analysis, preferences)

        image_gen = _get_image_generator()

        if not OPENROUTER_AVAILABLE or not image_gen:
            print("Image generation not available, returning text-only designs")
            for concept in design_concepts:
                concept['image_data'] = self._create_placeholder_image_data(concept)
                concept['image_status'] = 'placeholder'
            return design_concepts

        enhanced_designs = []

        for i, concept in enumerate(design_concepts[:3]):
            try:
                print(f"Generating image for design: {concept.get('design_name', f'Design {i+1}')}")

                image_data = image_gen.generate_design_image(room_analysis, concept)

                concept['image_data'] = image_data
                concept['image_status'] = 'generated' if image_data else 'fallback'

                concept['image_metadata'] = {
                    'generated_at': image_gen._get_current_timestamp(),
                    'generator': 'openrouter' if image_gen.use_api else 'fallback',
                    'room_type': room_analysis.get('room_type', 'unknown'),
                    'design_style': concept.get('style', 'unknown')
                }

                enhanced_designs.append(concept)

            except Exception as e:
                print(f"Error generating image for {concept.get('design_name', f'Design {i+1}')}: {e}")
                concept['image_data'] = self._create_placeholder_image_data(concept)
                concept['image_status'] = 'error'
                concept['image_error'] = str(e)[:100]
                enhanced_designs.append(concept)

        return enhanced_designs

    def _create_placeholder_image_data(self, design_concept: Dict) -> str:
        """Create placeholder image data for design concept"""
        try:
            from PIL import Image, ImageDraw
            import io

            colors = design_concept.get('color_palette', ['#FFFFFF', '#F5F5F5', '#333333'])
            primary_color = colors[0] if colors else '#FFFFFF'

            img = Image.new('RGB', (800, 600), primary_color)
            draw = ImageDraw.Draw(img)

            design_name = design_concept.get('design_name', 'Design Concept')
            style = design_concept.get('style', 'Style')

            try:
                draw.text((400, 250), design_name, fill='black', anchor='mm')
                draw.text((400, 350), f"Style: {style}", fill='black', anchor='mm')
                draw.text((400, 450), "Design Preview", fill='black', anchor='mm')
            except:
                draw.rectangle([300, 200, 500, 400], outline='black', width=2)

            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

            return f"data:image/png;base64,{img_base64}"

        except Exception as e:
            print(f"Error creating placeholder image: {e}")
            return ""

    def generate_single_design_with_image(self, room_analysis: Dict[str, Any],
                                        design_concept: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a single design concept with image"""
        image_gen = _get_image_generator()

        if not OPENROUTER_AVAILABLE or not image_gen:
            print("Image generation not available")
            design_concept['image_data'] = self._create_placeholder_image_data(design_concept)
            design_concept['image_status'] = 'placeholder'
            return design_concept

        try:
            print(f"Generating image for: {design_concept.get('design_name', 'Design')}")

            image_data = image_gen.generate_design_image(room_analysis, design_concept)

            design_concept['image_data'] = image_data
            design_concept['image_status'] = 'generated' if image_data else 'fallback'

            design_concept['image_metadata'] = {
                'generated_at': image_gen._get_current_timestamp(),
                'generator': 'openrouter' if image_gen.use_api else 'fallback',
                'room_type': room_analysis.get('room_type', 'unknown'),
                'design_style': design_concept.get('style', 'unknown')
            }

            return design_concept

        except Exception as e:
            print(f"Error in single design generation: {e}")
            design_concept['image_data'] = self._create_placeholder_image_data(design_concept)
            design_concept['image_status'] = 'error'
            design_concept['image_error'] = str(e)[:100]
            return design_concept

    def get_available_templates(self) -> List[Dict]:
        """Get available fallback templates from image generator"""
        image_gen = _get_image_generator()
        if OPENROUTER_AVAILABLE and image_gen:
            return image_gen.get_fallback_templates()
        return []

    def cleanup_resources(self):
        """Clean up old templates and resources"""
        image_gen = _get_image_generator()
        if OPENROUTER_AVAILABLE and image_gen:
            removed_count = image_gen.cleanup_old_templates()
            return removed_count
        return 0

    def get_image_generation_info(self) -> Dict:
        """Get information about image generation status and model"""
        image_gen = _get_image_generator()
        if OPENROUTER_AVAILABLE and image_gen:
            model_info = image_gen.get_current_model_info()
            return {
                'image_generation_available': model_info['model_available'],
                'current_model': model_info['model_name'],
                'generation_method': model_info['generation_method'],
                'api_status': model_info['api_status'],
                'design_generation_method': 'openrouter' if self.use_openrouter else 'offline'
            }
        else:
            return {
                'image_generation_available': False,
                'current_model': 'None',
                'generation_method': 'offline_fallback',
                'api_status': 'unavailable',
                'design_generation_method': 'offline'
            }

# Create singleton
design_generator = DesignGenerator()

def check_current_model_status():
    """Check and display current model status for both text and image generation"""
    print("\n" + "="*60)
    print("CURRENT MODEL STATUS")
    print("="*60)

    if design_generator.use_openrouter and design_generator.client:
        print("Design Generation: OpenRouter API")
        print(f"   Model: {design_generator.model}")
        print("   Status: Working")
    else:
        print("Design Generation: Offline Fallback Mode")
        print("   Status: Using context-aware fallback designs")

    image_info = design_generator.get_image_generation_info()
    if image_info['image_generation_available']:
        print("Image Generation: OpenRouter API")
        print(f"   Model: {image_info['current_model']}")
        print(f"   Status: {image_info['api_status']}")
    else:
        print("Image Generation: Offline Fallback Mode")
        print("   Status: Using enhanced placeholder images")

    print("="*60)
    return image_info

if __name__ == "__main__":
    check_current_model_status()
