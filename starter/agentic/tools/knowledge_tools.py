"""
Knowledge Base Tools for UDA-Hub
Provides tools for searching and retrieving knowledge base articles
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.tools import tool

# Add parent directories to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from data.models import udahub
from agentic.tools.db_manager import get_db_manager


def calculate_relevance_score(query: str, article: Any) -> float:
    """
    Calculate relevance score between query and article
    Uses simple keyword matching approach
    
    Args:
        query: User's question
        article: Knowledge article object
        
    Returns:
        Relevance score between 0 and 1
    """
    query_lower = query.lower()
    title_lower = article.title.lower()
    content_lower = article.content.lower()
    tags_lower = article.tags.lower() if article.tags else ""
    
    score = 0.0
    query_words = set(query_lower.split())
    
    # Exact title match gets high score
    if query_lower in title_lower:
        score += 0.5
    
    # Tag matches are important
    if article.tags:
        tag_words = set(tags_lower.replace(',', ' ').split())
        tag_matches = len(query_words.intersection(tag_words))
        score += tag_matches * 0.15
    
    # Content keyword matches
    content_matches = sum(1 for word in query_words if word in content_lower)
    score += content_matches * 0.08
    
    # Title keyword matches
    title_matches = sum(1 for word in query_words if word in title_lower)
    score += title_matches * 0.2
    
    # Cap at 1.0
    return min(score, 1.0)


@tool
def search_knowledge_base(query: str, tags: str = "", account_id: str = "cultpass") -> str:
    """
    Search the knowledge base for relevant articles.
    
    This tool searches through support articles to find information that can help
    resolve customer issues. Returns articles with relevance scores.
    
    Args:
        query: The customer's question or issue description (e.g., "how to login", "cancel subscription")
        tags: Optional comma-separated tags to filter by (e.g., "login,password" or "billing,refund")
        account_id: Account identifier (default: "cultpass")
        
    Returns:
        JSON string containing:
        - articles: List of relevant articles with title, content, and relevance score
        - confidence: Overall confidence score (0-1)
        - should_escalate: Boolean indicating if escalation is recommended
        
    Examples:
        search_knowledge_base(query="I can't log in")
        search_knowledge_base(query="refund request", tags="billing,refund")
    """
    try:
        db_manager = get_db_manager()
        
        with db_manager.get_udahub_session() as session:
            # Query all knowledge articles for the account
            articles_query = session.query(udahub.Knowledge).filter_by(account_id=account_id)
            
            # Filter by tags if provided
            if tags:
                tag_list = [t.strip().lower() for t in tags.split(',')]
                articles_query = articles_query.filter(
                    udahub.Knowledge.tags.ilike(f"%{tag_list[0]}%")
                )
            
            all_articles = articles_query.all()
            
            if not all_articles:
                return json.dumps({
                    "articles": [],
                    "confidence": 0.0,
                    "should_escalate": True,
                    "message": "No knowledge base articles found for this account."
                })
            
            # Calculate relevance scores
            scored_articles = []
            for article in all_articles:
                score = calculate_relevance_score(query, article)
                if score > 0.1:  # Only include articles with some relevance
                    scored_articles.append({
                        "article_id": article.article_id,
                        "title": article.title,
                        "content": article.content,
                        "tags": article.tags,
                        "relevance_score": round(score, 3)
                    })
            
            # Sort by relevance score
            scored_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Take top 3 articles
            top_articles = scored_articles[:3]
            
            # Calculate overall confidence (based on best match)
            confidence = top_articles[0]['relevance_score'] if top_articles else 0.0
            
            # Determine if escalation is needed
            should_escalate = confidence < 0.5 or len(top_articles) == 0
            
            result = {
                "articles": top_articles,
                "confidence": confidence,
                "should_escalate": should_escalate,
                "message": f"Found {len(top_articles)} relevant article(s)" if top_articles else "No relevant articles found"
            }
            
            return json.dumps(result, indent=2)
            
    except Exception as e:
        return json.dumps({
            "error": f"Error searching knowledge base: {str(e)}",
            "articles": [],
            "confidence": 0.0,
            "should_escalate": True
        })


@tool
def get_article_by_id(article_id: str) -> str:
    """
    Retrieve a specific knowledge base article by its ID.
    
    Args:
        article_id: The unique article identifier
        
    Returns:
        JSON string with article details or error message
    """
    try:
        db_manager = get_db_manager()
        
        with db_manager.get_udahub_session() as session:
            article = session.query(udahub.Knowledge).filter_by(article_id=article_id).first()
            
            if not article:
                return json.dumps({
                    "error": f"Article with ID {article_id} not found",
                    "found": False
                })
            
            return json.dumps({
                "found": True,
                "article_id": article.article_id,
                "title": article.title,
                "content": article.content,
                "tags": article.tags,
                "created_at": str(article.created_at)
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "error": f"Error retrieving article: {str(e)}",
            "found": False
        })


@tool
def list_knowledge_categories(account_id: str = "cultpass") -> str:
    """
    List all available knowledge base categories (extracted from tags).
    
    Args:
        account_id: Account identifier (default: "cultpass")
        
    Returns:
        JSON string with list of categories and article counts
    """
    try:
        db_manager = get_db_manager()
        
        with db_manager.get_udahub_session() as session:
            articles = session.query(udahub.Knowledge).filter_by(account_id=account_id).all()
            
            # Extract and count tags
            tag_counts = {}
            for article in articles:
                if article.tags:
                    tags = [t.strip() for t in article.tags.split(',')]
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # Sort by count
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            
            return json.dumps({
                "total_articles": len(articles),
                "categories": [
                    {"category": tag, "count": count}
                    for tag, count in sorted_tags
                ]
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "error": f"Error listing categories: {str(e)}",
            "categories": []
        })

