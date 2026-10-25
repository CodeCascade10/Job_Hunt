import { useState } from "react";
import api from "./api";
import "./App.css";

type Candidate = {
  id: number;
  full_name: string;
  email: string;
  target_role: string | null;
  skills: string[];
};

type Job = {
  id: number;
  title: string;
  company: string;
  location: string | null;
  job_url: string | null;
  source?: string;
};

type Recommendation = Job & {
  match_score: number;
  matching_skills: string[];
  missing_skills: string[];
  explanation: string;
};

function getErrorMessage(error: unknown): string {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (error as {
      response?: { data?: { detail?: string } };
    }).response;

    if (response?.data?.detail) {
      return response.data.detail;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong. Please try again.";
}

function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [candidateId, setCandidateId] = useState("");
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [loadingCandidate, setLoadingCandidate] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [skillsInput, setSkillsInput] = useState("");
  const [savingCandidate, setSavingCandidate] = useState(false);



  <section>
  <h2>Create candidate</h2>

  <form onSubmit={createCandidate}>
    <label htmlFor="fullName">Full name</label>
    <input
      id="fullName"
      value={fullName}
      onChange={(event) => setFullName(event.target.value)}
      required
      maxLength={150}
    />

    <label htmlFor="email">Email</label>
    <input
      id="email"
      type="email"
      value={email}
      onChange={(event) => setEmail(event.target.value)}
      required
    />

    <label htmlFor="targetRole">Target role</label>
    <input
      id="targetRole"
      value={targetRole}
      onChange={(event) => setTargetRole(event.target.value)}
      placeholder="e.g. Python Developer"
      maxLength={150}
    />

    <label htmlFor="skills">Skills (comma-separated)</label>
    <input
      id="skills"
      value={skillsInput}
      onChange={(event) => setSkillsInput(event.target.value)}
      placeholder="Python, FastAPI, SQL, Docker"
    />

    <button type="submit" disabled={savingCandidate}>
      {savingCandidate ? "Creating..." : "Create candidate"}
    </button>
  </form>
</section>

  async function loadJobs() {
    setLoadingJobs(true);
    setError("");
    setMessage("");

    try {
      const response = await api.get("/jobs/", {
        params: { limit: 20 },
      });

      setJobs(response.data.jobs ?? []);
      setMessage(`Loaded ${response.data.count ?? 0} jobs.`);
    } catch (err) {
      setError(`Could not load jobs: ${getErrorMessage(err)}`);
    } finally {
      setLoadingJobs(false);
    }
  }

  async function loadCandidateAndRecommendations() {
    const id = Number(candidateId);

    if (!Number.isInteger(id) || id < 1) {
      setError("Enter a valid positive candidate ID.");
      return;
    }

    setLoadingCandidate(true);
    setError("");
    setMessage("");
    setCandidate(null);
    setRecommendations([]);

    try {
      const [candidateResponse, recommendationResponse] = await Promise.all([
        api.get(`/candidates/${id}`),
        api.get(`/jobs/recommendations/${id}`, {
          params: { limit: 20 },
        }),
      ]);

      setCandidate(candidateResponse.data);
      setRecommendations(recommendationResponse.data.recommendations ?? []);
      setMessage(
        `Loaded profile and ${recommendationResponse.data.count ?? 0} recommendations.`,
      );
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoadingCandidate(false);
    }
  }

  async function createCandidate(event: React.FormEvent<HTMLFormElement>) {
  event.preventDefault();
  setError("");
  setMessage("");
  setSavingCandidate(true);

  try {
    const response = await api.post("/candidates/", {
      full_name: fullName.trim(),
      email: email.trim(),
      target_role: targetRole.trim() || null,
      skills: skillsInput
        .split(",")
        .map((skill) => skill.trim())
        .filter(Boolean),
    });

    const createdCandidate = response.data as Candidate;

    setCandidate(createdCandidate);
    setCandidateId(String(createdCandidate.id));
    setFullName("");
    setEmail("");
    setTargetRole("");
    setSkillsInput("");

    alert(
      `Profile created successfully!\nCandidate: ${createdCandidate.full_name}\nCandidate ID: ${createdCandidate.id}`,
    );

    setMessage(`Profile created successfully. Candidate ID: ${createdCandidate.id}`);

    await loadJobs();
      } catch (err) {
        setError(`Could not create candidate: ${getErrorMessage(err)}`);
      } finally {
        setSavingCandidate(false);
      }
    }


  async function updateCandidate(event: React.FormEvent<HTMLFormElement>) {
  event.preventDefault();

  if (!candidate) {
    setError("Load a candidate before editing their profile.");
    return;
  }

  setError("");
  setMessage("");
  setSavingCandidate(true);

  try {
    const response = await api.patch(
      `/candidates/${candidate.id}/profile`,
      {
        full_name: fullName.trim(),
        email: email.trim(),
        target_role: targetRole.trim() || null,
      },
    );

    const updatedCandidate = response.data as Candidate;
    setCandidate(updatedCandidate);

    const skills = skillsInput
      .split(",")
      .map((skill) => skill.trim())
      .filter(Boolean);

    await api.patch(`/candidates/${candidate.id}/skills`, { skills });

    const refreshed = await api.get(`/candidates/${candidate.id}`);
    setCandidate(refreshed.data);

    setMessage("Profile updated successfully.");
    alert(`Profile updated successfully!\nCandidate ID: ${candidate.id}`);

    await loadCandidateAndRecommendations();
  } catch (err) {
    setError(`Could not update profile: ${getErrorMessage(err)}`);
  } finally {
    setSavingCandidate(false);
  }
}

  return (
    <main className="app">
      <header>
        <h1>Agentic Job Hunter</h1>
        <p>Find jobs and explore recommendations matched to your skills.</p>
      </header>

      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}

      {message && (
        <p className="notice" role="status">
          {message}
        </p>
      )}

            <section>
        <h2>Create candidate</h2>

        <form 
         onSubmit={candidate ? updateCandidate : createCandidate}>
          <label htmlFor="fullName">Full name</label>
          <input
            id="fullName"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            required
            maxLength={150}
            placeholder="Enter full name"
          />

          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            placeholder="Enter email address"
          />

          <label htmlFor="targetRole">Target role</label>
          <input
            id="targetRole"
            value={targetRole}
            onChange={(event) => setTargetRole(event.target.value)}
            maxLength={150}
            placeholder="e.g. Python Developer"
          />

          <label htmlFor="skillsInput">Skills (comma-separated)</label>
          <input
            id="skillsInput"
            value={skillsInput}
            onChange={(event) => setSkillsInput(event.target.value)}
            placeholder="Python, FastAPI, SQL, Docker"
          />

          <button type="submit" disabled={savingCandidate}>
            {savingCandidate
              ? "Saving..."
              : candidate
                ? "Update profile"
                : "Create candidate"}
          </button>
        </form>
      </section>

      <section>
        <h2>Job listings</h2>
        <button onClick={loadJobs} disabled={loadingJobs}>
          {loadingJobs ? "Loading jobs..." : "Load jobs"}
        </button>

        {jobs.length === 0 && !loadingJobs && (
          <p>No jobs loaded yet. Select “Load jobs” to fetch listings.</p>
        )}

        <div className="job-list">
          {jobs.map((job) => (
            <article className="job" key={job.id}>
              <h3>{job.title}</h3>
              <p>{job.company}</p>
              <p>{job.location || "Location not specified"}</p>
              {job.source && <p>Source: {job.source}</p>}
              {job.job_url && (
                <a href={job.job_url} target="_blank" rel="noreferrer">
                  Original job listing
                </a>
              )}
            </article>
          ))}
        </div>
      </section>

      <section>
        <h2>Candidate recommendations</h2>

        <form
          onSubmit={(event) => {
            event.preventDefault();
            void loadCandidateAndRecommendations();
          }}
        >
          <label htmlFor="candidateId">Candidate ID</label>
          <input
            id="candidateId"
            type="number"
            min="1"
            required
            value={candidateId}
            onChange={(event) => setCandidateId(event.target.value)}
            placeholder="Enter an existing candidate ID"
          />

          <button type="submit" disabled={loadingCandidate}>
            {loadingCandidate ? "Loading profile..." : "Load recommendations"}
          </button>
        </form>

        {candidate && (
          <article className="job">
            <h3>{candidate.full_name}</h3>
            <p>{candidate.email}</p>
            <p>Target role: {candidate.target_role || "Not specified"}</p>
            <p>Skills: {candidate.skills?.join(", ") || "No skills listed"}</p>

            <button
              type="button"
              onClick={() => {
                setFullName(candidate.full_name);
                setEmail(candidate.email);
                setTargetRole(candidate.target_role || "");
                setSkillsInput(candidate.skills?.join(", ") || "");
                setMessage("Profile loaded into the form for editing.");
              }}
            >
              Edit profile
            </button>
          </article>
        )}

        {candidate && recommendations.length === 0 && !loadingCandidate && (
          <p>No matching recommendations were returned for this candidate.</p>
        )}

        <div className="job-list">
          {recommendations.map((job) => (
            <article className="job" key={job.id}>
              <h3>{job.title}</h3>
              <p>{job.company}</p>
              <p>{job.location || "Location not specified"}</p>
              <p>Match score: {job.match_score}%</p>
              <p>Matching skills: {job.matching_skills?.join(", ") || "None listed"}</p>
              <p>Missing skills: {job.missing_skills?.join(", ") || "None listed"}</p>
              {job.explanation && <p>{job.explanation}</p>}
              {job.job_url && (
                <a href={job.job_url} target="_blank" rel="noreferrer">
                  Original job listing
                </a>
              )}
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

export default App;