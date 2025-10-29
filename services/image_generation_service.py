"""
Image Generation Service
Implements the architecture: Generate → Save Image → Storage → URL → AI Api Call → BASE64 → Save → Database
"""
import os
import base64
import uuid
import json
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from PIL import Image
import io
import torch
from flask import current_app
from services.ai_image_analyzer import ai_analyzer
from services.design_generator import design_generator

# Qwen Image Editing Pipeline
try:
    from diffusers import QwenImageEditPlusPipeline
    QWEN_AVAILABLE = True
except ImportError:
    QWEN_AVAILABLE = False

# OpenAI for OpenRouter API
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    openai = None
    OPENAI_AVAILABLE = False

# Google Generative AI
try:
    import google.generativeai as genai
    from google.generativeai import types
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GENAI_AVAILABLE = False

class ImageStorageService:
    """Handles local image storage with URL generation"""

    def __init__(self, upload_folder: str = 'static/generated_images'):
        self.upload_folder = upload_folder
        self.base_url = '/static/generated_images'
        os.makedirs(upload_folder, exist_ok=True)

    def save_image_from_url(self, image_url: str, filename: str = None) -> Tuple[str, str]:
        """
        Download and save image from URL to local storage

        Args:
            image_url: URL of the image to download
            filename: Optional custom filename

        Returns:
            Tuple of (file_path, public_url)
        """
        try:
            # Generate unique filename if not provided
            if not filename:
                filename = f"{uuid.uuid4()}.png"

            # Ensure filename has extension
            if not '.' in filename:
                filename += '.png'

            file_path = os.path.join(self.upload_folder, filename)

            # Download image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # Save image
            with open(file_path, 'wb') as f:
                f.write(response.content)

            # Generate public URL
            public_url = f"{self.base_url}/{filename}"

            return file_path, public_url

        except Exception as e:
            print(f"Error saving image from URL: {e}")
            raise

    def save_image_from_base64(self, base64_data: str, filename: str = None) -> Tuple[str, str]:
        """
        Save BASE64 image data to local storage

        Args:
            base64_data: BASE64 encoded image data
            filename: Optional custom filename

        Returns:
            Tuple of (file_path, public_url)
        """
        try:
            # Generate unique filename if not provided
            if not filename:
                filename = f"{uuid.uuid4()}.png"

            # Ensure filename has extension
            if not '.' in filename:
                filename += '.png'

            file_path = os.path.join(self.upload_folder, filename)

            # Decode and save image
            if 'base64,' in base64_data:
                base64_data = base64_data.split('base64,')[1]

            image_data = base64.b64decode(base64_data)

            # Validate image data
            try:
                image = Image.open(io.BytesIO(image_data))
                image.verify()
                image = Image.open(io.BytesIO(image_data))  # Re-open after verify
                image.save(file_path)
            except Exception as img_error:
                print(f"Invalid image data: {img_error}")
                raise ValueError(f"Invalid image data: {img_error}")

            # Generate public URL
            public_url = f"{self.base_url}/{filename}"

            return file_path, public_url

        except Exception as e:
            print(f"Error saving BASE64 image: {e}")
            raise

    def convert_image_to_base64(self, file_path: str) -> str:
        """
        Convert image file to BASE64 string

        Args:
            file_path: Path to image file

        Returns:
            BASE64 encoded string with data URL prefix
        """
        try:
            with open(file_path, 'rb') as image_file:
                image_data = image_file.read()

            # Convert to BASE64
            base64_data = base64.b64encode(image_data).decode('utf-8')

            # Determine image format
            with Image.open(file_path) as img:
                format_lower = img.format.lower() if img.format else 'png'

            return f"data:image/{format_lower};base64,{base64_data}"

        except Exception as e:
            print(f"Error converting image to BASE64: {e}")
            raise

class ImageGenerationProcess:
    """Main service implementing the architecture flow"""

    def __init__(self):
        self.storage_service = ImageStorageService()
        self.ai_analyzer = ai_analyzer
        self.design_generator = design_generator
        self.qwen_pipeline = None
        if QWEN_AVAILABLE:
            self._initialize_qwen_pipeline()

    def _initialize_qwen_pipeline(self):
        """Initialize the Qwen image editing pipeline"""
        try:
            print("Initializing Qwen image editing pipeline...")
            self.qwen_pipeline = QwenImageEditPlusPipeline.from_pretrained(
                "Qwen/Qwen-Image-Edit-2509",
                torch_dtype=torch.bfloat16
            )
            print("Qwen pipeline loaded successfully")

            # Move to GPU if available
            if torch.cuda.is_available():
                self.qwen_pipeline.to('cuda')
                print("Qwen pipeline moved to CUDA")
            else:
                print("CUDA not available, using CPU")

            # Configure progress bar
            self.qwen_pipeline.set_progress_bar_config(disable=None)
            print("Qwen pipeline initialized successfully")

        except Exception as e:
            print(f"Error initializing Qwen pipeline: {e}")
            self.qwen_pipeline = None

    def execute_image_generation_flow(self, room_image_data: str, room_type: str = None) -> Dict[str, Any]:
        """
        Execute the complete image generation flow as per the architecture diagram

        Args:
            room_image_data: BASE64 encoded room image
            room_type: Optional room type hint

        Returns:
            Complete process results with all URLs and metadata
        """
        process_id = str(uuid.uuid4())
        process_start = datetime.utcnow()

        try:
            # Step 1: Save original room image to storage
            original_filename = f"original_{process_id}.png"
            original_file_path, original_url = self.storage_service.save_image_from_base64(
                room_image_data, original_filename
            )

            # Step 2: Analyze the room image using AI
            analysis = self.ai_analyzer.analyze_room_image(room_image_data, room_type)

            # Step 3: Generate design suggestions
            designs = self.design_generator.generate_design_suggestions(analysis)

            # Step 4: Generate actual design images (not just prompts)
            generated_images = []
            for i, design in enumerate(designs[:3]):  # Generate 3 design images
                design_image_result = self._generate_design_image(room_image_data, design, process_id, i)
                if design_image_result:
                    generated_images.append(design_image_result)

            # Step 5: Save all process data to database (we'll create a model for this)
            process_metadata = {
                'process_id': process_id,
                'original_image_url': original_url,
                'analysis': analysis,
                'designs': designs,
                'generated_images': generated_images,
                'status': 'completed',
                'created_at': process_start.isoformat()
            }

            # Step 6: Convert final images to BASE64 for frontend use
            base64_images = []
            for gen_image in generated_images:
                if 'final_image_url' in gen_image:
                    file_path = gen_image['final_image_url'].replace('/static/generated_images/', 'static/generated_images/')
                    try:
                        base64_image = self.storage_service.convert_image_to_base64(file_path)
                        base64_images.append({
                            'design_name': gen_image.get('design_name', 'Generated Design'),
                            'base64_data': base64_image,
                            'metadata': gen_image
                        })
                    except Exception as e:
                        print(f"Error converting image to BASE64: {e}")

            return {
                'success': True,
                'process_id': process_id,
                'original_image_url': original_url,
                'analysis': analysis,
                'designs': designs,
                'generated_images': generated_images,
                'base64_images': base64_images,
                'process_metadata': process_metadata
            }

        except Exception as e:
            print(f"Error in image generation flow: {e}")
            return {
                'success': False,
                'process_id': process_id,
                'error': str(e),
                'status': 'failed'
            }

    def _generate_design_image(self, room_image_data: str, design: Dict[str, Any], process_id: str, design_index: int) -> Optional[Dict[str, Any]]:
        """
        Generate a design image based on the user's actual room image using Qwen pipeline

        Args:
            room_image_data: Original room image BASE64 data
            design: Design concept dictionary
            process_id: Process ID for file naming
            design_index: Index of the design (for naming)

        Returns:
            Dictionary with design image URLs and metadata
        """
        try:
            design_name = design.get('design_name', f'Design_{design_index + 1}')
            style = design.get('style', 'modern')
            color_palette = design.get('color_palette', ['#FFFFFF', '#F5F5F5', '#333333'])

            # Create a personalized image generation prompt based on the user's actual room
            prompt = f"""Transform this exact room image to show a {style} interior design makeover.

Design Transformation Details:
- Design Name: {design_name}
- Target Style: {style}
- New Color Palette: {', '.join(color_palette[:4])}
- Key Design Elements: {', '.join(design.get('key_elements', ['modern furniture', 'updated lighting', 'new decor'])[:5])}

Requirements:
- Use this exact room layout and structure as the base
- Apply {style} design principles to transform the space
- Update wall colors, furniture, lighting, and decor
- Maintain the same room dimensions and architectural features
- Show realistic design changes that could actually be implemented
- Create a professional interior design visualization

Design Changes to Show:
- Replace existing furniture with {style}-appropriate pieces
- Update wall colors and finishes to match the new palette
- Add appropriate lighting fixtures for {style} aesthetic
- Include decorative elements that complement the {style} theme
- Arrange everything to create a cohesive {style} space

The result should be a realistic visualization of how this exact room would look after the {style} transformation."""

            design_filename = f"design_{process_id}_{design_index}.png"
            design_file_path = os.path.join(self.storage_service.upload_folder, design_filename)

            # Check if Qwen pipeline is available and use it
            if self.qwen_pipeline is not None:
                try:
                    # Decode the base64 room image data to PIL Image
                    if 'base64,' in room_image_data:
                        room_image_data = room_image_data.split('base64,')[1]

                    room_image_bytes = base64.b64decode(room_image_data)
                    room_image = Image.open(io.BytesIO(room_image_bytes))

                    # Generate the design image using Qwen pipeline
                    print(f"Generating design image {design_index + 1} using Qwen pipeline...")

                    # Use the Qwen pipeline for image editing
                    with torch.inference_mode():
                        output = self.qwen_pipeline(
                            image=[room_image],
                            prompt=prompt,
                            generator=torch.manual_seed(0),
                            true_cfg_scale=4.0,
                            negative_prompt=" ",
                            num_inference_steps=40,
                            guidance_scale=1.0,
                            num_images_per_prompt=1,
                        )

                    # Save the generated image
                    output_image = output.images[0]
                    output_image.save(design_file_path)
                    print(f"Design image {design_index + 1} saved successfully")

                    design_url = f"{self.storage_service.base_url}/{design_filename}"

                    return {
                        'design_name': design_name,
                        'design_style': style,
                        'design_description': design.get('description', ''),
                        'color_palette': color_palette,
                        'final_image_url': design_url,
                        'design_index': design_index,
                        'status': 'generated',
                        'image_generation_prompt': prompt,
                        'generation_method': 'qwen_pipeline',
                        'note': 'Design generated using Qwen image editing pipeline'
                    }

                except Exception as e:
                    print(f"Error using Qwen pipeline for design {design_index + 1}: {e}")
                    print("Falling back to placeholder generation...")
                    # Fall back to placeholder if Qwen fails

            # Fallback: Create a style-specific placeholder that matches the design concept
            print(f"Creating placeholder for design {design_index + 1}")
            placeholder_image = self._create_design_specific_placeholder(design, style)
            placeholder_image.save(design_file_path)

            design_url = f"{self.storage_service.base_url}/{design_filename}"

            return {
                'design_name': design_name,
                'design_style': style,
                'design_description': design.get('description', ''),
                'color_palette': color_palette,
                'design_image_url': design_url,
                'design_index': design_index,
                'status': 'generated',
                'image_generation_prompt': prompt,
                'generation_method': 'placeholder',
                'note': 'Placeholder design (Qwen pipeline unavailable)'
            }

        except Exception as e:
            print(f"Error generating design image: {e}")
            return None

    def _create_design_specific_placeholder(self, design: Dict[str, Any], style: str) -> Image.Image:
        """
        Create a design-specific placeholder image based on style

        Args:
            design: Design concept dictionary
            style: Design style for color selection

        Returns:
            PIL Image object
        """
        width, height = 800, 600
        colors = design.get('color_palette', [])

        # Select background color based on style
        style_colors = {
            'minimalist': (250, 250, 250),
            'scandinavian': (248, 248, 248),
            'industrial': (44, 44, 44),
            'bohemian': (245, 245, 220),
            'contemporary': (240, 240, 240),
            'farmhouse': (245, 245, 220),
            'modern': (248, 248, 248)
        }

        # Use style-specific color or first color from palette
        if colors and len(colors) > 0:
            try:
                first_color = colors[0].lstrip('#')
                rgb_color = tuple(int(first_color[i:i+2], 16) for i in (0, 2, 4))
            except:
                rgb_color = style_colors.get(style.lower(), (245, 245, 245))
        else:
            rgb_color = style_colors.get(style.lower(), (245, 245, 245))

        # Create gradient effect for more visual interest
        image = Image.new('RGB', (width, height), rgb_color)

        # Add some texture/pattern based on style
        if style.lower() == 'minimalist':
            # Simple geometric pattern
            from PIL import ImageDraw
            draw = ImageDraw.Draw(image)
            draw.rectangle([width//4, height//4, width*3//4, height*3//4], fill=(rgb_color[0]-10, rgb_color[1]-10, rgb_color[2]-10))
        elif style.lower() == 'scandinavian':
            # Warm, cozy feel
            overlay_color = (rgb_color[0]+5, rgb_color[1]+3, rgb_color[2]+1)
            overlay = Image.new('RGB', (width, height), overlay_color)
            image = Image.blend(image, overlay, 0.3)

        return image

    def _create_placeholder_design_image(self, design: Dict[str, Any]) -> Image.Image:
        """
        Create a placeholder design image (replace with actual AI image generation)

        Args:
            design: Design concept dictionary

        Returns:
            PIL Image object
        """
        # Create a simple colored rectangle as placeholder
        width, height = 800, 600
        colors = design.get('color_palette', ['#FFFFFF', '#F5F5F5', '#333333'])

        # Create image with main color as background
        try:
            main_color = colors[0].lstrip('#')
            rgb_color = tuple(int(main_color[i:i+2], 16) for i in (0, 2, 4))
        except:
            rgb_color = (245, 245, 245)  # Default light gray

        image = Image.new('RGB', (width, height), rgb_color)

        return image

# Create singleton instance
image_generation_service = ImageGenerationProcess()
