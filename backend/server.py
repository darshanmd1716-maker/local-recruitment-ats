from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import json
import re
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import aiofiles
import tempfile
import shutil

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Ensure upload directories exist
UPLOAD_DIR = ROOT_DIR / "uploads"
RECRUITMENT_DIR = ROOT_DIR / "Recruitment"
EXPORT_DIR = ROOT_DIR / "exports"
UPLOAD_DIR.mkdir(exist_ok=True)
RECRUITMENT_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)

# LLM API Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== Models ==============

class JobDescription(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    raw_text: str
    required_skills: List[str] = []
    experience_required: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class JobDescriptionCreate(BaseModel):
    title: str
    raw_text: str

class Candidate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    name: str
    mobile: Optional[str] = None
    email: Optional[str] = None
    skills: List[str] = []
    experience: Optional[str] = None
    current_role: Optional[str] = None
    match_percentage: float = 0.0
    category: str = "Rejected_Future"  # Shortlisted, Hold, Rejected_Future
    original_filename: str = ""
    current_ctc: Optional[str] = None
    expected_ctc: Optional[str] = None
    notice_period: Optional[str] = None
    negotiable: Optional[str] = None
    candidate_response: Optional[str] = "Pending"
    remarks: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProcessingResult(BaseModel):
    job_id: str
    total_processed: int
    shortlisted: int
    hold: int
    rejected_future: int
    top_candidates: List[Dict[str, Any]]
    folder_created: bool
    excel_path: Optional[str] = None
    duplicates_found: List[Dict[str, Any]] = []

class DuplicateCandidate(BaseModel):
    existing_candidate: Dict[str, Any]
    new_candidate: Dict[str, Any]
    match_type: str  # "email", "mobile", "both"
    existing_job_title: Optional[str] = None

class CompareRequest(BaseModel):
    candidate_ids: List[str]

# ============== Helper Functions ==============

def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """Normalize phone number for comparison"""
    if not phone:
        return None
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    # Return last 10 digits (standard mobile number)
    return digits[-10:] if len(digits) >= 10 else digits if digits else None

def normalize_email(email: Optional[str]) -> Optional[str]:
    """Normalize email for comparison"""
    if not email:
        return None
    return email.lower().strip()

async def check_duplicate_candidate(email: Optional[str], mobile: Optional[str], exclude_job_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Check if a candidate with same email or mobile exists"""
    normalized_email = normalize_email(email)
    normalized_mobile = normalize_phone(mobile)
    
    if not normalized_email and not normalized_mobile:
        return None
    
    # Build query for duplicates
    or_conditions = []
    if normalized_email:
        or_conditions.append({"email": {"$regex": f"^{re.escape(normalized_email)}$", "$options": "i"}})
    if normalized_mobile:
        # Match last 10 digits of phone
        or_conditions.append({"mobile": {"$regex": f"{normalized_mobile}$"}})
    
    if not or_conditions:
        return None
    
    query = {"$or": or_conditions}
    if exclude_job_id:
        query["job_id"] = {"$ne": exclude_job_id}
    
    existing = await db.candidates.find_one(query, {"_id": 0})
    if existing:
        # Determine match type
        existing_email = normalize_email(existing.get('email'))
        existing_mobile = normalize_phone(existing.get('mobile'))
        
        match_type = []
        if normalized_email and existing_email and normalized_email == existing_email:
            match_type.append("email")
        if normalized_mobile and existing_mobile and normalized_mobile == existing_mobile:
            match_type.append("mobile")
        
        existing['match_type'] = " & ".join(match_type) if match_type else "unknown"
        return existing
    
    return None

async def parse_jd_with_ai(jd_text: str) -> Dict[str, Any]:
    """Use AI to extract structured data from JD"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"jd-parse-{uuid.uuid4()}",
            system_message="You are an expert IT recruiter. Extract structured information from job descriptions."
        ).with_model("gemini", "gemini-2.5-flash")
        
        prompt = f"""Analyze this job description and extract the following information in JSON format:
{{
    "title": "Job title",
    "required_skills": ["skill1", "skill2", ...],
    "experience_required": "X years",
    "location": "Location or Remote"
}}

Job Description:
{jd_text}

Return ONLY valid JSON, no other text."""

        response = await chat.send_message(UserMessage(text=prompt))
        
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group())
        return {"title": "Unknown", "required_skills": [], "experience_required": None, "location": None}
    except Exception as e:
        logger.error(f"Error parsing JD with AI: {e}")
        return {"title": "Unknown", "required_skills": [], "experience_required": None, "location": None}

async def parse_resume_with_ai(file_path: str, file_content: bytes, filename: str) -> Dict[str, Any]:
    """Use AI to extract structured data from resume"""
    try:
        # Determine mime type
        ext = Path(filename).suffix.lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain'
        }
        mime_type = mime_types.get(ext, 'application/octet-stream')
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"resume-parse-{uuid.uuid4()}",
            system_message="You are an expert IT recruiter. Extract candidate information from resumes accurately."
        ).with_model("gemini", "gemini-2.5-flash")
        
        file_attachment = FileContentWithMimeType(
            file_path=file_path,
            mime_type=mime_type
        )
        
        prompt = """Extract the following information from this resume in JSON format:
{
    "name": "Full name of candidate",
    "mobile": "Phone number",
    "email": "Email address",
    "skills": ["skill1", "skill2", ...],
    "experience": "Total years of experience",
    "current_role": "Current or last job title"
}

Return ONLY valid JSON, no other text. If information is not found, use null."""

        response = await chat.send_message(UserMessage(
            text=prompt,
            file_contents=[file_attachment]
        ))
        
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group())
        return {"name": "Unknown", "mobile": None, "email": None, "skills": [], "experience": None, "current_role": None}
    except Exception as e:
        logger.error(f"Error parsing resume with AI: {e}")
        return {"name": "Unknown", "mobile": None, "email": None, "skills": [], "experience": None, "current_role": None}

async def calculate_match_score(jd_skills: List[str], jd_text: str, candidate_data: Dict[str, Any]) -> float:
    """Use AI for semantic matching between JD and resume"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"match-{uuid.uuid4()}",
            system_message="You are an expert IT recruiter. Evaluate candidate-job fit accurately."
        ).with_model("gemini", "gemini-2.5-flash")
        
        prompt = f"""As an IT recruiter, evaluate this candidate's match for the job.

Job Requirements:
- Required Skills: {', '.join(jd_skills)}
- Job Description: {jd_text[:1000]}

Candidate Profile:
- Name: {candidate_data.get('name', 'Unknown')}
- Skills: {', '.join(candidate_data.get('skills', []))}
- Experience: {candidate_data.get('experience', 'Unknown')}
- Current Role: {candidate_data.get('current_role', 'Unknown')}

Return ONLY a number between 0 and 100 representing the match percentage.
Consider:
- Skill overlap (40% weight)
- Experience relevance (30% weight)
- Role alignment (30% weight)

Return only the number, nothing else."""

        response = await chat.send_message(UserMessage(text=prompt))
        
        # Extract number from response
        numbers = re.findall(r'\d+(?:\.\d+)?', response)
        if numbers:
            score = float(numbers[0])
            return min(100, max(0, score))
        return 50.0
    except Exception as e:
        logger.error(f"Error calculating match score: {e}")
        # Fallback to keyword matching
        if not jd_skills:
            return 50.0
        candidate_skills = set(s.lower() for s in candidate_data.get('skills', []))
        jd_skills_lower = set(s.lower() for s in jd_skills)
        if not jd_skills_lower:
            return 50.0
        overlap = len(candidate_skills.intersection(jd_skills_lower))
        return min(100, (overlap / len(jd_skills_lower)) * 100)

def categorize_candidate(match_percentage: float) -> str:
    """Categorize candidate based on match percentage"""
    if match_percentage >= 75:
        return "Shortlisted"
    elif match_percentage >= 50:
        return "Hold"
    else:
        return "Rejected_Future"

def create_recruitment_folders(job_title: str) -> Dict[str, Path]:
    """Create folder structure for a job"""
    # Clean job title for folder name
    clean_title = re.sub(r'[^\w\s-]', '', job_title).strip().replace(' ', '_')
    job_folder = RECRUITMENT_DIR / clean_title
    
    folders = {
        "root": job_folder,
        "shortlisted": job_folder / "Shortlisted",
        "hold": job_folder / "Hold",
        "rejected_future": job_folder / "Rejected_Future"
    }
    
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)
    
    return folders

async def generate_excel_tracker(job_id: str, job_title: str) -> str:
    """Generate Excel tracker for a job"""
    # Fetch candidates for this job
    candidates = await db.candidates.find({"job_id": job_id}, {"_id": 0}).to_list(1000)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = job_title[:31]  # Excel sheet name limit
    
    # Headers
    headers = [
        "Candidate Name", "Mobile", "Email", "Skills", "Experience",
        "Match Percentage", "Current CTC", "Expected CTC", 
        "Notice Period / LWD", "Negotiable", "Candidate Response", "Remarks"
    ]
    
    # Styling
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="18181B", end_color="18181B", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Write headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
        cell.alignment = Alignment(horizontal='center')
    
    # Category colors
    category_colors = {
        "Shortlisted": "22C55E",
        "Hold": "EAB308",
        "Rejected_Future": "EF4444"
    }
    
    # Write data
    for row, candidate in enumerate(candidates, 2):
        data = [
            candidate.get('name', ''),
            candidate.get('mobile', ''),
            candidate.get('email', ''),
            ', '.join(candidate.get('skills', [])),
            candidate.get('experience', ''),
            f"{candidate.get('match_percentage', 0):.1f}%",
            candidate.get('current_ctc', ''),
            candidate.get('expected_ctc', ''),
            candidate.get('notice_period', ''),
            candidate.get('negotiable', ''),
            candidate.get('candidate_response', 'Pending'),
            candidate.get('remarks', '')
        ]
        
        category = candidate.get('category', 'Rejected_Future')
        row_fill = PatternFill(start_color=category_colors.get(category, "27272A"), 
                               end_color=category_colors.get(category, "27272A"), 
                               fill_type="solid")
        
        for col, value in enumerate(data, 1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.border = border
            if col == 6:  # Match percentage column
                cell.fill = row_fill
                cell.font = Font(bold=True, color="FFFFFF")
    
    # Adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column].width = adjusted_width
    
    # Save file
    filename = f"Recruitment_Tracker_{job_title[:20]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = EXPORT_DIR / filename
    wb.save(filepath)
    
    return str(filepath)

# ============== API Routes ==============

@api_router.get("/")
async def root():
    return {"message": "Local Recruitment ATS API"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Job Description Routes
@api_router.post("/jobs", response_model=JobDescription)
async def create_job(job_input: JobDescriptionCreate):
    """Create a new job description"""
    # Parse JD with AI
    parsed_data = await parse_jd_with_ai(job_input.raw_text)
    
    job = JobDescription(
        title=job_input.title or parsed_data.get('title', 'Unknown'),
        raw_text=job_input.raw_text,
        required_skills=parsed_data.get('required_skills', []),
        experience_required=parsed_data.get('experience_required'),
        location=parsed_data.get('location')
    )
    
    # Save to database
    doc = job.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.jobs.insert_one(doc)
    
    # Create recruitment folders
    create_recruitment_folders(job.title)
    
    return job

@api_router.get("/jobs", response_model=List[JobDescription])
async def get_jobs():
    """Get all job descriptions"""
    jobs = await db.jobs.find({}, {"_id": 0}).to_list(100)
    for job in jobs:
        if isinstance(job.get('created_at'), str):
            job['created_at'] = datetime.fromisoformat(job['created_at'])
    return jobs

@api_router.get("/jobs/{job_id}", response_model=JobDescription)
async def get_job(job_id: str):
    """Get a specific job description"""
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if isinstance(job.get('created_at'), str):
        job['created_at'] = datetime.fromisoformat(job['created_at'])
    return job

@api_router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its candidates"""
    result = await db.jobs.delete_one({"id": job_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.candidates.delete_many({"job_id": job_id})
    return {"message": "Job deleted successfully"}

# Resume Processing Routes
@api_router.post("/process-resumes/{job_id}", response_model=ProcessingResult)
async def process_resumes(job_id: str, files: List[UploadFile] = File(...)):
    """Process multiple resumes for a job"""
    # Get job
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Create folders
    folders = create_recruitment_folders(job['title'])
    
    candidates_processed = []
    shortlisted_count = 0
    hold_count = 0
    rejected_count = 0
    duplicates_found = []
    
    for file in files:
        # Skip non-resume files
        ext = Path(file.filename).suffix.lower()
        if ext not in ['.pdf', '.doc', '.docx', '.txt']:
            continue
        
        # Save uploaded file temporarily
        temp_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
        content = await file.read()
        
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(content)
        
        try:
            # Parse resume with AI
            parsed_data = await parse_resume_with_ai(str(temp_path), content, file.filename)
            
            # Check for duplicates across ALL jobs
            duplicate = await check_duplicate_candidate(
                parsed_data.get('email'),
                parsed_data.get('mobile')
            )
            
            if duplicate:
                # Get the job title for the existing candidate
                existing_job = await db.jobs.find_one({"id": duplicate.get('job_id')}, {"_id": 0})
                duplicates_found.append({
                    "new_name": parsed_data.get('name', 'Unknown'),
                    "new_email": parsed_data.get('email'),
                    "new_mobile": parsed_data.get('mobile'),
                    "existing_name": duplicate.get('name'),
                    "existing_email": duplicate.get('email'),
                    "existing_mobile": duplicate.get('mobile'),
                    "existing_job": existing_job.get('title') if existing_job else 'Unknown',
                    "existing_category": duplicate.get('category'),
                    "existing_match": duplicate.get('match_percentage'),
                    "match_type": duplicate.get('match_type', 'unknown'),
                    "filename": file.filename
                })
            
            # Calculate match score
            match_score = await calculate_match_score(
                job.get('required_skills', []),
                job.get('raw_text', ''),
                parsed_data
            )
            
            # Categorize
            category = categorize_candidate(match_score)
            
            # Create candidate record (still save even if duplicate - let recruiter decide)
            candidate = Candidate(
                job_id=job_id,
                name=parsed_data.get('name', 'Unknown'),
                mobile=parsed_data.get('mobile'),
                email=parsed_data.get('email'),
                skills=parsed_data.get('skills', []),
                experience=parsed_data.get('experience'),
                current_role=parsed_data.get('current_role'),
                match_percentage=match_score,
                category=category,
                original_filename=file.filename,
                remarks=f"DUPLICATE: Found in {duplicate.get('match_type')} match with existing candidate" if duplicate else None
            )
            
            # Save to database
            doc = candidate.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            doc['is_duplicate'] = True if duplicate else False
            await db.candidates.insert_one(doc)
            
            # Copy to appropriate folder
            category_folder = {
                "Shortlisted": folders["shortlisted"],
                "Hold": folders["hold"],
                "Rejected_Future": folders["rejected_future"]
            }
            dest_path = category_folder[category] / file.filename
            shutil.copy2(temp_path, dest_path)
            
            candidates_processed.append(candidate.model_dump())
            
            if category == "Shortlisted":
                shortlisted_count += 1
            elif category == "Hold":
                hold_count += 1
            else:
                rejected_count += 1
                
        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
    
    # Generate Excel tracker
    excel_path = await generate_excel_tracker(job_id, job['title'])
    
    # Get top 5 candidates
    top_candidates = sorted(candidates_processed, key=lambda x: x['match_percentage'], reverse=True)[:5]
    
    return ProcessingResult(
        job_id=job_id,
        total_processed=len(candidates_processed),
        shortlisted=shortlisted_count,
        hold=hold_count,
        rejected_future=rejected_count,
        top_candidates=top_candidates,
        folder_created=True,
        excel_path=excel_path.split('/')[-1] if excel_path else None,
        duplicates_found=duplicates_found
    )

# Candidate Routes
@api_router.get("/candidates/{job_id}", response_model=List[Candidate])
async def get_candidates(job_id: str, category: Optional[str] = None):
    """Get all candidates for a job"""
    query = {"job_id": job_id}
    if category:
        query["category"] = category
    
    candidates = await db.candidates.find(query, {"_id": 0}).to_list(1000)
    for candidate in candidates:
        if isinstance(candidate.get('created_at'), str):
            candidate['created_at'] = datetime.fromisoformat(candidate['created_at'])
    return candidates

@api_router.put("/candidates/{candidate_id}")
async def update_candidate(candidate_id: str, updates: Dict[str, Any]):
    """Update candidate details (for manual fields like CTC, response, etc.)"""
    allowed_fields = ['current_ctc', 'expected_ctc', 'notice_period', 'negotiable', 'candidate_response', 'remarks']
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if not filtered_updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    result = await db.candidates.update_one(
        {"id": candidate_id},
        {"$set": filtered_updates}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return {"message": "Candidate updated successfully"}

@api_router.delete("/candidates/{candidate_id}")
async def delete_candidate(candidate_id: str):
    """Delete a candidate"""
    result = await db.candidates.delete_one({"id": candidate_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"message": "Candidate deleted successfully"}

# Export Routes
@api_router.get("/export/{job_id}")
async def export_excel(job_id: str):
    """Generate and return Excel tracker"""
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    excel_path = await generate_excel_tracker(job_id, job['title'])
    
    return FileResponse(
        excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=Path(excel_path).name
    )

@api_router.get("/stats")
async def get_stats():
    """Get overall statistics"""
    total_jobs = await db.jobs.count_documents({})
    total_candidates = await db.candidates.count_documents({})
    shortlisted = await db.candidates.count_documents({"category": "Shortlisted"})
    hold = await db.candidates.count_documents({"category": "Hold"})
    rejected = await db.candidates.count_documents({"category": "Rejected_Future"})
    
    return {
        "total_jobs": total_jobs,
        "total_candidates": total_candidates,
        "shortlisted": shortlisted,
        "hold": hold,
        "rejected_future": rejected
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
