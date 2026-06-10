"""
Utilidades para manipulación de video usando FFmpeg.
Módulo: Shared / Utils
"""
import subprocess
from pathlib import Path
from loguru import logger
from typing import Optional

class VideoUtils:
    @staticmethod
    def extract_frame(video_path: str, timestamp_seconds: float, output_path: str) -> bool:
        """
        Extrae un frame específico de un video.
        """
        cmd = [
            'ffmpeg',
            '-ss', str(timestamp_seconds),
            '-i', video_path,
            '-frames:v', '1',
            '-q:v', '2',
            '-y',
            output_path
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extrayendo frame en {timestamp_seconds}s: {e.stderr.decode()}")
            return False

    @staticmethod
    def cut_clip(video_path: str, start_time: float, duration: float, output_path: str) -> bool:
        """
        Corta un clip de video de forma precisa.
        """
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-t', str(duration),
            '-i', video_path,
            '-c:v', 'libx264',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y',
            output_path
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error cortando clip: {e.stderr.decode()}")
            return False

    @staticmethod
    def extract_audio(video_path: str, output_audio_path: str, sample_rate: int = 16000) -> bool:
        """
        Extrae la pista de audio de un video en formato WAV mono.
        """
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', str(sample_rate),
            '-ac', '1',
            '-y',
            output_audio_path
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extrayendo audio: {e.stderr.decode()}")
            return False
