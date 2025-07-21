from _reference import Reference, cross_product


def demonstrate_slicing():
    """
    Demonstrate slicing behavior with the Reference class.
    This example shows how to create a multi-dimensional tensor and slice it along different axes.
    """
    print("=== Slicing Behavior Demonstration ===\n")
    
    # Create a 3D tensor with axes: 'batch', 'height', 'width'
    # Shape: (2, 3, 4) - 2 batches, 3 rows, 4 columns
    print("1. Creating a 3D tensor with shape (2, 3, 4):")
    tensor_3d = Reference(
        axes=['batch', 'height', 'width'],
        shape=(2, 3, 4),
        initial_value=0
    )
    
    # Fill the tensor with some data
    for b in range(2):
        for h in range(3):
            for w in range(4):
                tensor_3d.set(b * 100 + h * 10 + w, batch=b, height=h, width=w)
    
    print(f"Original tensor shape: {tensor_3d.shape}")
    print(f"Original tensor axes: {tensor_3d.axes}")
    print(f"Original tensor data:")
    for b in range(2):
        print(f"  Batch {b}:")
        for h in range(3):
            print(f"    Row {h}: {tensor_3d.get(batch=b, height=h)}")
    print()
    
    # Example 1: Slice along 'batch' axis (keep only batch axis)
    print("2. Slicing along 'batch' axis (keeping only batch axis):")
    batch_slice = tensor_3d.slice('batch')
    print(f"Sliced tensor shape: {batch_slice.shape}")
    print(f"Sliced tensor axes: {batch_slice.axes}")
    print(f"Sliced tensor data:")
    for b in range(batch_slice.shape[0]):
        print(f"  Batch {b}: {batch_slice.get(batch=b)}")
    print()
    
    # Example 2: Slice along 'height' axis (keep only height axis)
    print("3. Slicing along 'height' axis (keeping only height axis):")
    height_slice = tensor_3d.slice('height')
    print(f"Sliced tensor shape: {height_slice.shape}")
    print(f"Sliced tensor axes: {height_slice.axes}")
    print(f"Sliced tensor data:")
    for h in range(height_slice.shape[0]):
        print(f"  Height {h}: {height_slice.get(height=h)}")
    print()
    
    # Example 3: Slice along multiple axes ('batch', 'width')
    print("4. Slicing along multiple axes ('batch', 'width'):")
    multi_slice = tensor_3d.slice('batch', 'width')
    print(f"Sliced tensor shape: {multi_slice.shape}")
    print(f"Sliced tensor axes: {multi_slice.axes}")
    print(f"Sliced tensor data:")
    for b in range(multi_slice.shape[0]):
        print(f"  Batch {b}:")
        for w in range(multi_slice.shape[1]):
            print(f"    Width {w}: {multi_slice.get(batch=b, width=w)}")
    print()
    
    # Example 4: Using shape_view to create different views
    print("5. Using shape_view to create different views:")
    
    # View with only 'batch' and 'width' axes
    batch_width_view = tensor_3d.shape_view(['batch', 'width'])
    print(f"View with ['batch', 'width'] - shape: {batch_width_view.shape}")
    print(f"Data: {batch_width_view.tensor}")
    print()
    
    # View with all axes (same as original)
    all_axes_view = tensor_3d.shape_view()
    print(f"View with all axes - shape: {all_axes_view.shape}")
    print(f"Data: {all_axes_view.tensor}")
    print()
    
    # Example 5: Demonstrating get() with slicing
    print("6. Using get() with slicing:")
    
    # Get a specific slice
    specific_slice = tensor_3d.get(batch=0, height=slice(1, 3))
    print(f"Getting batch=0, height=slice(1,3): {specific_slice}")
    
    # Get all data for a specific batch
    batch_data = tensor_3d.get(batch=1)
    print(f"Getting all data for batch=1: {batch_data}")
    print()
    
    # Example 6: Show how slicing reduces dimensionality
    print("7. Demonstrating dimensionality reduction through slicing:")
    
    # Original tensor has 3 dimensions
    print(f"Original tensor: {len(tensor_3d.axes)} dimensions - {tensor_3d.axes}")
    
    # Slice to 2 dimensions
    two_d_slice = tensor_3d.slice('batch', 'height')
    print(f"After slicing ['batch', 'height']: {len(two_d_slice.axes)} dimensions - {two_d_slice.axes}")
    
    # Slice to 1 dimension
    one_d_slice = tensor_3d.slice('batch')
    print(f"After slicing ['batch']: {len(one_d_slice.axes)} dimensions - {one_d_slice.axes}")
    print()


def demonstrate_normcode_slicing():
    """
    Demonstrate NormCode slicing patterns using the Reference class.
    This implements the complex slicing operations shown in the user's examples.
    """
    print("=== NormCode Slicing Pattern Demonstration ===\n")
    
    # Pattern 1: [{A} and {B}] with nested references
    print("1. Pattern: [{A} and {B}]")
    print("   |ref. [%[%a1, %b1, %b2], %[%a2, %b1, %b2]]")
    print("   <= &in(A, B %:_)")
    print("   <- A |ref. [[%a1], [%a2]]")
    print("   <- B |ref. [[%b1, %b2]]")
    
    # Create reference A with shape (2,1) - two elements, each containing one value
    A_ref = Reference(
        axes=['d1', 'ad2'],
        shape=(2, 1),
        initial_value=0
    )
    A_ref.set('a1', d1=0, ad2=0)
    A_ref.set('a2', d1=1, ad2=0)
    
    print(f"\nReference A shape: {A_ref.shape}")
    print(f"Reference A axes: {A_ref.axes}")
    print(f"Reference A data:")
    print(A_ref.tensor)

    # A_only_axis = A_ref.axes[-1]
    # A_ref = A_ref.slice(A_only_axis)
    # print(f"\nReference A shape after slicing: {A_ref.shape}")
    # print(f"Reference A axes after slicing: {A_ref.axes}")
    # print(f"Reference A data after slicing:")
    # print(A_ref.tensor)

    
    # Create reference B with shape (1,2) - one element containing two values
    B_ref = Reference(
        axes=['d1', 'bd2'],
        shape=(2, 2),
        initial_value=0
    )
    B_ref.set('b1', d1=0, bd2=0)
    B_ref.set('b2', d1=0, bd2=1)
    B_ref.set('b3', d1=1, bd2=0)

    print(f"\nReference B shape: {B_ref.shape}")
    print(f"Reference B axes: {B_ref.axes}")
    print(f"Reference B data:")
    print(B_ref.tensor)

    # B_only_axis = B_ref.axes[-1]
    # B_ref = B_ref.slice(B_only_axis)
    # print(f"\nReference B shape after slicing: {B_ref.shape}")
    # print(f"Reference B axes after slicing: {B_ref.axes}")
    # print(f"Reference B data after slicing:")
    # print(B_ref.tensor)
    
    # Perform cross product
    C_ref = cross_product([A_ref, B_ref])

    print(f"\nReference C shape: {C_ref.shape}")
    print(f"Reference C axes: {C_ref.axes}")
    print(f"Reference C data:")
    print(C_ref.tensor)
    # axes_to_get = {
    #     A_only_axis: 0,
    #     B_only_axis: 0
    # }
    # print(C_ref.get(**axes_to_get))



    print("2. Pattern: [{adult} in {dorm} and {baby} in {room}]")
    print("   |ref. %K=[%C=[%D[1][%a1], %D[2][%a2]], %R[1][%b1, b2], %R[2][%b2]]")
    print("   <= &in(A: D?; B: R?)")
    print("   <- A")
    print("       |ref. %K=[%C=[%D[1]=[%a1], %D[2]=[%a2]]]")
    print("       |natural lanaguage: There is one Company(K); and one Class(C) in the company; In the")
    print("   <- B")



def demonstrate_irregular_slicing():
    """
    Demonstrate slicing with irregular data structures.
    """
    print("=== Irregular Data Slicing Demonstration ===\n")
    
    # Create a tensor with irregular data
    irregular_tensor = Reference(
        axes=['row', 'col'],
        shape=(3, 4),
        initial_value="@#SKIP#@"
    )
    
    # Set some irregular data
    irregular_tensor.set(10, row=0, col=0)
    irregular_tensor.set(20, row=0, col=1)
    irregular_tensor.set(30, row=1, col=0)
    irregular_tensor.set(40, row=2, col=2)
    
    print("Original irregular tensor:")
    for r in range(3):
        print(f"  Row {r}: {irregular_tensor.get(row=r)}")
    print()
    
    # Slice along 'row' axis
    row_slice = irregular_tensor.slice('row')
    print("Sliced along 'row' axis:")
    for r in range(row_slice.shape[0]):
        print(f"  Row {r}: {row_slice.get(row=r)}")
    print()


def irregular_tensor_example():
    """
    Demonstrate irregular tensor example.
    """
    print("=== Irregular Tensor Example ===\n")
    
    # Example 1: Simple irregular structure
    print("Example 1: Simple irregular structure")
    irregular_list_of_lists = [
        [[1,2], [3,4]],
        [[3,5], [4]],
    ]

    print("Original irregular data:")
    print(irregular_list_of_lists)
    print()

    irregular_tensor_reference = Reference(
        axes=['row', 'col', 'col2'],
        shape=(2, 2, 2),
        initial_value="@#SKIP#@"
    )

    irregular_tensor_reference.tensor = irregular_list_of_lists
    
    print("After setting tensor (with padding):")
    print(irregular_tensor_reference.tensor)
    print()
    print(f"Computed shape: {irregular_tensor_reference.shape}")
    print(f"Axes: {irregular_tensor_reference.axes}")
    print()
    
    # Show how the data is accessed
    print("Accessing specific elements:")
    print(f"row=0, col=0: {irregular_tensor_reference.get(row=0, col=0)}")
    print(f"row=0, col=1: {irregular_tensor_reference.get(row=0, col=1)}")
    print(f"row=1, col=0: {irregular_tensor_reference.get(row=1, col=0)}")
    print(f"row=1, col=1: {irregular_tensor_reference.get(row=1, col=1)}")
    print()
    print("Note: '@#SKIP#@' indicates padded/missing values to maintain regular structure")
    print()
    
    # Example 2: More complex irregular structure
    print("Example 2: More complex irregular structure")
    complex_irregular_data = [
        [[1, 2, 3], [4, 5]],
        [[6], [7, 8, 9, 10]],
        [[11, 12]]
    ]
    
    print("Original complex irregular data:")
    print(complex_irregular_data)
    print()
    
    complex_tensor = Reference(
        axes=['row', 'col', 'depth'],
        shape=(3, 2, 4),
        initial_value="@#SKIP#@"
    )
    
    complex_tensor.tensor = complex_irregular_data
    
    print("After setting tensor (with padding):")
    print(complex_tensor.tensor)
    print()
    print(f"Computed shape: {complex_tensor.shape}")
    print(f"Axes: {complex_tensor.axes}")
    print()
    
    print("Accessing specific elements:")
    print(f"row=0, col=0: {complex_tensor.get(row=0, col=0)}")
    print(f"row=0, col=1: {complex_tensor.get(row=0, col=1)}")
    print(f"row=1, col=0: {complex_tensor.get(row=1, col=0)}")
    print(f"row=1, col=1: {complex_tensor.get(row=1, col=1)}")
    print(f"row=2, col=0: {complex_tensor.get(row=2, col=0)}")
    print(f"row=2, col=1: {complex_tensor.get(row=2, col=1)}")
    print()


def debug_tensor_shape():
    """
    Debug function to understand why the tensor shape computation is incorrect.
    """
    print("=== Debug Tensor Shape Computation ===\n")
    
    irregular_list_of_lists = [
        [1, 2, 3],
        [4, ],
        [7, 8]
    ]
    
    print("Input irregular list:")
    print(irregular_list_of_lists)
    print()
    
    # Create a reference and see what happens
    irregular_tensor_reference = Reference(
        axes=['row', 'col'],
        shape=(3, 1),
        initial_value="@#SKIP#@"
    )
    
    print("Before setting tensor:")
    print(f"Shape: {irregular_tensor_reference.shape}")
    print(f"Data: {irregular_tensor_reference.data}")
    print()
    
    # Let's manually compute what the shape should be
    print("Manual shape computation:")
    max_cols = max(len(row) for row in irregular_list_of_lists)
    print(f"Expected shape: (3, {max_cols}) = (3, 3)")
    print()
    
    # Now set the tensor
    irregular_tensor_reference.tensor = irregular_list_of_lists
    
    print("After setting tensor:")
    print(f"Shape: {irregular_tensor_reference.shape}")
    print(f"Data: {irregular_tensor_reference.data}")
    print(f"Tensor property: {irregular_tensor_reference.tensor}")
    print()


if __name__ == "__main__":
    # debug_tensor_shape()
    irregular_tensor_example()
    # Run the demonstrations
    # demonstrate_slicing()
    # demonstrate_normcode_slicing()
    # demonstrate_irregular_slicing()










