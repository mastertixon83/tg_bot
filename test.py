def parse_value(data):
    # Проверяем, является ли это кортежем
    if isinstance(data, tuple) and len(data) == 1:
        value = data[0]

        # Проверяем, является ли значение набором (set)
        if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
            # Убираем фигурные скобки и разбиваем строку по запятой
            return list(map(int, value.strip('{}').split(',')))
        else:
            # Убираем скобки и кавычки, затем преобразуем к целому числу
            return int(value)
    raise ValueError("Input must be a single-element tuple")


# Примеры
data1 = ('156',)
data2 = ('{197,198,199}',)

# Парсим значения
parsed_value1 = parse_value(data1)
parsed_value2 = parse_value(data2)

print(f"Parsed value from data1: {type(parsed_value1)}")  # Output: 156
print(f"Parsed values from data2: {type(parsed_value2)}")  # Output: [197, 198, 199]

if type(parsed_value2) == list: print('OK')
