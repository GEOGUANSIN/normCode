from string import Template
from copy import copy
from _reference import Reference, cross_product, element_action
from _methods._demo import strip_element_wrapper, wrap_element_wrapper

def calculate_list_depth(lst):
    """Calculate the depth of a nested list structure"""
    if not isinstance(lst, list):
        return 0
    if not lst:
        return 1
    return 1 + max(calculate_list_depth(item) for item in lst)

def find_share_axes(references):
    """
    Find the shared axes between all references.
    """
    if not references:
        return []
    shared_axes = set(references[0].axes)
    for ref in references[1:]:
        shared_axes.intersection_update(ref.axes)
    return list(shared_axes)


def flatten_element(reference):
    """
    Flatten the element of the reference.
    """

    def flatten_all_list(nested_list):
        if not isinstance(nested_list, list):
            return [nested_list]
        return sum((flatten_all_list(item) for item in nested_list), [])

    return element_action(flatten_all_list, [reference])

def annotate_element(reference, annotation_list):

        def annotate_list(list):
            annotation_dict = {}
            for i, annotation in enumerate(annotation_list):
                annotation_dict[annotation] = list[i]
            return annotation_dict
        
        return element_action(annotate_list, [reference])
    


def demonstrate_normcode_simiple_or():
    """
    Demonstrate NormCode slicing patterns using the Reference class.
    This implements the complex slicing operations shown in the user's examples.
    """
    print("=== NormCode Slicing Pattern Demonstration ===\n")
    
    # Pattern 1: [ {A} or {B}]
    print("1. Pattern: [{A} or {B}]")
    print("   |ref. [%D[0]=%[%a1, %b1, %b2]], %D[1]=%[%a2, %b1, %b2]]")
    print("   <= &across(A; B)")
    print("   <- A |ref. [%D[0]=[%A[0]=%a1]], [%D[1]=[%A[1]=%a2]]]")
    print("   <- B |ref. [%D[0]=[%B[0]=%b1, %B[1]=%b2]], [%D[1]=[%B[0]=%b1, %B[1]=%b2]]]")
    
    # Create reference A with shape (2,1) - two elements, each containing one value
    A_ref = Reference(
        axes=['D', 'A'],
        shape=(2, 1),
        initial_value=0
    )
    A_ref.tensor = [['a1'], ['a2']]
    
    print(f"\nReference A shape: {A_ref.shape}")
    print(f"Reference A axes: {A_ref.axes}")
    print(f"Reference A data:")
    print(A_ref.tensor)
    
    # Create reference B with shape (1,2) - one element containing two values
    B_ref = Reference(
        axes=['D', 'B'],
        shape=(2, 2),
        initial_value=0
    )
    B_ref.tensor = [['b1', 'b2'], ['b1', 'b2']]

    print(f"\nReference B shape: {B_ref.shape}")
    print(f"Reference B axes: {B_ref.axes}")
    print(f"Reference B data:")
    print(B_ref.tensor)

    shared_axes = find_share_axes([A_ref, B_ref])
    print(f"Shared axes: {shared_axes}")

    A_ref = A_ref.slice(*shared_axes)
    B_ref = B_ref.slice(*shared_axes)

    # Perform cross product
    C_ref = cross_product([A_ref, B_ref])
    C_ref = flatten_element(C_ref)

    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data:")
    print(C_ref.tensor)
    

def demonstrate_normcode_and_in():

    normcode_pattern = """[{old expression} and {new expression} in all {old expression}]
    |ref. [%O[0]=%[%tech], %O[1]=%[%couch]]
    <= &in({old expression};{new expression})%:{old expression}
    <- {old expression}
        |ref. [%O[0]=%(tech), %O[1]=%(couch)]
        |nl. There are two old expressions(O[0], O[1]);
    <- {new expression}
        |ref. [%O[0]=[%N[0]=%(techie)], %O[1]=[%N[0]=%(couchie)]]
        |nl. There are two old expressions(O[0], O[1]);
    """

    print(normcode_pattern)

    old_ref = Reference(
        axes=['O'],
        shape=(2,),
        initial_value=0
    )
    old_ref.tensor = ['%(tech)', '%(couch)']    

    new_ref = Reference(
        axes=['O', 'N'],
        shape=(2,1),
        initial_value=0
    )
    new_ref.tensor = [['%(techie)'], ['%(couchie)']]

    shared_axes = find_share_axes([old_ref, new_ref])
    print(f"Shared axes: {shared_axes}")

    old_ref = old_ref.slice(*shared_axes)
    new_ref = new_ref.slice(*shared_axes)

    C_ref = cross_product([old_ref, new_ref])
    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data:")
    print(C_ref.tensor)

    C_ref = annotate_element(C_ref, ['{old expression}', '{new expression}'])
    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data:")
    print(C_ref.tensor)

    old_ref_axes = old_ref.axes
    old_ref_axes.pop(0)
    print(f"Old reference axes: {old_ref_axes}")
    C_ref = C_ref.slice(*old_ref_axes)
    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data:")
    print(C_ref.tensor)


    template = Template("Transform old expression (being '${input1}') into some new expression (like being '${input2}').")

    def create_element_actuation(annotation_list, template: Template):
        def element_actuation(element):
            return_string = ""
            for one_annotation in element:
                input_dict = {}
                for i, annotation in enumerate(annotation_list):
                    input_value = one_annotation[annotation]
                    if isinstance(input_value, list):
                        # Use the new from_data method to create reference from data
                        temp_ref = Reference.from_data(input_value)
                        temp_ref = element_action(strip_element_wrapper, [temp_ref])
                        input_value = str(temp_ref.tensor)
                    
                    input_dict[f"input{i+1}"] = strip_element_wrapper(input_value)

                template_copy = copy(template)
                return_string += template_copy.safe_substitute(**input_dict) + " \n"

            return return_string

        return element_actuation 

    element_actuation = create_element_actuation(['{old expression}', '{new expression}'], template)
    C_ref = element_action(element_actuation, [C_ref])
    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data:")
    print(C_ref.tensor)

def demonstrate_normcode_or_across():

    normcode_pattern = """[{old expression} or {new expression} across all {old expression}]
    |ref. [[%(tech), %(techie)], [%(couch), %(couchie)]]
    <= &across({old expression};{new expression})%:{old expression}
    <- {old expression}
        |ref. [%O[0]=%(tech), %O[1]=%(couch)]
        |nl. There are two old expressions(O[0], O[1]);
    <- {new expression}
        |ref. [%O[0]=[%N[0]=%(techie)], %O[1]=[%N[0]=%(couchie)]]
        |nl. There are two old expressions(O[0], O[1]);
    """

    print(normcode_pattern)

    old_ref = Reference(
        axes=['O'],
        shape=(2,),
        initial_value=0
    )
    old_ref.tensor = ['%(tech)', '%(couch)']    

    new_ref = Reference(
        axes=['O', 'N'],
        shape=(2,1),
        initial_value=0
    )
    new_ref.tensor = [['%(techie)'], ['%(couchie)']]

    shared_axes = find_share_axes([old_ref, new_ref])
    print(f"Shared axes: {shared_axes}")

    old_ref = old_ref.slice(*shared_axes)
    new_ref = new_ref.slice(*shared_axes)

    C_ref = cross_product([old_ref, new_ref])
    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data:")
    print(C_ref.tensor)


    old_ref_axes = old_ref.axes
    old_ref_axes.pop(0)
    print(f"Old reference axes: {old_ref_axes}")
    C_ref = C_ref.slice(*old_ref_axes)
    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data:")
    print(C_ref.tensor)

    C_ref = flatten_element(C_ref)
    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data:")
    print(C_ref.tensor)


    template = Template("Transform old expression (being '${input1}') into some new expression (like being '${input2}').")

    def create_element_actuation(annotation_list, template: Template):
        def element_actuation(element):
            return_string = ""
            for one_annotation in element:
                input_dict = {}
                for i, annotation in enumerate(annotation_list):
                    input_value = one_annotation[annotation]
                    if isinstance(input_value, list):
                        # Use the new from_data method to create reference from data
                        temp_ref = Reference.from_data(input_value)
                        temp_ref = element_action(strip_element_wrapper, [temp_ref])
                        input_value = str(temp_ref.tensor)
                    
                    input_dict[f"input{i+1}"] = strip_element_wrapper(input_value)

                template_copy = copy(template)
                return_string += template_copy.safe_substitute(**input_dict) + " \n"

            return return_string

        return element_actuation 


def demonstrate_normcode_and_only():

    normcode_pattern = """[{old expression} and {new expression}]
    |ref. [%O[0]=[%{old expression}%(tech), %{new expression}%(techie)], %O[1]=[%{old expression}%(couch), %{new expression}%(couchie)]]
    <= &and({old expression};{new expression})
    <- {old expression}
        |ref. [%O[0]=%(tech), %O[1]=%(couch)]
        |nl. There are two old expressions(O[0], O[1]);
    <- {new expression}
        |ref. [%O[0]=[%N[0]=%(techie)], %O[1]=[%N[0]=%(couchie)]]
        |nl. There are two old expressions(O[0], O[1]);
        |nl. For the first old expression(O[0]), there is one new expression(N[0]);
        |nl. For the second old expression(O[1]), there is one new expression(N[0]);
    """

    print(normcode_pattern)

    old_ref = Reference(
        axes=['O'],
        shape=(2,),
        initial_value=0
    )
    old_ref.tensor = ['%(tech)', '%(couch)']    

    new_ref = Reference(
        axes=['O', 'N'],
        shape=(2,1),
        initial_value=0
    )
    new_ref.tensor = [['%(techie)'], ['%(couchie)']]

    shared_axes = find_share_axes([old_ref, new_ref])
    print(f"Shared axes: {shared_axes}")

    old_ref = old_ref.slice(*shared_axes)
    new_ref = new_ref.slice(*shared_axes)

    C_ref = cross_product([old_ref, new_ref])
    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data:")
    print(C_ref.tensor)

    C_ref = annotate_element(C_ref, ['{old expression}', '{new expression}'])
    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data:")
    print(C_ref.tensor)



    template = Template("Transform old expression (being '${input1}') into some new expression (like being '${input2}').")

    def create_element_actuation(annotation_list, template: Template):
        def element_actuation(element):
            return_string = ""

            if not isinstance(element, list):
                element = [element]
                print(f"Element: {element}")

            for one_annotation in element:
                input_dict = {}
                for i, annotation in enumerate(annotation_list):
                    input_value = one_annotation[annotation]
                    if isinstance(input_value, list):
                        # Use the new from_data method to create reference from data
                        temp_ref = Reference.from_data(input_value)
                        temp_ref = element_action(strip_element_wrapper, [temp_ref])
                        input_value = str(temp_ref.tensor)
                    
                    input_dict[f"input{i+1}"] = strip_element_wrapper(input_value)

                template_copy = copy(template)
                return_string += template_copy.safe_substitute(**input_dict) + " \n"

            return return_string

        return element_actuation 

    element_actuation = create_element_actuation(['{old expression}', '{new expression}'], template)
    C_ref = element_action(element_actuation, [C_ref])
    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data:")
    print(C_ref.tensor)

def demonstrate_normcode_or_only():

    normcode_pattern = """[{old expression} or {new expression}]
    |ref. [%O[0]=%[%(tech), %(techie)], %O[1]=%[%(couch), %(couchie)]]
    <= &across({old expression};{new expression})
    <- {old expression}
        |ref. [%O[0]=%(tech), %O[1]=%(couch)]
        |nl. There are two old expressions(O[0], O[1]);
    <- {new expression}
        |ref. [%O[0]=[%N[0]=%(techie)], %O[1]=[%N[0]=%(couchie)]]
        |nl. There are two old expressions(O[0], O[1]);
        |nl. For the first old expression(O[0]), there is one new expression(N[0]);
        |nl. For the second old expression(O[1]), there is one new expression(N[0]);
    """

    print(normcode_pattern)

    old_ref = Reference(
        axes=['O'],
        shape=(2,),
        initial_value=0
    )
    old_ref.tensor = ['%(tech)', '%(couch)']    

    new_ref = Reference(
        axes=['O', 'N'],
        shape=(2,1),
        initial_value=0
    )
    new_ref.tensor = [['%(techie)'], ['%(couchie)']]

    shared_axes = find_share_axes([old_ref, new_ref])
    print(f"Shared axes: {shared_axes}")

    old_ref = old_ref.slice(*shared_axes)
    new_ref = new_ref.slice(*shared_axes)

    C_ref = cross_product([old_ref, new_ref])
    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data:")
    print(C_ref.tensor)

    C_ref = flatten_element(C_ref)
    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data:")
    print(C_ref.tensor)


    template = Template("Identify the longer expression (being '$output') in old expression or new expression (being '${input1}').")

    def create_element_actuation(template: Template):
        def element_actuation(element):
            format_string = ""
            if not isinstance(element, list):
                element = [element]
            for base_element in element:
                format_string += f"{strip_element_wrapper(base_element)}"
                if base_element != element[-1]:
                    format_string += "; "

            template_copy = copy(template)
            return_string = template_copy.safe_substitute(input1=format_string)
            return return_string
        
        return element_actuation 

    element_actuation = create_element_actuation(template)
    C_ref = element_action(element_actuation, [C_ref])
    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data:")
    print(C_ref.tensor)



if __name__ == "__main__":

    demonstrate_normcode_and_in()











