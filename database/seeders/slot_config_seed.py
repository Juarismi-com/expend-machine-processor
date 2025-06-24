from database.conn import get_db, close_db

def create_seed():
    """
        Numero gpio del raspberry,  cada column y fila necesarios hace una conviciona de slot
        rows = [17, 18, 27, 22, 23, 24]
        columns = [12, 16, 4, 5, 6, 13, 19, 26, 20, 21]
    """
    row_inserts = [
        (1, 17, 12),
        (2, 17, 16),
        (3, 17, 4),
        (4, 17, 5),
        (5, 17, 6),
        (6, 17, 13),
        (7, 17, 19),
        (8, 17, 26),
        (9, 17, 20),
        (10, 17, 21),
    ]
    
    
    get_db().executemany("INSERT INTO slot_config (slot_mi, file, columna) VALUES (?, ?, ?)", row_inserts)
    close_db()


if __name__ == "main":
    create_seed()