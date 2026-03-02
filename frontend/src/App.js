import React, { useState, useEffect, useCallback } from "react";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import {
  Briefcase,
  FileText,
  Users,
  Upload,
  Download,
  ChevronRight,
  Search,
  Plus,
  Trash2,
  Eye,
  CheckCircle,
  Clock,
  XCircle,
  BarChart3,
  FolderOpen,
  FileSpreadsheet,
  Loader2,
  Menu,
  X,
  AlertTriangle,
  Copy,
  GitCompare,
  ArrowLeftRight
} from "lucide-react";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Textarea } from "./components/ui/textarea";
import { Badge } from "./components/ui/badge";
import { Progress } from "./components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./components/ui/select";
import { ScrollArea } from "./components/ui/scroll-area";
import { Separator } from "./components/ui/separator";
import { Checkbox } from "./components/ui/checkbox";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "./components/ui/alert-dialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ============== Sidebar Component ==============
const Sidebar = ({ isOpen, setIsOpen }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { icon: BarChart3, label: "Dashboard", path: "/" },
    { icon: Briefcase, label: "Job Descriptions", path: "/jobs" },
    { icon: Users, label: "Candidates", path: "/candidates" },
    { icon: Upload, label: "Process Resumes", path: "/process" },
  ];

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
      
      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-[#18181b] border-r border-[#27272a] z-50 transform transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b border-[#27272a]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-[#22c55e] flex items-center justify-center">
              <Briefcase className="w-4 h-4 text-black" />
            </div>
            <span className="font-mono font-bold text-lg">ATS Agent</span>
          </div>
          <button
            className="lg:hidden p-1 hover:bg-[#27272a] rounded"
            onClick={() => setIsOpen(false)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="p-4 space-y-2">
          {menuItems.map((item) => (
            <button
              key={item.path}
              onClick={() => {
                navigate(item.path);
                setIsOpen(false);
              }}
              data-testid={`nav-${item.label.toLowerCase().replace(' ', '-')}`}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors sidebar-item ${
                location.pathname === item.path ? "active" : ""
              }`}
            >
              <item.icon className="w-5 h-5 text-[#a1a1aa]" />
              <span className="text-sm">{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-[#27272a]">
          <div className="text-xs text-[#a1a1aa] font-mono">
            <div>Local Recruitment ATS</div>
            <div className="text-[#22c55e]">Offline Mode</div>
          </div>
        </div>
      </aside>
    </>
  );
};

// ============== Dashboard Page ==============
const Dashboard = () => {
  const [stats, setStats] = useState({
    total_jobs: 0,
    total_candidates: 0,
    shortlisted: 0,
    hold: 0,
    rejected_future: 0,
  });
  const [recentJobs, setRecentJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, jobsRes] = await Promise.all([
          axios.get(`${API}/stats`),
          axios.get(`${API}/jobs`),
        ]);
        setStats(statsRes.data);
        setRecentJobs(jobsRes.data.slice(0, 5));
      } catch (error) {
        toast.error("Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const StatCard = ({ title, value, icon: Icon, color, testId }) => (
    <Card className="bg-[#18181b] border-[#27272a] card-hover">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-[#a1a1aa] mb-1">{title}</p>
            <p className="text-3xl font-mono font-bold" data-testid={testId}>{value}</p>
          </div>
          <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${color}`}>
            <Icon className="w-6 h-6" />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-[#22c55e]" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="dashboard">
      <div>
        <h1 className="text-3xl font-mono font-bold tracking-tight">Dashboard</h1>
        <p className="text-[#a1a1aa] mt-1">Your recruitment overview at a glance</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Jobs"
          value={stats.total_jobs}
          icon={Briefcase}
          color="bg-[#3b82f6]/20 text-[#3b82f6]"
          testId="stat-jobs"
        />
        <StatCard
          title="Total Candidates"
          value={stats.total_candidates}
          icon={Users}
          color="bg-[#8b5cf6]/20 text-[#8b5cf6]"
          testId="stat-candidates"
        />
        <StatCard
          title="Shortlisted"
          value={stats.shortlisted}
          icon={CheckCircle}
          color="bg-[#22c55e]/20 text-[#22c55e]"
          testId="stat-shortlisted"
        />
        <StatCard
          title="On Hold"
          value={stats.hold}
          icon={Clock}
          color="bg-[#eab308]/20 text-[#eab308]"
          testId="stat-hold"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Jobs */}
        <Card className="bg-[#18181b] border-[#27272a]">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-mono">Recent Jobs</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/jobs")}
                data-testid="view-all-jobs-btn"
              >
                View All <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {recentJobs.length === 0 ? (
              <div className="text-center py-8 text-[#a1a1aa]">
                <Briefcase className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No jobs created yet</p>
                <Button
                  className="mt-4"
                  onClick={() => navigate("/jobs")}
                  data-testid="create-first-job-btn"
                >
                  Create Your First Job
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {recentJobs.map((job, index) => (
                  <div
                    key={job.id}
                    className="flex items-center justify-between p-3 bg-[#27272a]/50 rounded-lg hover:bg-[#27272a] transition-colors cursor-pointer"
                    onClick={() => navigate(`/jobs/${job.id}`)}
                    style={{ animationDelay: `${index * 0.1}s` }}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded bg-[#27272a] flex items-center justify-center">
                        <FileText className="w-5 h-5 text-[#a1a1aa]" />
                      </div>
                      <div>
                        <p className="font-medium">{job.title}</p>
                        <p className="text-xs text-[#a1a1aa] font-mono">
                          {job.required_skills?.slice(0, 3).join(", ")}
                        </p>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-[#a1a1aa]" />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card className="bg-[#18181b] border-[#27272a]">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-mono">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              className="w-full justify-start gap-3 h-14 bg-[#27272a] hover:bg-[#3f3f46] text-left"
              onClick={() => navigate("/jobs")}
              data-testid="quick-add-job-btn"
            >
              <div className="w-10 h-10 rounded bg-[#22c55e]/20 flex items-center justify-center">
                <Plus className="w-5 h-5 text-[#22c55e]" />
              </div>
              <div>
                <p className="font-medium">Add New Job</p>
                <p className="text-xs text-[#a1a1aa]">Create a job description</p>
              </div>
            </Button>
            <Button
              className="w-full justify-start gap-3 h-14 bg-[#27272a] hover:bg-[#3f3f46] text-left"
              onClick={() => navigate("/process")}
              data-testid="quick-process-btn"
            >
              <div className="w-10 h-10 rounded bg-[#3b82f6]/20 flex items-center justify-center">
                <Upload className="w-5 h-5 text-[#3b82f6]" />
              </div>
              <div>
                <p className="font-medium">Process Resumes</p>
                <p className="text-xs text-[#a1a1aa]">Parse and match candidates</p>
              </div>
            </Button>
            <Button
              className="w-full justify-start gap-3 h-14 bg-[#27272a] hover:bg-[#3f3f46] text-left"
              onClick={() => navigate("/candidates")}
              data-testid="quick-view-candidates-btn"
            >
              <div className="w-10 h-10 rounded bg-[#8b5cf6]/20 flex items-center justify-center">
                <Users className="w-5 h-5 text-[#8b5cf6]" />
              </div>
              <div>
                <p className="font-medium">View Candidates</p>
                <p className="text-xs text-[#a1a1aa]">Browse all candidates</p>
              </div>
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Category Distribution */}
      <Card className="bg-[#18181b] border-[#27272a]">
        <CardHeader>
          <CardTitle className="text-lg font-mono">Candidate Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-[#22c55e]/10 border border-[#22c55e]/30">
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle className="w-5 h-5 text-[#22c55e]" />
                <span className="font-medium">Shortlisted</span>
              </div>
              <p className="text-2xl font-mono font-bold text-[#22c55e]">{stats.shortlisted}</p>
              <Progress
                value={stats.total_candidates > 0 ? (stats.shortlisted / stats.total_candidates) * 100 : 0}
                className="mt-2 h-1 bg-[#27272a]"
              />
            </div>
            <div className="p-4 rounded-lg bg-[#eab308]/10 border border-[#eab308]/30">
              <div className="flex items-center gap-3 mb-2">
                <Clock className="w-5 h-5 text-[#eab308]" />
                <span className="font-medium">On Hold</span>
              </div>
              <p className="text-2xl font-mono font-bold text-[#eab308]">{stats.hold}</p>
              <Progress
                value={stats.total_candidates > 0 ? (stats.hold / stats.total_candidates) * 100 : 0}
                className="mt-2 h-1 bg-[#27272a]"
              />
            </div>
            <div className="p-4 rounded-lg bg-[#ef4444]/10 border border-[#ef4444]/30">
              <div className="flex items-center gap-3 mb-2">
                <XCircle className="w-5 h-5 text-[#ef4444]" />
                <span className="font-medium">Rejected (Future)</span>
              </div>
              <p className="text-2xl font-mono font-bold text-[#ef4444]">{stats.rejected_future}</p>
              <Progress
                value={stats.total_candidates > 0 ? (stats.rejected_future / stats.total_candidates) * 100 : 0}
                className="mt-2 h-1 bg-[#27272a]"
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ============== Jobs Page ==============
const JobsPage = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newJob, setNewJob] = useState({ title: "", raw_text: "" });
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  const fetchJobs = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/jobs`);
      setJobs(res.data);
    } catch (error) {
      toast.error("Failed to load jobs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const handleCreateJob = async () => {
    if (!newJob.title || !newJob.raw_text) {
      toast.error("Please fill in all fields");
      return;
    }

    setCreating(true);
    try {
      await axios.post(`${API}/jobs`, newJob);
      toast.success("Job created successfully!");
      setShowCreateDialog(false);
      setNewJob({ title: "", raw_text: "" });
      fetchJobs();
    } catch (error) {
      toast.error("Failed to create job");
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteJob = async (jobId) => {
    try {
      await axios.delete(`${API}/jobs/${jobId}`);
      toast.success("Job deleted successfully");
      fetchJobs();
    } catch (error) {
      toast.error("Failed to delete job");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-[#22c55e]" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="jobs-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-mono font-bold tracking-tight">Job Descriptions</h1>
          <p className="text-[#a1a1aa] mt-1">Manage your job postings</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="gap-2" data-testid="create-job-btn">
              <Plus className="w-4 h-4" />
              Add Job
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-[#18181b] border-[#27272a] max-w-2xl">
            <DialogHeader>
              <DialogTitle className="font-mono">Create New Job</DialogTitle>
              <DialogDescription>
                Add a job description to start matching candidates
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Job Title</label>
                <Input
                  placeholder="e.g., Senior Java Developer"
                  value={newJob.title}
                  onChange={(e) => setNewJob({ ...newJob, title: e.target.value })}
                  className="bg-[#27272a] border-[#3f3f46]"
                  data-testid="job-title-input"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Job Description</label>
                <Textarea
                  placeholder="Paste the full job description here..."
                  value={newJob.raw_text}
                  onChange={(e) => setNewJob({ ...newJob, raw_text: e.target.value })}
                  className="bg-[#27272a] border-[#3f3f46] min-h-[200px]"
                  data-testid="job-description-input"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateJob} disabled={creating} data-testid="submit-job-btn">
                {creating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Create Job
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {jobs.length === 0 ? (
        <Card className="bg-[#18181b] border-[#27272a]">
          <CardContent className="py-16 text-center">
            <Briefcase className="w-16 h-16 mx-auto mb-4 text-[#a1a1aa] opacity-50" />
            <h3 className="text-xl font-medium mb-2">No Jobs Yet</h3>
            <p className="text-[#a1a1aa] mb-6">Create your first job description to get started</p>
            <Button onClick={() => setShowCreateDialog(true)} data-testid="empty-create-job-btn">
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Job
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {jobs.map((job, index) => (
            <Card
              key={job.id}
              className="bg-[#18181b] border-[#27272a] card-hover"
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-10 h-10 rounded bg-[#27272a] flex items-center justify-center">
                        <FileText className="w-5 h-5 text-[#22c55e]" />
                      </div>
                      <div>
                        <h3 className="text-lg font-medium">{job.title}</h3>
                        <p className="text-xs text-[#a1a1aa] font-mono">
                          {job.location || "Location not specified"} • {job.experience_required || "Experience flexible"}
                        </p>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2 mt-3">
                      {job.required_skills?.slice(0, 6).map((skill, i) => (
                        <span key={i} className="skill-tag">
                          {skill}
                        </span>
                      ))}
                      {job.required_skills?.length > 6 && (
                        <span className="skill-tag text-[#a1a1aa]">
                          +{job.required_skills.length - 6} more
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/process?job=${job.id}`)}
                      data-testid={`process-job-${job.id}-btn`}
                    >
                      <Upload className="w-4 h-4 mr-1" />
                      Process
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/candidates?job=${job.id}`)}
                      data-testid={`view-candidates-${job.id}-btn`}
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      View
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-[#ef4444] hover:text-[#ef4444] hover:bg-[#ef4444]/10"
                      onClick={() => handleDeleteJob(job.id)}
                      data-testid={`delete-job-${job.id}-btn`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// ============== Process Resumes Page ==============
const ProcessPage = () => {
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState("");
  const [files, setFiles] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const res = await axios.get(`${API}/jobs`);
        setJobs(res.data);
        
        // Check URL params for pre-selected job
        const params = new URLSearchParams(window.location.search);
        const jobId = params.get("job");
        if (jobId) {
          setSelectedJob(jobId);
        }
      } catch (error) {
        toast.error("Failed to load jobs");
      }
    };
    fetchJobs();
  }, []);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files).filter((file) =>
      [".pdf", ".doc", ".docx", ".txt"].some((ext) =>
        file.name.toLowerCase().endsWith(ext)
      )
    );
    setFiles((prev) => [...prev, ...droppedFiles]);
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files).filter((file) =>
      [".pdf", ".doc", ".docx", ".txt"].some((ext) =>
        file.name.toLowerCase().endsWith(ext)
      )
    );
    setFiles((prev) => [...prev, ...selectedFiles]);
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleProcess = async () => {
    if (!selectedJob) {
      toast.error("Please select a job");
      return;
    }
    if (files.length === 0) {
      toast.error("Please add some resumes");
      return;
    }

    setProcessing(true);
    setResult(null);

    try {
      const formData = new FormData();
      files.forEach((file) => {
        formData.append("files", file);
      });

      const res = await axios.post(`${API}/process-resumes/${selectedJob}`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setResult(res.data);
      toast.success(`Processed ${res.data.total_processed} resumes successfully!`);
      setFiles([]);
    } catch (error) {
      toast.error("Failed to process resumes");
    } finally {
      setProcessing(false);
    }
  };

  const handleExportExcel = async () => {
    if (!selectedJob) return;
    
    try {
      const response = await axios.get(`${API}/export/${selectedJob}`, {
        responseType: "blob",
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `Recruitment_Tracker.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Excel file downloaded!");
    } catch (error) {
      toast.error("Failed to download Excel file");
    }
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case "Shortlisted":
        return "bg-[#22c55e] text-black";
      case "Hold":
        return "bg-[#eab308] text-black";
      default:
        return "bg-[#ef4444] text-white";
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="process-page">
      <div>
        <h1 className="text-3xl font-mono font-bold tracking-tight">Process Resumes</h1>
        <p className="text-[#a1a1aa] mt-1">Upload resumes to parse and match against job requirements</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Section */}
        <Card className="bg-[#18181b] border-[#27272a]">
          <CardHeader>
            <CardTitle className="text-lg font-mono">Upload Resumes</CardTitle>
            <CardDescription>Select a job and upload candidate resumes</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Select Job</label>
              <Select value={selectedJob} onValueChange={setSelectedJob}>
                <SelectTrigger className="bg-[#27272a] border-[#3f3f46]" data-testid="job-select">
                  <SelectValue placeholder="Choose a job description" />
                </SelectTrigger>
                <SelectContent className="bg-[#18181b] border-[#27272a]">
                  {jobs.map((job) => (
                    <SelectItem key={job.id} value={job.id}>
                      {job.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div
              className={`upload-zone rounded-lg p-8 text-center ${dragActive ? "drag-active" : ""}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                type="file"
                id="file-upload"
                multiple
                accept=".pdf,.doc,.docx,.txt"
                className="hidden"
                onChange={handleFileSelect}
                data-testid="file-input"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <Upload className="w-12 h-12 mx-auto mb-4 text-[#a1a1aa]" />
                <p className="text-lg font-medium mb-1">Drop resumes here</p>
                <p className="text-sm text-[#a1a1aa]">or click to browse</p>
                <p className="text-xs text-[#a1a1aa] mt-2">Supports PDF, DOC, DOCX, TXT</p>
              </label>
            </div>

            {files.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm font-medium">{files.length} files selected</p>
                <ScrollArea className="h-40">
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-2 bg-[#27272a] rounded mb-2"
                    >
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-[#a1a1aa]" />
                        <span className="text-sm truncate max-w-[200px]">{file.name}</span>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(index)}
                        className="h-6 w-6 p-0"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </ScrollArea>
              </div>
            )}

            <Button
              className="w-full gap-2"
              onClick={handleProcess}
              disabled={processing || !selectedJob || files.length === 0}
              data-testid="process-btn"
            >
              {processing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Process {files.length} Resume{files.length !== 1 ? "s" : ""}
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Results Section */}
        <Card className="bg-[#18181b] border-[#27272a]">
          <CardHeader>
            <CardTitle className="text-lg font-mono">Processing Results</CardTitle>
          </CardHeader>
          <CardContent>
            {!result ? (
              <div className="text-center py-12 text-[#a1a1aa]">
                <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Results will appear here after processing</p>
              </div>
            ) : (
              <div className="space-y-6" data-testid="processing-results">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-[#27272a] rounded-lg text-center">
                    <p className="text-3xl font-mono font-bold">{result.total_processed}</p>
                    <p className="text-sm text-[#a1a1aa]">Total Processed</p>
                  </div>
                  <div className="p-4 bg-[#22c55e]/10 rounded-lg text-center border border-[#22c55e]/30">
                    <p className="text-3xl font-mono font-bold text-[#22c55e]">{result.shortlisted}</p>
                    <p className="text-sm text-[#a1a1aa]">Shortlisted</p>
                  </div>
                  <div className="p-4 bg-[#eab308]/10 rounded-lg text-center border border-[#eab308]/30">
                    <p className="text-3xl font-mono font-bold text-[#eab308]">{result.hold}</p>
                    <p className="text-sm text-[#a1a1aa]">On Hold</p>
                  </div>
                  <div className="p-4 bg-[#ef4444]/10 rounded-lg text-center border border-[#ef4444]/30">
                    <p className="text-3xl font-mono font-bold text-[#ef4444]">{result.rejected_future}</p>
                    <p className="text-sm text-[#a1a1aa]">Rejected (Future)</p>
                  </div>
                </div>

                <Separator className="bg-[#27272a]" />

                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium">Top 5 Candidates</h4>
                    <Badge variant="outline" className="font-mono">
                      <CheckCircle className="w-3 h-3 mr-1 text-[#22c55e]" />
                      Best Matches
                    </Badge>
                  </div>
                  <ScrollArea className="h-48">
                    {result.top_candidates.map((candidate, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 bg-[#27272a]/50 rounded-lg mb-2"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-[#27272a] flex items-center justify-center font-mono font-bold text-sm">
                            #{index + 1}
                          </div>
                          <div>
                            <p className="font-medium">{candidate.name}</p>
                            <p className="text-xs text-[#a1a1aa]">{candidate.current_role || "Role N/A"}</p>
                          </div>
                        </div>
                        <Badge className={`${getCategoryColor(candidate.category)} font-mono`}>
                          {candidate.match_percentage.toFixed(0)}%
                        </Badge>
                      </div>
                    ))}
                  </ScrollArea>
                </div>

                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    className="flex-1 gap-2"
                    onClick={() => navigate(`/candidates?job=${selectedJob}`)}
                    data-testid="view-all-candidates-btn"
                  >
                    <Eye className="w-4 h-4" />
                    View All
                  </Button>
                  <Button
                    className="flex-1 gap-2"
                    onClick={handleExportExcel}
                    data-testid="export-excel-btn"
                  >
                    <FileSpreadsheet className="w-4 h-4" />
                    Export Excel
                  </Button>
                </div>

                {/* Duplicates Warning */}
                {result.duplicates_found && result.duplicates_found.length > 0 && (
                  <div className="p-4 bg-[#eab308]/10 border border-[#eab308]/30 rounded-lg">
                    <div className="flex items-center gap-2 mb-3">
                      <AlertTriangle className="w-5 h-5 text-[#eab308]" />
                      <span className="font-medium text-[#eab308]">
                        {result.duplicates_found.length} Duplicate{result.duplicates_found.length > 1 ? 's' : ''} Detected
                      </span>
                    </div>
                    <ScrollArea className="max-h-40">
                      {result.duplicates_found.map((dup, index) => (
                        <div
                          key={index}
                          className="p-3 bg-[#27272a]/50 rounded-lg mb-2 text-sm"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <Copy className="w-4 h-4 text-[#eab308]" />
                            <span className="font-medium">{dup.new_name}</span>
                            <Badge variant="outline" className="text-xs">
                              {dup.match_type} match
                            </Badge>
                          </div>
                          <p className="text-[#a1a1aa] text-xs">
                            Already exists as <span className="text-white">{dup.existing_name}</span> in{" "}
                            <span className="text-[#3b82f6]">{dup.existing_job}</span>
                            {" "}({dup.existing_category} - {dup.existing_match?.toFixed(0)}%)
                          </p>
                          <p className="text-[#a1a1aa] text-xs mt-1 font-mono">
                            {dup.existing_email || dup.existing_mobile}
                          </p>
                        </div>
                      ))}
                    </ScrollArea>
                    <p className="text-xs text-[#a1a1aa] mt-2">
                      Candidates were still added but marked as duplicates. Review in Candidates page.
                    </p>
                  </div>
                )}

                <div className="flex items-center gap-2 text-sm text-[#22c55e] bg-[#22c55e]/10 p-3 rounded-lg">
                  <FolderOpen className="w-4 h-4" />
                  <span>Folders created successfully in /Recruitment/{jobs.find(j => j.id === selectedJob)?.title || 'Job'}/</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// ============== Candidates Page ==============
const CandidatesPage = () => {
  const [candidates, setCandidates] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [editCandidate, setEditCandidate] = useState(null);
  const [selectedForCompare, setSelectedForCompare] = useState([]);
  const [showCompareDialog, setShowCompareDialog] = useState(false);
  const [compareResult, setCompareResult] = useState(null);
  const [comparing, setComparing] = useState(false);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const res = await axios.get(`${API}/jobs`);
        setJobs(res.data);
        
        const params = new URLSearchParams(window.location.search);
        const jobId = params.get("job");
        if (jobId) {
          setSelectedJob(jobId);
        } else if (res.data.length > 0) {
          setSelectedJob(res.data[0].id);
        }
      } catch (error) {
        toast.error("Failed to load jobs");
      }
    };
    fetchJobs();
  }, []);

  useEffect(() => {
    const fetchCandidates = async () => {
      if (!selectedJob) {
        setLoading(false);
        return;
      }
      
      setLoading(true);
      try {
        let url = `${API}/candidates/${selectedJob}`;
        if (categoryFilter !== "all") {
          url += `?category=${categoryFilter}`;
        }
        const res = await axios.get(url);
        setCandidates(res.data);
      } catch (error) {
        toast.error("Failed to load candidates");
      } finally {
        setLoading(false);
      }
    };
    fetchCandidates();
  }, [selectedJob, categoryFilter]);

  const handleUpdateCandidate = async () => {
    if (!editCandidate) return;
    
    try {
      await axios.put(`${API}/candidates/${editCandidate.id}`, {
        current_ctc: editCandidate.current_ctc,
        expected_ctc: editCandidate.expected_ctc,
        notice_period: editCandidate.notice_period,
        negotiable: editCandidate.negotiable,
        candidate_response: editCandidate.candidate_response,
        remarks: editCandidate.remarks,
      });
      toast.success("Candidate updated successfully");
      setEditCandidate(null);
      
      // Refresh candidates
      const res = await axios.get(`${API}/candidates/${selectedJob}`);
      setCandidates(res.data);
    } catch (error) {
      toast.error("Failed to update candidate");
    }
  };

  const handleExportExcel = async () => {
    if (!selectedJob) return;
    
    try {
      const response = await axios.get(`${API}/export/${selectedJob}`, {
        responseType: "blob",
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `Recruitment_Tracker.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Excel file downloaded!");
    } catch (error) {
      toast.error("Failed to download Excel file");
    }
  };

  const toggleCompareSelection = (candidateId) => {
    setSelectedForCompare((prev) => {
      if (prev.includes(candidateId)) {
        return prev.filter((id) => id !== candidateId);
      }
      if (prev.length >= 5) {
        toast.error("Maximum 5 candidates can be compared");
        return prev;
      }
      return [...prev, candidateId];
    });
  };

  const handleCompare = async () => {
    if (selectedForCompare.length < 2) {
      toast.error("Select at least 2 candidates to compare");
      return;
    }

    setComparing(true);
    try {
      const res = await axios.post(`${API}/compare-candidates`, {
        candidate_ids: selectedForCompare,
      });
      setCompareResult(res.data);
      setShowCompareDialog(true);
    } catch (error) {
      toast.error("Failed to compare candidates");
    } finally {
      setComparing(false);
    }
  };

  const clearCompareSelection = () => {
    setSelectedForCompare([]);
    setCompareResult(null);
  };

  const filteredCandidates = candidates.filter((c) =>
    c.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.skills?.some((s) => s.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const getCategoryBadge = (category) => {
    switch (category) {
      case "Shortlisted":
        return <Badge className="status-shortlisted font-mono">{category}</Badge>;
      case "Hold":
        return <Badge className="status-hold font-mono">{category}</Badge>;
      default:
        return <Badge className="status-rejected font-mono">Rejected</Badge>;
    }
  };

  const getMatchColor = (percentage) => {
    if (percentage >= 75) return "text-[#22c55e]";
    if (percentage >= 50) return "text-[#eab308]";
    return "text-[#ef4444]";
  };

  return (
    <div className="space-y-6 animate-fadeIn" data-testid="candidates-page">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-mono font-bold tracking-tight">Candidates</h1>
          <p className="text-[#a1a1aa] mt-1">View and manage all candidates</p>
        </div>
        <div className="flex gap-2">
          {selectedForCompare.length > 0 && (
            <>
              <Button
                variant="outline"
                onClick={clearCompareSelection}
                className="gap-2"
                data-testid="clear-compare-btn"
              >
                <X className="w-4 h-4" />
                Clear ({selectedForCompare.length})
              </Button>
              <Button
                onClick={handleCompare}
                disabled={selectedForCompare.length < 2 || comparing}
                className="gap-2 bg-[#3b82f6] hover:bg-[#2563eb]"
                data-testid="compare-btn"
              >
                {comparing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <GitCompare className="w-4 h-4" />
                )}
                Compare {selectedForCompare.length} Candidates
              </Button>
            </>
          )}
          <Button
            onClick={handleExportExcel}
            disabled={!selectedJob}
            className="gap-2"
            data-testid="export-all-excel-btn"
          >
            <Download className="w-4 h-4" />
            Export Excel
          </Button>
        </div>
      </div>

      {/* Compare Dialog */}
      <Dialog open={showCompareDialog} onOpenChange={setShowCompareDialog}>
        <DialogContent className="bg-[#18181b] border-[#27272a] max-w-5xl max-h-[90vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle className="font-mono flex items-center gap-2">
              <ArrowLeftRight className="w-5 h-5 text-[#3b82f6]" />
              Compare Candidates
            </DialogTitle>
            <DialogDescription>
              Side-by-side comparison of selected candidates
            </DialogDescription>
          </DialogHeader>
          {compareResult && (
            <ScrollArea className="max-h-[60vh]">
              <div className="space-y-6">
                {/* Common Skills */}
                <div className="p-4 bg-[#27272a]/50 rounded-lg">
                  <h4 className="font-medium mb-2 flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-[#22c55e]" />
                    Common Skills ({compareResult.comparison_metrics.common_skills_count})
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {compareResult.comparison_metrics.common_skills.map((skill, i) => (
                      <span key={i} className="skill-tag bg-[#22c55e]/20 text-[#22c55e]">
                        {skill}
                      </span>
                    ))}
                    {compareResult.comparison_metrics.common_skills.length === 0 && (
                      <span className="text-[#a1a1aa] text-sm">No common skills found</span>
                    )}
                  </div>
                </div>

                {/* Comparison Grid */}
                <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${compareResult.candidates.length}, minmax(200px, 1fr))` }}>
                  {compareResult.candidates.map((candidate, index) => (
                    <Card key={candidate.id} className="bg-[#27272a] border-[#3f3f46]">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <Badge className={`${candidate.category === 'Shortlisted' ? 'bg-[#22c55e]' : candidate.category === 'Hold' ? 'bg-[#eab308]' : 'bg-[#ef4444]'} text-black font-mono`}>
                            {candidate.match_percentage?.toFixed(0)}%
                          </Badge>
                          <span className="text-xs text-[#a1a1aa]">#{index + 1}</span>
                        </div>
                        <CardTitle className="text-lg mt-2">{candidate.name}</CardTitle>
                        <CardDescription className="font-mono text-xs">
                          {candidate.current_role || "Role N/A"}
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-3 text-sm">
                        <div>
                          <p className="text-[#a1a1aa] text-xs mb-1">Experience</p>
                          <p className="font-mono">{candidate.experience || "N/A"}</p>
                        </div>
                        <div>
                          <p className="text-[#a1a1aa] text-xs mb-1">Contact</p>
                          <p className="font-mono text-xs">{candidate.email || "N/A"}</p>
                          <p className="font-mono text-xs">{candidate.mobile || "N/A"}</p>
                        </div>
                        <div>
                          <p className="text-[#a1a1aa] text-xs mb-1">Skill Coverage</p>
                          <Progress value={candidate.skill_coverage} className="h-2" />
                          <p className="text-xs mt-1 font-mono">{candidate.skill_coverage}%</p>
                        </div>
                        <div>
                          <p className="text-[#a1a1aa] text-xs mb-1">Skills ({candidate.skills?.length || 0})</p>
                          <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
                            {candidate.skills?.slice(0, 8).map((skill, i) => (
                              <span key={i} className="skill-tag text-xs">
                                {skill}
                              </span>
                            ))}
                            {candidate.skills?.length > 8 && (
                              <span className="skill-tag text-xs text-[#a1a1aa]">
                                +{candidate.skills.length - 8}
                              </span>
                            )}
                          </div>
                        </div>
                        {candidate.unique_skills?.length > 0 && (
                          <div>
                            <p className="text-[#a1a1aa] text-xs mb-1">Unique Skills</p>
                            <div className="flex flex-wrap gap-1">
                              {candidate.unique_skills.slice(0, 5).map((skill, i) => (
                                <span key={i} className="skill-tag text-xs bg-[#3b82f6]/20 text-[#3b82f6]">
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        <Separator className="bg-[#3f3f46]" />
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <p className="text-[#a1a1aa]">CTC</p>
                            <p className="font-mono">{candidate.current_ctc || "-"}</p>
                          </div>
                          <div>
                            <p className="text-[#a1a1aa]">Expected</p>
                            <p className="font-mono">{candidate.expected_ctc || "-"}</p>
                          </div>
                          <div>
                            <p className="text-[#a1a1aa]">Notice</p>
                            <p className="font-mono">{candidate.notice_period || "-"}</p>
                          </div>
                          <div>
                            <p className="text-[#a1a1aa]">Response</p>
                            <p className="font-mono">{candidate.candidate_response || "Pending"}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            </ScrollArea>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCompareDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Filters */}
      <Card className="bg-[#18181b] border-[#27272a]">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <Select value={selectedJob} onValueChange={setSelectedJob}>
                <SelectTrigger className="bg-[#27272a] border-[#3f3f46]" data-testid="filter-job-select">
                  <SelectValue placeholder="Select a job" />
                </SelectTrigger>
                <SelectContent className="bg-[#18181b] border-[#27272a]">
                  {jobs.map((job) => (
                    <SelectItem key={job.id} value={job.id}>
                      {job.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1 min-w-[200px]">
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="bg-[#27272a] border-[#3f3f46]" data-testid="filter-category-select">
                  <SelectValue placeholder="Filter by category" />
                </SelectTrigger>
                <SelectContent className="bg-[#18181b] border-[#27272a]">
                  <SelectItem value="all">All Categories</SelectItem>
                  <SelectItem value="Shortlisted">Shortlisted</SelectItem>
                  <SelectItem value="Hold">On Hold</SelectItem>
                  <SelectItem value="Rejected_Future">Rejected (Future)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1 min-w-[250px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#a1a1aa]" />
                <Input
                  placeholder="Search by name, email, or skill..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 bg-[#27272a] border-[#3f3f46]"
                  data-testid="search-input"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Candidates Table */}
      <Card className="bg-[#18181b] border-[#27272a]">
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-[#22c55e]" />
            </div>
          ) : filteredCandidates.length === 0 ? (
            <div className="text-center py-16 text-[#a1a1aa]">
              <Users className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p>No candidates found</p>
              <p className="text-sm mt-1">Process some resumes to see candidates here</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table className="data-table">
                <TableHeader>
                  <TableRow className="border-[#27272a] hover:bg-transparent">
                    <TableHead className="text-[#a1a1aa] w-12">
                      <div className="flex items-center gap-1">
                        <GitCompare className="w-4 h-4" />
                      </div>
                    </TableHead>
                    <TableHead className="text-[#a1a1aa]">Candidate</TableHead>
                    <TableHead className="text-[#a1a1aa]">Contact</TableHead>
                    <TableHead className="text-[#a1a1aa]">Skills</TableHead>
                    <TableHead className="text-[#a1a1aa]">Experience</TableHead>
                    <TableHead className="text-[#a1a1aa]">Match</TableHead>
                    <TableHead className="text-[#a1a1aa]">Status</TableHead>
                    <TableHead className="text-[#a1a1aa]">Response</TableHead>
                    <TableHead className="text-[#a1a1aa]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredCandidates.map((candidate) => (
                    <TableRow key={candidate.id} className={`border-[#27272a] ${candidate.is_duplicate ? 'bg-[#eab308]/5' : ''}`}>
                      <TableCell>
                        <Checkbox
                          checked={selectedForCompare.includes(candidate.id)}
                          onCheckedChange={() => toggleCompareSelection(candidate.id)}
                          className="border-[#3f3f46] data-[state=checked]:bg-[#3b82f6] data-[state=checked]:border-[#3b82f6]"
                          data-testid={`compare-checkbox-${candidate.id}`}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {candidate.is_duplicate && (
                            <AlertTriangle className="w-4 h-4 text-[#eab308]" title="Duplicate candidate" />
                          )}
                          <div>
                            <p className="font-medium">{candidate.name}</p>
                            <p className="text-xs text-[#a1a1aa]">{candidate.current_role || "N/A"}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm font-mono">
                          <p>{candidate.mobile || "N/A"}</p>
                          <p className="text-xs text-[#a1a1aa]">{candidate.email || "N/A"}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1 max-w-[200px]">
                          {candidate.skills?.slice(0, 3).map((skill, i) => (
                            <span key={i} className="skill-tag text-xs">
                              {skill}
                            </span>
                          ))}
                          {candidate.skills?.length > 3 && (
                            <span className="skill-tag text-xs text-[#a1a1aa]">
                              +{candidate.skills.length - 3}
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {candidate.experience || "N/A"}
                      </TableCell>
                      <TableCell>
                        <span className={`font-mono font-bold text-lg ${getMatchColor(candidate.match_percentage)}`}>
                          {candidate.match_percentage?.toFixed(0)}%
                        </span>
                      </TableCell>
                      <TableCell>{getCategoryBadge(candidate.category)}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono">
                          {candidate.candidate_response || "Pending"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setEditCandidate({ ...candidate })}
                              data-testid={`edit-candidate-${candidate.id}-btn`}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="bg-[#18181b] border-[#27272a] max-w-lg">
                            <DialogHeader>
                              <DialogTitle className="font-mono">{candidate.name}</DialogTitle>
                              <DialogDescription>
                                Update candidate details
                              </DialogDescription>
                            </DialogHeader>
                            {editCandidate && editCandidate.id === candidate.id && (
                              <div className="space-y-4 py-4">
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <label className="text-sm font-medium mb-2 block">Current CTC</label>
                                    <Input
                                      placeholder="e.g., 12 LPA"
                                      value={editCandidate.current_ctc || ""}
                                      onChange={(e) =>
                                        setEditCandidate({ ...editCandidate, current_ctc: e.target.value })
                                      }
                                      className="bg-[#27272a] border-[#3f3f46]"
                                    />
                                  </div>
                                  <div>
                                    <label className="text-sm font-medium mb-2 block">Expected CTC</label>
                                    <Input
                                      placeholder="e.g., 15 LPA"
                                      value={editCandidate.expected_ctc || ""}
                                      onChange={(e) =>
                                        setEditCandidate({ ...editCandidate, expected_ctc: e.target.value })
                                      }
                                      className="bg-[#27272a] border-[#3f3f46]"
                                    />
                                  </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <label className="text-sm font-medium mb-2 block">Notice Period</label>
                                    <Input
                                      placeholder="e.g., 30 days"
                                      value={editCandidate.notice_period || ""}
                                      onChange={(e) =>
                                        setEditCandidate({ ...editCandidate, notice_period: e.target.value })
                                      }
                                      className="bg-[#27272a] border-[#3f3f46]"
                                    />
                                  </div>
                                  <div>
                                    <label className="text-sm font-medium mb-2 block">Negotiable</label>
                                    <Select
                                      value={editCandidate.negotiable || ""}
                                      onValueChange={(val) =>
                                        setEditCandidate({ ...editCandidate, negotiable: val })
                                      }
                                    >
                                      <SelectTrigger className="bg-[#27272a] border-[#3f3f46]">
                                        <SelectValue placeholder="Select" />
                                      </SelectTrigger>
                                      <SelectContent className="bg-[#18181b] border-[#27272a]">
                                        <SelectItem value="Yes">Yes</SelectItem>
                                        <SelectItem value="No">No</SelectItem>
                                      </SelectContent>
                                    </Select>
                                  </div>
                                </div>
                                <div>
                                  <label className="text-sm font-medium mb-2 block">Candidate Response</label>
                                  <Select
                                    value={editCandidate.candidate_response || "Pending"}
                                    onValueChange={(val) =>
                                      setEditCandidate({ ...editCandidate, candidate_response: val })
                                    }
                                  >
                                    <SelectTrigger className="bg-[#27272a] border-[#3f3f46]">
                                      <SelectValue placeholder="Select" />
                                    </SelectTrigger>
                                    <SelectContent className="bg-[#18181b] border-[#27272a]">
                                      <SelectItem value="Yes">Yes</SelectItem>
                                      <SelectItem value="No">No</SelectItem>
                                      <SelectItem value="Pending">Pending</SelectItem>
                                    </SelectContent>
                                  </Select>
                                </div>
                                <div>
                                  <label className="text-sm font-medium mb-2 block">Remarks</label>
                                  <Textarea
                                    placeholder="Add notes..."
                                    value={editCandidate.remarks || ""}
                                    onChange={(e) =>
                                      setEditCandidate({ ...editCandidate, remarks: e.target.value })
                                    }
                                    className="bg-[#27272a] border-[#3f3f46]"
                                  />
                                </div>
                              </div>
                            )}
                            <DialogFooter>
                              <Button variant="outline" onClick={() => setEditCandidate(null)}>
                                Cancel
                              </Button>
                              <Button onClick={handleUpdateCandidate} data-testid="save-candidate-btn">
                                Save Changes
                              </Button>
                            </DialogFooter>
                          </DialogContent>
                        </Dialog>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// ============== Main App ==============
function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#09090b]">
      <BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#18181b",
              border: "1px solid #27272a",
              color: "#fafafa",
            },
          }}
        />
        <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
        
        {/* Mobile header */}
        <header className="lg:hidden fixed top-0 left-0 right-0 h-14 bg-[#18181b] border-b border-[#27272a] z-30 flex items-center px-4">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 hover:bg-[#27272a] rounded"
            data-testid="mobile-menu-btn"
          >
            <Menu className="w-5 h-5" />
          </button>
          <span className="ml-3 font-mono font-bold">ATS Agent</span>
        </header>

        {/* Main content */}
        <main className="lg:ml-64 pt-14 lg:pt-0 min-h-screen">
          <div className="p-6 lg:p-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/jobs" element={<JobsPage />} />
              <Route path="/process" element={<ProcessPage />} />
              <Route path="/candidates" element={<CandidatesPage />} />
            </Routes>
          </div>
        </main>
      </BrowserRouter>
    </div>
  );
}

export default App;
