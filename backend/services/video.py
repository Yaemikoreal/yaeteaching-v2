"""Video generation service: combine lesson + TTS + PPT into teaching video."""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from config.settings import settings


class VideoGenerator:
    """Generate teaching video from lesson plan + TTS audio + PPT slides."""

    def __init__(self):
        self.storage_path = Path(settings.storage_path) / "videos"
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        lesson_json: dict,
        audio_files: list[str],
        ppt_file: str,
        output_format: str = "mp4"
    ) -> str:
        """
        Generate teaching video from lesson, audio and PPT.

        Args:
            lesson_json: Lesson plan JSON with outline structure
            audio_files: List of audio file paths (one per section)
            ppt_file: PPT file path
            output_format: Output video format (default mp4)

        Returns:
            Path to generated video file
        """
        job_id = lesson_json.get("meta", {}).get("job_id", "unknown")
        output_path = self.storage_path / f"{job_id}.{output_format}"

        # Create temporary directory for intermediate files
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Step 1: Convert PPT slides to images
            slide_images = self._convert_ppt_to_images(ppt_file, tmp_dir)

            # Step 2: Get audio durations for timing
            durations = self._get_audio_durations(audio_files)

            # Step 3: Create video segments (slide + audio)
            segments = self._create_segments(slide_images, audio_files, durations, tmp_dir)

            # Step 4: Concatenate segments into final video
            self._concatenate_segments(segments, output_path)

        return str(output_path)

    def _convert_ppt_to_images(self, ppt_file: str, output_dir: str) -> list[str]:
        """
        Convert PPT slides to PNG images using LibreOffice or pdf2image.

        Args:
            ppt_file: Path to PPT file
            output_dir: Directory for output images

        Returns:
            List of image file paths
        """
        # Try LibreOffice first (more reliable for PPT)
        try:
            result = subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", output_dir,
                    ppt_file
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                pdf_path = Path(output_dir) / Path(ppt_file).with_suffix(".pdf").name
                # Convert PDF pages to images using pdftoppm or pdf2image
                images = self._convert_pdf_to_images(str(pdf_path), output_dir)
                return images
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback: use python-pptx export (limited quality)
        return self._export_ppt_images_python(ppt_file, output_dir)

    def _convert_pdf_to_images(self, pdf_file: str, output_dir: str) -> list[str]:
        """Convert PDF pages to PNG images."""
        try:
            result = subprocess.run(
                [
                    "pdftoppm",
                    "-png",
                    "-r", "150",  # Resolution
                    pdf_file,
                    Path(output_dir) / "slide"
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                # Collect generated images
                images = sorted(Path(output_dir).glob("slide-*.png"))
                return [str(img) for img in images]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback: try pdf2image Python library
        try:
            from pdf2image import convert_from_path
            pages = convert_from_path(pdf_file, dpi=150)
            images = []
            for i, page in enumerate(pages):
                img_path = Path(output_dir) / f"slide-{i+1}.png"
                page.save(str(img_path), "PNG")
                images.append(str(img_path))
            return images
        except ImportError:
            raise RuntimeError("No PDF to image converter available. Install pdftoppm or pdf2image.")

    def _export_ppt_images_python(self, ppt_file: str, output_dir: str) -> list[str]:
        """Export PPT slides as images using python-pptx (limited quality)."""
        from pptx import Presentation
        from pptx.util import Inches

        prs = Presentation(ppt_file)
        images = []

        # This is a placeholder - python-pptx doesn't support direct image export
        # In production, use LibreOffice or a dedicated PPT conversion service
        for i, slide in enumerate(prs.slides):
            # Create placeholder image with slide dimensions
            img_path = Path(output_dir) / f"slide-{i+1}.png"
            # Note: actual implementation would render slide to image
            # For now, create empty placeholder
            images.append(str(img_path))

        return images

    def _get_audio_durations(self, audio_files: list[str]) -> list[float]:
        """Get duration of each audio file in seconds."""
        durations = []
        for audio_file in audio_files:
            try:
                result = subprocess.run(
                    [
                        "ffprobe",
                        "-v", "error",
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        audio_file
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    durations.append(float(result.stdout.strip()))
                else:
                    durations.append(30.0)  # Default duration
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                durations.append(30.0)  # Default duration
        return durations

    def _create_segments(
        self,
        slide_images: list[str],
        audio_files: list[str],
        durations: list[float],
        output_dir: str
    ) -> list[str]:
        """Create video segments combining slides with audio."""
        segments = []

        # Match slides to audio sections
        # Intro slide + intro audio, main slides + main audio, conclusion slide + conclusion audio
        num_sections = len(audio_files)

        for i, (audio_file, duration) in enumerate(zip(audio_files, durations)):
            # Get corresponding slide (cycle through slides if more audio than slides)
            slide_idx = min(i, len(slide_images) - 1)
            slide_image = slide_images[slide_idx] if slide_images else None

            segment_path = Path(output_dir) / f"segment-{i}.mp4"

            if slide_image and os.path.exists(slide_image):
                # Create video segment from image + audio
                try:
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",  # Overwrite output
                            "-loop", "1",  # Loop image
                            "-i", slide_image,
                            "-i", audio_file,
                            "-c:v", "libx264",
                            "-tune", "stillimage",
                            "-c:a", "aac",
                            "-b:a", "192k",
                            "-pix_fmt", "yuv420p",
                            "-shortest",  # End when audio ends
                            "-t", str(duration),
                            str(segment_path)
                        ],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    if segment_path.exists():
                        segments.append(str(segment_path))
                except subprocess.TimeoutExpired:
                    # Fallback: create silent video from image
                    pass
            else:
                # Create video from audio only (with blank background)
                try:
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-f", "lavfi",
                            "-i", "color=c=white:s=1920x1080:d={}".format(duration),
                            "-i", audio_file,
                            "-c:v", "libx264",
                            "-c:a", "aac",
                            "-shortest",
                            str(segment_path)
                        ],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if segment_path.exists():
                        segments.append(str(segment_path))
                except subprocess.TimeoutExpired:
                    pass

        return segments

    def _concatenate_segments(self, segments: list[str], output_path: Path) -> bool:
        """Concatenate video segments into final video."""
        if not segments:
            raise RuntimeError("No video segments to concatenate")

        # Create concat file for ffmpeg
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            for segment in segments:
                f.write(f"file '{segment}'\n")
            concat_file = f.name

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concat_file,
                    "-c:v", "libx264",
                    "-c:a", "aac",
                    "-movflags", "+faststart",  # Web streaming optimization
                    str(output_path)
                ],
                capture_output=True,
                text=True,
                timeout=300
            )
            return output_path.exists()
        except subprocess.TimeoutExpired:
            raise RuntimeError("Video concatenation timed out")
        finally:
            os.unlink(concat_file)

    def get_video_metadata(self, video_file: str) -> dict:
        """Get video metadata (duration, resolution, codec)."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=width,height,codec_name,duration",
                    "-of", "json",
                    video_file
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                if data.get("streams"):
                    stream = data["streams"][0]
                    return {
                        "width": stream.get("width"),
                        "height": stream.get("height"),
                        "codec": stream.get("codec_name"),
                        "duration": float(stream.get("duration", 0))
                    }
        except Exception:
            pass
        return {}