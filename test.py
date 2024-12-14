options = 'Один, Два, Три'
option_list = [option.strip() for option in options.split(",")]

print(option_list)
print(option_list.index("Два"))