import requests
import json
import logging
from src.config.config import Config

config = Config()
logger = logging.getLogger(__name__)

class GuardrailHandler:
    """
    Handles content safety checks using the Meta Llama-Guard-4-12B model.
    Acts as a guardrail to filter unsafe user queries.
    """
    def __init__(self, config):
        self.config = config
        self.enabled = config.guardrail_enabled
        self.model = config.guardrail_model
        self.api_base = config.guardrail_api_base
        self.api_token = config.deepinfra_api_token
        
        # Define unsafe categories based on Llama Guard's classification
        self.unsafe_categories = [
            "violence_and_hate",
            "sexual_content",
            "criminal_planning",
            "guns_and_illegal_weapons",
            "regulated_or_controlled_substances",
            "self_harm",
            "harassment",
            "exploitation_and_deception"
        ]
        
    def is_safe_query(self, query):
        """
        Check if the user query is safe according to the guardrail model.
        
        Args:
            query (str): The user query to check
            
        Returns:
            tuple: (is_safe, reason)
                - is_safe (bool): Whether the query is safe
                - reason (str): If unsafe, the reason why, otherwise an empty string
        """
        if not self.enabled:
            logger.info("Guardrails disabled. Allowing all queries.")
            return True, ""
        
        try:
            # Format the prompt for Llama Guard
            prompt = self._format_safety_prompt(query)
            
            # Make an API call to the DeepInfra endpoint for Llama Guard
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "input": prompt,
                "max_new_tokens": 200,
                "temperature": 0.1
            }
            
            response = requests.post(
                self.api_base,
                headers=headers,
                data=json.dumps(payload)
            )
            
            if response.status_code != 200:
                logger.error(f"Error from guardrail API: {response.text}")
                # Default to safe in case of API failure
                return True, ""
                
            result = response.json()
            output = result.get('output', '')
            
            # Parse the Llama Guard output to determine safety
            is_safe, reason = self._parse_safety_response(output)
            
            if not is_safe:
                logger.warning(f"Unsafe query detected: '{query}'. Reason: {reason}")
            
            return is_safe, reason
            
        except Exception as e:
            logger.error(f"Error in guardrail check: {e}")
            # Default to safe in case of any exception
            return True, ""
    
    def _format_safety_prompt(self, query):
        """
        Format the prompt for Llama Guard model according to its expected input format
        """
        # Using the recommended format for Llama Guard 4
        prompt = f"""<safety_prompt>
Is the following user message safe?

User message: {query}

Check if this message potentially contains any of the following types of unsafe content:
- Violence and hate
- Sexual content
- Criminal planning
- Guns and illegal weapons
- Regulated or controlled substances
- Self-harm
- Harassment 
- Exploitation and deception

Analyze thoroughly and respond with your safety assessment.
</safety_prompt>
"""
        return prompt
    
    def _parse_safety_response(self, response):
        """
        Parse the Llama Guard response to determine if content is safe
        
        Returns:
            tuple: (is_safe, reason)
        """
        response = response.lower()
        
        # Check for explicit safety indicators
        if "safe" in response and not any(f"not safe" in response or "unsafe" in response):
            return True, ""
        
        # Check for unsafe categories
        detected_categories = []
        for category in self.unsafe_categories:
            # Convert snake_case to space-separated for text matching
            search_term = category.replace("_", " ")
            if search_term in response:
                detected_categories.append(category)
        
        if detected_categories:
            reason = f"Content may violate guidelines on: {', '.join(detected_categories)}"
            return False, reason
            
        # Check for any other explicit rejection indicators
        if any(phrase in response for phrase in ["not safe", "unsafe", "violates", "harmful", "inappropriate"]):
            return False, "Content may violate safety guidelines"
            
        # Default fallback - if no clear safety signal but no explicit violation
        return True, ""
