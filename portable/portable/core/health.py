"""
Health check module
Used for service monitoring and uptime validation
"""

def get_health_status():
    return {
        "status": "ok",
        "service": "Titan",
        "version": "0.1.0"
    }
