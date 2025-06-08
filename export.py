"""
JSON serialization utilities for Spotify Playlist Enhancer.
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def export_analysis(
    features: Dict[str, dict],
    tempo_buckets: Optional[Dict[str, List[str]]] = None,
    energy_buckets: Optional[Dict[str, List[str]]] = None,
    filepath: Optional[str] = None
) -> str:
    """
    Export analysis results to a JSON file.
    
    Args:
        features: Map of track URI to audio features
        tempo_buckets: Optional map of tempo category to track URIs
        energy_buckets: Optional map of energy category to track URIs
        filepath: Optional custom filepath for export
        
    Returns:
        str: Path to the exported JSON file
    """
    if not filepath:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"analysis_{timestamp}.json"
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "track_count": len(features),
        "audio_features": features
    }
    
    if tempo_buckets:
        data["tempo_buckets"] = tempo_buckets
    
    if energy_buckets:
        data["energy_buckets"] = energy_buckets
    
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Analysis exported to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to export analysis: {e}")
        raise 