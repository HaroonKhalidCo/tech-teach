"""
PPT Video Tool - Generate professional videos with synced audio.

WORKFLOW:
1. TEXT MODEL → Generates script with per-slide narration
2. IMAGE MODEL → Generates slide images based on content
3. AUDIO MODEL → Generates voice for EACH slide separately
4. LIBRARY → Combines images + synced audio into professional video
"""

import os
import uuid
import asyncio
import wave
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import json
import io
import subprocess

from PIL import Image, ImageDraw, ImageFont
import imageio
import numpy as np

from app.tools.base_tool import BaseTool
from app.core.config import settings


class PPTVideoTool(BaseTool):
    """Generate professional educational videos with synced audio."""
    
    NUM_SLIDES = 6
    FPS = 24
    MIN_SLIDE_DURATION = 8  # Minimum seconds per slide
    
    async def execute(
        self, 
        instructions: str, 
        source_content: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a professional video with synced audio."""
        print(f"\n{'='*60}")
        print(f"[PPTVideoTool] Starting Professional Video Generation")
        print(f"[PPTVideoTool] Topic: {instructions[:60]}...")
        print(f"{'='*60}\n")
        
        try:
            progress_cb = kwargs.get('progress_callback')
            
            # STEP 1: Generate detailed script with per-slide narration
            print("[PPTVideoTool] STEP 1/4: Generating detailed script...")
            if progress_cb:
                progress_cb(10, "script", "Writing video script...")
            script = await self._generate_detailed_script(instructions, source_content)
            print(f"[PPTVideoTool] ✓ Script: {len(script['slides'])} slides created")
            
            # STEP 2: Generate images for each slide
            print("\n[PPTVideoTool] STEP 2/4: Generating slide images...")
            if progress_cb:
                progress_cb(20, "images", "Creating slide images...")
            images = await self._generate_slide_images(script["slides"], instructions, progress_cb)
            print(f"[PPTVideoTool] ✓ Images: {len(images)} slides generated")
            
            # STEP 3: Generate audio for EACH slide separately
            print("\n[PPTVideoTool] STEP 3/4: Generating audio for each slide...")
            if progress_cb:
                progress_cb(50, "audio", "Recording narration...")
            audio_clips = await self._generate_slide_audio(script["slides"], progress_cb)
            print(f"[PPTVideoTool] ✓ Audio: {len(audio_clips)} clips generated")
            
            # STEP 4: Create synced video and save to file
            print("\n[PPTVideoTool] STEP 4/4: Creating synced video...")
            progress_cb = kwargs.get('progress_callback')
            if progress_cb:
                progress_cb(80, "video", "Creating final video...")
            
            video_path, total_duration = self._create_synced_video(images, audio_clips)
            print(f"[PPTVideoTool] ✓ Video saved: {os.path.basename(video_path)} ({total_duration}s)")
            
            if progress_cb:
                progress_cb(100, "complete", "Video ready!")
            
            print(f"\n{'='*60}")
            print(f"[PPTVideoTool] Professional Video Complete!")
            print(f"{'='*60}\n")
            
            return {
                "status": "success",
                "tool": "ppt_video",
                "file_path": video_path,
                "file_name": os.path.basename(video_path),
                "total_slides": len(script["slides"]),
                "duration_seconds": total_duration,
                "message": f"Professional video: {len(script['slides'])} slides, {total_duration}s with synced audio"
            }
            
        except Exception as e:
            import traceback
            print(f"\n[PPTVideoTool] ❌ ERROR: {e}")
            traceback.print_exc()
            return {
                "status": "error",
                "tool": "ppt_video",
                "message": f"Video generation failed: {str(e)}"
            }
    
    async def _generate_detailed_script(self, instructions: str, source: Optional[str]) -> Dict:
        """Generate script with separate narration for each slide."""
        prompt = f"""Create a professional {self.NUM_SLIDES}-slide video script.

TOPIC: {instructions}
{f'REFERENCE: {source[:1500]}' if source else ''}

Return ONLY this JSON format:
{{
    "title": "Video Title",
    "slides": [
        {{
            "number": 1,
            "title": "Introduction",
            "points": "Key bullet points",
            "visual": "Description of what the slide image should show",
            "narration": "The exact words to speak for THIS slide only. Write 2-3 complete sentences that will be spoken while this slide is shown. Be natural and engaging."
        }},
        {{
            "number": 2,
            "title": "Main Concept",
            "points": "Key points",
            "visual": "Visual description",
            "narration": "Narration for slide 2 only..."
        }}
    ]
}}

IMPORTANT:
- Each slide MUST have its own "narration" field
- Each narration should be 2-3 sentences (about 8-12 seconds when spoken)
- Make narrations flow naturally from one slide to the next
- First slide: Welcome and introduce topic
- Middle slides: Explain key concepts
- Last slide: Summarize and thank viewers

Create exactly {self.NUM_SLIDES} slides."""

        text = await self.generate_text(prompt)
        
        try:
            clean = text.strip()
            if '```' in clean:
                clean = clean.split('```')[1]
                if clean.startswith('json'):
                    clean = clean[4:]
                clean = clean.split('```')[0] if '```' in clean else clean
            return json.loads(clean.strip())
        except Exception as e:
            print(f"[PPTVideoTool] JSON parse error: {e}")
            # Generate default script with per-slide narration
            return self._generate_default_script(instructions)
    
    def _generate_default_script(self, topic: str) -> Dict:
        """Generate default script if parsing fails."""
        narrations = [
            f"Welcome to our educational video about {topic}. Today we'll explore this fascinating topic together.",
            f"Let's start by understanding the basics of {topic}. This foundation is essential for deeper learning.",
            f"Now let's dive into the key concepts. These are the core ideas you need to understand.",
            f"Here are some practical examples that illustrate {topic} in action.",
            f"Let's review the important points we've covered about {topic}.",
            f"Thank you for watching! Remember to practice what you've learned about {topic}."
        ]
        
        return {
            "title": topic[:50],
            "slides": [
                {
                    "number": i + 1,
                    "title": ["Introduction", "Basics", "Key Concepts", "Examples", "Summary", "Conclusion"][i],
                    "points": "Key content points",
                    "visual": "Educational visual",
                    "narration": narrations[i]
                }
                for i in range(self.NUM_SLIDES)
            ]
        }
    
    async def _generate_slide_images(self, slides: List[Dict], topic: str, progress_cb: Optional[Callable] = None) -> List[bytes]:
        """Generate professional images for each slide."""
        
        async def generate_slide(slide: Dict, idx: int) -> bytes:
            if progress_cb:
                progress_cb(20 + (idx * 5), "images", f"Creating image {idx+1}/{len(slides)}...")
            prompt = f"""Create a professional educational video slide image.

TOPIC: {topic}
SLIDE {idx + 1} of {self.NUM_SLIDES}

SLIDE TITLE: {slide.get('title', f'Slide {idx+1}')}
KEY POINTS: {slide.get('points', '')}

DESIGN REQUIREMENTS:
- Modern, professional presentation slide
- Clean layout with clear hierarchy
- Title prominently displayed at top
- Colorful but professional color scheme
- Topic-relevant illustrations and graphics
- 16:9 widescreen format
- Easy to read from a distance

VISUAL DESCRIPTION: {slide.get('visual', 'Educational diagram or illustration')}

Create a high-quality slide that looks like a professional video presentation."""

            try:
                return await self.generate_image(prompt)
            except Exception as e:
                print(f"[PPTVideoTool] Slide {idx+1} image error: {e}")
                return self._create_text_slide(slide, idx)
        
        tasks = [generate_slide(s, i) for i, s in enumerate(slides)]
        return await asyncio.gather(*tasks)
    
    def _create_text_slide(self, slide: Dict, index: int) -> bytes:
        """Create a text-based slide as fallback."""
        colors = [
            (30, 60, 114),   # Dark blue
            (20, 80, 100),   # Teal
            (70, 35, 100),   # Purple
            (100, 50, 30),   # Brown
            (40, 70, 90),    # Slate
            (60, 30, 80),    # Dark purple
        ]
        
        img = Image.new('RGB', (1920, 1080), colors[index % len(colors)])
        draw = ImageDraw.Draw(img)
        
        # Add title
        title = slide.get('title', f'Slide {index + 1}')
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        except:
            font = ImageFont.load_default()
        
        # Center title
        bbox = draw.textbbox((0, 0), title, font=font)
        x = (1920 - bbox[2]) // 2
        draw.text((x, 200), title, fill=(255, 255, 255), font=font)
        
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()
    
    async def _generate_slide_audio(self, slides: List[Dict], progress_cb: Optional[Callable] = None) -> List[Optional[str]]:
        """Generate audio for each slide separately."""
        audio_paths = []
        
        for i, slide in enumerate(slides):
            if progress_cb:
                progress_cb(50 + (i * 5), "audio", f"Recording voice {i+1}/{len(slides)}...")
            
            narration = slide.get('narration', '')
            if not narration or len(narration.strip()) < 10:
                print(f"[PPTVideoTool] Slide {i+1}: No narration, using default")
                narration = f"This is slide {i+1} about {slide.get('title', 'our topic')}."
            
            try:
                audio_path = os.path.join(settings.TEMP_DIR, f"slide_{i+1}_{uuid.uuid4().hex[:6]}.wav")
                await self.generate_audio(narration, audio_path)
                
                if os.path.exists(audio_path) and os.path.getsize(audio_path) > 100:
                    audio_paths.append(audio_path)
                    print(f"[PPTVideoTool] Slide {i+1}: Audio generated ({self._get_audio_duration(audio_path):.1f}s)")
                else:
                    audio_paths.append(None)
                    print(f"[PPTVideoTool] Slide {i+1}: Audio failed")
                    
            except Exception as e:
                print(f"[PPTVideoTool] Slide {i+1} audio error: {e}")
                audio_paths.append(None)
        
        return audio_paths
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds."""
        try:
            with wave.open(audio_path, 'rb') as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                return frames / rate
        except:
            return self.MIN_SLIDE_DURATION
    
    def _create_synced_video(self, images: List[bytes], audio_clips: List[Optional[str]]) -> tuple:
        """Create video with each slide synced to its audio, save to file."""
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        uid = uuid.uuid4().hex[:8]
        video_path = os.path.join(settings.OUTPUT_DIR, f"video_{ts}_{uid}.mp4")
        temp_video = video_path.replace('.mp4', '_temp.mp4')
        
        # Calculate duration for each slide based on its audio
        slide_durations = []
        for i, audio_path in enumerate(audio_clips):
            if audio_path and os.path.exists(audio_path):
                duration = max(self._get_audio_duration(audio_path), self.MIN_SLIDE_DURATION)
            else:
                duration = self.MIN_SLIDE_DURATION
            slide_durations.append(duration)
            print(f"[PPTVideoTool] Slide {i+1} duration: {duration:.1f}s")
        
        total_duration = sum(slide_durations)
        print(f"[PPTVideoTool] Total video duration: {total_duration:.1f}s")
        
        # Build video frames
        all_frames = []
        for i, (img_bytes, duration) in enumerate(zip(images, slide_durations)):
            img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
            img = img.resize((1920, 1080), Image.Resampling.LANCZOS)
            frame = np.array(img)
            
            # Calculate frames for this slide
            num_frames = int(duration * self.FPS)
            all_frames.extend([frame] * num_frames)
        
        # Write video without audio first
        print(f"[PPTVideoTool] Writing {len(all_frames)} frames...")
        
        writer = imageio.get_writer(
            temp_video,
            fps=self.FPS,
            codec='libx264',
            quality=8,
            macro_block_size=1
        )
        
        for frame in all_frames:
            writer.append_data(frame)
        writer.close()
        
        # Combine all audio clips into one
        combined_audio = self._combine_audio_clips(audio_clips, slide_durations)
        
        # Merge audio with video
        if combined_audio and os.path.exists(combined_audio):
            self._merge_audio_video(temp_video, combined_audio, video_path)
            # Cleanup temp files
            if os.path.exists(temp_video):
                os.remove(temp_video)
            if os.path.exists(combined_audio):
                os.remove(combined_audio)
        else:
            os.rename(temp_video, video_path)
        
        # Cleanup individual audio clips
        for audio_path in audio_clips:
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except:
                    pass
        
        return video_path, int(total_duration)
    
    def _combine_audio_clips(self, audio_clips: List[Optional[str]], durations: List[float]) -> Optional[str]:
        """Combine all audio clips with proper timing."""
        combined_path = os.path.join(settings.TEMP_DIR, f"combined_{uuid.uuid4().hex[:6]}.wav")
        
        # Collect valid audio data
        sample_rate = 24000
        all_audio_data = []
        
        for i, (audio_path, target_duration) in enumerate(zip(audio_clips, durations)):
            if audio_path and os.path.exists(audio_path):
                try:
                    with wave.open(audio_path, 'rb') as wav:
                        sample_rate = wav.getframerate()
                        audio_data = wav.readframes(wav.getnframes())
                        
                        # Calculate padding needed
                        audio_duration = len(audio_data) / (sample_rate * 2)  # 16-bit = 2 bytes
                        if audio_duration < target_duration:
                            # Add silence padding
                            padding_samples = int((target_duration - audio_duration) * sample_rate)
                            padding = b'\x00\x00' * padding_samples  # 16-bit silence
                            audio_data = audio_data + padding
                        
                        all_audio_data.append(audio_data)
                except Exception as e:
                    print(f"[PPTVideoTool] Error reading audio {i+1}: {e}")
                    # Add silence for this slide
                    silence_samples = int(target_duration * sample_rate)
                    all_audio_data.append(b'\x00\x00' * silence_samples)
            else:
                # Add silence for slides without audio
                silence_samples = int(target_duration * sample_rate)
                all_audio_data.append(b'\x00\x00' * silence_samples)
        
        if not all_audio_data:
            return None
        
        # Write combined audio
        try:
            with wave.open(combined_path, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                for data in all_audio_data:
                    wav.writeframes(data)
            
            print(f"[PPTVideoTool] Combined audio: {combined_path}")
            return combined_path
        except Exception as e:
            print(f"[PPTVideoTool] Error combining audio: {e}")
            return None
    
    def _merge_audio_video(self, video_path: str, audio_path: str, output_path: str):
        """Merge audio and video using ffmpeg."""
        try:
            result = subprocess.run([
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-shortest',
                output_path
            ], capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0:
                print("[PPTVideoTool] ✓ Audio synced with video")
            else:
                print(f"[PPTVideoTool] FFmpeg warning: {result.stderr[:200]}")
                # Still try to use output if it exists
                if not os.path.exists(output_path):
                    os.rename(video_path, output_path)
                    
        except Exception as e:
            print(f"[PPTVideoTool] Merge error: {e}")
            os.rename(video_path, output_path)
