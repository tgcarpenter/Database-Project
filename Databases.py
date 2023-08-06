import sqlite3 as sql
import shutil as shu
import datetime
import os
import sys

from PyQt6.QtCore import QObject, pyqtSignal, QThread


class Querier(QObject):
    finished = pyqtSignal(list)

    def __init__(self, common_query, name):
        super().__init__()
        self.common_query = common_query
        self.name = name

    def run(self):
        con = sql.connect(self.name)
        cur = con.cursor()
        query = cur.execute(self.common_query).fetchall()
        con.close()
        self.finished.emit(query)


class Database:
    def __init__(self, name):  # Main table is made with creation of class instance
        super().__init__()
        self.skip = False
        self.name = name + '.db'
        self.text_table_count = 1  # defines current name for text tables in column creation
        self.list_table_count = 1  # defines current name for list tables in column creation
        self.row_count = 0  # defines current row count
        self.class_count = 0  # defines position of created column classes in column_classes list  -- useless?
        # what if two columns are named the same thing? ugh!! <- fixed because I refer to them by position not name
        self.column_classes = []  # contains all the column class objects (in order of columns)
        self.to_delete = []
        self.common_query = "SELECT Main._id"
        self.thread = None

        con = sql.connect(self.name)
        cur = con.cursor()
        try:
            cur.execute('CREATE TABLE Main (_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE)')
        except:
            pass
        con.commit()
        con.close()

    def delete_database(self):
        os.remove(self.name)

    def copy_database(self):
        shu.copy(self.name, "temp.db")

    def backup_database(self, num):
        shu.copy(self.name, fr'backups\{self.name}{str(num)}')

    def not_saved(self):
        shu.copy("temp.db", self.name)

    def change_db_name(self, newname):
        self.name = newname + ".db"
        os.rename(self.name, newname + ".db")

    def rename_columns(self):  # Rework Column names
        for column in self.column_classes:
            if column.temp_saved_newname is not None:
                column.change_column_name(self.name, column.temp_saved_newname)

    def add_column_integer(self, name):  # Adds Integer column to main table: ONE to ONE
        self.column_classes.append(ColumnInteger(name, self.name))
        self.class_count += 1

    def add_column_text(self, name):  #
        self.column_classes.append(ColumnText(name, self.name, self.text_table_count))
        self.class_count += 1
        self.text_table_count += 1

    def add_column_list(self, name):
        self.column_classes.append(ColumnList(name, self.name, self.list_table_count))
        self.class_count += 1
        self.list_table_count += 1

    def delete_column(self, c_id):
        self.column_classes[c_id].delete_column(self.name)
        self.column_classes.remove(self.column_classes[c_id])
        if not self.column_classes:
            con = sql.connect(self.name)
            cur = con.cursor()
            cur.execute(f'DELETE FROM Main WHERE _id > 0')
            cur.execute(f'DELETE FROM "sqlite_sequence" WHERE "name" = "Main"')
            con.commit()
            con.close()

    def move_column(self, oIndex, nIndex):
        t_column = self.column_classes.pop(oIndex)
        self.column_classes.insert(nIndex, t_column)

    def delete_row(self, old_values: list, r_id):
        self.row_count -= 1
        for column, old_val in zip(self.column_classes, old_values):
            if column.table_name[1] == "T":
                column.delete_row(self.name, old_val)
            elif column.table_name[1] == "L":
                if old_val is None:
                    old_val = ""
                column.delete_row(self.name, old_val.split(", "), old_val.split(", "), r_id)
                con = sql.connect(self.name)
                cur = con.cursor()
                cur.execute(f'UPDATE {column.link_table_name} SET _main_id = _main_id - 1 WHERE _main_id > {r_id}')
                con.commit()
                con.close()
        con = sql.connect(self.name)
        cur = con.cursor()
        cur.execute(f'DELETE FROM Main WHERE _id = {r_id}')
        cur.execute(f'UPDATE Main SET _id = _id - 1 WHERE _id > {r_id}')
        cur.execute(f'DELETE FROM "sqlite_sequence" WHERE "name" = "Main"')
        con.commit()
        con.close()

    def clear_empty_rows(self, del_rows: list):  # needs to be moved to model
        for row in del_rows:
            self.delete_row([None for i in range(len(self.column_classes))], row)

    def get_rowcount(self):
        con = sql.connect(self.name)
        cur = con.cursor()
        x = cur.execute("SELECT MAX(_id) FROM Main").fetchone()
        self.row_count = x[0] if x[0] is not None else 0
        con.commit()
        con.close()

    def update_column(self, c_id, r_id, old_value, new_value):
        self.column_classes[c_id].update(self.name, old_value, new_value, r_id)

    def add_defaults(self):
        self.row_count += 1
        con = sql.connect(self.name)
        cur = con.cursor()
        cur.execute("INSERT INTO Main DEFAULT VALUES")
        for column in self.column_classes:
            if column.table_name[1] == 'L':
                cur.execute(f'INSERT INTO {column.link_table_name} (_main_id) VALUES ((SELECT MAX(_id) FROM Main))')
        con.commit()
        con.close()

    def get_column_headers(self) -> list:
        return ["id"] + [column.column_name[2:-1] for column in self.column_classes]

    def autofill_query(self, search):  # used as general autofill in search lineedit
        autofill = []
        con = sql.connect(self.name)
        cur = con.cursor()
        for column in self.column_classes:
            col_fil = cur.execute(f'SELECT DISTINCT {column.column_name} FROM {column.table_name} '
                                  f'WHERE {column.column_name} LIKE "{search}%" '
                                  f'AND {column.column_name} NOT LIKE "{search}"').fetchall()
            autofill += col_fil
        # print("auto", autofill)
        con.close()
        return autofill

    def list_column_query(self, col):  # Used for autofill in list column lineedit
        table = [column.table_name for column in self.column_classes if column.column_name == col]
        con = sql.connect(self.name)
        cur = con.cursor()
        autofill = cur.execute(f"SELECT DISTINCT {col} FROM {table[0]} "
                               f"WHERE {col} IS NOT NULL").fetchall()
        con.close()
        return autofill

    def generate_common_query(self):  # generates a common query to be used for querying (only used for scroll query)
        select_table_columns = ''  # not be given if search is given
        joined_tables = ''
        on_parameters = 'ON '
        for column in self.column_classes:
            select_table_columns += f"{column.table_name}.{column.column_name}, "  # Generating Columns Select

            if column.table_name[1] == 'T':  # Generating join tables and on parameters
                joined_tables += 'JOIN ' + column.table_name + ' '
                on_parameters += f'Main.{column.table_name.casefold()}_id = {column.table_name}._rowid_ AND '
            elif column.table_name[1] == 'L':
                joined_tables += f'JOIN (SELECT DISTINCT {column.link_table_name}._main_id, ' \
                                 f'group_concat({column.table_name}.{column.column_name}, ", ") OVER (PARTITION BY ' \
                                 f'Main._id) AS {column.column_name} FROM Main JOIN {column.table_name} JOIN ' \
                                 f'{column.link_table_name} ON Main._id = {column.link_table_name}._main_id AND ' \
                                 f'{column.table_name}._rowid_ = ' \
                                 f'{column.link_table_name}.{column.table_name.casefold()}_id) AS {column.table_name}' \
                                 f' '
                on_parameters += f'Main._id = {column.table_name}._main_id AND '
        self.common_query = fr'SELECT Main._id, {select_table_columns[:-2]} FROM Main {joined_tables} {on_parameters[:-4]} '
        print("common query generated")

    def background_query(self, table=None):  # runs background query to retrieve whole database
        if self.common_query and not self.skip and self.row_count > 0:
            self.skip = True
            self.thread = QThread()
            self.worker = Querier(self.common_query, self.name)
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            if table is not None:  # temporary, not sure if it is necessary
                self.worker.finished.connect(table.setAllData)
            self.worker.finished.connect(self.resetSkip)

            self.thread.start()
        elif self.row_count == 0:
            table.setAllData([])

    def resetSkip(self):
        self.skip = False

    def general_query(self, start: int, end: int, search=False):  # search holds the text to search for. start/end will
        con = sql.connect(self.name)
        cur = con.cursor()
        if not search:
            query = cur.execute(
                fr'{self.common_query} WHERE Main._id >= {start} AND Main._id <= {end}').fetchall()
        else:
            select_table_columns = ''  # not be given if search is given
            joined_tables = ''
            on_parameters = 'ON '
            where = 'WHERE ('
            for column in self.column_classes:
                select_table_columns += f"{column.table_name}.{column.column_name}, "  # Generating Columns Select

                if column.table_name[1] == 'T':  # Generating join tables and on parameters
                    joined_tables += 'JOIN ' + column.table_name + ' '
                    on_parameters += f'Main.{column.table_name.casefold()}_id = {column.table_name}._rowid_ AND '
                elif column.table_name[1] == 'L':
                    joined_tables += f'JOIN (SELECT DISTINCT {column.link_table_name}._main_id, ' \
                                     f'group_concat({column.table_name}.{column.column_name}, ", ") OVER (PARTITION BY ' \
                                     f'Main._id) AS {column.column_name} FROM Main JOIN {column.table_name} JOIN ' \
                                     f'{column.link_table_name} ON Main._id = {column.link_table_name}._main_id AND ' \
                                     f'{column.table_name}._rowid_ = ' \
                                     f'{column.link_table_name}.{column.table_name.casefold()}_id) AS {column.table_name}' \
                                     f' '
                    on_parameters += f'Main._id = {column.table_name}._main_id AND '
                if search:
                    where += fr'{column.column_name} LIKE "%{search}%" ESCAPE "\" OR '
            if search:
                where = where[:-3] + ')'
            else:
                where = f'WHERE Main._id >= {start} AND Main._id <= {end}'
            query = cur.execute(fr'SELECT Main._id, {select_table_columns[:-2]} FROM Main {joined_tables} {on_parameters[:-4]} '
                                fr'{where}').fetchall()
        con.close()
        return query


class Column:
    def __init__(self, name):
        self.column_name = "[_" + name + "]"
        self.temp_saved_newname = None
        self.table_name = None

    def set_temp_name(self, newname):  # this still functions, but I'm not sure its necessary
        self.temp_saved_newname = newname

    def change_column_name(self, db_name, newname):  # Rework Column names
        con = sql.connect(db_name)
        cur = con.cursor()
        cur.execute('ALTER TABLE {table_name} RENAME COLUMN {column_name} TO {newname}'
                    ''.format(table_name=self.table_name,
                              column_name=self.column_name, newname="[_" + newname + "]"))
        self.column_name = "[_" + newname + "]"
        con.commit()
        con.close()
        self.temp_saved_newname = None


class ColumnInteger(Column):
    def __init__(self, name, db_name):  # Inserts column into main table One-to-one
        super().__init__(name)
        self.table_name = "Main"  # this is interesting
        con = sql.connect(db_name)
        cur = con.cursor()
        cur.execute(f'ALTER TABLE Main ADD {self.column_name} INTEGER')
        con.commit()
        con.close()

    def delete_column(self, db_name):
        con = sql.connect(db_name)
        cur = con.cursor()
        cur.execute(f'ALTER TABLE Main DROP COLUMN {self.column_name}')
        con.commit()
        con.close()

    def update(self, db_name, _, new_value, r_id):
        con = sql.connect(db_name)
        cur = con.cursor()
        if not new_value:
            cur.execute(f'UPDATE Main SET {self.column_name} = Null '
                        f'WHERE _id = {r_id}')
        else:
            if new_value[0] == "_":
                new_value = new_value[1:]
            cur.execute(f'UPDATE Main SET {self.column_name} = "{new_value}" WHERE _id = {r_id}')
        con.commit()
        con.close()


class ColumnText(Column):
    def __init__(self, name, db_name, table_count):  # Creates a one-to-many relation between main table and text table
        super().__init__(name)
        self.table_name = '_TextTable' + str(table_count)
        con = sql.connect(db_name)
        cur = con.cursor()
        cur.execute(f'CREATE TABLE {self.table_name} ({self.column_name} TEXT UNIQUE)')
        cur.execute(f'INSERT INTO {self.table_name} DEFAULT VALUES')
        cur.execute(f'CREATE INDEX {self.table_name}index ON {self.table_name} ({self.column_name})')
        cur.execute(f'ALTER TABLE Main ADD {self.table_name.casefold() + "_id"} INTEGER NOT NULL DEFAULT 1')
        con.commit()
        con.close()

    def delete_column(self, db_name):
        con = sql.connect(db_name)
        cur = con.cursor()
        cur.execute(f'DROP TABLE {self.table_name}')
        cur.execute(f'ALTER TABLE Main DROP COLUMN {self.table_name.casefold()}_id')
        con.commit()
        con.close()

    def delete_row(self, db_name, old_value):
        con = sql.connect(db_name)
        cur = con.cursor()
        if old_value:
            temp_old_value = '"' + old_value + '"'
            temp = cur.execute(f'SELECT Main._id FROM Main JOIN {self.table_name} '
                               f'WHERE Main.{self.table_name.casefold() + "_id"} = {self.table_name}._rowid_ '
                               f'AND {self.table_name}.{self.column_name} = {temp_old_value}').fetchall()
            if len(temp) == 1:
                cur.execute(f'DELETE FROM {self.table_name} WHERE {self.column_name} = {temp_old_value}')
        con.commit()
        con.close()

    def update(self, db_name, old_value, new_value, r_id):
        con = sql.connect(db_name)
        cur = con.cursor()
        if old_value:
            temp_old_value = '"' + old_value + '"'
        else:
            temp_old_value = 'NULL'
        temp = cur.execute(f'SELECT Main._id FROM Main JOIN {self.table_name} '
                           f'WHERE Main.{self.table_name.casefold() + "_id"} = {self.table_name}._rowid_ '
                           f'AND {self.table_name}.{self.column_name} = {temp_old_value}').fetchall()
        if not new_value:
            cur.execute(f'UPDATE Main SET {self.table_name.casefold()}_id = 1 WHERE _id = {r_id}')
            if len(temp) == 1 and temp_old_value != "NULL":
                cur.execute(f'DELETE FROM {self.table_name} WHERE {self.column_name} = {temp_old_value}')
        elif len(temp) != 1:
            try:
                cur.execute(f'INSERT INTO {self.table_name} ({self.column_name}) VALUES (?)', (new_value,))
            except:
                pass
            cur.execute(f'UPDATE Main SET {self.table_name.casefold()}_id = (SELECT _rowid_ '
                        f'FROM {self.table_name} WHERE {self.table_name}.{self.column_name} = "{new_value}") '
                        f'WHERE _id = {r_id}')
        else:
            try:
                cur.execute(f'UPDATE {self.table_name} SET {self.column_name} = (?) '
                            f'WHERE {self.column_name} = "{old_value}"', (new_value,))
            except:
                cur.execute(f'UPDATE Main SET {self.table_name.casefold()}_id = (SELECT _rowid_ '
                            f'FROM {self.table_name} WHERE {self.table_name}.{self.column_name} = "{new_value}") '
                            f'WHERE _id = {r_id}')
                if temp_old_value != "NULL":
                    cur.execute(f'DELETE FROM {self.table_name} WHERE {self.column_name} = {temp_old_value}')
        con.commit()
        con.close()


class ColumnList(Column):
    def __init__(self, name, db_name, table_count):  # Creates a many-to-many relation between main table and list table
        super().__init__(name)
        self.table_name = '_ListTable' + str(table_count)
        self.link_table_name = '_LinkTable' + str(table_count)
        con = sql.connect(db_name)
        cur = con.cursor()
        cur.execute(f'CREATE TABLE {self.table_name} '  # create list table
                    f'({self.column_name} TEXT UNIQUE)')
        cur.execute(f'INSERT INTO {self.table_name} DEFAULT VALUES')
        cur.execute(
            f'CREATE TABLE {self.link_table_name} ({self.table_name.casefold() + "_id"} INTEGER NOT NULL '  # Create link table
            f'DEFAULT 1, _main_id INTEGER NOT NULL)')
        cur.execute(f'INSERT INTO {self.link_table_name} (_main_id) SELECT Main._id FROM Main')
        con.commit()
        con.close()

    def delete_column(self, db_name):
        con = sql.connect(db_name)
        cur = con.cursor()
        cur.execute(f'DROP TABLE {self.table_name}')
        cur.execute(f'DROP TABLE {self.link_table_name}')
        con.commit()
        con.close()

    def add_default_to_link_table(self, db_name, row_number):  # not sure what this is for either
        con = sql.connect(db_name)
        cur = con.cursor()
        cur.execute(f'INSERT INTO {self.link_table_name} (_main_id) VALUES ({row_number})')
        con.commit()
        con.close()

    def update(self, db_name, old_value, new_value, r_id):
        if new_value is None:
            new_value = ''
        if old_value == new_value:
            return
        new_value = new_value.split(", ")
        old_value = old_value.split(", ")
        o_value, n_value = [value for value in old_value if value not in new_value], \
                           [value for value in new_value if value not in old_value]
        self.add_values(db_name, new_value, n_value, r_id)
        self.delete_row(db_name, old_value, o_value, r_id)

    def add_values(self, db_name, new_value, n_value, r_id):

        def insert_new_list_value(value):
            try:
                cur.execute(f'INSERT INTO {self.table_name} ({self.column_name}) VALUES (?)', (value,))
            except:
                pass
            cur.execute(f'INSERT INTO {self.link_table_name} (_main_id, {self.table_name.casefold()}_id) '
                        f'SELECT Main._id, {self.table_name}._rowid_ FROM {self.table_name} JOIN Main '
                        f'WHERE {self.table_name}.{self.column_name} = "{value}" AND Main._id = {r_id}')

        con = sql.connect(db_name)
        cur = con.cursor()
        if new_value != [''] and new_value is not None:
            for v in n_value:
                insert_new_list_value(v)
        else:
            cur.execute(f'INSERT INTO {self.link_table_name} (_main_id, {self.table_name.casefold()}_id) '
                        f' VALUES ({r_id}, 1)')
        con.commit()
        con.close()

    def delete_row(self, db_name, old_value, o_value, r_id):

        def delete_from_link_table(value):
            cur.execute(f'DELETE FROM {self.link_table_name} WHERE _main_id = {r_id} AND '
                        f'{self.table_name.casefold()}_id = (SELECT _rowid_ FROM {self.table_name}'
                        f' WHERE {self.column_name} = "{value}")')

        def delete_from_table(value):
            cur.execute(f'DELETE FROM {self.table_name} WHERE {self.column_name} = "{value}"')

        def count_values_uses(value):
            return cur.execute(f'SELECT {self.link_table_name}._main_id, '
                               f'{self.link_table_name}.{self.table_name.casefold()}_id FROM {self.link_table_name} '
                               f'JOIN {self.table_name} WHERE {self.link_table_name}.{self.table_name.casefold()}_id = '
                               f'{self.table_name}._rowid_ AND '
                               f'{self.table_name}.{self.column_name} = "{value}"').fetchall()

        con = sql.connect(db_name)
        cur = con.cursor()
        if old_value != ['']:
            for v in o_value:
                temp = count_values_uses(v)
                delete_from_link_table(v)
                if len(temp) == 1:
                    delete_from_table(v)
        else:
            cur.execute(f'DELETE FROM {self.link_table_name} WHERE _main_id = {r_id} AND '
                        f'{self.table_name.casefold()}_id = 1')
        con.commit()
        con.close()
