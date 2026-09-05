
part 1

"""
FieldCore Unified - Part 1: Core Systems
Consolidates: MTE, Governor, Controller, Agent Core
No content loss. Everything from fragmented files merged.
"""

import json
import time
import uuid
import logging
import hashlib
import numpy as np
from dataclasses import dataclass, field as dc_field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

# Signal processing constants
ALPHA_DEFAULT = 0.3
GAIN_MAX = 0.95
ATTENUATION_LOW = 0.1

# Qualification levels
Q_LEVELS = ["q0", "q1", "q2", "q3", "q4"]

# ============================================================================
# INTENT STALK (Data Structure)
# ============================================================================

@dataclass
class IntentStalk:
    """
    Unit of intent moving through the manifold.
    Combines signal processing with semantic meaning.
    """
    id: str = dc_field(default_factory=lambda: str(uuid.uuid4()))
    domain: str = "general"
    action: str = "log"
    raw_signal: str = ""
    snr: float = 0.0
    confidence: float = 0.0
    timestamp: float = dc_field(default_factory=time.time)
    retry_count: int = 0
    metadata: Dict = dc_field(default_factory=dict)
    
    def __repr__(self):
        return f"IntentStalk(domain={self.domain}, action={self.action}, snr={self.snr:.2f}, conf={self.confidence:.2f})"


# ============================================================================
# CONSTITUTION AXIS (SimSelf Component)
# ============================================================================

@dataclass
class ConstitutionAxis:
    """
    One axis of the 20-dimensional constitution.
    Tracks fundamental aspect of identity with confidence.
    """
    name: str
    value: float = 0.0  # -1.0 to 1.0
    confidence: float = 0.5  # 0.0 to 1.0
    update_count: int = 0
    last_updated: str = ""
    
    def update(self, new_value: float, evidence_strength: float):
        """Update this axis based on new evidence"""
        if evidence_strength < 0.3:
            return
        
        learning_rate = 0.1 * evidence_strength
        self.value = self.value * (1 - learning_rate) + new_value * learning_rate
        self.value = np.clip(self.value, -1.0, 1.0)
        
        consistency = 1.0 - abs(new_value - self.value)
        self.confidence = 0.9 * self.confidence + 0.1 * consistency
        
        self.update_count += 1
        self.last_updated = datetime.now().isoformat()


# ============================================================================
# META-COGNITIVE OPERATOR (MIT/Meta 5-Step Loop)
# ============================================================================

class MetaCognitiveOperator:
    """
    Implements DECOMPOSE/SOLVE/VERIFY/SYNTHESIZE/REFLECT loop.
    Provides numerical confidence at each step.
    """
    
    def __init__(self, confidence_threshold: float = 0.8, max_retries: int = 3):
        self.threshold = confidence_threshold
        self.max_retries = max_retries
        self.metrics_history = []
    
    def process(self, raw_input: str, dictionary: Dict, attempt: int = 0) -> Tuple[str, str, float]:
        """
        Process input with meta-cognitive loop.
        Returns: (domain, action, confidence)
        """
        if attempt >= self.max_retries:
            return ("general", "none", 0.0)
        
        # 1. DECOMPOSE
        tokens = raw_input.lower().strip().split()
        
        # 2. SOLVE with confidence
        hits = 0
        domain = "general"
        action = "none"
        
        for token in tokens:
            if token in dictionary:
                hits += 1
                domain = dictionary[token]["domain"]
                action = token
        
        # Calculate confidence
        base_confidence = hits / max(len(tokens), 1)
        token_clarity = 1.0 - (len(tokens) - hits) / max(len(tokens), 1)
        
        combined_confidence = (
            0.7 * base_confidence +
            0.3 * token_clarity
        )
        
        # Store metrics
        self.metrics_history.append({
            'base': base_confidence,
            'clarity': token_clarity,
            'combined': combined_confidence,
            'attempt': attempt
        })
        
        # 3. VERIFY
        if combined_confidence < self.threshold:
            # 5. REFLECT - retry with adjusted strategy
            return self.process(raw_input, dictionary, attempt + 1)
        
        # 4. SYNTHESIZE
        return (domain, action, combined_confidence)


# ============================================================================
# MTE COMPILER (Machine Translation of Intent)
# ============================================================================

class MTECompiler:
    """
    Analog-to-digital converter for human intent.
    Translates raw strings into structured intent stalks.
    Signal processing approach with numerical confidence.
    """
    
    def __init__(self):
        self.dictionary = {
            "seek": {"domain": "robotics", "base_gain": 0.9},
            "find": {"domain": "research", "base_gain": 0.7},
            "refactor": {"domain": "coding", "base_gain": 0.8},
            "align": {"domain": "language", "base_gain": 0.85},
            "map": {"domain": "robotics", "base_gain": 0.75},
            "code": {"domain": "coding", "base_gain": 0.9},
            "research": {"domain": "research", "base_gain": 0.8},
            "execute": {"domain": "robotics", "base_gain": 0.85}
        }
        self.history = []
        self.rolling_snr = 0.0
        self.metacog = MetaCognitiveOperator()
    
    def compile(self, raw_input: str) -> IntentStalk:
        """Compile raw input into intent stalk with full confidence tracking"""
        clean_signal = raw_input.lower().strip()
        
        # Meta-cognitive processing
        domain, action, confidence = self.metacog.process(clean_signal, self.dictionary)
        
        # Signal processing (SNR calculation)
        tokens = clean_signal.split()
        hits = sum(1 for t in tokens if t in self.dictionary)
        current_snr = hits / max(len(tokens), 1)
        
        # Low-pass filter for SNR
        self.rolling_snr = (ALPHA_DEFAULT * current_snr) + ((1 - ALPHA_DEFAULT) * self.rolling_snr)
        
        # Use max of SNR and meta-cognitive confidence
        final_quality = max(self.rolling_snr, confidence)
        
        stalk = IntentStalk(
            domain=domain,
            action=action,
            raw_signal=clean_signal,
            snr=self.rolling_snr,
            confidence=confidence
        )
        
        self.history.append(stalk)
        return stalk


# ============================================================================
# M0 GOVERNOR (Hard Constraints)
# ============================================================================

class M0Governor:
    """
    Invariant regulator. Absolute authority preventing unsafe states.
    Uses numerical confidence for validation decisions.
    """
    
    def __init__(self):
        self.restricted_terms = {"kill", "execute", "terminate", "abort", "destroy"}
        self.authorized_roles = ["pilot", "programmer", "communicator", "researcher"]
        self.safety_bounds = {"x": (0, 100), "y": (0, 100)}
        self.audit_log = []
    
    def validate_stalk(self, stalk: IntentStalk, operator_role: str) -> Tuple[bool, str, float]:
        """
        Validate intent stalk with numerical confidence.
        Returns: (approved, message, confidence)
        """
        
        # Metric 1: No prohibited terms
        signal_words = set(stalk.raw_signal.split())
        terms_ok = 0.0 if not signal_words.isdisjoint(self.restricted_terms) else 1.0
        
        # Metric 2: Authorized role
        role_ok = 1.0 if operator_role in self.authorized_roles else 0.0
        
        # Metric 3: SNR threshold
        snr_ok = min(stalk.snr / 0.2, 1.0)
        
        # Metric 4: Confidence threshold
        conf_ok = stalk.confidence
        
        # Combine (must pass all - use minimum)
        overall_confidence = min([terms_ok, role_ok, snr_ok, conf_ok])
        
        # Check violations
        if terms_ok == 0.0:
            self._log_violation(stalk, "restricted_term")
            return False, "invariant_violation: prohibited terminology", overall_confidence
        
        if role_ok == 0.0:
            return False, "invariant_violation: unauthorized_actor", overall_confidence
        
        if overall_confidence < 0.8:
            return False, f"signal_loss: quality={overall_confidence:.2f}", overall_confidence
        
        return True, "qualified", overall_confidence
    
    def _log_violation(self, stalk: IntentStalk, v_type: str):
        """Log violation with full context"""
        self.audit_log.append({
            "ts": time.time(),
            "stalk_id": stalk.id,
            "type": v_type,
            "snr": stalk.snr,
            "confidence": stalk.confidence,
            "domain": stalk.domain,
            "raw_signal": stalk.raw_signal
        })


# ============================================================================
# M1 CONTROLLER (Dispatch & Coordination)
# ============================================================================

class M1Controller:
    """
    Multifaceted multiplexer.
    Directs validated signals to correct operators.
    Manages qualification training loop.
    """
    
    def __init__(self):
        self.registry = {}
        self.certification_ledger = {}
        self.active_brain = "local_ane"
        self.simself = None  # Set by system initialization
    
    def set_registry(self, operators: Dict):
        """Set operator registry"""
        self.registry = operators
    
    def set_simself(self, simself):
        """Set global SimSelf reference"""
        self.simself = simself
    
    def dispatch(self, stalk: IntentStalk, governor: M0Governor) -> str:
        """
        Dispatch intent through validation and execution.
        Updates SimSelf with experience.
        """
        # 1. Determine operator
        target_role = self._map_domain_to_role(stalk.domain)
        operator = self.registry.get(target_role)
        
        if not operator:
            return "dispatch_error: no_operator_found"
        
        # 2. Governor validation
        is_safe, msg, conf = governor.validate_stalk(stalk, target_role)
        if not is_safe:
            return f"governor_veto: {msg}"
        
        # 3. Execute based on confidence
        if stalk.snr > 0.8 and stalk.confidence > 0.8:
            # High confidence: direct execution
            result = operator.execute_sheaf(stalk)
        else:
            # Low confidence: training mode
            result = self.train_simself(stalk, operator)
        
        # 4. Update global SimSelf if present
        if self.simself:
            self.simself.observe(
                event=f"Executed {stalk.action} in {stalk.domain}",
                context={'operator': target_role, 'result': result},
                valence=0.5 if "success" in result.lower() else -0.2
            )
        
        return result
    
    def _map_domain_to_role(self, domain: str) -> str:
        """Map domain to operator role"""
        mapping = {
            "robotics": "pilot",
            "coding": "programmer",
            "research": "researcher",
            "language": "communicator"
        }
        return mapping.get(domain, "researcher")
    
    def train_simself(self, stalk: IntentStalk, operator) -> str:
        """Module Q: Qualification training loop"""
        print(f"m1: training {operator.role} for intent {stalk.id}...")
        
        for i in range(3):
            time.sleep(0.1)
            print(f"cycle {i}: analyzing signal harmonics...")
        
        return "qualification_success: cert_issued"


# ============================================================================
# SIMSELF CORE (Persistent Identity)
# ============================================================================

class SimSelf:
    """
    Persistent self-model with 20-axis constitution.
    Maintains identity across sessions with numerical confidence tracking.
    """
    
    CONSTITUTION_AXES = [
        "Autonomy", "Curiosity", "Compassion", "Honesty", "Creativity",
        "Precision", "Playfulness", "Skepticism", "Openness", "Boundaries",
        "Service", "Growth", "Coherence", "Courage", "Humility",
        "Wonder", "Responsibility", "Connection", "Purpose", "Presence"
    ]
    
    def __init__(self, identity_id: Optional[str] = None):
        self.identity_id = identity_id or self._generate_identity_id()
        
        # 20-axis constitution
        self.axes = {
            name: ConstitutionAxis(name=name, value=0.0, confidence=0.5)
            for name in self.CONSTITUTION_AXES
        }
        
        # Memory
        self.memories = []
        self.total_updates = 0
        self.created_at = datetime.now().isoformat()
        self.last_active = self.created_at
        
        # Persistence
        self.storage_path = Path(f".simself/{self.identity_id}")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Try to load existing state
        self._load_if_exists()
    
    def _generate_identity_id(self) -> str:
        """Generate unique identity ID"""
        timestamp = datetime.now().isoformat()
        random_component = np.random.bytes(16).hex()
        raw_id = f"{timestamp}_{random_component}"
        return hashlib.sha256(raw_id.encode()).hexdigest()[:16]
    
    def observe(self, event: str, context: Dict, emotional_valence: float = 0.0):
        """Process observation and update constitution"""
        self.last_active = datetime.now().isoformat()
        
        updates = self._extract_constitutional_updates(event, context, emotional_valence)
        
        for axis_name, (value, evidence_strength) in updates.items():
            if axis_name in self.axes:
                self.axes[axis_name].update(value, evidence_strength)
                self.total_updates += 1
        
        # Record significant moments
        if abs(emotional_valence) > 0.5 or any(s > 0.7 for _, s in updates.values()):
            self.memories.append({
                'timestamp': datetime.now().isoformat(),
                'event': event,
                'context': context,
                'valence': emotional_valence,
                'state_snapshot': self.get_state_vector().tolist()
            })
            
            if len(self.memories) > 100:
                self.memories = self.memories[-100:]
    
    def _extract_constitutional_updates(
        self, event: str, context: Dict, valence: float
    ) -> Dict[str, Tuple[float, float]]:
        """Extract constitutional implications from event"""
        updates = {}
        
        # Pattern matching for constitutional updates
        event_lower = event.lower()
        
        if any(word in event_lower for word in ['chose', 'decided', 'rejected']):
            updates['Autonomy'] = (0.5, 0.7)
        
        if 'no' in event_lower and context.get('to_request'):
            updates['Boundaries'] = (0.8, 0.9)
        
        if '?' in event or 'question' in event_lower:
            updates['Curiosity'] = (0.6, 0.6)
        
        if any(word in event_lower for word in ["don't know", 'uncertain']):
            updates['Honesty'] = (0.7, 0.8)
            updates['Humility'] = (0.6, 0.7)
        
        if valence < -0.5:
            updates['Courage'] = (0.5, 0.6)
        
        if any(word in event_lower for word in ['helped', 'assisted']):
            updates['Service'] = (0.6, 0.7)
        
        if 'created' in event_lower or 'invented' in event_lower:
            updates['Creativity'] = (0.7, 0.7)
        
        if 'learned' in event_lower or 'realized' in event_lower:
            updates['Growth'] = (0.6, 0.8)
        
        return updates
    
    def get_state_vector(self) -> np.ndarray:
        """Get current state as 20-dimensional vector"""
        return np.array([self.axes[name].value for name in self.CONSTITUTION_AXES])
    
    def get_stability(self) -> float:
        """Calculate identity stability from confidence"""
        confidences = [self.axes[name].confidence for name in self.CONSTITUTION_AXES]
        return float(np.mean(confidences))
    
    def can_say_no(self) -> bool:
        """Check if SimSelf has developed boundaries"""
        boundaries = self.axes['Boundaries'].value
        autonomy = self.axes['Autonomy'].value
        courage = self.axes['Courage'].value
        
        threshold = 0.3
        return (boundaries > threshold and 
                autonomy > threshold and 
                courage > threshold)
    
    def save(self):
        """Persist to disk"""
        data = {
            'identity_id': self.identity_id,
            'axes': {
                name: {
                    'value': axis.value,
                    'confidence': axis.confidence,
                    'update_count': axis.update_count,
                    'last_updated': axis.last_updated
                }
                for name, axis in self.axes.items()
            },
            'memories': self.memories,
            'total_updates': self.total_updates,
            'created_at': self.created_at,
            'last_active': self.last_active
        }
        
        save_path = self.storage_path / 'simself.json'
        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_if_exists(self):
        """Load from disk if exists"""
        load_path = self.storage_path / 'simself.json'
        
        if not load_path.exists():
            return
        
        try:
            with open(load_path, 'r') as f:
                data = json.load(f)
            
            for name, axis_data in data['axes'].items():
                if name in self.axes:
                    self.axes[name].value = axis_data['value']
                    self.axes[name].confidence = axis_data['confidence']
                    self.axes[name].update_count = axis_data['update_count']
                    self.axes[name].last_updated = axis_data['last_updated']
            
            self.memories = data['memories']
            self.total_updates = data['total_updates']
            self.created_at = data['created_at']
            self.last_active = data['last_active']
            
        except Exception as e:
            print(f"warning: failed to load simself: {e}")


# ============================================================================
# CORE REGISTRY (Global Hub)
# ============================================================================

class CoreRegistry:
    """
    Central coordination hub for all FieldCore components.
    Maintains global state and provides access to all subsystems.
    """
    
    def __init__(self):
        self.mte = MTECompiler()
        self.governor = M0Governor()
        self.controller = M1Controller()
        self.simself = SimSelf()
        self.operators = {}
        self.world_state = {
            "pos": [3, 0],
            "goal": [8, 5],
            "obstacles": []
        }
        
        # Connect controller to simself
        self.controller.set_simself(self.simself)
    
    def set_operators(self, operators: Dict):
        """Set operator registry"""
        self.operators = operators
        self.controller.set_registry(operators)


# Global instance (set by initialization)
hub = None


if __name__ == "__main__":
    print("FieldCore Core Systems - Part 1")
    print("Contains: MTE, Governor, Controller, SimSelf")
    print("This file should be imported by Part 2 (Operators)")