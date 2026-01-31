from __future__ import annotations

import re
from typing import Any, List

from pypika import Parameter
from tortoise.backends.base.executor import BaseExecutor
from tortoise.models import Model

from .types import quote_identifier


class DmExecutor(BaseExecutor):
    """Dameng database executor - Handles SQL execution and parameter processing"""
    
    EXPLAIN_PREFIX = "EXPLAIN PLAN FOR"
    
    # Parameter placeholder regex - For precise matching and replacement
    PARAM_PATTERN = re.compile(r':(\d+)\b')
    
    def parameter(self, pos: int) -> Parameter:
        """Return parameter placeholder - Dameng uses :number format"""
        return Parameter(f":{pos}")
    
    def quote(self, name: str) -> str:
        """Quote identifier - Dameng uses double quotes, handles keywords automatically"""
        return quote_identifier(name)
    
    async def _process_insert_result(self, instance: Model, results: Any) -> None:
        """Process insert result and set generated primary key if needed"""
        # For Dameng database with IDENTITY columns, we need to get the generated ID
        if self.model._meta.generated_db_fields:
            pk_field_object = self.model._meta.pk
            if pk_field_object and getattr(pk_field_object, 'generated', False):
                # Try different methods to get the last inserted ID
                methods = [
                    "SELECT SCOPE_IDENTITY() AS last_id",
                    "SELECT @@IDENTITY AS last_id", 
                    "SELECT LAST_INSERT_ID() AS last_id",
                    "SELECT CURRVAL('SEQ_AI_COPILOT') AS last_id",  # If using sequence
                ]
                
                for method in methods:
                    try:
                        query_result = await self.db.execute_query_dict(method)
                        if query_result and query_result[0].get('last_id'):
                            last_id = query_result[0]['last_id']
                            instance.pk = last_id
                            return
                    except Exception:
                        continue
                
                # If all identity functions fail, try querying max ID
                try:
                    table_name = self.model._meta.db_table
                    pk_column = pk_field_object.source_field or pk_field_object.model_field_name
                    max_id_query = f'SELECT MAX("{pk_column}") AS max_id FROM "{table_name}"'
                    query_result = await self.db.execute_query_dict(max_id_query)
                    if query_result and query_result[0].get('max_id'):
                        max_id = query_result[0]['max_id']
                        instance.pk = max_id
                except Exception:
                    # If all methods fail, leave the ID as None
                    pass
    
    def convert_parameters(self, query: str) -> str:
        """Convert :1, :2 format parameter placeholders to dmPython's ? format"""
        # Save all string contents to avoid replacing parameters inside strings
        strings = []
        string_pattern = re.compile(r"'[^']*'")
        
        # Temporarily replace strings with placeholders
        def save_string(match):
            strings.append(match.group(0))
            return f"__STR_{len(strings)-1}__"
        
        query_with_placeholders = string_pattern.sub(save_string, query)
        
        # Replace parameters
        query_with_placeholders = self.PARAM_PATTERN.sub('?', query_with_placeholders)
        
        # Restore strings
        for i, string in enumerate(strings):
            query_with_placeholders = query_with_placeholders.replace(
                f"__STR_{i}__", string
            )
        
        return query_with_placeholders