# This is a fake secret for testing purposes
API_KEY = "a_super_long_and_very_secret_api_key_for_testing_12345"

def well_documented_function():
    """This function is properly documented."""
    print("hello")

def undocumented_function(p):
    if p:
        return True
    return False

def overly_complex_function(h):
    if h:
        if h:
            if h:
                if h:
                    if h:
                        if h:
                            if h:
                                if h:
                                    if h:
                                        if h:
                                            if h:
                                                print("ok")
def inefficient_string_builder(my_list):
    """Builds a string badly."""
    final_string = ""
    for item in my_list:
        final_string += str(item) + ","
    return final_string