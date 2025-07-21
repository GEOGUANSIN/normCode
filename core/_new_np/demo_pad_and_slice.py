from _reference import Reference, cross_product, element_action


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
    print("Tensor without skip values:")
    print(irregular_tensor_reference.get_tensor(ignore_skip=True))
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
    print("Tensor without skip values:")
    print(complex_tensor.get_tensor(ignore_skip=True))
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


def demonstrate_ignore_skip():
    """
    Demonstrate the ignore_skip functionality.
    """
    print("=== Ignore Skip Demonstration ===\n")
    
    # Create a tensor with some skip values
    test_tensor = Reference(
        axes=['row', 'col'],
        shape=(3, 3),
        initial_value="@#SKIP#@"
    )
    
    # Set some data with skip values
    test_tensor.set(1, row=0, col=0)
    test_tensor.set(2, row=0, col=1)
    test_tensor.set(3, row=1, col=0)
    test_tensor.set(4, row=2, col=2)
    
    print("Original tensor with skip values:")
    print(test_tensor.tensor)
    print()
    
    print("Tensor without skip values:")
    print(test_tensor.get_tensor(ignore_skip=True))
    print()
    
    print("Comparison:")
    print("With skip values (regular tensor):", test_tensor.tensor)
    print("Without skip values (cleaned):", test_tensor.get_tensor(ignore_skip=True))
    print()
    
    # Show how it works with irregular data
    print("With irregular data:")
    irregular_data = [
        [1, 2, 3],
        [4],
        [7, 8]
    ]
    
    irregular_ref = Reference(
        axes=['row', 'col'],
        shape=(3, 3),
        initial_value="@#SKIP#@"
    )
    irregular_ref.tensor = irregular_data
    
    print("Original irregular data:", irregular_data)
    print("Padded tensor:", irregular_ref.tensor)
    print("Cleaned tensor:", irregular_ref.get_tensor(ignore_skip=True))
    print()

def demonstrate_reference_from_data():
    """
    Demonstrate creating Reference objects from data without specifying axes and shape.
    """
    print("=== Reference.from_data() Demonstration ===\n")
    
    # Example 1: Simple 1D list
    print("1. Creating Reference from 1D list:")
    data_1d = ['a', 'b', 'c']
    ref_1d = Reference.from_data(data_1d, axis_names=['items'])
    print(f"   Input data: {data_1d}")
    print(f"   Generated axes: {ref_1d.axes}")
    print(f"   Generated shape: {ref_1d.shape}")
    print(f"   Reference tensor: {ref_1d.tensor}")
    
    # Example 2: 2D nested list
    print("\n2. Creating Reference from 2D nested list:")
    data_2d = [['a1', 'a2'], ['b1', 'b2'], ['c1']]
    ref_2d = Reference.from_data(data_2d, axis_names=['rows', 'cols'])
    print(f"   Input data: {data_2d}")
    print(f"   Generated axes: {ref_2d.axes}")
    print(f"   Generated shape: {ref_2d.shape}")
    print(f"   Reference tensor: {ref_2d.tensor}")
    
    # Example 3: Using auto-generated axis names
    print("\n3. Creating Reference with auto-generated axis names:")
    data_3d = [[['x1', 'x2'], ['y1']], [['z1', 'z2', 'z3']]]
    ref_3d = Reference.from_data(data_3d)  # No axis names provided
    print(f"   Input data: {data_3d}")
    print(f"   Generated axes: {ref_3d.axes}")
    print(f"   Generated shape: {ref_3d.shape}")
    print(f"   Reference tensor: {ref_3d.tensor}")
    
    # Example 4: Irregular tensor with skip values
    print("\n4. Creating Reference from irregular tensor:")
    data_irregular = [['a1', 'a2'], ['b1'], ['c1', 'c2', 'c3']]
    ref_irregular = Reference.from_data(data_irregular, axis_names=['groups', 'items'])
    print(f"   Input data: {data_irregular}")
    print(f"   Generated axes: {ref_irregular.axes}")
    print(f"   Generated shape: {ref_irregular.shape}")
    print(f"   Reference tensor: {ref_irregular.tensor}")
    print(f"   Note: Missing elements are padded with '@#SKIP#@'")

def demonstrate_none_axis_auto_removal():
    """
    Demonstrate the automatic removal of _none_axis when other axes are present.
    """
    print("=== _none_axis Auto-Removal Demonstration ===\n")
    
    # Example 1: Creating a reference with _none_axis using from_data
    print("1. Creating a reference with _none_axis:")
    # Create a reference with _none_axis using from_data
    ref_with_none = Reference.from_data([["hello", "world"]], axis_names=['_none_axis', 'items'])
    print(f"   Original axes: {ref_with_none.axes}")
    print(f"   Original shape: {ref_with_none.shape}")
    print(f"   Original tensor: {ref_with_none.tensor}")
    
    # Example 2: Cross product with another reference
    print("\n2. Cross product with another reference:")
    other_ref = Reference.from_data(['a', 'b'], axis_names=['items'])
    print(f"   Other reference axes: {other_ref.axes}")
    print(f"   Other reference shape: {other_ref.shape}")
    
    combined = cross_product([ref_with_none, other_ref])
    print(f"   Combined axes: {combined.axes}")
    print(f"   Combined shape: {combined.shape}")
    print(f"   Combined tensor: {combined.tensor}")
    print(f"   Note: _none_axis was automatically removed!")
    
    # Example 3: Element action with _none_axis
    print("\n3. Element action with _none_axis:")
    def combine_strings(*args):
        return " + ".join(str(arg) for arg in args)
    
    result = element_action(combine_strings, [ref_with_none, other_ref])
    print(f"   Result axes: {result.axes}")
    print(f"   Result shape: {result.shape}")
    print(f"   Result tensor: {result.tensor}")
    print(f"   Note: _none_axis was automatically removed!")
    
    # Example 4: When _none_axis is the only axis
    print("\n4. When _none_axis is the only axis (no removal):")
    single_none = Reference.from_data(["single_value"], axis_names=['_none_axis'])
    print(f"   Single _none_axis axes: {single_none.axes}")
    print(f"   Single _none_axis shape: {single_none.shape}")
    print(f"   Single _none_axis tensor: {single_none.tensor}")
    print(f"   Note: _none_axis is preserved when it's the only axis!")



if __name__ == "__main__":

    irregular_tensor_example()












