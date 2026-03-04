from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
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
import shutil

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import aiofiles

from pypdf import PdfReader
from docx import Document

import google.generativeai as genai


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

app = FastAPI()

api_router = APIRouter(prefix="/api")

UPLOAD_DIR = ROOT_DIR / "uploads"
RECRUITMENT_DIR = ROOT_DIR / "Recruitment"
EXPORT_DIR = ROOT_DIR / "exports"

UPLOAD_DIR.mkdir(exist_ok=True)
RECRUITMENT_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# ===================== GEMINI =====================

def configure_gemini():
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY missing")
    genai.configure(api_key=api_key)


async def gemini_text(prompt: str, model: str = "gemini-1.5-flash") -> str:

    configure_gemini()

    def run():
        m = genai.GenerativeModel(model)
        resp = m.generate_content(prompt)
        return (resp.text or "").strip()

    return await asyncio.to_thread(run)


def safe_json_from_text(text):

    match = re.search(r"\{[\s\S]*\}", text)

    if not match:
        return None

    try:
        return json.loads(match.group())
    except Exception:
        return None


# ===================== MODELS =====================

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
    category: str = "Rejected_Future"
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


class CompareRequest(BaseModel):

    candidate_ids: List[str]


# ===================== HELPERS =====================

def normalize_phone(phone):

    if not phone:
        return None

    digits = re.sub(r"\D", "", phone)

    if len(digits) >= 10:
        return digits[-10:]

    return digits


def normalize_email(email):

    if not email:
        return None

    return email.lower().strip()


# ===================== TEXT EXTRACTION =====================

def extract_text_from_pdf(path):

    try:

        reader = PdfReader(path)

        parts = []

        for page in reader.pages:
            parts.append(page.extract_text() or "")

        return "\n".join(parts)

    except Exception as e:

        logger.error(e)

        return ""


def extract_text_from_docx(path):

    try:

        doc = Document(path)

        return "\n".join(p.text for p in doc.paragraphs)

    except Exception as e:

        logger.error(e)

        return ""


def extract_resume_text(file_path, content, filename):

    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)

    if ext == ".docx":
        return extract_text_from_docx(file_path)

    if ext == ".txt":
        return content.decode("utf-8", errors="ignore")

    return ""


# ===================== AI =====================

async def parse_jd_with_ai(jd_text):

    prompt = f"""
Extract structured job details.

Return JSON ONLY

Job Description:
{jd_text}
"""

    response = await gemini_text(prompt)

    data = safe_json_from_text(response)

    if not data:
        return {
            "title": "Unknown",
            "required_skills": [],
            "experience_required": None,
            "location": None,
        }

    return data


async def parse_resume_with_ai(file_path, content, filename):

    resume_text = extract_resume_text(file_path, content, filename)

    if not resume_text:
        return {
            "name": "Unknown",
            "mobile": None,
            "email": None,
            "skills": [],
            "experience": None,
            "current_role": None,
        }

    prompt = f"""
Extract candidate information.

Resume:
{resume_text[:12000]}
"""

    response = await gemini_text(prompt)

    data = safe_json_from_text(response)

    if not data:
        return {
            "name": "Unknown",
            "mobile": None,
            "email": None,
            "skills": [],
            "experience": None,
            "current_role": None,
        }

    return data


# ===================== API =====================

@api_router.get("/")
async def root():

    return {"message": "ATS API running"}


@api_router.get("/health")
async def health():

    return {"status": "healthy"}


# ===================== JOBS =====================

@api_router.get("/jobs")
async def get_jobs():

    jobs = await db.jobs.find({}, {"_id": 0}).to_list(100)

    return jobs


@api_router.post("/jobs")
async def create_job(job_input: JobDescriptionCreate):

    parsed = await parse_jd_with_ai(job_input.raw_text)

    job = JobDescription(
        title=job_input.title,
        raw_text=job_input.raw_text,
        required_skills=parsed.get("required_skills", []),
        experience_required=parsed.get("experience_required"),
        location=parsed.get("location"),
    )

    doc = job.model_dump()

    doc["created_at"] = doc["created_at"].isoformat()

    await db.jobs.insert_one(doc)

    return job


# ===================== STATS =====================

@api_router.get("/stats")
async def stats():

    total_jobs = await db.jobs.count_documents({})

    total_candidates = await db.candidates.count_documents({})

    return {
        "total_jobs": total_jobs,
        "total_candidates": total_candidates,
    }


# ===================== ROUTER =====================

app.include_router(api_router)


# ===================== CORS FIX =====================

allowed_origins = [
    "https://ats.dmags.in",
    "https://darshanmd1716-maker.github.io",
    "http://localhost:3000",
]

env_origins = os.environ.get("CORS_ORIGINS")

if env_origins:
    allowed_origins.extend(
        [o.strip() for o in env_origins.split(",") if o.strip()]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================== SHUTDOWN =====================

@app.on_event("shutdown")
async def shutdown():

    client.close()