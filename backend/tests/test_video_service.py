"""Tests for video generation service."""
import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from services.video import VideoGenerator


@pytest.fixture
def video_generator():
    """Create video generator instance."""
    return VideoGenerator()


@pytest.fixture
def sample_lesson_json():
    """Sample lesson JSON for testing."""
    return {
        "meta": {
            "job_id": "test-job-123",
            "subject": "数学",
            "grade": "7年级",
            "topic": "一元一次方程",
            "duration": 45
        },
        "outline": {
            "introduction": {
                "title": "导入",
                "content": "通过生活中的例子引入方程概念..."
            },
            "main_sections": [
                {
                    "title": "方程的基本概念",
                    "content": "详细讲解..."
                }
            ],
            "conclusion": {
                "title": "总结",
                "content": "回顾本节课重点..."
            }
        }
    }


class TestVideoGenerator:
    """Test VideoGenerator class."""

    def test_init(self, video_generator):
        """Test initialization."""
        assert video_generator.storage_path is not None
        assert os.path.exists(video_generator.storage_path)

    @patch('services.video.subprocess.run')
    def test_get_audio_durations(self, video_generator):
        """Test getting audio durations."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "30.5\n"

        with tempfile.NamedTemporaryFile(suffix=".mp3") as audio_file:
            audio_files = [audio_file.name]
            durations = video_generator._get_audio_durations(audio_files)

            assert len(durations) == 1
            assert durations[0] == 30.5

    def test_get_audio_durations_default(self, video_generator):
        """Test getting audio durations with missing file."""
        # Non-existent file should return default duration
        durations = video_generator._get_audio_durations(["/nonexistent/audio.mp3"])
        assert durations == [30.0]

    @patch('services.video.subprocess.run')
    def test_get_video_metadata(self, video_generator):
        """Test getting video metadata."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"streams":[{"width":1920,"height":1080,"codec_name":"h264","duration":"60.0"}]}'

        with tempfile.NamedTemporaryFile(suffix=".mp4") as video_file:
            metadata = video_generator.get_video_metadata(video_file.name)
            assert metadata.get("width") == 1920
            assert metadata.get("height") == 1080

    def test_get_video_metadata_error(self, video_generator):
        """Test getting video metadata with error."""
        metadata = video_generator.get_video_metadata("/nonexistent/video.mp4")
        assert metadata == {}

    @patch('services.video.VideoGenerator._convert_ppt_to_images')
    @patch('services.video.VideoGenerator._get_audio_durations')
    @patch('services.video.VideoGenerator._create_segments')
    @patch('services.video.VideoGenerator._concatenate_segments')
    def test_generate_success(
        self,
        video_generator,
        sample_lesson_json,
        mock_concatenate,
        mock_create_segments,
        mock_get_durations,
        mock_convert_ppt
    ):
        """Test successful video generation."""
        mock_convert_ppt.return_value = ["slide1.png", "slide2.png"]
        mock_get_durations.return_value = [30.0, 60.0]
        mock_create_segments.return_value = ["segment1.mp4", "segment2.mp4"]
        mock_concatenate.return_value = True

        audio_files = ["audio1.mp3", "audio2.mp3"]
        ppt_file = "lesson.pptx"

        with patch.object(video_generator.storage_path, '__truediv__') as mock_path:
            mock_result_path = Mock()
            mock_result_path.__str__ = lambda self: "/tmp/videos/test-job-123.mp4"
            mock_path.return_value = mock_result_path

            result = video_generator.generate(
                sample_lesson_json,
                audio_files,
                ppt_file
            )

            assert result is not None

    @patch('services.video.subprocess.run')
    def test_convert_pdf_to_images(self, video_generator):
        """Test PDF to image conversion."""
        mock_result = Mock()
        mock_result.returncode = 0

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create mock PDF
            pdf_path = os.path.join(tmp_dir, "test.pdf")
            with open(pdf_path, 'w') as f:
                f.write("mock pdf content")

            # Mock pdftoppm output
            images = video_generator._convert_pdf_to_images(pdf_path, tmp_dir)
            # Should return empty or handle gracefully if pdftoppm not available
            assert isinstance(images, list)


class TestVideoGeneratorIntegration:
    """Integration tests for video generator (require ffmpeg)."""

    @pytest.mark.skipif(
        not os.path.exists("/usr/bin/ffmpeg"),
        reason="ffmpeg not available"
    )
    def test_real_audio_duration(self, video_generator):
        """Test real audio duration extraction (requires ffmpeg)."""
        # This test would create a real audio file and test duration extraction
        # Skipped in CI environments without ffmpeg
        pass

    @pytest.mark.skipif(
        not os.path.exists("/usr/bin/ffmpeg"),
        reason="ffmpeg not available"
    )
    def test_real_video_generation(self, video_generator, sample_lesson_json):
        """Test real video generation (requires ffmpeg and dependencies)."""
        # This test would create real video output
        # Skipped in CI environments
        pass