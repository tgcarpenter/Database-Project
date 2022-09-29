import sqlite3 as sql


class Database:
    def __init__(self, name):  # Main table is made with creation of class instance
        self.name = name + '.db'
        self.text_table_count = 1  # defines current name for text tables in column creation
        self.list_table_count = 1  # defines current name for list tables in column creation
        self.row_count = 0  # defines current row count
        self.class_count = 0  # defines position of created column classes in column_classes list
        # what if two columns are named the same thing? ugh!! <- fixed because I refer to them by position not name
        self.column_classes = []  # contains all the column class objects (in order of columns)
        con = sql.connect(self.name)
        cur = con.cursor()
        try:
            cur.execute('CREATE TABLE Main (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE)')
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

    def change_db_name(self, newname):
        self.name = newname

    def change_column_name(self, c_id, newname):  # Rework Column names
        con = sql.connect(self.name)
        cur = con.cursor()
        cur.execute('ALTER TABLE {table_name} RENAME COLUMN {column_name} TO {newname}'
                    ''.format(table_name=self.column_classes[c_id].table_name,
                              column_name=self.column_classes[c_id].column_name, newname="[" + newname + "]"))
        self.column_classes[c_id].column_name = "[" + newname + "]"
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

    def delete_row(self, old_values: list, r_id):
        self.row_count -= 1
        for column, old_val in zip(self.column_classes, old_values):
            if column.table_name[0] == "T":
                column.delete_row(self.name, old_val)
            elif column.table_name[0] == "L":
                column.delete_row(self.name, old_val, None, r_id)
        con = sql.connect(self.name)
        cur = con.cursor()
        cur.execute(f'DELETE FROM Main WHERE _rowid_ = {r_id}')
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
            if column.table_name[0] == 'L':
                cur.execute(f'INSERT INTO {column.link_table_name} (main_id) VALUES ((SELECT MAX(id) FROM Main))')
        con.commit()
        con.close()

    def get_column_headers(self):
        return [column.column_name[1:-1] for column in self.column_classes]

    def general_query(self, start, end):
        select_table_columns = ''
        joined_tables = ''
        on_parameters = ''
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
            if column.table_name[0] == 'T':  # Generating join tables and on parameters
                joined_tables += 'JOIN ' + column.table_name + ' '
                if switch:
                    switch = False
                    on_parameters += f'ON Main.{column.table_name.casefold()}_id = {column.table_name}.id '
                else:
                    on_parameters += f'AND Main.{column.table_name.casefold()}_id = {column.table_name}.id '
            elif column.table_name[0] == 'L':
                joined_tables += f'JOIN (SELECT DISTINCT {column.link_table_name}.main_id, ' \
                                 f'group_concat({column.table_name}.{column.column_name}, ", ") OVER (PARTITION BY ' \
                                 f'Main.id) AS {column.column_name} FROM Main JOIN {column.table_name} JOIN ' \
                                 f'{column.link_table_name} ON Main.id = {column.link_table_name}.main_id AND ' \
                                 f'{column.table_name}.id = ' \
                                 f'{column.link_table_name}.{column.table_name.casefold()}_id) AS {column.table_name}' \
                                 f' '
                if switch:
                    switch = False
                    on_parameters += f'ON Main.id = {column.table_name}.main_id '
                else:
                    on_parameters += f'AND Main.id = {column.table_name}.main_id '
            count += 1
        query = cur.execute(f'SELECT {select_table_columns} FROM Main {joined_tables} {on_parameters} '
                            f'WHERE Main._rowid_ >= {start} AND Main._rowid_ <= {end}').fetchall()
        con.close()
        return query


class ColumnInteger:
    def __init__(self, name, db_name):  # Inserts column into main table One-to-one
        self.column_name = "[" + name + "]"
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

    def insert_into(self, db_name, *args):  # not sure this is used
        values = ''
        count = 0
        for item in args:
            if type(item) == int():
                return
            elif count == 0:
                values = str(item)
            else:
                values = values + ', ' + str(item)
            count += 1  # <-- UP should be in input class
        con = sql.connect(db_name)
        cur = con.cursor()
        cur.execute(f'INSERT INTO Main ({self.column_name}) VALUES (?)', (values,))
        con.commit()
        con.close()

    def update(self, db_name, old_value, new_value, r_id):
        con = sql.connect(db_name)
        cur = con.cursor()
        if not new_value:
            cur.execute(f'UPDATE Main SET {self.column_name} = Null '
                        f'WHERE _rowid_ = {r_id}')
        else:
            cur.execute(f'UPDATE Main SET {self.column_name} = "{new_value}" WHERE _rowid_ = {r_id}')
        con.commit()
        con.close()


class ColumnText:
    def __init__(self, name, db_name, table_count):  # Creates a one-to-many relation between main table and text table
        self.column_name = "[" + name + "]"
        self.table_name = 'TextTable' + str(table_count)
        con = sql.connect(db_name)
        cur = con.cursor()
        cur.execute(f'CREATE TABLE {self.table_name} (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, '
                    f'{self.column_name} TEXT UNIQUE)')
        cur.execute(f'INSERT INTO {self.table_name} DEFAULT VALUES')
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
            temp = cur.execute(f'SELECT Main.id FROM Main JOIN {self.table_name} '
                               f'WHERE Main.{self.table_name.casefold() + "_id"} = {self.table_name}.id '
                               f'AND {self.table_name}.{self.column_name} = {temp_old_value}').fetchall()
            if len(temp) == 1:
                cur.execute(f'DELETE FROM {self.table_name} WHERE {self.column_name} = {temp_old_value}')
        con.commit()
        con.close()

    def insert_into(self, db_name, *args):
        values = ''
        count = 0
        for item in args:
            if item in ['', ', ']:  # Prevents blank string (Probably redundant)
                continue
            elif count == 0:
                values = str(item)
            else:
                values += ', ' + str(item)  # <-- UP should be in input class
        con = sql.connect(db_name)
        cur = con.cursor()
        try:
            cur.execute(f'INSERT INTO {self.table_name} ({self.column_name}) VALUES (?)', (values,))
        except:
            pass
        cur.execute(f'INSERT INTO Main ({self.table_name.casefold() + "_id"}) SELECT id FROM {self.table_name} '
                    f'WHERE {self.column_name} = "{values}"')
        con.commit()
        con.close()

    def update(self, db_name, old_value, new_value, r_id):
        con = sql.connect(db_name)
        cur = con.cursor()
        if old_value:
            temp_old_value = '"' + old_value + '"'
        else:
            temp_old_value = 'NULL'
        temp = cur.execute(f'SELECT Main.id FROM Main JOIN {self.table_name} '
                           f'WHERE Main.{self.table_name.casefold() + "_id"} = {self.table_name}.id '
                           f'AND {self.table_name}.{self.column_name} = {temp_old_value}').fetchall()
        if not new_value:
            cur.execute(f'UPDATE Main SET {self.table_name.casefold()}_id = 1 WHERE _rowid_ = {r_id}')
            if len(temp) == 1 and temp_old_value != "NULL":
                cur.execute(f'DELETE FROM {self.table_name} WHERE {self.column_name} = {temp_old_value}')
        elif len(temp) != 1:
            try:
                cur.execute(f'INSERT INTO {self.table_name} ({self.column_name}) VALUES (?)', (new_value,))
            except:
                pass
            cur.execute(f'UPDATE Main SET {self.table_name.casefold()}_id = (SELECT {self.table_name}.id '
                        f'FROM {self.table_name} WHERE {self.table_name}.{self.column_name} = "{new_value}") '
                        f'WHERE _rowid_ = {r_id}')
        else:
            cur.execute(f'UPDATE {self.table_name} SET {self.column_name} = (?) '
                        f'WHERE {self.column_name} = "{old_value}"', (new_value,))
        con.commit()
        con.close()


class ColumnList:
    def __init__(self, name, db_name, table_count):  # Creates a many-to-many relation between main table and list table
        self.column_name = "[" + name + "]"
        self.table_name = 'ListTable' + str(table_count)
        self.link_table_name = 'LinkTable' + str(table_count)
        con = sql.connect(db_name)
        cur = con.cursor()
        cur.execute(f'CREATE TABLE {self.table_name} '  # create list table
                    f'(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, {self.column_name} TEXT UNIQUE)')
        cur.execute(f'INSERT INTO {self.table_name} DEFAULT VALUES')
        cur.execute(
            f'CREATE TABLE {self.link_table_name} ({self.table_name.casefold() + "_id"} INTEGER NOT NULL '  # Create link table
            f'DEFAULT 1, main_id INTEGER NOT NULL, PRIMARY KEY ({self.table_name.casefold() + "_id"}, main_id))')
        cur.execute(f'INSERT INTO {self.link_table_name} (main_id) SELECT Main.id FROM Main')
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
        cur.execute(f'INSERT INTO {self.link_table_name} (main_id) VALUES ({row_number})')
        con.commit()
        con.close()

    def insert_into(self, db_name, *args):  # Might be for only one value at a time, for look insert_into through list
        con = sql.connect(db_name)
        cur = con.cursor()
        cur.execute('INSERT INTO Main DEFAULT VALUES')
        for value in args:
            try:
                cur.execute(f'INSERT INTO {self.table_name} ({self.column_name}) VALUES (?)', (value,))
            except:
                pass
            cur.execute(f'INSERT INTO {self.link_table_name} (main_id, {self.table_name.casefold() + "_id"}) '
                        f'SELECT Main.id, {self.table_name + ".id"} FROM {self.table_name} JOIN Main '
                        f'WHERE {self.column_name} = "{value}" '
                        f'AND (SELECT Main.id FROM Main ORDER BY Main.id DES LIMIT 1)')
        con.commit()
        con.close()

    def update(self, db_name, old_value, new_value, r_id):
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
            cur.execute(f'INSERT INTO {self.link_table_name} (main_id, {self.table_name.casefold()}_id) '
                        f'SELECT Main.id, {self.table_name}.id FROM {self.table_name} JOIN Main '
                        f'WHERE {self.table_name}.{self.column_name} = "{value}" AND Main.id = {r_id}')

        con = sql.connect(db_name)
        cur = con.cursor()
        r_id = cur.execute(f'SELECT id FROM Main WHERE _rowid_ = {r_id}').fetchone()[0]
        if new_value != [''] and new_value is not None:
            for v in n_value:
                insert_new_list_value(v)
        else:
            cur.execute(f'INSERT INTO {self.link_table_name} (main_id, {self.table_name.casefold()}_id) '
                        f' VALUES ({r_id}, 1)')
        con.commit()
        con.close()

    def delete_row(self, db_name, old_value, o_value, r_id):

        def delete_from_link_table(value):
            cur.execute(f'DELETE FROM {self.link_table_name} WHERE main_id = {r_id} AND '
                        f'{self.table_name.casefold()}_id = (SELECT id FROM {self.table_name}'
                        f' WHERE {self.column_name} = "{value}")')

        def delete_from_table(value):
            cur.execute(f'DELETE FROM {self.table_name} WHERE {self.column_name} = "{value}"')

        def count_values_uses(value):
            return cur.execute(f'SELECT {self.link_table_name}.main_id, '
                               f'{self.link_table_name}.{self.table_name.casefold()}_id FROM {self.link_table_name} '
                               f'JOIN {self.table_name} '
                               f'WHERE {self.link_table_name}.{self.table_name.casefold()}_id = {self.table_name}.id '
                               f'AND {self.table_name}.{self.column_name} = "{value}"').fetchall()

        con = sql.connect(db_name)
        cur = con.cursor()
        r_id = cur.execute(f'SELECT id FROM Main WHERE _rowid_ = {r_id}').fetchone()[0]
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
            cur.execute(f'DELETE FROM {self.link_table_name} WHERE main_id = {r_id} AND '
                        f'{self.table_name.casefold()}_id = 1')
        con.commit()
        con.close()


if __name__ == '__main__':
    db1 = Database('CL')
    db1.add_column_text('Name')
    db1.add_column_text('Composer Name')
    db1.add_column_text('Arranger Name')
    db1.add_column_integer('Number of Pieces')
    db1.add_column_list('Voicing')
