import sqlite3 as sql


class Database:
    def __init__(self, name):  # Main table is made with creation of class instance
        self.name = name + '.db'
        self.text_table_count = 1  # defines current name for text tables in column creation
        self.list_table_count = 1  # defines current name for list tables in column creation
        self.row_count = 0  # defines current row count
        self.class_count = 0  # defines position of created column classes in column_classes list  -- useless?
        # what if two columns are named the same thing? ugh!! <- fixed because I refer to them by position not name
        self.column_classes = []  # contains all the column class objects (in order of columns)
        con = sql.connect(self.name)
        cur = con.cursor()
        try:
            cur.execute('CREATE TABLE Main (_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE)')
        except:
            pass
        con.commit()
        con.close()

    def delete_database(self):
        con = sql.connect(self.name)
        cur = con.cursor()
        cur.execute(f'DROP DATABASE {self.name}')
        con.commit()
        con.close()

    def change_db_name(self, newname):  # this doesn't work
        self.name = newname

    def change_column_name(self, c_id, newname):  # Rework Column names
        con = sql.connect(self.name)
        cur = con.cursor()
        cur.execute('ALTER TABLE {table_name} RENAME COLUMN {column_name} TO {newname}'
                    ''.format(table_name=self.column_classes[c_id].table_name,
                              column_name=self.column_classes[c_id].column_name, newname="[_" + newname + "]"))
        self.column_classes[c_id].column_name = "[_" + newname + "]"
        con.commit()
        con.close()

    def temp(self):
        for column in self.column_classes:
            if column.table_name[1] == 'T':
                con = sql.connect(self.name)
                cur = con.cursor()
                cur.execute(f'CREATE INDEX {column.table_name}index ON {column.table_name} ({column.column_name})')
                con.commit()
                con.close()

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

    def delete_column(self, c_id):  #
        self.column_classes[c_id].delete_column(self.name)
        self.column_classes.remove(self.column_classes[c_id])

    def move_column(self, oIndex, nIndex):
        t_column = self.column_classes.pop(oIndex)
        self.column_classes.insert(nIndex, t_column)

    def delete_row(self, old_values: list, r_id):
        self.row_count -= 1
        for column, old_val in zip(self.column_classes, old_values):
            if column.table_name[1] == "T":
                column.delete_row(self.name, old_val)
            elif column.table_name[1] == "L":
                column.delete_row(self.name, old_val, None, r_id)
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

    def input_into_column(self, c_id, *args):  # Not sure what this is for
        self.column_classes[c_id].insert_into(self.name, args)
        self.row_count += 1
        for column in self.column_classes:
            if column != self.column_classes[c_id] and isinstance(column, ColumnList):
                column.add_default_to_link_table(self.name, self.row_count)

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

    def autofill_query(self, search):
        case = "CASE "
        col = "FROM Main JOIN "
        con = sql.connect(self.name)
        cur = con.cursor()
        for column in self.column_classes:
            case += f"WHEN {column.table_name}.{column.column_name} LIKE '{search}%' " \
                    f"THEN TRIM({column.table_name}.{column.column_name}, ' %') "
            if column.table_name == "Main":
                continue
            col += f"{column.table_name} JOIN "
        autofill = cur.execute(f'SELECT DISTINCT {case} END C {col[:-6]} '
                               f'WHERE C IS NOT NULL AND C != "{search}" ORDER BY C').fetchall()
        print("auto", autofill)
        return autofill

    def general_query(self, start=int, end=int, search=False):  # search holds the text to search for. start/end will
        select_table_columns = ''                               # not be given if search is given
        joined_tables = ''
        on_parameters = ''
        where = 'WHERE ('
        count = 1
        switch = True
        con = sql.connect(self.name)
        cur = con.cursor()
        for column in self.column_classes:
            select_table_columns += column.table_name + '.' + column.column_name  # Generating Columns Select
            if count == len(self.column_classes):
                select_table_columns += ' '
            else:
                select_table_columns += ', '
            if column.table_name[1] == 'T':  # Generating join tables and on parameters
                joined_tables += 'JOIN ' + column.table_name + ' '
                if switch:
                    switch = False
                    on_parameters += f'ON Main.{column.table_name.casefold()}_id = {column.table_name}._rowid_ '
                else:
                    on_parameters += f'AND Main.{column.table_name.casefold()}_id = {column.table_name}._rowid_ '
            elif column.table_name[1] == 'L':
                joined_tables += f'JOIN (SELECT DISTINCT {column.link_table_name}._main_id, ' \
                                 f'group_concat({column.table_name}.{column.column_name}, ", ") OVER (PARTITION BY ' \
                                 f'Main._id) AS {column.column_name} FROM Main JOIN {column.table_name} JOIN ' \
                                 f'{column.link_table_name} ON Main._id = {column.link_table_name}._main_id AND ' \
                                 f'{column.table_name}._rowid_ = ' \
                                 f'{column.link_table_name}.{column.table_name.casefold()}_id) AS {column.table_name}' \
                                 f' '
                if switch:
                    switch = False
                    on_parameters += f'ON Main._id = {column.table_name}._main_id '
                else:
                    on_parameters += f'AND Main._id = {column.table_name}._main_id '
            if search:
                where += fr'{column.column_name} LIKE "%{search}%" ESCAPE "\" OR '
            count += 1
        if search:
            where = where[:-3] + ')'
        else:
            where = f'WHERE Main._id >= {start} AND Main._id <= {end}'
        query = cur.execute(fr'SELECT Main._id, {select_table_columns} FROM Main {joined_tables} {on_parameters} '
                            fr'{where}').fetchall()
        con.close()
        return query


class ColumnInteger:
    def __init__(self, name, db_name):  # Inserts column into main table One-to-one
        self.column_name = "[_" + name + "]"
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

    def update(self, db_name, old_value, new_value, r_id):
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


class ColumnText:
    def __init__(self, name, db_name, table_count):  # Creates a one-to-many relation between main table and text table
        self.column_name = "[_" + name + "]"
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
            cur.execute(f'UPDATE {self.table_name} SET {self.column_name} = (?) '
                        f'WHERE {self.column_name} = "{old_value}"', (new_value,))
        con.commit()
        con.close()


class ColumnList:
    def __init__(self, name, db_name, table_count):  # Creates a many-to-many relation between main table and list table
        self.column_name = "[_" + name + "]"
        self.table_name = '_ListTable' + str(table_count)
        self.link_table_name = '_LinkTable' + str(table_count)
        con = sql.connect(db_name)
        cur = con.cursor()
        cur.execute(f'CREATE TABLE {self.table_name} '  # create list table
                    f'({self.column_name} TEXT UNIQUE)')
        cur.execute(f'INSERT INTO {self.table_name} DEFAULT VALUES')
        cur.execute(
            f'CREATE TABLE {self.link_table_name} ({self.table_name.casefold() + "_id"} INTEGER NOT NULL '  # Create link table
            f'DEFAULT 1, _main_id INTEGER NOT NULL, PRIMARY KEY ({self.table_name.casefold() + "_id"}, _main_id))')
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

    def add_default_to_link_table(self, db_name, row_number): # not sure what this is for either
        con = sql.connect(db_name)
        cur = con.cursor()
        cur.execute(f'INSERT INTO {self.link_table_name} (_main_id) VALUES ({row_number})')
        con.commit()
        con.close()

    def update(self, db_name, old_value, new_value, r_id):
        if new_value is None:
            new_value = ''
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
        if not o_value:
            old_value = old_value.split(", ")
            o_value = old_value
        if old_value != [''] and old_value is not None:
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
