from abc import ABC, abstractmethod

class DALInterface(ABC):
    """Abstract class defining the interface for database operations."""

    @abstractmethod
    def create_table(self, conn):
        pass

    @abstractmethod
    def insert(self, conn, *args):
        pass

    @abstractmethod
    def get_all(self, conn):
        pass

    @abstractmethod
    def get_by_id(self, conn, record_id):
        pass

    @abstractmethod
    def update(self, conn, record_id, *args):
        pass

    @abstractmethod
    def delete(self, conn, record_id):
        pass

    def check_connection(self, conn):
        """Checks if the database connection is active."""
        if conn is None or conn.closed:
            raise Exception("Database connection is closed or invalid.")
