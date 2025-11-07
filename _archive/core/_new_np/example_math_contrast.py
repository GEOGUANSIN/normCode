from typing import List, Tuple
from unicodedata import digit
from _concept import Concept
from _reference import Reference, cross_product, element_action
from _inference import Inference, register_inference_sequence, _log_inference_result
from _agentframe import AgentFrame, logger, _log_concept_details, _log_inference_result, create_concept_with_reference, create_simple_concept
from _language_models import LanguageModel
from _methods._quantification_demo import all_quantification_demo_methods
from _methods._grouping_demo import all_grouping_demo_methods
from _methods._workspace_demo import all_workspace_demo_methods
import random
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from tqdm import tqdm
import asyncio



OPERATOR_DESCRIPTION = """*every(_loopBaseConcept_)%:[_viewAxis_].[_conceptToInfer_?]@(_loopIndex_)^(_inLoopConcept_<*_carryoverCondition_>)"""

SEQUENCE_DESCRIPTION = """
**Variable Definitions:**
- `_loopBaseConcept_`: The main concept being iterated over (provides the list of elements to process)
- `_currentLoopBaseConcept_`: The current element in the loop, as a concept
- `_processedloopedElement_`: The collection of previously processed elements, stored in the workspace
- `_toLoopElement_`: The ordered list of elements to process, derived from `_loopBaseConcept_` via Group Perception (GP)
- `_currentConceptToInferElement_`: The current value for the concept being inferred in this loop iteration

**Quantification Sequence Steps:**

1. **Input Working Configuration (IWC):**
    - Initialize the working configuration for the inference process.

2. **Formal Actuator Perception (FAP):**
    - Parse the quantification normcode expression to extract loop base, view axis, and concept to infer.
    - Prepare a function for grouping/combining references according to the quantification pattern.

3. **Group Perception (GP):**
    - Use the FAP result to generate the ordered list of elements (`_toLoopElement_`) to loop over, based on the view axis.

4. **Context Value Perception (CVP):**
    - Determine the current element in the loop (`_currentLoopBaseConcept_`), check if it is new, and find the next element to process.

5. **Actuator Value Perception (AVP):**
    - Load the current value for the concept to infer (`_currentConceptToInferElement_`).

6. **Perception Tool Actuation (PTA):**
    - If the current element is new, update the workspace with the current loop base and concept to infer.
    - Update context concepts as needed for the next iteration.

7. **Grouping Actuation (GA):**
    - Combine all processed elements for the concept to infer into a single reference, using the workspace and the list of looped elements.

8. **Return Reference (RR):**
    - Set the reference for the concept to infer to the combined result from GA.

9. **Output Working Configuration (OWC):**
    - Check if all elements in `_toLoopElement_` have been processed and update the working configuration's completion status accordingly.

"""

READ_DIGIT_PAIRS = "::(Given {2}<$({both numbers})%_>, Find {1}?<$({digit pairs}*)%_> in {3}<$({digit position}*)%_> counting from the right to the left )"


def log_subworkspace_tensors(subworkspace):
    """
    Log the structure of a given subworkspace, showing for each loop index the concept names and the .tensor attribute of their Reference values.
    """
    msg = "[Subworkspace] current_subworkspace:"
    for loop_index, concept_dict in subworkspace.items():
        msg += f"\n  loop_index={loop_index}:"
        for concept_name, ref in concept_dict.items():
            tensor = getattr(ref, 'tensor', None)
            msg += f"  {concept_name}: tensor={tensor};"
    logger.debug(msg)

def init_concept_with_references(two_numbers_value="43, 34", digit_position_value=[1,2]):
    """
    Initialize concepts with references for the digit processing inference normcode.
    
    Returns:
        tuple: (value_concepts, function_concept, concept_to_infer)
    """
    two_numbers_concept, two_numbers_ref = create_concept_with_reference(
        concept_name="{two numbers}",
        concept_id="two_numbers",
        reference_value=two_numbers_value,
        concept_type="{}",
        reference_axes=["two_numbers"],
        reference_shape=(1,)
    )
    
    # Create concept for digit position
    digit_position_concept = create_simple_concept(
        concept_name="{digit position}",
        concept_id="digit_position",
        concept_type="{}",
    )

    digit_position_value = [f"%({i})" for i in digit_position_value]
    digit_position_concept.reference = Reference.from_data(digit_position_value, axis_names=["digit_position"])
    
    # Create concept for digit pairs
    digit_pairs_concept = create_simple_concept(
        concept_name="{digit pairs}",
        concept_id="digit_pairs",
        concept_type="{}",
    )

    read_function_concept, read_function_ref = create_concept_with_reference(
        concept_name=READ_DIGIT_PAIRS,
        concept_id="read_function",
        reference_value=READ_DIGIT_PAIRS,
        concept_type="::({})",
        reference_axes=["read_function"],
        reference_shape=(1,)
    )
    
    digit_quantification_concept = create_simple_concept(
        concept_name="*every({digit position})%:[{digit position}].[{digit pairs}?]",
        concept_id="corresponding_digit_pair",
        concept_type="*every",
    )

    # Create concept for digit position
    digit_position_concept_in_loop = create_simple_concept(
        concept_name="{digit position}*",
        concept_id="digit_position_in_loop",
        concept_type="{}",
    )
    
    # Create concept for digit pairs
    digit_pairs_in_loop_types = (
        "the two single digits occupying the same position"
    )
    digit_pairs_concept_in_loop, _ = create_concept_with_reference(
        concept_name="{digit pairs}*?",
        concept_id="digit_pairs_in_loop",
        reference_value=digit_pairs_in_loop_types,
        concept_type="{}",
        reference_axes=["digit_pairs_in_loop"],
        reference_shape=(1,)
    )
    
    return (
        two_numbers_concept,
        digit_position_concept,
        digit_pairs_concept,
        digit_position_concept_in_loop,
        digit_pairs_concept_in_loop,
        read_function_concept,
        digit_quantification_concept,
    )
 
def init_working_configuration():
    working_configuration = {
        "{two numbers}": {
            "perception": {
                "mvp": {
                    "mode": "formal"
                },
            },
            "actuation": {},
            "cognition": {}
        },
        "{digit position}": {
            "perception": {
                "mvp": {
                    "mode": "formal"
                },
            },
            "actuation": {},
            "cognition": {}
        },
        "{digit pairs}": {
        "perception": {
            "mvp": {
                "mode": "formal"
            },
        },
        "actuation": {
        },
        "cognition": {
        }
        },
        "{digit position}*": {
        "perception": {
            "mvp": {
                "mode": "formal"
            },
        },
        "actuation": {
        },
        "cognition": {
        }
        },
        "{digit pairs}*?": {
        "perception": {
            "mvp": {
                "mode": "formal"
            },
        },
        "actuation": {
        },
        "cognition": {
        }
        },
        "*every({digit position})%:[{digit position}].[{digit pairs}?]": {
            "perception": {
                "asp": {
                    "mode": "in-cognition"
                }
            },
            "actuation": {
                "pta": {
                    "mode": "in-cognition",
                    "value_order": {
                        "{digit position}": 0
                    }
                }
            },
            "cognition": {
                "rr": {
                    "mode": "identity"
                },
                "": {
                    "mode": "in-cognition"
                }
            }
        },
        READ_DIGIT_PAIRS: {
            "perception": {
                "asp": {
                    "mode": "in-cognition"
                },
                "ap": {
                    "mode": "llm_formal",
                    "product": "translated_templated_function",
                    "value_order": {
                        "{digit pairs}*?": 0,
                        "{two numbers}": 1,
                        "{digit position}*": 2
                    }
                }
            },
            "actuation": {
                "pta": {
                    "mode": "in-cognition",
                    "value_order": {
                        "{digit pairs}*?": 0,
                        "{two numbers}": 1,
                        "{digit position}*": 2
                    }
                },
                "ma": {
                    "mode": "formal",
                },
            },
            "cognition": {
                "rr": {
                    "mode": "identity"
                },
            }
        }
    }
    return working_configuration



class QuantAgent(AgentFrame):
    def __init__(self, name, working_configuration, **body):
        super().__init__(name, working_configuration=working_configuration, **body)
        self.body = body
        self._norm_code_setup()

    def _norm_code_setup(self):
        logger.debug(f"Setting up norm code for model: {self.AgentFrameModel}")
        if self.AgentFrameModel == "demo":
            logger.info("Setting up demo configuration")
            # Quantification
            self._set_up_quantification_demo()
        else:
            logger.warning(f"Unknown AgentFrameModel: {self.AgentFrameModel}")

    def configure(self, inference_instance: Inference, inference_sequence: str, **kwargs):
        logger.info(f"Configuring inference instance with sequence: {inference_sequence}")
        if self.AgentFrameModel == "demo":
            if inference_sequence == "quantification":
                logger.debug("Configuring quantification demo")
                methods = all_quantification_demo_methods("quantification")
                self._configure_quantification_demo(inference_instance, **methods)
            else:
                logger.warning(f"Unknown inference sequence: {inference_sequence}")
        else:
            logger.warning(f"Configuration not supported for model: {self.AgentFrameModel}")

    def _set_up_quantification_demo(self):
        logger.debug("Setting up quantification demo sequence")
        all_working_configuration = self.working_configuration
        workspace = self.body["workspace"]
        @register_inference_sequence("quantification")
        def quantification(self: Inference, input_data: dict) -> Tuple[Concept, List[Concept], dict, dict]:
            logger.info("Executing quantification sequence")

            # 1. Input Working Configuration (IWC)
            logger.debug("***STEP 1: Input Working Configuration (IWC)***")
            working_configuration = self.IWC(
                value_concepts=self.value_concepts,
                function_concept=self.function_concept,
                concept_to_infer=self.concept_to_infer,
                all_working_configuration=all_working_configuration
            )

            # 2. Formal Actuator Perception (FAP)
            logger.debug("***STEP 2: Formal Actuator Perception (FAP)***")
            fap_result = self.FAP(
                function_concept=self.function_concept,
                value_concepts=self.value_concepts
            )
            formal_actuator_function, parsed_normcode_quantification = fap_result

            # 3. Group Perception (GP)
            logger.debug("***STEP 3: Group Perception (GP)***")
            to_loop_elements = self.GP(
                formal_actuator_function=formal_actuator_function,
                value_concepts=self.value_concepts,
                parsed_normcode_quantification=parsed_normcode_quantification,
                context_concepts=self.context_concepts
            )

            # 4. Context Value Perception (CVP)
            logger.debug("***STEP 4: Context Value Perception (CVP)***")
            current_loop_element, is_new, next_current_loop_base_element = self.CVP(
                context_concepts=self.context_concepts,
                parsed_normcode_quantification=parsed_normcode_quantification,
                workspace=workspace,
                to_loop_elements=to_loop_elements
            )

            # 5. Actuator Value Perception (AVP)
            logger.debug("***STEP 5: Actuator Value Perception (AVP)***")
            current_concept_element = self.AVP(
                function_concept=self.function_concept
            )

            # 6. Perception Tool Actuation (PTA)
            logger.debug("***STEP 6: Perception Tool Actuation (PTA)***")
            updated_context_concepts: List[Concept] = self.PTA(
                parsed_normcode_quantification=parsed_normcode_quantification,
                workspace=workspace,
                next_current_loop_base_element=next_current_loop_base_element,
                current_loop_base_element=current_loop_element,
                concept_to_infer_name=self.concept_to_infer.name,
                current_loop_element=current_concept_element,
                context_concepts=self.context_concepts,
                is_new=is_new
            )

            # 7. Grouping Actuation (GA)
            if is_new:
                logger.debug("***STEP 7: Grouping Actuation (GA)***")
                combined_reference = self.GA(
                    workspace=workspace,
                    to_loop_elements_reference=to_loop_elements,
                    parsed_normcode_quantification = parsed_normcode_quantification,
                    concept_to_infer=self.concept_to_infer,
                    context_concepts=self.context_concepts,
                    value_concepts=self.value_concepts
                )
            else:
                combined_reference = None

            # 8. Return Reference (RR)
            logger.debug("***STEP 8: Return Reference (RR)***")
            concept_to_infer_with_reference = self.RR(
                concept_to_infer_reference=combined_reference,
                concept_to_infer=self.concept_to_infer,
            )

            # 9. Output Working Configuration (OWC)
            logger.debug("***STEP 9: Output Working Configuration (OWC)***")
            working_configuration = self.OWC(
                working_configuration=working_configuration,
                function_concept=self.function_concept,
                workspace=workspace,
                loop_base_concept_name=parsed_normcode_quantification['LoopBaseConcept'],
                to_loop_elements=to_loop_elements,
                concept_to_infer=self.concept_to_infer,
            )

            logger.info("Quantification sequence completed")
            logger.debug(f"Updated context concepts: {[c.name for c in updated_context_concepts]}")
            for context_concept in updated_context_concepts:
                if context_concept.reference is not None:   
                    logger.debug(f"Context concept: {context_concept.name}, reference: {context_concept.reference.tensor}, axes: {context_concept.reference.axes}, shape: {context_concept.reference.shape}")
                else:
                    logger.debug(f"Context concept: {context_concept.name}, reference: None")
            logger.debug(f"Working configuration: {working_configuration}")

            logger.debug(f"Workspace: {workspace}")

            return concept_to_infer_with_reference, updated_context_concepts, working_configuration, workspace

            
    def _configure_quantification_demo(self, inference_instance: Inference, **methods):
        logger.debug("Configuring quantification demo steps")
        @inference_instance.register_step("IWC")
        def input_working_configurations(**fkwargs):
            logger.debug("Executing IWC step")
            function = methods.get("input_working_configurations", self._input_working_configurations)
            return function(**fkwargs)

        @inference_instance.register_step("FAP")
        def formal_actuator_perception(**fkwargs):
            logger.debug("Executing FAP step")
            function = methods.get("formal_actuator_perception", self._formal_actuator_perception)
            return function(**fkwargs)

        @inference_instance.register_step("GP")
        def group_perception(**fkwargs):
            logger.debug("Executing GP step")
            function = methods.get("group_perception", self._group_perception)
            return function(**fkwargs)

        @inference_instance.register_step("CVP")
        def context_value_perception(**fkwargs):
            logger.debug("Executing CVP step")
            function = methods.get("context_value_perception", self._context_value_perception)
            return function(**fkwargs)

        @inference_instance.register_step("AVP")
        def actuator_value_perception(**fkwargs):
            logger.debug("Executing AVP step")
            function = methods.get("actuator_value_perception", self._actuator_value_perception)
            return function(**fkwargs)

        @inference_instance.register_step("PTA")
        def perception_tool_actuation(**fkwargs):
            logger.debug("Executing PTA step")
            function = methods.get("perception_tool_actuation", self._perception_tool_actuation)
            return function(**fkwargs)

        @inference_instance.register_step("GA")
        def grouping_actuation(**fkwargs):
            logger.debug("Executing GA step")
            function = methods.get("grouping_actuation", self._grouping_actuation)
            return function(**fkwargs)

        @inference_instance.register_step("RR")
        def return_reference(**fkwargs):
            logger.debug("Executing RR step")
            function = methods.get("return_reference", self._return_reference)
            return function(**fkwargs)

        @inference_instance.register_step("OWC")
        def output_working_configurations(**fkwargs):
            logger.debug("Executing OWC step")
            function = methods.get("output_working_configurations", self._output_working_configurations)
            return function(**fkwargs)

    def _is_new_element(self, current_element, processed_elements):
        """Helper method to check if current element is new"""
        return current_element not in processed_elements

    # Placeholder methods for quantification steps
    def _input_working_configurations(self, *args, **kwargs):
        """Perform the input working configurations"""
        logger.warning("Executing IWC step: This will do nothing.")
        pass

    def _output_working_configurations(self, *args, **kwargs):
        """Perform the output working configurations"""
        logger.warning("Executing OWC step: This will do nothing.")
        pass

    def _return_reference(self, *args, **kwargs):
        """Perform the return reference"""
        logger.warning("Executing RR step: This will do nothing.")
        pass

    def _formal_actuator_perception(self, *args, **kwargs):
        """Perform the formal actuator perception"""
        logger.warning("Executing FAP step: This will do nothing.")
        pass

    def _group_perception(self, *args, **kwargs):
        """Perform the group perception"""
        logger.warning("Executing GP step: This will do nothing.")
        pass

    def _context_value_perception(self, *args, **kwargs):
        """Perform the context value perception"""
        logger.warning("Executing CVP step: This will do nothing.")
        pass

    def _actuator_value_perception(self, *args, **kwargs):
        """Perform the actuator value perception"""
        logger.warning("Executing AVP step: This will do nothing.")
        pass

    def _perception_tool_actuation(self, *args, **kwargs):
        """Perform the perception tool actuation"""
        logger.warning("Executing PTA step: This will do nothing.")
        pass

    def _grouping_actuation(self, *args, **kwargs):
        """Perform the grouping actuation"""
        logger.warning("Executing GA step: This will do nothing.")
        pass



def renew_concepts_from_context(updated_context_concepts: List[Concept], *concepts_to_renew: Concept) -> List[Concept]:
    """
    Renew the references of input concepts based on updated context concepts.
    
    Args:
        updated_context_concepts (List[Concept]): List of context concepts with updated references
        *concepts_to_renew (Concept): Variable number of concepts to renew
        
    Returns:
        List[Concept]: List of renewed concepts in the same order as input
    """
    renewed_concepts = []
    
    for concept_to_renew in concepts_to_renew:
        if not isinstance(concept_to_renew, Concept):
            logger.warning(f"Expected Concept object, got {type(concept_to_renew)}: {concept_to_renew}")
            renewed_concepts.append(concept_to_renew)
            continue
            
        # Find matching context concept
        matching_context_concept = None
        for context_concept in updated_context_concepts:
            if isinstance(context_concept, Concept) and context_concept.name == concept_to_renew.name:
                matching_context_concept = context_concept
                break
        
        if matching_context_concept is not None and matching_context_concept.reference is not None:
            new_reference = matching_context_concept.reference.copy()
            if isinstance(new_reference, Reference):
                concept_to_renew.reference = new_reference
                logger.debug(f"Renewed concept: {concept_to_renew.name}, reference: {concept_to_renew.reference.tensor}, axes: {concept_to_renew.reference.axes}, shape: {concept_to_renew.reference.shape}")
            else:
                logger.warning(f"Expected Reference object, got {type(new_reference)}: {new_reference}")
        else:
            logger.debug(f"No matching context concept found for: {concept_to_renew.name}")
        
        renewed_concepts.append(concept_to_renew)
    
    return renewed_concepts


def generate_number_string(length: int) -> str:
    """
    Generate a random number string of the specified length, allowing leading zeros.
    
    Args:
        length: Length of the number string to generate
        
    Returns:
        str: Random number string of the specified length
    """
    import random
    # Generate each digit randomly (0-9) and join into a string
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


def generate_number_strings(length: int) -> str:
    """
    Generate two random numbers as strings of the specified length, separated by " and "
    Each number will have leading zeros to ensure consistent length
    """
    import random
    num1 = ''.join(str(random.randint(0, 9)) for _ in range(length))
    num2 = ''.join(str(random.randint(0, 9)) for _ in range(length))
    return f"{num1} and {num2}"


def get_digit_pair_at_position(two_numbers: str, position: int) -> list[int]:
    """
    Get the digit pair at a specific position in two numbers
    
    Args:
        two_numbers: String in the format "num1 and num2"
        position: Position to retrieve (1-indexed from right to left)
        
    Returns:
        List of two integers representing the digits at the specified position
    """
    # Split the two numbers
    num1, num2 = two_numbers.split(" and ")
    
    # Reverse both numbers to make indexing from right easier
    num1_rev = num1[::-1]
    num2_rev = num2[::-1]
    
    # Get digits at position (0-indexed from right)
    # Use '0' if position is beyond the number length
    digit1 = num1_rev[position-1] if position <= len(num1_rev) else '0'
    digit2 = num2_rev[position-1] if position <= len(num2_rev) else '0'
    
    return [int(digit1), int(digit2)]


async def run_trial(length, position, semaphore, llm):
    """
    Run a single trial for digit extraction accuracy testing.
    """
    async with semaphore:
        two_numbers = generate_number_strings(length)
        correct_answer = get_digit_pair_at_position(two_numbers, position)
        
        try:
            # Ask LLM for the digit at position
            response = await asyncio.to_thread(
                llm.generate,
                f"Output in JSON format with keys 'analysis' and 'final_answer': "
                f"what is the {position}th digit of {two_numbers} from right to left? "
                f"The 'final_answer' should be a Python list of two integers representing the digits at that position.",
                response_format={"type": "json_object"},
            )
            
            # Parse and validate response
            try:
                response_json = json.loads(response)
                llm_answer = response_json.get('final_answer', [])
                
                if isinstance(llm_answer, list) and len(llm_answer) == 2:
                    return 1 if llm_answer == correct_answer else 0
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON response: {response}")
        except Exception as e:
            logger.error(f"Error during LLM call: {e}")
        return 0


async def run_experiment():
    """
    Run an experiment to test LLM accuracy on digit extraction at different positions
    across various string lengths. Generates a heatmap visualization of accuracy rates.
    Uses asynchronous processing with concurrency limit.
    """
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    from tqdm.asyncio import tqdm_asyncio

    # Experiment parameters
    min_length = 1
    max_length = 100
    num_trials = 5
    concurrency_limit = 12  # Maximum concurrent requests
    llm = LanguageModel("qwen-turbo-latest")

    # Create logarithmic length sequence (more samples at lower lengths)
    log_min = np.log(min_length)
    log_max = np.log(max_length)
    log_lengths = np.exp(np.linspace(log_min, log_max, 15))  # 15 points on log scale
    lengths = np.unique(np.round(log_lengths).astype(int))   # Convert to unique integers
    logger.info(f"Testing lengths: {lengths}")

    # Initialize results matrix (lengths x positions)
    results = np.full((max_length, max_length), np.nan)  # Use NaN for untested positions

    # Create a semaphore to limit concurrency
    semaphore = asyncio.Semaphore(concurrency_limit)

    # Progress bar for lengths
    for length in tqdm(lengths, desc="Testing lengths"):
        # Create position sequence: first, last, and up to 4 uniformly distributed positions
        if length <= 2:
            positions = [1, length] if length > 1 else [1]
        else:
            # Always include first and last positions
            positions = [1, length]
            # Add up to 4 more positions in between
            num_mid_points = min(4, length - 2)
            if num_mid_points > 0:
                mid_positions = np.linspace(2, length-1, num_mid_points + 2)[1:-1]
                positions.extend(np.round(mid_positions).astype(int))
            positions = sorted(set(positions))  # Remove duplicates and sort
        
        logger.debug(f"Testing length {length} at positions: {positions}")
        
        for position in tqdm(positions, desc=f"Positions for length {length}", leave=False):
            # Create all trial tasks for this (length, position)
            tasks = [run_trial(length, position, semaphore, llm) for _ in range(num_trials)]
            
            # Run trials concurrently with progress bar
            trial_results = await tqdm_asyncio.gather(*tasks, desc="Trials")
            
            # Calculate accuracy for this position
            accuracy = sum(trial_results) / num_trials # type: ignore
            results[length - 1][position - 1] = accuracy
    
    # Create visualization
    plt.figure(figsize=(12, 8))
    cmap = LinearSegmentedColormap.from_list('accuracy', ['#ff4d4d', '#4dff4d'])
    
    # Create mask for untested positions
    mask = np.isnan(results)
    
    # Plot heatmap
    plt.imshow(results, cmap=cmap, vmin=0, vmax=1, aspect='auto')
    plt.colorbar(label='Accuracy Rate')
    
    # Set labels and title
    plt.title('LLM Digit Extraction Accuracy by Position and String Length')
    plt.xlabel('Position (from right)')
    plt.ylabel('String Length')
    
    # Set ticks
    plt.xticks(np.arange(0, max_length), np.arange(1, max_length + 1).astype(str).tolist())
    plt.yticks(np.arange(0, max_length), np.arange(1, max_length + 1).astype(str).tolist())
    
    # Add accuracy values to cells
    for i in range(max_length):
        for j in range(max_length):
            if not np.isnan(results[i, j]):
                plt.text(j, i, f"{results[i, j]:.2f}", 
                         ha="center", va="center", 
                         color="black" if results[i, j] > 0.5 else "white")
    
    # Add grid for tested positions
    plt.grid(True, color='gray', linestyle='-', linewidth=0.5, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('digit_extraction_accuracy.png')
    plt.show()
    logger.info("Experiment complete. Visualization saved as 'digit_extraction_accuracy.png'")


def validate_digit_position_response(response_json: dict, number: str) -> dict:
    """
    Validate the JSON response for digit position annotation.
    
    Args:
        response_json: Parsed JSON response from LLM
        number: Original number string to validate against
        
    Returns:
        dict: Validation results with keys:
            - 'success': bool indicating overall success
            - 'correct_count': number of correct digit-position pairs
            - 'total_digits': total number of digits
            - 'accuracy': percentage of correct pairs
            - 'errors': list of error details
    """
    # Extract digits from response
    response_digits = response_json.get('digits', [])
    total_digits = len(number)
    correct_count = 0
    errors = []
    
    # Validate each digit-position pair
    for i, digit_info in enumerate(response_digits):
        expected_digit = number[i]
        expected_position = total_digits - i  # 1-indexed from right
        
        # Check if response has required keys
        if 'digit' not in digit_info or 'position' not in digit_info:
            errors.append({
                'index': i,
                'error': 'Missing keys in response',
                'expected': {'digit': expected_digit, 'position': expected_position},
                'actual': digit_info
            })
            continue
        
        actual_digit = str(digit_info['digit'])
        actual_position = digit_info['position']
        
        # Validate digit and position
        if actual_digit != expected_digit:
            errors.append({
                'index': i,
                'error': 'Digit mismatch',
                'expected': expected_digit,
                'actual': actual_digit
            })
        elif actual_position != expected_position:
            errors.append({
                'index': i,
                'error': 'Position mismatch',
                'expected': expected_position,
                'actual': actual_position
            })
        else:
            correct_count += 1
    
    # Calculate accuracy
    accuracy = (correct_count / total_digits) * 100 if total_digits > 0 else 0
    
    return {
        'success': correct_count == total_digits,
        'correct_count': correct_count,
        'total_digits': total_digits,
        'accuracy': accuracy,
        'errors': errors
    }


def inquire_digit_position_by_number(number: str, position: int, length: int) -> str:
    """
    Generate an LLM inquiry to find the digit at a specific position in a number.
    
    Args:
        number: The original number string
        position: The position to find (1-indexed from right to left)
        length: The length of the number
    Returns:
        str: Formatted inquiry string
    """
    return (
        f"Given the number {number}, what is the digit at position {position} when counting from right to left? "
        f"(Position 1 is the rightmost digit and position {length} is the leftmost digit). Output your answer in JSON format with the following keys: "
        f"'analysis' (a string explaining your reasoning) and 'digit' (the digit at the specified position as a string)."
    )

def inquire_digit_position_by_record(record: list[dict], position: int) -> str:
    """
    Generate an LLM inquiry to find the digit at a specific position in a number.
    
    Args:
        record: The record of number's digit in each position
        position: The position to find (1-indexed from right to left)
        
    Returns:
        str: Formatted inquiry string
    """
    return (
        f"Given the record of number's digit in each position, what is the digit at position {position} when counting from right to left? "
        f"The record is: {record}"
        f"Output your answer in JSON format with the following keys: "
        f"'analysis' (a string explaining your reasoning) and 'digit' (the digit at the specified position as a string)."
    )

def validate_number_differences(a: int | str, b: int | str) -> dict:
    s1 = str(a)
    s2 = str(b)
    max_len = max(len(s1), len(s2))
    s1 = s1.zfill(max_len)
    s2 = s2.zfill(max_len)

    diffs = []
    for i in range(max_len):
        # position_from_right: 1 is rightmost, increasing leftward
        pos_from_right = i + 1
        d1 = s1[-pos_from_right]
        d2 = s2[-pos_from_right]
        if d1 != d2:
            diffs.append({
                "position_from_right": pos_from_right,
                "a_digit": d1,
                "b_digit": d2
            })

    return {
        "equal": len(diffs) == 0,
        "count": len(diffs),
        "numeric_delta": int(b) - int(a),
        "differences": diffs  # ordered from right to left
    }

    # Example usage with the two sums in this file:
    # result = validate_number_differences(sum1, sum2)
    # print(result["equal"], result["count"])
    # print(result["differences"][:10])  # first 10 mismatches from the right




if __name__ == "__main__":
    # Test the helper function
    number_length = 50
    position = 48
    test_number = generate_number_string(number_length)
    test_number2 = generate_number_string(number_length)

    # sum = int(test_number) + int(test_number2)
    # logger.info(f"Test number 1: {test_number}, Test number 2: {test_number2}, Sum: {sum}")


    # sum1 = 119731344401632240203004242988513205799260297559136853690716627173070069616012694073296324139635376715550615452916357090704697778723284727894521889361013879861037360692641739619298675296677922239500902427195211270661143256260396587
    # logger.info(f"Sum1: {sum1}")

    # sum2 = 119731344401632240203004242988313205799260297559136853250716627173124069616012694073296324139635436315850615452916357090704697778723284828894521889328526079860037360692641748619298675296678922239500902427195222270661167157260396587
    # logger.info(f"Sum2: {sum2}")

    # result = validate_number_differences(sum1, sum2)
    # logger.info(f"Result: {result}")
    # logger.info(f"Equal: {result['equal']}, Count: {result['count']}")
    # logger.info(f"Result: {result['differences']}")


    # logger.info(f'two sums the same? {sum1 == sum2}')
    # logger.info(f"Generated test number: {test_number}")
    
    llm = LanguageModel("qwen-turbo-latest")
    extra_info = "(counting from right to left with position starting at 1)"
    # extra_info = "(counting from right to left, starting at position 1 for the rightmost digit and ending at position {number_length} for the leftmost digit)"
    answer = llm.generate(
        f"For the number {test_number}, annotate the position number {extra_info} for each digit. "
        "Output your final answer in JSON format with the following keys: "
        "'analysis' (a string explaining your reasoning) and "
        "'digits' (a list of dictionaries, each with keys 'digit' (string) and 'position' (integer), in the same order as the digits in the number from left to right).",
        response_format={"type": "json_object"}
    )
    logger.debug(answer)
    
    # Validate the response
    try:
        response_json = json.loads(answer)
        validation = validate_digit_position_response(response_json, test_number)
        logger.info(f"Validation results for {test_number}: {validation}")
    except json.JSONDecodeError:
        logger.error("Invalid JSON response from LLM")

    # if response_json:
    #     # Use the original number for the inquiry
    #     digit_answer = llm.generate(
    #         inquire_digit_position_by_number(test_number, position, number_length),
    #         response_format={"type": "json_object"}
    #     )
    #     logger.debug(digit_answer)
        
    #     try:
    #         digit_response = json.loads(digit_answer)
    #         llm_digit = digit_response.get('digit', '')
    #         correct_digit = test_number[-position]  # Position from right
    #         is_correct = llm_digit == correct_digit
            
    #         logger.info(f"Correct digit at position {position}: {correct_digit}")
    #         logger.info(f"LLM response digit: {llm_digit}")
    #         logger.info(f"LLM digit is correct: {is_correct}")
    #     except json.JSONDecodeError:
    #         logger.error("Invalid JSON response for digit inquiry")

    #     digit_answer_by_record = llm.generate(
    #         inquire_digit_position_by_record(response_json['digits'], position),
    #         response_format={"type": "json_object"}
    #     )
    #     logger.debug(digit_answer_by_record)

    #     try:
    #         digit_response_by_record = json.loads(digit_answer_by_record)
    #         llm_digit_by_record = digit_response_by_record.get('digit', '')
    #         correct_digit_by_record = test_number[-position]  # Position from right
    #         is_correct_by_record = llm_digit_by_record == correct_digit_by_record
            
    #         logger.info(f"Correct digit at position {position}: {correct_digit_by_record}")
    #         logger.info(f"LLM response digit: {llm_digit_by_record}")
    #         logger.info(f"LLM digit is correct: {is_correct_by_record}")
    #     except json.JSONDecodeError:
    #         logger.error("Invalid JSON response for digit inquiry by record")



    