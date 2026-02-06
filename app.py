from flask import Flask, render_template, url_for, request, redirect, flash, session
import manager
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'f1l2a3s4h5'


ADMIN_CREDENTIALS = {
    "login": "admin",
    "password": "admin"
}


@app.route('/')
def index():
    manager.init_db()
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    login = request.form.get('login')
    password = request.form.get('password')

    if login == ADMIN_CREDENTIALS["login"] and password == ADMIN_CREDENTIALS["password"]:
        session['logged_in'] = True
        flash(
            'Успешный вход в систему',
            'success'
        )
        return redirect(url_for('administration'))
    else:
        flash(
            'Неверный логин или пароль.',
            'danger'
        )
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop(
        'logged_in',
        None
    )
    flash(
        'Выход из системы',
        'info'
    )
    return redirect(url_for('index'))


@app.route('/administration', methods=['POST', 'GET'])
def administration():
    if 'logged_in' not in session or not session['logged_in']:
        flash(
            'Для доступа к странице администрирования необходима авторизация',
            'warning'
        )
        return redirect(url_for('index'))

    branches_for_select = manager.get_branch_names_for_select()
    books_for_select = manager.get_book_titles_for_select()

    if request.method == 'POST':
        if 'add_branch_name' in request.form:
            branch_name = request.form['add_branch_name'].strip()
            if branch_name:
                if manager.add_branch(branch_name):
                    flash(
                        'Филиал успешно добавлен',
                        'success'
                    )
                else:
                    flash(
                        'Филиал с таким названием уже существует',
                        'danger'
                    )
            else:
                flash(
                    'Название филиала не может быть пустым',
                    'danger'
                )
            return redirect(url_for('administration'))

        if 'update_branch_id' in request.form and 'update_branch_name' in request.form:
            branch_id = request.form['update_branch_id']
            new_name = request.form['update_branch_name'].strip()
            if branch_id and new_name:
                if manager.update_branch(branch_id, new_name):
                    flash(
                        'Филиал успешно обновлен',
                        'success'
                    )
                else:
                    flash(
                        'Не удалось обновить филиал',
                        'danger'
                    )
            else:
                flash(
                    'Необходимо выбрать филиал и ввести новое название',
                    'danger'
                )
            return redirect(url_for('administration'))

        if 'add_book_title' in request.form:
            title = request.form.get('add_book_title', '').strip()
            author = request.form.get('add_book_author', '').strip()
            publisher = request.form.get('add_book_publisher', '').strip()
            year_str = request.form.get('add_book_year', '').strip()
            pages_str = request.form.get('add_book_pages', '').strip()
            illus_str = request.form.get('add_book_illus', '').strip()
            price_str = request.form.get('add_book_price', '').strip()
            branch_id_str = request.form.get('add_book_branch')
            faculty_name = request.form.get('add_book_faculty', '').strip()

            try:
                year = int(year_str) if year_str else None
                pages = int(pages_str) if pages_str else None
                illus = int(illus_str) if illus_str else None
                price = float(price_str) if price_str else None
            except ValueError:
                flash(
                    'Ошибка ввода числовых данных для книги',
                    'danger'
                )
                return redirect(url_for('administration'))

            if not title or not author or not branch_id_str or not faculty_name:
                flash(
                    'Необходимо заполнить все обязательные поля для книги (название, автор, филиал, факультет)',
                    'danger'
                )
                return redirect(url_for('administration'))

            try:
                branch_id = int(branch_id_str)
                new_book_id = manager.add_book(
                    title,
                    author,
                    publisher,
                    year,
                    pages,
                    illus,
                    price,
                    branch_id,
                    faculty_name
                )
                flash(
                    f'Книга "{title}" успешно добавлена',
                    'success'
                )

                return redirect(url_for('administration'))
            except Exception as e:
                flash(
                    f'Ошибка при добавлении книги: {e}',
                    'danger'
                )
                return redirect(url_for('administration'))

        if 'update_book_id' in request.form:
            book_id = request.form['update_book_id']
            title = request.form.get('update_book_title', '').strip()
            author = request.form.get('update_book_author', '').strip()
            publisher = request.form.get('update_book_publisher', '').strip()
            year_str = request.form.get('update_book_year', '').strip()
            pages_str = request.form.get('update_book_pages', '').strip()
            illus_str = request.form.get('update_book_illus', '').strip()
            price_str = request.form.get('update_book_price', '').strip()

            try:
                year = int(year_str) if year_str else None
                pages = int(pages_str) if pages_str else None
                illus = int(illus_str) if illus_str else None
                price = float(price_str) if price_str else None
            except ValueError:
                flash(
                    'Ошибка ввода числовых данных для книги',
                    'danger'
                )
                return redirect(url_for('administration'))

            if not book_id or not title or not author:
                flash(
                    'Необходимо выбрать книгу и заполнить обязательные поля (название, автор)',
                    'danger'
                )
                return redirect(url_for('administration'))

            try:
                if manager.update_book(book_id, title, author, publisher, year, pages, illus, price):
                    flash(
                        'Информация о книге успешно обновлена',
                        'success'
                    )
                else:
                    flash(
                        'Не удалось обновить информацию о книге',
                        'danger'
                    )
                return redirect(url_for('administration'))
            except Exception as e:
                flash(
                    f'Ошибка при обновлении книги: {e}',
                    'danger'
                )
                return redirect(url_for('administration'))

    book_to_edit = None
    if request.args.get('edit_book'):
        try:
            book_id = int(request.args['edit_book'])
            book_to_edit = manager.get_book_details_for_update(book_id)
        except ValueError:
            flash(
                'Некорректный ID книги для редактирования',
                'danger'
            )
        except Exception as e:
            flash(
                f'Ошибка при загрузке данных для редактирования: {e}',
                'danger'
            )

    all_books = manager.get_all_books()
    all_branches = manager.get_branches()

    return render_template(
        'administration.html',
        branches=branches_for_select,
        books=books_for_select,
        all_books=all_books,
        all_branches=all_branches,
        book_to_edit=book_to_edit
    )




@app.route('/usage', methods=['POST', 'GET'])
def usage():
    books_for_select = manager.get_book_titles_for_select()
    branches_for_select = manager.get_branch_names_for_select()
    all_books_data = manager.get_all_books()

    if request.method == 'POST':
        if 'action' in request.form and request.form['action'] == 'count_copies':
            book_title = request.form.get('title')
            branch_name = request.form.get('branch')

            if book_title and branch_name:
                quantity = manager.count_book_in_branch(
                    book_title,
                    branch_name
                )
                flash(
                    f'Количество экземпляров книги "{book_title}" в филиале "{branch_name}": {quantity}',
                    'info'
                )
            else:
                flash(
                    'Выберите книгу и филиал.',
                    'warning'
                )
            return redirect(url_for('usage'))

        elif 'action' in request.form and request.form['action'] == 'count_faculties':
            book_title = request.form.get('title')
            branch_name = request.form.get('branch')

            if book_title and branch_name:
                faculties = manager.get_faculties_for_book_in_branch(
                    book_title,
                    branch_name
                )
                if faculties:
                    flash(
                        f'Книга "{book_title}" используется на факультетах: {", ".join(faculties)} (в филиале "{branch_name}")',
                        'info'
                    )
                else:
                    flash(
                        f'Информация о факультетах для книги "{book_title}" в филиале "{branch_name}" не найдена',
                        'warning'
                    )
            else:
                flash(
                    'Выберите книгу и филиал',
                    'warning'
                )
            return redirect(url_for('usage'))
        else:
            flash(
                'Неизвестное действие',
                'danger'
            )
            return redirect(url_for('usage'))

    return render_template(
        'usage.html',
        books=books_for_select,
        branches=branches_for_select,
        all_books_data=all_books_data
    )





