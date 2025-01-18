from medicalgrouplibrary.unificator import add_synonym
from medicalgrouplibrary.units import *

# add_synonym("Гемоглобін (HBC)", "Гемоглобин")
# x = get_unification_name("HG")
# print(x)


#
# zx = add_unit(1, "г/дл", False)
#
wx = get_units_for_standard_name(1)
print(f'get_units_for_standard_name: {wx}')

# x = get_standard_unit_for_standard_name(1)
# print(x)

# z = get_conversions_for_unit("г/дл")
# print(z)

# e = add_unit_conversation(2, 1, "x * 10", 1)

#
# result = convert_to_standard_unit(100, 2, 1)
# print(result)


result = calculate_conversion(12.5, 'мг/мл', 'г/100мл', standard_name_id=1)

if 'error' in result:
    print(result['error'])
else:
    print(f"Значення: {result['value']}")
    print("Шлях конверсії:", result['path'])
