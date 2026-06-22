# DPal 🔗

**Where Palestinian developers build in the open.**

DPal is a professional networking platform built specifically for developers in Gaza and Palestine. It brings together developer profiles, projects, skills, and collaborations in one place — making it easier to showcase work, find collaborators, and grow professionally.

> DPal bridges the gap between talented Palestinian developers and the global tech community — one project at a time.

---

## ✨ Features

- **Developer Profiles** — bio, skills, location, GitHub link, and avatar
- **Project Showcase** — post projects as Solo or Team, with tech stack, GitHub link, and image
- **Team Collaboration** — credit multiple contributors on a single project
- **Community Engagement** — like, comment, and share any project (AJAX, no page reload)
- **Skill-Based Discovery** — filter developers and projects by technology
- **GitHub Sign-In** — log in instantly with a GitHub account, no registration form required
- **Secure Authentication** — Bcrypt password hashing, session-based authorization, CSRF protection
- **REST API** — public JSON endpoints for project data

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django (Python) |
| Database | SQLite (dev) — MySQL-ready |
| Frontend | HTML5, CSS3, JavaScript |
| Auth | Bcrypt + Django Sessions + GitHub OAuth |
| AJAX | Vanilla JavaScript / Fetch API |
| Image handling | Pillow |

---

## 📁 Project Structure

```
dpal/
├── dpal/                   # Project settings & root URLs
│   ├── settings.py
│   └── urls.py
│
├── users_app/                 # Users, auth, profiles, GitHub OAuth
│   ├── models.py             (User, Skill, UserSkill, Follow)
│   ├── views.py
│   ├── urls.py
│   └── templates/users_app/
│       ├── landing.html
│       ├── index.html         (Sign in / Register)
│       ├── profile.html
│       ├── developers.html
│       ├── about.html
│       └── complete_profile.html
│
├── projects_app/              # Projects, likes, comments, shares
│   ├── models.py             (Project, Contributor, Comment, Like, Share)
│   ├── views.py
│   ├── urls.py
│   └── templates/projects_app/
│       ├── dashboard.html
│       ├── project_detail.html
│       └── edit_project.html
│
├── media/                      # Uploaded avatars & project images
├── static/                     # CSS files
├── db.sqlite3
└── manage.py
```

---

## 🗺️ Pages

| Page | URL | Description |
|---|---|---|
| Landing | `/` | Public marketing page |
| Sign in / Register | `/auth` | Auth page with two forms + GitHub sign-in |
| Dashboard / Feed | `/dashboard` | All projects, search, filter, composer |
| Project Detail | `/project/<id>` | Full project info, contributors, comments, likes, shares |
| Developer Profile | `/profile/<id>` | Bio, skills, own projects, contributions, liked projects |
| Developers Directory | `/developers` | Browse and filter developers by skill |
| About | `/about` | Platform mission and team |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/projects/` | All projects as JSON |
| `GET` | `/api/projects/<id>/` | Single project as JSON |
| `POST` | `/api/projects/<id>/like/` | Like / unlike a project (AJAX) |
| `POST` | `/api/projects/<id>/comment/` | Add a comment (AJAX) |
| `POST` | `/api/projects/<id>/share/` | Share a project (AJAX) |

---

## 🗄️ Data Model (ERD Summary)

| Entity | Description |
|---|---|
| **User** | Registered developer — profile, skills, GitHub link |
| **Project** | Solo or team project posted by a developer |
| **Contributor** | Junction table — credits multiple developers on a team project |
| **Comment** | A comment left on a project by any user |
| **Like** | A like given by any user to any project |
| **Share** | A share action by any user on any project |
| **Skill** / **UserSkill** | Many-to-many relationship between developers and skills |
| **Follow** | Many-to-many relationship between developers (peer following) |

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/dpal.git
cd dpal
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies

```bash
pip install django bcrypt pillow requests
```

### 4. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Start the server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** in your browser.

---

## 🔑 GitHub Sign-In Setup (optional)

DPal supports signing in with GitHub instead of creating a password.

1. Go to **GitHub → Settings → Developer settings → OAuth Apps → New OAuth App**
2. Set:
   - **Homepage URL:** `http://127.0.0.1:8000`
   - **Authorization callback URL:** `http://127.0.0.1:8000/auth/github/callback/`
3. Copy the **Client ID** and **Client Secret** into `dpal/settings.py`:

```python
GITHUB_CLIENT_ID = 'your_client_id_here'
GITHUB_CLIENT_SECRET = 'your_client_secret_here'
GITHUB_CALLBACK_URL = 'http://127.0.0.1:8000/auth/github/callback/'
```

> ⚠️ Never commit real credentials to GitHub. Use environment variables or a `.env` file (excluded via `.gitignore`) in production.

---

## 🐬 Switching to MySQL

Replace the `DATABASES` block in `dpal/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dpal',
        'USER': 'root',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

Then:

```bash
pip install mysqlclient
python manage.py makemigrations
python manage.py migrate
```

---

## 🌱 Seed Sample Data

```bash
python manage.py shell
```

```python
import bcrypt
from users_app.models import User, Skill, UserSkill
from projects_app.models import Project, Contributor, Comment, Like

pw = bcrypt.hashpw('password123'.encode(), bcrypt.gensalt()).decode()

dalya = User.objects.create(full_name='Dalya Muhaisen', email='dalya@gmail.com', password=pw, bio='Building tools for my community.', role_title='Full-stack developer', location='Gaza')
omar  = User.objects.create(full_name='Ali Nasser', email='ali@gmail.com', password=pw, role_title='Backend engineer', location='Khan Younis')

for name in ['Django', 'React', 'PostgreSQL', 'Docker', 'Python']:
    Skill.objects.get_or_create(name=name)

UserSkill.objects.get_or_create(user=dalya, skill=Skill.objects.get(name='Django'))

p1 = Project.objects.create(title='Gaza Transit API', description='Open, realtime public-transit data for Gaza City.', tech_stack='Django, PostgreSQL, React', project_type='team', owner=dalya)
Contributor.objects.create(project=p1, user=omar)
Like.objects.create(user=omar, project=p1)
Comment.objects.create(content='This is exactly what the ecosystem needs!', user=omar, project=p1)

print("Seed complete! Login: dalya@gmail.com / password123")
```

---

## ✅ Project Requirements Checklist

- [x] 5+ pages (Login/Register, Dashboard, Project Detail, Profile, Developers, About)
- [x] Responsive design
- [x] AJAX (like, comment, share — no page reload)
- [x] Bcrypt password hashing
- [x] Session-based authorization
- [x] CSRF protection
- [x] Full CRUD (Create, Read, Update, Delete projects)
- [x] Public REST API (`/api/projects/`)
- [x] GitHub OAuth sign-in
- [ ] MySQL in production *(currently SQLite for local development)*
- [ ] AWS deployment *(pending)*

---

## 👩‍💻 Author

**Dalya Muhaisen**
Software Engineer · Gaza, Palestine 🇵🇸
Axsos Academy — Full-Stack Django Project, 2026


<img width="1891" height="910" alt="Screenshot (374)" src="https://github.com/user-attachments/assets/c6285966-16da-4364-9449-5d8ce1fd66b1" />

<img width="1896" height="936" alt="Screenshot (375)" src="https://github.com/user-attachments/assets/6dfa26b3-102c-4bdc-9767-0fdb21199b11" />

<img width="1905" height="885" alt="Screenshot (376)" src="https://github.com/user-attachments/assets/17fdb54d-afd9-4189-bd68-c3cdf309fe79" />
<img width="1842" height="873" alt="Screenshot (379)" src="https://github.com/user-attachments/assets/01114140-77f1-467a-b370-cbac3586c6b7" />
<img width="1888" height="916" alt="Screenshot (378)" src="https://github.com/user-attachments/assets/1a254ac7-86d5-4a7c-8878-695f5648f7f1" />
<img width="1885" height="939" alt="Screenshot (377)" src="https://github.com/user-attachments/assets/0ed7287b-101a-40b8-86b6-5a34b8632efb" />
