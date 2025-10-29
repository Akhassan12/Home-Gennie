# services/design_generator.py - PURE GEMINI + OFFLINE DESIGN GENERATION
"""
Design Generator Service - No OpenRouter dependency
Uses only Gemini API and intelligent offline fallbacks
"""
import os
from typing import Dict, List, Any
import base64
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Import Gemini Image Generator (with lazy loading to avoid circular imports)
GEMINI_AVAILABLE = False
gemini_image_generator = None

def _get_gemini_generator():
    """Lazy load Gemini generator to avoid circular imports"""
    global gemini_image_generator, GEMINI_AVAILABLE
    if gemini_image_generator is None:
        try:
            # Try importing with full path
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            services_dir = os.path.join(parent_dir, 'services')

            if services_dir not in sys.path:
                sys.path.insert(0, services_dir)

            from gemini_image_generator import gemini_image_generator
            GEMINI_AVAILABLE = True
            print("[SUCCESS] Gemini Image Generator loaded successfully")
        except ImportError as e:
            try:
                # Try alternative import
                from ..services.gemini_image_generator import gemini_image_generator
                GEMINI_AVAILABLE = True
                print("[SUCCESS] Gemini Image Generator loaded with relative import")
            except ImportError:
                try:
                    # Direct import
                    from services.gemini_image_generator import gemini_image_generator
                    GEMINI_AVAILABLE = True
                    print("[SUCCESS] Gemini Image Generator loaded with direct import")
                except ImportError as e2:
                    print(f"[WARNING] Gemini Image Generator not available: {e2}")
                    GEMINI_AVAILABLE = False
    return gemini_image_generator

# Try to import Gemini for design generation
try:
    import google.generativeai as genai
    GEMINI_TEXT_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_TEXT_AVAILABLE = False
    print("[WARNING] Google Generative AI not available for text generation")

class DesignGenerator:
    def __init__(self):
        """Initialize with Gemini API for text generation"""
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = None
        self.use_gemini = False

        if self.gemini_api_key and GEMINI_TEXT_AVAILABLE:
            try:
                # Configure Gemini
                genai.configure(api_key=self.gemini_api_key)

                # Test with text generation model
                self.gemini_model = genai.GenerativeModel('models/gemini-2.0-flash-exp')
                print("[SUCCESS] Gemini Design Generator initialized")
                self.use_gemini = True

            except Exception as e:
                print(f"[WARNING] Gemini text generation failed: {str(e)[:80]}")
                self.gemini_model = None
        else:
            print("[INFO] Using offline design generation only")

    def generate_design_suggestions(self, room_analysis: Dict[str, Any],
                                preferences: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generate design suggestions using Gemini or offline fallbacks"""
        if self.use_gemini and self.gemini_model:
            return self._generate_with_gemini(room_analysis, preferences)
        else:
            return self._get_fallback_designs(room_analysis)

    def _generate_with_gemini(self, room_analysis: Dict, preferences: Dict = None) -> List[Dict]:
        """Generate designs using Gemini API"""
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

            # Generate with Gemini
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=2000,
                    temperature=0.8,
                    top_p=0.9
                )
            )

            result = response.text
            print("[SUCCESS] Gemini design generation completed")

            # Parse JSON response
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()

            designs = json.loads(result)
            return designs if isinstance(designs, list) else [designs]

        except Exception as e:
            print(f"[WARNING] Gemini design generation failed: {str(e)[:100]}")
            return self._get_fallback_designs(room_analysis)

    def _get_fallback_designs(self, room_analysis: Dict) -> List[Dict]:
        """Generate context-aware fallback designs based on room analysis"""
        room_type = room_analysis.get('room_type', 'room').lower()
        room_size = room_analysis.get('room_size', 'medium').lower()
        current_style = room_analysis.get('current_style', {}).get('primary_style', 'basic').lower()

        # Base designs that can be customized based on room analysis
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

        # Customize designs based on room analysis
        customized_designs = []
        for design in base_designs:
            custom_design = design.copy()
            custom_design["design_name"] = design["name"]
            custom_design["color_palette"] = design["colors"]
            custom_design["key_elements"] = design["elements"]
            custom_design["lighting_plan"] = design["lighting"]
            custom_design["budget_estimate"] = design["budget"]
            custom_design["implementation_steps"] = design["steps"]

            # Customize based on room type
            if room_type == "bedroom":
                custom_design["design_name"] = f"Bedroom - {design['name']}"
                custom_design["description"] = f"Transform your bedroom into a {design['style'].lower()} sanctuary for rest and relaxation."
                custom_design["key_elements"] = [elem.replace("sofa", "bed").replace("Platform sofa", "Platform bed") for elem in design["elements"]]
            elif room_type == "kitchen":
                custom_design["design_name"] = f"Kitchen - {design['name']}"
                custom_design["description"] = f"Create a functional and stylish {design['style'].lower()} kitchen space."
                custom_design["key_elements"] = [elem.replace("sofa", "island").replace("Platform sofa", "Kitchen island") for elem in design["elements"]]
            elif room_type == "living_room" or room_type == "living room":
                custom_design["design_name"] = f"Living Room - {design['name']}"
                custom_design["description"] = f"Design a comfortable {design['style'].lower()} living space for relaxation and entertainment."
            elif room_type == "office":
                custom_design["design_name"] = f"Office - {design['name']}"
                custom_design["description"] = f"Create a productive {design['style'].lower()} workspace that inspires focus."
                custom_design["key_elements"] = [elem.replace("sofa", "desk").replace("Platform sofa", "Standing desk") for elem in design["elements"]]

            # Adjust for room size
            if room_size == "compact" or room_size == "small":
                custom_design["key_elements"] = custom_design["key_elements"][:3]  # Fewer elements for small spaces
                custom_design["description"] += " Optimized for smaller spaces with multi-functional furniture."
            elif room_size == "spacious" or room_size == "large":
                custom_design["key_elements"].append("Statement pieces")
                custom_design["key_elements"].append("Area rugs")
                custom_design["description"] += " Designed to take advantage of the larger space."

            customized_designs.append(custom_design)

        return customized_designs

    def generate_designs_offline(self, room_analysis: Dict, preferences: Dict = None) -> List[Dict]:
        """Generate designs completely offline without any API calls"""
        print("[INFO] Generating designs in offline mode...")

        room_type = room_analysis.get('room_type', 'room').lower()
        style_pref = preferences.get('style', 'modern').lower() if preferences else 'modern'

        # Create designs based on room type and style preference
        designs = []

        # Modern style designs
        if style_pref in ['modern', 'minimalist', 'contemporary']:
            if room_type == "living_room" or room_type == "living room":
                designs = [
                    {
                        "design_name": "Modern Living Space",
                        "style": "Modern",
                        "description": "Clean, functional living room with contemporary furniture and neutral tones.",
                        "color_palette": ["#FFFFFF", "#F8F8F8", "#2C2C2C", "#FF6B35"],
                        "key_elements": ["Sectional sofa", "Coffee table", "Floor lamp", "Abstract art", "Area rug"],
                        "lighting_plan": "Recessed lighting with floor lamps",
                        "budget_estimate": "Moderate",
                        "implementation_steps": ["Clear clutter", "Paint walls white", "Add modern furniture", "Install lighting", "Add textiles"]
                    },
                    {
                        "design_name": "Minimalist Living Room",
                        "style": "Minimalist",
                        "description": "Simple, uncluttered space focusing on essential furniture and clean lines.",
                        "color_palette": ["#FFFFFF", "#E8E8E8", "#333333", "#4A90E2"],
                        "key_elements": ["Simple sofa", "Side tables", "Table lamp", "Wall shelves", "Potted plants"],
                        "lighting_plan": "Natural light with minimal artificial lighting",
                        "budget_estimate": "Budget-friendly",
                        "implementation_steps": ["Remove unnecessary items", "Choose neutral colors", "Select simple furniture", "Maximize natural light", "Add minimal decor"]
                    }
                ]
            elif room_type == "bedroom":
                designs = [
                    {
                        "design_name": "Modern Bedroom Retreat",
                        "style": "Modern",
                        "description": "Peaceful bedroom with clean design and comfortable bedding.",
                        "color_palette": ["#F5F5F5", "#D4D4D4", "#2C2C2C", "#8E44AD"],
                        "key_elements": ["Platform bed", "Nightstands", "Table lamps", "Wall art", "Curtains"],
                        "lighting_plan": "Soft ambient lighting with reading lamps",
                        "budget_estimate": "Moderate",
                        "implementation_steps": ["Choose bed frame", "Add bedside tables", "Select comfortable bedding", "Install lighting", "Add window treatments"]
                    }
                ]
            else:
                # Generic modern design
                designs = [
                    {
                        "design_name": "Modern Space Design",
                        "style": "Modern",
                        "description": "Contemporary design with clean lines and functional layout.",
                        "color_palette": ["#FFFFFF", "#F0F0F0", "#333333", "#E74C3C"],
                        "key_elements": ["Modern furniture", "Clean lines", "Functional layout", "Quality materials", "Simple decor"],
                        "lighting_plan": "Layered lighting design",
                        "budget_estimate": "Moderate",
                        "implementation_steps": ["Plan layout", "Select furniture", "Choose colors", "Add lighting", "Style with decor"]
                    }
                ]

        # Traditional style designs
        elif style_pref in ['traditional', 'classic', 'rustic']:
            designs = [
                {
                    "design_name": "Classic Traditional Design",
                    "style": "Traditional",
                    "description": "Timeless design with classic furniture and warm colors.",
                    "color_palette": ["#F5F5DC", "#8B7355", "#D2B48C", "#654321"],
                    "key_elements": ["Wooden furniture", "Classic patterns", "Warm textiles", "Traditional art", "Decorative accessories"],
                    "lighting_plan": "Warm ambient lighting with chandeliers",
                    "budget_estimate": "Premium",
                    "implementation_steps": ["Choose wood tones", "Add classic pieces", "Layer textures", "Install traditional lighting", "Add personal touches"]
                }
            ]

        # If no specific matches, use general designs
        if not designs:
            designs = [
                {
                    "design_name": "Contemporary Style",
                    "style": "Contemporary",
                    "description": "Balanced design combining modern and traditional elements.",
                    "color_palette": ["#FFFFFF", "#E8E8E8", "#4A4A4A", "#FF8C42"],
                    "key_elements": ["Comfortable seating", "Functional tables", "Good lighting", "Personal decor", "Plants"],
                    "lighting_plan": "Mixed natural and artificial lighting",
                    "budget_estimate": "Moderate",
                    "implementation_steps": ["Assess space", "Choose furniture", "Add lighting", "Style surfaces", "Add finishing touches"]
                }
            ]

        return designs

    def force_fallback_mode(self) -> List[Dict]:
        """Force fallback mode for testing"""
        print("[INFO] Forcing fallback mode for design generation...")
        return self._get_fallback_designs({"room_type": "living_room"})

    def test_design_generation(self) -> Dict:
        """Test design generation functionality"""
        print("[TEST] Testing design generation...")

        # Test data
        test_room_analysis = {
            "room_type": "living_room",
            "room_size": "medium",
            "current_style": {"primary_style": "basic"}
        }

        try:
            # Test Gemini-based generation
            if self.use_gemini:
                print("[TEST] Testing Gemini-based generation...")
                designs = self.generate_design_suggestions(test_room_analysis)
                return {
                    'status': 'success',
                    'message': f'Generated {len(designs)} designs using Gemini',
                    'designs_count': len(designs),
                    'generation_method': 'gemini'
                }
            else:
                # Test fallback generation
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
        """
        Generate design suggestions with Gemini-generated images

        Args:
            room_analysis: Analysis of the room
            preferences: User preferences for design

        Returns:
            List of design concepts with generated images
        """
        # First generate the design concepts
        design_concepts = self.generate_design_suggestions(room_analysis, preferences)

        # Get Gemini generator (lazy loading)
        gemini_gen = _get_gemini_generator()

        if not GEMINI_AVAILABLE or not gemini_gen:
            print("⚠️ Gemini image generation not available, returning text-only designs")
            # Add placeholder images to designs
            for concept in design_concepts:
                concept['image_data'] = self._create_placeholder_image_data(concept)
                concept['image_status'] = 'placeholder'
            return design_concepts

        # Generate images for each design concept
        enhanced_designs = []

        for i, concept in enumerate(design_concepts[:3]):  # Limit to 3 designs
            try:
                print(f"🎨 Generating image for design: {concept.get('design_name', f'Design {i+1}')}")

                # Generate image using Gemini
                image_data = gemini_gen.generate_design_image(room_analysis, concept)

                # Add image data to the concept
                concept['image_data'] = image_data
                concept['image_status'] = 'generated' if image_data else 'fallback'

                # Add metadata about image generation
                concept['image_metadata'] = {
                    'generated_at': gemini_gen._get_current_timestamp(),
                    'generator': 'gemini' if gemini_gen.use_api else 'fallback',
                    'room_type': room_analysis.get('room_type', 'unknown'),
                    'design_style': concept.get('style', 'unknown')
                }

                enhanced_designs.append(concept)

            except Exception as e:
                print(f"❌ Error generating image for {concept.get('design_name', f'Design {i+1}')}: {e}")
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

            # Get colors from design palette
            colors = design_concept.get('color_palette', ['#FFFFFF', '#F5F5F5', '#333333'])
            primary_color = colors[0] if colors else '#FFFFFF'

            # Create image
            img = Image.new('RGB', (800, 600), primary_color)
            draw = ImageDraw.Draw(img)

            # Add design name as text overlay
            design_name = design_concept.get('design_name', 'Design Concept')
            style = design_concept.get('style', 'Style')

            # Try to add text (fallback if fonts not available)
            try:
                # Draw design name
                draw.text((400, 250), design_name, fill='black', anchor='mm')
                draw.text((400, 350), f"Style: {style}", fill='black', anchor='mm')
                draw.text((400, 450), "Design Preview", fill='black', anchor='mm')
            except:
                # Simple rectangle if text fails
                draw.rectangle([300, 200, 500, 400], outline='black', width=2)

            # Convert to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

            return f"data:image/png;base64,{img_base64}"

        except Exception as e:
            print(f"Error creating placeholder image: {e}")
            return ""

    def generate_single_design_with_image(self, room_analysis: Dict[str, Any],
                                        design_concept: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a single design concept with image

        Args:
            room_analysis: Analysis of the room
            design_concept: Specific design concept to visualize

        Returns:
            Enhanced design concept with generated image
        """
        # Get Gemini generator (lazy loading)
        gemini_gen = _get_gemini_generator()

        if not GEMINI_AVAILABLE or not gemini_gen:
            print("⚠️ Gemini image generation not available")
            design_concept['image_data'] = self._create_placeholder_image_data(design_concept)
            design_concept['image_status'] = 'placeholder'
            return design_concept

        try:
            print(f"🎨 Generating image for: {design_concept.get('design_name', 'Design')}")

            # Generate the image
            image_data = gemini_gen.generate_design_image(room_analysis, design_concept)

            # Add image data to concept
            design_concept['image_data'] = image_data
            design_concept['image_status'] = 'generated' if image_data else 'fallback'

            # Add metadata
            design_concept['image_metadata'] = {
                'generated_at': gemini_gen._get_current_timestamp(),
                'generator': 'gemini' if gemini_gen.use_api else 'fallback',
                'room_type': room_analysis.get('room_type', 'unknown'),
                'design_style': design_concept.get('style', 'unknown')
            }

            return design_concept

        except Exception as e:
            print(f"❌ Error in single design generation: {e}")
            design_concept['image_data'] = self._create_placeholder_image_data(design_concept)
            design_concept['image_status'] = 'error'
            design_concept['image_error'] = str(e)[:100]
            return design_concept

    def get_available_templates(self) -> List[Dict]:
        """Get available fallback templates from Gemini generator"""
        gemini_gen = _get_gemini_generator()
        if GEMINI_AVAILABLE and gemini_gen:
            return gemini_gen.get_fallback_templates()
        return []

    def cleanup_resources(self):
        """Clean up old templates and resources"""
        gemini_gen = _get_gemini_generator()
        if GEMINI_AVAILABLE and gemini_gen:
            removed_count = gemini_gen.cleanup_old_templates()
            return removed_count
        return 0

    def get_image_generation_info(self) -> Dict:
        """Get information about image generation status and model"""
        gemini_gen = _get_gemini_generator()
        if GEMINI_AVAILABLE and gemini_gen:
            model_info = gemini_gen.get_current_model_info()
            return {
                'image_generation_available': model_info['model_available'],
                'current_model': model_info['model_name'],
                'generation_method': model_info['generation_method'],
                'api_status': model_info['api_status'],
                'design_generation_method': 'gemini' if self.use_gemini else 'offline'
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

# Add a method to check current model status
def check_current_model_status():
    """Check and display current model status for both text and image generation"""
    print("\n" + "="*60)
    print("🤖 CURRENT MODEL STATUS")
    print("="*60)

    # Check design generation status
    if design_generator.use_gemini and design_generator.gemini_model:
        print("✅ Design Generation: Gemini API (Text)")
        print(f"   Model: {getattr(design_generator.gemini_model, 'model_name', 'Unknown')}")
        print("   Status: Working")
    else:
        print("⚠️ Design Generation: Offline Fallback Mode")
        print("   Status: Using context-aware fallback designs")

    # Check image generation status
    image_info = design_generator.get_image_generation_info()
    if image_info['image_generation_available']:
        print("✅ Image Generation: Gemini API")
        print(f"   Model: {image_info['current_model']}")
        print(f"   Status: {image_info['api_status']}")
    else:
        print("⚠️ Image Generation: Offline Fallback Mode")
        print("   Status: Using enhanced placeholder images")

    print("="*60)
    return image_info

if __name__ == "__main__":
    # When run directly, show model status
    check_current_model_status()
