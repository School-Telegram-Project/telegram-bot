'''
Shared utils
Общие утилиты
'''

from collections.abc import Iterable


def value_in_dict(key: str, dictionary: dict, value = None) -> bool:
    '''
    Check if value type exists in dictionary
    If value is set, checks if it is equal

    Проверяет, есть ли тип значения в словаре
    Если указано значение, проверяет, если это значение равно ему
    '''
    if key not in dictionary:
        return False
    if value is None:
        return True

    return (
        value == dictionary[key] or
        (isinstance(dictionary[key], Iterable) and value in dictionary[key])
    )

def add_value(key, value, dictionary: dict) -> None:
    '''
    Add `value` to `dictionary[key]`

    Добавить значение `value` к `dictionary[key]`
    '''
    if key in dictionary:
        match dictionary[key]:
            case list():
                if isinstance(value, Iterable):
                    dictionary[key].extend(value)
                else:
                    dictionary[key].append(value)
            case set():
                dictionary[key].add(value)
            case _:
                dictionary[key] += value
    else:
        dictionary[key] = value
