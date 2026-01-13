"""
Token & Cost Estimator - Feature #2: LLM Token & Cost Estimation (Informational)

Provides pre-generation analysis of token usage and estimated costs.

Rules:
- No runtime billing assumptions
- No optimization claims
- Display estimates only, never enforce decisions
- Clearly marked as non-guaranteed
- All estimates are informational only
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CostEstimate:
    """
    Represents a cost estimate - explicitly marked as informational.
    
    IMPORTANT: These estimates are not guaranteed and may not reflect
    actual costs. Use for planning purposes only.
    """
    # Token estimates
    tokens_per_chat_request: int = 0
    tokens_per_rag_query: int = 0
    tokens_per_embedding: int = 0
    
    # Cost estimates (USD)
    estimated_cost_per_chat_request_usd: float = 0.0
    estimated_cost_per_rag_query_usd: float = 0.0
    estimated_cost_per_embedding_usd: float = 0.0
    
    # Monthly projections (based on assumed usage)
    monthly_estimate_low_usd: float = 0.0
    monthly_estimate_high_usd: float = 0.0
    assumed_requests_per_day_low: int = 100
    assumed_requests_per_day_high: int = 10000
    
    # Metadata
    model_used: str = ""
    embedding_model_used: str = ""
    pricing_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    # Mandatory disclaimer
    disclaimer: str = (
        "DISCLAIMER: These estimates are informational only and NOT guaranteed. "
        "Actual costs depend on usage patterns, prompt lengths, response lengths, "
        "and current API pricing which may change. Do not use these estimates for "
        "billing or financial planning without verification from your LLM provider."
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "tokens": {
                "per_chat_request": self.tokens_per_chat_request,
                "per_rag_query": self.tokens_per_rag_query,
                "per_embedding": self.tokens_per_embedding,
            },
            "costs_usd": {
                "per_chat_request": round(self.estimated_cost_per_chat_request_usd, 6),
                "per_rag_query": round(self.estimated_cost_per_rag_query_usd, 6),
                "per_embedding": round(self.estimated_cost_per_embedding_usd, 6),
            },
            "monthly_projection_usd": {
                "low": round(self.monthly_estimate_low_usd, 2),
                "high": round(self.monthly_estimate_high_usd, 2),
                "assumptions": {
                    "requests_per_day_low": self.assumed_requests_per_day_low,
                    "requests_per_day_high": self.assumed_requests_per_day_high,
                }
            },
            "models": {
                "llm": self.model_used,
                "embedding": self.embedding_model_used,
            },
            "pricing_date": self.pricing_date,
            "disclaimer": self.disclaimer,
        }


# =============================================================================
# Token Pricing (Informational, may be outdated)
# =============================================================================

TOKEN_PRICING = {
    # OpenAI pricing as of late 2024 (per 1K tokens)
    # IMPORTANT: These prices may be outdated. Check OpenAI pricing page.
    "gpt-4o": {
        "input": 0.005,      # $5.00 per 1M input tokens
        "output": 0.015,     # $15.00 per 1M output tokens
    },
    "gpt-4o-mini": {
        "input": 0.00015,    # $0.15 per 1M input tokens
        "output": 0.0006,    # $0.60 per 1M output tokens
    },
    "gpt-4-turbo": {
        "input": 0.01,       # $10.00 per 1M input tokens
        "output": 0.03,      # $30.00 per 1M output tokens
    },
    "gpt-3.5-turbo": {
        "input": 0.0005,     # $0.50 per 1M input tokens
        "output": 0.0015,    # $1.50 per 1M output tokens
    },
    # Embedding models
    "text-embedding-3-small": {
        "input": 0.00002,    # $0.02 per 1M tokens
        "output": 0.0,
    },
    "text-embedding-3-large": {
        "input": 0.00013,    # $0.13 per 1M tokens
        "output": 0.0,
    },
    "text-embedding-ada-002": {
        "input": 0.0001,     # $0.10 per 1M tokens
        "output": 0.0,
    },
}

# Default token estimates for different operation types
DEFAULT_TOKEN_ESTIMATES = {
    "chat": {
        "input_tokens": 500,   # System prompt + user message
        "output_tokens": 300,  # Response
    },
    "rag": {
        "input_tokens": 1500,  # System prompt + context + query
        "output_tokens": 500,  # Response with citations
    },
    "embedding": {
        "input_tokens": 200,   # Average chunk size
        "output_tokens": 0,
    },
}


def estimate_costs(cps_data: Dict[str, Any]) -> CostEstimate:
    """
    Estimate token usage and costs based on CPS configuration.
    
    DISCLAIMER: All estimates are informational and non-guaranteed.
    Actual costs depend on many factors not accounted for here.
    
    Args:
        cps_data: CPS model as dictionary
        
    Returns:
        CostEstimate with projected costs and mandatory disclaimer
    """
    features = cps_data.get("features", {})
    model = cps_data.get("model") or "gpt-4o"
    embedding_model = cps_data.get("embedding_model") or "text-embedding-3-small"
    
    # Get pricing (fallback to gpt-4o if model not found)
    model_pricing = TOKEN_PRICING.get(model, TOKEN_PRICING.get("gpt-4o"))
    embedding_pricing = TOKEN_PRICING.get(
        embedding_model, TOKEN_PRICING.get("text-embedding-3-small")
    )
    
    estimate = CostEstimate(
        model_used=model,
        embedding_model_used=embedding_model,
    )
    
    # Calculate chat costs
    if features.get("chat"):
        chat_estimates = DEFAULT_TOKEN_ESTIMATES["chat"]
        estimate.tokens_per_chat_request = (
            chat_estimates["input_tokens"] + chat_estimates["output_tokens"]
        )
        
        input_cost = (chat_estimates["input_tokens"] / 1000) * model_pricing["input"]
        output_cost = (chat_estimates["output_tokens"] / 1000) * model_pricing["output"]
        estimate.estimated_cost_per_chat_request_usd = input_cost + output_cost
    
    # Calculate RAG costs
    if features.get("rag"):
        rag_estimates = DEFAULT_TOKEN_ESTIMATES["rag"]
        estimate.tokens_per_rag_query = (
            rag_estimates["input_tokens"] + rag_estimates["output_tokens"]
        )
        
        input_cost = (rag_estimates["input_tokens"] / 1000) * model_pricing["input"]
        output_cost = (rag_estimates["output_tokens"] / 1000) * model_pricing["output"]
        estimate.estimated_cost_per_rag_query_usd = input_cost + output_cost
    
    # Calculate embedding costs
    if features.get("embeddings"):
        embed_estimates = DEFAULT_TOKEN_ESTIMATES["embedding"]
        estimate.tokens_per_embedding = embed_estimates["input_tokens"]
        
        estimate.estimated_cost_per_embedding_usd = (
            (embed_estimates["input_tokens"] / 1000) * embedding_pricing["input"]
        )
    
    # Calculate monthly projections
    # Assumptions for low/high usage scenarios
    requests_per_day_low = 100
    requests_per_day_high = 10000
    days_per_month = 30
    
    daily_cost = 0.0
    if features.get("chat"):
        daily_cost += estimate.estimated_cost_per_chat_request_usd
    if features.get("rag"):
        daily_cost += estimate.estimated_cost_per_rag_query_usd
    if features.get("embeddings"):
        # Assume 10 embeddings per request
        daily_cost += estimate.estimated_cost_per_embedding_usd * 10
    
    estimate.monthly_estimate_low_usd = daily_cost * requests_per_day_low * days_per_month
    estimate.monthly_estimate_high_usd = daily_cost * requests_per_day_high * days_per_month
    estimate.assumed_requests_per_day_low = requests_per_day_low
    estimate.assumed_requests_per_day_high = requests_per_day_high
    
    return estimate


def get_pricing_info() -> Dict[str, Any]:
    """
    Get current token pricing information.
    
    Returns:
        Dictionary with pricing info and disclaimer
    """
    return {
        "pricing": TOKEN_PRICING,
        "disclaimer": (
            "These prices are informational only and may be outdated. "
            "Check your LLM provider's pricing page for current rates."
        ),
        "last_updated": "2024-01",  # Update this when pricing changes
    }
