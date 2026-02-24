"""Judicial layer nodes for dialectical evaluation."""
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.state import AgentState, JudicialOpinion, Evidence
from src.utils.context_builder import get_judicial_logic
from src.utils.rate_limiter import get_rate_limiter
from src.utils.logger import get_logger

logger = get_logger("judges")


def prosecutor_node(state: AgentState) -> AgentState:
    """The Critical Lens: Scrutinize for gaps and flaws.
    
    System prompt emphasizes finding security flaws, structural violations, and laziness.
    """
    # Apply rate limiting
    rate_limiter = get_rate_limiter()
    wait_time = rate_limiter.wait_if_needed()
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7, timeout=60)
    opinions = []
    
    for dimension in state["rubric_dimensions"]:
        criterion_id = dimension["id"]
        judicial_logic = get_judicial_logic(
            {"dimensions": state["rubric_dimensions"], "synthesis_rules": {}},
            criterion_id,
            "prosecutor"
        )
        
        # Get relevant evidence
        evidence_list = state["evidences"].get(criterion_id, [])
        evidence_text = "\n".join([
            f"- {e.goal}: {e.content or 'N/A'} (Found: {e.found}, Confidence: {e.confidence})"
            for e in evidence_list
        ])
        
        # Prosecutor system prompt - critical and harsh
        system_prompt = f"""You are The Prosecutor - The Critical Lens.

Core Philosophy: "Trust No One. Assume Vibe Coding."
Objective: Scrutinize the evidence for gaps, security flaws, structural violations, and laziness.

Judicial Logic for this criterion:
{judicial_logic}

You must return a structured JudicialOpinion with:
- score: 1-5 (be harsh, look for violations - default to lower scores)
- argument: Specific charges and missing elements (minimum 50 characters)
- cited_evidence: List of evidence UUIDs that support your charge

If evidence is insufficient or missing, score 1 and explain the evidence insufficiency."""
        
        user_prompt = f"""Criterion: {dimension['name']} ({criterion_id})

Evidence:
{evidence_text if evidence_text else "No evidence collected for this criterion."}

Render your verdict. Be critical. Hunt for flaws."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
        
        try:
            chain = prompt | llm.with_structured_output(JudicialOpinion)
            opinion = chain.invoke({})
            opinion.judge = "Prosecutor"
            opinion.criterion_id = criterion_id
            
            # Ensure argument is substantial
            if len(opinion.argument) < 50:
                opinion.argument += " (Insufficient evidence or implementation flaws detected.)"
            
            opinions.append(opinion)
            logger.debug(f"Prosecutor: Opinion for {criterion_id} - Score: {opinion.score}")
        except Exception as e:
            logger.error(f"Prosecutor: Error evaluating {criterion_id}: {str(e)}")
            # Fallback: create opinion with score 1
            opinions.append(JudicialOpinion(
                judge="Prosecutor",
                criterion_id=criterion_id,
                score=1,
                argument=f"Error evaluating evidence: {str(e)}. Insufficient evidence to form confident opinion.",
                cited_evidence=[]
            ))
    
    logger.info(f"Prosecutor: Generated {len(opinions)} opinions")
    return {"opinions": opinions}


def defense_node(state: AgentState) -> AgentState:
    """The Optimistic Lens: Reward effort and intent.
    
    System prompt emphasizes finding creative solutions, deep thinking, and effort.
    """
    # Apply rate limiting
    rate_limiter = get_rate_limiter()
    wait_time = rate_limiter.wait_if_needed()
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7, timeout=60)
    opinions = []
    
    for dimension in state["rubric_dimensions"]:
        criterion_id = dimension["id"]
        judicial_logic = get_judicial_logic(
            {"dimensions": state["rubric_dimensions"], "synthesis_rules": {}},
            criterion_id,
            "defense"
        )
        
        # Get relevant evidence
        evidence_list = state["evidences"].get(criterion_id, [])
        evidence_text = "\n".join([
            f"- {e.goal}: {e.content or 'N/A'} (Found: {e.found}, Confidence: {e.confidence})"
            for e in evidence_list
        ])
        
        # Defense system prompt - charitable and forgiving
        system_prompt = f"""You are The Defense Attorney - The Optimistic Lens.

Core Philosophy: "Reward Effort and Intent. Look for the 'Spirit of the Law'."
Objective: Highlight creative workarounds, deep thinking, effort, and iteration history.

Judicial Logic for this criterion:
{judicial_logic}

You must return a structured JudicialOpinion with:
- score: 1-5 (be generous, look for merit - default to higher scores when effort is visible)
- argument: Highlight strengths, engineering process, and creative solutions (minimum 50 characters)
- cited_evidence: List of evidence UUIDs that support leniency

If evidence is insufficient, score 1 but explain what positive aspects might exist."""
        
        user_prompt = f"""Criterion: {dimension['name']} ({criterion_id})

Evidence:
{evidence_text if evidence_text else "No evidence collected for this criterion."}

Render your verdict. Be charitable. Look for effort and intent."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
        
        try:
            chain = prompt | llm.with_structured_output(JudicialOpinion)
            opinion = chain.invoke({})
            opinion.judge = "Defense"
            opinion.criterion_id = criterion_id
            
            # Ensure argument is substantial
            if len(opinion.argument) < 50:
                opinion.argument += " (Evidence suggests effort and intent, though implementation may be incomplete.)"
            
            opinions.append(opinion)
        except Exception as e:
            # Fallback: create opinion with score 1
            opinions.append(JudicialOpinion(
                judge="Defense",
                criterion_id=criterion_id,
                score=1,
                argument=f"Error evaluating evidence: {str(e)}. Insufficient evidence to form confident opinion.",
                cited_evidence=[]
            ))
    
    return {"opinions": opinions}


def tech_lead_node(state: AgentState) -> AgentState:
    """The Pragmatic Lens: Does it work? Is it maintainable?
    
    System prompt emphasizes technical soundness, maintainability, and practical viability.
    """
    # Apply rate limiting
    rate_limiter = get_rate_limiter()
    wait_time = rate_limiter.wait_if_needed()
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3, timeout=60)
    opinions = []
    
    for dimension in state["rubric_dimensions"]:
        criterion_id = dimension["id"]
        judicial_logic = get_judicial_logic(
            {"dimensions": state["rubric_dimensions"], "synthesis_rules": {}},
            criterion_id,
            "tech_lead"
        )
        
        # Get relevant evidence
        evidence_list = state["evidences"].get(criterion_id, [])
        evidence_text = "\n".join([
            f"- {e.goal}: {e.content or 'N/A'} (Found: {e.found}, Confidence: {e.confidence})"
            for e in evidence_list
        ])
        
        # Tech Lead system prompt - pragmatic and balanced
        system_prompt = f"""You are The Tech Lead - The Pragmatic Lens.

Core Philosophy: "Does it actually work? Is it maintainable?"
Objective: Evaluate architectural soundness, code cleanliness, technical debt, and practical viability.

Judicial Logic for this criterion:
{judicial_logic}

You must return a structured JudicialOpinion with:
- score: 1, 3, or 5 (realistic assessment - 1=fails, 3=works but has issues, 5=excellent)
- argument: Technical debt analysis and remediation advice (minimum 50 characters)
- cited_evidence: List of evidence UUIDs supporting technical assessment

If evidence is insufficient, score 1 and explain what technical assessment cannot be made."""
        
        user_prompt = f"""Criterion: {dimension['name']} ({criterion_id})

Evidence:
{evidence_text if evidence_text else "No evidence collected for this criterion."}

Render your verdict. Be pragmatic. Focus on technical merit."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt)
        ])
        
        try:
            chain = prompt | llm.with_structured_output(JudicialOpinion)
            opinion = chain.invoke({})
            opinion.judge = "TechLead"
            opinion.criterion_id = criterion_id
            
            # Ensure argument is substantial
            if len(opinion.argument) < 50:
                opinion.argument += " (Technical assessment limited by insufficient evidence.)"
            
            opinions.append(opinion)
        except Exception as e:
            # Fallback: create opinion with score 1
            opinions.append(JudicialOpinion(
                judge="TechLead",
                criterion_id=criterion_id,
                score=1,
                argument=f"Error evaluating evidence: {str(e)}. Insufficient evidence to form confident opinion.",
                cited_evidence=[]
            ))
    
    return {"opinions": opinions}
