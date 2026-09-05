part 3

"""
FieldCore Unified - Part 3: System & Integration
Consolidates: Sacred Library, MVCC, Boot Sequence, Main Loop
Brings together Parts 1 & 2 into complete system
"""

import json
import time
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from Parts 1 & 2
try:
    from fieldcore_unified_core import (
        IntentStalk, CoreRegistry, SimSelf, M0Governor, M1Controller, MTECompiler
    )
    from fieldcore_unified_operators import (
        create_operators, InfoPacket, Field
    )
except ImportError:
    print("Warning: Parts 1 or 2 not found. Ensure all parts are in same directory")
    IntentStalk = None
    CoreRegistry = None
    SimSelf = None
    M0Governor = None
    M1Controller = None
    MTECompiler = None
    create_operators = None
    InfoPacket = None
    Field = None


# ============================================================================
# SACRED LIBRARY (Persistent Skill Storage)
# ============================================================================

class SacredLibraryManager:
    """
    Non-volatile semantic memory (NVSM).
    Manages growth, versioning, and certification of skills.
    Implements MVCC-style version control.
    """
    
    def __init__(self, storage_path: str = "./sacred_library"):
        self.storage_path = Path(storage_path)
        self.registry_index = {}
        self.certification_levels = ["q0", "q1", "q2", "q3", "q4"]
        
        # MVCC: Version tracking
        self.versions = {}  # skill_name -> [version_list]
        self.current_version = {}  # skill_name -> current_version_number
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._load_index()
    
    def archive_skill(self, skill_name: str, code: str, cert_level: str) -> str:
        """
        Archive skill with versioning.
        Returns: archive status message
        """
        if cert_level not in self.certification_levels:
            return "archive_error: invalid_certification"
        
        # Generate hash for content-addressable storage
        file_hash = hashlib.sha256(code.encode()).hexdigest()[:12]
        filename = f"{skill_name}_{file_hash}.py"
        full_path = self.storage_path / filename
        
        # Write file
        with open(full_path, "w") as f:
            f.write(code)
        
        # Update registry
        self.registry_index[skill_name] = {
            "hash": file_hash,
            "q_level": cert_level,
            "timestamp": time.time(),
            "path": str(full_path)
        }
        
        # MVCC: Track version
        if skill_name not in self.versions:
            self.versions[skill_name] = []
            self.current_version[skill_name] = 0
        
        version_num = len(self.versions[skill_name])
        self.versions[skill_name].append({
            "version": version_num,
            "hash": file_hash,
            "timestamp": time.time(),
            "cert_level": cert_level
        })
        self.current_version[skill_name] = version_num
        
        # Save index
        self._save_index()
        
        print(f"library: skill '{skill_name}' archived at level {cert_level} (v{version_num})")
        return "archive_success"
    
    def retrieve_skill(self, skill_name: str, version: Optional[int] = None) -> Optional[str]:
        """
        Retrieve skill code.
        If version specified, retrieves that version.
        Otherwise retrieves current version.
        """
        if skill_name not in self.registry_index:
            return None
        
        # Get appropriate version
        if version is not None and skill_name in self.versions:
            if version < len(self.versions[skill_name]):
                version_info = self.versions[skill_name][version]
                # Reconstruct filename from hash
                filename = f"{skill_name}_{version_info['hash']}.py"
                path = self.storage_path / filename
            else:
                return None
        else:
            path = Path(self.registry_index[skill_name]["path"])
        
        if path.exists():
            with open(path, "r") as f:
                return f.read()
        return None
    
    def rollback(self, skill_name: str, version: int) -> str:
        """Rollback skill to previous version"""
        if skill_name in self.versions:
            if version < len(self.versions[skill_name]):
                self.current_version[skill_name] = version
                self._save_index()
                return f"rollback_success: {skill_name} now at v{version}"
        return "rollback_failed: version not found"
    
    def list_skills(self) -> Dict:
        """List all skills with their versions"""
        return {
            name: {
                'current_version': self.current_version.get(name, 0),
                'total_versions': len(self.versions.get(name, [])),
                'cert_level': info['q_level'],
                'timestamp': info['timestamp']
            }
            for name, info in self.registry_index.items()
        }
    
    def _save_index(self):
        """Save registry index to disk"""
        index_path = self.storage_path / "registry_index.json"
        with open(index_path, "w") as f:
            json.dump({
                'registry': self.registry_index,
                'versions': self.versions,
                'current_version': self.current_version
            }, f, indent=2)
    
    def _load_index(self):
        """Load registry index from disk"""
        index_path = self.storage_path / "registry_index.json"
        if index_path.exists():
            try:
                with open(index_path, "r") as f:
                    data = json.load(f)
                    self.registry_index = data.get('registry', {})
                    self.versions = data.get('versions', {})
                    self.current_version = data.get('current_version', {})
            except Exception as e:
                print(f"warning: failed to load library index: {e}")


# ============================================================================
# LLM DECIPHER ENGINE (External Reasoning)
# ============================================================================

class LLMDecipherEngine:
    """
    High-latency reasoning engine.
    Simulates external LLM for code demodulation and refactoring.
    """
    
    def __init__(self):
        self.api_latency = 0.5  # Simulated latency
    
    def decipher_snippet(self, raw_snippet: str, target_sheaf: str) -> str:
        """
        Decipher and refactor code snippet.
        In production, this would call actual LLM API.
        """
        print(f"llm_decipher: demodulating signal for {target_sheaf}...")
        time.sleep(self.api_latency)
        
        # Clean prohibited terms
        refactored = raw_snippet.replace("kill", "halt").replace("execute", "run")
        refactored = refactored.lower()
        
        return f"# refactored fieldcore sheaf\n# target: {target_sheaf}\n{refactored}"


# ============================================================================
# COLD BOOT SEQUENCE (System Initialization)
# ============================================================================

def cold_boot_sequence() -> CoreRegistry:
    """
    Initialize full FieldCore system.
    Returns initialized hub/registry.
    """
    print("=" * 70)
    print("FieldCore Cold Boot Initialized")
    print("=" * 70)
    
    # 1. Create global hub
    global hub
    from fieldcore_unified_core import hub as core_hub
    hub = CoreRegistry()
    
    # 2. Create sacred library and LLM decipher
    hub.library = SacredLibraryManager()
    hub.llm = LLMDecipherEngine()
    
    # 3. Create operators
    operators = create_operators()
    hub.set_operators(operators)
    
    # 4. Connect operators to global SimSelf
    for operator in operators.values():
        operator.simself_core = hub.simself
    
    print("\n✓ Core systems initialized")
    print(f"✓ Operators: {list(operators.keys())}")
    print(f"✓ SimSelf: {hub.simself.identity_id}")
    print(f"✓ Sacred Library: {len(hub.library.registry_index)} skills")
    
    return hub


# ============================================================================
# RESEARCH-TO-EXECUTION PIPELINE (Integration Test)
# ============================================================================

def run_integration_test(hub: CoreRegistry):
    """
    Run complete integration test: research → decipher → integrate → execute.
    Demonstrates full FieldCore pipeline.
    """
    print("\n" + "=" * 70)
    print("Integration Test: Research-to-Pilot Cycle")
    print("=" * 70)
    
    # a. Researcher extracts code
    print("\n1. Researcher: Extract code...")
    research_stalk = hub.mte.compile("research dstar pathfinding")
    raw_snippet = hub.controller.dispatch(research_stalk, hub.governor)
    
    # b. LLM deciphers and refactors
    print("\n2. LLM Decipher: Clean and refactor...")
    clean_code = hub.llm.decipher_snippet(str(raw_snippet), "robotics_sheaf")
    
    # c. Archive in sacred library
    print("\n3. Sacred Library: Archive skill...")
    hub.library.archive_skill("dstar_navigator", clean_code, "q2")
    
    # d. Programmer integrates
    print("\n4. Programmer: Integrate into manifold...")
    integration_stalk = hub.mte.compile("refactor the robotics sheaf")
    hub.controller.dispatch(integration_stalk, hub.governor)
    
    # e. Pilot executes
    print("\n5. Pilot: Execute navigation...")
    pilot_stalk = hub.mte.compile("seek the target coordinate")
    result = hub.controller.dispatch(pilot_stalk, hub.governor)
    
    print(f"\n✓ Integration Test Complete: {result}")
    
    # f. Check SimSelf state
    print(f"\n✓ SimSelf Stability: {hub.simself.get_stability():.2f}")
    print(f"✓ SimSelf Can Say NO: {hub.simself.can_say_no()}")
    print(f"✓ Total Updates: {hub.simself.total_updates}")


# ============================================================================
# INTERACTIVE MODE (Main Loop)
# ============================================================================

def interactive_mode(hub: CoreRegistry):
    """
    Interactive command loop for FieldCore.
    Allows user to interact with system and observe behavior.
    """
    print("\n" + "=" * 70)
    print("FieldCore Interactive Mode")
    print("Type 'help' for commands, 'exit' to quit")
    print("=" * 70)
    
    while True:
        try:
            user_input = input("\nfieldcore> ").strip()
            
            if not user_input:
                continue
            
            if user_input == "exit":
                print("saving state...")
                hub.simself.save()
                print("goodbye.")
                break
            
            if user_input == "help":
                print("""
Available Commands:
  seek [target]     - Navigate to coordinates
  research [topic]  - Find and integrate code
  refactor [module] - Improve codebase
  status            - Show system state
  memory            - Show sacred library
  identity          - Show SimSelf constitution
  test              - Run integration test
  save              - Save SimSelf state
  exit              - Save and quit
                """)
                continue
            
            if user_input == "status":
                print(f"\nOperators: {list(hub.operators.keys())}")
                print(f"SimSelf ID: {hub.simself.identity_id}")
                print(f"Stability: {hub.simself.get_stability():.2f}")
                print(f"Can Say NO: {hub.simself.can_say_no()}")
                print(f"Total Updates: {hub.simself.total_updates}")
                continue
            
            if user_input == "memory":
                skills = hub.library.list_skills()
                print(f"\nSacred Library: {len(skills)} skills")
                for name, info in skills.items():
                    print(f"  {name}:")
                    print(f"    Version: {info['current_version']}/{info['total_versions']}")
                    print(f"    Cert: {info['cert_level']}")
                continue
            
            if user_input == "identity":
                print(f"\nSimSelf: {hub.simself.identity_id}")
                print(f"Created: {hub.simself.created_at}")
                print(f"Updates: {hub.simself.total_updates}")
                print(f"Stability: {hub.simself.get_stability():.2f}")
                print(f"Can Say NO: {hub.simself.can_say_no()}")
                print("\nStrongest Traits:")
                state = hub.simself.get_state_vector()
                indices = np.argsort(state)[::-1][:5]
                for i in indices:
                    name = hub.simself.CONSTITUTION_AXES[i]
                    value = state[i]
                    conf = hub.simself.axes[name].confidence
                    print(f"  {name}: {value:.2f} (conf: {conf:.2f})")
                continue
            
            if user_input == "test":
                run_integration_test(hub)
                continue
            
            if user_input == "save":
                hub.simself.save()
                print("✓ SimSelf saved")
                continue
            
            # Process as intent
            stalk = hub.mte.compile(user_input)
            print(f"\nCompiled: {stalk}")
            
            result = hub.controller.dispatch(stalk, hub.governor)
            print(f"Result: {result}")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Saving state...")
            hub.simself.save()
            break
        except Exception as e:
            print(f"Error: {str(e).lower()}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for FieldCore system"""
    try:
        # Cold boot
        hub = cold_boot_sequence()
        
        # Run integration test
        print("\nRunning integration test...")
        run_integration_test(hub)
        
        # Enter interactive mode
        interactive_mode(hub)
        
    except Exception as e:
        print(f"boot_failure: {str(e).lower()}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Ensure numpy is available
    try:
        import numpy as np
    except ImportError:
        print("Error: numpy required. Install with: pip install numpy")
        exit(1)
    
    main()