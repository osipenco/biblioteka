import psycopg2
import os


DB_HOST = os.environ.get(
    "DB_HOST",
    "localhost"
)
DB_PORT = os.environ.get(
    "DB_PORT",
    "5432"
)
DB_NAME = os.environ.get(
    "DB_NAME",
    "biblioteka_db"
)
DB_USER = os.environ.get(
    "DB_USER",
    "admin"
)
DB_PASSWORD = os.environ.get(
    "DB_PASSWORD",
    "admin"
)


def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except psycopg2.Error as e:
        print(f"Ошибка подключения к базе данных PostgreSQL: {e}")
        return None


def init_db():
    conn = get_db_connection()
    if conn is None:
        print("Не удалось подключиться к базе данных PostgreSQL")
        return

    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS branches (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faculties (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            publisher VARCHAR(255),
            publication_year INTEGER,
            page_count INTEGER,
            illustration_count INTEGER,
            price DECIMAL(10, 2) -- Пример использования DECIMAL для денег
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS book_in_branch (
            book_id INTEGER,
            branch_id INTEGER,
            quantity INTEGER DEFAULT 1,
            PRIMARY KEY (book_id, branch_id),
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE, -- Добавление ON DELETE CASCADE
            FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS book_on_faculty (
            book_id INTEGER,
            faculty_id INTEGER,
            PRIMARY KEY (book_id, faculty_id),
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            FOREIGN KEY (faculty_id) REFERENCES faculties(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    cursor.close()
    conn.close()
    print("База данных и таблицы PostgreSQL успешно созданы (или уже существуют)")


def add_branch(name):
    conn = get_db_connection()
    if conn is None: return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO branches (name) VALUES (%s)",
            (name,)
        )
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


from psycopg2.extras import RealDictCursor


def get_branches():
    conn = get_db_connection()
    if conn is None: return []
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM branches ORDER BY name")
        branches = cursor.fetchall()
        return branches
    finally:
        cursor.close()
        conn.close()


def update_branch(branch_id, new_name):
    conn = get_db_connection()
    if conn is None: return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE branches SET name = %s WHERE id = %s RETURNING id",
            (new_name, branch_id)
        )
        updated_id = cursor.fetchone()
        conn.commit()
        return updated_id is not None
    except psycopg2.IntegrityError:
        conn.rollback()
        return False
    except psycopg2.Error as e:
        print(f"Ошибка при обновлении филиала: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def get_branch_by_id(branch_id):
    conn = get_db_connection()
    if conn is None: return None
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            "SELECT * FROM branches WHERE id = %s",
            (branch_id,)
        )
        branch = cursor.fetchone()
        return branch
    except psycopg2.Error as e:
        print(f"Ошибка при получении филиала по ID: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def add_book(
    title,
    author,
    publisher,
    publication_year,
    page_count,
    illustration_count,
    price,
    branch_id,
    faculty_name
):
    conn = get_db_connection()
    if conn is None: return None
    cursor = conn.cursor()
    book_id = None

    try:
        cursor.execute(
            '''
            INSERT INTO books (title, author, publisher, publication_year, page_count, illustration_count, price)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            ''',
            (title, author, publisher, publication_year, page_count, illustration_count, price)
        )

        book_id_result = cursor.fetchone()
        if book_id_result:
            book_id = book_id_result[0]

        cursor.execute(
            "SELECT quantity FROM book_in_branch WHERE book_id = %s AND branch_id = %s",
            (book_id, branch_id)
        )
        existing_entry = cursor.fetchone()

        if existing_entry:

            cursor.execute(
                "UPDATE book_in_branch SET quantity = quantity + 1 WHERE book_id = %s AND branch_id = %s",
                (book_id, branch_id)
            )
        else:
            cursor.execute(
                "INSERT INTO book_in_branch (book_id, branch_id, quantity) VALUES (%s, %s, 1)",
                (book_id, branch_id)
            )

        cursor.execute(
            "INSERT INTO faculties (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING id",
            (faculty_name,)
        )
        faculty_id_result = cursor.fetchone()

        if faculty_id_result:
            faculty_id = faculty_id_result[0]
        else:
            cursor.execute(
                "SELECT id FROM faculties WHERE name = %s",
                (faculty_name,)
            )
            faculty_id_result = cursor.fetchone()
            if faculty_id_result:
                faculty_id = faculty_id_result[0]
            else:
                raise Exception(f"Не удалось получить ID для факультета: {faculty_name}")

        cursor.execute(
            "INSERT INTO book_on_faculty (book_id, faculty_id) VALUES (%s, %s) ON CONFLICT (book_id, faculty_id) DO NOTHING",
            (book_id, faculty_id)
        )

        conn.commit()
        return book_id

    except psycopg2.Error as e:
        print(f"Ошибка при добавлении книги: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def get_all_books():
    conn = get_db_connection()
    if conn is None: return []
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute('''
            SELECT
                b.id, b.title, b.author, b.publisher, b.publication_year,
                b.page_count, b.illustration_count, b.price,
                STRING_AGG(DISTINCT br.name, ', ') AS branches, -- STRING_AGG для агрегации строк
                STRING_AGG(DISTINCT f.name, ', ') AS faculties
            FROM books b
            LEFT JOIN book_in_branch bib ON b.id = bib.book_id
            LEFT JOIN branches br ON bib.branch_id = br.id
            LEFT JOIN book_on_faculty bof ON b.id = bof.book_id
            LEFT JOIN faculties f ON bof.faculty_id = f.id
            GROUP BY b.id -- Группируем по ID книги
            ORDER BY b.title
        ''')
        books = cursor.fetchall()
        return books
    except psycopg2.Error as e:
        print(f"Ошибка при получении всех книг: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_book_by_id(book_id):
    conn = get_db_connection()
    if conn is None: return None
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            "SELECT * FROM books WHERE id = %s",
            (book_id,)
        )
        book = cursor.fetchone()
        return book
    except psycopg2.Error as e:
        print(f"Ошибка при получении книги по ID: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def update_book(
    book_id,
    title,
    author,
    publisher,
    publication_year,
    page_count,
    illustration_count,
    price
):
    conn = get_db_connection()
    if conn is None: return False
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            UPDATE books
            SET title = %s, author = %s, publisher = %s, publication_year = %s,
                page_count = %s, illustration_count = %s, price = %s
            WHERE id = %s
            ''',
            (title, author, publisher, publication_year, page_count, illustration_count, price, book_id)
        )

        updated = cursor.rowcount > 0
        conn.commit()
        return updated
    except psycopg2.Error as e:
        print(f"Ошибка при обновлении книги: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def get_book_details_for_update(book_id):
    conn = get_db_connection()
    if conn is None: return None
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT
                b.id, b.title, b.author, b.publisher, b.publication_year,
                b.page_count, b.illustration_count, b.price,
                STRING_AGG(DISTINCT bib.branch_id::TEXT, ',') AS branch_ids, -- Приводим ID к TEXT для STRING_AGG
                STRING_AGG(DISTINCT bof.faculty_id::TEXT, ',') AS faculty_ids
            FROM books b
            LEFT JOIN book_in_branch bib ON b.id = bib.book_id
            LEFT JOIN book_on_faculty bof ON b.id = bof.book_id
            WHERE b.id = %s
            GROUP BY b.id -- Группируем по ID книги
        """, (book_id,))
        book = cursor.fetchone()

        if book:
            book['branch_ids'] = book['branch_ids'] if book['branch_ids'] is not None else ""
            book['faculty_ids'] = book['faculty_ids'] if book['faculty_ids'] is not None else ""

        return book
    except psycopg2.Error as e:
        print(f"Ошибка при получении деталей книги для обновления: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def count_book_in_branch(book_title, branch_name):
    conn = get_db_connection()
    if conn is None: return 0
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute('''
            SELECT bib.quantity
            FROM book_in_branch bib
            JOIN books b ON bib.book_id = b.id
            JOIN branches br ON bib.branch_id = br.id
            WHERE b.title = %s AND br.name = %s
        ''', (book_title, branch_name))
        result = cursor.fetchone()
        return result['quantity'] if result else 0
    except psycopg2.Error as e:
        print(f"Ошибка при подсчете книги в филиале: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()


def get_faculties_for_book_in_branch(book_title, branch_name):
    conn = get_db_connection()
    if conn is None: return []
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute('''
            SELECT DISTINCT f.name
            FROM book_on_faculty bof
            JOIN books b ON bof.book_id = b.id
            JOIN faculties f ON bof.faculty_id = f.id
            JOIN book_in_branch bib ON b.id = bib.book_id -- Нужно JOIN с book_in_branch, чтобы проверить наличие в филиале
            JOIN branches br ON bib.branch_id = br.id
            WHERE b.title = %s AND br.name = %s
        ''', (book_title, branch_name))
        faculties_data = cursor.fetchall()
        return [f['name'] for f in faculties_data]
    except psycopg2.Error as e:
        print(f"Ошибка при получении факультетов для книги в филиале: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_book_titles_for_select():
    conn = get_db_connection()
    if conn is None: return []
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("SELECT id, title FROM books ORDER BY title")
        titles = cursor.fetchall()
        return titles
    except psycopg2.Error as e:
        print(f"Ошибка при получении названий книг для select: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def get_branch_names_for_select():
    conn = get_db_connection()
    if conn is None: return []
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("SELECT id, name FROM branches ORDER BY name")
        branches = cursor.fetchall()
        return branches
    except psycopg2.Error as e:
        print(f"Ошибка при получении названий филиалов для select: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    init_db()
