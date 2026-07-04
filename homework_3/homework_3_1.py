# --- Рядки (Strings) ---
# Напишіть функцію, яка приймає рядок і повертає його довжину
def string_length(string):
    return len(string)

print(string_length("Hello, World!"))

# Створіть функцію, яка приймає два рядки і повертає об'єднаний рядок
def combined_string(string1, string2):
    return string1 + string2

print(combined_string("Hello, ", "World!"))

# --- Числа (Int/float) ---
# Реалізуйте функцію, яка приймає число і повертає його квадрат
def number_square(number):
    return number ** 2

print(number_square(6))

# Створіть функцію, яка приймає два числа і повертає їхню суму
def sum_of_numbers(number1, number2):
    return number1 + number2

print(sum_of_numbers(5, 4))

# Створіть функцію яка приймає 2 числа типу int, виконує операцію ділення та повертає чілу частину і залишок
def divide_numbers(number1, number2):
    integer, remainder = divmod(number1, number2)

    return integer, remainder

print(divide_numbers(10, 3))

# --- Списки (Lists) ---
# Напишіть функцію для обчислення середнього значення списку чисел
def average_number(numbers_list):
    return sum(numbers_list) / len(numbers_list)

print(average_number([1, 2, 3, 4, 5]))

# Реалізуйте функцію, яка приймає два списки і повертає список, який містить спільні елементи обох списків
def combined_list(list1, list2):
    return list(set(list1) & set(list2))

print(combined_list([1, 2, 3], [3, 4, 5, 6]))

# --- Словники (Dictionaries) ---
# Створіть функцію, яка приймає словник і виводить всі ключі цього словника
def dictionary_keys(dictionary):
    return list(dictionary.keys())

print(dictionary_keys({'a': 1, 'b': 2, 'c': 3}))

# Реалізуйте функцію, яка приймає два словники і повертає новий словник, який є об'єднанням обох словників
def combined_dictionary(dictionary1, dictionary2):
    return dictionary1 | dictionary2

print(combined_dictionary({'a': 1, 'b': 2, 'c': 3}, {'d': 4, 'e': 5}))

# --- Множини (Sets) ---
# Напишіть функцію, яка приймає дві множини і повертає їхнє об'єднання
def combined_set(set1, set2):
    return set1.union(set2)

print(combined_set({1, 2, 3}, {3, 4, 5, 6}))

# Створіть функцію, яка перевіряє, чи є одна множина підмножиною іншої
def subset(set1, set2):
    intersection_set = set1.intersection(set2)
    if intersection_set == set2:
        return True
    else:
        return False

print(subset({1, 2, 3, 4, 5}, {1, 4}))

# --- Умовні вирази та цикли ---
# Реалізуйте функцію, яка приймає число і виводить "Парне", якщо число парне, і "Непарне", якщо непарне
def is_even(number):
    if number % 2 == 0:
        return "Парне"
    else:
        return "Непарне"

print(is_even(3))
print(is_even(4))

# Створіть функцію, яка приймає список чисел і повертає новий список, що містить тільки парні числа
def is_even_list(user_list):
    list_with_even = []
    for number in user_list:
        if number % 2 == 0:
            list_with_even.append(number)

    return list_with_even

print(is_even_list([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))

# Написати лямбда-функцію визначальну парне/непарне
is_even_number = lambda number: "парне" if number % 2 == 0 else "не парне"
print(is_even_number(3))
print(is_even_number(4))
