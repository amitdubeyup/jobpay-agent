import asyncio
from typing import List, Dict, Any, Tuple
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
import logging

from app.core.config import settings
from app.models.job import Job
from app.models.user import Candidate
from app.schemas.job import JobMatchCreate
from app.services.job_service import JobMatchService
from app.services.user_service import CandidateService

logger = logging.getLogger(__name__)


class AIMatchingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name="gpt-3.5-turbo",
            temperature=0.3
        )
        self.job_match_service = JobMatchService(db)
        self.candidate_service = CandidateService(db)
        
        # Scoring weights
        self.weights = {
            'skills': 0.4,
            'location': 0.2,
            'experience': 0.25,
            'salary': 0.15
        }
    
    async def find_matching_candidates(self, job: Job, top_k: int = 20) -> List[JobMatchCreate]:
        """Find and score candidates for a job using AI."""
        try:
            # Get all potential candidates
            candidates = await self.candidate_service.search_candidates(limit=1000)
            
            if not candidates:
                logger.info(f"No candidates found for job {job.id}")
                return []
            
            # Calculate matches
            matches = []
            
            for candidate in candidates:
                match_score = await self._calculate_match_score(job, candidate)
                
                if match_score['overall_score'] >= 0.3:  # Minimum threshold
                    match = JobMatchCreate(
                        job_id=job.id,
                        candidate_id=candidate.id,
                        overall_score=match_score['overall_score'],
                        skills_score=match_score['skills_score'],
                        location_score=match_score['location_score'],
                        experience_score=match_score['experience_score'],
                        salary_score=match_score['salary_score'],
                        matching_skills=match_score['matching_skills'],
                        missing_skills=match_score['missing_skills'],
                        match_reasons=match_score['match_reasons']
                    )
                    matches.append(match)
            
            # Sort by overall score and return top K
            matches.sort(key=lambda x: x.overall_score, reverse=True)
            return matches[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding matching candidates for job {job.id}: {str(e)}")
            return []
    
    async def _calculate_match_score(self, job: Job, candidate: Candidate) -> Dict[str, Any]:
        """Calculate comprehensive match score between job and candidate."""
        
        # Skills matching using semantic similarity
        skills_score, matching_skills, missing_skills = await self._calculate_skills_score(
            job.required_skills, candidate.skills
        )
        
        # Location matching
        location_score = self._calculate_location_score(job.location, candidate.location)
        
        # Experience matching
        experience_score = self._calculate_experience_score(
            job.experience_min, job.experience_max, candidate.experience_years
        )
        
        # Salary matching
        salary_score = self._calculate_salary_score(
            job.salary_min, job.salary_max, candidate.preferences
        )
        
        # Calculate overall weighted score
        overall_score = (
            skills_score * self.weights['skills'] +
            location_score * self.weights['location'] +
            experience_score * self.weights['experience'] +
            salary_score * self.weights['salary']
        )
        
        # Generate match reasons using LLM
        match_reasons = await self._generate_match_reasons(job, candidate, {
            'skills_score': skills_score,
            'location_score': location_score,
            'experience_score': experience_score,
            'salary_score': salary_score
        })
        
        return {
            'overall_score': round(overall_score, 3),
            'skills_score': round(skills_score, 3),
            'location_score': round(location_score, 3),
            'experience_score': round(experience_score, 3),
            'salary_score': round(salary_score, 3),
            'matching_skills': matching_skills,
            'missing_skills': missing_skills,
            'match_reasons': match_reasons
        }
    
    async def _calculate_skills_score(
        self, 
        required_skills: List[str], 
        candidate_skills: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """Calculate skills matching score using semantic similarity."""
        
        if not required_skills:
            return 1.0, candidate_skills, []
        
        if not candidate_skills:
            return 0.0, [], required_skills
        
        try:
            # Create embeddings for skills
            required_texts = [f"skill: {skill}" for skill in required_skills]
            candidate_texts = [f"skill: {skill}" for skill in candidate_skills]
            
            required_embeddings = await self.embeddings.aembed_documents(required_texts)
            candidate_embeddings = await self.embeddings.aembed_documents(candidate_texts)
            
            # Calculate similarity matrix
            required_arr = np.array(required_embeddings)
            candidate_arr = np.array(candidate_embeddings)
            
            # Cosine similarity
            similarity_matrix = np.dot(required_arr, candidate_arr.T) / (
                np.linalg.norm(required_arr, axis=1, keepdims=True) *
                np.linalg.norm(candidate_arr, axis=1, keepdims=True).T
            )
            
            # Find best matches for each required skill
            matching_skills = []
            missing_skills = []
            skill_scores = []
            
            for i, req_skill in enumerate(required_skills):
                max_similarity = np.max(similarity_matrix[i])
                best_match_idx = np.argmax(similarity_matrix[i])
                
                if max_similarity >= 0.7:  # High similarity threshold
                    matching_skills.append(candidate_skills[best_match_idx])
                    skill_scores.append(max_similarity)
                elif max_similarity >= 0.5:  # Medium similarity threshold
                    matching_skills.append(candidate_skills[best_match_idx])
                    skill_scores.append(max_similarity * 0.8)  # Reduce score for partial match
                else:
                    missing_skills.append(req_skill)
                    skill_scores.append(0.0)
            
            # Calculate overall skills score
            if skill_scores:
                overall_score = np.mean(skill_scores)
            else:
                overall_score = 0.0
            
            return overall_score, matching_skills, missing_skills
            
        except Exception as e:
            logger.error(f"Error calculating skills score: {str(e)}")
            # Fallback to exact matching
            matching = set(required_skills) & set(candidate_skills)
            missing = set(required_skills) - set(candidate_skills)
            score = len(matching) / len(required_skills) if required_skills else 1.0
            
            return score, list(matching), list(missing)
    
    def _calculate_location_score(self, job_location: str, candidate_location: str) -> float:
        """Calculate location matching score."""
        if not job_location or not candidate_location:
            return 0.5  # Neutral score for missing location data
        
        job_loc = job_location.lower().strip()
        candidate_loc = candidate_location.lower().strip()
        
        # Exact match
        if job_loc == candidate_loc:
            return 1.0
        
        # Check if one contains the other (city vs state/country)
        if job_loc in candidate_loc or candidate_loc in job_loc:
            return 0.8
        
        # Check for common location keywords
        job_words = set(job_loc.split())
        candidate_words = set(candidate_loc.split())
        common_words = job_words & candidate_words
        
        if common_words:
            return 0.6
        
        # No match
        return 0.2
    
    def _calculate_experience_score(
        self, 
        job_exp_min: int, 
        job_exp_max: int, 
        candidate_exp: int
    ) -> float:
        """Calculate experience matching score."""
        if candidate_exp is None:
            return 0.5  # Neutral score for missing experience
        
        if job_exp_min is None and job_exp_max is None:
            return 1.0  # No experience requirements
        
        if job_exp_min is None:
            job_exp_min = 0
        
        if job_exp_max is None:
            job_exp_max = float('inf')
        
        # Candidate meets requirements
        if job_exp_min <= candidate_exp <= job_exp_max:
            return 1.0
        
        # Candidate is overqualified
        if candidate_exp > job_exp_max:
            # Penalize based on how overqualified
            excess = candidate_exp - job_exp_max
            penalty = min(excess * 0.1, 0.3)  # Max 30% penalty
            return max(0.7, 1.0 - penalty)
        
        # Candidate is underqualified
        if candidate_exp < job_exp_min:
            # Penalize based on experience gap
            gap = job_exp_min - candidate_exp
            penalty = min(gap * 0.15, 0.8)  # Max 80% penalty
            return max(0.1, 1.0 - penalty)
        
        return 0.5
    
    def _calculate_salary_score(
        self, 
        job_salary_min: float, 
        job_salary_max: float, 
        candidate_preferences: Dict[str, Any]
    ) -> float:
        """Calculate salary matching score."""
        candidate_salary_min = candidate_preferences.get('salary_min')
        candidate_salary_max = candidate_preferences.get('salary_max')
        
        # No salary data
        if not any([job_salary_min, job_salary_max, candidate_salary_min, candidate_salary_max]):
            return 0.5
        
        # No candidate preferences
        if not candidate_salary_min and not candidate_salary_max:
            return 0.7  # Assume candidate is flexible
        
        # No job salary range
        if not job_salary_min and not job_salary_max:
            return 0.5
        
        # Set defaults
        if job_salary_min is None:
            job_salary_min = 0
        if job_salary_max is None:
            job_salary_max = float('inf')
        if candidate_salary_min is None:
            candidate_salary_min = 0
        if candidate_salary_max is None:
            candidate_salary_max = float('inf')
        
        # Check overlap
        overlap_start = max(job_salary_min, candidate_salary_min)
        overlap_end = min(job_salary_max, candidate_salary_max)
        
        if overlap_start <= overlap_end:
            # Calculate overlap percentage
            job_range = job_salary_max - job_salary_min
            candidate_range = candidate_salary_max - candidate_salary_min
            overlap_size = overlap_end - overlap_start
            
            if job_range > 0 and candidate_range > 0:
                job_overlap_pct = overlap_size / job_range
                candidate_overlap_pct = overlap_size / candidate_range
                return min(job_overlap_pct, candidate_overlap_pct, 1.0)
            else:
                return 1.0
        
        # No overlap - calculate how far apart they are
        gap = min(
            abs(job_salary_min - candidate_salary_max),
            abs(candidate_salary_min - job_salary_max)
        )
        
        # Normalize gap (assuming average range is around 50k)
        normalized_gap = gap / 50000
        penalty = min(normalized_gap * 0.2, 0.7)  # Max 70% penalty
        
        return max(0.1, 1.0 - penalty)
    
    async def _generate_match_reasons(
        self, 
        job: Job, 
        candidate: Candidate, 
        scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate human-readable match reasons using LLM."""
        
        prompt_template = PromptTemplate(
            input_variables=[
                "job_title", "job_skills", "job_location", "job_experience",
                "candidate_skills", "candidate_location", "candidate_experience",
                "skills_score", "location_score", "experience_score", "salary_score"
            ],
            template="""
            Analyze why this candidate matches this job and provide concise reasons:
            
            Job: {job_title}
            Required Skills: {job_skills}
            Location: {job_location}
            Experience: {job_experience} years
            
            Candidate:
            Skills: {candidate_skills}
            Location: {candidate_location}
            Experience: {candidate_experience} years
            
            Scores:
            - Skills: {skills_score}
            - Location: {location_score}
            - Experience: {experience_score}
            - Salary: {salary_score}
            
            Provide a JSON response with:
            1. "strengths": List of 2-3 key strengths
            2. "concerns": List of 1-2 potential concerns
            3. "summary": One sentence summary
            
            Keep it concise and professional.
            """
        )
        
        try:
            chain = LLMChain(llm=self.llm, prompt=prompt_template)
            
            response = await chain.arun(
                job_title=job.title,
                job_skills=", ".join(job.required_skills),
                job_location=job.location or "Remote/Flexible",
                job_experience=f"{job.experience_min or 0}-{job.experience_max or 'Any'}",
                candidate_skills=", ".join(candidate.skills or []),
                candidate_location=candidate.location or "Not specified",
                candidate_experience=candidate.experience_years or "Not specified",
                skills_score=scores['skills_score'],
                location_score=scores['location_score'],
                experience_score=scores['experience_score'],
                salary_score=scores['salary_score']
            )
            
            # Try to parse JSON response
            import json
            try:
                return json.loads(response)
            except:
                # Fallback to basic reasons
                return {
                    "summary": f"Candidate has {scores['skills_score']:.1%} skills match for {job.title}",
                    "strengths": ["Skills alignment", "Experience level"],
                    "concerns": ["Location fit"] if scores['location_score'] < 0.7 else []
                }
                
        except Exception as e:
            logger.error(f"Error generating match reasons: {str(e)}")
            return {
                "summary": f"Good overall match with {max(scores.values()):.1%} compatibility",
                "strengths": ["Professional fit"],
                "concerns": []
            }
