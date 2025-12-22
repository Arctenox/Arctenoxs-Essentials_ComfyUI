"""
Arctenox Essentials - Prompt Styler (Enhanced)
===============================================

Pre-defined style templates for instant prompt enhancement.
Expanded with 40+ styles optimized for Illustrious/SDXL/NoobAI/Pony.

Features:
- 40+ professional style presets
- Quality tier system (draft/standard/high/ultimate)
- Automatic negative prompt suggestions
- Combinable style modifiers
- Custom style support
- Optimized for modern SDXL-based models

Author: Arctenox
Version: 1.1.0
License: GPL-3.0
"""


class PromptStyler:
    """
    Apply pre-defined style templates to prompts.
    
    Enhances base prompts with professional styling without requiring
    users to memorize complex quality tags and style-specific terminology.
    """
    
    # Style templates with positive and negative additions
    STYLE_TEMPLATES = {
        "None": {
            "positive": "",
            "negative": ""
        },
        # Photography Styles
        "Cinematic": {
            "positive": "cinematic lighting, dramatic shadows, film grain, depth of field, bokeh, professional color grading, 35mm film, anamorphic lens",
            "negative": "flat lighting, amateur, smartphone photo, overexposed, underexposed"
        },
        "Photorealistic": {
            "positive": "photorealistic, hyper detailed, professional photography, 8k uhd, dslr, soft lighting, high quality, film grain, Fujifilm XT3",
            "negative": "drawing, painting, illustration, cartoon, anime, rendered, fake, artificial"
        },
        "Studio Portrait": {
            "positive": "studio portrait, professional lighting, clean background, sharp focus, well-lit, posed, high-end photography",
            "negative": "candid, casual, snapshot, blurry, amateur, poor lighting"
        },
        "Landscape": {
            "positive": "landscape photography, golden hour, vast scenery, natural lighting, atmospheric perspective, majestic, wide angle",
            "negative": "portrait, close-up, indoor, studio, cluttered, narrow view"
        },
        "Macro": {
            "positive": "macro photography, extreme close-up, shallow depth of field, detailed texture, sharp focus point, ring light",
            "negative": "wide angle, distant, landscape, low detail, deep focus"
        },
        "Street Photography": {
            "positive": "street photography, candid moment, urban environment, natural light, documentary style, authentic, raw",
            "negative": "staged, studio, posed, artificial lighting, oversaturated"
        },
        "Fashion Photography": {
            "positive": "fashion photography, editorial style, high fashion, dramatic lighting, professional model pose, glamorous, vogue style",
            "negative": "casual, amateur, poor composition, unflattering angles, bad lighting"
        },
        "Black and White": {
            "positive": "black and white photography, monochrome, high contrast, dramatic shadows, grayscale, fine art photography",
            "negative": "color, colorful, vibrant, saturated, chromatic"
        },
        "HDR": {
            "positive": "HDR photography, high dynamic range, enhanced details, vivid colors, tone mapped, surreal clarity",
            "negative": "flat, low contrast, washed out, underexposed, dull"
        },
        "Long Exposure": {
            "positive": "long exposure, motion blur, light trails, smooth water, dreamy atmosphere, ethereal, time-lapse effect",
            "negative": "frozen motion, sharp, static, instant capture, fast shutter"
        },
        
        # Anime/Illustration Styles
        "Anime": {
            "positive": "anime style, vibrant colors, clean lineart, cel shaded, studio anime, detailed eyes, expressive",
            "negative": "realistic, photographic, 3d render, western cartoon, sketchy, messy lines"
        },
        "Manga": {
            "positive": "manga style, black and white, screentone, dynamic composition, expressive linework, Japanese comic style",
            "negative": "color, photorealistic, western comic, painted, soft edges"
        },
        "Chibi": {
            "positive": "chibi style, super deformed, cute, big head small body, simplified features, adorable, kawaii",
            "negative": "realistic proportions, detailed anatomy, mature, serious, photorealistic"
        },
        "Webtoon": {
            "positive": "webtoon style, digital art, clean lines, vibrant colors, Korean manhwa style, vertical scroll format",
            "negative": "traditional manga, black and white, sketchy, watercolor, oil painting"
        },
        "Visual Novel": {
            "positive": "visual novel art, detailed character design, anime aesthetic, clean background, professional illustration",
            "negative": "sketchy, unfinished, rough, messy, low quality"
        },
        "Light Novel": {
            "positive": "light novel illustration, anime art style, detailed coloring, professional grade, cover art quality",
            "negative": "rough sketch, unpolished, amateur, western style, photorealistic"
        },
        
        # Artistic Styles
        "Oil Painting": {
            "positive": "oil painting, classical art style, brush strokes visible, textured canvas, rich colors, masterpiece, fine art",
            "negative": "digital art, photograph, smooth, flat, modern, cgi"
        },
        "Watercolor": {
            "positive": "watercolor painting, soft edges, flowing colors, artistic, traditional media, paper texture, delicate",
            "negative": "digital, sharp edges, photograph, 3d render, harsh lines"
        },
        "Impressionist": {
            "positive": "impressionist painting, loose brushwork, light and color emphasis, outdoor scene, soft focus, artistic",
            "negative": "realistic, detailed, sharp, photographic, precise, technical"
        },
        "Art Nouveau": {
            "positive": "art nouveau style, flowing lines, organic forms, decorative, ornate details, elegant curves, vintage poster",
            "negative": "minimalist, modern, geometric, industrial, plain, simple"
        },
        "Pop Art": {
            "positive": "pop art style, bold colors, high contrast, graphic design, comic book influence, Andy Warhol style, vibrant",
            "negative": "realistic, muted colors, subtle, traditional, classical, painterly"
        },
        "Abstract": {
            "positive": "abstract art, non-representational, geometric shapes, bold colors, modern art, expressive, contemporary",
            "negative": "realistic, photographic, detailed, representational, traditional"
        },
        "Sketch": {
            "positive": "pencil sketch, hand drawn, loose lines, artistic, traditional drawing, graphite, study drawing",
            "negative": "finished painting, digital, photographic, polished, colored"
        },
        "Ink Drawing": {
            "positive": "ink drawing, line art, pen and ink, cross hatching, detailed linework, traditional illustration",
            "negative": "painted, colored, digital, photographic, soft edges"
        },
        
        # Digital Art Styles
        "Digital Painting": {
            "positive": "digital painting, concept art, detailed illustration, professional digital art, painterly style, artstation quality",
            "negative": "photograph, 3d render, low quality, amateur, unfinished"
        },
        "Concept Art": {
            "positive": "concept art, professional illustration, detailed environment, matte painting, cinematic composition, artstation trending",
            "negative": "amateur, low detail, unfinished, simple, basic"
        },
        "Comic Book": {
            "positive": "comic book art, bold lines, dynamic composition, speech bubbles style, vibrant colors, action pose, graphic novel",
            "negative": "realistic, photographic, soft, muted, subtle, painterly"
        },
        "Pixel Art": {
            "positive": "pixel art, retro gaming aesthetic, 16-bit style, limited color palette, sharp pixels, nostalgic",
            "negative": "smooth, high resolution, photorealistic, modern, blurry"
        },
        "Low Poly": {
            "positive": "low poly, geometric, faceted, stylized 3d, clean edges, minimalist 3d art, isometric",
            "negative": "high poly, realistic, detailed textures, photorealistic, smooth surfaces"
        },
        "Vector Art": {
            "positive": "vector art, clean lines, flat colors, geometric shapes, modern illustration, scalable graphics",
            "negative": "raster, pixelated, textured, painterly, photographic"
        },
        
        # Fantasy/Sci-Fi Styles
        "Fantasy Art": {
            "positive": "fantasy art, magical atmosphere, ethereal lighting, detailed environment, epic composition, concept art, matte painting",
            "negative": "modern, contemporary, realistic photo, plain, mundane, boring"
        },
        "Dark Fantasy": {
            "positive": "dark fantasy, gothic atmosphere, moody lighting, dramatic, ominous, detailed armor and weapons, epic scale",
            "negative": "bright, cheerful, colorful, modern, minimalist, simple"
        },
        "Sci-Fi": {
            "positive": "sci-fi, futuristic, neon lighting, cyberpunk, advanced technology, sleek design, holographic elements",
            "negative": "medieval, fantasy, low-tech, primitive, rustic, old-fashioned"
        },
        "Cyberpunk": {
            "positive": "cyberpunk aesthetic, neon lights, dark urban setting, high tech low life, rain-slicked streets, dystopian future",
            "negative": "bright, natural, rural, low-tech, minimalist, clean"
        },
        "Steampunk": {
            "positive": "steampunk, Victorian era, brass and copper, gears and cogs, industrial, retro-futuristic, detailed machinery",
            "negative": "modern, minimalist, digital, clean, sleek, contemporary"
        },
        "Post-Apocalyptic": {
            "positive": "post-apocalyptic, wasteland, ruined buildings, survival aesthetic, worn and weathered, desolate atmosphere",
            "negative": "pristine, new, clean, colorful, happy, prosperous"
        },
        
        # Aesthetic Styles
        "Vaporwave": {
            "positive": "vaporwave aesthetic, neon colors, retro futurism, glitch art, 80s style, cyberpunk, grid patterns",
            "negative": "realistic, natural colors, modern, minimalist, plain"
        },
        "Pastel Goth": {
            "positive": "pastel goth, soft pastel colors, dark themes, cute but creepy, alternative fashion, dreamy atmosphere",
            "negative": "realistic, harsh colors, bright, conventional, plain"
        },
        "Kawaii": {
            "positive": "kawaii aesthetic, cute, pastel colors, soft and fluffy, adorable, Japanese cute culture, cheerful",
            "negative": "dark, realistic, serious, mature, gritty, horror"
        },
        "Minimalist": {
            "positive": "minimalist, clean composition, simple shapes, negative space, elegant, refined, uncluttered",
            "negative": "busy, cluttered, detailed, ornate, complex, maximalist"
        },
        "Maximalist": {
            "positive": "maximalist, ornate details, rich textures, complex composition, abundant decoration, opulent, layered",
            "negative": "minimalist, simple, plain, sparse, basic, unadorned"
        },
        
        # Cinematic Styles
        "Film Noir": {
            "positive": "film noir, black and white, high contrast, dramatic lighting, venetian blind shadows, mystery, detective style",
            "negative": "colorful, bright, cheerful, modern, digital, soft lighting"
        },
        "Horror": {
            "positive": "horror atmosphere, dark and moody, eerie lighting, unsettling, dramatic shadows, tense mood, mysterious",
            "negative": "cheerful, bright, colorful, happy, safe, comfortable, welcoming"
        },
        "Western": {
            "positive": "western style, dusty atmosphere, golden hour lighting, frontier aesthetic, rugged, classic western film",
            "negative": "modern, futuristic, urban, clean, polished, digital"
        },
        
        # Vintage Styles
        "Vintage": {
            "positive": "vintage style, retro, faded colors, film grain, nostalgic, aged photo, classic, timeless",
            "negative": "modern, contemporary, digital, sharp, vibrant, new, glossy"
        },
        "1950s": {
            "positive": "1950s aesthetic, vintage Americana, retro fashion, pastel colors, classic cars, rockabilly style",
            "negative": "modern, contemporary, digital, futuristic, minimalist"
        },
        "1980s": {
            "positive": "1980s aesthetic, neon colors, retro technology, synthwave, vintage electronics, bold geometric patterns",
            "negative": "modern, minimalist, muted colors, contemporary, clean"
        },
        "Victorian": {
            "positive": "Victorian era, ornate details, historical fashion, classical architecture, elegant, period accurate, vintage",
            "negative": "modern, contemporary, minimalist, futuristic, casual"
        },
        
        # Special Effects
        "Glitch Art": {
            "positive": "glitch art, digital distortion, corrupted data aesthetic, chromatic aberration, scanline effects, cyberpunk",
            "negative": "clean, perfect, smooth, realistic, traditional, flawless"
        },
        "Neon": {
            "positive": "neon lighting, glowing elements, vibrant colors, electric aesthetic, night scene, luminous, bright",
            "negative": "natural lighting, muted colors, daytime, subdued, dim"
        },
        "Holographic": {
            "positive": "holographic effect, iridescent, rainbow colors, futuristic, shimmering, metallic sheen, sci-fi",
            "negative": "matte, flat colors, dull, natural, traditional"
        },
    }
    
    # Quality tiers
    QUALITY_TIERS = {
        "None": "",
        "Draft": "good quality",
        "Standard": "high quality, detailed",
        "High": "highly detailed, professional quality, masterpiece",
        "Ultimate": "masterpiece, best quality, ultra detailed, 8k uhd, professional, award winning, trending on artstation"
    }
    
    # Common negative prompt base
    NEGATIVE_BASE = "blurry, low quality, worst quality, low resolution, bad anatomy, bad proportions, distorted, disfigured"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_prompt": ("STRING", {
                    "default": "a beautiful landscape",
                    "multiline": True,
                    "tooltip": "Your main subject/scene description"
                }),
                "style": (list(cls.STYLE_TEMPLATES.keys()),),
                "quality_tier": (list(cls.QUALITY_TIERS.keys()),),
                "use_negative_suggestions": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Auto-add style-appropriate negative prompts"
                }),
            },
            "optional": {
                "custom_positive": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Additional positive prompt additions"
                }),
                "custom_negative": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Additional negative prompt additions"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt")
    FUNCTION = "apply_style"
    CATEGORY = "Arctenox Essentials/Prompting"
    
    def apply_style(self, base_prompt, style, quality_tier, use_negative_suggestions, 
                   custom_positive="", custom_negative=""):
        """
        Apply selected style and quality to base prompt.
        
        Args:
            base_prompt: Main subject/scene description
            style: Selected style template
            quality_tier: Quality level (draft/standard/high/ultimate)
            use_negative_suggestions: Whether to add style-appropriate negatives
            custom_positive: Additional positive additions
            custom_negative: Additional negative additions
        
        Returns:
            tuple: (styled_positive_prompt, styled_negative_prompt)
        """
        # Start with base prompt
        positive_parts = [base_prompt.strip()]
        
        # Add quality tier
        if quality_tier != "None":
            quality_text = self.QUALITY_TIERS[quality_tier]
            if quality_text:
                positive_parts.append(quality_text)
        
        # Add style template
        if style != "None":
            style_data = self.STYLE_TEMPLATES[style]
            if style_data["positive"]:
                positive_parts.append(style_data["positive"])
        
        # Add custom positive
        if custom_positive.strip():
            positive_parts.append(custom_positive.strip())
        
        # Build positive prompt
        positive_prompt = ", ".join(positive_parts)
        
        # Build negative prompt
        negative_parts = [self.NEGATIVE_BASE]
        
        # Add style-specific negatives
        if use_negative_suggestions and style != "None":
            style_data = self.STYLE_TEMPLATES[style]
            if style_data["negative"]:
                negative_parts.append(style_data["negative"])
        
        # Add custom negative
        if custom_negative.strip():
            negative_parts.append(custom_negative.strip())
        
        negative_prompt = ", ".join(negative_parts)
        
        return (positive_prompt, negative_prompt)


class PromptStylerAdvanced(PromptStyler):
    """
    Advanced prompt styler with multiple style mixing and emphasis control.
    
    Allows combining multiple styles and controlling their influence.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_prompt": ("STRING", {
                    "default": "a beautiful landscape",
                    "multiline": True,
                    "tooltip": "Your main subject/scene description"
                }),
                "primary_style": (list(cls.STYLE_TEMPLATES.keys()),),
                "secondary_style": (list(cls.STYLE_TEMPLATES.keys()),),
                "style_mix_ratio": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1,
                    "tooltip": "0.0 = all secondary, 1.0 = all primary"
                }),
                "quality_tier": (list(cls.QUALITY_TIERS.keys()),),
                "use_negative_suggestions": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "custom_positive": ("STRING", {
                    "default": "",
                    "multiline": True
                }),
                "custom_negative": ("STRING", {
                    "default": "",
                    "multiline": True
                }),
                "emphasis_words": ("STRING", {
                    "default": "",
                    "tooltip": "Comma-separated words to emphasize with (word:1.2) syntax"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt", "style_info")
    FUNCTION = "apply_advanced_style"
    CATEGORY = "Arctenox Essentials/Prompting"
    
    def apply_advanced_style(self, base_prompt, primary_style, secondary_style, 
                           style_mix_ratio, quality_tier, use_negative_suggestions,
                           custom_positive="", custom_negative="", emphasis_words=""):
        """
        Apply mixed styles with emphasis control.
        """
        # Start with base prompt
        positive_parts = [base_prompt.strip()]
        
        # Add quality tier
        if quality_tier != "None":
            quality_text = self.QUALITY_TIERS[quality_tier]
            if quality_text:
                positive_parts.append(quality_text)
        
        # Mix primary and secondary styles based on ratio
        style_parts = []
        
        if primary_style != "None" and style_mix_ratio > 0.3:
            primary_data = self.STYLE_TEMPLATES[primary_style]
            if primary_data["positive"]:
                style_parts.append(primary_data["positive"])
        
        if secondary_style != "None" and secondary_style != primary_style and style_mix_ratio < 0.7:
            secondary_data = self.STYLE_TEMPLATES[secondary_style]
            if secondary_data["positive"]:
                style_parts.append(secondary_data["positive"])
        
        if style_parts:
            positive_parts.append(", ".join(style_parts))
        
        # Add custom positive
        if custom_positive.strip():
            positive_parts.append(custom_positive.strip())
        
        # Build positive prompt
        positive_prompt = ", ".join(positive_parts)
        
        # Apply emphasis to specific words
        if emphasis_words.strip():
            words = [w.strip() for w in emphasis_words.split(",")]
            for word in words:
                if word and word in positive_prompt:
                    positive_prompt = positive_prompt.replace(word, f"({word}:1.2)")
        
        # Build negative prompt (combine negatives from both styles)
        negative_parts = [self.NEGATIVE_BASE]
        
        if use_negative_suggestions:
            if primary_style != "None":
                primary_data = self.STYLE_TEMPLATES[primary_style]
                if primary_data["negative"]:
                    negative_parts.append(primary_data["negative"])
            
            if secondary_style != "None" and secondary_style != primary_style:
                secondary_data = self.STYLE_TEMPLATES[secondary_style]
                if secondary_data["negative"]:
                    negative_parts.append(secondary_data["negative"])
        
        if custom_negative.strip():
            negative_parts.append(custom_negative.strip())
        
        negative_prompt = ", ".join(negative_parts)
        
        # Create style info for reference
        style_info = f"Primary: {primary_style} ({style_mix_ratio*100:.0f}%)"
        if secondary_style != "None" and secondary_style != primary_style:
            style_info += f" + Secondary: {secondary_style} ({(1-style_mix_ratio)*100:.0f}%)"
        
        return (positive_prompt, negative_prompt, style_info)


# Node registration
NODE_CLASS_MAPPINGS = {
    "PromptStyler": PromptStyler,
    "PromptStylerAdvanced": PromptStylerAdvanced,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptStyler": "Prompt Styler (Arctenox's Essentials)",
    "PromptStylerAdvanced": "Prompt Styler [Advanced] (Arctenox's Essentials)",
}