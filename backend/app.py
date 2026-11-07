import os
import re
import sqlite3
from functools import wraps

from flask import Flask, request, jsonify, g
from flask_cors import CORS

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from itsdangerous import (
    URLSafeTimedSerializer,
    BadSignature,
    SignatureExpired
)

from docx import Document
from PyPDF2 import PdfReader

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# =====================================
# APPLICATION CONFIGURATION
# =====================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SMARTHIRE_SECRET_KEY",
    "smarthire-local-development-secret-change-before-deployment"
)

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

CORS(app)

serializer = URLSafeTimedSerializer(
    app.config["SECRET_KEY"]
)

DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "smarthire.db"
)

TOKEN_LIFETIME = 7 * 24 * 60 * 60


# =====================================
# DATABASE
# =====================================

def get_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT NOT NULL UNIQUE,

            password_hash TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    connection.commit()

    connection.close()


initialize_database()


# =====================================
# USER HELPERS
# =====================================

def public_user(user):

    return {

        "id": user["id"],

        "name": user["name"],

        "email": user["email"]

    }


def create_token(user_id):

    return serializer.dumps(
        str(user_id),
        salt="smarthire-auth-token"
    )


def token_required(function):

    @wraps(function)
    def decorated(*args, **kwargs):

        authorization = request.headers.get(
            "Authorization", ""
        )

        if not authorization.startswith("Bearer "):

            return jsonify({
                "error": "Please log in to continue."
            }), 401

        token = authorization.split(" ", 1)[1]

        try:

            user_id = serializer.loads(
                token,
                salt="smarthire-auth-token",
                max_age=TOKEN_LIFETIME
            )

        except SignatureExpired:

            return jsonify({
                "error": "Your session has expired. Please log in again."
            }), 401

        except BadSignature:

            return jsonify({
                "error": "Invalid authentication token."
            }), 401

        except Exception:

            return jsonify({
                "error": "Authentication failed."
            }), 401


        connection = get_connection()

        user = connection.execute(
            "SELECT id, name, email FROM users WHERE id = ?",
            (int(user_id),)
        ).fetchone()

        connection.close()

        if not user:

            return jsonify({
                "error": "User account not found."
            }), 401

        g.current_user = user

        return function(*args, **kwargs)

    return decorated


# =====================================
# SIGNUP API
# =====================================

@app.route("/api/auth/signup", methods=["POST"])
def signup():

    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()

    email = str(data.get("email", "")).strip().lower()

    password = str(data.get("password", ""))


    if not name or not email or not password:

        return jsonify({
            "error": "Please fill in all required fields."
        }), 400


    if len(name) > 100:

        return jsonify({
            "error": "Name must be 100 characters or fewer."
        }), 400


    if not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        email
    ):

        return jsonify({
            "error": "Please enter a valid email address."
        }), 400


    if len(email) > 254:

        return jsonify({
            "error": "Email address is too long."
        }), 400


    if len(password) < 8:

        return jsonify({
            "error": "Password must contain at least 8 characters."
        }), 400


    if len(password) > 128:

        return jsonify({
            "error": "Password is too long."
        }), 400


    password_hash = generate_password_hash(password)

    connection = get_connection()

    try:

        cursor = connection.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (name, email, password_hash)
        )

        connection.commit()

        user_id = cursor.lastrowid

        user = connection.execute(
            "SELECT id, name, email FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        token = create_token(user_id)

        return jsonify({

            "status": "success",

            "message": "Account created successfully.",

            "token": token,

            "user": public_user(user)

        }), 201


    except sqlite3.IntegrityError:

        return jsonify({
            "error": "An account with this email already exists. Please log in."
        }), 409

    except Exception:

        app.logger.exception("Signup failed")

        return jsonify({
            "error": "Unable to create account."
        }), 500

    finally:

        connection.close()


# =====================================
# LOGIN API
# =====================================

@app.route("/api/auth/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()

    password = str(data.get("password", ""))


    if not email or not password:

        return jsonify({
            "error": "Enter your email and password."
        }), 400


    connection = get_connection()

    user = connection.execute(
        """
        SELECT id, name, email, password_hash
        FROM users
        WHERE email = ?
        """,
        (email,)
    ).fetchone()

    connection.close()


    if not user or not check_password_hash(
        user["password_hash"],
        password
    ):

        return jsonify({
            "error": "Incorrect email or password."
        }), 401


    token = create_token(user["id"])

    return jsonify({

        "status": "success",

        "message": "Login successful.",

        "token": token,

        "user": public_user(user)

    })


# =====================================
# CURRENT USER API
# =====================================

@app.route("/api/auth/me", methods=["GET"])
@token_required
def current_user():

    return jsonify({

        "status": "success",

        "user": public_user(g.current_user)

    })


# =====================================
# HEALTH CHECK
# =====================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({

        "status": "success",

        "message": "SmartHire backend is running."

    })


# =====================================
# JOB DATABASE
# =====================================

JOBS = [

    {
        "title": "Python Developer",
        "category": "Software Development",
        "company": "Sample Job Profile",
        "location": "India",
        "experience": "0-2 Years",
        "skills": [
            "Python", "SQL", "Flask",
            "Django", "REST API", "Git"
        ],
        "description": """
        Python development, Flask, Django,
        SQL, REST APIs, backend development and Git.
        """
    },

    {
        "title": "Data Analyst",
        "category": "Data Analytics",
        "company": "Sample Job Profile",
        "location": "India",
        "experience": "0-2 Years",
        "skills": [
            "Python", "SQL", "Excel",
            "Power BI", "Statistics", "Pandas"
        ],
        "description": """
        Data analysis, Python, SQL,
        Excel, Power BI, statistics and Pandas.
        """
    },

    {
        "title": "Machine Learning Engineer",
        "category": "Artificial Intelligence",
        "company": "Sample Job Profile",
        "location": "India",
        "experience": "0-2 Years",
        "skills": [
            "Python", "Machine Learning",
            "Scikit-learn", "NumPy",
            "Pandas", "Deep Learning"
        ],
        "description": """
        Machine learning, Python, model training,
        Scikit-learn, NumPy, Pandas and deep learning.
        """
    },

    {
        "title": "Frontend Developer",
        "category": "Web Development",
        "company": "Sample Job Profile",
        "location": "India",
        "experience": "0-2 Years",
        "skills": [
            "HTML", "CSS", "JavaScript",
            "React", "Git", "Responsive Design"
        ],
        "description": """
        Frontend development, HTML, CSS,
        JavaScript, React and responsive websites.
        """
    },

    {
        "title": "Backend Developer",
        "category": "Software Development",
        "company": "Sample Job Profile",
        "location": "India",
        "experience": "0-2 Years",
        "skills": [
            "Python", "Java", "SQL",
            "Flask", "REST API", "Git"
        ],
        "description": """
        Backend development, APIs, databases,
        Python, Java, SQL, Flask and Git.
        """
    },

    {
        "title": "Java Developer",
        "category": "Software Development",
        "company": "Sample Job Profile",
        "location": "India",
        "experience": "0-2 Years",
        "skills": [
            "Java", "SQL", "OOP",
            "Data Structures", "Spring Boot", "Git"
        ],
        "description": """
        Java programming, Spring Boot,
        OOP, SQL and data structures.
        """
    },

    {
        "title": "Data Scientist",
        "category": "Data Science",
        "company": "Sample Job Profile",
        "location": "India",
        "experience": "0-2 Years",
        "skills": [
            "Python", "Machine Learning",
            "Statistics", "Pandas",
            "NumPy", "Data Visualization"
        ],
        "description": """
        Data science, machine learning, statistics,
        Python, Pandas, NumPy and predictive analytics.
        """
    },

    {
        "title": "NLP Engineer",
        "category": "Artificial Intelligence",
        "company": "Sample Job Profile",
        "location": "India",
        "experience": "0-2 Years",
        "skills": [
            "Python", "NLP", "Machine Learning",
            "Scikit-learn", "Deep Learning", "TensorFlow"
        ],
        "description": """
        Natural language processing, text processing,
        Python, machine learning and deep learning.
        """
    }

]


# =====================================
# SKILL CATEGORIES
# =====================================

SKILL_CATEGORIES = {

    "Programming Languages": [
        "Python", "Java", "JavaScript", "C++", "C"
    ],

    "Web Development": [
        "HTML", "CSS", "React", "Node.js",
        "Flask", "Django", "Spring Boot",
        "REST API", "Responsive Design"
    ],

    "Databases": [
        "SQL", "MySQL", "PostgreSQL",
        "MongoDB", "SQLite"
    ],

    "Data Analytics": [
        "Excel", "Power BI", "Tableau",
        "Statistics", "Pandas", "NumPy",
        "Data Visualization"
    ],

    "Artificial Intelligence": [
        "Machine Learning", "Scikit-learn",
        "Deep Learning", "NLP",
        "TensorFlow", "PyTorch"
    ],

    "Tools": [
        "Git", "GitHub", "Docker",
        "AWS", "Linux", "Jupyter"
    ],

    "Core Computer Science": [
        "Data Structures", "OOP",
        "Operating Systems", "Computer Networks", "DBMS"
    ]

}


ALL_SKILLS = [
    skill
    for skills in SKILL_CATEGORIES.values()
    for skill in skills
]


# =====================================
# RESUME SECTIONS
# =====================================

RESUME_SECTIONS = {

    "Summary": [
        "summary", "professional summary",
        "career objective", "objective"
    ],

    "Education": [
        "education", "academic background", "qualifications"
    ],

    "Experience": [
        "experience", "work experience",
        "internship", "employment history"
    ],

    "Projects": [
        "projects", "academic projects", "personal projects"
    ],

    "Skills": [
        "skills", "technical skills", "key skills"
    ],

    "Certifications": [
        "certifications", "certificates", "courses"
    ]

}


# =====================================
# RESUME TEXT EXTRACTION
# =====================================

def extract_resume(file):

    filename = file.filename.lower()

    if filename.endswith(".pdf"):

        reader = PdfReader(file.stream)

        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )


    if filename.endswith(".docx"):

        document = Document(file.stream)

        paragraphs = [
            p.text
            for p in document.paragraphs
            if p.text.strip()
        ]

        for table in document.tables:

            for row in table.rows:

                paragraphs.append(
                    " ".join(
                        cell.text for cell in row.cells
                    )
                )

        return "\n".join(paragraphs)


    raise ValueError("Only PDF and DOCX files are supported.")


# =====================================
# SKILL DETECTION
# =====================================

def detect_skills(text):

    detected = []

    normalized = text.lower()

    for skill in ALL_SKILLS:

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(skill.lower())
            + r"(?![a-z0-9])"
        )

        if re.search(pattern, normalized):

            detected.append(skill)

    return detected


def categorize_skills(detected):

    result = {}

    detected_set = set(detected)

    for category, skills in SKILL_CATEGORIES.items():

        matched = [
            skill for skill in skills
            if skill in detected_set
        ]

        if matched:

            result[category] = matched

    return result


# =====================================
# SECTION DETECTION
# =====================================

def detect_sections(text):

    lines = [
        re.sub(r"[^a-z0-9 ]", " ", line.lower()).strip()
        for line in text.splitlines()
    ]

    detected = []

    for section, aliases in RESUME_SECTIONS.items():

        found = False

        for alias in aliases:

            for line in lines:

                if (
                    line == alias
                    or line.startswith(alias + " ")
                ):

                    found = True
                    break

            if found:
                break

        if found:
            detected.append(section)

    missing = [
        section
        for section in RESUME_SECTIONS
        if section not in detected
    ]

    return detected, missing


# =====================================
# CONTACT EXTRACTION
# =====================================

def extract_contact(text):

    email = re.search(
        r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
        text,
        re.I
    )

    phone = re.search(
        r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)",
        text
    )

    return {

        "email": email.group(0) if email else None,

        "phone": phone.group(0) if phone else None

    }


# =====================================
# RESUME COMPLETENESS SCORE
# =====================================

def calculate_resume_score(
    text,
    word_count,
    skills,
    sections,
    contact
):

    section_score = (
        len(sections) / len(RESUME_SECTIONS)
    ) * 30


    contact_score = 0

    if contact["email"]:
        contact_score += 5

    if contact["phone"]:
        contact_score += 5


    skill_score = min(
        len(skills) / 8,
        1
    ) * 20


    if 200 <= word_count <= 900:
        length_score = 15

    elif 120 <= word_count < 200:
        length_score = 10

    elif 900 < word_count <= 1200:
        length_score = 10

    elif 80 <= word_count < 120:
        length_score = 6

    else:
        length_score = 3


    metric_pattern = re.compile(
        r"\b\d+(?:\.\d+)?\s*"
        r"(?:%|percent\b|users?\b|customers?\b|"
        r"projects?\b|records?\b|hours?\b|"
        r"days?\b|weeks?\b|months?\b|years?\b)",
        re.I
    )

    quantified_lines = [
        line for line in text.splitlines()
        if metric_pattern.search(line)
    ]

    impact_score = min(
        len(quantified_lines),
        3
    ) * 5


    action_verbs = [
        "developed", "implemented", "created",
        "designed", "built", "managed",
        "analyzed", "improved", "optimized",
        "automated", "tested", "deployed",
        "led", "delivered", "engineered", "trained"
    ]

    detected_actions = [
        verb for verb in action_verbs
        if re.search(r"\b" + verb + r"\b", text, re.I)
    ]

    if len(detected_actions) >= 4:
        action_score = 10

    elif len(detected_actions) >= 2:
        action_score = 7

    elif len(detected_actions) == 1:
        action_score = 4

    else:
        action_score = 0


    total = round(
        section_score
        + contact_score
        + skill_score
        + length_score
        + impact_score
        + action_score
    )

    total = max(0, min(100, total))


    if total >= 80:
        label = "Strong completeness"

    elif total >= 60:
        label = "Good completeness"

    elif total >= 40:
        label = "Needs improvement"

    else:
        label = "Incomplete resume"


    recommendations = []


    if not contact["email"]:
        recommendations.append(
            "Add a professional email address."
        )

    if not contact["phone"]:
        recommendations.append(
            "Add a contact phone number."
        )

    for section in RESUME_SECTIONS:

        if section not in sections:
            recommendations.append(
                f"Add a clearly labeled {section} section when relevant."
            )

    if len(skills) < 5:
        recommendations.append(
            "Include relevant technical skills you genuinely possess."
        )

    if word_count < 120:
        recommendations.append(
            "Add more relevant details about your education, "
            "experience and projects."
        )

    elif word_count > 1200:
        recommendations.append(
            "Remove repetitive or unnecessary content."
        )

    if impact_score < 15:
        recommendations.append(
            "Include measurable project or work results "
            "where you have genuine evidence."
        )

    if action_score < 10:
        recommendations.append(
            "Use strong action verbs in your experience and project descriptions."
        )

    if not recommendations:
        recommendations.append(
            "Your resume has good structural completeness. "
            "Continue improving role-specific achievements."
        )


    return {

        "score": total,

        "label": label,

        "breakdown": {

            "section_completeness": round(section_score, 1),

            "contact_information": round(contact_score, 1),

            "skill_coverage": round(skill_score, 1),

            "content_length": length_score,

            "quantified_achievements": impact_score,

            "action_verbs": action_score

        },

        "recommendations": recommendations,

        "methodology": (
            "Rule-based resume completeness score. "
            "This is not an ATS score or hiring probability."
        )

    }


# =====================================
# JOB RECOMMENDATION ENGINE
# =====================================

def rank_jobs(resume_text, detected_skills):

    documents = [

        " ".join([
            job["title"],
            job["category"],
            " ".join(job["skills"]),
            job["description"]
        ])

        for job in JOBS

    ]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True
    )

    job_matrix = vectorizer.fit_transform(documents)

    resume_vector = vectorizer.transform([resume_text])

    similarities = cosine_similarity(
        resume_vector,
        job_matrix
    )[0]

    skill_set = set(detected_skills)

    results = []

    for index, job in enumerate(JOBS):

        required = job["skills"]

        matched = [
            skill for skill in required
            if skill in skill_set
        ]

        missing = [
            skill for skill in required
            if skill not in skill_set
        ]

        coverage = (
            len(matched) / len(required) * 100
            if required else 0
        )

        similarity = float(similarities[index] * 100)

        score = (
            0.70 * similarity
            + 0.30 * coverage
        )

        results.append({

            "title": job["title"],
            "category": job["category"],
            "company": job["company"],
            "location": job["location"],
            "experience": job["experience"],

            "match_score": round(score, 1),

            "text_similarity": round(similarity, 1),

            "skill_coverage": round(coverage, 1),

            "matched_skills": matched,

            "missing_skills": missing

        })

    return sorted(
        results,
        key=lambda item: item["match_score"],
        reverse=True
    )[:5]


# =====================================
# RESUME ANALYSIS API
# =====================================

@app.route("/api/analyze", methods=["POST"])
@token_required
def analyze_resume():

    if "resume" not in request.files:

        return jsonify({
            "error": "Please upload your resume."
        }), 400

    file = request.files["resume"]

    if not file.filename:
        return jsonify({
            "error": "No file selected."
        }), 400

    try:

        text = extract_resume(file)

        text = re.sub(r"[\t\r]+", " ", text)

        text = re.sub(r"[ ]{2,}", " ", text).strip()

        if len(text) < 40:

            return jsonify({
                "error": (
                    "Insufficient text extracted. "
                    "Scanned PDFs require OCR."
                )
            }), 422


        word_count = len(
            re.findall(r"\b\w+\b", text)
        )

        contact = extract_contact(text)

        detected = detect_skills(text)

        skills_by_category = categorize_skills(detected)

        detected_sections, missing_sections = detect_sections(text)


        resume_score = calculate_resume_score(
            text,
            word_count,
            detected,
            detected_sections,
            contact
        )


        jobs = rank_jobs(text, detected)

        top_role = (
            jobs[0]["title"]
            if jobs else "Not enough evidence"
        )


        improvement_plan = []

        if jobs:

            for skill in jobs[0]["missing_skills"]:

                improvement_plan.append(
                    f"Develop practical experience in {skill} "
                    f"for the {top_role} role."
                )


        improvement_plan.extend(
            resume_score["recommendations"]
        )


        return jsonify({

            "status": "success",

            "resume_filename": file.filename,

            "character_count": len(text),

            "word_count": word_count,

            "contact": contact,

            "detected_sections": detected_sections,

            "missing_sections": missing_sections,

            "detected_skills": detected,

            "skills_by_category": skills_by_category,

            "resume_score": resume_score,

            "top_matching_role": top_role,

            "recommended_jobs": jobs,

            "improvement_plan": improvement_plan,

            "dataset_note": (
                "Prototype uses 8 sample job profiles. "
                "Scores are similarity-based, not hiring probabilities."
            )

        })


    except Exception:

        app.logger.exception("Resume analysis failed")

        return jsonify({
            "error": "Unable to process this resume. Check the file and try again."
        }), 500


# =====================================
# FILE SIZE ERROR
# =====================================

@app.errorhandler(413)
def file_too_large(error):

    return jsonify({
        "error": "Maximum resume size is 10 MB."
    }), 413


# =====================================
# RUN SERVER
# =====================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )