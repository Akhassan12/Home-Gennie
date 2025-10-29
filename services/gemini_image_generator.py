#!/usr/bin/env python3
"""
OpenRouter Image Generation Service
Uses OpenRouter API for generating interior design images with database fallback
"""
import os
import base64
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False
    print("⚠️ openai package not installed")

# Import database models
def get_db_model():
    """Lazy import to avoid circular import"""
    try:
        from models.ar_models import GeneratedDesignTemplate, db as _db
        return GeneratedDesignTemplate, _db
    except ImportError:
        print("⚠️ Database models not available")
        return None, None

GeneratedDesignTemplate, db = get_db_model()
DB_AVAILABLE = GeneratedDesignTemplate is not None and db is not None

class GeminiImageGenerator:
    """Service for generating images using OpenRouter API"""

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
                    http_client = httpx.Client(timeout=60.0)

                    self.client = OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=self.openrouter_api_key,
                        http_client=http_client
                    )

                    # Test connection with Gemini image generation model
                    image_models = [
                        "gemini-2.0-flash-exp-image-generation"
                    ]

                    for model in image_models:
                        try:
                            print(f"[INFO] Testing image model: {model}")
                            # Simple test for image generation
                            test_response = self.client.images.generate(
                                model=model,
                                prompt="A simple test image of a room",
                                size="512x512",
                                n=1
                            )
                            if test_response and test_response.data:
                                self.image_model = model
                                print(f"✅ OpenRouter Image Generator initialized with {model}")
                                self.use_api = True
                                break
                        except Exception as model_error:
                            print(f"[WARNING] Model {model} failed: {str(model_error)[:50]}")
                            continue

                    if not self.use_api:
                        print("❌ No working image generation models found")

                finally:
                    # Restore proxy settings
                    for proxy_var, proxy_value in old_proxies.items():
                        os.environ[proxy_var] = proxy_value

            except Exception as e:
                print(f"❌ OpenRouter Image Generator failed: {str(e)[:80]}")
                self.client = None
        else:
            print("⚠️ Using fallback image generation")

    def generate_design_image(self, room_analysis: Dict[str, Any], design_concept: Dict[str, Any]) -> Optional[str]:
        """
        Generate an image based on room analysis and design concept

        Args:
            room_analysis: Analysis of the original room
            design_concept: Design concept to visualize

        Returns:
            Base64 encoded image data or None if failed
        """
        if not self.use_api or not self.client:
            print(f"[WARNING] Image generation not available, using fallback")
            return self._get_fallback_image_from_db(room_analysis, design_concept)

        try:
            # Create detailed prompt for image generation
            prompt = self._create_image_generation_prompt(room_analysis, design_concept)

            print(f"[INFO] Generating image for design: {design_concept.get('design_name', 'Unknown')}")
            print(f"[INFO] Using model: {self.image_model}")

            # Generate image using OpenRouter
            response = self.client.images.generate(
                model=self.image_model,
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )

            if response and response.data and response.data[0].url:
                image_url = response.data[0].url
                print(f"[SUCCESS] Image generated successfully: {image_url}")

                # Download and convert to base64
                import requests
                img_response = requests.get(image_url)
                if img_response.status_code == 200:
                    img_base64 = base64.b64encode(img_response.content).decode('utf-8')
                    image_data = f"data:image/png;base64,{img_base64}"

                    # Save successful generation to database for future fallback use
                    if image_data and DB_AVAILABLE:
                        self._save_generated_image_to_db(
                            room_analysis,
                            design_concept,
                            image_data,
                            prompt,
                            'openrouter',
                            'working'
                        )

                    return image_data
                else:
                    print(f"[WARNING] Failed to download generated image")
            else:
                print(f"[WARNING] Empty response from image generation")

            # Save failed attempt to database and get fallback
            if DB_AVAILABLE:
                self._save_generated_image_to_db(
                    room_analysis,
                    design_concept,
                    None,
                    prompt,
                    'openrouter',
                    'failed'
                )

            return self._get_fallback_image_from_db(room_analysis, design_concept)

        except Exception as e:
            print(f"[ERROR] Image generation failed: {str(e)[:100]}")

            # Save error to database and get fallback
            if DB_AVAILABLE:
                self._save_generated_image_to_db(
                    room_analysis,
                    design_concept,
                    None,
                    self._create_image_generation_prompt(room_analysis, design_concept),
                    'openrouter',
                    'error'
                )

            return self._get_fallback_image_from_db(room_analysis, design_concept)

    def _create_image_generation_prompt(self, room_analysis: Dict, design_concept: Dict) -> str:
        """Create a detailed prompt for image generation"""
        room_type = room_analysis.get('room_type', 'room')
        current_style = room_analysis.get('current_style', {}).get('primary_style', 'basic')

        design_name = design_concept.get('design_name', 'New Design')
        design_style = design_concept.get('style', 'modern')
        color_palette = design_concept.get('color_palette', ['#FFFFFF', '#F5F5F5', '#333333'])
        key_elements = design_concept.get('key_elements', ['modern furniture'])

        # Create a more detailed and specific prompt for better image generation
        prompt = f"""### 🧠 Prompt: Generate 3 Professional Interior Design Visualizations

You are an expert **architectural and interior visualization AI**.  
Your task is to **generate 3 detailed, realistic, and high-end interior design images** that illustrate the transformation of a room’s current style into a new design concept.

---

#### 🏠 ROOM INFORMATION:
- **Current room type:** {room_type}  
- **Current style:** {current_style}  
- **Room size:** {room_analysis.get('room_size', 'medium')}  
- **Room shape:** {room_analysis.get('room_shape', 'rectangular')}  

---

#### 🎨 DESIGN TRANSFORMATION:
- **New design name:** {design_name}  
- **Target style:** {design_style}  
- **Color palette:** {', '.join(color_palette[:4])}  
- **Key design elements:** {', '.join(key_elements[:5])}  

---

#### 👁️ VISUALIZATION REQUIREMENTS:
Create a professional interior design image that shows:

1. **Complete Room View:** Full room perspective showing all walls, floor, and ceiling.  
2. **Furniture Layout:** Strategic placement of all furniture and decor items.  
3. **Color Integration:** {design_style} color scheme applied throughout the space.  
4. **Lighting Design:** Natural and artificial lighting creating perfect ambiance.  
5. **Material Quality:** High-end materials and finishes appropriate for {design_style} style.  
6. **Spatial Flow:** Clear traffic patterns and functional zones.

---

#### 🧾 STYLE SPECIFICATIONS:
- **Design Style:** {design_style} interior design  
- **Quality Level:** Professional luxury interior design  
- **Lighting:** Realistic interior lighting with shadows and highlights  
- **Composition:** Centered, well-balanced room composition  
- **Details:** Include textures, patterns, and material finishes  

---

#### 💡 RENDERING STYLE:
Professional interior design visualization, architectural rendering, high resolution, detailed textures, realistic lighting, {design_style} aesthetic, **luxury interior design magazine quality**.  
Focus on creating an **aspirational yet realistic transformation** from **{current_style}** to **{design_style}**.

---

#### 🖼️ IMAGE OUTPUT:
Generate 3 unique images:
1. **Wide-Angle Room View** – Full perspective of the transformed room.  
2. **Design Details Close-Up** – Focus on textures, furniture, and decor.  
3. **Ambience & Mood Shot** – Capture the lighting and atmosphere.  

Each image should look **photo-realistic**, **stylistically consistent**, and **professionally composed**."""

        return prompt

    def _process_generated_image(self, response, design_concept: Dict) -> str:
        """Process the generated image response"""
        try:
            # This would depend on how Gemini returns generated images
            # For now, return a placeholder
            design_name = design_concept.get('design_name', 'Generated Design')

            # Create a simple colored placeholder based on the design palette
            return self._create_design_placeholder(design_concept)

        except Exception as e:
            print(f"Error processing generated image: {e}")
            return self._create_design_placeholder(design_concept)

    def _create_design_placeholder(self, design_concept: Dict) -> str:
        """Create a design-specific placeholder image"""
        try:
            from PIL import Image, ImageDraw
            import io

            # Get colors from design palette
            colors = design_concept.get('color_palette', ['#FFFFFF', '#F5F5F5', '#333333'])
            primary_color = colors[0] if colors else '#FFFFFF'
            secondary_color = colors[1] if len(colors) > 1 else '#F5F5F5'
            accent_color = colors[2] if len(colors) > 2 else '#333333'

            # Create image with gradient
            img = Image.new('RGB', (800, 600), primary_color)
            draw = ImageDraw.Draw(img)

            # Add gradient effect
            for i in range(600):
                r = int(int(primary_color[1:3], 16) + (int(secondary_color[1:3], 16) - int(primary_color[1:3], 16)) * i // 600)
                g = int(int(primary_color[3:5], 16) + (int(secondary_color[3:5], 16) - int(primary_color[3:5], 16)) * i // 600)
                b = int(int(primary_color[5:7], 16) + (int(secondary_color[5:7], 16) - int(primary_color[5:7], 16)) * i // 600)
                draw.line([(0, i), (800, i)], fill=(r, g, b))

            # Add design name as text
            design_name = design_concept.get('design_name', 'Design Concept')
            design_style = design_concept.get('style', 'Modern')

            try:
                # Draw design name
                draw.text((400, 250), design_name, fill=accent_color, anchor='mm')
                draw.text((400, 320), f"Style: {design_style}", fill=accent_color, anchor='mm')

                # Add color palette indicators
                start_y = 380
                for i, color in enumerate(colors[:4]):
                    draw.rectangle([350 + i*30, start_y, 370 + i*30, start_y + 20], fill=color, outline=accent_color)

                draw.text((400, start_y + 30), "Design Preview", fill=accent_color, anchor='mm')

            except:
                # Simple fallback if text fails
                draw.rectangle([300, 200, 500, 400], outline=accent_color, width=2)
                draw.text((400, 300), "Design", fill=accent_color, anchor='mm')

            # Convert to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

            return f"data:image/png;base64,{img_base64}"

        except Exception as e:
            print(f"Error creating placeholder: {e}")
            # Return a simple fallback base64 image (1x1 white PNG)
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

    def _create_enhanced_placeholder(self, design_concept: Dict, prompt: str) -> str:
        """Create an enhanced placeholder with design details"""
        try:
            from PIL import Image, ImageDraw
            import io

            # Get colors from design palette
            colors = design_concept.get('color_palette', ['#FFFFFF', '#F5F5F5', '#333333', '#E67E22'])
            primary_color = colors[0] if colors else '#FFFFFF'
            secondary_color = colors[1] if len(colors) > 1 else '#F5F5F5'
            accent_color = colors[2] if len(colors) > 2 else '#333333'

            # Create image with gradient background
            img = Image.new('RGB', (800, 600), primary_color)
            draw = ImageDraw.Draw(img)

            # Add gradient effect
            for i in range(600):
                r = int(int(primary_color[1:3], 16) + (int(secondary_color[1:3], 16) - int(primary_color[1:3], 16)) * i // 600)
                g = int(int(primary_color[3:5], 16) + (int(secondary_color[3:5], 16) - int(primary_color[3:5], 16)) * i // 600)
                b = int(int(primary_color[5:7], 16) + (int(secondary_color[5:7], 16) - int(primary_color[5:7], 16)) * i // 600)
                draw.line([(0, i), (800, i)], fill=(r, g, b))

            # Add design name as text
            design_name = design_concept.get('design_name', 'Design Concept')
            design_style = design_concept.get('style', 'Modern')

            try:
                # Draw design name (larger font)
                draw.text((400, 250), design_name, fill=accent_color, anchor='mm')
                draw.text((400, 320), f"Style: {design_style}", fill=accent_color, anchor='mm')

                # Add color palette indicators
                start_y = 380
                for i, color in enumerate(colors[:4]):
                    draw.rectangle([350 + i*30, start_y, 370 + i*30, start_y + 20], fill=color, outline=accent_color)

                draw.text((400, start_y + 30), "Design Preview", fill=accent_color, anchor='mm')

            except:
                # Simple fallback if text fails
                draw.rectangle([300, 200, 500, 400], outline=accent_color, width=2)
                draw.text((400, 300), "Design", fill=accent_color, anchor='mm')

            # Convert to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

            return f"data:image/png;base64,{img_base64}"

        except Exception as e:
            print(f"Error creating enhanced placeholder: {e}")
            return self._create_design_placeholder(design_concept)

    def _get_fallback_image(self, design_concept: Dict) -> str:
        """Return fallback image"""
        return self._create_design_placeholder(design_concept)

    def _save_generated_image_to_db(self, room_analysis: Dict, design_concept: Dict,
                                   image_data: str, prompt: str, generated_by: str, api_status: str):
        """Save generated image to database for future fallback use"""
        if not DB_AVAILABLE or not GeneratedDesignTemplate:
            return False

        try:
            # Create unique template ID
            template_id = f"template_{uuid.uuid4().hex[:16]}"

            # Extract design information
            design_name = design_concept.get('design_name', 'Generated Design')
            design_style = design_concept.get('style', 'modern')
            room_type = room_analysis.get('room_type', 'room')
            room_size = room_analysis.get('room_size', 'medium')
            room_shape = room_analysis.get('room_shape', 'rectangular')

            # Convert data to JSON strings
            color_palette = json.dumps(design_concept.get('color_palette', []))
            key_elements = json.dumps(design_concept.get('key_elements', []))
            design_concept_json = json.dumps(design_concept)

            # Create database record
            template = GeneratedDesignTemplate(
                template_id=template_id,
                design_name=design_name,
                design_style=design_style,
                room_type=room_type,
                room_size=room_size,
                room_shape=room_shape,
                color_palette=color_palette,
                key_elements=key_elements,
                design_concept=design_concept_json,
                image_data=image_data if image_data else '',
                generation_prompt=prompt,
                generated_by=generated_by,
                api_key_status=api_status,
                is_active=True
            )

            db.session.add(template)
            db.session.commit()

            print(f"💾 Saved design template '{design_name}' to database")
            return True

        except Exception as e:
            print(f"Error saving template to database: {e}")
            if db:
                db.session.rollback()
            return False

    def _get_fallback_image_from_db(self, room_analysis: Dict, design_concept: Dict) -> str:
        """Get fallback image from database templates"""
        if not DB_AVAILABLE or not GeneratedDesignTemplate:
            print("⚠️ Database not available, using placeholder fallback")
            return self._create_design_placeholder(design_concept)

        try:
            # Try to find matching templates in database
            design_style = design_concept.get('style', 'modern')
            room_type = room_analysis.get('room_type', 'room')

            # Look for templates with same style and room type
            templates = GeneratedDesignTemplate.query.filter_by(
                design_style=design_style,
                room_type=room_type,
                is_active=True
            ).order_by(GeneratedDesignTemplate.usage_count.desc()).limit(5).all()

            if templates:
                # Use the most popular template (highest usage count)
                best_template = templates[0]
                best_template.increment_usage()

                print(f"📋 Using database fallback template: {best_template.design_name}")
                return best_template.image_data

            # If no style/room match, look for any active template
            fallback_templates = GeneratedDesignTemplate.query.filter_by(
                is_active=True
            ).order_by(GeneratedDesignTemplate.usage_count.desc()).limit(3).all()

            if fallback_templates:
                template = fallback_templates[0]
                template.increment_usage()

                print(f"📋 Using generic fallback template: {template.design_name}")
                return template.image_data

            # If no templates in database, create and save a new placeholder
            print("📋 No templates in database, creating new fallback")
            placeholder_image = self._create_design_placeholder(design_concept)

            if placeholder_image:
                self._save_generated_image_to_db(
                    room_analysis,
                    design_concept,
                    placeholder_image,
                    self._create_image_generation_prompt(room_analysis, design_concept),
                    'fallback',
                    'placeholder'
                )

            return placeholder_image

        except Exception as e:
            print(f"Error getting fallback from database: {e}")
            return self._create_design_placeholder(design_concept)

    def get_fallback_templates(self, limit: int = 10) -> List[Dict]:
        """Get available fallback templates from database"""
        if not DB_AVAILABLE or not GeneratedDesignTemplate:
            return []

        try:
            templates = GeneratedDesignTemplate.query.filter_by(
                is_active=True
            ).order_by(GeneratedDesignTemplate.usage_count.desc()).limit(limit).all()

            return [template.to_dict() for template in templates]

        except Exception as e:
            print(f"Error getting fallback templates: {e}")
            return []

    def mark_template_as_fallback(self, template_id: str) -> bool:
        """Mark a template as a fallback option"""
        if not DB_AVAILABLE or not GeneratedDesignTemplate:
            return False

        try:
            template = GeneratedDesignTemplate.query.filter_by(template_id=template_id).first()
            if template:
                template.mark_as_fallback()
                print(f"✅ Marked template '{template.design_name}' as fallback")
                return True
            return False

        except Exception as e:
            print(f"Error marking template as fallback: {e}")
            return False

    def update_api_key_status(self, status: str) -> bool:
        """Update API key status in all templates"""
        if not DB_AVAILABLE or not GeneratedDesignTemplate:
            return False

        try:
            # Update all templates with current API status
            templates = GeneratedDesignTemplate.query.filter_by(generated_by='gemini').all()
            for template in templates:
                template.update_api_status(status)

            print(f"💾 Updated {len(templates)} templates with API status: {status}")
            return True

        except Exception as e:
            print(f"Error updating API status: {e}")
            return False

    def cleanup_old_templates(self, days_old: int = 30) -> int:
        """Clean up old unused templates"""
        if not DB_AVAILABLE or not GeneratedDesignTemplate:
            return 0

        try:
            from datetime import timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            old_templates = GeneratedDesignTemplate.query.filter(
                GeneratedDesignTemplate.created_at < cutoff_date,
                GeneratedDesignTemplate.usage_count == 0
            ).all()

            count = len(old_templates)
            for template in old_templates:
                db.session.delete(template)

            db.session.commit()

            if count > 0:
                print(f"🗑️ Cleaned up {count} old unused templates")

            return count

        except Exception as e:
            print(f"Error cleaning up templates: {e}")
            if db:
                db.session.rollback()
            return 0

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat()

    def generate_multiple_designs(self, room_analysis: Dict, design_concepts: List[Dict]) -> List[Dict]:
        """Generate images for multiple design concepts"""
        results = []

        for i, concept in enumerate(design_concepts[:3]):  # Generate up to 3 images
            image_data = self.generate_design_image(room_analysis, concept)

            results.append({
                'design_name': concept.get('design_name', f'Design {i+1}'),
                'design_style': concept.get('style', 'Modern'),
                'image_data': image_data,
                'status': 'generated' if image_data else 'fallback'
            })

        return results

    def get_current_model_info(self) -> Dict:
        """Get information about the currently used image generation model"""
        if self.image_model and self.use_api:
            return {
                'model_available': True,
                'model_name': self.image_model,
                'generation_method': 'openrouter_api',
                'api_status': 'working'
            }
        else:
            return {
                'model_available': False,
                'model_name': 'None',
                'generation_method': 'offline_fallback',
                'api_status': 'unavailable'
            }

# Create singleton instance
gemini_image_generator = GeminiImageGenerator()
