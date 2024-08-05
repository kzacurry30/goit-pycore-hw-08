import re
from collections import UserDict
from datetime import datetime, timedelta
import pickle

# Клас Field и його підкласи
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

class Name(Field):
    def __init__(self, value):
        super().__init__(value)
        if not value:
            raise ValueError("Name is a mandatory field.")

class Phone(Field):
    def __init__(self, value):
        super().__init__(value)
        if not self.validate_phone(value):
            raise ValueError("Phone number must be 10 digits.")

    @staticmethod
    def validate_phone(phone):
        return re.fullmatch(r'\d{10}', phone) is not None

class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y")
            super().__init__(value)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

# Клас Record
class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        self.phones = [p for p in self.phones if p.value != phone]

    def edit_phone(self, old_phone, new_phone):
        if not any(p.value == old_phone for p in self.phones):
            raise ValueError(f"Phone number {old_phone} not found.")
        self.remove_phone(old_phone)
        self.add_phone(new_phone)

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def __str__(self):
        phones = ", ".join(str(phone) for phone in self.phones)
        return f"Name: {self.name}, Phones: {phones}, Birthday: {self.birthday if self.birthday else 'N/A'}"

# Клас AddressBook
class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.today()
        upcoming_birthdays = []
        for record in self.data.values():
            if record.birthday:
                bday = datetime.strptime(record.birthday.value, "%d.%m.%Y").replace(year=today.year)
                if today <= bday <= (today + timedelta(days=7)):
                    if bday.weekday() >= 5:  # If the birthday falls on weekend
                        bday = bday + timedelta(days=(7 - bday.weekday()))
                    upcoming_birthdays.append({"name": record.name.value, "birthday": bday.strftime("%d.%m.%Y")})
        return upcoming_birthdays

    def __str__(self):
        return '\n'.join(str(record) for record in self.data.values())

# Функції для серіалізації/десеріалізації
def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено

# Декоратор для обробки помилок
def input_error(handler):
    def wrapper(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except (ValueError, IndexError) as e:
            return str(e)
    return wrapper

# Функції обробники команд
@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_phone(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return f"Phone number changed for {name}."
    return f"Contact {name} not found."

@input_error
def show_phones(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record:
        return f"{name}: {', '.join(str(phone) for phone in record.phones)}"
    return f"Contact {name} not found."

def show_all_contacts(args, book: AddressBook):
    return str(book)

@input_error
def add_birthday(args, book: AddressBook):
    name, birthday, *_ = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return f"Birthday added for {name}."
    return f"Contact {name} not found."

@input_error
def show_birthday(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday is on {record.birthday}."
    elif record:
        return f"No birthday set for {name}."
    return f"Contact {name} not found."

@input_error
def birthdays(args, book: AddressBook):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if upcoming_birthdays:
        return "\n".join([f"{item['name']}: {item['birthday']}" for item in upcoming_birthdays])
    return "No upcoming birthdays."

# Основна функція
def parse_input(user_input):
    return user_input.split()

def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            save_data(book)  # Сохранить данные перед выходом
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_phone(args, book))

        elif command == "phone":
            print(show_phones(args, book))

        elif command == "all":
            print(show_all_contacts(args, book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
