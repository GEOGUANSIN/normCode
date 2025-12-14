import copy
from typing import Any, Optional, List
import logging

# Dev mode flag - when True, exceptions in cross_action and element_action are raised instead of returning skip values
_DEV_MODE = False

def set_dev_mode(enabled: bool):
    """
    Enable or disable dev mode for Reference operations.
    
    When dev mode is enabled, exceptions in cross_action and element_action
    will be raised instead of being silently converted to skip values.
    This is useful for debugging.
    
    Args:
        enabled (bool): True to enable dev mode, False to disable
    """
    global _DEV_MODE
    _DEV_MODE = enabled
    if enabled:
        logging.info("Reference dev mode ENABLED - exceptions will be raised")
    else:
        logging.info("Reference dev mode DISABLED - exceptions will return skip values")

def get_dev_mode() -> bool:
    """Check if dev mode is currently enabled."""
    global _DEV_MODE
    return _DEV_MODE

class Reference:
    def __init__(self, axes, shape, initial_value=None, skip_value="@#SKIP#@"):
        if len(axes) != len(set(axes)):
            raise ValueError("Axes must be unique")
        if len(axes) != len(shape):
            raise ValueError("Axes and shape must have the same length")
        self.axes: list[str] = axes
        self.shape: tuple[int, ...] = tuple(shape)
        self.skip_value: str = skip_value
        self.data: list[Any] = self._create_nested_list(shape, initial_value)

    def copy(self):
        """
        Create a deep copy of the Reference object.
        
        Returns:
            Reference: A new Reference object with copied axes, shape, skip_value, and data
        """
        new_ref = Reference(
            axes=self.axes.copy(),
            shape=self.shape,
            initial_value=None,
            skip_value=self.skip_value
        )
        new_ref.data = copy.deepcopy(self.data)
        return new_ref

    @classmethod
    def from_data(cls, data, axis_names=None, skip_value="@#SKIP#@"):
        """
        Create a Reference object from input data by automatically discovering axes and shape.
        
        Args:
            data: The input data (nested list structure)
            axis_names: Optional list of axis names. If None, will generate generic names.
            skip_value: Value to use for missing/skip elements
            
        Returns:
            Reference: A new Reference object with automatically discovered axes and shape
        """
        if not isinstance(data, list):
            raise TypeError("Data must be a nested list structure")
        
        # Create a temporary instance to compute shape
        temp_ref = cls([], (), initial_value=None, skip_value=skip_value)
        shape = temp_ref._compute_irregular_shape(data)
        
        # Generate axis names if not provided, or adjust shape if they are provided.
        if axis_names is None:
            axis_names = [f"axis_{i}" for i in range(len(shape))]
        else:
            if len(axis_names) > len(shape):
                raise ValueError(f"Number of axis names ({len(axis_names)}) cannot be greater than data rank ({len(shape)})")
            if len(axis_names) < len(shape):
                shape = shape[:len(axis_names)]
        
        # Create the reference
        ref = cls(axis_names, shape, initial_value=None, skip_value=skip_value)
        ref._replace_data(data)  # Use _replace_data to bypass validation and pad correctly
        return ref

    @staticmethod
    def _create_nested_list(shape, initial_value):
        if not shape:
            return initial_value
        return [Reference._create_nested_list(shape[1:], initial_value) for _ in range(shape[0])]

    @property
    def tensor(self):
        """Direct access to the underlying tensor data structure with skip values"""
        return self.data

    def get_tensor(self, ignore_skip=False):
        """
        Get the underlying tensor data structure.
        
        Args:
            ignore_skip (bool): If True, returns tensor without skip values.
                              If False, returns the full tensor with skip values.
        
        Returns:
            The tensor data structure
        """
        if ignore_skip:
            return self._remove_skip_values(self.data)
        return self.data

    def _remove_skip_values(self, data):
        """Recursively remove skip values from the tensor data"""
        if not isinstance(data, list):
            return data
        
        result = []
        for item in data:
            if item != self.skip_value:
                if isinstance(item, list):
                    cleaned_item = self._remove_skip_values(item)
                    if cleaned_item:  # Only add non-empty lists
                        result.append(cleaned_item)
                else:
                    result.append(item)
        
        return result

    @tensor.setter
    def tensor(self, value):
        """
        Set the entire tensor with validation for:
        - Rank matches number of axes
        - Regular tensor structure
        """
        if not isinstance(value, list):
            raise TypeError("Tensor must be a nested list structure")

        # Validate that the rank matches
        observed_rank = self._get_rank(value)
        expected_rank = len(self.axes)

        if observed_rank != expected_rank:
            raise ValueError(
                f"Tensor rank mismatch. Got {observed_rank}, "
                f"expected {expected_rank} (number of axes)"
            )

        # For irregular tensors, compute the appropriate shape
        # and update the shape to match the data
        new_shape = self._compute_irregular_shape(value)
        self.shape = new_shape
        
        # Pad the tensor to the computed shape
        padded_data = self._pad_tensor(value, new_shape)
        self.data = padded_data

    def _pad_tensor(self, tensor, target_shape):
        """Pad a tensor to match the target shape with skip values"""
        if not target_shape:
            return tensor

        current_dim = target_shape[0]
        if not isinstance(tensor, list):
            return [self.skip_value] * current_dim

        # Pad the current dimension
        padded = []
        for i in range(current_dim):
            if i < len(tensor):
                padded.append(self._pad_tensor(tensor[i], target_shape[1:]))
            else:
                padded.append(self._pad_tensor(self.skip_value, target_shape[1:]))

        return padded

    def _get_rank(self, lst):
        """Calculate tensor rank by nested list depth"""
        rank = 0
        current = lst
        while isinstance(current, list):
            rank += 1
            if not current:  # Handle empty lists
                break
            current = current[0]
        return rank

    def _compute_shape(self, lst):
        """Calculate tensor shape from nested list structure, handling irregular dimensions"""
        shape = []
        current = lst
        while isinstance(current, list):
            if not current:  # Handle empty lists
                shape.append(0)
                break
            # Handle mixed list and non-list elements
            max_len = 0
            for sublist in current:
                if isinstance(sublist, list):
                    max_len = max(max_len, len(sublist))
                else:
                    max_len = max(max_len, 1)  # Count non-list elements as length 1
            shape.append(max_len)
            
            # Check if we should continue to next dimension
            # For irregular tensors, we need to check if any element is a list
            has_list_elements = any(isinstance(elem, list) for elem in current)
            if has_list_elements:
                # Find the first list element to continue traversal
                for elem in current:
                    if isinstance(elem, list):
                        current = elem
                        break
            else:
                break  # No more list elements found
        return tuple(shape)

    def _compute_irregular_shape(self, lst):
        """Compute shape for irregular tensors, preserving the maximum dimensions"""
        if not isinstance(lst, list):
            return ()
        
        # For the first dimension, use the length of the list
        shape = [len(lst)]
        
        # For subsequent dimensions, recursively compute the maximum shape
        if lst:
            # Find all list elements to determine the next dimension
            list_elements = [elem for elem in lst if isinstance(elem, list)]
            if list_elements:
                # Compute the maximum shape of all sublists
                sub_shapes = [self._compute_irregular_shape(sublist) for sublist in list_elements]
                if sub_shapes:
                    # Find the maximum length for each dimension
                    max_dims = len(max(sub_shapes, key=len))
                    for dim in range(max_dims):
                        max_len = 0
                        for sub_shape in sub_shapes:
                            if dim < len(sub_shape):
                                max_len = max(max_len, sub_shape[dim])
                        shape.append(max_len)
        
        return tuple(shape)

    def _validate_shape(self, lst, expected_shape):
        """Verify dimensions throughout the tensor, allowing for irregular structures"""
        if len(expected_shape) == 0:
            return
        if not isinstance(lst, list):
            return  # Skip validation for non-list elements
        if len(lst) > expected_shape[0]:
            raise ValueError(f"Dimension at level {len(expected_shape)} exceeds maximum. "
                           f"Expected at most {expected_shape[0]}, got {len(lst)}")
        # Only validate sublists if we have more dimensions to check
        if len(expected_shape) > 1:
            for sublist in lst:
                if isinstance(sublist, list):
                    self._validate_shape(sublist, expected_shape[1:])
                # Skip validation for non-list elements

    def get(self, **kwargs):
        """Get element(s) from the tensor, handling skip values"""
        for key in kwargs:
            if key not in self.axes:
                raise KeyError(f"Axis '{key}' not found in {self.axes}")
        indices = []
        for axis in self.axes:
            indices.append(kwargs.get(axis, slice(None)))
        return self._get_element(self.data, indices)

    def _get_element(self, data, indices):
        """Get element(s) from the tensor, handling skip values"""
        if not indices:
            return data
        current = indices[0]
        remaining = indices[1:]
        if isinstance(current, slice):
            result = []
            for i in range(len(data)):
                if i < len(data) and data[i] != self.skip_value:
                    result.append(self._get_element(data[i], remaining))
                else:
                    result.append(self.skip_value)
            return result
        else:
            if current < len(data) and data[current] != self.skip_value:
                return self._get_element(data[current], remaining)
            return self.skip_value

    def set(self, value, **kwargs):
        """Set element(s) in the tensor, handling skip values"""
        for key in kwargs:
            if key not in self.axes:
                raise KeyError(f"Axis '{key}' not found in {self.axes}")
        indices = []
        for axis in self.axes:
            indices.append(kwargs.get(axis, slice(None)))
        self._set_element(self.data, indices, value)

    def _set_element(self, data, indices, value):
        """Set element(s) in the tensor, handling skip values"""
        if not indices:
            if isinstance(value, list):
                raise ValueError("Cannot set a list as a leaf value")
            data[:] = value
            return

        current = indices[0]
        remaining = indices[1:]
        if isinstance(current, slice):
            start, stop, step = current.indices(len(data))
            for i in range(start, stop, step):
                if i >= len(data):
                    data.extend([self.skip_value] * (i - len(data) + 1))
                if remaining:
                    if data[i] == self.skip_value:
                        data[i] = []
                    self._set_element(data[i], remaining, value)
                else:
                    data[i] = value
        else:
            if current >= len(data):
                data.extend([self.skip_value] * (current - len(data) + 1))
            if remaining:
                if data[current] == self.skip_value:
                    data[current] = []
                self._set_element(data[current], remaining, value)
            else:
                data[current] = value

    def slice(self, *selected_axes):
        # Handle case where no axes are provided
        if not selected_axes:
            # Create a reference with single axis "_none_axis" and shape (1,)
            # Store the entire tensor as a single element
            return Reference(
                axes=["_none_axis"],
                shape=(1,),
                initial_value=None,
                skip_value="@#SKIP#@"
            )._replace_data([self.tensor])

        # Validate selected axes
        for axis in selected_axes:
            if axis not in self.axes:
                raise KeyError(f"Axis '{axis}' not found in {self.axes}")
        if len(selected_axes) != len(set(selected_axes)):
            raise ValueError("Duplicate axes in selection")

        # Calculate new shape based on selected axes
        new_shape = tuple(self.shape[self.axes.index(axis)] for axis in selected_axes)

        # Build sliced data structure
        def build_sliced_data(current_axes, index_dict):
            if not current_axes:
                # Get the sub-tensor for current indices
                kwargs = {selected_axes[i]: index_dict[i] for i in range(len(index_dict))}
                sub_tensor = self.get(**kwargs)
                if sub_tensor == self.skip_value:
                    return "@#SKIP#@"
                # If any element in the sub-tensor is a skip value, return skip value for the entire sub-tensor
                if isinstance(sub_tensor, list):
                    if any(elem == self.skip_value for elem in sub_tensor):
                        return "@#SKIP#@"
                return sub_tensor
            else:
                axis = current_axes[0]
                axis_size = new_shape[len(index_dict)]
                return [build_sliced_data(current_axes[1:], index_dict + [i])
                        for i in range(axis_size)]

        sliced_data = build_sliced_data(selected_axes, [])

        # Create and return new Reference
        return Reference(
            axes=list(selected_axes),
            shape=new_shape,
            initial_value=None,
            skip_value="@#SKIP#@"
        )._replace_data(sliced_data)

    def shape_view(self, view: Optional[List[str]] = None) -> 'Reference':
        """Apply view by selecting specified axes, using all when empty.
        
        Args:
            view: Optional list of axes to keep in the view. If None or empty, uses all axes.
            
        Returns:
            A new Reference with only the selected axes
        """
        # Use all axes if view is empty
        selected_axes = view if view else self.axes.copy()

        # Validate existence of selected axes
        available_axes = set(self.axes)
        for axis in selected_axes:
            if axis not in available_axes:
                raise ValueError(f"Axis '{axis}' not found in reference axes")

        # Create new reference with selected axes
        return self.slice(*selected_axes)

    def _replace_data(self, new_data):
        """Private method to directly set data (bypassing normal initialization)"""
        # Ensure the new data is properly padded
        padded_data = self._pad_tensor(new_data, self.shape)
        self.data = padded_data
        return self

    def _auto_remove_none_axis(self):
        """
        Automatically remove _none_axis if other axes are present.
        This makes the behavior more intuitive when _none_axis is used as a temporary container.
        """
        if "_none_axis" in self.axes and len(self.axes) > 1:
            # Remove _none_axis from axes and shape
            none_axis_index = self.axes.index("_none_axis")
            new_axes = [axis for axis in self.axes if axis != "_none_axis"]
            new_shape = tuple(dim for i, dim in enumerate(self.shape) if i != none_axis_index)
            
            # Extract the actual data from the _none_axis dimension
            if len(self.shape) == 1:
                # If only _none_axis, extract the single element
                new_data = self.data[0]
            else:
                # If multiple axes, extract data from _none_axis dimension
                new_data = self._extract_from_none_axis(self.data, none_axis_index)
            
            # Create new reference without _none_axis
            result = Reference(
                axes=new_axes,
                shape=new_shape,
                initial_value=None,
                skip_value=self.skip_value
            )._replace_data(new_data)
            return result
        
        return self

    def _extract_from_none_axis(self, data, none_axis_index):
        """Extract data from the _none_axis dimension"""
        if none_axis_index == 0:
            # _none_axis is the first dimension
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data
        else:
            # _none_axis is in a deeper dimension
            if not isinstance(data, list):
                return data
            
            result = []
            for item in data:
                if isinstance(item, list):
                    extracted = self._extract_from_none_axis(item, none_axis_index - 1)
                    result.append(extracted)
                else:
                    result.append(item)
            return result

    def _reshape_from_list(self, data_iter, shape):
        """Recursively builds a nested list from a flat iterator and a shape."""
        if not shape:
            try:
                return next(data_iter)
            except StopIteration:
                return self.skip_value

        return [self._reshape_from_list(data_iter, shape[1:]) for _ in range(shape[0])]

    def append(self, other: 'Reference', by_axis: Optional[str] = None) -> 'Reference':
        if by_axis is None:
            if not self.axes:
                raise ValueError("Cannot infer axis for append when reference has no axes.")

            # Find the axes in `self` that are not in `other`, preserving order and duplicates.
            other_axes_list = list(other.axes)
            unmatched_target_axes = []
            for axis in self.axes:
                try:
                    # Try to "consume" an axis from the other reference
                    other_axes_list.remove(axis)
                except ValueError:
                    # If it fails, the axis is unique to self
                    unmatched_target_axes.append(axis)

            # 1. Unique axis inference on the unmatched set (highest priority)
            if len(unmatched_target_axes) == 1:
                by_axis = unmatched_target_axes[0]
            # 2. Heuristic based on the rank of the *unmatched* axes
            else:
                unmatched_source_axes_count = len(other_axes_list)
                if 0 < unmatched_source_axes_count < len(unmatched_target_axes):
                    index = len(unmatched_target_axes) - unmatched_source_axes_count
                    by_axis = unmatched_target_axes[index]
                # 3. Final fallback to the last axis
                else:
                    by_axis = self.axes[-1]

        if by_axis not in self.axes:
            raise ValueError(f"Axis '{by_axis}' not found in {self.axes}")

        new_ref = self.copy()
        axis_idx = new_ref.axes.index(by_axis)

        # Pattern 1: Appending new elements to a container axis (e.g., by_axis is not the last axis)
        if axis_idx < len(new_ref.axes) - 1:
            slice_shape = new_ref.shape[axis_idx + 1:]
            other_leaves = list(other._get_leaves())

            import math
            slice_len = math.prod(slice_shape) if slice_shape else 1

            new_slices = []
            if slice_len > 0:
                if len(other_leaves) % slice_len != 0:
                    raise ValueError(
                        f"Shape mismatch: cannot reshape data of length {len(other_leaves)} "
                        f"into slices of shape {slice_shape} (slice size is {slice_len})")

                if other_leaves:
                    num_new_slices = len(other_leaves) // slice_len
                    leaves_iter = iter(other_leaves)
                    new_slices = [self._reshape_from_list(leaves_iter, slice_shape) for _ in range(num_new_slices)]
            elif len(other_leaves) > 0:  # slice_len is 0 and there is data
                raise ValueError(f"Shape mismatch: cannot append data to zero-sized slice shape {slice_shape}")

            def _recursive_append_slices(data, depth):
                if depth == axis_idx - 1:
                    # We are at the parent level of the axis to append to.
                    # Append the new slices to each sublist at this level.
                    for sublist in data:
                        if isinstance(sublist, list):
                            sublist.extend(new_slices)
                    return

                # Recurse deeper
                for sublist in data:
                    if isinstance(sublist, list):
                        _recursive_append_slices(sublist, depth + 1)

            if axis_idx == 0:
                new_ref.data.extend(new_slices)
            else:
                _recursive_append_slices(new_ref.data, 0)

            # Update shape
            new_shape = list(new_ref.shape)
            new_shape[axis_idx] += len(new_slices)
            new_ref.shape = tuple(new_shape)

            return new_ref

        # Pattern 2: Appending data within existing elements (by_axis is the last axis)
        else:
            # Determine if it's element-wise or broadcast append
            is_elementwise = False
            if len(self.axes) > 1:
                self_prefix_axes = self.axes[:-1]
                other_prefix_axes = [ax for ax in other.axes if ax in self_prefix_axes]
                
                if set(self_prefix_axes) == set(other_prefix_axes):
                    # Check if shapes match for all prefix axes
                    shapes_match = True
                    for ax in self_prefix_axes:
                        self_ax_idx = self.axes.index(ax)
                        other_ax_idx = other.axes.index(ax)
                        if self.shape[self_ax_idx] != other.shape[other_ax_idx]:
                            shapes_match = False
                            break
                    if shapes_match:
                        is_elementwise = True

            def _recursive_append(self_data, other_data, self_depth):
                if self_depth == axis_idx:
                    # At the target axis, perform append
                    if is_elementwise:
                        append_val = list(other._get_leaves(other_data))
                        return self_data + append_val
                    else:
                        # Broadcast: other_data is the single chunk to append everywhere
                        return self_data + other_data
                else:
                    # Recurse deeper
                    if is_elementwise:
                        if len(self_data) != len(other_data):
                            raise ValueError(f"Shape mismatch at axis '{new_ref.axes[self_depth]}': "
                                             f"{len(self_data)} vs {len(other_data)}")
                        return [_recursive_append(self_item, other_item, self_depth + 1)
                                for self_item, other_item in zip(self_data, other_data)]
                    else:  # broadcast
                        return [_recursive_append(self_item, other_data, self_depth + 1)
                                for self_item in self_data]

            if is_elementwise:
                new_ref.data = _recursive_append(new_ref.data, other.data, 0)
            else:
                # For broadcast, flatten the entire other reference
                other_leaves = list(other._get_leaves())
                new_ref.data = _recursive_append(new_ref.data, other_leaves, 0)

            # Update shape
            if new_ref.data:
                new_shape = list(new_ref.shape)
                # To calculate the new dimension, we need to see how long the inner lists are.
                # We can compute the new shape from the resulting data.
                new_ref.shape = new_ref._compute_irregular_shape(new_ref.data)
                # This might not be perfect if the list is empty, but it's a start.
                if len(new_ref.shape) != len(self.shape):
                     # If the rank changes, we have an issue. For now, assume it doesn't.
                     pass
            
            return new_ref

    def _get_leaves(self, data=None):
        """Recursively yield all non-list elements from a nested list structure."""
        if data is None:
            data = self.data

        if isinstance(data, list):
            for item in data:
                yield from self._get_leaves(item)
        elif data != self.skip_value:
            yield data


def cross_product(references):
    if not references:
        raise ValueError("At least one reference must be provided")

    for ref in references:
        if not isinstance(ref, Reference):
            raise TypeError("All elements must be Reference instances")

    # Collect all axes and validate their shapes
    axis_order = []  # Maintain order of first occurrence
    axis_shapes = {}

    for ref in references:
        for axis in ref.axes:
            if axis not in axis_order:
                axis_order.append(axis)
                axis_index = ref.axes.index(axis)
                axis_shapes[axis] = ref.shape[axis_index]
            else:
                axis_index = ref.axes.index(axis)
                if ref.shape[axis_index] != axis_shapes[axis]:
                    raise ValueError(
                        f"Shape mismatch for axis '{axis}': {ref.shape[axis_index]} vs {axis_shapes[axis]}")

    combined_axes = axis_order
    combined_shape = tuple(axis_shapes[axis] for axis in combined_axes)

    # Build the nested data structure
    def build_data(current_axes, index_dict):
        if not current_axes:
            # Collect elements from all references
            elements = []
            for ref in references:
                # Get relevant indices for this reference
                ref_indices = {axis: index_dict[axis] for axis in ref.axes}
                element = ref.get(**ref_indices)
                elements.append(element)
            
            # If any element is a skip value, return skip value for the entire sub-tensor
            if any(e == ref.skip_value for e, ref in zip(elements, references)):
                return "@#SKIP#@"
            return elements
        else:
            axis = current_axes[0]
            axis_size = axis_shapes[axis]
            return [build_data(current_axes[1:], {**index_dict, axis: i})
                    for i in range(axis_size)]

    # Generate the new data
    new_data = build_data(combined_axes, {})

    # Create and return new Reference with automatic _none_axis removal
    result = Reference(
        axes=combined_axes,
        shape=combined_shape,
        initial_value=None,
        skip_value="@#SKIP#@"
    )._replace_data(new_data)
    
    return result._auto_remove_none_axis()


def join(references: List['Reference'], new_axis_name: str) -> 'Reference':
    """
    Joins a list of references with the same shape along a new axis.

    Args:
        references (List[Reference]): A list of Reference objects to join.
                                      All references must have the same axes and shape.
        new_axis_name (str): The name for the new axis.

    Returns:
        Reference: A new Reference object with the combined data and the new axis.
    """
    if not references:
        raise ValueError("At least one reference must be provided for join operation")

    first_ref = references[0]
    if not isinstance(first_ref, Reference):
        raise TypeError("All elements must be Reference instances")

    common_axes = first_ref.axes
    common_shape = first_ref.shape

    for i, ref in enumerate(references[1:], 1):
        if not isinstance(ref, Reference):
            raise TypeError("All elements must be Reference instances")
        
        # Handle axis permutation
        if ref.axes != common_axes:
            if set(ref.axes) == set(common_axes):
                # Realign axes to match common_axes
                ref = ref.slice(*common_axes)
            else:
                raise ValueError(
                    f"Axis mismatch at index {i}. Expected {common_axes}, got {ref.axes}"
                )
        
        if ref.shape != common_shape:
            raise ValueError(
                f"Shape mismatch at index {i}. Expected {common_shape}, got {ref.shape}"
            )
            
    new_axes = [new_axis_name] + common_axes
    new_shape = (len(references),) + common_shape
    new_data = [ref.tensor for ref in references]  # Use original ref list? No, use aligned refs!

    # We need to update the list of references to use the aligned ones
    # But the loop iterates over references[1:]. first_ref is references[0].
    # Let's restructure slightly to collect aligned references.
    
    aligned_references = [first_ref]
    for i, ref in enumerate(references[1:], 1):
        if not isinstance(ref, Reference):
            raise TypeError("All elements must be Reference instances")
        
        if ref.axes != common_axes:
            if set(ref.axes) == set(common_axes):
                ref = ref.slice(*common_axes)
            else:
                raise ValueError(
                    f"Axis mismatch at index {i}. Expected {common_axes}, got {ref.axes}"
                )
        
        if ref.shape != common_shape:
            raise ValueError(
                f"Shape mismatch at index {i}. Expected {common_shape}, got {ref.shape}"
            )
        aligned_references.append(ref)

    new_axes = [new_axis_name] + common_axes
    new_shape = (len(aligned_references),) + common_shape
    new_data = [ref.tensor for ref in aligned_references]

    # Create and return new Reference
    result = Reference(
        axes=new_axes,
        shape=new_shape,
        initial_value=None,
        skip_value=first_ref.skip_value
    )._replace_data(new_data)

    return result


def cross_action(A, B, new_axis_name):
    # Validate inputs
    if not isinstance(A, Reference) or not isinstance(B, Reference):
        raise TypeError("Both A and B must be Reference instances")

    # Combine axes from A and B
    combined_axes = list(A.axes)  # Start with axes from A
    for axis in B.axes:
        if axis not in combined_axes:
            combined_axes.append(axis)  # Add axes from B that are not already in A

    # Compute the shape of the resulting tensor
    combined_shape = []
    for axis in combined_axes:
        if axis in A.axes and axis in B.axes:
            # Axes shared by A and B must have the same shape
            if A.shape[A.axes.index(axis)] != B.shape[B.axes.index(axis)]:
                raise ValueError(f"Shape mismatch for shared axis '{axis}': "
                               f"{A.shape[A.axes.index(axis)]} vs {B.shape[B.axes.index(axis)]}")
            combined_shape.append(A.shape[A.axes.index(axis)])
        elif axis in A.axes:
            # Axis only in A
            combined_shape.append(A.shape[A.axes.index(axis)])
        else:
            # Axis only in B
            combined_shape.append(B.shape[B.axes.index(axis)])

    # Build the new data structure
    def build_data(current_axes, index_dict):
        if not current_axes:
            # Retrieve the function from A and the input from B
            a_indices = {axis: index_dict[axis] for axis in A.axes}
            b_indices = {axis: index_dict[axis] for axis in B.axes}
            func = A.get(**a_indices)
            input_val = B.get(**b_indices)
            
            if func == A.skip_value or input_val == B.skip_value:
                return "@#SKIP#@"
                
            if not callable(func):
                raise TypeError(f"Element at {a_indices} in A is not a callable function")
            try:
                result = func(input_val)
                if not isinstance(result, list):
                    raise TypeError(f"Function at {a_indices} in A must return a list")
                # If any element in the result is a skip value, return skip value for the entire result
                if any(r == "@#SKIP#@" for r in result):
                    return "@#SKIP#@"
                return result
            except Exception as e:
                # Re-raise specific exceptions that need to propagate up (e.g., for human-in-the-loop)
                # Check if this is a NeedsUserInteraction exception (avoiding import)
                if e.__class__.__name__ == 'NeedsUserInteraction':
                    raise
                # In dev mode, always raise exceptions for debugging
                if get_dev_mode():
                    logging.error(f"cross_action: Exception in dev mode at {a_indices}: {type(e).__name__}: {e}")
                    raise
                return "@#SKIP#@"
        else:
            axis = current_axes[0]
            axis_size = combined_shape[len(index_dict)]
            return [build_data(current_axes[1:], {**index_dict, axis: i})
                    for i in range(axis_size)]

    new_data = build_data(combined_axes, {})

    # Create the new Reference
    new_axes = combined_axes + [new_axis_name]
    retrieved_entry = new_data
    for i in range(len(combined_shape)):
        if not retrieved_entry:
            break
        retrieved_entry = retrieved_entry[0]
    if isinstance(retrieved_entry, str) and retrieved_entry == "@#SKIP#@":
        new_shape = combined_shape + [1]
    else:
        new_shape = combined_shape + [len(retrieved_entry) if retrieved_entry else 0]
    result_ref = Reference(new_axes, new_shape, None, skip_value="@#SKIP#@")
    result_ref._replace_data(new_data)
    return result_ref._auto_remove_none_axis()

def element_action(f, references, index_awareness=False):
    """
    Applies a function element-wise across multiple References with potentially different axes.
    Returns a new Reference with combined axes and results of f applied to aligned elements.

    Args:
        f (callable): Function to apply to elements from the References
        references (list): List of Reference instances
        index_awareness (bool): If True, passes location information as second argument to f

    Returns:
        Reference: New Reference with combined axes and transformed data
    """
    # Validate inputs
    if not references:
        raise ValueError("At least one reference must be provided")
    for ref in references:
        if not isinstance(ref, Reference):
            raise TypeError("All elements must be Reference instances")

    # Collect and validate axes
    combined_axes = []
    axis_sizes = {}

    # Gather all unique axes while preserving order
    for ref in references:
        for axis in ref.axes:
            if axis not in combined_axes:
                combined_axes.append(axis)

    # Validate axis compatibility
    for axis in combined_axes:
        sizes = []
        for ref in references:
            if axis in ref.axes:
                idx = ref.axes.index(axis)
                sizes.append(ref.shape[idx])
        if not all(s == sizes[0] for s in sizes):
            raise ValueError(f"Shape mismatch for axis '{axis}'")
        axis_sizes[axis] = sizes[0]

    # Compute combined shape
    combined_shape = [axis_sizes[axis] for axis in combined_axes]

    # Build the nested data structure
    def build_data(current_axes, index_dict):
        # logging.debug(f"element_action: build_data | current_axes: {current_axes} | index_dict: {index_dict}")
        if not current_axes:
            # Collect elements from all references
            elements = []
            for ref in references:
                # Get relevant indices for this reference
                ref_indices = {axis: index_dict[axis] for axis in ref.axes if axis in index_dict}
                element = ref.get(**ref_indices)

                if element is None:
                    elements.append("@#SKIP#@")
                else:
                    elements.append(element)
            
            # logging.debug(f"element_action: collected elements {elements} for index {index_dict}")

            # Apply function to collected elements
            try:
                if any(e == "@#SKIP#@" for e in elements):
                    return "@#SKIP#@"
                if index_awareness:
                    result = f(*elements, index_dict)
                    # logging.debug(f"element_action: applied function '{f.__name__}' to {elements}, result: {result}")
                    return result
                else:
                    result = f(*elements)
                    # logging.debug(f"element_action: applied function '{f.__name__}' to {elements}, result: {result}")
                    return result
            except Exception as e:
                # Re-raise specific exceptions that need to propagate up (e.g., for human-in-the-loop)
                # Check if this is a NeedsUserInteraction exception (avoiding import)
                if e.__class__.__name__ == 'NeedsUserInteraction':
                    raise
                # In dev mode, always raise exceptions for debugging
                if get_dev_mode():
                    logging.error(f"element_action: Exception in dev mode at {index_dict}: {type(e).__name__}: {e}")
                    raise
                # logging.error(f"element_action: error applying function '{f.__name__}' to {elements}: {e}")
                return "@#SKIP#@"
        else:
            axis = current_axes[0]
            axis_size = axis_sizes[axis]
            return [build_data(current_axes[1:], {**index_dict, axis: i})
                    for i in range(axis_size)]

    # Generate the new data
    new_data = build_data(combined_axes, {})

    # Create and return new Reference with automatic _none_axis removal
    result = Reference(
        axes=combined_axes,
        shape=combined_shape,
        initial_value=None,
        skip_value="@#SKIP#@"
    )._replace_data(new_data)
    
    return result._auto_remove_none_axis()


if __name__ == "__main__":


    # Reference A: stores a function at a=0
    A = Reference(axes=['a'], shape=(1,), initial_value=1)
    A.set(lambda x: {x:x}, a=0)  # Function returns a list of length 2

    # Reference B: stores a value at b=0
    B = Reference(axes=['b'], shape=(1,), initial_value=0)
    B.set(42, b=0)

    # Perform cross action
    result = cross_action(A, B, new_axis_name='result')

    print("A axes:", A.axes, "shape:", A.shape)
    print("B axes:", B.axes, "shape:", B.shape)
    print("Result axes:", result.axes, "shape:", result.shape)
    print("Result tensor:", result.tensor)
    print("Result[0,0]:", result.get(a=0, b=0))



    print("\n=== Example 1: Basic Grade Tensor Creation and Operations ===")
    # Create a 3D tensor for student grades (students × semesters × assignments)
    grades = Reference(
        axes=['student', 'semester', 'assignment'],
        shape=(3, 2, 4),  # 3 students, 2 semesters, 4 assignments
        initial_value=0
    )

    # Set some sample grades
    print("\nSetting initial grades...")
    print("Input data:")
    print("Student 0, Semester 0:")
    print("- Assignment 0: 85")
    print("- Assignment 1: 90")
    print("- Assignment 2: Missing (@#SKIP#@)")
    print("- Assignment 3: 88")
    
    grades.set(85, student=0, semester=0, assignment=0)
    grades.set(90, student=0, semester=0, assignment=1)
    grades.set("@#SKIP#@", student=0, semester=0, assignment=2)  # Missing grade
    grades.set(88, student=0, semester=0, assignment=3)

    # Demonstrate get operations with explanations
    print("\nOutput:")
    print("Grades for Student 0, Semester 0:", grades.get(student=0, semester=0))
    print("Note: The '@#SKIP#@' indicates a missing grade for assignment 2")

    print("\n=== Example 2: Cross Product with Attendance Data ===")
    # Create attendance data
    print("\nInput data:")
    print("Grades data (from previous example):")
    print("- Student 0, Semester 0: [85, 90, @#SKIP#@, 88]")
    print("\nAttendance data:")
    print("- Student 0, Semester 0: 95%")
    print("- Student 0, Semester 1: Missing (@#SKIP#@)")
    print("- Student 1, Semester 0: 85%")
    
    attendance = Reference(
        axes=['student', 'semester'],
        shape=(3, 2),
        initial_value=0
    )
    attendance.set(95, student=0, semester=0)
    attendance.set("@#SKIP#@", student=0, semester=1)  # Missing attendance
    attendance.set(85, student=1, semester=0)

    # Combine grades and attendance
    print("\nPerforming cross product operation...")
    combined = cross_product([grades, attendance])
    print("\nOutput:")
    print("Combined data structure:")
    print("Axes:", combined.axes)
    print("Shape:", combined.shape)
    print("\nSample combined data for Student 0, Semester 0:")
    print(combined.get(student=0, semester=0))
    print("Note: The '@#SKIP#@' appears where either grades or attendance is missing")

    print("\n=== Example 3: Slicing Operations ===")
    print("\nInput data:")
    print("Grades data (from previous example):")
    print("- Student 0, Semester 0: [85, 90, @#SKIP#@, 88]")
    
    # Create a slice of grades by student and assignment
    print("\nCreating a slice of grades by student and assignment...")
    student_assignment_slice = grades.slice('student', 'assignment')
    print("\nOutput:")
    print("Slice axes:", student_assignment_slice.axes)
    print("Slice shape:", student_assignment_slice.shape)
    print("\nGrades for Student 0 across all assignments:")
    print(student_assignment_slice.get(student=0))
    print("Note: Missing grades are marked with '@#SKIP#@'")

    # Test slicing with no axes (new functionality)
    print("\n=== Example 3b: Slicing with No Axes ===")
    print("\nInput data:")
    print("Grades data (from previous example):")
    print("- Shape: (3, 2, 4) with axes ['student', 'semester', 'assignment']")
    
    print("\nCreating a slice with no axes specified...")
    no_axis_slice = grades.slice()
    print("\nOutput:")
    print("Slice axes:", no_axis_slice.axes)
    print("Slice shape:", no_axis_slice.shape)
    print("\nEntire tensor stored at _none_axis=0:")
    print(no_axis_slice.get(_none_axis=0))
    print("Note: The entire tensor is stored as a single element with axis '_none_axis'")

    print("\n=== Example 4: Cross Action with Functions ===")
    print("\nInput data:")
    print("Functions (with axis 'x'):")
    print("- (x=0): [z, z*2]")
    print("- (x=1): [z+1, z-1]")
    print("- (x=2): Missing (@#SKIP#@)")
    print("\nInput values (with axis 'y'):")
    print("- (y=0): 5")
    print("- (y=1): 3")
    print("- (y=2): Missing (@#SKIP#@)")
    
    # Create a reference with functions (only axis 'x')
    functions = Reference(['x'], (3,))
    functions.set(lambda z: [z, z*2], x=0)  # Function that returns [input, input*2]
    functions.set(lambda z: [z+1, z-1], x=1)  # Function that returns [input+1, input-1]
    functions.set("@#SKIP#@", x=2)  # Missing function

    # Create a reference with values (only axis 'y')
    values = Reference(['y'], (3,))
    values.set(5, y=0)  # Input value 5
    values.set(3, y=1)  # Input value 3
    values.set("@#SKIP#@", y=2)  # Missing value

    print("\nPerforming cross action between functions and values...")
    print("Note: Functions and values share no axes, so the result will have both 'x' and 'y' axes")
    result = cross_action(functions, values, "result")
    print("\nOutput:")
    print("Result structure:")
    print("Axes:", result.axes)
    print("Shape:", result.shape)
    print("\nSample results:")
    print("For x=0, y=0: Function [z, z*2] applied to 5 =", result.get(x=0, y=0))
    print("For x=0, y=1: Function [z, z*2] applied to 3 =", result.get(x=0, y=1))
    print("For x=0, y=2: Function [z, z*2] applied to missing =", result.get(x=0, y=2))
    print("For x=1, y=0: Function [z+1, z-1] applied to 5 =", result.get(x=1, y=0))
    print("For x=1, y=1: Function [z+1, z-1] applied to 3 =", result.get(x=1, y=1))
    print("For x=1, y=2: Function [z+1, z-1] applied to missing =", result.get(x=1, y=2))
    print("For x=2, y=0: Missing function applied to 5 =", result.get(x=2, y=0))
    print("For x=2, y=1: Missing function applied to 3 =", result.get(x=2, y=1))
    print("For x=2, y=2: Missing function applied to missing =", result.get(x=2, y=2))
    print("\nNote: '@#SKIP#@' appears where either function or input is missing")

    print("\n=== Example 5: Element-wise Operations ===")
    print("\nInput data:")
    print("Reference A:")
    print("- (x=0,y=0): 1")
    print("- (x=0,y=1): 2")
    print("- (x=1,y=0): Missing (@#SKIP#@)")
    print("\nReference B:")
    print("- (x=0,y=0): 3")
    print("- (x=0,y=1): 4")
    print("- (x=1,y=0): 5")
    
    # Create two references for element-wise operations
    A = Reference(['x', 'y'], (2, 2))
    A.set(1, x=0, y=0)
    A.set(2, x=0, y=1)
    A.set("@#SKIP#@", x=1, y=0)

    B = Reference(['x', 'y'], (2, 2))
    B.set(3, x=0, y=0)
    B.set(4, x=0, y=1)
    B.set(5, x=1, y=0)

    print("\nPerforming element-wise addition...")
    def add(a, b):
        return a + b

    result = element_action(add, [A, B])
    print("\nOutput:")
    print("Result axes:", result.axes)
    print("Result shape:", result.shape)
    print("\nSample results:")
    print("For x=0, y=0: 1 + 3 =", result.get(x=0, y=0))
    print("For x=0, y=1: 2 + 4 =", result.get(x=0, y=1))
    print("For x=1, y=0: Missing + 5 =", result.get(x=1, y=0))
    print("Note: '@#SKIP#@' appears where any input is missing")


    print("\n=== Example 6: Append Operation ===")
    print("\n--- Pattern 1: Appending new elements to a container ---")
    # Corresponds to: f(B[A[1,2], [3,4]], C[5,6], by_axis=B) = B[A[1,2], [3,4], [5,6]]
    target_ref = Reference.from_data([[1, 2], [3, 4]], axis_names=['B', 'A'])
    source_ref = Reference.from_data([5, 6], axis_names=['C'])
    result_ref = target_ref.append(source_ref, by_axis='B')
    print("Target:", target_ref.tensor)
    print("Source:", source_ref.tensor)
    print("Append by axis 'B':")
    print("  Result tensor:", result_ref.tensor)
    print("  Result shape:", result_ref.shape)

    print("\n--- Pattern 2a: Element-wise append ---")
    # Corresponds to: f(B[A[1,2], [3,4]], B[C[5],[6]], by_axis=A) = B[A[1,2,5], [3,4,6]]
    target_ref = Reference.from_data([[1, 2], [3, 4]], axis_names=['B', 'A'])
    source_ref = Reference.from_data([[5], [6]], axis_names=['B', 'C'])
    result_ref = target_ref.append(source_ref, by_axis='A')
    print("Target:", target_ref.tensor)
    print("Source:", source_ref.tensor)
    print("Append by axis 'A' (element-wise):")
    print("  Result tensor:", result_ref.tensor)
    print("  Result shape:", result_ref.shape)

    print("\n--- Pattern 2b: Broadcast append ---")
    # Corresponds to: f(B[A[1,2], [3,4]], C[5,6], by_axis=A) = B[A[1,2,5,6], [3,4,5,6]]
    target_ref = Reference.from_data([[1, 2], [3, 4]], axis_names=['B', 'A'])
    source_ref = Reference.from_data([5, 6], axis_names=['C'])
    result_ref = target_ref.append(source_ref, by_axis='A')
    print("Target:", target_ref.tensor)
    print("Source:", source_ref.tensor)
    print("Append by axis 'A' (broadcast):")
    print("  Result tensor:", result_ref.tensor)
    print("  Result shape:", result_ref.shape)
    
    print("\n--- Error case: Shape mismatch ---")
    # Corresponds to: f(B[A[1,2], [3,4]], B[C[5],[6],[7]], by_axis=B)=ERROR:mismatch_shape at A
    target_ref = Reference.from_data([[1, 2], [3, 4]], axis_names=['B', 'A'])
    source_ref = Reference.from_data([5, 6, 7], axis_names=['C'])
    try:
        target_ref.append(source_ref, by_axis='B')
    except ValueError as e:
        print("Caught expected error:", e)

    print("\n=== Example 7: Advanced Append Operations ===")
    print("\n--- Pattern 1: Appending to a nested container axis ---")
    # Corresponds to: f(D[B[A[1,2], [3,4]]], C[5,6], by_axis=B) = D[B[A[1,2], [3,4], [5,6]]]
    target_ref = Reference.from_data([[[1, 2], [3, 4]]], axis_names=['D', 'B', 'A'])
    source_ref = Reference.from_data([5, 6], axis_names=['C'])
    result_ref = target_ref.append(source_ref, by_axis='B')
    print("Target:", target_ref.tensor)
    print("Source:", source_ref.tensor)
    print("Append by axis 'B':")
    print("  Result tensor:", result_ref.tensor)
    print("  Result shape:", result_ref.shape)
    print("  Note: A new slice '[5, 6]' was appended to each sublist along the 'B' axis.")

    print("\n--- Pattern 2: Broadcast append to the last axis ---")
    # Corresponds to: f(D[B[A[1,2], [3,4]]], B[5,6], by_axis=A) = D[B[A[1,2,5,6], [3,4,5,6]]]
    target_ref = Reference.from_data([[[1, 2], [3, 4]]], axis_names=['D', 'B', 'A'])
    source_ref = Reference.from_data([5, 6], axis_names=['B']) # Note: source_ref axis doesn't matter for broadcast
    result_ref = target_ref.append(source_ref, by_axis='A')
    print("Target:", target_ref.tensor)
    print("Source:", source_ref.tensor)
    print("Append by axis 'A' (broadcast):")
    print("  Result tensor:", result_ref.tensor)
    print("  Result shape:", result_ref.shape)
    print("  Note: The source data '[5, 6]' was broadcast-appended to every list along the 'A' axis.")


    print("\n=== Example 8: More Complex Append Scenarios ===")
    print("\n--- Appending a multi-dimensional slice to a nested axis ---")
    # Target has a nested structure where the slice shape is 2x2
    target_ref = Reference.from_data(
        [[[[1, 2], [3, 4]]]], # Shape (1, 1, 2, 2)
        axis_names=['E', 'D', 'B', 'A']
    )
    # Source data can be formed into a 2x2 slice
    source_ref = Reference.from_data([5, 6, 7, 8], axis_names=['C'])
    result_ref = target_ref.append(source_ref, by_axis='D')
    print("Target:", target_ref.tensor)
    print("Source:", source_ref.tensor)
    print("Append by nested axis 'D':")
    print("  Result tensor:", result_ref.tensor)
    print("  Result shape:", result_ref.shape)
    print("  Note: The source data was reshaped into a [2, 2] slice and appended at the 'D' axis level.")

    print("\n--- True element-wise append to the last axis ---")
    # Target and Source share prefix axes 'D' and 'B'
    target_ref = Reference.from_data(
        [[[1, 2], [3, 4]], [[11, 12], [13, 14]]], # Shape (2, 2, 2)
        axis_names=['D', 'B', 'A']
    )
    source_ref = Reference.from_data(
        [[[5], [6]], [[15], [16]]], # Shape (2, 2, 1)
        axis_names=['D', 'B', 'C']
    )
    result_ref = target_ref.append(source_ref, by_axis='A')
    print("Target:", target_ref.tensor)
    print("Source:", source_ref.tensor)
    print("Append by axis 'A' (element-wise):")
    print("  Result tensor:", result_ref.tensor)
    print("  Result shape:", result_ref.shape)
    print("  Note: Appends happened element-wise based on matching 'D' and 'B' axes.")

    print("\n--- Error case: Shape mismatch on nested append ---")
    target_ref = Reference.from_data([[[1, 2], [3, 4]]], axis_names=['D', 'B', 'A'])
    # Source data has 3 elements, which doesn't fit into slices of size 2 (shape of 'A')
    source_ref = Reference.from_data([5, 6, 7], axis_names=['C'])
    print("Target:", target_ref.tensor)
    print("Source:", source_ref.tensor)
    try:
        target_ref.append(source_ref, by_axis='B')
    except ValueError as e:
        print("Caught expected error:", e)

    print("\n--- User-provided nested append case ---")
    target_ref = Reference.from_data([[[1, 2], [3, 4]]], axis_names=['D', 'B', 'A'])
    source_ref = Reference.from_data([[5, 6], [7, 8]], axis_names=['X', 'Y'])
    print("Target:", target_ref.tensor)
    print("Source:", source_ref.tensor)
    result_ref = target_ref.append(source_ref, by_axis='B')
    print("Append by axis 'B':")
    print("  Result tensor:", result_ref.tensor)
    print("  Result shape:", result_ref.shape)

    print("\n--- Appending with implicit last axis ---")
    target_ref = Reference.from_data(
        [[[1, 2], [3, 4]], [[11, 12], [13, 14]]],  # Shape (2, 2, 2)
        axis_names=['D', 'B', 'A']
    )
    source_ref = Reference.from_data(
        [[[5], [6]], [[15], [16]]],  # Shape (2, 2, 1)
        axis_names=['D', 'B', 'C']
    )
    # by_axis is omitted, should default to 'A'
    result_ref = target_ref.append(source_ref)
    print("Target:", target_ref.tensor)
    print("Source:", source_ref.tensor)
    print("Append with implicit axis ('A'):")
    print("  Result tensor:", result_ref.tensor)
    print("  Result shape:", result_ref.shape)
    print("  Note: `by_axis` was inferred as 'A', the unique axis in target not in source.")

    print("\n--- Appending with rank-based axis inference ---")
    # Target axes are [D, B, A] (rank 3). Source axes are [X, Y] (rank 2).
    # There is no unique unmatched axis.
    # The heuristic len(target_axes) - len(source_axes) = 3 - 2 = 1 is used.
    # The inferred axis is target_axes[1], which is 'B'.
    target_ref = Reference.from_data([[[1, 2], [3, 4]]], axis_names=['D', 'B', 'A'])
    source_ref = Reference.from_data([[5, 6], [7, 8]], axis_names=['X', 'Y'])
    result_ref = target_ref.append(source_ref)
    print("Target:", target_ref.tensor)
    print("Source:", source_ref.tensor)
    print("Append with rank-inferred axis ('B'):")
    print("  Result tensor:", result_ref.tensor)
    print("  Result shape:", result_ref.shape)
    print("  Note: `by_axis` was inferred as 'B' based on source rank.")

    print("\n--- Appending with rank-based inference on unique axes ---")
    # Target axes are [a, b, c, b] (unmatched are [b, c, b], rank 3).
    # Source axes are [a, x, y] (unmatched are [x, y], rank 2).
    # The heuristic len(unmatched_target) - len(unmatched_source) = 3 - 2 = 1 is used.
    # The inferred axis is unmatched_target[1], which is 'c'.
    target_ref = Reference(axes=['a', 'b', 'c', 'b'], shape=(1, 1, 2, 2))
    target_ref.tensor = [[[[1, 2], [3, 4]]]]
    source_ref = Reference.from_data([[5, 6], [7, 8]], axis_names=['x', 'y'])
    # Need to add 'a' to source_ref to match the scenario
    source_ref = Reference.from_data([[[5, 6], [7, 8]]], axis_names=['a', 'x', 'y'])
    result_ref = target_ref.append(source_ref)
    print("Target axes:", target_ref.axes)
    print("Source axes:", source_ref.axes)
    print("Append with rank-inferred unique axis ('c'):")
    print("  Result tensor:", result_ref.tensor)
    print("  Result shape:", result_ref.shape)
    print("  Note: `by_axis` was inferred as 'c' by applying rank logic to unique axes.")


    print("\n=== Example 9: Join Operation ===")
    print("\n--- Joining two references with the same shape ---")
    ref1 = Reference.from_data([[1, 2], [3, 4]], axis_names=['B', 'A'])
    ref2 = Reference.from_data([[5, 6], [7, 8]], axis_names=['B', 'A'])

    joined_ref = join([ref1, ref2], new_axis_name='C')

    print("Reference 1:", ref1.tensor)
    print("Reference 2:", ref2.tensor)
    print("Joined reference tensor (new axis 'C' prepended):")
    print("  Result tensor:", joined_ref.tensor)
    print("  Result axes:", joined_ref.axes)
    print("  Result shape:", joined_ref.shape)

    print("\n--- Error case: Mismatched shapes ---")
    ref3 = Reference.from_data([9, 10], axis_names=['B'])
    try:
        join([ref1, ref3], new_axis_name='C')
    except ValueError as e:
        print("Caught expected error:", e)