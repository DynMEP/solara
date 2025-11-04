# =============================================================================
# SOLARA Weather API (NSRDB)
# =============================================================================
# Purpose: NREL NSRDB TMY/PSM3 downloader with caching, geocoding, validation, and robust retry/backoff compliant with NREL ToS.
# Version: 3.1.1
# Author: Alfonso Davila - Electrical Engineer | Power Distribution Systems | Renewable Energy Systems | Dynamo BIM
# Repository: https://github.com/DynMEP/solara
# License: MIT License (see LICENSE in repository)
# Created: November 2025
# Last Updated: November 04, 2025
# Compatibility: Python 3.9+, requests, pandas, geopy
# Notes:
#   - Requires NREL_API_KEY and NREL_EMAIL (per ToS)
#   - Caches CSV files under ~/.solara/weather_cache
#   - Validates schema (GHI/DNI/DHI/Temperature/Wind Speed)
# Features:
#   - Exponential backoff & rate‑limit handling
#   - Geocode addresses to coords via Nominatim
#   - Batch downloads with polite delays
#   - Cache management & on‑disk validation
# Quick Start:
#   export NREL_API_KEY=...; export NREL_EMAIL=you@example.com
#   from solara_weather_api import NSRDBWeatherAPI
#   api = NSRDBWeatherAPI(); api.get_weather_data(39.74, -104.99, 'Denver_CO')
# =============================================================================

import os
import json
import hashlib
import requests
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

logger = logging.getLogger('SOLARA.Weather')

def load_environment_variables(env_file: str = '.env', verbose: bool = True) -> bool:
    """Load environment variables from .env file if available.
    
    Args:
        env_file: Path to .env file (default: '.env')
        verbose: Whether to print status messages
    
    Returns:
        True if .env file was loaded, False otherwise
    """
    env_path = Path(env_file)
    
    if not env_path.exists():
        if verbose:
            logger.info(f"No .env file found at {env_path}")
            logger.info("Environment variables will be loaded from system only")
        return False
    
    if not DOTENV_AVAILABLE:
        if verbose:
            logger.warning("python-dotenv not installed")
            logger.warning("Install with: pip install python-dotenv")
            logger.warning(f"Skipping .env file: {env_path}")
        return False
    
    # Load .env file
    try:
        load_dotenv(env_path, override=False)  
        if verbose:
            logger.info(f"✓ Loaded environment from: {env_path}")
        return True
    except Exception as e:
        if verbose:
            logger.warning(f"Could not load .env file: {e}")
        return False


load_environment_variables(verbose=False)


class NSRDBWeatherAPI:
    
    BASE_URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-tmy-download.csv"
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 email: Optional[str] = None,
                 cache_dir: Optional[Path] = None):
        self.api_key = api_key or os.environ.get('NREL_API_KEY')
        self.email = email or os.environ.get('NREL_EMAIL')
        
        # Validate API key
        if not self.api_key:
            raise ValueError(
                "❌ NREL API key required.\n"
                "   Get one at: https://developer.nrel.gov/signup/\n"
                "   Set via: export NREL_API_KEY='your_key'\n"
                "   Or pass to constructor: NSRDBWeatherAPI(api_key='your_key')"
            )
        
        if not self.email:
            raise ValueError(
                "❌ Email required for NREL API (per Terms of Service).\n"
                "   Set via: export NREL_EMAIL='your@email.com'\n"
                "   Or pass to constructor: NSRDBWeatherAPI(email='your@email.com')\n\n"
                "   Why required? NREL requires attribution and contact info\n"
                "   for API usage tracking and compliance."
            )
        
        # Basic email validation
        if '@' not in self.email or '.' not in self.email:
            raise ValueError(f"❌ Invalid email format: {self.email}")
        
        self.cache_dir = cache_dir or Path.home() / '.solara' / 'weather_cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize geocoder
        self.geocoder = Nominatim(user_agent="solara_v3")
        
        logger.info(f"✓ NSRDB API initialized for {self.email}")
        logger.info(f"✓ Cache directory: {self.cache_dir}")
    
    def _create_session_with_retries(self, max_retries: int = 3) -> requests.Session:
        session = requests.Session()
        
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=2,  # Exponential backoff: 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
            raise_on_status=False 
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def get_weather_data(
        self, 
        latitude: float, 
        longitude: float, 
        location_name: str,
        year: str = 'tmy',
        attributes: str = 'ghi,dni,dhi,wind_speed,air_temperature',
        interval: int = 60,
        use_cache: bool = True,
        max_retries: int = 3
    ) -> str:
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {latitude}")
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {longitude}")
        
        # Check cache first
        cache_file = self._get_cache_path(latitude, longitude, year)
        if use_cache and cache_file.exists():
            logger.info(f"✓ Using cached weather data: {cache_file.name}")
            return str(cache_file)
        
        # Download from NSRDB with retry logic
        logger.info(f"⏳ Downloading weather data for {location_name}...")
        logger.info(f"   Coordinates: {latitude:.4f}, {longitude:.4f}")
        logger.info(f"   Year: {year} | Interval: {interval} min")
        
        params = {
            'api_key': self.api_key,
            'wkt': f'POINT({longitude} {latitude})',
            'names': year,
            'attributes': attributes,
            'interval': interval,
            'email': self.email,  
            'mailing_list': 'false'
        }
        
        session = self._create_session_with_retries(max_retries)
        
        attempt = 0
        last_error = None
        
        while attempt < max_retries:
            try:
                attempt += 1
                if attempt > 1:
                    logger.info(f"   Retry attempt {attempt}/{max_retries}...")
                
                response = session.get(
                    self.BASE_URL, 
                    params=params, 
                    timeout=60 
                )
                
                # Check for API errors
                if response.status_code == 429:
                    logger.warning("⚠ Rate limit hit, waiting before retry...")
                    time.sleep(5 * attempt)  
                    continue
                
                if response.status_code == 403:
                    raise ValueError(
                        "❌ API key invalid or expired.\n"
                        "   Get a new key at: https://developer.nrel.gov/signup/"
                    )
                
                response.raise_for_status()
                
                if response.text.startswith('{'):
                    error_data = json.loads(response.text)
                    raise ValueError(f"API Error: {error_data.get('error', 'Unknown error')}")
                
                # Save to cache
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                with open(cache_file, 'w') as f:
                    f.write(response.text)
                
                # Validate downloaded data
                self._validate_weather_file(cache_file)
                
                logger.info(f"✓ Weather data downloaded: {cache_file.name}")
                return str(cache_file)
                
            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(f"⚠ Request timeout (attempt {attempt}/{max_retries})")
                if attempt < max_retries:
                    time.sleep(2 * attempt)
                    
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"⚠ Request failed: {e} (attempt {attempt}/{max_retries})")
                if attempt < max_retries:
                    time.sleep(2 * attempt)
        
        logger.error(f"❌ Failed to download after {max_retries} attempts")
        logger.error("   Please check:")
        logger.error("   1. Internet connection is stable")
        logger.error("   2. NREL API key is valid: https://developer.nrel.gov/signup/")
        logger.error(f"   3. Email is correct: {self.email}")
        logger.error(f"   4. Coordinates are valid: {latitude}, {longitude}")
        logger.error(f"   5. NREL service status: https://developer.nrel.gov/")
        
        raise RuntimeError(f"Weather download failed after {max_retries} retries") from last_error
    
    def geocode_address(self, address: str, timeout: int = 10) -> Tuple[float, float, str]:
        try:
            logger.info(f"⏳ Geocoding: {address}")
            location = self.geocoder.geocode(address, timeout=timeout)
            
            if location:
                logger.info(f"✓ Found: {location.address}")
                logger.info(f"  Coordinates: {location.latitude:.4f}, {location.longitude:.4f}")
                return location.latitude, location.longitude, location.address
            else:
                raise ValueError(
                    f"❌ Could not geocode address: '{address}'\n"
                    "   Try a more specific address or provide coordinates directly."
                )
                
        except GeocoderTimedOut:
            logger.error(f"❌ Geocoding service timed out after {timeout}s")
            raise ValueError(
                "Geocoding service timeout. Try again or use coordinates directly."
            )
        except Exception as e:
            logger.error(f"❌ Geocoding failed: {e}")
            raise
    
    def batch_download(self, 
                      locations: Dict[str, Tuple[float, float]],
                      delay_between: float = 1.0) -> Dict[str, str]:
        results = {}
        total = len(locations)
        
        logger.info(f"⏳ Batch downloading weather data for {total} locations...")
        
        for i, (name, (lat, lon)) in enumerate(locations.items(), 1):
            logger.info(f"[{i}/{total}] Processing {name}...")
            
            try:
                weather_file = self.get_weather_data(lat, lon, name)
                results[name] = weather_file
                
                # Delay between requests to respect rate limits
                if i < total:
                    time.sleep(delay_between)
                    
            except Exception as e:
                logger.error(f"❌ Failed to download {name}: {e}")
                results[name] = None
        
        success_count = sum(1 for v in results.values() if v is not None)
        logger.info(f"✓ Batch complete: {success_count}/{total} successful")
        
        return results
    
    def _get_cache_path(self, latitude: float, longitude: float, year: str) -> Path:
        # Create hash from coordinates for unique filename
        location_str = f"{latitude:.4f}_{longitude:.4f}_{year}"
        location_hash = hashlib.md5(location_str.encode()).hexdigest()[:8]
        
        filename = f"nsrdb_{location_hash}_{year}.csv"
        return self.cache_dir / filename
    
    def _validate_weather_file(self, file_path: Path) -> bool:
        if not file_path.exists():
            raise FileNotFoundError(f"Weather file not found: {file_path}")
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size < 1000: 
            raise ValueError(f"Weather file is too small ({file_size} bytes) - likely an error")
        
        # Read weather data
        try:
            df = pd.read_csv(file_path, skiprows=2) 
        except Exception as e:
            raise ValueError(f"Could not read weather file: {e}")
        
        # Check required columns (NSRDB format)
        required_cols = ['GHI', 'DNI', 'DHI', 'Temperature', 'Wind Speed']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}\nAvailable: {list(df.columns)}")
        
        # Check data length (should be 8760 for TMY)
        expected_length = 8760
        actual_length = len(df)
        
        if actual_length != expected_length:
            logger.warning(
                f"⚠ Expected {expected_length} records (typical year), "
                f"found {actual_length}"
            )
        
        # Check for excessive missing data
        for col in required_cols:
            missing_count = df[col].isna().sum()
            missing_pct = (missing_count / len(df)) * 100
            
            if missing_pct > 10:  # More than 10% missing
                logger.warning(
                    f"⚠ Column '{col}' has {missing_pct:.1f}% missing values "
                    f"({missing_count}/{len(df)} records)"
                )
            elif missing_count > 0:
                logger.info(f"  Note: '{col}' has {missing_count} missing values")
        
        logger.info(f"✓ Weather file validated: {actual_length} records")
        return True
    
    def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        import time
        
        count = 0
        cutoff_time = None
        
        if older_than_days:
            cutoff_time = time.time() - (older_than_days * 86400)
        
        for file in self.cache_dir.glob('*.csv'):
            if cutoff_time is None or file.stat().st_mtime < cutoff_time:
                try:
                    file.unlink()
                    count += 1
                except Exception as e:
                    logger.warning(f"Could not delete {file.name}: {e}")
        
        logger.info(f"✓ Cleared {count} cached weather file(s)")
        return count


# ============================================================================
# Quick validation test
# ============================================================================

def test_api_setup():
    try:
        api = NSRDBWeatherAPI()
        print(f"✓ API initialized successfully")
        print(f"  Email: {api.email}")
        print(f"  Cache: {api.cache_dir}")
        return True
    except ValueError as e:
        print(f"❌ API setup error:\n{e}")
        return False


if __name__ == "__main__":
    print("SOLARA Weather API - Configuration Test")
    print("=" * 60)
    test_api_setup()