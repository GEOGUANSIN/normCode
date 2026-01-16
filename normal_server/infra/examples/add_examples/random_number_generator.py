"""
Random number generator for testing the number pair addition example.

This module provides functions to generate random numbers as strings with
various configurations for testing purposes.
"""

import random
from typing import List, Tuple, Optional, Union


class RandomNumberGenerator:
    """Generates random numbers as strings for testing purposes."""
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the random number generator.
        
        Args:
            seed: Optional seed for reproducible random generation
        """
        if seed is not None:
            random.seed(seed)
        self.seed = seed
    
    def generate_single_number(self, 
                             min_length: int = 1, 
                             max_length: int = 5,
                             leading_zero_allowed: bool = False) -> str:
        """
        Generate a single random number as a string.
        
        Args:
            min_length: Minimum number of digits (default: 1)
            max_length: Maximum number of digits (default: 5)
            leading_zero_allowed: Whether to allow leading zeros (default: False)
            
        Returns:
            Random number as a string
            
        Raises:
            ValueError: If min_length > max_length or if min_length < 1
        """
        if min_length > max_length:
            raise ValueError(f"min_length ({min_length}) cannot be greater than max_length ({max_length})")
        if min_length < 1:
            raise ValueError("min_length must be at least 1")
        
        # Choose random length within bounds
        length = random.randint(min_length, max_length)
        
        if leading_zero_allowed:
            # Generate number with possible leading zeros
            digits = [str(random.randint(0, 9)) for _ in range(length)]
            return ''.join(digits)
        else:
            # Generate number without leading zeros
            # First digit cannot be 0
            first_digit = str(random.randint(1, 9))
            remaining_digits = [str(random.randint(0, 9)) for _ in range(length - 1)]
            return first_digit + ''.join(remaining_digits)
    
    def generate_number_pair(self, 
                           min_length: int = 1, 
                           max_length: int = 5,
                           same_length: bool = False,
                           leading_zero_allowed: bool = False) -> Tuple[str, str]:
        """
        Generate a pair of random numbers as strings.
        
        Args:
            min_length: Minimum number of digits for each number (default: 1)
            max_length: Maximum number of digits for each number (default: 5)
            same_length: Whether both numbers should have the same length (default: False)
            leading_zero_allowed: Whether to allow leading zeros (default: False)
            
        Returns:
            Tuple of two random numbers as strings
        """
        if same_length:
            # Both numbers have the same random length
            length = random.randint(min_length, max_length)
            num1 = self.generate_single_number(length, length, leading_zero_allowed)
            num2 = self.generate_single_number(length, length, leading_zero_allowed)
        else:
            # Numbers can have different lengths
            num1 = self.generate_single_number(min_length, max_length, leading_zero_allowed)
            num2 = self.generate_single_number(min_length, max_length, leading_zero_allowed)
        
        return (num1, num2)
    
    def generate_multiple_pairs(self, 
                              count: int,
                              min_length: int = 1, 
                              max_length: int = 5,
                              same_length: bool = False,
                              leading_zero_allowed: bool = False) -> List[Tuple[str, str]]:
        """
        Generate multiple pairs of random numbers.
        
        Args:
            count: Number of pairs to generate
            min_length: Minimum number of digits for each number (default: 1)
            max_length: Maximum number of digits for each number (default: 5)
            same_length: Whether both numbers in each pair should have the same length (default: False)
            leading_zero_allowed: Whether to allow leading zeros (default: False)
            
        Returns:
            List of tuples containing random number pairs
        """
        return [self.generate_number_pair(min_length, max_length, same_length, leading_zero_allowed) 
                for _ in range(count)]
    
    def generate_with_constraints(self, 
                                min_sum: Optional[int] = None,
                                max_sum: Optional[int] = None,
                                min_length: int = 1, 
                                max_length: int = 5,
                                max_attempts: int = 1000) -> Tuple[str, str]:
        """
        Generate a number pair that meets sum constraints.
        
        Args:
            min_sum: Minimum allowed sum of the two numbers (optional)
            max_sum: Maximum allowed sum of the two numbers (optional)
            min_length: Minimum number of digits for each number (default: 1)
            max_length: Maximum number of digits for each number (default: 5)
            max_attempts: Maximum number of attempts to find valid pair (default: 1000)
            
        Returns:
            Tuple of two random numbers that meet the constraints
            
        Raises:
            RuntimeError: If no valid pair is found within max_attempts
        """
        for _ in range(max_attempts):
            num1, num2 = self.generate_number_pair(min_length, max_length)
            try:
                sum_value = int(num1) + int(num2)
                
                # Check constraints
                if min_sum is not None and sum_value < min_sum:
                    continue
                if max_sum is not None and sum_value > max_sum:
                    continue
                
                return (num1, num2)
            except ValueError:
                # Skip if conversion fails (shouldn't happen with our generator)
                continue
        
        raise RuntimeError(f"Could not generate valid pair within {max_attempts} attempts")
    
    def generate_edge_cases(self) -> List[Tuple[str, str]]:
        """
        Generate edge case number pairs for testing.
        
        Returns:
            List of edge case number pairs
        """
        edge_cases = [
            ("0", "0"),           # Both zeros
            ("1", "1"),           # Smallest non-zero
            ("9", "9"),           # Single digit max
            ("10", "10"),         # Two digit minimum
            ("99", "99"),         # Two digit max
            ("100", "100"),       # Three digit minimum
            ("999", "999"),       # Three digit max
            ("0", "1"),           # Zero and one
            ("1", "0"),           # One and zero
            ("0", "99"),          # Zero and large number
            ("99", "0"),          # Large number and zero
            ("1", "99"),          # Small and large
            ("99", "1"),          # Large and small
            ("123", "456"),       # Different lengths
            ("9999", "1"),        # Very different lengths
            ("0001", "0002"),     # Leading zeros (if allowed)
        ]
        return edge_cases
    
    def generate_carry_cases(self, min_length: int = 2, max_length: int = 4) -> List[Tuple[str, str]]:
        """
        Generate number pairs that will produce carry operations.
        
        Args:
            min_length: Minimum number of digits (default: 2)
            max_length: Maximum number of digits (default: 4)
            
        Returns:
            List of number pairs that produce carries
        """
        carry_cases = []
        
        # Single digit carries
        for i in range(5, 10):  # 5-9
            for j in range(5, 10):  # 5-9
                carry_cases.append((str(i), str(j)))
        
        # Multi-digit carries
        for _ in range(10):
            length = random.randint(min_length, max_length)
            
            # Generate numbers that will definitely carry
            num1_digits = []
            num2_digits = []
            
            for pos in range(length):
                # At least one position should carry
                if pos == 0 or random.choice([True, False]):
                    # This position will carry
                    d1 = random.randint(5, 9)
                    d2 = random.randint(5, 9)
                else:
                    # This position might not carry
                    d1 = random.randint(0, 9)
                    d2 = random.randint(0, 9)
                
                num1_digits.append(str(d1))
                num2_digits.append(str(d2))
            
            # Ensure no leading zeros
            if num1_digits[0] == '0':
                num1_digits[0] = str(random.randint(1, 9))
            if num2_digits[0] == '0':
                num2_digits[0] = str(random.randint(1, 9))
            
            carry_cases.append((''.join(num1_digits), ''.join(num2_digits)))
        
        return carry_cases


def quick_generate(min_length: int = 1, 
                  max_length: int = 5, 
                  seed: Optional[int] = None) -> Tuple[str, str]:
    """
    Quick function to generate a single random number pair.
    
    Args:
        min_length: Minimum number of digits (default: 1)
        max_length: Maximum number of digits (default: 5)
        seed: Optional seed for reproducible generation
        
    Returns:
        Tuple of two random numbers as strings
    """
    generator = RandomNumberGenerator(seed)
    return generator.generate_number_pair(min_length, max_length)


def generate_test_suite(count: int = 20,
                       include_edge_cases: bool = True,
                       include_carry_cases: bool = True,
                       min_length: int = 1,
                       max_length: int = 5,
                       seed: Optional[int] = None) -> List[Tuple[str, str]]:
    """
    Generate a comprehensive test suite of number pairs.
    
    Args:
        count: Number of random pairs to generate (default: 20)
        include_edge_cases: Whether to include edge cases (default: True)
        include_carry_cases: Whether to include carry cases (default: True)
        min_length: Minimum number of digits (default: 1)
        max_length: Maximum number of digits (default: 5)
        seed: Optional seed for reproducible generation
        
    Returns:
        List of number pairs for testing
    """
    generator = RandomNumberGenerator(seed)
    test_cases = []
    
    # Add edge cases
    if include_edge_cases:
        test_cases.extend(generator.generate_edge_cases())
    
    # Add carry cases
    if include_carry_cases:
        test_cases.extend(generator.generate_carry_cases(min_length, max_length))
    
    # Add random cases
    random_cases = generator.generate_multiple_pairs(count, min_length, max_length)
    test_cases.extend(random_cases)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_cases = []
    for case in test_cases:
        if case not in seen:
            seen.add(case)
            unique_cases.append(case)
    
    return unique_cases


if __name__ == "__main__":
    # Demo the random number generator
    print("=== Random Number Generator Demo ===\n")
    
    # Basic generation
    print("1. Basic random number generation:")
    generator = RandomNumberGenerator(seed=42)
    
    print("   Single numbers:")
    for i in range(5):
        num = generator.generate_single_number(min_length=2, max_length=4)
        print(f"     {num}")
    
    print("\n   Number pairs:")
    for i in range(5):
        pair = generator.generate_number_pair(min_length=2, max_length=4)
        print(f"     {pair[0]} + {pair[1]} = {int(pair[0]) + int(pair[1])}")
    
    # Edge cases
    print("\n2. Edge cases:")
    edge_cases = generator.generate_edge_cases()
    for i, (num1, num2) in enumerate(edge_cases[:5]):
        try:
            result = int(num1) + int(num2)
            print(f"     {num1} + {num2} = {result}")
        except ValueError:
            print(f"     {num1} + {num2} = [invalid]")
    
    # Carry cases
    print("\n3. Carry cases (first 5):")
    carry_cases = generator.generate_carry_cases()
    for i, (num1, num2) in enumerate(carry_cases[:5]):
        result = int(num1) + int(num2)
        print(f"     {num1} + {num2} = {result}")
    
    # Quick generation
    print("\n4. Quick generation:")
    for i in range(3):
        pair = quick_generate(min_length=3, max_length=6, seed=123)
        print(f"     {pair[0]} + {pair[1]} = {int(pair[0]) + int(pair[1])}")
    
    # Test suite
    print("\n5. Test suite sample:")
    test_suite = generate_test_suite(count=5, seed=456)
    print(f"   Generated {len(test_suite)} test cases")
    for i, (num1, num2) in enumerate(test_suite[:3]):
        result = int(num1) + int(num2)
        print(f"     Case {i+1}: {num1} + {num2} = {result}")
