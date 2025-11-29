"""Base class for all tools using Gemini models."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
import wave
import struct

from google import genai
from google.genai import types as genai_types

from app.core.config import settings


class BaseTool(ABC):
    """
    Base class using Gemini models:
    - Text: gemini-2.0-flash-exp
    - Image: gemini-2.5-flash-image
    - Audio: gemini-2.5-flash-preview-tts
    """
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.text_model = "gemini-2.0-flash-exp"
        self.image_model = "gemini-2.5-flash-image"
        self.audio_model = "gemini-2.5-pro-preview-tts"
    
    @abstractmethod
    async def execute(
        self, 
        instructions: str, 
        source_content: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute the tool."""
        pass
    
    async def generate_text(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate text using Gemini 2.0 Flash."""
        print(f"[{self.__class__.__name__}] Generating text with {self.text_model}...")
        try:
            response = await self.client.aio.models.generate_content(
                model=self.text_model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=8192,
                )
            )
            return response.text
        except Exception as e:
            print(f"[{self.__class__.__name__}] Text error: {e}")
            raise
    
    async def generate_image(self, prompt: str) -> bytes:
        """Generate image using Gemini 2.5 Flash Image model."""
        print(f"[{self.__class__.__name__}] Generating image with {self.image_model}...")
        try:
            response = await self.client.aio.models.generate_content(
                model=self.image_model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                )
            )
            
            # Extract image from response
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        mime = part.inline_data.mime_type
                        if mime and mime.startswith('image/'):
                            print(f"[{self.__class__.__name__}] Image generated successfully")
                            return part.inline_data.data
            
            raise Exception("No image in response")
            
        except Exception as e:
            print(f"[{self.__class__.__name__}] Image error: {e}")
            raise
    
    async def generate_audio(self, text: str, output_path: str) -> str:
        """Generate audio using Gemini TTS model and save as proper WAV."""
        print(f"[{self.__class__.__name__}] Generating audio with {self.audio_model}...")
        try:
            response = await self.client.aio.models.generate_content(
                model=self.audio_model,
                contents=text,
                config=genai_types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=genai_types.SpeechConfig(
                        voice_config=genai_types.VoiceConfig(
                            prebuilt_voice_config=genai_types.PrebuiltVoiceConfig(
                                voice_name="Kore"
                            )
                        )
                    )
                )
            )
            
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        mime_type = part.inline_data.mime_type
                        audio_data = part.inline_data.data
                        
                        if "audio" in mime_type:
                            # Parse sample rate from mime type (audio/L16;codec=pcm;rate=24000)
                            sample_rate = 24000  # default
                            if "rate=" in mime_type:
                                try:
                                    rate_str = mime_type.split("rate=")[1].split(";")[0]
                                    sample_rate = int(rate_str)
                                except:
                                    pass
                            
                            # Convert raw PCM to proper WAV file
                            self._save_pcm_as_wav(audio_data, output_path, sample_rate)
                            
                            print(f"[{self.__class__.__name__}] Audio saved: {output_path} ({len(audio_data)} bytes, {sample_rate}Hz)")
                            return output_path
            
            raise Exception("No audio generated")
            
        except Exception as e:
            print(f"[{self.__class__.__name__}] Audio error: {e}")
            raise
    
    def _save_pcm_as_wav(self, pcm_data: bytes, output_path: str, sample_rate: int = 24000):
        """Convert raw PCM data to proper WAV file with headers."""
        # PCM is 16-bit signed, mono
        channels = 1
        sample_width = 2  # 16-bit = 2 bytes
        
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)
