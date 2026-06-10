# CallQA Server - Automatización de Corte de Videos

Sistema de procesamiento y segmentación automática de grabaciones en clips de llamadas individuales.

---

## Estructura del Proyecto

```
callqa-server/
│
├── src/
│   ├── __init__.py
│   ├── main.py                          # API FastAPI
│   ├── worker.py                        # Script de procesamiento
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── database.py
│   │   └── config.yaml
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── operator.py
│   │   ├── transfer_session.py
│   │   ├── uploaded_file.py            # Clip original de 30 min
│   │   ├── call_segment.py             # Llamada detectada
│   │   ├── processed_clip.py           # Clip individual generado
│   │   ├── phone_call.py               # CDR de sistema telefónico
│   │   ├── call_mapping.py             # Correlación clip-llamada
│   │   └── evaluation.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_watcher.py             # Monitor de nuevos archivos
│   │   ├── audio_analyzer.py           # Detección de llamadas
│   │   ├── cdr_sync.py                 # Sincronización CDR
│   │   ├── call_detector.py            # Lógica de detección
│   │   ├── clip_generator.py           # Generación de clips
│   │   ├── correlator.py               # Correlación temporal
│   │   └── storage_manager.py          # Gestión de archivos
│   │
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── pipeline.py                 # Pipeline de procesamiento
│   │   ├── queue_manager.py            # Cola de trabajos
│   │   └── state_machine.py            # Máquina de estados
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── audio_utils.py              # Utilidades de audio
│   │   ├── video_utils.py              # Utilidades de video
│   │   └── helpers.py
│   │
│   └── api/
│       ├── __init__.py
│       ├── app.py
│       └── routes/
│           ├── __init__.py
│           ├── transfers.py
│           ├── uploads.py
│           ├── processing.py           # Monitoreo de procesamiento
│           └── admin.py
│
├── scripts/
│   ├── __init__.py
│   ├── init_db.py                      # Inicializar BD
│   ├── import_cdr.py                   # Importar CDR histórico
│   └── cleanup.py
│
├── alembic/                             # Migraciones
│   ├── versions/
│   └── env.py
│
├── tests/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
│
├── requirements.txt
├── config.yaml
├── .env.example
└── README.md
```

---

## 1. Modelos de Base de Datos

### `models/uploaded_file.py`

```python
"""
Modelo para archivos de grabación original (30 minutos).
"""
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from config.database import Base


class ProcessingState(enum.Enum):
    """Estados de procesamiento de un clip."""
    RECEIVED = "received"               # Recibido
    ANALYZING = "analyzing"             # Analizando audio
    CORTING = "cutting"                 # Cortando en segmentos
    CORRELATING = "correlating"         # Correlacionando con CDR
    GENERATING = "generating"           # Generando clips
    COMPLETED = "completed"             # Completado
    FAILED = "failed"                   # Fallo
    PARTIAL = "partial"                 # Parcialmente exitoso


class UploadedFile(Base):
    """Archivo original de 30 minutos subido por cliente."""
    
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Referencia a sesión de transferencia
    transfer_session_id = Column(Integer, ForeignKey('transfer_sessions.id'), nullable=False)
    transfer_session = relationship("TransferSession")
    
    # Información del archivo
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False, unique=True)
    file_size = Column(BigInteger, nullable=False)
    checksum = Column(String(64), nullable=False)
    
    # Información de grabación
    operator_id = Column(Integer, ForeignKey('operators.id'), nullable=False)
    operator = relationship("Operator")
    
    recording_date = Column(DateTime, nullable=False)  # Fecha de grabación
    duration_seconds = Column(Integer, nullable=True)
    
    # Procesamiento
    state = Column(Enum(ProcessingState), default=ProcessingState.RECEIVED, nullable=False)
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    
    # Resultados
    calls_detected = Column(Integer, default=0)  # Llamadas detectadas
    clips_generated = Column(Integer, default=0)  # Clips generados
    error_message = Column(String(500), nullable=True)
    
    # Relaciones
    call_segments = relationship("CallSegment", back_populates="uploaded_file")
    processed_clips = relationship("ProcessedClip", back_populates="uploaded_file")
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

### `models/call_segment.py`

```python
"""
Modelo para segmentos de llamada detectados en audio.
"""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime

from config.database import Base


class CallSegment(Base):
    """Segmento de llamada detectado en el audio."""
    
    __tablename__ = "call_segments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Referencia al archivo original
    uploaded_file_id = Column(Integer, ForeignKey('uploaded_files.id'), nullable=False)
    uploaded_file = relationship("UploadedFile", back_populates="call_segments")
    
    # Ubicación temporal en el archivo original
    start_time_seconds = Column(Float, nullable=False)  # Inicio del segmento
    end_time_seconds = Column(Float, nullable=False)    # Fin del segmento
    duration_seconds = Column(Float, nullable=False)
    
    # Información de audio
    silence_confidence = Column(Float)   # Confianza en detección de silencios
    speech_confidence = Column(Float)    # Confianza en detección de voz
    
    # Correlación con CDR (opcional, puede ser None)
    phone_call_id = Column(Integer, ForeignKey('phone_calls.id'), nullable=True)
    phone_call = relationship("PhoneCall", back_populates="call_segments")
    
    # Información de correlación
    correlation_confidence = Column(Float)  # Confianza en el matching
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

### `models/phone_call.py`

```python
"""
Modelo para registros de llamadas del sistema telefónico (CDR).
"""
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from config.database import Base


class PhoneCall(Base):
    """Registro de llamada del sistema telefónico (CDR)."""
    
    __tablename__ = "phone_calls"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identificación
    call_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Operador y dirección
    operator_id = Column(Integer, ForeignKey('operators.id'), nullable=False)
    operator = relationship("Operator")
    
    # Detalles de la llamada
    phone_number = Column(String(50))
    call_direction = Column(String(20))  # inbound, outbound
    call_type = Column(String(50))       # voice, queue, etc
    
    # Timestamps exactos
    start_time = Column(DateTime, nullable=False, index=True)  # Hora inicio
    end_time = Column(DateTime, nullable=False)                # Hora fin
    duration_seconds = Column(Integer, nullable=False)
    
    # Información adicional
    disposition = Column(String(100))  # hangup, abandoned, transferred, etc
    queue_name = Column(String(100))
    
    # Relaciones
    call_segments = relationship("CallSegment", back_populates="phone_call")
    
    # Timestamps de importación
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Índices para búsquedas rápidas
    __table_args__ = (
        # Índice para búsquedas por operador y fecha
        # CREATE INDEX idx_phone_calls_operator_start ON phone_calls(operator_id, start_time)
    )
```

### `models/processed_clip.py`

```python
"""
Modelo para clips procesados individuales.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from config.database import Base


class ProcessedClip(Base):
    """Clip de video procesado (una llamada individual)."""
    
    __tablename__ = "processed_clips"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Referencia a archivos
    uploaded_file_id = Column(Integer, ForeignKey('uploaded_files.id'), nullable=False)
    uploaded_file = relationship("UploadedFile", back_populates="processed_clips")
    
    call_segment_id = Column(Integer, ForeignKey('call_segments.id'), nullable=True)
    call_segment = relationship("CallSegment")
    
    phone_call_id = Column(Integer, ForeignKey('phone_calls.id'), nullable=True)
    phone_call = relationship("PhoneCall")
    
    # Información del clip
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False, unique=True)
    file_size = Column(Integer)
    
    # Ubicación en el original
    start_time_seconds = Column(Float, nullable=False)
    end_time_seconds = Column(Float, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    
    # Operador
    operator_id = Column(Integer, ForeignKey('operators.id'), nullable=False)
    operator = relationship("Operator")
    
    # Metadata de la llamada
    call_metadata = Column(JSON, nullable=True)  # {
        #   "phone_number": "...",
        #   "direction": "inbound",
        #   "disposition": "completed",
        #   "original_duration": 245
        # }
    
    # Estados
    status = Column(String(20), default="ready")  # ready, archived, evaluated
    is_archived = Column(String(1), default="N")
    
    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

---

## 2. Servicios de Procesamiento

### `services/file_watcher.py`

```python
"""
Monitor de nuevos archivos subidos al servidor.
"""
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
from loguru import logger
import time

from config.settings import Settings
from models.uploaded_file import UploadedFile, ProcessingState
from processing.queue_manager import ProcessingQueueManager


class FileWatcher:
    """Monitor de nuevos archivos para procesamiento."""
    
    def __init__(self, settings: Settings, db_session):
        self.settings = settings
        self.db = db_session
        self.upload_dir = Path(settings.upload_directory)
        self.queue_manager = ProcessingQueueManager(db_session)
    
    def scan_for_new_files(self) -> List[UploadedFile]:
        """
        Escanea el directorio de uploads buscando archivos nuevos.
        
        Returns:
            Lista de archivos encontrados
        """
        new_files = []
        
        if not self.upload_dir.exists():
            logger.warning(f"Directorio no existe: {self.upload_dir}")
            return new_files
        
        # Buscar archivos de video que no hayan sido procesados
        for file_path in self.upload_dir.rglob("*.mkv"):
            uploaded_file = self._check_file_in_db(file_path)
            
            if uploaded_file:
                # Ya existe en BD
                if uploaded_file.state == ProcessingState.RECEIVED:
                    # Listo para procesar
                    new_files.append(uploaded_file)
            else:
                logger.debug(f"Archivo encontrado pero no está en BD: {file_path}")
        
        return new_files
    
    def _check_file_in_db(self, file_path: Path) -> Optional[UploadedFile]:
        """Verifica si un archivo está registrado en la BD."""
        return self.db.query(UploadedFile).filter(
            UploadedFile.file_path == str(file_path)
        ).first()
    
    def watch_continuously(self, check_interval: int = 30):
        """
        Monitorea continuamente nuevos archivos.
        
        Args:
            check_interval: Intervalo de escaneo en segundos
        """
        logger.info(f"Iniciando monitoreo de archivos (cada {check_interval}s)")
        
        while True:
            try:
                new_files = self.scan_for_new_files()
                
                for uploaded_file in new_files:
                    logger.info(f"Nuevo archivo encontrado: {uploaded_file.filename}")
                    
                    # Agregar a cola de procesamiento
                    self.queue_manager.enqueue_for_processing(uploaded_file)
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error en file watcher: {e}")
                time.sleep(check_interval)
```

### `services/audio_analyzer.py`

```python
"""
Análisis de audio para detección de llamadas.
"""
import librosa
import numpy as np
from typing import List, Tuple
from loguru import logger

from config.settings import Settings
from models.call_segment import CallSegment
from utils.audio_utils import AudioUtils


class AudioAnalyzer:
    """Analizador de audio para detectar límites de llamadas."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.audio_utils = AudioUtils()
        
        # Parámetros de detección
        self.silence_threshold_db = -40  # dB
        self.min_call_duration = 3       # Duración mínima de llamada en segundos
        self.silence_duration = 2        # Segundos de silencio para marcar fin
        self.frame_duration = 0.020      # 20ms frames
    
    def detect_call_segments(self, audio_file_path: str) -> List[Tuple[float, float]]:
        """
        Detecta segmentos de llamadas en un archivo de audio.
        
        Args:
            audio_file_path: Ruta del archivo de audio
            
        Returns:
            Lista de tuplas (start_time, end_time) en segundos
        """
        logger.info(f"Analizando audio: {audio_file_path}")
        
        try:
            # Cargar audio
            y, sr = librosa.load(audio_file_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            logger.info(f"Audio cargado: {duration:.1f} segundos, SR: {sr} Hz")
            
            # Detectar energía en cada frame
            S = librosa.feature.melspectrogram(y=y, sr=sr)
            energy = librosa.power_to_db(S, ref=np.max)
            
            # Calcula energía promedio por frame
            frame_energy = np.mean(energy, axis=0)
            
            # Detectar frames silenciosos
            is_silent = frame_energy < self.silence_threshold_db
            
            # Convertir frames a tiempo
            frame_times = librosa.frames_to_time(
                np.arange(len(is_silent)),
                sr=sr
            )
            
            # Detectar transiciones silencio -> sonido -> silencio
            segments = self._extract_segments_from_silence(
                is_silent,
                frame_times
            )
            
            logger.info(f"Detectados {len(segments)} segmentos de llamadas")
            
            return segments
            
        except Exception as e:
            logger.error(f"Error analizando audio: {e}")
            raise
    
    def _extract_segments_from_silence(
        self,
        is_silent: np.ndarray,
        frame_times: np.ndarray
    ) -> List[Tuple[float, float]]:
        """
        Extrae segmentos basado en transiciones de silencio.
        
        Args:
            is_silent: Array booleano indicando frames silenciosos
            frame_times: Tiempos correspondientes a cada frame
            
        Returns:
            Lista de segmentos (start, end)
        """
        segments = []
        
        # Invertir para detectar sonido
        has_sound = ~is_silent
        
        # Detectar transiciones
        transitions = np.diff(has_sound.astype(int))
        starts = np.where(transitions == 1)[0]  # Inicio de sonido
        ends = np.where(transitions == -1)[0]    # Fin de sonido
        
        # Asegurar que emparejemos correctamente
        if len(starts) > 0 and len(ends) > 0:
            # Si comienza con sonido
            if starts[0] > ends[0]:
                ends = ends[1:]
            
            # Si termina con sonido
            if len(starts) > len(ends):
                starts = starts[:len(ends)]
        
        # Crear segmentos
        for start_idx, end_idx in zip(starts, ends):
            start_time = frame_times[start_idx]
            end_time = frame_times[end_idx]
            duration = end_time - start_time
            
            # Filtrar por duración mínima
            if duration >= self.min_call_duration:
                segments.append((start_time, end_time))
        
        return segments
    
    def analyze_call_quality(self, audio_file_path: str, segment: Tuple[float, float]) -> dict:
        """
        Analiza la calidad de un segmento de llamada.
        
        Args:
            audio_file_path: Ruta del archivo
            segment: Tupla (start_time, end_time)
            
        Returns:
            Dict con métricas de calidad
        """
        try:
            y, sr = librosa.load(audio_file_path, sr=None)
            
            # Extraer segmento
            start_sample = int(segment[0] * sr)
            end_sample = int(segment[1] * sr)
            segment_audio = y[start_sample:end_sample]
            
            # Calcular métricas
            mfcc = librosa.feature.mfcc(y=segment_audio, sr=sr)
            zero_crossing_rate = librosa.feature.zero_crossing_rate(segment_audio)
            
            return {
                'mfcc_mean': float(np.mean(mfcc)),
                'zcr_mean': float(np.mean(zero_crossing_rate)),
                'rms_energy': float(np.sqrt(np.mean(segment_audio**2))),
                'duration': segment[1] - segment[0]
            }
            
        except Exception as e:
            logger.error(f"Error analizando calidad: {e}")
            return {}
```

### `services/cdr_sync.py`

```python
"""
Sincronización de registros CDR del sistema telefónico.
"""
from datetime import datetime, timedelta, date
from typing import List, Optional
from loguru import logger

from config.settings import Settings
from models.phone_call import PhoneCall
from models.operator import Operator


class CDRSync:
    """Sincronizador de registros CDR."""
    
    def __init__(self, settings: Settings, db_session):
        self.settings = settings
        self.db = db_session
    
    def sync_cdr_for_date(self, target_date: date) -> int:
        """
        Sincroniza registros CDR para una fecha específica.
        
        Args:
            target_date: Fecha para sincronizar (date object)
            
        Returns:
            Cantidad de registros importados
        """
        logger.info(f"Sincronizando CDR para {target_date}")
        
        try:
            # Obtener registros del sistema telefónico
            cdr_records = self._fetch_cdr_from_telephony_system(target_date)
            
            if not cdr_records:
                logger.info("No hay registros CDR para esa fecha")
                return 0
            
            logger.info(f"Obtenidos {len(cdr_records)} registros del sistema telefónico")
            
            # Importar cada registro
            imported_count = 0
            for cdr in cdr_records:
                if self._import_cdr_record(cdr):
                    imported_count += 1
            
            self.db.commit()
            
            logger.info(f"Importados {imported_count}/{len(cdr_records)} registros CDR")
            
            return imported_count
            
        except Exception as e:
            logger.error(f"Error sincronizando CDR: {e}")
            self.db.rollback()
            raise
    
    def _fetch_cdr_from_telephony_system(self, target_date: date) -> List[dict]:
        """
        Obtiene registros CDR del sistema telefónico.
        
        Este método debe adaptarse al sistema telefónico específico.
        Ejemplos: UCCX, Avaya, FreePBX, etc.
        
        Args:
            target_date: Fecha para consultar
            
        Returns:
            Lista de diccionarios con información de llamadas
        """
        # Ejemplo: Conectar a UCCX via API
        # En realidad, esto dependería del sistema telefónico específico
        
        import requests
        
        api_url = self.settings.cdr_api_url
        headers = {
            'Authorization': f'Bearer {self.settings.cdr_api_token}'
        }
        
        params = {
            'date': target_date.isoformat(),
            'limit': 10000
        }
        
        try:
            response = requests.get(
                f"{api_url}/calls",
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            return response.json().get('calls', [])
            
        except Exception as e:
            logger.error(f"Error fetching CDR: {e}")
            return []
    
    def _import_cdr_record(self, cdr: dict) -> bool:
        """
        Importa un registro CDR individual.
        
        Args:
            cdr: Diccionario con datos del CDR
            
        Returns:
            True si se importó exitosamente
        """
        try:
            # Verificar que el operador existe
            operator = self.db.query(Operator).filter(
                Operator.operator_code == cdr['operator_code']
            ).first()
            
            if not operator:
                logger.warning(f"Operador no encontrado: {cdr['operator_code']}")
                return False
            
            # Verificar que no exista ya
            existing = self.db.query(PhoneCall).filter(
                PhoneCall.call_id == cdr['call_id']
            ).first()
            
            if existing:
                logger.debug(f"Llamada ya existe: {cdr['call_id']}")
                return False
            
            # Crear registro
            phone_call = PhoneCall(
                call_id=cdr['call_id'],
                operator_id=operator.id,
                phone_number=cdr.get('phone_number'),
                call_direction=cdr.get('direction', 'inbound'),
                call_type=cdr.get('call_type'),
                start_time=datetime.fromisoformat(cdr['start_time']),
                end_time=datetime.fromisoformat(cdr['end_time']),
                duration_seconds=cdr['duration'],
                disposition=cdr.get('disposition'),
                queue_name=cdr.get('queue_name')
            )
            
            self.db.add(phone_call)
            
            return True
            
        except Exception as e:
            logger.error(f"Error importing CDR record: {e}")
            return False
    
    def sync_continuous(self, check_interval: int = 300):
        """
        Sincronización continua de CDR.
        
        Args:
            check_interval: Intervalo de verificación en segundos
        """
        import time
        
        logger.info("Iniciando sincronización continua de CDR")
        
        while True:
            try:
                # Sincronizar últimos N días
                for days_ago in range(0, self.settings.cdr_sync_days_back):
                    target_date = datetime.now().date() - timedelta(days=days_ago)
                    self.sync_cdr_for_date(target_date)
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error en sincronización continua: {e}")
                time.sleep(check_interval)
```

### `services/correlator.py`

```python
"""
Correlación entre segmentos de video y registros CDR.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from loguru import logger

from models.call_segment import CallSegment
from models.phone_call import PhoneCall
from models.uploaded_file import UploadedFile


class CallCorrelator:
    """Correlaciona segmentos de video con registros CDR."""
    
    def __init__(self, settings, db_session):
        self.settings = settings
        self.db = db_session
        
        # Tolerancia de timing (en segundos)
        self.time_tolerance = 30
        self.duration_tolerance_percent = 0.15  # 15%
    
    def correlate_segments_with_cdr(
        self,
        uploaded_file: UploadedFile
    ) -> int:
        """
        Correlaciona los segmentos detectados con registros CDR.
        
        Args:
            uploaded_file: Archivo original procesado
            
        Returns:
            Cantidad de segmentos correlacionados
        """
        logger.info(f"Correlacionando segmentos con CDR para {uploaded_file.filename}")
        
        correlated_count = 0
        
        for segment in uploaded_file.call_segments:
            # Obtener llamada correlacionada
            phone_call = self._find_matching_call(uploaded_file, segment)
            
            if phone_call:
                segment.phone_call_id = phone_call.id
                segment.correlation_confidence = self._calculate_confidence(
                    uploaded_file,
                    segment,
                    phone_call
                )
                correlated_count += 1
                
                logger.debug(
                    f"Correlacionado: {segment.start_time_seconds}s "
                    f"-> Llamada {phone_call.call_id} "
                    f"(confianza: {segment.correlation_confidence:.2f})"
                )
            else:
                logger.debug(
                    f"No se encontró correlación para segmento en {segment.start_time_seconds}s"
                )
        
        self.db.commit()
        
        logger.info(f"Correlacionados {correlated_count}/{len(uploaded_file.call_segments)} segmentos")
        
        return correlated_count
    
    def _find_matching_call(
        self,
        uploaded_file: UploadedFile,
        segment: CallSegment
    ) -> Optional[PhoneCall]:
        """
        Busca la llamada CDR que corresponde a un segmento.
        
        Args:
            uploaded_file: Archivo original
            segment: Segmento de llamada
            
        Returns:
            Registro PhoneCall si lo encuentra
        """
        # Calcular tiempo absoluto del segmento
        # El archivo se grabó en uploaded_file.recording_date
        segment_start_absolute = (
            uploaded_file.recording_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(seconds=segment.start_time_seconds)
        )
        
        segment_end_absolute = (
            uploaded_file.recording_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(seconds=segment.end_time_seconds)
        )
        
        segment_duration = segment.end_time_seconds - segment.start_time_seconds
        
        # Buscar llamadas cercanas en tiempo
        time_window_start = segment_start_absolute - timedelta(seconds=self.time_tolerance)
        time_window_end = segment_end_absolute + timedelta(seconds=self.time_tolerance)
        
        candidates = self.db.query(PhoneCall).filter(
            PhoneCall.operator_id == uploaded_file.operator_id,
            PhoneCall.start_time >= time_window_start,
            PhoneCall.start_time <= time_window_end
        ).all()
        
        if not candidates:
            return None
        
        # Seleccionar el mejor match
        best_match = None
        best_score = -1
        
        for call in candidates:
            # Calcular diferencia de timing
            time_diff = abs(
                (segment_start_absolute - call.start_time).total_seconds()
            )
            
            # Calcular diferencia de duración
            duration_diff = abs(
                segment_duration - call.duration_seconds
            ) / call.duration_seconds if call.duration_seconds > 0 else 0
            
            # Score: penalizar diferencias
            score = 100 - time_diff - (duration_diff * 100)
            
            if score > best_score and duration_diff < self.duration_tolerance_percent:
                best_match = call
                best_score = score
        
        return best_match
    
    def _calculate_confidence(
        self,
        uploaded_file: UploadedFile,
        segment: CallSegment,
        phone_call: PhoneCall
    ) -> float:
        """
        Calcula confianza de la correlación (0-1).
        
        Args:
            uploaded_file: Archivo original
            segment: Segmento de video
            phone_call: Llamada CDR
            
        Returns:
            Score de confianza (0-1)
        """
        # Calcular tiempo absoluto del segmento
        segment_start_absolute = (
            uploaded_file.recording_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(seconds=segment.start_time_seconds)
        )
        
        segment_duration = segment.end_time_seconds - segment.start_time_seconds
        
        # Diferencia de timing
        time_diff = abs(
            (segment_start_absolute - phone_call.start_time).total_seconds()
        )
        
        # Diferencia de duración
        duration_diff = abs(
            segment_duration - phone_call.duration_seconds
        ) / phone_call.duration_seconds if phone_call.duration_seconds > 0 else 0
        
        # Calcular confianza como función inversa de diferencias
        time_penalty = max(0, 1 - (time_diff / self.time_tolerance))
        duration_penalty = max(0, 1 - (duration_diff * 5))  # Peso más alto a duración
        
        confidence = (time_penalty + duration_penalty) / 2
        
        return max(0, min(1, confidence))
```

### `services/clip_generator.py`

```python
"""
Generación de clips individuales a partir de segmentos detectados.
"""
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional
from loguru import logger

from config.settings import Settings
from models.uploaded_file import UploadedFile
from models.processed_clip import ProcessedClip
from models.call_segment import CallSegment


class ClipGenerator:
    """Generador de clips individuales."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.output_base_dir = Path(settings.clips_output_directory)
    
    def generate_clips_for_file(self, uploaded_file: UploadedFile, db_session) -> int:
        """
        Genera clips individuales para cada segmento de un archivo.
        
        Args:
            uploaded_file: Archivo original
            db_session: Sesión de BD
            
        Returns:
            Cantidad de clips generados
        """
        logger.info(f"Generando clips para {uploaded_file.filename}")
        
        generated_count = 0
        
        for segment in uploaded_file.call_segments:
            try:
                clip = self.generate_clip_for_segment(
                    uploaded_file,
                    segment,
                    db_session
                )
                
                if clip:
                    generated_count += 1
                    logger.success(f"Clip generado: {clip.filename}")
                    
            except Exception as e:
                logger.error(f"Error generando clip: {e}")
        
        logger.info(f"Clips generados: {generated_count}")
        
        return generated_count
    
    def generate_clip_for_segment(
        self,
        uploaded_file: UploadedFile,
        segment: CallSegment,
        db_session
    ) -> Optional[ProcessedClip]:
        """
        Genera un clip individual para un segmento específico.
        
        Args:
            uploaded_file: Archivo original
            segment: Segmento a extraer
            db_session: Sesión de BD
            
        Returns:
            Registro ProcessedClip creado
        """
        try:
            # Construir nombre de salida
            output_filename = self._build_output_filename(
                uploaded_file,
                segment
            )
            
            # Construir path de salida
            output_dir = self._build_output_directory(uploaded_file, segment)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / output_filename
            
            # Extraer clip usando FFmpeg
            self._extract_clip_ffmpeg(
                uploaded_file.file_path,
                segment.start_time_seconds,
                segment.end_time_seconds,
                str(output_path)
            )
            
            # Obtener tamaño del archivo generado
            file_size = output_path.stat().st_size
            
            # Crear registro en BD
            processed_clip = ProcessedClip(
                uploaded_file_id=uploaded_file.id,
                call_segment_id=segment.id,
                phone_call_id=segment.phone_call_id,
                filename=output_filename,
                file_path=str(output_path),
                file_size=file_size,
                start_time_seconds=segment.start_time_seconds,
                end_time_seconds=segment.end_time_seconds,
                duration_seconds=segment.duration_seconds,
                operator_id=uploaded_file.operator_id,
                status="ready",
                call_metadata=self._build_call_metadata(segment)
            )
            
            db_session.add(processed_clip)
            db_session.commit()
            
            return processed_clip
            
        except Exception as e:
            logger.error(f"Error generando clip para segmento: {e}")
            return None
    
    def _build_output_filename(
        self,
        uploaded_file: UploadedFile,
        segment: CallSegment
    ) -> str:
        """
        Construye nombre del archivo de salida.
        
        Formato: {operator}_{date}_{call_id}_{start_time}.mp4
        """
        date_str = uploaded_file.recording_date.strftime("%Y%m%d")
        
        if segment.phone_call_id and segment.phone_call:
            call_id = segment.phone_call.call_id
        else:
            call_id = f"seg_{int(segment.start_time_seconds)}"
        
        start_time = int(segment.start_time_seconds)
        
        filename = f"{uploaded_file.operator.operator_code}_{date_str}_{call_id}_{start_time}.mp4"
        
        return filename
    
    def _build_output_directory(
        self,
        uploaded_file: UploadedFile,
        segment: CallSegment
    ) -> Path:
        """
        Construye directorio de salida.
        
        Estructura: /clips/{operator}/{date}/{call_id}/
        """
        date_str = uploaded_file.recording_date.strftime("%Y-%m-%d")
        
        if segment.phone_call_id and segment.phone_call:
            call_id = segment.phone_call.call_id
        else:
            call_id = f"segment_{int(segment.start_time_seconds)}"
        
        output_dir = (
            self.output_base_dir 
            / uploaded_file.operator.operator_code 
            / date_str 
            / call_id
        )
        
        return output_dir
    
    def _extract_clip_ffmpeg(
        self,
        input_path: str,
        start_seconds: float,
        end_seconds: float,
        output_path: str
    ):
        """
        Extrae un clip usando FFmpeg.
        
        Args:
            input_path: Archivo de entrada
            start_seconds: Tiempo de inicio
            end_seconds: Tiempo de fin
            output_path: Archivo de salida
        """
        duration = end_seconds - start_seconds
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ss', str(start_seconds),
            '-t', str(duration),
            '-c:v', 'libx264',           # Codec de video
            '-crf', '23',                 # Calidad (0-51, lower = better)
            '-c:a', 'aac',               # Codec de audio
            '-b:a', '128k',              # Bitrate de audio
            '-y',                         # Sobrescribir sin preguntar
            output_path
        ]
        
        logger.debug(f"Ejecutando FFmpeg: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos max
            )
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg error: {result.stderr}")
            
            logger.debug(f"Clip extraído exitosamente: {output_path}")
            
        except subprocess.TimeoutExpired:
            raise Exception("FFmpeg timeout")
        except Exception as e:
            raise Exception(f"Error extrayendo clip: {e}")
    
    def _build_call_metadata(self, segment: CallSegment) -> dict:
        """
        Construye metadata de la llamada para el clip.
        
        Args:
            segment: Segmento de llamada
            
        Returns:
            Diccionario con metadata
        """
        metadata = {
            'duration': segment.duration_seconds,
            'segment_confidence': segment.silence_confidence
        }
        
        if segment.phone_call:
            metadata.update({
                'phone_number': segment.phone_call.phone_number,
                'direction': segment.phone_call.call_direction,
                'disposition': segment.phone_call.disposition,
                'original_duration': segment.phone_call.duration_seconds,
                'correlation_confidence': segment.correlation_confidence
            })
        
        return metadata
```

---

## 3. Pipeline de Procesamiento

### `processing/pipeline.py`

```python
"""
Pipeline principal de procesamiento de videos.
"""
from datetime import datetime
from loguru import logger

from config.database import SessionLocal
from config.settings import Settings

from models.uploaded_file import UploadedFile, ProcessingState
from models.call_segment import CallSegment

from services.audio_analyzer import AudioAnalyzer
from services.cdr_sync import CDRSync
from services.correlator import CallCorrelator
from services.clip_generator import ClipGenerator
from utils.video_utils import VideoUtils


class ProcessingPipeline:
    """Pipeline principal de procesamiento."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.db = SessionLocal()
        
        self.audio_analyzer = AudioAnalyzer(settings)
        self.cdr_sync = CDRSync(settings, self.db)
        self.correlator = CallCorrelator(settings, self.db)
        self.clip_generator = ClipGenerator(settings)
        self.video_utils = VideoUtils(settings)
    
    def process_uploaded_file(self, uploaded_file: UploadedFile) -> bool:
        """
        Procesa un archivo subido a través del pipeline completo.
        
        Args:
            uploaded_file: Archivo a procesar
            
        Returns:
            True si el procesamiento fue exitoso
        """
        logger.info(f"Iniciando procesamiento: {uploaded_file.filename}")
        
        try:
            # PASO 1: Extraer audio del video
            logger.info("PASO 1: Extrayendo audio...")
            audio_path = self._extract_audio(uploaded_file)
            
            # PASO 2: Analizar audio y detectar llamadas
            logger.info("PASO 2: Detectando llamadas...")
            segments = self._detect_call_segments(uploaded_file, audio_path)
            
            if not segments:
                logger.warning("No se detectaron llamadas")
                uploaded_file.state = ProcessingState.COMPLETED
                uploaded_file.calls_detected = 0
                self.db.commit()
                return True
            
            # PASO 3: Sincronizar CDR
            logger.info("PASO 3: Sincronizando CDR...")
            self._sync_cdr(uploaded_file)
            
            # PASO 4: Correlacionar con CDR
            logger.info("PASO 4: Correlacionando con CDR...")
            correlations = self._correlate_with_cdr(uploaded_file)
            
            # PASO 5: Generar clips
            logger.info("PASO 5: Generando clips...")
            clips_generated = self._generate_clips(uploaded_file)
            
            # Actualizar estado
            uploaded_file.state = ProcessingState.COMPLETED
            uploaded_file.processing_completed_at = datetime.utcnow()
            uploaded_file.clips_generated = clips_generated
            
            self.db.commit()
            
            logger.success(
                f"✓ Procesamiento completado: "
                f"{uploaded_file.calls_detected} llamadas, "
                f"{clips_generated} clips generados"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error en pipeline: {e}")
            logger.exception(e)
            
            uploaded_file.state = ProcessingState.FAILED
            uploaded_file.error_message = str(e)
            self.db.commit()
            
            return False
        
        finally:
            # Limpieza
            try:
                if audio_path and audio_path.exists():
                    audio_path.unlink()
                    logger.debug("Archivo de audio temporal eliminado")
            except:
                pass
    
    def _extract_audio(self, uploaded_file: UploadedFile) -> str:
        """
        Extrae audio del video.
        
        Args:
            uploaded_file: Archivo de video
            
        Returns:
            Ruta del archivo de audio extraído
        """
        uploaded_file.state = ProcessingState.ANALYZING
        self.db.commit()
        
        audio_path = self.video_utils.extract_audio(uploaded_file.file_path)
        
        logger.debug(f"Audio extraído: {audio_path}")
        
        return audio_path
    
    def _detect_call_segments(
        self,
        uploaded_file: UploadedFile,
        audio_path: str
    ) -> int:
        """
        Detecta segmentos de llamadas en el audio.
        
        Args:
            uploaded_file: Archivo original
            audio_path: Ruta del archivo de audio
            
        Returns:
            Cantidad de segmentos detectados
        """
        # Analizar audio
        segment_list = self.audio_analyzer.detect_call_segments(audio_path)
        
        if not segment_list:
            return 0
        
        # Crear registros en BD
        for start_time, end_time in segment_list:
            segment = CallSegment(
                uploaded_file_id=uploaded_file.id,
                start_time_seconds=start_time,
                end_time_seconds=end_time,
                duration_seconds=end_time - start_time
            )
            self.db.add(segment)
        
        self.db.commit()
        
        uploaded_file.calls_detected = len(segment_list)
        self.db.commit()
        
        logger.info(f"Detectados {len(segment_list)} segmentos de llamadas")
        
        return len(segment_list)
    
    def _sync_cdr(self, uploaded_file: UploadedFile):
        """
        Sincroniza registros CDR para la fecha del archivo.
        
        Args:
            uploaded_file: Archivo original
        """
        from datetime import date
        
        recording_date = uploaded_file.recording_date.date()
        self.cdr_sync.sync_cdr_for_date(recording_date)
    
    def _correlate_with_cdr(self, uploaded_file: UploadedFile) -> int:
        """
        Correlaciona segmentos con registros CDR.
        
        Args:
            uploaded_file: Archivo original
            
        Returns:
            Cantidad de correlaciones exitosas
        """
        return self.correlator.correlate_segments_with_cdr(uploaded_file)
    
    def _generate_clips(self, uploaded_file: UploadedFile) -> int:
        """
        Genera clips individuales.
        
        Args:
            uploaded_file: Archivo original
            
        Returns:
            Cantidad de clips generados
        """
        return self.clip_generator.generate_clips_for_file(uploaded_file, self.db)
```

### `processing/queue_manager.py`

```python
"""
Gestión de cola de procesamiento.
"""
from typing import Optional
from datetime import datetime
from loguru import logger

from models.uploaded_file import UploadedFile, ProcessingState


class ProcessingQueueManager:
    """Gestor de cola de procesamiento."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def enqueue_for_processing(self, uploaded_file: UploadedFile):
        """
        Agrega un archivo a la cola de procesamiento.
        
        Args:
            uploaded_file: Archivo a procesar
        """
        if uploaded_file.state != ProcessingState.RECEIVED:
            logger.warning(f"Archivo no está en estado RECEIVED: {uploaded_file.filename}")
            return
        
        uploaded_file.state = ProcessingState.ANALYZING
        uploaded_file.processing_started_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(f"Archivo encolado: {uploaded_file.filename}")
    
    def get_next_for_processing(self) -> Optional[UploadedFile]:
        """
        Obtiene el siguiente archivo para procesar.
        
        Returns:
            Siguiente archivo en la cola
        """
        file = self.db.query(UploadedFile).filter(
            UploadedFile.state == ProcessingState.RECEIVED
        ).order_by(
            UploadedFile.uploaded_at.asc()
        ).first()
        
        return file
```

---

## 4. Script Principal de Worker

### `worker.py`

```python
#!/usr/bin/env python3
"""
CallQA Server - Worker de Procesamiento
Script principal que ejecuta el pipeline de procesamiento.
"""
import sys
import time
import signal
from pathlib import Path
from datetime import datetime, timedelta

from loguru import logger

from config.settings import Settings
from config.database import SessionLocal, engine, Base
from utils.logger import setup_logging

from services.file_watcher import FileWatcher
from processing.pipeline import ProcessingPipeline
from processing.queue_manager import ProcessingQueueManager

from models.uploaded_file import ProcessingState


class ProcessingWorker:
    """Worker principal de procesamiento."""
    
    def __init__(self):
        self.settings = Settings()
        setup_logging(self.settings)
        
        self.db = SessionLocal()
        self.file_watcher = FileWatcher(self.settings, self.db)
        self.pipeline = ProcessingPipeline(self.settings)
        self.queue_manager = ProcessingQueueManager(self.db)
        
        self.running = False
        self.processed_files = 0
        self.failed_files = 0
        
        logger.info("=== CallQA Server - Processing Worker ===")
        logger.info(f"Upload Dir: {self.settings.upload_directory}")
        logger.info(f"Output Dir: {self.settings.clips_output_directory}")
    
    def start(self):
        """Inicia el worker de procesamiento."""
        self.running = True
        logger.info("Iniciando worker...")
        
        try:
            # Inicializar BD si es necesario
            Base.metadata.create_all(bind=engine)
            
            # Limpiar timeouts previos
            self._clean_stuck_processing()
            
            # Iniciar loop de procesamiento
            self._run_processing_loop()
            
        except KeyboardInterrupt:
            logger.info("Interrupción recibida")
            self.stop()
        except Exception as e:
            logger.error(f"Error en worker: {e}")
            logger.exception(e)
            sys.exit(1)
    
    def _run_processing_loop(self):
        """Loop principal de procesamiento."""
        logger.info("Worker listo, esperando archivos para procesar...")
        
        check_interval = self.settings.get('worker', {}).get('check_interval', 30)
        
        while self.running:
            try:
                # Obtener siguiente archivo de la cola
                uploaded_file = self.queue_manager.get_next_for_processing()
                
                if uploaded_file:
                    logger.info(f"Procesando archivo: {uploaded_file.filename}")
                    
                    # Procesar archivo
                    success = self.pipeline.process_uploaded_file(uploaded_file)
                    
                    if success:
                        self.processed_files += 1
                        logger.success(f"✓ Archivo procesado: {uploaded_file.filename}")
                    else:
                        self.failed_files += 1
                        logger.error(f"✗ Fallo procesando: {uploaded_file.filename}")
                    
                    # Estadísticas
                    self._log_statistics()
                else:
                    # Sin archivos, esperar
                    logger.debug("Sin archivos para procesar, esperando...")
                    time.sleep(check_interval)
                    
            except Exception as e:
                logger.error(f"Error en loop de procesamiento: {e}")
                logger.exception(e)
                time.sleep(check_interval)
    
    def _clean_stuck_processing(self):
        """Limpia archivos que quedaron en estado de procesamiento."""
        from models.uploaded_file import UploadedFile
        
        # Timeout de 2 horas
        timeout_hours = 2
        cutoff_time = datetime.utcnow() - timedelta(hours=timeout_hours)
        
        stuck_files = self.db.query(UploadedFile).filter(
            UploadedFile.state.in_([
                ProcessingState.ANALYZING,
                ProcessingState.CORTING,
                ProcessingState.CORRELATING,
                ProcessingState.GENERATING
            ]),
            UploadedFile.processing_started_at < cutoff_time
        ).all()
        
        for file in stuck_files:
            logger.warning(f"Limpiando archivo stuck: {file.filename}")
            file.state = ProcessingState.RECEIVED
            file.processing_started_at = None
        
        if stuck_files:
            self.db.commit()
            logger.info(f"Limpiados {len(stuck_files)} archivos stuck")
    
    def _log_statistics(self):
        """Registra estadísticas de procesamiento."""
        logger.info(
            f"Estadísticas - Procesados: {self.processed_files}, "
            f"Fallidos: {self.failed_files}"
        )
    
    def stop(self):
        """Detiene el worker."""
        logger.info("Deteniendo worker...")
        self.running = False
        self.db.close()
        logger.info("Worker detenido")


def signal_handler(signum, frame):
    """Manejador de señales."""
    logger.info(f"Señal recibida: {signum}")
    sys.exit(0)


def main():
    """Función principal."""
    # Configurar manejadores de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Iniciar worker
    worker = ProcessingWorker()
    worker.start()


if __name__ == "__main__":
    main()
```

---

## 5. Configuración

### `config/settings.py`

```python
"""
Configuración del servidor.
"""
import os
from pathlib import Path
import yaml
from dotenv import load_dotenv


class Settings:
    """Configuración principal."""
    
    def __init__(self, config_path: str = "config.yaml"):
        load_dotenv()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Database
        self.database_url = os.getenv(
            "DATABASE_URL",
            self.config['database']['url']
        )
        
        # Storage
        self.upload_directory = Path(self.config['storage']['upload_directory'])
        self.clips_output_directory = Path(self.config['storage']['clips_output_directory'])
        self.temp_directory = Path(self.config['storage'].get('temp_directory', '/tmp/callqa'))
        
        # CDR Integration
        self.cdr_api_url = self.config['cdr']['api_url']
        self.cdr_api_token = os.getenv('CDR_API_TOKEN', '')
        self.cdr_sync_days_back = self.config['cdr'].get('sync_days_back', 7)
        
        # Processing
        self.ffmpeg_path = self.config['processing'].get('ffmpeg_path', 'ffmpeg')
        self.ffprobe_path = self.config['processing'].get('ffprobe_path', 'ffprobe')
        
        # Worker
        self.worker_check_interval = self.config['worker'].get('check_interval', 30)
        self.worker_max_concurrent = self.config['worker'].get('max_concurrent', 3)
        
        # Logging
        self.log_level = self.config['logging'].get('level', 'INFO')
    
    def get(self, *keys, default=None):
        """Obtiene valor de configuración usando notación de puntos."""
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
```

### `config.yaml`

```yaml
# CallQA Server Configuration

database:
  url: "postgresql://callqa:password@localhost:5432/callqa_db"

storage:
  upload_directory: "/data/callqa/uploads"
  clips_output_directory: "/data/callqa/clips"
  temp_directory: "/tmp/callqa"

api:
  host: "0.0.0.0"
  port: 8000
  workers: 4

cdr:
  api_url: "http://cisco-uccx:8080/api/v1"
  api_token: "${CDR_API_TOKEN}"
  sync_days_back: 7

processing:
  ffmpeg_path: "/usr/bin/ffmpeg"
  ffprobe_path: "/usr/bin/ffprobe"
  
  audio:
    sample_rate: 16000
    silence_threshold_db: -40
    min_call_duration: 3
    silence_duration: 2

worker:
  check_interval: 30
  max_concurrent: 3
  timeout_hours: 2

logging:
  level: "INFO"
  max_file_size_mb: 50
  retention_days: 30
```

---

## 6. Scripts Auxiliares

### `scripts/init_db.py`

```python
#!/usr/bin/env python3
"""
Script para inicializar la base de datos.
"""
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config.database import engine, Base
from config.settings import Settings
from loguru import logger

from models.operator import Operator
from models.transfer_session import TransferSession
from models.uploaded_file import UploadedFile
from models.call_segment import CallSegment
from models.phone_call import PhoneCall
from models.processed_clip import ProcessedClip
from models.call_mapping import CallMapping
from models.evaluation import Evaluation


def init_database():
    """Inicializa la base de datos."""
    logger.info("Inicializando base de datos...")
    
    try:
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        logger.success("✓ Base de datos inicializada exitosamente")
        
    except Exception as e:
        logger.error(f"Error inicializando BD: {e}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()
```

### `scripts/import_cdr.py`

```python
#!/usr/bin/env python3
"""
Script para importar registros CDR históricos.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, date

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config.database import SessionLocal
from config.settings import Settings
from loguru import logger

from services.cdr_sync import CDRSync


def import_cdr_history(days_back: int = 7):
    """
    Importa registros CDR históricos.
    
    Args:
        days_back: Cantidad de días atrás para importar
    """
    logger.info(f"Importando CDR histórico ({days_back} días)")
    
    try:
        settings = Settings()
        db = SessionLocal()
        cdr_sync = CDRSync(settings, db)
        
        total_imported = 0
        
        for days_ago in range(0, days_back):
            target_date = datetime.now().date() - timedelta(days=days_ago)
            
            imported = cdr_sync.sync_cdr_for_date(target_date)
            total_imported += imported
        
        logger.success(f"✓ Importados {total_imported} registros CDR")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error importando CDR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Importar CDR histórico")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Cantidad de días atrás para importar (default: 7)"
    )
    
    args = parser.parse_args()
    
    import_cdr_history(args.days)
```

---

## 7. Dockerfile y Docker Compose

### `docker/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY src /app/src
COPY config.yaml /app/
COPY scripts /app/scripts

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from config.database import SessionLocal; SessionLocal()" || exit 1

# Comando por defecto: ejecutar API
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `docker/docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: callqa-postgres
    environment:
      POSTGRES_USER: callqa
      POSTGRES_PASSWORD: ${DB_PASSWORD:-callqa123}
      POSTGRES_DB: callqa_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U callqa"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: callqa-api
    command: python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
    environment:
      DATABASE_URL: postgresql://callqa:${DB_PASSWORD:-callqa123}@postgres:5432/callqa_db
      CDR_API_TOKEN: ${CDR_API_TOKEN}
    volumes:
      - /data/callqa/uploads:/data/callqa/uploads
      - /data/callqa/clips:/data/callqa/clips
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy

  worker:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: callqa-worker
    command: python worker.py
    environment:
      DATABASE_URL: postgresql://callqa:${DB_PASSWORD:-callqa123}@postgres:5432/callqa_db
      CDR_API_TOKEN: ${CDR_API_TOKEN}
    volumes:
      - /data/callqa/uploads:/data/callqa/uploads
      - /data/callqa/clips:/data/callqa/clips
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## Flujo Completo de Procesamiento

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FLUJO DE PROCESAMIENTO                          │
└─────────────────────────────────────────────────────────────────────┘

1. RECEPCIÓN
   Cliente transfiere clip_30min.mkv
   → Archivo guardado: /uploads/OP001/2025-02-12/clip_30min.mkv
   → Registro creado: UploadedFile (state=RECEIVED)

2. MONITOREO
   FileWatcher escanea /uploads
   → Detecta nuevo archivo
   → Enqueue para procesamiento

3. EXTRACCIÓN DE AUDIO
   AudioExtractor
   → Extrae pista de audio: audio_temp.wav
   → 30 minutos de audio en 16kHz

4. DETECCIÓN DE LLAMADAS
   AudioAnalyzer.detect_call_segments()
   → Análisis de energía en ventanas
   → Detección de silencios (> 2 segundos)
   → Resultado: [(2.5, 245.3), (250.1, 480.5), ...]
   → Crear CallSegment para cada uno

5. SINCRONIZACIÓN CDR
   CDRSync.sync_cdr_for_date()
   → Consultar API telefónica
   → Importar registros: PhoneCall
   → operator_id: OP001, 2025-02-12

6. CORRELACIÓN
   CallCorrelator.correlate_segments_with_cdr()
   → Para cada CallSegment:
     - Calcular tiempo absoluto
     - Buscar PhoneCall cercano (±30 segundos)
     - Validar duración (±15%)
     - Calcular confidence score
   → Actualizar: segment.phone_call_id

7. GENERACIÓN DE CLIPS
   ClipGenerator.generate_clips_for_file()
   → Para cada CallSegment:
     - Extraer con FFmpeg
     - Ruta: /clips/OP001/2025-02-12/call_id/
     - Nombre: OP001_20250212_CALL123_120.mp4
     - Crear ProcessedClip record

8. COMPLETAR
   UploadedFile.state = COMPLETED
   → clips_generated: 15
   → calls_detected: 15
   → processing_completed_at: timestamp

SALIDA:
→ 15 clips listos para evaluación
→ Organizados por operador, fecha, llamada
→ Metadata completa disponible en BD
```

---

## Ejecución

### Iniciar Todo

```bash
# Inicializar BD
python scripts/init_db.py

# Importar CDR histórico
python scripts/import_cdr.py --days 7

# Iniciar servicios con Docker Compose
docker-compose -f docker/docker-compose.yml up -d

# Ver logs del worker
docker logs -f callqa-worker

# Ver logs de la API
docker logs -f callqa-api
```

### Monitoreo

```bash
# Conexión a BD
psql -h localhost -U callqa -d callqa_db

# Ver archivos en procesamiento
SELECT filename, state, calls_detected FROM uploaded_files ORDER BY uploaded_at DESC;

# Ver clips generados
SELECT filename, duration_seconds, status FROM processed_clips ORDER BY generated_at DESC;

# Ver llamadas correlacionadas
SELECT COUNT(*) FROM call_segments WHERE phone_call_id IS NOT NULL;
```

---

¿Necesitas que profundice en alguna parte específica del procesamiento o que agregue características adicionales como paralelización, compresión adaptativa o alertas?