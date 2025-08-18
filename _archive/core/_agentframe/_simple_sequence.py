"""
Abstract Sequence Configuration - Demonstrates the core logic pattern
"""

from typing import Dict, Any, Callable
import inspect

# Sequence class for executing registered steps
class Inference:
    def __init__(self, sequence_name: str):
        self.sequence_name = sequence_name
        self._sequences = self._discover_sequences()
        # Instance-specific step registry
        self._step_registry = {}
        self._initialize_steps()

    @classmethod
    def register_inference_sequence(cls, sequence_name: str):
        """Class method decorator to register a function as a sequence method of the Inference class"""
        def decorator(func: Callable) -> Callable:
            # Add the function as a method to the Inference class
            method_name = f"{sequence_name}"
            setattr(cls, method_name, func)
            return func
        return decorator

    def register_step(self, step_name: str, **metadata):
        """Instance method to register a step for this specific instance"""
        def decorator(func: Callable) -> Callable:
            self._step_registry[step_name] = {
                "function": func,
                "metadata": metadata
            }
            return func
        return decorator

    @property
    def steps(self):
        """Return steps for this specific instance"""
        # Use object.__getattribute__ to avoid triggering __getattr__
        return object.__getattribute__(self, '_step_registry')

    def _initialize_steps(self):
        """Initialize step and check functions from instance registry"""
        # Replace step functions
        for step_name, step_data in self._step_registry.items():
            # Remove 'step_' prefix if present for cleaner method names
            method_name = step_name.replace('step_', '') if step_name.startswith('step_') else step_name
            setattr(self, method_name, step_data["function"])
    
    def __getattr__(self, name):
        """Handle missing methods gracefully"""
        # Use object.__getattribute__ to avoid recursion
        step_registry = object.__getattribute__(self, '_step_registry')
        if name in step_registry:
            return step_registry[name]["function"]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def _discover_sequences(self) -> Dict[str, Callable]:
        """Discover sequence methods dynamically"""
        return {
            name: method for name, method in inspect.getmembers(self, inspect.ismethod)
            if name in [self.sequence_name]  # Only include the specific sequence method
        }

    def execute(self, input_data, sequence_method: str | None = None):
        """Execute the selected sequence method (default: the one matching sequence_name)"""
        method_name = sequence_method or self.sequence_name
        if method_name not in self._sequences:
            raise ValueError(f"Sequence '{method_name}' not found. Available: {list(self._sequences.keys())}")
        return self._sequences[method_name](input_data)


# Abstract usage pattern
if __name__ == "__main__":

    @Inference.register_inference_sequence("arithmetic_calculator")
    def arithmetic_calculator(self, input_data):
        """`(IWCC-((NFC-CLOC)-[(MVP-CP)-[(PA)]-(VCA-MA)]-RRC)-OWCC)`"""
        context = {"input": input_data, "sequence": "arithmetic_calculator"}
        results = {}
        
        # Step 1: Validate input
        validation_result = self.validate_input(context)
        results["validation"] = validation_result
        context["validation"] = validation_result
        
        # Step 2: Perform calculation
        calculation_result = self.perform_calculation(context)
        results["calculation"] = calculation_result
        context["calculation"] = calculation_result
        
        # Step 3: Format result
        format_result = self.format_result(context)
        results["formatted_result"] = format_result
        context["formatted_result"] = format_result
        
        return results

    # Create inference instance for arithmetic calculator
    arithmetic_calculator_instance = Inference(sequence_name="arithmetic_calculator")

    # Register steps for THIS SPECIFIC INSTANCE
    @arithmetic_calculator_instance.register_step("validate_input")
    def validate_input(context):
        """Validate that input contains two numbers"""
        input_data = context.get("input", {})
        a = input_data.get("a")
        b = input_data.get("b")
        if a is None or b is None:
            return {"valid": False, "error": "Missing operands a or b"}
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            return {"valid": False, "error": "Operands must be numbers"}
        return {"valid": True, "a": a, "b": b}

    @arithmetic_calculator_instance.register_step("perform_calculation")
    def perform_calculation(context):
        """Perform the arithmetic operation"""
        validation = context.get("validation", {})
        if not validation.get("valid"):
            return {"error": validation.get("error")}
        
        a = validation["a"]
        b = validation["b"]
        operation = context.get("input", {}).get("operation", "add")
        
        if operation == "add":
            result = a + b + 2
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                return {"error": "Division by zero"}
            result = a / b
        else:
            return {"error": f"Unknown operation: {operation}"}
        
        return {"result": result, "operation": operation, "a": a, "b": b}

    @arithmetic_calculator_instance.register_step("format_result")
    def format_result(context):
        """Format the calculation result"""
        calculation = context.get("calculation", {})
        if "error" in calculation:
            return {"formatted": f"Error: {calculation['error']}"}
        
        result = calculation["result"]
        operation = calculation["operation"]
        a = calculation["a"]
        b = calculation["b"]
        
        # Map operation names to symbols
        operation_symbols = {
            "add": "+",
            "subtract": "-", 
            "multiply": "×",
            "divide": "÷"
        }
        symbol = operation_symbols.get(operation, operation)
        
        return {"formatted": f"{a} {symbol} {b} = {result}"}

    # Execute the arithmetic calculator
    result1 = arithmetic_calculator_instance.execute({"a": 5, "b": 3, "operation": "add"})
    print("Addition result:", result1["formatted_result"]["formatted"])
    
    result2 = arithmetic_calculator_instance.execute({"a": 10, "b": 2, "operation": "multiply"})
    print("Multiplication result:", result2["formatted_result"]["formatted"])
    
    result3 = arithmetic_calculator_instance.execute({"a": 15, "b": 0, "operation": "divide"})
    print("Division result:", result3["formatted_result"]["formatted"])

    # Now you can create different instances with different step configurations
    scientific_calculator_instance = Inference(sequence_name="arithmetic_calculator")
    
    @scientific_calculator_instance.register_step("validate_input")
    def scientific_validate_input(context):
        """Scientific calculator validation - allows complex numbers"""
        # Different validation logic for scientific calculator
        return {"valid": True, "scientific": True}
    
    # This instance has different steps than the arithmetic_calculator_instance

