"""
Health Check and Metrics Endpoint
=================================

Provides health status, performance metrics, and SLO monitoring
for production WhisperForge deployment.
"""

import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

import logging


@dataclass
class HealthStatus:
    """Health check status"""
    status: str  # healthy, degraded, unhealthy
    timestamp: str
    checks: Dict[str, Any]
    version: str = "2.0"
    uptime_seconds: float = 0


@dataclass
class SLOMetrics:
    """SLO metrics for monitoring"""
    error_rate_5xx: float
    median_response_time: float
    p95_response_time: float
    pipeline_success_rate: float
    avg_pipeline_duration: float
    active_users_1h: int
    total_requests_1h: int


class HealthChecker:
    """Health check and metrics provider"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        self.metrics_cache = {}
        self.cache_ttl = 60  # Cache for 60 seconds
    
    def get_health_status(self) -> HealthStatus:
        """Get comprehensive health status"""
        checks = {}
        overall_status = "healthy"
        
        # Database connectivity check
        db_status = self._check_database()
        checks["database"] = db_status
        if db_status["status"] != "healthy":
            overall_status = "degraded"
        
        # Environment variables check
        env_status = self._check_environment()
        checks["environment"] = env_status
        if env_status["status"] != "healthy":
            overall_status = "unhealthy"
        
        # AI providers check
        ai_status = self._check_ai_providers()
        checks["ai_providers"] = ai_status
        
        # File system check
        fs_status = self._check_filesystem()
        checks["filesystem"] = fs_status
        if fs_status["status"] != "healthy":
            overall_status = "degraded"
        
        # Memory and performance check
        perf_status = self._check_performance()
        checks["performance"] = perf_status
        
        return HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            checks=checks,
            uptime_seconds=time.time() - self.start_time
        )
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            from .supabase_integration import get_supabase_client
            
            client = get_supabase_client()
            if not client:
                return {
                    "status": "unhealthy",
                    "message": "Supabase client not initialized",
                    "response_time_ms": 0
                }
            
            # Test connection with a simple query
            start_time = time.time()
            try:
                # Try to query users table (should exist)
                result = client.table('users').select('id').limit(1).execute()
                response_time = (time.time() - start_time) * 1000
                
                return {
                    "status": "healthy",
                    "message": "Database connection successful",
                    "response_time_ms": round(response_time, 2),
                    "tables_accessible": True
                }
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                return {
                    "status": "degraded",
                    "message": f"Database query failed: {str(e)}",
                    "response_time_ms": round(response_time, 2),
                    "tables_accessible": False
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Database check failed: {str(e)}",
                "response_time_ms": 0
            }
    
    def _check_environment(self) -> Dict[str, Any]:
        """Check required environment variables"""
        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY",
            "JWT_SECRET"
        ]
        
        missing_vars = []
        configured_vars = []
        
        for var in required_vars:
            if os.getenv(var):
                configured_vars.append(var)
            else:
                missing_vars.append(var)
        
        # Check optional AI provider keys
        ai_providers = {}
        for provider, key in [
            ("openai", "OPENAI_API_KEY"),
            ("anthropic", "ANTHROPIC_API_KEY"),
            ("grok", "GROK_API_KEY")
        ]:
            ai_providers[provider] = bool(os.getenv(key))
        
        if missing_vars:
            return {
                "status": "unhealthy",
                "message": f"Missing required environment variables: {', '.join(missing_vars)}",
                "missing_vars": missing_vars,
                "configured_vars": configured_vars,
                "ai_providers": ai_providers
            }
        
        return {
            "status": "healthy",
            "message": "All required environment variables configured",
            "configured_vars": configured_vars,
            "ai_providers": ai_providers
        }
    
    def _check_ai_providers(self) -> Dict[str, Any]:
        """Check AI provider availability"""
        providers = {}
        
        # Check OpenAI
        if os.getenv("OPENAI_API_KEY"):
            try:
                import openai
                providers["openai"] = {
                    "configured": True,
                    "status": "available"
                }
            except ImportError:
                providers["openai"] = {
                    "configured": True,
                    "status": "library_missing"
                }
        else:
            providers["openai"] = {"configured": False}
        
        # Check Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                import anthropic
                providers["anthropic"] = {
                    "configured": True,
                    "status": "available"
                }
            except ImportError:
                providers["anthropic"] = {
                    "configured": True,
                    "status": "library_missing"
                }
        else:
            providers["anthropic"] = {"configured": False}
        
        # Check Grok
        if os.getenv("GROK_API_KEY"):
            providers["grok"] = {
                "configured": True,
                "status": "available"
            }
        else:
            providers["grok"] = {"configured": False}
        
        configured_count = sum(1 for p in providers.values() if p["configured"])
        
        return {
            "status": "healthy" if configured_count > 0 else "degraded",
            "message": f"{configured_count} AI providers configured",
            "providers": providers
        }
    
    def _check_filesystem(self) -> Dict[str, Any]:
        """Check filesystem access and disk space"""
        try:
            # Check logs directory
            logs_dir = Path("logs")
            logs_writable = False
            
            try:
                logs_dir.mkdir(exist_ok=True)
                test_file = logs_dir / "health_check_test.tmp"
                test_file.write_text("test")
                test_file.unlink()
                logs_writable = True
            except Exception:
                pass
            
            # Check session storage directory
            session_dir = Path.home() / ".whisperforge_sessions"
            session_writable = False
            
            try:
                session_dir.mkdir(exist_ok=True)
                test_file = session_dir / "health_check_test.tmp"
                test_file.write_text("test")
                test_file.unlink()
                session_writable = True
            except Exception:
                pass
            
            # Get disk usage (simplified)
            import shutil
            total, used, free = shutil.disk_usage(".")
            free_gb = free // (1024**3)
            
            status = "healthy"
            issues = []
            
            if not logs_writable:
                issues.append("logs directory not writable")
                status = "degraded"
            
            if not session_writable:
                issues.append("session directory not writable")
                status = "degraded"
            
            if free_gb < 1:  # Less than 1GB free
                issues.append("low disk space")
                status = "degraded"
            
            return {
                "status": status,
                "message": "Filesystem checks passed" if not issues else f"Issues: {', '.join(issues)}",
                "logs_writable": logs_writable,
                "session_writable": session_writable,
                "free_space_gb": free_gb,
                "issues": issues
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Filesystem check failed: {str(e)}"
            }
    
    def _check_performance(self) -> Dict[str, Any]:
        """Check current performance metrics"""
        try:
            import psutil
            
            # Get CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            status = "healthy"
            issues = []
            
            if cpu_percent > 80:
                issues.append("high CPU usage")
                status = "degraded"
            
            if memory.percent > 85:
                issues.append("high memory usage")
                status = "degraded"
            
            return {
                "status": status,
                "message": "Performance within normal range" if not issues else f"Issues: {', '.join(issues)}",
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "issues": issues
            }
            
        except ImportError:
            return {
                "status": "healthy",
                "message": "Performance monitoring not available (psutil not installed)",
                "cpu_percent": None,
                "memory_percent": None
            }
        except Exception as e:
            return {
                "status": "degraded",
                "message": f"Performance check failed: {str(e)}"
            }
    
    def get_slo_metrics(self, hours: int = 1) -> SLOMetrics:
        """Get SLO metrics for the specified time period"""
        cache_key = f"slo_metrics_{hours}h"
        
        # Check cache
        if cache_key in self.metrics_cache:
            cached_time, cached_data = self.metrics_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return cached_data
        
        # Calculate metrics from logs
        metrics = self._calculate_slo_metrics(hours)
        
        # Cache results
        self.metrics_cache[cache_key] = (time.time(), metrics)
        
        return metrics
    
    def _calculate_slo_metrics(self, hours: int) -> SLOMetrics:
        """Calculate SLO metrics from structured logs"""
        try:
            # Read recent log files
            logs_dir = Path("logs")
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            total_requests = 0
            error_5xx_count = 0
            response_times = []
            pipeline_durations = []
            pipeline_successes = 0
            pipeline_failures = 0
            unique_users = set()
            
            # Process log files
            for log_file in logs_dir.glob("whisperforge_structured_*.jsonl"):
                try:
                    with open(log_file, 'r') as f:
                        for line in f:
                            try:
                                log_entry = json.loads(line.strip())
                                log_time = datetime.fromisoformat(log_entry.get('timestamp', ''))
                                
                                if log_time < cutoff_time:
                                    continue
                                
                                # Count requests and errors
                                if log_entry.get('event_type') == 'performance':
                                    metric_name = log_entry.get('metric_name', '')
                                    if 'response_time' in metric_name or 'duration' in metric_name:
                                        total_requests += 1
                                        response_time = log_entry.get('metric_value', 0)
                                        response_times.append(response_time)
                                        
                                        # Check for 5xx errors (simplified)
                                        if not log_entry.get('success', True):
                                            error_5xx_count += 1
                                
                                # Track pipeline metrics
                                if log_entry.get('pipeline_status') == 'completed':
                                    duration = log_entry.get('duration_seconds', 0)
                                    pipeline_durations.append(duration)
                                    if log_entry.get('success', True):
                                        pipeline_successes += 1
                                    else:
                                        pipeline_failures += 1
                                
                                # Track unique users
                                user_id = log_entry.get('user_id')
                                if user_id:
                                    unique_users.add(user_id)
                                    
                            except (json.JSONDecodeError, ValueError, KeyError):
                                continue
                                
                except Exception:
                    continue
            
            # Calculate metrics
            error_rate_5xx = (error_5xx_count / max(total_requests, 1)) * 100
            median_response_time = self._calculate_percentile(response_times, 50) if response_times else 0
            p95_response_time = self._calculate_percentile(response_times, 95) if response_times else 0
            
            total_pipelines = pipeline_successes + pipeline_failures
            pipeline_success_rate = (pipeline_successes / max(total_pipelines, 1)) * 100
            avg_pipeline_duration = sum(pipeline_durations) / max(len(pipeline_durations), 1) if pipeline_durations else 0
            
            return SLOMetrics(
                error_rate_5xx=round(error_rate_5xx, 2),
                median_response_time=round(median_response_time, 2),
                p95_response_time=round(p95_response_time, 2),
                pipeline_success_rate=round(pipeline_success_rate, 2),
                avg_pipeline_duration=round(avg_pipeline_duration, 2),
                active_users_1h=len(unique_users),
                total_requests_1h=total_requests
            )
            
        except Exception as e:
            self.logger.error("Failed to calculate SLO metrics", error=e)
            # Return default metrics
            return SLOMetrics(
                error_rate_5xx=0.0,
                median_response_time=0.0,
                p95_response_time=0.0,
                pipeline_success_rate=100.0,
                avg_pipeline_duration=0.0,
                active_users_1h=0,
                total_requests_1h=0
            )
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile from list of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
    
    def check_slo_violations(self) -> List[Dict[str, Any]]:
        """Check for SLO violations and return alerts"""
        metrics = self.get_slo_metrics(hours=1)
        violations = []
        
        # Check error rate SLO: < 1% 5xx errors
        if metrics.error_rate_5xx > 1.0:
            violations.append({
                "type": "error_rate_violation",
                "severity": "critical",
                "message": f"5xx error rate {metrics.error_rate_5xx}% exceeds 1% threshold",
                "current_value": metrics.error_rate_5xx,
                "threshold": 1.0,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check response time SLO: median < 30s
        if metrics.median_response_time > 30000:  # 30 seconds in ms
            violations.append({
                "type": "response_time_violation",
                "severity": "warning",
                "message": f"Median response time {metrics.median_response_time}ms exceeds 30s threshold",
                "current_value": metrics.median_response_time,
                "threshold": 30000,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Check pipeline duration SLO: avg < 30s
        if metrics.avg_pipeline_duration > 30:
            violations.append({
                "type": "pipeline_duration_violation",
                "severity": "warning",
                "message": f"Average pipeline duration {metrics.avg_pipeline_duration}s exceeds 30s threshold",
                "current_value": metrics.avg_pipeline_duration,
                "threshold": 30,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return violations
    
    def get_metrics_json(self) -> str:
        """Get metrics in JSON format for external monitoring"""
        health = self.get_health_status()
        slo_metrics = self.get_slo_metrics()
        violations = self.check_slo_violations()
        
        return json.dumps({
            "health": asdict(health),
            "slo_metrics": asdict(slo_metrics),
            "violations": violations,
            "timestamp": datetime.utcnow().isoformat()
        }, indent=2)


# Global health checker instance
health_checker = HealthChecker() 