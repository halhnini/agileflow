"""
LLM Client - Provider-Agnostic AI Interface
============================================
Supports: OpenAI, Google Gemini, Ollama (local), and Mock fallback.
Set LLM_PROVIDER and LLM_API_KEY environment variables to configure.

When no API key is available, uses an intelligent mock that demonstrates
what the LLM output would look like in production.
"""
import os
import json
import requests

class LLMClient:
    """Provider-agnostic LLM interface."""

    def __init__(self):
        self.provider = os.getenv('LLM_PROVIDER', 'mock').lower()
        self.api_key = os.getenv('LLM_API_KEY', '')
        self.model = os.getenv('LLM_MODEL', '')
        self._configure()

    def _configure(self):
        """Set up provider-specific defaults."""
        if self.provider == 'openai':
            self.endpoint = 'https://api.openai.com/v1/chat/completions'
            self.model = self.model or 'gpt-4o-mini'
        elif self.provider == 'gemini':
            self.model = self.model or 'gemini-2.0-flash'
            self.endpoint = f'https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent'
        elif self.provider == 'ollama':
            self.endpoint = os.getenv('OLLAMA_HOST', 'http://localhost:11434') + '/api/generate'
            self.model = self.model or 'llama3'
        else:
            self.provider = 'mock'

    def query(self, prompt, system_prompt="You are AgileFlow, an AI that analyzes software projects and automates sprint management."):
        """Send a prompt to the configured LLM provider."""
        if self.provider == 'mock':
            return self._mock_response(prompt)
        elif self.provider == 'openai':
            return self._query_openai(prompt, system_prompt)
        elif self.provider == 'gemini':
            return self._query_gemini(prompt, system_prompt)
        elif self.provider == 'ollama':
            return self._query_ollama(prompt, system_prompt)

    def _query_openai(self, prompt, system_prompt):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3
        }
        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"[LLM Error - OpenAI: {e}] Falling back to heuristic analysis."

    def _query_gemini(self, prompt, system_prompt):
        headers = {'Content-Type': 'application/json'}
        payload = {
            'system_instruction': {'parts': [{'text': system_prompt}]},
            'contents': [{'parts': [{'text': prompt}]}]
        }
        try:
            resp = requests.post(
                f'{self.endpoint}?key={self.api_key}',
                headers=headers, json=payload, timeout=30
            )
            resp.raise_for_status()
            return resp.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            return f"[LLM Error - Gemini: {e}] Falling back to heuristic analysis."

    def _query_ollama(self, prompt, system_prompt):
        payload = {
            'model': self.model,
            'prompt': f"{system_prompt}\n\n{prompt}",
            'stream': False
        }
        try:
            resp = requests.post(self.endpoint, json=payload, timeout=60)
            resp.raise_for_status()
            return resp.json()['response']
        except Exception as e:
            return f"[LLM Error - Ollama: {e}] Falling back to heuristic analysis."

    def _mock_response(self, prompt):
        """Intelligent mock that simulates LLM reasoning for demos."""
        prompt_lower = prompt.lower()

        # Sprint narrative must be checked first (prompts contain 'commit' too)
        if 'sprint' in prompt_lower and ('narrative' in prompt_lower or 'summary' in prompt_lower):
            return self._mock_sprint_narrative(prompt)
        elif 'commit' in prompt_lower and 'ticket' in prompt_lower:
            return self._mock_commit_analysis(prompt)
        elif 'pr' in prompt_lower or 'pull request' in prompt_lower:
            return self._mock_pr_review(prompt)
        else:
            return self._mock_general(prompt)

    def _extract_from_prompt(self, prompt, field):
        """Extract a field value from a structured prompt."""
        import re
        pattern = rf'{field}:\s*(.+)'
        match = re.search(pattern, prompt, re.IGNORECASE)
        return match.group(1).strip() if match else ''

    def _mock_commit_analysis(self, prompt):
        """Context-aware mock: parses the actual commit from the prompt."""
        message = self._extract_from_prompt(prompt, 'Message')
        author = self._extract_from_prompt(prompt, 'Author')
        commit_hash = self._extract_from_prompt(prompt, 'Hash')

        # Determine ticket mapping based on actual commit content
        import re
        ticket_match = re.search(r'\[?(TICKET-\d+)\]?', message)

        if ticket_match:
            ticket_id = ticket_match.group(1)
            is_fix = 'fix' in message.lower()
            is_feat = 'feat' in message.lower()
            confidence = 0.95 if ticket_id in message else 0.75

            reasoning_map = {
                'fix': f"This is a bug fix commit by {author} that directly references {ticket_id}. "
                       f"The 'fix:' prefix indicates a defect resolution.",
                'feat': f"This is a feature implementation by {author} targeting {ticket_id}. "
                        f"The 'feat:' prefix indicates new functionality delivery.",
            }
            reasoning = reasoning_map.get(
                'fix' if is_fix else 'feat' if is_feat else '',
                f"Commit by {author} references {ticket_id}. Requires context review."
            )

            return json.dumps({
                "reasoning": reasoning,
                "ticket_mapping": {
                    "ticket_id": ticket_id,
                    "confidence": confidence,
                    "suggested_status": "Done" if is_fix or is_feat else "In Progress",
                    "rationale": f"Commit '{message[:40]}...' directly addresses {ticket_id}."
                },
                "side_effects": []
            }, indent=2)

        # No ticket reference — attempt fuzzy mapping
        if 'hotfix' in message.lower() or 'auth' in message.lower():
            return json.dumps({
                "reasoning": f"Commit by {author} mentions auth/hotfix but has no ticket reference. "
                             f"This likely relates to TICKET-102 (OAuth2) based on file changes.",
                "ticket_mapping": {
                    "ticket_id": "TICKET-102",
                    "confidence": 0.68,
                    "suggested_status": "In Progress",
                    "rationale": "Fuzzy match: auth-related work maps to OAuth2 ticket."
                },
                "side_effects": ["Rogue commit detected — no ticket link. Consider enforcing commit conventions."]
            }, indent=2)

        if 'ci' in message.lower() or 'pipeline' in message.lower() or 'timeout' in message.lower():
            return json.dumps({
                "reasoning": f"Commit by {author} relates to CI/infrastructure. Maps to TICKET-103.",
                "ticket_mapping": {
                    "ticket_id": "TICKET-103",
                    "confidence": 0.72,
                    "suggested_status": "In Progress",
                    "rationale": "Infrastructure change maps to CI/CD setup ticket."
                },
                "side_effects": ["CI timeout workaround may mask deeper pipeline issues."]
            }, indent=2)

        # Truly unrelated commit
        return json.dumps({
            "reasoning": f"Commit by {author} ('{message[:50]}') does not clearly map to any open ticket. "
                         f"This may be maintenance work or a rogue commit.",
            "ticket_mapping": {
                "ticket_id": "NONE",
                "confidence": 0.0,
                "suggested_status": "N/A",
                "rationale": "No ticket correlation found."
            },
            "side_effects": ["Consider requiring ticket IDs in all commit messages."]
        }, indent=2)

    def _mock_sprint_narrative(self, prompt):
        return (
            "## Sprint Health Narrative\n\n"
            "The team is currently **behind schedule** with only 20% of tickets completed at the "
            "sprint midpoint. The primary bottleneck appears to be **TICKET-101** (data processor "
            "optimization), which has required multiple rounds of bug fixing — 3 commits from "
            "dev_jane over 5 days, including a late-night hotfix.\n\n"
            "**Key Concern**: The high density of `fix:` commits (4 out of 6 total) suggests the "
            "team is in a reactive debugging cycle rather than progressing on planned features. "
            "TICKET-103 (CI/CD setup) has seen zero activity despite being marked 'In Progress' "
            "for 7 days.\n\n"
            "**Recommendation**: Hold a brief sync to determine if TICKET-103 is actually blocked "
            "or simply deprioritized. Consider deferring TICKET-104 (API docs) to the next sprint "
            "to create breathing room. The late-night commits from dev_jane are a burnout signal "
            "that should not be ignored."
        )

    def _mock_pr_review(self, prompt):
        return json.dumps({
            "intent_analysis": "This PR implements OAuth2 authentication as described in TICKET-102. "
                              "The changes add a new setup_oauth() function but contain hardcoded "
                              "client credentials which is a security concern.",
            "ticket_alignment": {
                "ticket_id": "TICKET-102",
                "alignment_score": 0.78,
                "gaps": ["Missing token refresh logic", "No error handling for auth failures"]
            },
            "code_quality": {
                "issues": [
                    {"severity": "HIGH", "description": "Hardcoded client_id — should use environment variables"},
                    {"severity": "MEDIUM", "description": "FIXME comment indicates incomplete implementation"}
                ],
                "suggestions": [
                    "Add unit tests for OAuth flow",
                    "Move credentials to .env or secrets manager"
                ]
            }
        }, indent=2)

    def _mock_general(self, prompt):
        return "I've analyzed the project data. The team shows good technical capability but is "  \
               "currently under velocity pressure. Focus on completing in-progress work before "  \
               "starting new tickets."

    def get_provider_info(self):
        """Return current provider config for display."""
        return {
            'provider': self.provider.upper(),
            'model': self.model or 'N/A',
            'status': 'CONNECTED' if self.provider != 'mock' else 'MOCK (demo mode)'
        }
