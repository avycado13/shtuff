import os
import sqlite3
import datetime
import uuid
import pickle


class FileStorage:
    def __init__(self, root_dir):
        self.root_dir = root_dir

    def validate_access_token(self, access_token):
        with sqlite3.connect('file_storage.db') as conn:
            c = conn.cursor()
            c.execute(
                "SELECT * FROM access_tokens WHERE access_token=?", (access_token,))
            result = c.fetchone()
        return result is not None

    def check_permission(self, access_token, permission):
        with sqlite3.connect('file_storage.db') as conn:
            c = conn.cursor()
            c.execute("SELECT " + permission +
                      " FROM permissions WHERE access_token=?", (access_token,))
            result = c.fetchone()
        return result is not None and result[0]

    def upload_file(self, access_token, file_path, destination):
        if not self.validate_access_token(access_token):
            raise Exception('Invalid access token')
        if not self.check_permission(access_token, 'can_write'):
            raise Exception('Access token does not have write permission')
        destination_path = os.path.join(self.root_dir, destination)
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        with open(file_path, 'rb') as f:
            data = f.read()
        
        with open(destination_path, 'wb') as f:
            pickle.dump(data, f)
        
        print('File uploaded successfully.')


    def download_file(self, access_token, source, destination_path):
        if not self.validate_access_token(access_token):
            raise Exception('Invalid access token')
        if not self.check_permission(access_token, 'can_read'):
            raise Exception('Access token does not have read permission')
        source_path = os.path.join(self.root_dir, source)
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        with open(source_path, 'rb') as f:
            data = pickle.load(f)
        
        with open(destination_path, 'wb') as f:
            f.write(data)
        
        print('File downloaded successfully.')

    def delete_file(self, access_token, file_path):
        if not self.validate_access_token(access_token):
            raise Exception('Invalid access token')
        if not self.check_permission(access_token, 'can_delete'):
            raise Exception('Access token does not have delete permission')
        file_path = os.path.join(self.root_dir, file_path)
        os.remove(file_path)
        print('File deleted successfully.')

    def list_files(self, access_token):
        if not self.validate_access_token(access_token):
            raise Exception('Invalid access token')
        if not self.check_permission(access_token, 'can_read'):
            raise Exception('Access token does not have read permission')
        files = []
        for root, _, filenames in os.walk(self.root_dir):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                files.append(file_path)
        return files

    def get_file_metadata(self, access_token, file_path):
        if not self.validate_access_token(access_token):
            raise Exception('Invalid access token')
        if not self.check_permission(access_token, 'can_read'):
            raise Exception('Access token does not have read permission')
        file_path = os.path.join(self.root_dir, file_path)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            creation_time = os.path.getctime(file_path)
            modification_time = os.path.getmtime(file_path)
            permissions = os.stat(file_path).st_mode
            return {
                'size': size,
                'creation_time': datetime.datetime.fromtimestamp(creation_time),
                'modification_time': datetime.datetime.fromtimestamp(modification_time),
                'permissions': permissions
            }
        else:
            return None

    def generate_access_token(self, can_read=True, can_write=True, can_delete=True):
        access_token = str(uuid.uuid4())
        with sqlite3.connect('file_storage.db') as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO access_tokens (access_token) VALUES (?)", (access_token,))
            c.execute("INSERT INTO permissions (access_token, can_read, can_write, can_delete) VALUES (?, ?, ?, ?)",
                      (access_token, can_read, can_write, can_delete))
        print('Access token generated successfully.')
        return access_token

    def create_schema(self):
        with sqlite3.connect('file_storage.db') as conn:
            c = conn.cursor()

            # Create table for access tokens
            c.execute('''
                CREATE TABLE IF NOT EXISTS access_tokens (
                    access_token TEXT PRIMARY KEY
                )
            ''')

            # Create table for permissions
            c.execute('''
                CREATE TABLE IF NOT EXISTS permissions (
                    access_token TEXT PRIMARY KEY,
                    can_read BOOLEAN,
                    can_write BOOLEAN,
                    can_delete BOOLEAN,
                    FOREIGN KEY(access_token) REFERENCES access_tokens(access_token)
                )
            ''')

        print('Schema created successfully.')
