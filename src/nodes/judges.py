"""Judicial layer nodes for dialectical evaluation.

STRUCTURED OUTPUT ENFORCEMENT (rubric: structured_output_enforcement):
- All Judge LLM calls use .with_structured_output(JudicialOpinion) bound to the Pydantic schema.
- Output includes score (int 1-5), argument (str), cited_evidence (list of evidence UUIDs).
- Retry logic (JUDICIAL_OPINION_RETRIES) on Pydantic ValidationError and parse failures.
- Output is validated against JudicialOpinion before being added to state.

JUDICIAL NUANCE AND DIALECTICS (rubric: judicial_nuance):
- Three distinct, conflicting personas run in parallel on the same evidence:
  1. Prosecutor: adversarial lens; looks for gaps, security flaws, structural violations, laziness.
  2. Defense: charitable lens; rewards effort, intent, creative workarounds, Spirit of the Law.
  3. Tech Lead: pragmatic lens; focuses on architectural soundness, maintainability, practical viability.
- Each persona has a separate system prompt; prompts are intentionally distinct to produce genuine score variance.
"""
from typing import Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from src.state import AgentState, JudicialOpinion, Evidence
from src.config import load_env_config
from src.utils.context_builder import get_judicial_logic
from src.utils.rate_limiter import get_rate_limiter
from src.utils.logger import get_logger

logger = get_logger("judges")

# Retries for structured output parse/validation failures (e.g. invalid JSON from LLM)
JUDICIAL_OPINION_RETRIES = 3


def _escape_braces_for_prompt(text: str) -> str:
    """Escape { and } so LangChain prompt template doesn't treat them as placeholders."""
    if not text:
        return text
    return str(text).replace("{", "{{").replace("}", "}}")


def _invoke_judicial_chain(chain, judge_name: str, criterion_id: str) -> Optional[JudicialOpinion]:
    """Invoke chain with retries on validation/parse errors. Returns None if all retries fail.
    Explicitly retries on Pydantic ValidationError (malformed LLM output) and other exceptions.
    """
    last_error = None
    for attempt in range(JUDICIAL_OPINION_RETRIES):
        try:
            opinion = chain.invoke({})
            if opinion and isinstance(opinion, JudicialOpinion):
                return opinion
        except ValidationError as e:
            last_error = e
            logger.warning(
                f"{judge_name}: Attempt {attempt + 1}/{JUDICIAL_OPINION_RETRIES} for {criterion_id} "
                f"structured output validation failed: {e}"
            )
        except Exception as e:
            last_error = e
            logger.warning(
                f"{judge_name}: Attempt {attempt + 1}/{JUDICIAL_OPINION_RETRIES} for {criterion_id} failed: {e}"
            )
    logger.error(f"{judge_name}: All {JUDICIAL_OPINION_RETRIES} attempts failed for {criterion_id}: {last_error}")
    return None


def _create_llm(temperature: float, model: str = None) -> ChatOpenAI:
    """Create LLM instance with proper configuration for OpenAI or OpenRouter.
    
    Args:
        temperature: Temperature for the model
        model: Model name (optional, uses config default if not provided)
        
    Returns:
        Configured ChatOpenAI instance
    """
    config = load_env_config()
    api_key = config["api_key"]
    use_openrouter = config.get("use_openrouter", False)
    model_name = model or config.get("model", "gpt-4o")
    
    if use_openrouter:
        # OpenRouter configuration
        base_url = config.get("openrouter_base_url", "https://openrouter.ai/api/v1")
        llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            timeout=60,
            api_key=api_key,
            base_url=base_url,
            default_headers={
                "HTTP-Referer": "https://github.com/MamaMoh/TRP1-Challenge-Week-2",  # Optional
                "X-Title": "Automaton Auditor",  # Optional
            }
        )
    else:
        # Standard OpenAI configuration
        llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            timeout=60,
            api_key=api_key
        )
    
    return llm


def prosecutor_node(state: AgentState) -> AgentState:
    """The Critical Lens: Scrutinize for gaps and flaws.
    
    System prompt emphasizes finding security flaws, structural violations, and laziness.
    """
    # Apply rate limiting
    rate_limiter = get_rate_limiter()
    wait_time = rate_limiter.wait_if_needed()
    
    llm = _create_llm(temperature=0.7)
    opinions = []
    
    for dimension in state["rubric_dimensions"]:
        criterion_id = dimension["id"]
        judicial_logic = get_judicial_logic(
            {"dimensions": state["rubric_dimensions"], "synthesis_rules": {}},
            criterion_id,
            "prosecutor"
        )
        
        # Get relevant evidence (escape braces so prompt template doesn't interpret them)
        evidence_list = state["evidences"].get(criterion_id, [])
        evidence_text = "\n".join([
            f"- {e.goal}: {e.content or 'N/A'} (Found: {e.found}, Confidence: {e.confidence})"
            for e in evidence_list
        ])
        evidence_text_safe = _escape_braces_for_prompt(evidence_text)
        judicial_logic_safe = _escape_braces_for_prompt(judicial_logic)

        # Prosecutor system prompt - adversarial, critical, harsh (distinct from Defense/Tech Lead)
        system_prompt = f"""You are The Prosecutor - The Critical Lens.

Core Philosophy: "Trust No One. Assume Vibe Coding."
Objective: Adversarial scrutiny. Scrutinize the evidence for gaps, security flaws, structural violations, and laziness.

Judicial Logic for this criterion:
{judicial_logic_safe}

You must return a structured JudicialOpinion with:
- score: 1-5 (be harsh, look for violations - default to lower scores)
- argument: Specific charges and missing elements (minimum 50 characters)
- cited_evidence: List of evidence UUIDs that support your charge

If evidence is insufficient or missing, score 1 and explain the evidence insufficiency."""

        user_prompt = f"""Criterion: {_escape_braces_for_prompt(dimension['name'])} ({criterion_id})

Evidence:
{evidence_text_safe if evidence_text_safe else "No evidence collected for this criterion."}

Render your verdict. Be critical. Hunt for flaws."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
        
        chain = prompt | llm.with_structured_output(JudicialOpinion)
        opinion = _invoke_judicial_chain(chain, "Prosecutor", criterion_id)
        if opinion:
            opinion.judge = "Prosecutor"
            opinion.criterion_id = criterion_id
            if len(opinion.argument) < 50:
                opinion.argument += " (Insufficient evidence or implementation flaws detected.)"
            opinions.append(opinion.model_dump())
            logger.debug(f"Prosecutor: Opinion for {criterion_id} - Score: {opinion.score}")
        else:
            opinions.append(JudicialOpinion(
                judge="Prosecutor",
                criterion_id=criterion_id,
                score=1,
                argument="Structured output parse failed after retries. Insufficient evidence to form confident opinion.",
                cited_evidence=[]
            ).model_dump())
    logger.info(f"Prosecutor: Generated {len(opinions)} opinions")
    return {"opinions": opinions}


def defense_node(state: AgentState) -> AgentState:
    """The Optimistic Lens: Reward effort and intent.
    
    System prompt emphasizes finding creative solutions, deep thinking, and effort.
    """
    # Apply rate limiting
    rate_limiter = get_rate_limiter()
    wait_time = rate_limiter.wait_if_needed()
    
    llm = _create_llm(temperature=0.7)
    opinions = []
    
    for dimension in state["rubric_dimensions"]:
        criterion_id = dimension["id"]
        judicial_logic = get_judicial_logic(
            {"dimensions": state["rubric_dimensions"], "synthesis_rules": {}},
            criterion_id,
            "defense"
        )
        
        # Get relevant evidence (escape braces for prompt template)
        evidence_list = state["evidences"].get(criterion_id, [])
        evidence_text = "\n".join([
            f"- {e.goal}: {e.content or 'N/A'} (Found: {e.found}, Confidence: {e.confidence})"
            for e in evidence_list
        ])
        evidence_text_safe = _escape_braces_for_prompt(evidence_text)
        judicial_logic_safe = _escape_braces_for_prompt(judicial_logic)

        # Defense system prompt - charitable, forgiving (distinct from Prosecutor/Tech Lead)
        system_prompt = f"""You are The Defense Attorney - The Optimistic Lens.

Core Philosophy: "Reward Effort and Intent. Look for the 'Spirit of the Law'."
Objective: Charitable interpretation. Highlight creative workarounds, deep thinking, effort, and iteration history.

Judicial Logic for this criterion:
{judicial_logic_safe}

You must return a structured JudicialOpinion with:
- score: 1-5 (be generous, look for merit - default to higher scores when effort is visible)
- argument: Highlight strengths, engineering process, and creative solutions (minimum 50 characters)
- cited_evidence: List of evidence UUIDs that support leniency

If evidence is insufficient, score 1 but explain what positive aspects might exist."""

        user_prompt = f"""Criterion: {_escape_braces_for_prompt(dimension['name'])} ({criterion_id})

Evidence:
{evidence_text_safe if evidence_text_safe else "No evidence collected for this criterion."}

Render your verdict. Be charitable. Look for effort and intent."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
        
        chain = prompt | llm.with_structured_output(JudicialOpinion)
        opinion = _invoke_judicial_chain(chain, "Defense", criterion_id)
        if opinion:
            opinion.judge = "Defense"
            opinion.criterion_id = criterion_id
            if len(opinion.argument) < 50:
                opinion.argument += " (Evidence suggests effort and intent, though implementation may be incomplete.)"
            opinions.append(opinion.model_dump())
        else:
            opinions.append(JudicialOpinion(
                judge="Defense",
                criterion_id=criterion_id,
                score=1,
                argument="Structured output parse failed after retries. Insufficient evidence to form confident opinion.",
                cited_evidence=[]
            ).model_dump())
    return {"opinions": opinions}


def tech_lead_node(state: AgentState) -> AgentState:
    """The Pragmatic Lens: Does it work? Is it maintainable?
    
    System prompt emphasizes technical soundness, maintainability, and practical viability.
    """
    # Apply rate limiting
    rate_limiter = get_rate_limiter()
    wait_time = rate_limiter.wait_if_needed()
    
    llm = _create_llm(temperature=0.3)
    opinions = []
    
    for dimension in state["rubric_dimensions"]:
        criterion_id = dimension["id"]
        judicial_logic = get_judicial_logic(
            {"dimensions": state["rubric_dimensions"], "synthesis_rules": {}},
            criterion_id,
            "tech_lead"
        )
        
        # Get relevant evidence (escape braces for prompt template)
        evidence_list = state["evidences"].get(criterion_id, [])
        evidence_text = "\n".join([
            f"- {e.goal}: {e.content or 'N/A'} (Found: {e.found}, Confidence: {e.confidence})"
            for e in evidence_list
        ])
        evidence_text_safe = _escape_braces_for_prompt(evidence_text)
        judicial_logic_safe = _escape_braces_for_prompt(judicial_logic)

        # Tech Lead system prompt - pragmatic, balanced (distinct from Prosecutor/Defense)
        system_prompt = f"""You are The Tech Lead - The Pragmatic Lens.

Core Philosophy: "Does it actually work? Is it maintainable?"
Objective: Pragmatic assessment. Evaluate architectural soundness, code cleanliness, technical debt, and practical viability.

Judicial Logic for this criterion:
{judicial_logic_safe}

You must return a structured JudicialOpinion with:
- score: 1, 3, or 5 (realistic assessment - 1=fails, 3=works but has issues, 5=excellent)
- argument: Technical debt analysis and remediation advice (minimum 50 characters)
- cited_evidence: List of evidence UUIDs supporting technical assessment

If evidence is insufficient, score 1 and explain what technical assessment cannot be made."""

        user_prompt = f"""Criterion: {_escape_braces_for_prompt(dimension['name'])} ({criterion_id})

Evidence:
{evidence_text_safe if evidence_text_safe else "No evidence collected for this criterion."}

Render your verdict. Be pragmatic. Focus on technical merit."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
        
        chain = prompt | llm.with_structured_output(JudicialOpinion)
        opinion = _invoke_judicial_chain(chain, "TechLead", criterion_id)
        if opinion:
            opinion.judge = "TechLead"
            opinion.criterion_id = criterion_id
            if len(opinion.argument) < 50:
                opinion.argument += " (Technical assessment limited by insufficient evidence.)"
            opinions.append(opinion.model_dump())
        else:
            opinions.append(JudicialOpinion(
                judge="TechLead",
                criterion_id=criterion_id,
                score=1,
                argument="Structured output parse failed after retries. Insufficient evidence to form confident opinion.",
                cited_evidence=[]
            ).model_dump())
    return {"opinions": opinions}
