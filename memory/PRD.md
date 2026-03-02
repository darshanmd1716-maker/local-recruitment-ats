# Local Recruitment Automation Agent (ATS Assistant) - PRD

## Original Problem Statement
Build a Local Recruitment Automation Agent for IT recruiters that works offline on Windows laptops. Features include JD analysis, resume parsing, candidate matching, folder organization, and Excel tracker generation.

## User Personas
- **Primary**: IT Recruiters working locally without cloud dependencies
- **Secondary**: HR Managers needing candidate tracking and Excel reports

## Core Requirements (Static)
1. Accept JD (text/PDF/DOC) and extract skills, experience, location
2. Parse resumes to extract: Name, Mobile, Email, Skills, Experience, Role
3. AI-powered semantic matching with Match Score (0-100%)
4. Categorize: Shortlisted (≥75%), Hold (50-74%), Rejected_Future (<50%)
5. Create folder structure: Recruitment/<Job>/Shortlisted|Hold|Rejected_Future
6. Maintain Excel tracker with all candidate data
7. No cloud uploads, no email/WhatsApp, preserve data integrity

## What's Been Implemented (Jan 2026)
- ✅ Dashboard with stats cards (Jobs, Candidates, Shortlisted, Hold)
- ✅ Job Description creation with AI parsing (Gemini)
- ✅ Resume upload and processing with file drag-drop
- ✅ AI-powered resume parsing extracting all required fields
- ✅ Semantic matching algorithm with categorization
- ✅ Folder structure creation at /backend/Recruitment/
- ✅ Excel tracker generation with styled columns
- ✅ Candidate management with manual field updates
- ✅ Dark theme UI with JetBrains Mono font
- ✅ Responsive design with mobile sidebar

## Tech Stack
- **Backend**: FastAPI, MongoDB, emergentintegrations (Gemini AI)
- **Frontend**: React, Tailwind CSS, shadcn/ui components
- **AI**: Gemini 2.5 Flash for resume/JD parsing and matching

## Prioritized Backlog

### P0 - Critical
- All features implemented ✅

### P1 - High Priority
- Bulk resume download from category folders
- Duplicate candidate detection
- Interview scheduling integration

### P2 - Medium Priority
- Resume templates matching
- Skills gap analysis report
- Candidate comparison view

### P3 - Low Priority
- Dark/Light theme toggle
- Custom match score weights
- Resume annotation features

## Next Tasks
1. Add bulk export functionality for specific categories
2. Implement duplicate candidate warning
3. Add interview scheduling calendar
4. Create skills gap analysis dashboard
