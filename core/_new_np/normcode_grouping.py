from string import Template
from copy import copy
from _reference import Reference, cross_product, element_action
from _methods._demo import strip_element_wrapper, wrap_element_wrapper


class NormCodeSlicer:
    """
    A class that abstracts NormCode slicing patterns as functions of references.
    Provides methods for different slicing operations: simple_or, and_in, or_across, and_only, or_only.
    """
    
    def __init__(self, skip_value="@#SKIP#@"):
        """
        Initialize the NormCodeSlicer.
        
        Args:
            skip_value (str): Value to use for missing/skip elements
        """
        self.skip_value = skip_value
    
    def find_share_axes(self, references):
        """
        Find the shared axes between all references.
        
        Args:
            references (list): List of Reference objects
            
        Returns:
            list: List of shared axis names
        """
        if not references:
            return []
        shared_axes = set(references[0].axes)
        for ref in references[1:]:
            shared_axes.intersection_update(ref.axes)
        return list(shared_axes)
    
    def flatten_element(self, reference):
        """
        Flatten the element of the reference.
        
        Args:
            reference (Reference): The reference to flatten
            
        Returns:
            Reference: A new reference with flattened elements
        """
        def flatten_all_list(nested_list):
            if not isinstance(nested_list, list):
                return [nested_list]
            return sum((flatten_all_list(item) for item in nested_list), [])
        
        return element_action(flatten_all_list, [reference])
    
    def annotate_element(self, reference, annotation_list):
        """
        Annotate elements with labels.
        
        Args:
            reference (Reference): The reference to annotate
            annotation_list (list): List of annotation labels
            
        Returns:
            Reference: A new reference with annotated elements
        """
        def annotate_list(lst):
            annotation_dict = {}
            for i, annotation in enumerate(annotation_list):
                annotation_dict[annotation] = lst[i]
            return annotation_dict
        
        return element_action(annotate_list, [reference])
    
    def create_element_actuation(self, annotation_list, template):
        """
        Create an element actuation function for template processing.
        
        Args:
            annotation_list (list): List of annotation labels
            template (Template): String template for processing
            
        Returns:
            function: Element actuation function
        """
        def element_actuation(element):
            return_string = ""
            # Handle both single annotation dict and list of annotation dicts
            if isinstance(element, list):
                annotation_items = element
            else:
                annotation_items = [element]
            
            for one_annotation in annotation_items:
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
    
    
    def and_in(self, references, annotation_list, slice_axes=None, template=None):
        """
        Implement the AND patterns: 
        - AND IN: [{old expression} and {new expression} in all {old expression}] (when slice_axes provided)
        - AND ONLY: [{old expression} and {new expression}] (when slice_axes is None)
        
        Args:
            references (list): List of Reference objects to combine
            annotation_list (list): List of annotation labels
            slice_axes (list, optional): List of axes to slice by, the last axis will be removed. 
                                       If None, no slicing is performed (AND ONLY pattern).
            template (Template, optional): Template for processing results
            
        Returns:
            Reference: Processed reference with annotations
        """
        # Find shared axes
        shared_axes = self.find_share_axes(references)
        
        # Slice references to shared axes
        sliced_refs = [ref.slice(*shared_axes) for ref in references]
        
        # Perform cross product
        result = cross_product(sliced_refs)
        
        # Annotate elements
        result = self.annotate_element(result, annotation_list)
        
        # Slice by slice_axes if provided (AND IN pattern)
        if slice_axes is not None:
            slice_axes_copy = slice_axes.copy()  # Create a copy to avoid modifying the original
            slice_axes_copy.pop()
            result = result.slice(*slice_axes_copy)
        
        # Apply template if provided
        if template:
            element_actuation = self.create_element_actuation(
                annotation_list, 
                template
            )
            result = element_action(element_actuation, [result])
        
        return result
    
    def or_across(self, references, slice_axes=None, template=None):
        """
        Implement the OR patterns:
        - OR ACROSS: [{old expression} or {new expression} across all {old expression}] (when slice_axes provided)
        - OR ONLY: [{old expression} or {new expression}] (when slice_axes is None)
        
        Args:
            references (list): List of Reference objects to combine
            slice_axes (list, optional): List of axes to slice by, the last axis will be removed.
                                       If None, no slicing is performed (OR ONLY pattern).
            template (Template, optional): Template for processing results
            
        Returns:
            Reference: Processed reference with flattened elements
        """
        # Find shared axes
        shared_axes = self.find_share_axes(references)
        
        # Slice references to shared axes
        sliced_refs = [ref.slice(*shared_axes) for ref in references]
        
        # Perform cross product
        result = cross_product(sliced_refs)
        
        # Slice by slice_axes if provided (OR ACROSS pattern)
        if slice_axes is not None:
            slice_axes_copy = slice_axes.copy()  # Create a copy to avoid modifying the original
            slice_axes_copy.pop()
            result = result.slice(*slice_axes_copy)
        
        # Flatten elements
        result = self.flatten_element(result)
        
        # Apply template if provided
        if template:
            element_actuation = self.create_simple_element_actuation(template)
            result = element_action(element_actuation, [result])
        
        return result
    

    
    def create_simple_element_actuation(self, template):
        """
        Create a simple element actuation function for templates without annotations.
        
        Args:
            template (Template): String template for processing
            
        Returns:
            function: Element actuation function
        """
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


# Example usage and demonstration
def demonstrate_normcode_slicer():
    """
    Demonstrate the NormCodeSlicer class with examples similar to slice_with_normcode.py
    """
    print("=== NormCodeSlicer Class Demonstration ===\n")
    
    # Create a slicer instance
    slicer = NormCodeSlicer()
    
    print("1. AND IN Pattern: [{old expression} and {new expression} in all {old expression}]")
    print("   |ref. [%[%[%{old expression}%(tech), %{new expression}%(techie)], %[%{old expression}%(couch), %{new expression}%(couchie)]]]")
    print("   <= &in({old expression};{new expression})%:{old expression}")
    print("   <- {old expression}")
    print("       |ref. [%O[0]=%(tech), %O[1]=%(couch)]")
    print("       |nl. There are two old expressions(O[0], O[1]);")
    print("   <- {new expression}")
    print("       |ref. [%O[0]=[%N[0]=%(techie)], %O[1]=[%N[0]=%(couchie)]]")
    print("       |nl. There are two old expressions(O[0], O[1]);")
    
    # Create sample references
    old_ref = Reference(
        axes=['O'],
        shape=(2,),
        initial_value=0
    )
    old_ref.tensor = ['%(tech)', '%(couch)']
    
    new_ref = Reference(
        axes=['O', 'N'],
        shape=(2, 1),
        initial_value=0
    )
    new_ref.tensor = [['%(techie)'], ['%(couchie)']]
    
    print(f"\nReference old shape: {old_ref.shape}")
    print(f"Reference old axes: {old_ref.axes}")
    print(f"Reference old data: {old_ref.tensor}")
    
    print(f"\nReference new shape: {new_ref.shape}")
    print(f"Reference new axes: {new_ref.axes}")
    print(f"Reference new data: {new_ref.tensor}")
    
    # Create template for processing
    template = Template("Transform old expression (being '${input1}') into some new expression (like being '${input2}').")
    
    result_and_in = slicer.and_in([old_ref, new_ref], ['{old expression}', '{new expression}'], ['O'])
    print(f"\nResult shape: {result_and_in.shape}")
    print(f"Result axes: {result_and_in.axes}")
    print(f"Result data: {result_and_in.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("2. OR ACROSS Pattern: [{old expression} or {new expression} across all {old expression}]")
    print("   |ref. [[%(tech), %(techie), %(couch), %(couchie)]]")
    print("   <= &across({old expression};{new expression})%:{old expression}")
    print("   <- {old expression}")
    print("       |ref. [%O[0]=%(tech), %O[1]=%(couch)]")
    print("       |nl. There are two old expressions(O[0], O[1]);")
    print("   <- {new expression}")
    print("       |ref. [%O[0]=[%N[0]=%(techie)], %O[1]=[%N[0]=%(couchie)]]")
    print("       |nl. There are two old expressions(O[0], O[1]);")
    
    # Create a different template for OR ACROSS pattern that only uses input1
    or_across_template = Template("Transform expressions: ${input1}")
    result_or_across = slicer.or_across([old_ref, new_ref], ['O'])
    print(f"\nResult shape: {result_or_across.shape}")
    print(f"Result axes: {result_or_across.axes}")
    print(f"Result data: {result_or_across.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("3. AND ONLY Pattern: [{old expression} and {new expression}]")
    print("   |ref. [%O[0]=[%[%{old expression}%(tech), %{new expression}%(techie)]], %O[1]=[%[%{old expression}%(couch), %{new expression}%(couchie)]]]")
    print("   <= &and({old expression};{new expression})")
    print("   <- {old expression}")
    print("       |ref. [%O[0]=%(tech), %O[1]=%(couch)]")
    print("       |nl. There are two old expressions(O[0], O[1]);")
    print("   <- {new expression}")
    print("       |ref. [%O[0]=[%N[0]=%(techie)], %O[1]=[%N[0]=%(couchie)]]")
    print("       |nl. There are two old expressions(O[0], O[1]);")
    
    result_and_only = slicer.and_in([old_ref, new_ref], ['{old expression}', '{new expression}'])
    print(f"\nResult shape: {result_and_only.shape}")
    print(f"Result axes: {result_and_only.axes}")
    print(f"Result data: {result_and_only.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("4. OR ONLY Pattern: [{old expression} or {new expression}]")
    print("   |ref. [%O[0]=%[%(tech), %(techie)], %O[1]=%[%(couch), %(couchie)]]")
    print("   <= &across({old expression};{new expression})")
    print("   <- {old expression}")
    print("       |ref. [%O[0]=%(tech), %O[1]=%(couch)]")
    print("       |nl. There are two old expressions(O[0], O[1]);")
    print("   <- {new expression}")
    print("       |ref. [%O[0]=[%N[0]=%(techie)], %O[1]=[%N[0]=%(couchie)]]")
    print("       |nl. There are two old expressions(O[0], O[1]);")
    
    # Create a different template for OR ONLY pattern
    or_template = Template("Identify the longer expression (being '$output') in old expression or new expression (being '${input1}').")
    
    result_or_only = slicer.or_across([old_ref, new_ref])
    print(f"\nResult shape: {result_or_only.shape}")
    print(f"Result axes: {result_or_only.axes}")
    print(f"Result data: {result_or_only.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("5. SIMPLE OR ONLY Pattern: [{A} or {B}]")
    print("   |ref. [%D[0]=%[%a1, %b1, %b2]], %D[1]=%[%a2, %b1, %b2]]")
    print("   <= &or(A; B)")
    print("   <- A |ref. [%D[0]=[%A[0]=%a1]], [%D[1]=[%A[1]=%a2]]]")
    print("   <- B |ref. [%D[0]=[%B[0]=%b1, %B[1]=%b2]], [%D[1]=[%B[0]=%b1, %B[1]=%b2]]]")
    
    # Create references for simple OR ONLY pattern
    A_ref = Reference(
        axes=['D', 'A'],
        shape=(2, 1),
        initial_value=0
    )
    A_ref.tensor = [['a1'], ['a2']]
    
    B_ref = Reference(
        axes=['D', 'B'],
        shape=(2, 2),
        initial_value=0
    )
    B_ref.tensor = [['b1', 'b2'], ['b1', 'b2']]
    
    print(f"\nReference A shape: {A_ref.shape}")
    print(f"Reference A axes: {A_ref.axes}")
    print(f"Reference A data: {A_ref.tensor}")
    
    print(f"\nReference B shape: {B_ref.shape}")
    print(f"Reference B axes: {B_ref.axes}")
    print(f"Reference B data: {B_ref.tensor}")
    
    result_simple_or_only = slicer.or_across([A_ref, B_ref])
    print(f"\nResult shape: {result_simple_or_only.shape}")
    print(f"Result axes: {result_simple_or_only.axes}")
    print(f"Result data: {result_simple_or_only.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("6. SIMPLE AND ONLY Pattern: [{A} and {B}]")
    print("   |ref. [%D[0]=[%{A}%a1, %{B}%b1, %{B}%b2]], %D[1]=[%{A}%a2, %{B}%b1, %{B}%b2]]")
    print("   <= &and(A; B)")
    print("   <- A |ref. [%D[0]=[%A[0]=%a1]], [%D[1]=[%A[1]=%a2]]]")
    print("   <- B |ref. [%D[0]=[%B[0]=%b1, %B[1]=%b2]], [%D[1]=[%B[0]=%b1, %B[1]=%b2]]]")
    
    result_simple_and_only = slicer.and_in([A_ref, B_ref], ['{A}', '{B}'])
    print(f"\nResult shape: {result_simple_and_only.shape}")
    print(f"Result axes: {result_simple_and_only.axes}")
    print(f"Result data: {result_simple_and_only.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("7. SIMPLE OR ACROSS Pattern: [{A} or {B} across all {A}]")
    print("   |ref. [[%a1, %b1, %b2], [%a2, %b1, %b2]]")
    print("   <= &across(A; B)%:{A}")
    print("   <- A |ref. [%D[0]=[%A[0]=%a1]], [%D[1]=[%A[1]=%a2]]]")
    print("   <- B |ref. [%D[0]=[%B[0]=%b1, %B[1]=%b2]], [%D[1]=[%B[0]=%b1, %B[1]=%b2]]]")
    
    result_simple_or_across = slicer.or_across([A_ref, B_ref], ['D'])
    print(f"\nResult shape: {result_simple_or_across.shape}")
    print(f"Result axes: {result_simple_or_across.axes}")
    print(f"Result data: {result_simple_or_across.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("8. SIMPLE AND IN Pattern: [{A} and {B} in all {A}]")
    print("   |ref. [%[%{A}%a1, %{B}%b1, %{B}%b2], %[%{A}%a2, %{B}%b1, %{B}%b2]]")
    print("   <= &in(A; B)%:{A}")
    print("   <- A |ref. [%D[0]=[%A[0]=%a1]], [%D[1]=[%A[1]=%a2]]]")
    print("   <- B |ref. [%D[0]=[%B[0]=%b1, %B[1]=%b2]], [%D[1]=[%B[0]=%b1, %B[1]=%b2]]]")
    
    result_simple_and_in = slicer.and_in([A_ref, B_ref], ['{A}', '{B}'], ['D'])
    print(f"\nResult shape: {result_simple_and_in.shape}")
    print(f"Result axes: {result_simple_and_in.axes}")
    print(f"Result data: {result_simple_and_in.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("9. THREE REFERENCES - AND IN Pattern: [{A} and {B} and {C} in all {A}]")
    print("   |ref. [%[%{A}%a1, %{B}%b1, %{C}%c1], %[%{A}%a2, %{B}%b1, %{C}%c1]]")
    print("   <= &in(A; B; C)%:{A}")
    print("   <- A |ref. [%D[0]=[%A[0]=%a1]], [%D[1]=[%A[1]=%a2]]]")
    print("   <- B |ref. [%D[0]=[%B[0]=%b1]], [%D[1]=[%B[0]=%b1]]]")
    print("   <- C |ref. [%D[0]=[%C[0]=%c1]], [%D[1]=[%C[0]=%c1]]]")
    
    # Create a third reference C
    C_ref = Reference(
        axes=['D', 'C'],
        shape=(2, 1),
        initial_value=0
    )
    C_ref.tensor = [['c1'], ['c1']]
    
    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data: {C_ref.tensor}")
    
    result_three_and_in = slicer.and_in([A_ref, B_ref, C_ref], ['{A}', '{B}', '{C}'], ['D'])
    print(f"\nResult shape: {result_three_and_in.shape}")
    print(f"Result axes: {result_three_and_in.axes}")
    print(f"Result data: {result_three_and_in.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("10. THREE REFERENCES - OR ACROSS Pattern: [{A} or {B} or {C} across all {A}]")
    print("   |ref. [[%a1, %b1, %c1], [%a2, %b1, %c1]]")
    print("   <= &across(A; B; C)%:{A}")
    print("   <- A |ref. [%D[0]=[%A[0]=%a1]], [%D[1]=[%A[1]=%a2]]]")
    print("   <- B |ref. [%D[0]=[%B[0]=%b1]], [%D[1]=[%B[0]=%b1]]]")
    print("   <- C |ref. [%D[0]=[%C[0]=%c1]], [%D[1]=[%C[0]=%c1]]]")
    
    result_three_or_across = slicer.or_across([A_ref, B_ref, C_ref], ['D'])
    print(f"\nResult shape: {result_three_or_across.shape}")
    print(f"Result axes: {result_three_or_across.axes}")
    print(f"Result data: {result_three_or_across.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("11. THREE REFERENCES - AND ONLY Pattern: [{A} and {B} and {C}]")
    print("   |ref. [%D[0]=[%{A}%a1, %{B}%b1, %{C}%c1]], %D[1]=[%{A}%a2, %{B}%b1, %{C}%c1]]")
    print("   <= &and(A; B; C)")
    print("   <- A |ref. [%D[0]=[%A[0]=%a1]], [%D[1]=[%A[1]=%a2]]]")
    print("   <- B |ref. [%D[0]=[%B[0]=%b1]], [%D[1]=[%B[0]=%b1]]]")
    print("   <- C |ref. [%D[0]=[%C[0]=%c1]], [%D[1]=[%C[0]=%c1]]]")
    
    result_three_and_only = slicer.and_in([A_ref, B_ref, C_ref], ['{A}', '{B}', '{C}'])
    print(f"\nResult shape: {result_three_and_only.shape}")
    print(f"Result axes: {result_three_and_only.axes}")
    print(f"Result data: {result_three_and_only.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("12. THREE REFERENCES - OR ONLY Pattern: [{A} or {B} or {C}]")
    print("   |ref. [%D[0]=%[%a1, %b1, %c1]], %D[1]=%[%a2, %b1, %c1]]")
    print("   <= &or(A; B; C)")
    print("   <- A |ref. [%D[0]=[%A[0]=%a1]], [%D[1]=[%A[1]=%a2]]]")
    print("   <- B |ref. [%D[0]=[%B[0]=%b1]], [%D[1]=[%B[0]=%b1]]]")
    print("   <- C |ref. [%D[0]=[%C[0]=%c1]], [%D[1]=[%C[0]=%c1]]]")
    
    result_three_or_only = slicer.or_across([A_ref, B_ref, C_ref])
    print(f"\nResult shape: {result_three_or_only.shape}")
    print(f"Result axes: {result_three_or_only.axes}")
    print(f"Result data: {result_three_or_only.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("13. FOUR REFERENCES - Complex AND IN Pattern: [{A} and {B} and {C} and {D} in all {A}]")
    print("   |ref. [%[%{A}%a1, %{B}%b1, %{C}%c1, %{D}%d1], %[%{A}%a2, %{B}%b1, %{C}%c1, %{D}%d1]]")
    print("   <= &in(A; B; C; D)%:{A}")
    print("   <- A |ref. [%D[0]=[%A[0]=%a1]], [%D[1]=[%A[1]=%a2]]]")
    print("   <- B |ref. [%D[0]=[%B[0]=%b1]], [%D[1]=[%B[0]=%b1]]]")
    print("   <- C |ref. [%D[0]=[%C[0]=%c1]], [%D[1]=[%C[0]=%c1]]]")
    print("   <- D |ref. [%D[0]=[%E[0]=%d1]], [%D[1]=[%E[0]=%d1]]]")
    
    # Create a fourth reference D
    D_ref = Reference(
        axes=['D', 'E'],
        shape=(2, 1),
        initial_value=0
    )
    D_ref.tensor = [['d1'], ['d1']]
    
    print(f"\nReference D shape: {D_ref.shape}")
    print(f"Reference D axes: {D_ref.axes}")
    print(f"Reference D data: {D_ref.tensor}")
    
    result_four_and_in = slicer.and_in([A_ref, B_ref, C_ref, D_ref], ['{A}', '{B}', '{C}', '{D}'], ['D'])
    print(f"\nResult shape: {result_four_and_in.shape}")
    print(f"Result axes: {result_four_and_in.axes}")
    print(f"Result data: {result_four_and_in.tensor}")
    
    print("\n" + "="*60 + "\n")
    
    print("14. FOUR REFERENCES - Complex OR ACROSS Pattern: [{A} or {B} or {C} or {D} across all {A}]")
    print("   |ref. [[%a1, %b1, %c1, %d1], [%a2, %b1, %c1, %d1]]")
    print("   <= &across(A; B; C; D)%:{A}")
    print("   <- A |ref. [%D[0]=[%A[0]=%a1]], [%D[1]=[%A[1]=%a2]]]")
    print("   <- B |ref. [%D[0]=[%B[0]=%b1]], [%D[1]=[%B[0]=%b1]]]")
    print("   <- C |ref. [%D[0]=[%C[0]=%c1]], [%D[1]=[%C[0]=%c1]]]")
    print("   <- D |ref. [%D[0]=[%E[0]=%d1]], [%D[1]=[%E[0]=%d1]]]")
    
    result_four_or_across = slicer.or_across([A_ref, B_ref, C_ref, D_ref], ['D'])
    print(f"\nResult shape: {result_four_or_across.shape}")
    print(f"Result axes: {result_four_or_across.axes}")
    print(f"Result data: {result_four_or_across.tensor}")


if __name__ == "__main__":
    demonstrate_normcode_slicer()