import re

# Elmininates highly erronious characters 
def space_clone_less(str):
    return ''.join(re.split('_|-| |\.', str)).lower()

# Counts highly erronious characters 
def space_twin_cou(str):
    return len(re.split('_|-| |\.', str)) - 1

