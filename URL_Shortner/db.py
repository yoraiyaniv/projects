import time
import mysql.connector
import random
import string

class DBOps():    
    def __init__(self):
        self.conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="urls_storage")
        self.cursor = self.conn.cursor()
        self.ID_LEN = 6
    
    # This function assigns an id for given url in the database.
    # Each database entry contains:
    # 1. random id value for the url
    # 2. the original url
    # 3. time of expiration - given as an integer of the seconds passed since the epoch (January 1, 1970, 00:00:00 at UTC)
    def assign_url_id(self, url: str, ttl: int = 86400) -> str:
        expiration_time = time.time() + ttl
        
        while True:
            id = str(''.join(random.choices(string.ascii_letters + string.digits, k=self.ID_LEN)))
            self.cursor.execute("SELECT * FROM urls WHERE id='%s';"%(id)) 
            if len(self.cursor.fetchall()) == 0:
                break
            else:
                continue
        
        self.cursor.execute("INSERT INTO urls (id, url, expiration_time) VALUES ('%s','%s',%s);"%(id, url, expiration_time))
        self.conn.commit()
        
        return id
    
    def create_urls_table(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS urls(id VARCHAR(256), url TEXT, expiration_time INT)")
        self.conn.commit()

    def delete_id(self, id: str) -> bool:
        self.cursor.execute("DELETE FROM urls WHERE id='%s';"%(id))
        self.conn.commit()
        return self.cursor.rowcount != 0
    
    def get_assigned_url(self, id: str) -> str:
        try:
            self.cursor.execute("SELECT * FROM urls WHERE id='%s';"%(id))
        except:
            raise ValueError("Id have no associated url in database.")
        return self.cursor.fetchall()[0][1]
    
    def close_connection(self) -> bool:
        try:
            self.cursor.close()
            self.conn.close()
            return True
        except:
            return False
        
    def delete_expired_urls(self) -> int:
        t = time.time()

        self.cursor.execute("DELETE FROM urls WHERE expiration_time < %s;"%(t))
        self.conn.commit()
        
        return self.cursor.rowcount
    
    def delete_table(self):
        self.cursor.execute("DROP TABLE urls;")
        self.conn.commit()
        