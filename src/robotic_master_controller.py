from typing import Dict, List, Any, Optional

# Import the newly created components
from .instruction_library import InstructionLibrary
from .experience_archive import ExperienceArchive
from .robotic_field_core import RoboticFieldCore

class RoboticMasterController:
    """
    Orchestrates the interactive learning process for the robot,
    integrating InstructionLibrary, ExperienceArchive, and RoboticFieldCore
    as described in master_apprentice_controller.md.
    """
    def __init__(self):
        self.library = InstructionLibrary()
        self.archive = ExperienceArchive()
        self.fieldcore = RoboticFieldCore()
        print("RoboticMasterController: Initialized.")
    
    def execute_command(self, natural_language_command: str, current_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executes a natural language command, learning interactively if needed.
        """
        if current_context is None:
            current_context = {}

        print(f"
RoboticMasterController: Received command '{natural_language_command}'")

        # Step 1: Consult library for candidate constraints
        candidate_constraints: List[str] = []
        semantic_actions = self.library.lookup_semantic_command(natural_language_command.lower())
        if semantic_actions:
            for action_name in semantic_actions:
                action_def = self.library.lookup_action(action_name)
                if action_def:
                    candidate_constraints.extend(action_def['constraints'])
        
        # Step 2: Check archive for similar past successes
        similar_experiences = self.archive.search_similar(natural_language_command, current_context)
        if similar_experiences:
            print(f"RoboticMasterController: Found {len(similar_experiences)} similar past experiences.")

        # Step 3: Attempt collapse with all available knowledge
        collapse_result = self.fieldcore.attempt_collapse(
            natural_language_command,
            candidate_constraints,
            current_context,
            similar_experiences
        )
        
        if collapse_result['success']:
            print("RoboticMasterController: Command collapsed successfully.")
            # Store the successful experience
            success_data = {
                "command": natural_language_command,
                "original_nl_command": natural_language_command, # For initial command
                "plan": collapse_result['plan'],
                "final_constraints": collapse_result['final_constraints'],
                "context": current_context
            }
            self.archive.store_success(success_data)
            return self._execute_plan(collapse_result['plan'])
        else:
            print(f"RoboticMasterController: Command collapse failed: {collapse_result['reason']}")
            return self._interactive_resolution(natural_language_command, collapse_result, current_context)

    def _execute_plan(self, plan: List[str]) -> Dict[str, Any]:
        """
        Simulates the execution of a robotic plan.
        """
        print(f"RoboticMasterController: Executing plan: {plan}")
        # In a real robot, this would involve sending commands to actuators.
        # For simulation, just print and return success.
        return {"status": "executed", "plan": plan}

    def _interactive_resolution(self, original_command: str, collapse_result: Dict[str, Any], current_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulates an interactive learning loop with a human to resolve ambiguities.
        """
        print(f"RoboticMasterController: Initiating interactive resolution.")
        
        question = collapse_result.get('question', 'I do not understand. Can you provide more information?')
        print(f"Robot asks: '{question}'")
        
        # Simulate human input - for a real system, this would come from a user interface
        if collapse_result.get('context_needed') == 'coffee_type':
            human_answer = "Espresso"
            new_constraint = "coffee_type=espresso"
        elif collapse_result.get('context_needed') == 'coffee_beans_location':
            human_answer = "In the pantry, top shelf"
            new_constraint = "location_coffee_beans=pantry_top_shelf"
        else:
            human_answer = "No more information"
            new_constraint = None

        print(f"Human answers: '{human_answer}'")

        if new_constraint:
            # Store the learning event
            self.archive.store_resolution_pattern(
                question=question,
                answer=human_answer,
                new_constraints=[new_constraint],
                command_context=original_command
            )
            # Add new constraint to context for retry
            updated_context = current_context.copy()
            if collapse_result.get('context_needed'):
                updated_context[collapse_result['context_needed']] = new_constraint.split('=')[1] # Add the value
            
            # Retry the command with the updated context and constraints
            print("RoboticMasterController: Retrying command with new information...")
            return self.execute_command(original_command, updated_context)
        else:
            return {"status": "failed_interactive_resolution", "message": "Human provided no useful new information."}

if __name__ == '__main__':
    print("--- Running RoboticMasterController simulation ---")
    
    controller = RoboticMasterController()

    # Scenario 1: Simple command, should execute directly
    print("
--- Scenario 1: Simple command 'grasp object' ---")
    result1 = controller.execute_command("grasp object", current_context={"object": "visible"})
    print(f"Final Result 1: {result1}")

    # Scenario 2: Command requiring clarification
    print("
--- Scenario 2: Command 'make coffee' requiring clarification ---")
    result2 = controller.execute_command("make coffee")
    print(f"Final Result 2: {result2}")

    # Scenario 3: Command with initial partial context, requiring location info
    print("
--- Scenario 3: Command 'get coffee beans' requiring location ---")
    result3 = controller.execute_command("get coffee beans", current_context={"robot_state": "ready"})
    print(f"Final Result 3: {result3}")

    print("
--- Archive contents after simulation ---")
    print(f"Successful experiences: {len(controller.archive.get_all_successes())}")
    print(f"Resolution patterns: {len(controller.archive.get_all_resolution_patterns())}")
