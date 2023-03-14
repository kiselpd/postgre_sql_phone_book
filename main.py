import psycopg2
from psycopg2 import Error


class PhoneBookDatabase:

    def __init__(self, database: str, user: str, password: str):
        self.__database = database
        self.__user = user
        self.__password = password
    

    def connect(self):
        try:
            self.__conn = psycopg2.connect(database=self.__database, user=self.__user, password=self.__password)
        except(Exception, Error) as error:
            print("Ошибка соединения с PostgreSQL", error)


    def disconnect(self):
        try:
            self.__conn.close()
        except(Exception, Error) as error:
            print("Ошибка соединения с PostgreSQL", error)


    def create_tables(self):
        with self.__conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS client(
                    id SERIAL PRIMARY KEY,
                    first_name VARCHAR(40) NOT NULL,
                    second_name VARCHAR(40) NOT NULL,
                    email VARCHAR(50) NOT NULL UNIQUE
                );
                """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS phone_number(
                    id SERIAL PRIMARY KEY,
                    number VARCHAR(20) NOT NULL UNIQUE,
                    id_client INTEGER NOT NULL REFERENCES client(id)
                );
                """)

            self.__conn.commit()


    def drop_tables(self):
        try:
            with self.__conn.cursor() as cur:
                cur.execute("""
                    DROP TABLE phone_number;
                    DROP TABLE client;
                    """)
                self.__conn.commit()
        except(Exception, Error) as error:
            print("Таблиц не существует!", error)
            self.__conn.rollback()


    def add_client(self, first_name: str, second_name: str, email: str):
        answer = None
        try:
            with self.__conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO client(first_name, second_name, email)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                    """, (first_name, second_name, email))

                answer = cur.fetchone()[0]
                self.__conn.commit()
        except(Exception, Error) as error:
            print("Клиент с таким email уже существует!", error)
            self.__conn.rollback()
        finally:
            return answer


    def add_phone_number(self, number: str, id_client: str):
        answer = None
        try:
            with self.__conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO phone_number(number, id_client)
                    VALUES (%s, %s)
                    RETURNING id;
                    """, (number, id_client))

                answer = cur.fetchone()[0]
                self.__conn.commit()
        except(Exception, Error) as error:
            print("Такой номер уже существует!", error)
            self.__conn.rollback()
        finally:
            return answer


    def change_client_info(self, id: int, new_first_name: str, new_second_name: str, new_email: str, new_number: str):
        with self.__conn.cursor() as cur:
            cur.execute("""
                UPDATE client
                SET first_name=%s, second_name=%s, email=%s
                WHERE id=%s
                """, (new_first_name, new_second_name, new_email, id))
            
            cur.execute("""
                UPDATE phone_number
                SET number=%s
                WHERE id_client=%s
                """, (new_number, id))
                
            self.__conn.commit()


    def __delete_all_numbers(self, id_client: str):
        with self.__conn.cursor() as cur:
            cur.execute("""
                DELETE FROM phone_number
                WHERE id_client=%s;
                """, (id_client,))
                
            self.__conn.commit()


    def delete_number(self, id_client: int, number: str=None):
        if number is None:
            self.__delete_all_numbers(id_client)
        else:
            with self.__conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM phone_number
                    WHERE id_client=%s AND number=%s;
                    """, (id_client, number))
                    
                self.__conn.commit()


    def delete_client(self, id_client: int):
        self.__delete_all_numbers(id_client)

        with self.__conn.cursor() as cur:
            cur.execute("""
                DELETE FROM client
                WHERE id=%s;
                """, (id_client,))
                    
            self.__conn.commit()

    
    def __find_client_with_name(self, first_name: str, second_name: str):
        with self.__conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM client
                WHERE first_name=%s AND second_name=%s;
                """, (first_name, second_name))
            client = cur.fetchone()

            cur.execute("""
                SELECT number FROM phone_number
                WHERE id_client=%s;
                """, (client[0],))
            number = cur.fetchone()[0]

            self.__conn.commit()
        
        client = list(client)
        client.append(number)
        return client
    

    def __find_client_with_email(self, email: str):
        with self.__conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM client
                WHERE email=%s;
                """, (email,))
            client = list(cur.fetchone())

            cur.execute("""
                SELECT number FROM phone_number
                WHERE id_client=%s;
                """, (client[0],))
            
            number = cur.fetchone()[0]
            self.__conn.commit()
        
        client.append(number)
        return client
    

    def __find_client_with_number(self, number: str):
        with self.__conn.cursor() as cur:
            cur.execute("""
                SELECT id_client FROM phone_number
                WHERE number=%s;
                """, (number,))
            answer = cur.fetchone()[0]

            if answer:
                cur.execute("""
                SELECT * FROM client
                WHERE id=%s;
                """, (answer,))
                answer = cur.fetchone()

            self.__conn.commit()
        
        return list(answer) + [number]
    

    def find_client(self, first_name: str=None, second_name: str=None, email: str=None, number: str=None):
        if number is not None:
            return self.__find_client_with_number(number)

        if email is not None:
            return self.__find_client_with_email(email)
        
        if first_name is not None and second_name is not None:
            return self.__find_client_with_name(first_name, second_name)
        
        return None


def solution():
    database = input("Введите название БД: ")
    user = input("Введите имя пользователя: ")
    password = input("Введите пароль: ")
    
    ph_book = PhoneBookDatabase(database, user, password)
    ph_book.connect()

    while(True):
        menu_point = int(input("""
            Введите номер действия:
            1. Создать таблицы
            2. Удалить таблицы
            3. Добавить клиента
            4. Добавить телефон для существующего клиента
            5. Изменить данные о клиенте
            6. Удалить телефон для существующего клиента
            7. Удалить существующего клиента
            8. Найти клиента
            9. Выход
        """))

        if menu_point==1:
            ph_book.create_tables()
        elif menu_point==2:
            ph_book.drop_tables()
        elif menu_point==3:
            first_name = input("Введите имя: ")
            second_name = input("Введите фамилию: ")
            email = input("Введите email: ")
            print("id нового пользователя:", ph_book.add_client(first_name, second_name, email))
        elif menu_point==4:
            number = input("Введите номер: ")
            id = int(input("Введите id клиента: "))
            print("id нового номера: ", ph_book.add_phone_number(number, id))
        elif menu_point==5:
            id = int(input("Введите id клиента: "))
            new_first_name = input("Введите имя: ")
            new_second_name = input("Введите фамилию: ")
            new_email = input("Введите email: ")
            new_number = input("Введите номер: ")
            ph_book.change_client_info(id, new_first_name, new_second_name, new_email, new_number)
        elif menu_point==6:
            id = int(input("Введите id клиента: "))
            number = input("Введите номер: ")
            ph_book.delete_number(id, number)
        elif menu_point==7:
            id = int(input("Введите id клиента: "))
            ph_book.delete_client(id)
        elif menu_point==8:
            first_name = input("Введите имя: ")
            second_name = input("Введите фамилию: ")
            email = input("Введите email: ")
            number = input("Введите номер: ")
            print(ph_book.find_client(None if first_name=="" else first_name, None if second_name=="" else second_name,\
                                                   None if email=="" else email, None if number=="" else number))
        elif menu_point==9:
            break

    ph_book.disconnect()



if __name__=="__main__":
    solution()