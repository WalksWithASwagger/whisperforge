"""
Research Enrichment Module for WhisperForge
Extracts entities from content and generates supporting research links
"""

import logging
import re
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from .utils import get_openai_client

logger = logging.getLogger(__name__)

def track_token_usage(operation: str, total_tokens: int, prompt_tokens: int, completion_tokens: int):
    """Simple token usage tracking fallback"""
    logger.info(f"Token usage - {operation}: {total_tokens} total ({prompt_tokens} prompt + {completion_tokens} completion)")

class ResearchEnricher:
    """Handles research enrichment for pipeline content"""
    
    def __init__(self):
        self.provider = "openai"  # Hard-coded as specified
        self.max_entities = 5  # Configurable limit
        self.max_links_per_entity = 3  # Max links per entity
        
    def extract_entities(self, wisdom: str, transcript: str, ai_model: str = "gpt-4") -> List[Dict[str, Any]]:
        """Extract interesting entities from wisdom and transcript content"""
        try:
            logger.info("Starting entity extraction from content")
            
            # Prepare content for analysis
            content = f"WISDOM NOTES:\n{wisdom}\n\nTRANSCRIPT:\n{transcript[:2000]}..."
            
            entity_extraction_prompt = """Analyze the provided content and extract the most interesting proper nouns and "big-idea" phrases that would benefit from supporting research links.

Focus on:
- People (names, experts, thought leaders)
- Organizations (companies, institutions, movements) 
- Projects (initiatives, studies, technologies)
- Methods (frameworks, methodologies, processes)
- Theories (concepts, philosophies, scientific theories)
- Technologies (tools, platforms, innovations)

Return EXACTLY 3-5 entities in this JSON format:
{
  "entities": [
    {
      "name": "Entity Name",
      "type": "person|organization|project|method|theory|technology", 
      "context": "Brief context from the content explaining why this entity is mentioned",
      "search_terms": ["term1", "term2", "term3"]
    }
  ]
}

Be selective - only include entities that would genuinely benefit from research links to enhance understanding."""

            client = get_openai_client()
            if not client:
                logger.error("OpenAI client not available for entity extraction")
                return []
            
            response = client.chat.completions.create(
                model=ai_model,
                messages=[
                    {"role": "system", "content": entity_extraction_prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            # Track token usage
            usage = response.usage
            track_token_usage("research_entity_extraction", usage.total_tokens, usage.prompt_tokens, usage.completion_tokens)
            
            # Parse response
            entities_data = self._parse_entities_response(response.choices[0].message.content)
            logger.info(f"Extracted {len(entities_data)} entities successfully")
            
            return entities_data
            
        except Exception as e:
            logger.exception(f"Error in entity extraction: {e}")
            return []
    
    def _parse_entities_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse the entities response from AI model"""
        try:
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                return data.get("entities", [])
            
            logger.warning("Could not parse JSON from entities response")
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in entities response: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing entities response: {e}")
            return []
    
    def generate_research_links(self, entities: List[Dict[str, Any]], ai_model: str = "gpt-4") -> List[Dict[str, Any]]:
        """Generate research links for extracted entities"""
        try:
            logger.info(f"Generating research links for {len(entities)} entities")
            
            enriched_entities = []
            
            for entity in entities:
                try:
                    entity_research = self._research_single_entity(entity, ai_model)
                    if entity_research:
                        enriched_entities.append(entity_research)
                    
                    # Rate limiting between requests
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error researching entity {entity.get('name', 'unknown')}: {e}")
                    # Continue with other entities
                    continue
            
            logger.info(f"Successfully enriched {len(enriched_entities)} entities with research")
            return enriched_entities
            
        except Exception as e:
            logger.exception(f"Error in research link generation: {e}")
            return []
    
    def _research_single_entity(self, entity: Dict[str, Any], ai_model: str) -> Optional[Dict[str, Any]]:
        """Research a single entity and generate supporting links"""
        try:
            entity_name = entity.get("name", "")
            entity_type = entity.get("type", "")
            entity_context = entity.get("context", "")
            search_terms = entity.get("search_terms", [entity_name])
            
            research_prompt = f"""You are a research assistant. Generate high-quality, authoritative links for this entity.

ENTITY: {entity_name}
TYPE: {entity_type}
CONTEXT: {entity_context}
SEARCH_TERMS: {', '.join(search_terms)}

Provide:
1. A concise "why this matters" explanation (2-3 sentences max)
2. Up to 3 high-quality links (official websites, authoritative articles, academic sources)
3. Mark ONE link as the "gem" - the single best resource

Return in this JSON format:
{{
  "name": "{entity_name}",
  "type": "{entity_type}",
  "context": "{entity_context}",
  "why_matters": "Brief explanation of why this entity is significant and worth exploring further",
  "links": [
    {{
      "title": "Link Title",
      "url": "https://example.com",
      "description": "Brief description of what this link provides",
      "is_gem": true
    }},
    {{
      "title": "Link Title 2", 
      "url": "https://example2.com",
      "description": "Brief description",
      "is_gem": false
    }}
  ]
}}

Focus on REAL, authoritative sources. If you cannot suggest specific URLs, provide realistic examples of what types of sources would be valuable."""

            client = get_openai_client()
            if not client:
                logger.error("OpenAI client not available for research generation")
                return None
            
            response = client.chat.completions.create(
                model=ai_model,
                messages=[
                    {"role": "system", "content": research_prompt}
                ],
                max_tokens=800,
                temperature=0.4
            )
            
            # Track token usage
            usage = response.usage
            track_token_usage("research_link_generation", usage.total_tokens, usage.prompt_tokens, usage.completion_tokens)
            
            # Parse response
            research_data = self._parse_research_response(response.choices[0].message.content)
            
            if research_data:
                logger.info(f"Successfully researched entity: {entity_name}")
                return research_data
            else:
                logger.warning(f"Failed to parse research data for entity: {entity_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error researching single entity {entity.get('name', 'unknown')}: {e}")
            return None
    
    def _parse_research_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the research response from AI model"""
        try:
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                
                # Validate required fields
                if data.get('name') and data.get('why_matters') and data.get('links'):
                    return data
            
            logger.warning("Could not parse valid JSON from research response")
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in research response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing research response: {e}")
            return None
    
    def enrich_content(self, wisdom: str, transcript: str, ai_model: str = "gpt-4") -> Dict[str, Any]:
        """Main method to enrich content with research links"""
        try:
            logger.info("Starting research enrichment process")
            start_time = time.time()
            
            # Step 1: Extract entities
            entities = self.extract_entities(wisdom, transcript, ai_model)
            if not entities:
                logger.warning("No entities extracted - returning empty research")
                return {
                    "entities": [],
                    "total_entities": 0,
                    "processing_time": time.time() - start_time,
                    "status": "no_entities_found"
                }
            
            # Step 2: Generate research links
            enriched_entities = self.generate_research_links(entities, ai_model)
            
            processing_time = time.time() - start_time
            
            result = {
                "entities": enriched_entities,
                "total_entities": len(enriched_entities),
                "processing_time": processing_time,
                "status": "success" if enriched_entities else "failed"
            }
            
            logger.info(f"Research enrichment completed in {processing_time:.2f}s with {len(enriched_entities)} enriched entities")
            return result
            
        except Exception as e:
            logger.exception(f"Error in research enrichment: {e}")
            return {
                "entities": [],
                "total_entities": 0,
                "processing_time": time.time() - start_time if 'start_time' in locals() else 0,
                "status": "error",
                "error_message": str(e)
            }


def generate_research_enrichment(wisdom: str, transcript: str, ai_provider: str, ai_model: str, enabled: bool = True) -> Dict[str, Any]:
    """Main function to generate research enrichment - follows existing content generation patterns"""
    
    if not enabled:
        logger.info("Research enrichment disabled - skipping")
        return {
            "entities": [],
            "total_entities": 0,
            "processing_time": 0,
            "status": "disabled"
        }
    
    if ai_provider.lower() != "openai":
        logger.warning(f"Research enrichment only supports OpenAI provider, got: {ai_provider}")
        return {
            "entities": [],
            "total_entities": 0,
            "processing_time": 0,
            "status": "unsupported_provider",
            "error_message": f"Research enrichment requires OpenAI provider, got: {ai_provider}"
        }
    
    try:
        enricher = ResearchEnricher()
        return enricher.enrich_content(wisdom, transcript, ai_model)
        
    except Exception as e:
        logger.exception(f"Error in research enrichment generation: {e}")
        return {
            "entities": [],
            "total_entities": 0,
            "processing_time": 0,
            "status": "error",
            "error_message": str(e)
        } 