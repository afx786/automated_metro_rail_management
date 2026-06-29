# iot.py - Update the IoT functions
import random
from typing import Dict, List
import time

class IoTClient:
    """Singleton class to manage IoT connections and bulk requests"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize connection pool or session for bulk requests"""
        # For real IoT systems, you'd create a connection pool here
        self.batch_size = 50  # Process 50 trainsets per batch
        self.cache = {}
        self.cache_timeout = 30  # seconds
    
    def get_bulk_fitness_data(self, codes: List[str]) -> Dict[str, dict]:
        """Get fitness data for multiple trainsets in optimized batches"""
        results = {}
        
        # Process in batches to avoid overwhelming the IoT system
        for i in range(0, len(codes), self.batch_size):
            batch_codes = codes[i:i + self.batch_size]
            batch_results = self._process_batch(batch_codes)
            results.update(batch_results)
        
        return results
    
    def _process_batch(self, codes: List[str]) -> Dict[str, dict]:
        """Process a batch of trainsets (simulated or real API call)"""
        batch_results = {}
        
        # SIMULATED BULK API CALL - Replace with actual bulk IoT API
        # This would be a single HTTP request for all codes in real implementation
        for code in codes:
            # Check cache first
            cached_data = self.cache.get(code)
            if cached_data and (time.time() - cached_data['timestamp']) < self.cache_timeout:
                batch_results[code] = cached_data['data']
                continue
            
            # Generate/simulate fitness data
            fitness_data = {
                "brake_temp": round(random.uniform(30, 80), 1),
                "hvac_status": random.choice(["ok", "fault"]),
                "signal_comm_ok": random.choice([True, True, True, False]),
                "last_updated": time.time()
            }
            
            # Cache the result
            self.cache[code] = {
                'data': fitness_data,
                'timestamp': time.time()
            }
            
            batch_results[code] = fitness_data
        
        return batch_results

# Global singleton instance
iot_client = IoTClient()

def get_bulk_trainset_fitness(codes: List[str]) -> Dict[str, dict]:
    """Public function to get bulk fitness data"""
    return iot_client.get_bulk_fitness_data(codes)

def get_trainset_fitness(code: str) -> dict:
    """Backward compatibility - uses bulk internally"""
    result = iot_client.get_bulk_fitness_data([code])
    return result[code]