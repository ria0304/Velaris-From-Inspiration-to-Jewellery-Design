# backend/sketch_processor.py

"""
Sketch preprocessing pipeline for Velaris.
Handles: image enhancement, edge detection, feature extraction,
shape recognition, and preparation for SVG generation.
"""

import base64
import io
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

import numpy as np
from fastapi import HTTPException

# Try to import OpenCV - graceful fallback if not available
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not installed. Sketch processing will be limited.")

# Try to import PIL for image handling
try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not installed. Sketch processing will be limited.")


@dataclass
class ProcessedSketch:
    """Result of sketch preprocessing."""
    edges: np.ndarray  # Edge detection result
    contours: List[np.ndarray]  # Detected contours
    features: Dict[str, Any]  # Extracted features
    shapes: List[Dict[str, Any]]  # Recognized shapes
    enhanced_image: np.ndarray  # Enhanced image
    bounding_boxes: List[Tuple[int, int, int, int]]  # Bounding boxes


class SketchProcessor:
    """Handles sketch preprocessing and feature extraction."""
    
    def __init__(self):
        self.edge_low_threshold = 50
        self.edge_high_threshold = 150
        self.contour_approximation = 0.02
        
    def preprocess(self, image_data: str) -> ProcessedSketch:
        """
        Full preprocessing pipeline for a sketch.
        
        Args:
            image_data: Base64 encoded image data (data:image/...;base64,...)
            
        Returns:
            ProcessedSketch with all extracted information
        """
        if not CV2_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="OpenCV not available. Please install: pip install opencv-python"
            )
        
        # Decode image
        image = self._decode_image(image_data)
        
        # 1. Image Enhancement
        enhanced = self._enhance_image(image)
        
        # 2. Edge Detection
        edges = self._detect_edges(enhanced)
        
        # 3. Contour Detection
        contours = self._find_contours(edges)
        
        # 4. Feature Extraction
        features = self._extract_features(enhanced, contours)
        
        # 5. Shape Recognition
        shapes = self._recognize_shapes(contours)
        
        # 6. Bounding Boxes
        boxes = self._get_bounding_boxes(contours)
        
        return ProcessedSketch(
            edges=edges,
            contours=contours,
            features=features,
            shapes=shapes,
            enhanced_image=enhanced,
            bounding_boxes=boxes
        )
    
    def _decode_image(self, image_data: str) -> np.ndarray:
        """Decode base64 image to OpenCV format."""
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # Decode base64
        img_bytes = base64.b64decode(image_data)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Failed to decode image")
        
        return img
    
    def _enhance_image(self, image: np.ndarray) -> np.ndarray:
        """Apply image enhancement techniques."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Adaptive histogram equalization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blurred)
        
        # Enhance contrast
        enhanced = cv2.normalize(enhanced, None, 0, 255, cv2.NORM_MINMAX)
        
        return enhanced
    
    def _detect_edges(self, image: np.ndarray) -> np.ndarray:
        """Detect edges using Canny edge detection."""
        # Use automatic threshold if not specified
        if self.edge_low_threshold is None:
            median = np.median(image)
            self.edge_low_threshold = int(max(0, 0.66 * median))
            self.edge_high_threshold = int(min(255, 1.33 * median))
        
        edges = cv2.Canny(
            image,
            self.edge_low_threshold,
            self.edge_high_threshold,
            apertureSize=3
        )
        
        return edges
    
    def _find_contours(self, edges: np.ndarray) -> List[np.ndarray]:
        """Find and filter contours."""
        contours, hierarchy = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter out small contours
        min_area = 100
        filtered = [c for c in contours if cv2.contourArea(c) > min_area]
        
        return filtered
    
    def _extract_features(self, image: np.ndarray, contours: List[np.ndarray]) -> Dict[str, Any]:
        """Extract features from the sketch."""
        features = {
            'num_contours': len(contours),
            'total_area': sum(cv2.contourArea(c) for c in contours),
            'average_area': 0,
            'complexity': 0,
            'dominant_shapes': [],
            'symmetry_score': 0,
            'stroke_confidence': 0,
        }
        
        if contours:
            areas = [cv2.contourArea(c) for c in contours]
            features['average_area'] = np.mean(areas)
            
            # Calculate complexity based on contour perimeter
            perimeters = [cv2.arcLength(c, True) for c in contours]
            features['complexity'] = np.mean(perimeters) / 100
            
            # Detect dominant shapes
            features['dominant_shapes'] = self._detect_dominant_shapes(contours)
            
            # Calculate symmetry
            features['symmetry_score'] = self._calculate_symmetry(contours)
            
        return features
    
    def _recognize_shapes(self, contours: List[np.ndarray]) -> List[Dict[str, Any]]:
        """Recognize shapes from contours."""
        shapes = []
        
        for contour in contours:
            shape_info = self._classify_shape(contour)
            if shape_info:
                shapes.append(shape_info)
        
        return shapes
    
    def _classify_shape(self, contour: np.ndarray) -> Optional[Dict[str, Any]]:
        """Classify a single contour as a shape."""
        # Approximate contour
        epsilon = self.contour_approximation * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Get shape properties
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if area < 100:
            return None
        
        # Calculate circularity
        if perimeter > 0:
            circularity = 4 * np.pi * area / (perimeter * perimeter)
        else:
            circularity = 0
        
        # Classify based on number of vertices
        vertices = len(approx)
        
        shape_type = "unknown"
        confidence = 0.5
        
        if vertices == 3:
            shape_type = "triangle"
            confidence = 0.8
        elif vertices == 4:
            # Check if rectangle or square
            rect = cv2.minAreaRect(contour)
            width, height = rect[1]
            if width > 0 and height > 0:
                aspect_ratio = max(width, height) / min(width, height)
                if aspect_ratio < 1.1:
                    shape_type = "square"
                    confidence = 0.9
                else:
                    shape_type = "rectangle"
                    confidence = 0.8
        elif vertices > 6 and circularity > 0.8:
            shape_type = "circle"
            confidence = 0.9
        elif vertices > 6:
            shape_type = "polygon"
            confidence = 0.6
        elif circularity > 0.7:
            shape_type = "oval"
            confidence = 0.7
        else:
            shape_type = "irregular"
            confidence = 0.4
        
        return {
            'type': shape_type,
            'confidence': confidence,
            'vertices': vertices,
            'area': area,
            'perimeter': perimeter,
            'circularity': circularity,
            'contour': contour.tolist() if isinstance(contour, np.ndarray) else contour
        }
    
    def _detect_dominant_shapes(self, contours: List[np.ndarray]) -> List[str]:
        """Detect dominant shapes in the sketch."""
        shape_counts = {}
        
        for contour in contours:
            shape_info = self._classify_shape(contour)
            if shape_info and shape_info['confidence'] > 0.6:
                shape_type = shape_info['type']
                shape_counts[shape_type] = shape_counts.get(shape_type, 0) + 1
        
        # Sort by count
        sorted_shapes = sorted(shape_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [s[0] for s in sorted_shapes[:3]]
    
    def _calculate_symmetry(self, contours: List[np.ndarray]) -> float:
        """Calculate symmetry score for the sketch."""
        if len(contours) < 2:
            return 0.0
        
        # Simple symmetry: compare areas of matching contours
        areas = sorted([cv2.contourArea(c) for c in contours], reverse=True)
        
        if len(areas) >= 2:
            # Compare largest two contours
            ratio = min(areas[0], areas[1]) / max(areas[0], areas[1])
            return ratio * 100
        
        return 0.0
    
    def _get_bounding_boxes(self, contours: List[np.ndarray]) -> List[Tuple[int, int, int, int]]:
        """Get bounding boxes for all contours."""
        boxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            boxes.append((x, y, w, h))
        return boxes


# ─── FastAPI Endpoint ──────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class SketchProcessRequest(BaseModel):
    image_data: str  # Base64 encoded image
    extract_features: bool = True
    detect_shapes: bool = True


class SketchProcessResponse(BaseModel):
    success: bool
    shapes: List[Dict[str, Any]]
    features: Dict[str, Any]
    edge_image: Optional[str] = None  # Base64 encoded edge detection result
    message: str


@router.post("/api/sketch-process", response_model=SketchProcessResponse)
def process_sketch(request: SketchProcessRequest) -> SketchProcessResponse:
    """Process a hand-drawn sketch for feature extraction and shape recognition."""
    
    if not CV2_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="OpenCV not available. Please install: pip install opencv-python"
        )
    
    try:
        processor = SketchProcessor()
        result = processor.preprocess(request.image_data)
        
        # Convert edge image to base64 for display
        edge_image_base64 = None
        if result.edges is not None:
            _, buffer = cv2.imencode('.png', result.edges)
            edge_image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return SketchProcessResponse(
            success=True,
            shapes=result.shapes,
            features=result.features,
            edge_image=edge_image_base64,
            message=f"Processed {len(result.contours)} contours, found {len(result.shapes)} shapes"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sketch processing failed: {str(e)}")
