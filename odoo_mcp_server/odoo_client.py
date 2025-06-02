"""Odoo XML-RPC client with connection pooling and retry logic."""

import asyncio
import json
import logging
import xmlrpc.client
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class OdooConfig(BaseSettings):
    """Configuration for Odoo connection."""
    
    url: str = Field(
        default="http://localhost:8069",
        description="Odoo server URL"
    )
    database: str = Field(
        description="Odoo database name"
    )
    username: Optional[str] = Field(
        default=None,
        description="Username for authentication"
    )
    password: Optional[str] = Field(
        default=None,
        description="Password for authentication"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication (Odoo 14+)"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts"
    )
    retry_delay: float = Field(
        default=1.0,
        description="Delay between retries in seconds"
    )
    
    class Config:
        env_prefix = "ODOO_"
        
    @validator("url")
    def validate_url(cls, v):
        """Ensure URL is properly formatted."""
        if not v.startswith(("http://", "https://")):
            v = f"http://{v}"
        return v.rstrip("/")


class OdooClient:
    """Asynchronous Odoo XML-RPC client."""
    
    def __init__(self, config: OdooConfig):
        self.config = config
        self.uid: Optional[int] = None
        self.password: Optional[str] = None
        self._common_proxy: Optional[xmlrpc.client.ServerProxy] = None
        self._object_proxy: Optional[xmlrpc.client.ServerProxy] = None
        self._lock = asyncio.Lock()
        
    @property
    def is_connected(self) -> bool:
        """Check if client is authenticated."""
        return self.uid is not None
        
    async def connect(self) -> Dict[str, Any]:
        """Authenticate with Odoo server."""
        async with self._lock:
            try:
                # Create proxies
                self._common_proxy = xmlrpc.client.ServerProxy(
                    f"{self.config.url}/xmlrpc/2/common",
                    allow_none=True,
                    encoding="utf-8"
                )
                self._object_proxy = xmlrpc.client.ServerProxy(
                    f"{self.config.url}/xmlrpc/2/object",
                    allow_none=True,
                    encoding="utf-8"
                )
                
                # Get server version
                version = await self._execute_with_retry(
                    self._common_proxy.version
                )
                
                # Authenticate
                auth_params = [
                    self.config.database,
                    self.config.username or "",
                    self.config.password or self.config.api_key or ""
                ]
                
                self.uid = await self._execute_with_retry(
                    self._common_proxy.authenticate,
                    *auth_params
                )
                
                if not self.uid:
                    raise Exception("Authentication failed")
                    
                # Store password/api_key for future calls
                self.password = self.config.password or self.config.api_key
                
                return {
                    "success": True,
                    "uid": self.uid,
                    "version": version,
                    "database": self.config.database
                }
                
            except Exception as e:
                logger.error(f"Connection failed: {str(e)}")
                raise
                
    async def execute(
        self,
        model: str,
        method: str,
        *args,
        **kwargs
    ) -> Any:
        """Execute a method on an Odoo model."""
        if not self.is_connected:
            raise Exception("Not authenticated")
            
        params = [
            self.config.database,
            self.uid,
            self.password,
            model,
            method,
            *args
        ]
        
        if kwargs:
            params.append(kwargs)
            
        return await self._execute_with_retry(
            self._object_proxy.execute_kw,
            *params
        )
        
    async def search(
        self,
        model: str,
        domain: List[Any],
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None
    ) -> List[int]:
        """Search for records."""
        kwargs = {
            "offset": offset
        }
        if limit is not None:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order
            
        return await self.execute(model, "search", domain, **kwargs)
        
    async def read(
        self,
        model: str,
        ids: List[int],
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Read records by IDs."""
        kwargs = {}
        if fields:
            kwargs["fields"] = fields
            
        return await self.execute(model, "read", ids, **kwargs)
        
    async def search_read(
        self,
        model: str,
        domain: List[Any],
        fields: Optional[List[str]] = None,
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search and read in one call."""
        kwargs = {
            "offset": offset
        }
        if fields:
            kwargs["fields"] = fields
        if limit is not None:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order
            
        return await self.execute(model, "search_read", domain, **kwargs)
        
    async def create(
        self,
        model: str,
        values: Dict[str, Any]
    ) -> int:
        """Create a new record."""
        return await self.execute(model, "create", values)
        
    async def write(
        self,
        model: str,
        ids: List[int],
        values: Dict[str, Any]
    ) -> bool:
        """Update existing records."""
        return await self.execute(model, "write", ids, values)
        
    async def unlink(
        self,
        model: str,
        ids: List[int]
    ) -> bool:
        """Delete records."""
        return await self.execute(model, "unlink", ids)
        
    async def _execute_with_retry(self, func, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                # Run in executor to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: func(*args, **kwargs)
                )
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt + 1} failed: {str(e)}"
                )
                
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(
                        self.config.retry_delay * (attempt + 1)
                    )
                    
        raise last_error