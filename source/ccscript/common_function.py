from pathlib import Path

def does_file_exist(file_full_path):

    file = Path(file_full_path)
    return (file.is_file())
    
    
    
    