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
        concept_name="::(Read {1}?<$({digit pairs}*)%_> of {2}<$({both numbers})%_> in {3}<$({digit position}*)%_> from the right)",
        concept_id="read_function",
        reference_value="::(Read {1}?<$({digit pairs}*)%_> of {2}<$({both numbers})%_> in {3}<$({digit position}*)%_> from the right)",
        concept_type="::({})",
        reference_axes=["read_function"],
        reference_shape=(1,)
    )
    
    digit_quantification_concept = create_simple_concept(
        concept_name="*every({digit position})%:[{digit position}].[{digit pairs}?]",
        concept_id="quantified_digit_pairs",
        concept_type="*every",
    )
    
    # Create function concept for reading digit pairs
    read_function_concept, read_function_ref = create_concept_with_reference(
        concept_name="::(Read {1}?<$({digit pairs}*)%_> of {2}<$({two numbers})%_> in {3}<$({digit position}*)%_> from the right)",
        concept_id="read_function",
        reference_value="::(Read {1}?<$({digit pairs}*)%_> of {2}<$({two numbers})%_> in {3}<$({digit position}*)%_> from the right)",
        concept_type="::({})",
        reference_axes=["read_function"],
        reference_shape=(1,)
    )

    # Create concept for digit position
    digit_position_concept_in_loop = create_simple_concept(
        concept_name="{digit position}*",
        concept_id="digit_position_in_loop",
        concept_type="{}",
    )
    
    # Create concept for digit pairs
    digit_pairs_in_loop_types = (
        " the digits from two numbers that occupy the same specific position"
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
        "::(Read {1}?<$({digit pairs}*)%_> of {2}<$({two numbers})%_> in {3}<$({digit position}*)%_> from the right)": {
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
            logger.debug("Step 1: Input Working Configuration (IWC)")
            working_configuration = self.IWC(
                value_concepts=self.value_concepts,
                function_concept=self.function_concept,
                concept_to_infer=self.concept_to_infer,
                all_working_configuration=all_working_configuration
            )

            # 2. Formal Actuator Perception (FAP)
            logger.debug("Step 2: Formal Actuator Perception (FAP)")
            fap_result = self.FAP(
                function_concept=self.function_concept,
                value_concepts=self.value_concepts
            )
            formal_actuator_function, parsed_normcode_quantification = fap_result

            # 3. Group Perception (GP)
            logger.debug("Step 3: Group Perception (GP)")
            to_loop_elements = self.GP(
                formal_actuator_function=formal_actuator_function,
                value_concepts=self.value_concepts
            )

            # 4. Context Value Perception (CVP)
            logger.debug("Step 4: Context Value Perception (CVP)")
            current_loop_element, is_new, next_current_loop_base_element = self.CVP(
                context_concepts=self.context_concepts,
                parsed_normcode_quantification=parsed_normcode_quantification,
                workspace=workspace,
                to_loop_elements=to_loop_elements
            )

            # 5. Actuator Value Perception (AVP)
            logger.debug("Step 5: Actuator Value Perception (AVP)")
            current_concept_element = self.AVP(
                function_concept=self.function_concept
            )

            # 6. Perception Tool Actuation (PTA)
            logger.debug("Step 6: Perception Tool Actuation (PTA)")
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
                logger.debug("Step 7: Grouping Actuation (GA)")
                combined_reference = self.GA(
                    workspace=workspace,
                    to_loop_elements_reference=to_loop_elements,
                    parsed_normcode_quantification = parsed_normcode_quantification,
                    concept_to_infer=self.concept_to_infer
                )
            else:
                combined_reference = None

            # 8. Return Reference (RR)
            logger.debug("Step 8: Return Reference (RR)")
            concept_to_infer_with_reference = self.RR(
                concept_to_infer_reference=combined_reference,
                concept_to_infer=self.concept_to_infer,
            )

            # 9. Output Working Configuration (OWC)
            logger.debug("Step 9: Output Working Configuration (OWC)")
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





if __name__ == "__main__":

    inference_normcode = """{digit pairs}
    <= *every({digit position})%:[{digit position}].[{digit pairs}?]^({digit position}*)
        <= ::(Read {digit pairs}*? of {two numbers} in {digit position}* from the right)
        <- {two numbers}
        <- {digit pairs}*?
        <- {digit position}*
    <- {digit position}
"""
    (two_numbers_concept,
        digit_position_concept,
        digit_pairs_concept,
        digit_position_concept_in_loop,
        digit_pairs_concept_in_loop,
        read_function_concept,
        digit_quantification_concept,
    ) = init_concept_with_references(
        two_numbers_value="43, 34",
        digit_position_value=[1,2],
    )

    in_quantification_inference = Inference(
        sequence_name="imperative",
        concept_to_infer=digit_quantification_concept,
        value_concepts=[digit_position_concept_in_loop, two_numbers_concept, digit_pairs_concept_in_loop],
        function_concept=read_function_concept
    )

    quantification_inference = Inference(
        sequence_name="quantification",
        concept_to_infer=digit_pairs_concept,
        value_concepts=[digit_position_concept],
        function_concept=digit_quantification_concept,
        context_concepts=[digit_position_concept_in_loop, digit_pairs_concept_in_loop]
    )


        # Initialize agent
    llm = LanguageModel("qwen-turbo-latest")
    cal_agent = AgentFrame(
        "demo", 
        init_working_configuration(), 
        llm=llm,
    )

    # Initialize quantification agent
    workspace = {}
    quant_agent = QuantAgent(
        "demo", 
        init_working_configuration(), 
        llm=llm, 
        workspace=workspace
    )
    quant_agent.configure(
        inference_instance=quantification_inference, 
        inference_sequence="quantification",
    )


    logger.debug("=== BEFORE Execution ===")
    _log_concept_details(digit_position_concept_in_loop, digit_position_concept_in_loop.reference)
    _log_concept_details(digit_pairs_concept_in_loop, digit_pairs_concept_in_loop.reference)
    

    (concept_to_infer_with_reference, 
    updated_context_concepts, 
    working_configuration, 
    workspace) = quantification_inference.execute()

        # Log the concepts After execution
    logger.debug("=== After Quantification Execution 1 ===")
    _log_concept_details(digit_position_concept_in_loop, digit_position_concept_in_loop.reference)
    _log_concept_details(digit_pairs_concept_in_loop, digit_pairs_concept_in_loop.reference)
    for key, subworkspace in workspace.items(): #type: ignore
        log_subworkspace_tensors(subworkspace)

    in_quantification_inference.value_concepts = [digit_position_concept_in_loop, two_numbers_concept, digit_pairs_concept_in_loop]
    cal_agent.configure(
        inference_instance=in_quantification_inference, 
        inference_sequence="imperative",
    )
    digit_quantification_concept = in_quantification_inference.execute()

    logger.debug("=== After Imperative Execution ===")
    _log_concept_details(digit_quantification_concept, digit_quantification_concept.reference)

    quant_agent = QuantAgent(
        "demo", 
        working_configuration, 
        llm=llm, 
        workspace=workspace
    )

    quantification_inference.function_concept = digit_quantification_concept
    quant_agent.configure(
        inference_instance=quantification_inference, 
        inference_sequence="quantification",
    )
    (concept_to_infer_with_reference, 
    updated_context_concepts, 
    working_configuration, 
    workspace) = quantification_inference.execute()

    logger.debug("=== After Quantification Execution 2 ===")
    _log_concept_details(digit_position_concept_in_loop, digit_position_concept_in_loop.reference)
    _log_concept_details(digit_pairs_concept_in_loop, digit_pairs_concept_in_loop.reference)
    _log_concept_details(concept_to_infer_with_reference, concept_to_infer_with_reference.reference) # type: ignore
    


    # # Renew the original concepts using the new function
    # (a,
    #         b) = renew_concepts_from_context(
    #          updated_context_concepts,  # type: ignore
    #          digit_position_concept_in_loop, # type: ignore
    #          digit_pairs_concept_in_loop)
    
    # # Log the concepts after renewal
    # logger.debug("=== AFTER RENEWAL ===")
    # _log_concept_details(a, a.reference)
    # _log_concept_details(b, b.reference)

