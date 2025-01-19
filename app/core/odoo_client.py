import xmlrpc.client
from typing import Optional, Dict, Any
from app.core.config import settings

class OdooClient:
    def __init__(self):
        self.url = settings.ODOO_URL
        self.db = settings.ODOO_DB
        self.username = settings.ODOO_USERNAME
        self.password = settings.ODOO_PASSWORD
        
        # XML-RPC endpoints
        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        
    def authenticate(self, login: str, password: str) -> Optional[int]:
        """Authenticate user against Odoo"""
        try:
            uid = self.common.authenticate(self.db, login, password, {})
            if uid:
                return uid
            return None
        except Exception as e:
            print(f"Odoo authentication error: {e}")
            return None
            
    def get_user_info(self, uid: int) -> Optional[Dict[Any, Any]]:
        """Get user information from Odoo"""
        try:
            user_data = self.models.execute_kw(
                self.db, 
                uid, 
                self.password,
                'res.users', 
                'read', 
                [uid],
                {'fields': ['name', 'email', 'login', 'partner_id']}
            )
            if user_data:
                return user_data[0]
            return None
        except Exception as e:
            print(f"Error fetching user info: {e}")
            return None 