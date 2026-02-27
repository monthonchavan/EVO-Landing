"""
Hardware Data Import Module for LandingOS
Supports importing event camera data from various hardware formats.
"""

import os
import struct
import csv
import json
import numpy as np
from typing import List, Dict, Tuple, Optional, BinaryIO
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

@dataclass
class ImportedEvent:
    """Represents a single event from hardware"""
    x: int
    y: int
    timestamp: float  # microseconds
    polarity: int  # 1 or -1

@dataclass 
class HardwareDataset:
    """Container for imported hardware data"""
    id: str
    name: str
    format: str
    resolution: Tuple[int, int]
    events: List[Dict]
    metadata: Dict
    imported_at: datetime
    total_events: int
    duration_us: float

class EventFileParser:
    """Parser for various event camera file formats"""
    
    SUPPORTED_FORMATS = {
        'csv': 'CSV (x, y, timestamp, polarity)',
        'json': 'JSON event array',
        'aedat4': 'AEDAT 4.0 (Prophesee/iniVation)',
        'raw': 'Raw binary (Prophesee EVK)',
        'txt': 'Text file (space/tab separated)',
        'npy': 'NumPy array'
    }
    
    def __init__(self):
        self.events = []
        self.metadata = {}
    
    def parse_file(self, file_content: bytes, filename: str, format_hint: str = None) -> HardwareDataset:
        """Parse event file and return dataset"""
        import uuid
        
        # Determine format
        if format_hint:
            file_format = format_hint
        else:
            ext = os.path.splitext(filename)[1].lower().lstrip('.')
            file_format = ext if ext in self.SUPPORTED_FORMATS else 'csv'
        
        # Parse based on format
        if file_format == 'csv':
            events, metadata = self._parse_csv(file_content)
        elif file_format == 'json':
            events, metadata = self._parse_json(file_content)
        elif file_format == 'txt':
            events, metadata = self._parse_txt(file_content)
        elif file_format == 'npy':
            events, metadata = self._parse_npy(file_content)
        elif file_format == 'aedat4':
            events, metadata = self._parse_aedat4(file_content)
        elif file_format == 'raw':
            events, metadata = self._parse_raw_prophesee(file_content)
        else:
            raise ValueError(f"Unsupported format: {file_format}")
        
        # Calculate statistics
        if events:
            timestamps = [e['timestamp'] for e in events]
            duration = max(timestamps) - min(timestamps)
            
            # Determine resolution from data
            max_x = max(e['x'] for e in events)
            max_y = max(e['y'] for e in events)
            resolution = (max_x + 1, max_y + 1)
        else:
            duration = 0
            resolution = (640, 480)
        
        return HardwareDataset(
            id=str(uuid.uuid4())[:8],
            name=filename,
            format=file_format,
            resolution=resolution,
            events=events,
            metadata=metadata,
            imported_at=datetime.now(timezone.utc),
            total_events=len(events),
            duration_us=duration
        )
    
    def _parse_csv(self, content: bytes) -> Tuple[List[Dict], Dict]:
        """Parse CSV format: x,y,timestamp,polarity"""
        events = []
        metadata = {'format': 'csv'}
        
        try:
            text = content.decode('utf-8')
            lines = text.strip().split('\n')
            
            # Check for header
            first_line = lines[0].lower()
            start_idx = 1 if any(h in first_line for h in ['x', 'timestamp', 'polarity']) else 0
            
            for line in lines[start_idx:]:
                if not line.strip():
                    continue
                    
                # Try comma, then tab, then space
                for delimiter in [',', '\t', ' ']:
                    parts = [p.strip() for p in line.split(delimiter) if p.strip()]
                    if len(parts) >= 4:
                        break
                
                if len(parts) >= 4:
                    events.append({
                        'x': int(float(parts[0])),
                        'y': int(float(parts[1])),
                        'timestamp': float(parts[2]),
                        'polarity': 1 if float(parts[3]) > 0 else -1
                    })
        except Exception as e:
            logger.error(f"CSV parse error: {e}")
            raise ValueError(f"Failed to parse CSV: {e}")
        
        metadata['parsed_events'] = len(events)
        return events, metadata
    
    def _parse_txt(self, content: bytes) -> Tuple[List[Dict], Dict]:
        """Parse text format (space/tab separated)"""
        return self._parse_csv(content)  # Same logic works
    
    def _parse_json(self, content: bytes) -> Tuple[List[Dict], Dict]:
        """Parse JSON format"""
        events = []
        metadata = {'format': 'json'}
        
        try:
            data = json.loads(content.decode('utf-8'))
            
            # Handle different JSON structures
            if isinstance(data, list):
                event_list = data
            elif isinstance(data, dict):
                if 'events' in data:
                    event_list = data['events']
                    metadata.update({k: v for k, v in data.items() if k != 'events'})
                else:
                    event_list = [data]
            else:
                raise ValueError("Invalid JSON structure")
            
            for e in event_list:
                events.append({
                    'x': int(e.get('x', e.get('X', 0))),
                    'y': int(e.get('y', e.get('Y', 0))),
                    'timestamp': float(e.get('timestamp', e.get('t', e.get('ts', 0)))),
                    'polarity': 1 if e.get('polarity', e.get('p', e.get('pol', 1))) > 0 else -1
                })
        except Exception as e:
            logger.error(f"JSON parse error: {e}")
            raise ValueError(f"Failed to parse JSON: {e}")
        
        return events, metadata
    
    def _parse_npy(self, content: bytes) -> Tuple[List[Dict], Dict]:
        """Parse NumPy array format"""
        events = []
        metadata = {'format': 'npy'}
        
        try:
            arr = np.load(BytesIO(content), allow_pickle=True)
            
            # Handle structured array or regular array
            if arr.dtype.names:
                # Structured array
                for i in range(len(arr)):
                    events.append({
                        'x': int(arr['x'][i]) if 'x' in arr.dtype.names else int(arr[i][0]),
                        'y': int(arr['y'][i]) if 'y' in arr.dtype.names else int(arr[i][1]),
                        'timestamp': float(arr['t'][i]) if 't' in arr.dtype.names else float(arr[i][2]),
                        'polarity': int(arr['p'][i]) if 'p' in arr.dtype.names else int(arr[i][3])
                    })
            else:
                # Regular array: assume columns are [x, y, t, p]
                for row in arr:
                    events.append({
                        'x': int(row[0]),
                        'y': int(row[1]),
                        'timestamp': float(row[2]),
                        'polarity': 1 if row[3] > 0 else -1
                    })
        except Exception as e:
            logger.error(f"NumPy parse error: {e}")
            raise ValueError(f"Failed to parse NumPy: {e}")
        
        return events, metadata
    
    def _parse_aedat4(self, content: bytes) -> Tuple[List[Dict], Dict]:
        """Parse AEDAT 4.0 format (simplified)"""
        events = []
        metadata = {'format': 'aedat4'}
        
        try:
            # AEDAT 4 uses flatbuffers - simplified parsing
            # For full support, would need aedat library
            # This handles basic event structure
            
            stream = BytesIO(content)
            
            # Skip header (variable length, ends with #!END-HEADER)
            header = b''
            while True:
                byte = stream.read(1)
                if not byte:
                    break
                header += byte
                if header.endswith(b'#!END-HEADER\r\n') or header.endswith(b'#!END-HEADER\n'):
                    break
            
            metadata['header'] = header.decode('utf-8', errors='ignore')
            
            # Read events (simplified - assumes CD events)
            # Real AEDAT4 requires flatbuffers parsing
            remaining = stream.read()
            
            # Try to parse as packed events (x:16, y:16, p:8, t:64)
            event_size = 12  # Approximate
            num_events = min(len(remaining) // event_size, 100000)  # Limit
            
            for i in range(num_events):
                try:
                    offset = i * event_size
                    x = struct.unpack('<H', remaining[offset:offset+2])[0] & 0x7FF
                    y = struct.unpack('<H', remaining[offset+2:offset+4])[0] & 0x7FF
                    p = remaining[offset+4] & 1
                    t = struct.unpack('<Q', remaining[offset+4:offset+12])[0] >> 8
                    
                    if x < 2000 and y < 2000:  # Sanity check
                        events.append({
                            'x': x,
                            'y': y,
                            'timestamp': float(t),
                            'polarity': 1 if p else -1
                        })
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"AEDAT4 parse warning: {e}")
            metadata['parse_warning'] = str(e)
        
        return events, metadata
    
    def _parse_raw_prophesee(self, content: bytes) -> Tuple[List[Dict], Dict]:
        """Parse Prophesee RAW format"""
        events = []
        metadata = {'format': 'raw_prophesee'}
        
        try:
            # Prophesee EVK raw format
            # Each event is typically 8 bytes: timestamp(32) + data(32)
            stream = BytesIO(content)
            
            # Skip header if present
            first_bytes = stream.read(4)
            if first_bytes == b'%RAW':
                # Skip to end of header line
                while stream.read(1) != b'\n':
                    pass
            else:
                stream.seek(0)
            
            # Read events
            event_size = 8
            remaining = stream.read()
            num_events = min(len(remaining) // event_size, 100000)
            
            for i in range(num_events):
                offset = i * event_size
                data = struct.unpack('<II', remaining[offset:offset+8])
                
                timestamp = data[0]
                event_data = data[1]
                
                x = (event_data >> 12) & 0x7FF
                y = (event_data >> 1) & 0x7FF
                p = event_data & 1
                
                if x < 2000 and y < 2000:
                    events.append({
                        'x': x,
                        'y': y,
                        'timestamp': float(timestamp),
                        'polarity': 1 if p else -1
                    })
                    
        except Exception as e:
            logger.warning(f"RAW parse warning: {e}")
            metadata['parse_warning'] = str(e)
        
        return events, metadata


class DataExporter:
    """Export simulation and experiment data"""
    
    @staticmethod
    def export_events_csv(events: List[Dict]) -> str:
        """Export events to CSV format"""
        output = "x,y,timestamp,polarity\n"
        for e in events:
            output += f"{e['x']},{e['y']},{e['timestamp']},{e['polarity']}\n"
        return output
    
    @staticmethod
    def export_events_json(events: List[Dict], metadata: Dict = None) -> str:
        """Export events to JSON format"""
        data = {
            'metadata': metadata or {},
            'total_events': len(events),
            'events': events
        }
        return json.dumps(data, indent=2)
    
    @staticmethod
    def export_trajectory_csv(poses: List[Dict]) -> str:
        """Export trajectory to CSV"""
        output = "time,x,y,z,roll,pitch,yaw\n"
        for p in poses:
            output += f"{p.get('time',0)},{p.get('x',0)},{p.get('y',0)},{p.get('z',0)},"
            output += f"{p.get('roll',0)},{p.get('pitch',0)},{p.get('yaw',0)}\n"
        return output
    
    @staticmethod
    def export_metrics_csv(metrics: List[Dict]) -> str:
        """Export metrics history to CSV"""
        if not metrics:
            return "time,position_error,attitude_error,drift_rate,latency_ms\n"
        
        output = "time,position_error,attitude_error,drift_rate,latency_ms\n"
        for m in metrics:
            output += f"{m.get('time',0)},{m.get('position_error',0)},"
            output += f"{m.get('attitude_error',0)},{m.get('drift_rate',0)},{m.get('latency_ms',0)}\n"
        return output
    
    @staticmethod
    def export_full_experiment(experiment: Dict) -> str:
        """Export complete experiment data to JSON"""
        return json.dumps(experiment, indent=2, default=str)


# Global parser instance
event_parser = EventFileParser()
data_exporter = DataExporter()
