"""Skill vocabulary, aliases, learning resources and sample data."""
from urllib.parse import quote_plus

SKILLS = {
    "Programming Languages": ["python", "java", "javascript", "typescript", "c++", "c#", "golang", "rust",
                              "php", "ruby", "kotlin", "swift", "scala", "matlab", "bash", "dart"],
    "Web Development": ["html", "css", "react", "angular", "vue", "node.js", "express", "django", "flask",
                        "fastapi", "spring boot", "asp.net", "rest api", "graphql", "tailwind", "bootstrap",
                        "next.js", "wordpress"],
    "Data & Databases": ["sql", "mysql", "postgresql", "mongodb", "sqlite", "redis", "oracle", "firebase",
                         "elasticsearch", "data modeling", "etl", "nosql"],
    "Data Science & AI": ["machine learning", "deep learning", "nlp", "computer vision", "pandas", "numpy",
                          "scikit-learn", "tensorflow", "pytorch", "keras", "opencv", "data analysis",
                          "data visualization", "statistics", "feature engineering", "spark", "hadoop",
                          "matplotlib", "seaborn", "streamlit", "jupyter", "generative ai", "llm"],
    "BI & Analytics": ["power bi", "tableau", "excel", "looker", "google analytics", "a/b testing"],
    "Cloud & DevOps": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins", "ci/cd",
                       "linux", "git", "github", "gitlab", "ansible", "nginx", "microservices"],
    "Mobile": ["android", "ios", "flutter", "react native", "xamarin"],
    "Security & Networking": ["cybersecurity", "penetration testing", "networking", "tcp/ip", "cryptography",
                              "owasp", "siem", "firewall"],
    "Testing & Practices": ["unit testing", "pytest", "selenium", "junit", "agile", "scrum", "jira",
                            "tdd", "code review", "object-oriented programming", "data structures",
                            "algorithms", "design patterns"],
    "Soft Skills": ["communication", "teamwork", "problem solving", "leadership", "time management",
                    "critical thinking", "presentation", "adaptability", "collaboration"],
}

ALIASES = {
    "js": "javascript", "ts": "typescript", "reactjs": "react", "react.js": "react", "vuejs": "vue",
    "vue.js": "vue", "nodejs": "node.js", "node": "node.js", "sklearn": "scikit-learn", "scikit learn": "scikit-learn",
    "postgres": "postgresql", "mongo": "mongodb", "k8s": "kubernetes", "amazon web services": "aws",
    "google cloud": "gcp", "natural language processing": "nlp", "tf": "tensorflow", "cpp": "c++",
    "oop": "object-oriented programming", "object oriented programming": "object-oriented programming",
    "restful": "rest api", "rest apis": "rest api", "restful api": "rest api", "ms excel": "excel",
    "microsoft excel": "excel", "powerbi": "power bi", "go lang": "golang", "ci cd": "ci/cd",
    "problem-solving": "problem solving", "team work": "teamwork", "large language models": "llm",
    "dsa": "data structures", "springboot": "spring boot", "data viz": "data visualization",
}

SKILL_TO_CATEGORY = {s: c for c, lst in SKILLS.items() for s in lst}

# Free, official or well-known learning resources: skill -> (label, url)
RESOURCES = {
    "python": ("Official Python Tutorial", "https://docs.python.org/3/tutorial/"),
    "sql": ("SQLBolt interactive lessons", "https://sqlbolt.com/"),
    "git": ("Pro Git (free book)", "https://git-scm.com/book/en/v2"),
    "docker": ("Docker Get Started", "https://docs.docker.com/get-started/"),
    "kubernetes": ("Kubernetes Basics", "https://kubernetes.io/docs/tutorials/kubernetes-basics/"),
    "pandas": ("pandas: 10 minutes to pandas", "https://pandas.pydata.org/docs/user_guide/10min.html"),
    "numpy": ("NumPy Quickstart", "https://numpy.org/doc/stable/user/quickstart.html"),
    "scikit-learn": ("scikit-learn Tutorials", "https://scikit-learn.org/stable/tutorial/index.html"),
    "tensorflow": ("TensorFlow Tutorials", "https://www.tensorflow.org/tutorials"),
    "pytorch": ("PyTorch Tutorials", "https://pytorch.org/tutorials/"),
    "react": ("React Learn", "https://react.dev/learn"),
    "html": ("MDN Learn Web Development", "https://developer.mozilla.org/en-US/docs/Learn"),
    "css": ("MDN Learn Web Development", "https://developer.mozilla.org/en-US/docs/Learn"),
    "javascript": ("javascript.info", "https://javascript.info/"),
    "typescript": ("TypeScript Handbook", "https://www.typescriptlang.org/docs/handbook/intro.html"),
    "django": ("Django Official Tutorial", "https://docs.djangoproject.com/en/stable/intro/tutorial01/"),
    "flask": ("Flask Quickstart", "https://flask.palletsprojects.com/en/stable/quickstart/"),
    "fastapi": ("FastAPI Tutorial", "https://fastapi.tiangolo.com/tutorial/"),
    "streamlit": ("Streamlit Docs", "https://docs.streamlit.io/get-started"),
    "mongodb": ("MongoDB University (free)", "https://learn.mongodb.com/"),
    "postgresql": ("PostgreSQL Tutorial", "https://www.postgresqltutorial.com/"),
    "linux": ("Linux Journey", "https://linuxjourney.com/"),
    "aws": ("AWS Skill Builder (free tier)", "https://skillbuilder.aws/"),
    "azure": ("Microsoft Learn: Azure", "https://learn.microsoft.com/training/azure/"),
    "power bi": ("Microsoft Learn: Power BI", "https://learn.microsoft.com/training/powerplatform/power-bi"),
    "tableau": ("Tableau Free Training Videos", "https://www.tableau.com/learn/training"),
    "machine learning": ("Google ML Crash Course", "https://developers.google.com/machine-learning/crash-course"),
    "deep learning": ("fast.ai Practical Deep Learning", "https://course.fast.ai/"),
    "nlp": ("Hugging Face NLP Course", "https://huggingface.co/learn/nlp-course"),
    "statistics": ("Khan Academy Statistics", "https://www.khanacademy.org/math/statistics-probability"),
    "agile": ("Scrum Guide", "https://scrumguides.org/"),
    "scrum": ("Scrum Guide", "https://scrumguides.org/"),
    "pytest": ("pytest Getting Started", "https://docs.pytest.org/en/stable/getting-started.html"),
    "data structures": ("CS50 (free)", "https://cs50.harvard.edu/x/"),
    "algorithms": ("CS50 (free)", "https://cs50.harvard.edu/x/"),
}

CATEGORY_TIPS = {
    "Soft Skills": "Add concrete examples (projects, clubs, volunteering) that demonstrate this skill on your CV.",
}


def get_resources(skill):
    """Return list of (label, url) for a skill, with generic free fallbacks."""
    out = []
    if skill in RESOURCES:
        out.append(RESOURCES[skill])
    out.append((f"Search free tutorials for '{skill}' on YouTube",
                f"https://www.youtube.com/results?search_query={quote_plus('learn ' + skill + ' beginner tutorial')}"))
    out.append(("freeCodeCamp", f"https://www.freecodecamp.org/news/search/?query={quote_plus(skill)}"))
    return out


SAMPLE_CV = """Aisha Perera
Computer Science Undergraduate | Colombo, Sri Lanka

SUMMARY
Final-year student passionate about data analysis and web development, with strong teamwork and communication skills.

SKILLS
Python, Java, SQL, MySQL, HTML, CSS, JavaScript, Pandas, NumPy, Matplotlib, Git, GitHub, Excel, Flask, Object Oriented Programming, Data Structures

PROJECTS
- Student Performance Predictor: used Python, pandas and scikit-learn for machine learning and data visualization.
- Campus Event Portal: built a Flask web app with MySQL and REST API endpoints; worked in an Agile team.

EDUCATION
BSc (Hons) in Computer Science, expected 2026
"""

SAMPLE_JD = """Junior Data Scientist

We are looking for a motivated Junior Data Scientist to join our analytics team.

Responsibilities:
- Clean and analyze large datasets using Python, pandas and SQL
- Build machine learning models with scikit-learn and TensorFlow
- Create dashboards using Power BI or Tableau
- Deploy models using Docker and AWS
- Collaborate in an Agile team and present findings to stakeholders

Requirements:
- Knowledge of statistics, data visualization and feature engineering
- Experience with Git and Linux
- Strong problem solving and communication skills
- Familiarity with NLP or deep learning is a plus
"""
