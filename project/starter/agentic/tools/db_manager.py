"""
Database Manager for UDA-Hub Multi-Agent System
Handles connections to both CultPass and UdaHub databases
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Optional, Generator, cast


class DatabaseManager:
    """Manages database connections for both external (CultPass) and core (UdaHub) databases"""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            base_path: Base path to project root. If None, auto-detects.
        """
        if base_path is None:
            # Auto-detect base path (assuming we're in agentic/tools/)
            current_file = Path(__file__).resolve()
            base_path_path = current_file.parent.parent.parent
        else:
            base_path_path = Path(cast(str, base_path))
        
        self.base_path = base_path_path
        
        # Database paths
        self.cultpass_db_path = self.base_path / "data" / "external" / "cultpass.db"
        self.udahub_db_path = self.base_path / "data" / "core" / "udahub.db"
        
        # Verify databases exist
        if not self.cultpass_db_path.exists():
            raise FileNotFoundError(f"CultPass database not found at {self.cultpass_db_path}")
        if not self.udahub_db_path.exists():
            raise FileNotFoundError(f"UdaHub database not found at {self.udahub_db_path}")
        
        # Create engines
        self.cultpass_engine = create_engine(f"sqlite:///{self.cultpass_db_path}", echo=False)
        self.udahub_engine = create_engine(f"sqlite:///{self.udahub_db_path}", echo=False)
        
        # Create session makers
        self.CultPassSession = sessionmaker(bind=self.cultpass_engine)
        self.UdaHubSession = sessionmaker(bind=self.udahub_engine)
    
    @contextmanager
    def get_cultpass_session(self) -> Generator[Session, None, None]:
        """Get a CultPass database session with automatic commit/rollback"""
        session = self.CultPassSession()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    @contextmanager
    def get_udahub_session(self) -> Generator[Session, None, None]:
        """Get a UdaHub database session with automatic commit/rollback"""
        session = self.UdaHubSession()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def close(self):
        """Close all database connections"""
        self.cultpass_engine.dispose()
        self.udahub_engine.dispose()


# Global instance for easy access
_db_manager = None

def get_db_manager(base_path: Optional[str] = None) -> DatabaseManager:
    """Get or create global database manager instance"""
    global _db_manager  # noqa: PLW0603
    if _db_manager is None:
        _db_manager = DatabaseManager(base_path)
    return _db_manager

