from flask import Flask, render_template, request, redirect, session, flash
from db import get_db, Base, engine
import models
import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from pypdf import PdfReader
import docx
from typing import Dict, List, Any
import openai
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key_change_in_production")

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# OpenAI setup (optional)
try:
    openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    OPENAI_AVAILABLE = True
except Exception as e:
    print(f"OpenAI not available: {e}")
    openai_client = None
    OPENAI_AVAILABLE = False

Base.metadata.create_all(bind=engine)

# ---------------- SKILLS ----------------
ROLE_SKILLS = {
    "software engineer": [
        "python", "java", "c++", "javascript",
        "typescript", "golang", "rust", "kotlin",
        "data structures", "algorithms", "oop",
        "solid principles", "design patterns",
        "sql", "postgresql", "mysql", "mongodb",
        "git", "system design",
        "testing", "unit testing", "integration testing",
        "rest api", "graphql", "grpc",
        "microservices", "cloud", "security",
        "performance optimization", "debugging",
        "linux", "docker", "kubernetes",
        "ci/cd", "jenkins", "github actions",
        "aws", "gcp", "azure", "communication",
        "fastapi", "spring boot", "node", "react"
    ],
    "data scientist": [
        "python", "pandas", "numpy",
        "machine learning", "deep learning",
        "statistics", "sql", "postgresql",
        "data visualization", "matplotlib", "seaborn",
        "plotly", "feature engineering", "model evaluation",
        "data cleaning", "data engineering",
        "mlops", "big data", "spark", "hadoop",
        "communication", "visualization",
        "tensorflow", "pytorch", "scikit-learn",
        "jupyter", "git", "aws", "gcp",
        "docker", "tableau", "power bi",
        "experimental design", "a/b testing",
        "time series analysis", "nlp"
    ],
    "data analyst": [
        "excel", "sql", "power bi",
        "tableau", "python", "data analysis",
        "data cleaning", "statistics",
        "dashboarding", "reporting",
        "power query", "presentation",
        "communication", "data visualization",
        "postgresql", "mysql", "mongodb",
        "advanced excel", "vba", "python pandas",
        "looker", "google analytics", "amplitude",
        "cohort analysis", "retention analysis",
        "funnel analysis", "metric design",
        "git", "jupyter"
    ],
    "web developer": [
        "html", "css", "javascript",
        "react", "node", "mongodb",
        "responsive design", "typescript",
        "web accessibility", "ui/ux",
        "api integration", "webpack",
        "testing", "seo",
        "git", "graphql", "firebase",
        "next.js", "vue.js", "angular",
        "tailwind css", "bootstrap", "sass",
        "redux", "context api", "express",
        "postgresql", "mysql", "fastapi",
        "docker", "aws", "netlify", "vercel",
        "ci/cd", "github actions", "performance optimization",
        "web security", "http", "rest api"
    ],
    "machine learning engineer": [
        "python", "machine learning",
        "deep learning", "tensorflow",
        "pytorch", "nlp",
        "model deployment", "mlops",
        "data pipelines", "api development",
        "cloud", "feature engineering",
        "scikit-learn", "optimization",
        "statistics", "git", "computer vision",
        "reinforcement learning", "transformers",
        "hugging face", "sql", "postgresql",
        "fastapi", "docker", "kubernetes",
        "aws", "gcp", "spark", "hadoop"
    ],
    "ai engineer": [
        "python", "machine learning", "deep learning",
        "tensorflow", "pytorch", "nlp", "computer vision",
        "transformers", "hugging face", "langchain",
        "llm", "gpt", "prompt engineering",
        "reinforcement learning", "generative ai",
        "vector databases", "pinecone", "weaviate",
        "model deployment", "mlops", "api development",
        "fastapi", "cloud", "aws", "gcp",
        "docker", "kubernetes", "sql", "git",
        "git", "monitoring", "ethics", "data privacy"
    ],
    "devops engineer": [
        "linux", "docker", "kubernetes",
        "aws", "ci/cd", "ansible",
        "terraform", "monitoring",
        "jenkins", "bash scripting",
        "networking", "security",
        "cloud", "gcp", "azure", "prometheus",
        "grafana", "datadog", "helm", "vault",
        "postgresql", "mysql", "redis", "nginx",
        "apache", "istio", "istio service mesh",
        "argocd", "infrastructure as code", "cloudformation"
    ]
}

SKILL_NOTES = {
    "python": "Python is a versatile programming language used across web development, data science, automation, and AI. It is favored for its readable syntax, rich ecosystem of libraries, and strong community support. Learning Python opens doors to full-stack development, machine learning, scripting, and many automation tasks.",
    "java": "Java is a powerful object-oriented language widely used for enterprise systems, Android apps, and large-scale backend services. It emphasizes portability through the JVM, strong typing, and robust libraries. Java experience shows you can work on scalable distributed systems and backend architecture.",
    "c++": "C++ is a systems programming language prized for its performance and fine-grained control over memory. It is fundamental for game engines, embedded systems, and performance-critical applications. Understanding C++ helps you learn low-level concepts such as pointers, memory management, and optimization.",
    "javascript": "JavaScript drives modern web interactivity and is the main language of frontend development. It also powers backend services through Node.js, enabling full-stack development with one language. Mastery of JavaScript means you can build responsive web apps, browser experiences, and server APIs.",
    "data structures": "Data structures like arrays, linked lists, trees, and hash maps let you organize and access data efficiently. They are essential for solving technical interview problems and writing performant software. A strong understanding of data structures helps you select the right tool for each task.",
    "algorithms": "Algorithms define the step-by-step logic to solve problems and process data. Studying algorithms teaches you how to optimize solutions for speed and memory usage. This knowledge is critical for coding interviews and for designing high-quality, maintainable systems.",
    "oop": "Object-oriented programming uses classes, objects, inheritance, and encapsulation to structure software. It helps model real-world problems and build reusable, maintainable code. OOP skills are valuable in many languages and large application codebases.",
    "sql": "SQL is the standard language for interacting with relational databases. It lets you query, filter, join, and aggregate data to answer business questions. SQL proficiency is key for backend engineering, data analytics, and any role that works with structured data.",
    "git": "Git is the de facto version control system used by software teams worldwide. It enables branching, merging, and collaboration in code repositories. Knowing Git demonstrates you can manage changes, work in teams, and maintain a clean project history.",
    "system design": "System design is about planning scalable, reliable, and maintainable architectures for real-world applications. It covers topics like load balancing, caching, databases, and microservices. Good system design skills show you can build software that performs well under growth and complexity.",
    "pandas": "Pandas is a Python library for structured data analysis with DataFrame objects. It simplifies cleaning, transforming, and summarizing datasets. Data scientists and analysts use Pandas to prepare data for modeling, reporting, and visualization.",
    "numpy": "NumPy provides fast numerical array operations and mathematical functions in Python. It is the foundation for scientific computing, enabling vectorized computations and linear algebra. Learning NumPy helps you work efficiently with large datasets and numerical models.",
    "machine learning": "Machine learning teaches computers to learn patterns from data and make predictions. It includes supervised and unsupervised methods, feature engineering, and model evaluation. Skills here are essential for building predictive systems and data-driven products.",
    "deep learning": "Deep learning uses neural networks to solve complex problems like image recognition, language understanding, and speech processing. It relies on frameworks, GPUs, and large datasets. Experience with deep learning indicates you can build advanced AI applications.",
    "statistics": "Statistics helps you analyze data, infer trends, and make valid decisions under uncertainty. It includes probability, distributions, hypothesis testing, and sample analysis. Statistical knowledge improves your ability to interpret results and validate machine learning models.",
    "data visualization": "Data visualization turns raw data into meaningful charts and dashboards. It helps stakeholders understand trends, compare metrics, and discover insights quickly. Strong visualization skills make your analysis more persuasive and actionable.",
    "excel": "Excel is a core productivity tool for data entry, analysis, and reporting in many business settings. It offers formulas, pivot tables, and charting features for quick insights. Excel proficiency is often expected in analyst and operations roles.",
    "power bi": "Power BI is a Microsoft tool for building interactive reports and business intelligence dashboards. It connects to many data sources and supports visual analytics. Power BI knowledge shows you can turn data into executive-level decision support.",
    "tableau": "Tableau is a visual analytics platform for exploring and sharing data insights. It helps build dashboards, perform ad hoc analysis, and visualize complex data relationships. Tableau expertise is valuable in analytics, marketing, and reporting roles.",
    "data analysis": "Data analysis is the process of cleaning, exploring, and interpreting data to uncover patterns. It includes hypothesis testing, trend discovery, and summarizing findings. Data analysis skills are central to making data-driven business decisions.",
    "html": "HTML defines the structure of web pages with elements like headings, paragraphs, and links. It is the essential first step in creating any website. HTML knowledge allows you to build and understand web page layouts.",
    "css": "CSS controls the presentation of web pages, including layout, colors, fonts, and responsiveness. It enables polished and mobile-friendly user interfaces. CSS skills are essential for frontend developers and designers.",
    "react": "React is a JavaScript library for building component-based user interfaces and single-page applications. It simplifies building reusable UI pieces and managing state. React experience shows you can create modern, dynamic web applications.",
    "node": "Node.js allows you to run JavaScript on the server and build backend applications. It is commonly used for APIs, real-time services, and tooling. Node skills help bridge frontend and backend development in full-stack projects.",
    "mongodb": "MongoDB is a document-oriented NoSQL database that stores flexible JSON-like records. It is ideal for fast development and evolving schemas. MongoDB knowledge helps you build modern web apps with non-relational data.",
    "tensorflow": "TensorFlow is a framework for building and training machine learning and deep learning models. It supports neural networks, deployment, and production workflows. TensorFlow skills are useful for AI engineering and research projects.",
    "pytorch": "PyTorch is a deep learning library known for its dynamic computation graphs and research-friendly API. It is widely used in academia and production models. Learning PyTorch helps you prototype advanced neural networks quickly.",
    "nlp": "Natural Language Processing (NLP) enables machines to read, interpret, and generate human language. It includes tasks like sentiment analysis, translation, and text classification. NLP is a key area for AI products that work with text and speech.",
    "linux": "Linux is a common operating system for servers, cloud environments, and development workstations. Linux proficiency includes command-line tools, shell scripting, and system administration. These skills are essential for DevOps and infrastructure roles.",
    "docker": "Docker packages applications into containers that run consistently across environments. It simplifies deployment, testing, and dependency management. Docker knowledge helps you deliver software in portable, reproducible units.",
    "kubernetes": "Kubernetes manages containerized applications across many servers, handling scaling, service discovery, and reliability. It is used for cloud-native deployments and microservice orchestration. Kubernetes experience shows you can operate production-grade distributed systems.",
    "aws": "AWS offers cloud services for compute, storage, networking, databases, and more. Understanding AWS lets you deploy scalable infrastructure and use managed cloud tools. AWS skills are highly sought after in cloud engineering and DevOps roles.",
    "ci/cd": "CI/CD automates the process of building, testing, and deploying software changes. It reduces manual errors and speeds up delivery cycles. CI/CD expertise shows you can maintain high-quality, repeatable release processes.",
    "testing": "Testing ensures software works correctly and helps prevent regressions. Learn unit testing, integration testing, and test automation to improve code quality.",
    "unit testing": "Unit testing validates individual pieces of code in isolation. It makes your codebase safer, easier to maintain, and more reliable.",
    "rest api": "REST APIs let applications communicate over HTTP using standard operations. Building and consuming APIs is essential for modern web services.",
    "microservices": "Microservices break a system into smaller services that can be developed and scaled independently. They are useful for larger distributed applications.",
    "cloud": "Cloud computing provides scalable infrastructure and services hosted by providers like AWS, Azure, and GCP. Cloud skills let you deploy applications in production.",
    "security": "Security knowledge helps protect systems from attacks and keep user data safe. It includes access control, encryption, and secure coding practices.",
    "performance optimization": "Performance optimization improves how fast and efficiently applications run. It includes profiling, caching, and tuning algorithms.",
    "debugging": "Debugging is the process of finding and fixing issues in code. Strong debugging skills help you resolve problems quickly and keep applications stable.",
    "feature engineering": "Feature engineering transforms raw data into meaningful features for machine learning models. It is a critical step in building accurate models.",
    "model evaluation": "Model evaluation measures how well a machine learning model performs and helps you choose the best solution.",
    "data cleaning": "Data cleaning removes errors, missing values, and inconsistencies from datasets so analysis and modeling are more accurate.",
    "data engineering": "Data engineering focuses on building pipelines and systems for collecting, storing, and processing large datasets.",
    "mlops": "MLOps combines machine learning and operations to deploy and maintain models reliably in production.",
    "big data": "Big data refers to working with very large datasets using tools like Spark and Hadoop.",
    "dashboarding": "Dashboarding means designing clear visual summaries of business data for stakeholders.",
    "reporting": "Reporting involves presenting data findings in structured reports to support decisions.",
    "power query": "Power Query extracts, transforms, and loads data inside Excel and Power BI.",
    "presentation": "Presentation skills help you communicate data insights clearly to teams and managers.",
    "responsive design": "Responsive design ensures websites work well across phones, tablets, and desktops.",
    "typescript": "TypeScript adds strong typing to JavaScript, improving code quality and maintainability.",
    "web accessibility": "Web accessibility makes websites usable for people with disabilities, improving inclusivity and compliance.",
    "ui/ux": "UI/UX design focuses on creating usable, attractive, and intuitive interfaces.",
    "api integration": "API integration connects services and data between systems for modern web applications.",
    "webpack": "Webpack bundles JavaScript and assets for optimized web application delivery.",
    "seo": "SEO improves a website's visibility in search engines and drives more organic traffic.",
    "graphql": "GraphQL is a query language for APIs that lets clients request exactly the data they need.",
    "firebase": "Firebase offers backend services like authentication, database, and hosting for web and mobile apps.",
    "model deployment": "Model deployment publishes machine learning models so they can be used by applications.",
    "data pipelines": "Data pipelines move and transform data through systems for analytics and modeling.",
    "api development": "API development creates services that allow applications to communicate and reuse logic.",
    "scikit-learn": "Scikit-learn is a Python library for traditional machine learning algorithms and model evaluation.",
    "optimization": "Optimization improves model performance and algorithm efficiency, often by tuning parameters.",
    "ansible": "Ansible automates infrastructure configuration and deployment through simple playbooks.",
    "terraform": "Terraform defines infrastructure as code so cloud resources can be provisioned consistently.",
    "monitoring": "Monitoring tracks system health and alerts you about performance or errors in production.",
    "jenkins": "Jenkins automates software builds, tests, and deployments through CI/CD pipelines.",
    "bash scripting": "Bash scripting automates tasks and workflows in Linux and Unix environments.",
    "networking": "Networking knowledge helps you configure servers, routes, and secure communication between systems.",
    "azure": "Azure is Microsoft's cloud platform offering compute, storage, and app services.",
    "gcp": "Google Cloud Platform provides cloud services for compute, storage, AI, and data analytics.",
    "computer vision": "Computer vision enables machines to interpret and understand images and video. It is crucial for applications like facial recognition, object detection, and autonomous vehicles. CV expertise opens doors to robotics, medical imaging, and advanced AI applications.",
    "reinforcement learning": "Reinforcement learning trains agents to learn optimal behaviors through rewards and penalties. It powers game AI, robotics, and autonomous systems. Understanding RL shows you can solve complex sequential decision-making problems.",
    "transformers": "The Transformer architecture revolutionized NLP and is the foundation of modern LLMs. It uses self-attention mechanisms to process sequences in parallel. Transformer knowledge is essential for working with cutting-edge language and vision models.",
    "hugging face": "Hugging Face provides thousands of pre-trained models for NLP, vision, and speech. It simplifies accessing and fine-tuning state-of-the-art models. Hugging Face expertise lets you rapidly prototype advanced AI applications.",
    "langchain": "LangChain is a framework for building applications powered by LLMs. It handles prompt chaining, memory, and tool integration. LangChain skills enable you to build sophisticated language model applications.",
    "llm": "Large Language Models like GPT, Claude, and LLaMA can generate text, answer questions, and reason. Understanding LLMs is critical for modern AI development. LLM knowledge helps you build AI-powered features and products.",
    "prompt engineering": "Prompt engineering is the art of crafting inputs to get desired outputs from LLMs. It's essential for maximizing model performance without fine-tuning. Strong prompt engineering skills make you highly effective with AI tools.",
    "generative ai": "Generative AI creates new content like text, images, music, and code from learned patterns. It includes GANs, diffusion models, and autoregressive models. Generative AI expertise positions you at the forefront of AI innovation.",
    "vector databases": "Vector databases store and query embeddings for semantic search and similarity matching. They are essential for retrieval-augmented generation and AI applications. Vector database knowledge enables efficient similarity-based systems.",
    "pinecone": "Pinecone is a managed vector database for semantic search at scale. It simplifies building AI applications that require similarity matching. Pinecone expertise streamlines production AI deployments.",
    "weaviate": "Weaviate is an open-source vector search engine for semantic understanding. It combines semantic search with traditional database features. Weaviate skills enable you to build intelligent search and recommendation systems.",
    "golang": "Go is a modern language for building concurrent, networked services. It is known for fast compilation, built-in concurrency, and clean syntax. Go skills are valuable for building microservices and cloud infrastructure tools.",
    "rust": "Rust is a systems language that provides memory safety without garbage collection. It prevents common bugs and enables high-performance code. Rust expertise is valuable for systems programming and performance-critical applications.",
    "kotlin": "Kotlin is a modern JVM language that improves upon Java with concise syntax and safety features. It is the preferred language for modern Android development. Kotlin skills make you efficient in Android and backend development.",
    "solid principles": "SOLID principles (Single Responsibility, Open/Closed, Liskov, Interface Segregation, Dependency Inversion) guide clean code design. They help prevent code smell and reduce technical debt. Applying SOLID principles shows you can write maintainable software.",
    "design patterns": "Design patterns are reusable solutions to common programming problems. They include Creational, Structural, and Behavioral patterns. Pattern knowledge helps you design flexible, scalable code.",
    "grpc": "gRPC is a high-performance RPC framework using HTTP/2 and protocol buffers. It enables efficient communication between microservices. gRPC expertise is valuable for building scalable distributed systems.",
    "github actions": "GitHub Actions automates workflows directly in GitHub repositories. It integrates testing, building, and deployment seamlessly. GitHub Actions knowledge streamlines CI/CD for your projects.",
    "spring boot": "Spring Boot simplifies building Java applications with embedded servers and auto-configuration. It's widely used for enterprise backend services. Spring Boot skills make you productive in Java development.",
    "fastapi": "FastAPI is a modern Python framework for building fast, production-ready APIs. It features automatic validation, async support, and interactive API docs. FastAPI expertise enables you to build efficient Python backends.",
    "express": "Express is a minimal Node.js framework for building web applications and APIs. It's flexible and widely adopted in the Node ecosystem. Express skills are essential for full-stack JavaScript development.",
    "next.js": "Next.js extends React with server-side rendering, static generation, and built-in optimization. It simplifies deploying production-grade React applications. Next.js expertise enables you to build performant, scalable web apps.",
    "vue.js": "Vue.js is a progressive JavaScript framework for building reactive user interfaces. It offers a gentler learning curve than React. Vue.js skills make you productive in modern frontend development.",
    "angular": "Angular is a comprehensive framework for building large-scale web applications with TypeScript. It includes routing, forms, HTTP client, and more. Angular expertise is valued for enterprise-level frontend development.",
    "tailwind css": "Tailwind CSS is a utility-first framework for rapid UI development without leaving HTML. It enables consistent design systems and responsive layouts. Tailwind expertise accelerates your frontend development workflow.",
    "bootstrap": "Bootstrap is a CSS framework with pre-built components for responsive design. It simplifies building professional-looking websites quickly. Bootstrap skills are useful for rapid prototyping and design-conscious development.",
    "sass": "Sass extends CSS with variables, mixins, nesting, and functions for maintainable stylesheets. It reduces code duplication and improves organization. Sass expertise helps you write scalable, DRY CSS.",
    "redux": "Redux is a state management library for JavaScript applications. It provides a single source of truth for application state. Redux knowledge helps you manage complex state in large applications.",
    "context api": "Context API is React's built-in solution for state management. It avoids prop drilling and reduces dependency on external libraries. Context API expertise enables efficient state management in React apps.",
    "postgresql": "PostgreSQL is a powerful, open-source relational database with advanced features. It supports JSON, arrays, and complex queries. PostgreSQL expertise makes you proficient in modern database design.",
    "mysql": "MySQL is a widely-used relational database for web applications and data storage. It's known for reliability and ease of use. MySQL skills are fundamental for web development and data management.",
    "redis": "Redis is an in-memory data structure store used for caching, sessions, and real-time analytics. It's known for high performance and versatility. Redis expertise enables you to optimize application performance significantly.",
    "cassandra": "Cassandra is a distributed NoSQL database for massive scale. It offers high availability and fault tolerance. Cassandra skills are valuable for handling big data at scale.",
    "matplotlib": "Matplotlib is a foundational Python library for creating static, publication-quality visualizations. It's versatile and widely used in data science. Matplotlib expertise enables effective data visualization.",
    "seaborn": "Seaborn is built on Matplotlib and simplifies statistical data visualization with attractive defaults. It integrates well with pandas. Seaborn skills accelerate your data exploration and visualization work.",
    "plotly": "Plotly creates interactive, web-based visualizations and dashboards. It supports 3D charts and real-time updates. Plotly expertise enables you to create engaging, interactive data visualizations.",
    "jupyter": "Jupyter notebooks provide interactive environments for code, visualization, and narrative. They are standard in data science and research. Jupyter expertise streamlines exploratory analysis and reproducible research.",
    "spark": "Apache Spark is a distributed computing framework for big data processing. It handles massive datasets efficiently with parallel computing. Spark skills are essential for handling enterprise-scale data.",
    "hadoop": "Hadoop is a distributed framework for processing large datasets across clusters. It includes HDFS for storage and MapReduce for processing. Hadoop expertise is valuable for big data infrastructure.",
    "helm": "Helm is the package manager for Kubernetes, simplifying deployment and updates. It uses templates for reproducible deployments. Helm expertise streamlines Kubernetes application management.",
    "prometheus": "Prometheus is an open-source monitoring system for collecting and querying metrics. It's widely used for infrastructure monitoring. Prometheus expertise enables proactive system monitoring.",
    "grafana": "Grafana creates rich dashboards and visualizations for monitoring metrics. It integrates with many data sources including Prometheus. Grafana expertise helps you visualize system health and performance.",
    "datadog": "Datadog is a comprehensive monitoring and analytics platform for infrastructure, apps, and logs. It's used by many enterprises for observability. Datadog expertise enables full-stack monitoring and troubleshooting.",
    "vault": "HashiCorp Vault securely manages secrets, encryption keys, and sensitive data. It provides audit logs and access controls. Vault expertise helps you implement security best practices.",
    "istio": "Istio is a service mesh for managing microservices communication and security. It provides traffic management, security policies, and observability. Istio expertise enables sophisticated microservices infrastructure.",
    "argocd": "ArgoCD enables GitOps for Kubernetes deployments. It synchronizes cluster state with Git repositories. ArgoCD expertise streamlines continuous deployment workflows.",
    "cloudformation": "CloudFormation lets you define AWS infrastructure as code using templates. It enables reproducible, versioned infrastructure. CloudFormation expertise simplifies AWS resource management.",
    "flask": "Flask is a lightweight Python web framework for building applications quickly. It's flexible and suitable for small to medium projects. Flask expertise enables rapid web development in Python.",
    "django": "Django is a full-featured Python web framework with built-in admin, ORM, and security. It follows the MTV architecture. Django expertise enables you to build robust, feature-rich web applications.",
    "looker": "Looker is Google's business intelligence platform for data exploration and visualization. It supports complex data modeling. Looker expertise helps you deliver business insights effectively.",
    "google analytics": "Google Analytics tracks website traffic, user behavior, and conversions. It's essential for web analytics and optimization. Google Analytics expertise enables data-driven web strategy.",
    "amplitude": "Amplitude provides product analytics for tracking user behavior and engagement. It helps identify growth opportunities. Amplitude expertise enables product-driven decision making.",
    "cohort analysis": "Cohort analysis groups users by shared characteristics to understand behavior patterns. It reveals retention and engagement trends. Cohort analysis skills help you understand user lifecycle.",
    "retention analysis": "Retention analysis measures how well a product keeps users engaged over time. It's critical for assessing product success. Retention analysis expertise helps you improve user loyalty.",
    "funnel analysis": "Funnel analysis tracks user progression through stages to identify conversion bottlenecks. It reveals where users drop off. Funnel analysis skills help you optimize user journeys.",
    "metric design": "Metric design involves selecting and defining KPIs that drive business and product decisions. It requires understanding business goals. Metric design expertise ensures you're measuring what matters.",
    "advanced excel": "Advanced Excel includes array formulas, pivot tables, VLOOKUP, and data analysis tools. It's essential for quantitative work. Advanced Excel skills make you efficient in data analysis.",
    "vba": "VBA (Visual Basic for Applications) automates Excel tasks and creates custom functions. It enables complex Excel workflows. VBA skills extend Excel's capabilities significantly.",
    "nginx": "Nginx is a high-performance web server and reverse proxy. It's known for efficiency and scalability. Nginx expertise enables you to optimize web server performance.",
    "apache": "Apache is a widely-used web server supporting various modules and configurations. It's reliable and feature-rich. Apache expertise is valuable for server administration.",
    "infrastructure as code": "Infrastructure as code treats infrastructure like application code using version control and automation. It enables reproducible, documented infrastructure. IaC expertise improves infrastructure reliability and scalability.",
    "istio service mesh": "Service mesh infrastructure handles communication between microservices with traffic management and security. It simplifies microservices operations. Service mesh expertise enables sophisticated distributed systems.",
    "natural language processing": "NLP enables computers to understand and process human language. It includes tokenization, sentiment analysis, and translation. NLP expertise opens doors to language-based AI applications.",
    "large language model": "Large Language Models are neural networks trained on vast text data for understanding and generation. They power modern AI assistants. LLM expertise positions you at the frontier of AI development.",
    "artificial intelligence": "Artificial intelligence encompasses techniques to make machines intelligent and capable of learning. It includes machine learning, deep learning, and reasoning. AI expertise is increasingly valuable across industries."
}

SKILL_RESOURCES = {
    "python": "Read the official Python docs, follow Real Python tutorials, and build small automation or data projects.",
    "java": "Use Oracle's Java tutorials and create a backend service or Android sample app.",
    "c++": "Study modern C++ references, write a command-line tool, and explore memory management techniques.",
    "javascript": "Learn from MDN Web Docs and build a web interface or Node.js API.",
    "data structures": "Practice array, tree, and graph problems on LeetCode and HackerRank.",
    "algorithms": "Review sorting, searching, and dynamic programming, then solve interview-style problems.",
    "oop": "Build a small application using classes, inheritance, and encapsulation patterns.",
    "sql": "Practice SQL queries on sample databases with joins, aggregations, and window functions.",
    "git": "Use GitHub and Git commands to manage branches, commits, and pull requests.",
    "system design": "Read system design guides and sketch architecture diagrams for scalable services.",
    "pandas": "Work with DataFrames in Python to clean, filter, and analyze CSV datasets.",
    "numpy": "Practice vectorized math operations and array manipulation in NumPy.",
    "machine learning": "Follow scikit-learn tutorials to train, evaluate, and tune prediction models.",
    "deep learning": "Build simple neural networks using TensorFlow or PyTorch tutorials.",
    "statistics": "Study distributions, hypothesis testing, and data summaries with real examples.",
    "data visualization": "Create charts and dashboards with Matplotlib, Seaborn, or Power BI.",
    "excel": "Practice formulas, pivot tables, and chart building in Excel.",
    "power bi": "Build interactive Power BI reports and connect to live data sources.",
    "tableau": "Create visual analytics dashboards in Tableau and publish insights.",
    "data analysis": "Analyze datasets end-to-end with cleaning, visualization, and summary reports.",
    "html": "Build web pages using HTML structure, forms, and semantic tags.",
    "css": "Practice layouts, Flexbox, Grid, and responsive styles with CSS.",
    "react": "Build a React app with components, state, and hooks.",
    "node": "Create a Node.js backend API and learn routing and middleware.",
    "mongodb": "Model and query documents in MongoDB with a small application.",
    "tensorflow": "Follow TensorFlow beginner tutorials for neural network training.",
    "pytorch": "Practice PyTorch model building and training loops.",
    "nlp": "Try text classification and tokenization tutorials for NLP tasks.",
    "linux": "Practice Linux command-line tools, shell scripts, and system management.",
    "docker": "Containerize an application using Docker and understand image layers.",
    "kubernetes": "Deploy containers with Kubernetes and learn about pods and services.",
    "aws": "Use AWS free tier services like EC2, S3, and Lambda in a small cloud project.",
    "ci/cd": "Set up a CI/CD pipeline with GitHub Actions or another automation tool.",
    "computer vision": "Work with image processing libraries like OpenCV and build vision models with PyTorch.",
    "reinforcement learning": "Study reward functions and Q-learning algorithms with environments like OpenAI Gym.",
    "transformers": "Learn the Transformer architecture and fine-tune pre-trained models from Hugging Face.",
    "hugging face": "Explore pre-trained NLP and vision models in the Hugging Face Hub and integrate into applications.",
    "langchain": "Build LLM chains and applications using LangChain for language model composition.",
    "llm": "Understand large language models like GPT, BERT, and how to prompt and fine-tune them.",
    "prompt engineering": "Learn to craft effective prompts for LLMs to get desired outputs and responses.",
    "generative ai": "Explore generative models like GANs, diffusion models, and language generation techniques.",
    "vector databases": "Work with vector storage systems for semantic search and similarity matching.",
    "pinecone": "Use Pinecone for scalable vector search in production AI applications.",
    "weaviate": "Deploy Weaviate for vector search and semantic understanding at scale.",
    "golang": "Learn Go for building fast, concurrent backend services and cloud tooling.",
    "rust": "Master Rust for systems programming, performance-critical code, and memory safety.",
    "kotlin": "Use Kotlin for modern Android development and JVM-based backend services.",
    "solid principles": "Apply SOLID principles (Single Responsibility, Open/Closed, etc.) to write maintainable code.",
    "design patterns": "Implement Gang of Four patterns like Singleton, Factory, Observer for clean architecture.",
    "grpc": "Build high-performance services using gRPC and protocol buffers.",
    "github actions": "Automate CI/CD workflows using GitHub Actions for testing and deployment.",
    "spring boot": "Create enterprise Java applications with Spring Boot framework and ecosystem.",
    "fastapi": "Build modern, fast Python APIs with FastAPI and automatic API documentation.",
    "express": "Create Node.js applications and APIs using the Express.js framework.",
    "next.js": "Build production-ready React applications with Next.js for server-side rendering and optimization.",
    "vue.js": "Learn Vue.js for building reactive and component-based user interfaces.",
    "angular": "Build large-scale applications with Angular framework and TypeScript.",
    "tailwind css": "Use utility-first Tailwind CSS for rapid UI development and responsive design.",
    "bootstrap": "Build responsive websites quickly with Bootstrap components and grid system.",
    "sass": "Write maintainable CSS with Sass for variables, mixins, and nested selectors.",
    "redux": "Manage complex state in React applications using Redux and middleware.",
    "context api": "Use React Context API for state management without external libraries.",
    "postgresql": "Work with PostgreSQL for relational databases with advanced features.",
    "mysql": "Manage data using MySQL, a popular relational database management system.",
    "redis": "Use Redis for caching, sessions, and real-time data in high-performance applications.",
    "cassandra": "Scale horizontally with Cassandra for distributed NoSQL databases.",
    "mongodb": "Design schemas and query document-oriented MongoDB databases.",
    "matplotlib": "Create static visualizations and plots using Matplotlib for data analysis.",
    "seaborn": "Build statistical data visualizations with Seaborn built on Matplotlib.",
    "plotly": "Create interactive visualizations with Plotly for web-based dashboards.",
    "jupyter": "Write and share interactive notebooks with Jupyter for data analysis and research.",
    "scikit-learn": "Train machine learning models using scikit-learn's algorithms and tools.",
    "spark": "Process big data at scale using Apache Spark for distributed computing.",
    "hadoop": "Manage large datasets with Hadoop for distributed storage and processing.",
    "docker": "Containerize applications with Docker for consistent deployment.",
    "kubernetes": "Orchestrate containers with Kubernetes for scalable cloud deployments.",
    "helm": "Deploy and manage Kubernetes applications using Helm charts.",
    "prometheus": "Monitor systems and collect metrics with Prometheus.",
    "grafana": "Create dashboards and visualizations for monitoring with Grafana.",
    "datadog": "Monitor infrastructure and applications with Datadog observability platform.",
    "vault": "Manage secrets and encryption keys securely with HashiCorp Vault.",
    "istio": "Implement service mesh with Istio for microservices communication.",
    "argocd": "Deploy GitOps workflows with ArgoCD for declarative deployments.",
    "cloudformation": "Define AWS infrastructure as code using CloudFormation templates.",
    "terraform": "Provision infrastructure across cloud providers with Terraform.",
    "ansible": "Automate infrastructure provisioning and configuration with Ansible playbooks.",
    "jenkins": "Set up CI/CD pipelines with Jenkins for automated builds and testing.",
    "monitoring": "Implement system monitoring and alerting for production applications.",
    "ethics": "Understand AI ethics, bias, fairness, and responsible AI development.",
    "data privacy": "Apply GDPR, data protection, and privacy-first principles in applications.",
    "flask": "Build lightweight Python web applications with Flask microframework.",
    "django": "Create full-featured web applications with Django framework.",
    "power query": "Extract and transform data using Power Query in Excel and Power BI.",
    "looker": "Build business intelligence dashboards with Google Looker.",
    "google analytics": "Track and analyze website traffic with Google Analytics.",
    "amplitude": "Track product analytics and user behavior with Amplitude.",
    "cohort analysis": "Analyze user groups over time to understand retention and behavior.",
    "retention analysis": "Measure how well a product keeps users engaged over time.",
    "funnel analysis": "Analyze conversion funnels to identify bottlenecks in user journeys.",
    "metric design": "Design meaningful metrics and KPIs for business and product success.",
    "advanced excel": "Master advanced Excel functions, array formulas, and complex analyses.",
    "vba": "Automate Excel tasks and create custom functions using VBA.",
    "nginx": "Configure and optimize Nginx web server for high performance.",
    "apache": "Set up and manage Apache web server for web applications.",
    "bash scripting": "Automate Linux tasks and workflows with Bash shell scripts.",
    "networking": "Configure networks, understand TCP/IP, and troubleshoot connectivity.",
    "security": "Implement security best practices, encryption, and secure coding.",
    "performance optimization": "Profile and optimize application performance for speed and efficiency.",
    "debugging": "Use debugging tools and techniques to find and fix code issues.",
    "testing": "Write and execute tests to ensure software quality and reliability.",
    "unit testing": "Write isolated tests for individual code units and functions.",
    "integration testing": "Test interactions between multiple components and systems.",
    "rest api": "Design and build RESTful APIs following REST principles.",
    "graphql": "Query and manipulate data efficiently with GraphQL APIs.",
    "communication": "Communicate technical concepts clearly to team members and stakeholders.",
    "api development": "Build robust and scalable APIs for application integration.",
    "system design": "Design scalable, reliable systems for production applications.",
    "microservices": "Build applications as independent, loosely coupled services.",
    "cloud": "Deploy and manage applications on cloud platforms (AWS, GCP, Azure).",
    "feature engineering": "Create meaningful features from raw data for machine learning."
}

SKILL_CATEGORIES = {
    "python": "Programming",
    "java": "Programming",
    "c++": "Programming",
    "javascript": "Programming",
    "typescript": "Programming",
    "html": "Frontend",
    "css": "Frontend",
    "react": "Frontend",
    "node": "Backend",
    "django": "Backend",
    "flask": "Backend",
    "mongodb": "Database",
    "sql": "Database",
    "pandas": "Data",
    "numpy": "Data",
    "tensorflow": "AI/ML",
    "pytorch": "AI/ML",
    "machine learning": "AI/ML",
    "deep learning": "AI/ML",
    "nlp": "AI/ML",
    "data visualization": "Data",
    "data analysis": "Data",
    "statistics": "Data",
    "cloud": "Cloud",
    "aws": "Cloud",
    "azure": "Cloud",
    "gcp": "Cloud",
    "docker": "DevOps",
    "kubernetes": "DevOps",
    "ci/cd": "DevOps",
    "jenkins": "DevOps",
    "terraform": "DevOps",
    "ansible": "DevOps",
    "linux": "DevOps",
    "git": "Tools",
    "testing": "Tools",
    "unit testing": "Tools",
    "rest api": "Tools",
    "graphql": "Tools",
    "webpack": "Tools",
    "seo": "Other",
    "presentation": "Other",
    "communication": "Other",
    "security": "Other",
    "system design": "Architecture",
    "microservices": "Architecture",
    "data pipelines": "Architecture",
    "model deployment": "Architecture",
    "mlops": "Architecture",
    "performance optimization": "Optimization",
    "debugging": "Optimization",
    "golang": "Programming",
    "rust": "Programming",
    "kotlin": "Programming",
    "computer vision": "AI/ML",
    "reinforcement learning": "AI/ML",
    "transformers": "AI/ML",
    "hugging face": "AI/ML",
    "langchain": "AI/ML",
    "llm": "AI/ML",
    "prompt engineering": "AI/ML",
    "generative ai": "AI/ML",
    "vector databases": "AI/ML",
    "pinecone": "AI/ML",
    "weaviate": "AI/ML",
    "solid principles": "Architecture",
    "design patterns": "Architecture",
    "grpc": "Backend",
    "github actions": "DevOps",
    "spring boot": "Backend",
    "fastapi": "Backend",
    "express": "Backend",
    "next.js": "Frontend",
    "vue.js": "Frontend",
    "angular": "Frontend",
    "tailwind css": "Frontend",
    "bootstrap": "Frontend",
    "sass": "Frontend",
    "redux": "Frontend",
    "context api": "Frontend",
    "postgresql": "Database",
    "mysql": "Database",
    "redis": "Database",
    "cassandra": "Database",
    "matplotlib": "Data",
    "seaborn": "Data",
    "plotly": "Data",
    "jupyter": "Tools",
    "scikit-learn": "AI/ML",
    "spark": "Data",
    "hadoop": "Data",
    "helm": "DevOps",
    "prometheus": "DevOps",
    "grafana": "DevOps",
    "datadog": "DevOps",
    "vault": "DevOps",
    "istio": "DevOps",
    "argocd": "DevOps",
    "cloudformation": "DevOps",
    "flask": "Backend",
    "django": "Backend",
    "looker": "Data",
    "google analytics": "Data",
    "amplitude": "Data",
    "cohort analysis": "Data",
    "retention analysis": "Data",
    "funnel analysis": "Data",
    "metric design": "Data",
    "advanced excel": "Tools",
    "vba": "Tools",
    "nginx": "DevOps",
    "apache": "DevOps",
    "bash scripting": "DevOps",
    "networking": "DevOps",
    "monitoring": "DevOps",
    "ethics": "Other",
    "data privacy": "Other",
    "power query": "Tools",
    "integration testing": "Tools",
    "api development": "Backend",
    "model evaluation": "AI/ML",
    "data cleaning": "Data",
    "data engineering": "Data",
    "infrastructure as code": "DevOps",
    "istio service mesh": "DevOps",
    "natural language processing": "AI/ML",
    "large language model": "AI/ML",
    "artificial intelligence": "AI/ML"
}

SKILL_BULLETS = {
    "python": "Developed Python scripts to automate data processing, reducing manual effort by 40%.",
    "java": "Built a Java-based backend service that handled REST API requests for 10,000+ users.",
    "c++": "Implemented performance-critical modules in C++ for a high-speed simulation application.",
    "javascript": "Created interactive web interfaces using JavaScript and modern frontend frameworks.",
    "react": "Built reusable React components to deliver responsive UI experiences.",
    "node": "Created RESTful APIs using Node.js for seamless frontend-backend communication.",
    "sql": "Designed optimized SQL queries to extract business metrics from relational databases.",
    "git": "Managed version control workflows with Git, including branching and pull requests.",
    "docker": "Containerized applications using Docker for consistent deployment across environments.",
    "kubernetes": "Deployed containerized workloads in Kubernetes clusters for high availability.",
    "aws": "Provisioned AWS infrastructure for cloud-hosted applications and services.",
    "data analysis": "Analyzed datasets to identify trends and support data-driven decisions.",
    "data visualization": "Created dashboards and charts to communicate insights to stakeholders.",
    "machine learning": "Trained and evaluated machine learning models to solve prediction problems.",
    "deep learning": "Built neural network models for image and text classification tasks.",
    "nlp": "Developed NLP pipelines for sentiment analysis and text classification.",
    "powershell": "Automated system tasks using PowerShell scripts.",
    "computer vision": "Built computer vision models for image recognition and object detection.",
    "reinforcement learning": "Developed RL agents that learned optimal strategies for complex tasks.",
    "transformers": "Fine-tuned Transformer models for state-of-the-art NLP and vision tasks.",
    "hugging face": "Leveraged Hugging Face models to accelerate AI model development and deployment.",
    "langchain": "Built LLM applications using LangChain for advanced language model orchestration.",
    "llm": "Integrated large language models into production systems for intelligent features.",
    "prompt engineering": "Optimized prompts to extract desired outputs from large language models.",
    "generative ai": "Created generative AI systems for text, image, and code generation.",
    "vector databases": "Implemented vector search systems for semantic similarity and recommendation.",
    "pinecone": "Deployed Pinecone for scalable vector search in production systems.",
    "weaviate": "Built semantic search solutions using Weaviate vector database.",
    "golang": "Developed high-performance microservices and cloud tools using Go.",
    "rust": "Built memory-safe, high-performance systems programming solutions in Rust.",
    "kotlin": "Developed modern Android applications and backend services with Kotlin.",
    "solid principles": "Applied SOLID principles to design maintainable and scalable code.",
    "design patterns": "Implemented design patterns for flexible, extensible software architecture.",
    "grpc": "Built efficient microservices communication using gRPC and protocol buffers.",
    "github actions": "Automated CI/CD workflows with GitHub Actions for continuous deployment.",
    "spring boot": "Developed enterprise Java applications with Spring Boot framework.",
    "fastapi": "Built fast, modern Python APIs with FastAPI and async support.",
    "express": "Created scalable Node.js applications and APIs using Express.js.",
    "next.js": "Built optimized, production-ready React applications with Next.js.",
    "vue.js": "Developed reactive user interfaces using Vue.js framework.",
    "angular": "Built large-scale enterprise web applications with Angular.",
    "tailwind css": "Rapidly built responsive UIs using Tailwind CSS utilities.",
    "bootstrap": "Created professional-looking responsive websites with Bootstrap.",
    "sass": "Organized and maintained CSS at scale using Sass.",
    "redux": "Managed complex application state with Redux.",
    "context api": "Implemented state management using React Context API.",
    "postgresql": "Designed and optimized PostgreSQL databases for production systems.",
    "mysql": "Built relational databases with MySQL for web applications.",
    "redis": "Implemented caching and session management with Redis.",
    "cassandra": "Scaled databases to handle massive data volumes with Cassandra.",
    "matplotlib": "Created publication-quality visualizations with Matplotlib.",
    "seaborn": "Generated statistical visualizations with Seaborn.",
    "plotly": "Built interactive, web-based data visualizations with Plotly.",
    "jupyter": "Developed and shared interactive analyses using Jupyter notebooks.",
    "scikit-learn": "Trained machine learning models using scikit-learn algorithms.",
    "spark": "Processed large datasets efficiently using Apache Spark.",
    "hadoop": "Built distributed data processing systems with Hadoop.",
    "helm": "Managed Kubernetes deployments at scale using Helm charts.",
    "prometheus": "Set up comprehensive monitoring systems with Prometheus.",
    "grafana": "Created monitoring dashboards with Grafana for system observability.",
    "datadog": "Monitored infrastructure and applications using Datadog.",
    "vault": "Implemented secure secret management using HashiCorp Vault.",
    "istio": "Implemented service mesh for microservices communication with Istio.",
    "argocd": "Deployed GitOps workflows with ArgoCD for continuous delivery.",
    "cloudformation": "Provisioned AWS infrastructure using CloudFormation templates.",
    "flask": "Built lightweight web applications and APIs using Flask.",
    "django": "Created full-featured web applications with Django framework.",
    "looker": "Built business intelligence dashboards with Google Looker.",
    "google analytics": "Analyzed web traffic and user behavior with Google Analytics.",
    "amplitude": "Tracked product analytics and user engagement metrics with Amplitude.",
    "cohort analysis": "Identified user retention patterns through cohort analysis.",
    "retention analysis": "Analyzed user retention metrics to improve product engagement.",
    "funnel analysis": "Identified conversion bottlenecks using funnel analysis.",
    "metric design": "Designed meaningful KPIs aligned with business objectives.",
    "advanced excel": "Built complex spreadsheet models and analyses in Excel.",
    "vba": "Automated Excel workflows and created custom tools with VBA.",
    "nginx": "Optimized web server performance using Nginx.",
    "apache": "Configured and managed Apache web servers for production.",
    "bash scripting": "Automated infrastructure tasks with Bash scripts.",
    "networking": "Configured networks and resolved connectivity issues.",
    "monitoring": "Implemented comprehensive monitoring for system health and alerts.",
    "ethics": "Applied ethical principles to AI and data science projects.",
    "data privacy": "Implemented privacy-first practices and GDPR compliance.",
    "integration testing": "Wrote integration tests to verify component interactions.",
    "model evaluation": "Evaluated machine learning models for accuracy and performance.",
    "data cleaning": "Prepared datasets by cleaning and preprocessing data.",
    "data engineering": "Built data pipelines and infrastructure for analytics.",
    "infrastructure as code": "Defined infrastructure using code for reproducibility.",
    "istio service mesh": "Implemented advanced service mesh for microservices.",
    "natural language processing": "Applied NLP techniques for language understanding tasks.",
    "large language model": "Integrated LLMs into production applications.",
    "artificial intelligence": "Developed AI systems and algorithms for intelligent solutions." 
}

# ---------------- ROLE ALIASES ----------------
ROLE_ALIASES = {
    "software engineer": ["software", "developer", "backend", "full stack", "backend engineer", "software engineer"],
    "data scientist": ["data science", "data scientist", "ml", "data"],
    "data analyst": ["analyst", "data analyst", "analytics"],
    "web developer": ["web", "frontend", "fullstack", "web dev"],
    "machine learning engineer": ["ml engineer", "machine learning", "ml engineer"],
    "ai engineer": ["ai engineer", "llm engineer", "artificial intelligence", "ai/ml", "generative ai", "llm", "ai"],
    "devops engineer": ["devops", "cloud", "aws", "sre", "infrastructure"]
}

# ---------------- SYNONYMS ----------------
SYNONYMS = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "ml": "machine learning",
    "dl": "deep learning",
    "ai": "artificial intelligence",
    "np": "numpy",
    "pd": "pandas",
    "tf": "tensorflow",
    "cv": "computer vision",
    "nlp": "natural language processing",
    "llm": "large language model",
    "db": "database",
    "api": "api development",
    "oop": "object-oriented programming",
    "ci/cd": "continuous integration continuous deployment",
    "sql": "sql",
    "nosql": "nosql databases",
    "sre": "site reliability engineering",
    "devops": "devops engineer"
}

# ---------------- HELPERS ----------------
def normalize_text(text: str) -> str:
    text = text.lower()
    for k, v in SYNONYMS.items():
        pattern = r"\b" + re.escape(k) + r"\b"
        text = re.sub(pattern, v, text)
    return text


def detect_role(user_input: str) -> str:
    user_input = user_input.lower()

    # First pass: check for multi-word keywords (more specific)
    # Sort keywords by word count (descending) and length (descending)
    matches = []
    for role, keywords in ROLE_ALIASES.items():
        for word in keywords:
            if word in user_input:
                word_count = len(word.split())  # Number of words in keyword
                keyword_length = len(word)
                matches.append((role, word_count, keyword_length))

    # Return the role with the best match (most words, then longest)
    if matches:
        matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        return matches[0][0]

    return "software engineer"


def skill_match(skill: str, text: str) -> bool:
    variants = [
        skill,
        skill.replace(" ", ""),
        skill.replace(" ", "-")
    ]
    for v in variants:
        pattern = r"\b" + re.escape(v) + r"\b"
        if re.search(pattern, text):
            return True
    return False


# ---------------- ANALYSIS ----------------
def analyze_resume(resume_text: str, role: str) -> Dict[str, Any]:
    matched_role = detect_role(role)
    required_skills = ROLE_SKILLS.get(matched_role, [])

    # AI-powered skill extraction
    if OPENAI_AVAILABLE and openai_client:
        prompt = f"""
        Analyze this resume text for a {matched_role} position. Extract all technical skills, technologies, and competencies mentioned.
        Resume text:
        {resume_text[:4000]}  # Limit to avoid token limits

        Required skills for {matched_role}: {', '.join(required_skills)}

        Provide a JSON response with:
        - detected_skills: array of skills found in resume
        - missing_skills: array of required skills not found
        - score: percentage (0-100) based on skill coverage
        - suggestions: array of 3-5 specific improvement suggestions
        - strengths: array of 2-3 key strengths from the resume
        """

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            ai_analysis = json.loads(response.choices[0].message.content)
            
            detected_skills = ai_analysis.get("detected_skills", [])
            missing_skills = ai_analysis.get("missing_skills", [])
            score = ai_analysis.get("score", 0)
            suggestions = ai_analysis.get("suggestions", [])
            strengths = ai_analysis.get("strengths", [])
            
        except Exception as e:
            # Fallback to original logic if AI fails
            print(f"AI analysis failed: {e}")
            text = normalize_text(resume_text)
            detected_skills = [skill for skill in required_skills if skill_match(skill, text)]
            missing_skills = [skill for skill in required_skills if skill not in detected_skills]
            score = int((len(detected_skills) / len(required_skills)) * 100) if required_skills else 0
            suggestions = ["Add more specific examples of your technical skills", "Include quantifiable achievements", "Tailor your resume to the specific role"]
            strengths = ["Strong technical foundation", "Relevant experience"]
    else:
        # Fallback to original logic
        text = normalize_text(resume_text)
        detected_skills = [skill for skill in required_skills if skill_match(skill, text)]
        missing_skills = [skill for skill in required_skills if skill not in detected_skills]
        score = int((len(detected_skills) / len(required_skills)) * 100) if required_skills else 0
        suggestions = ["Add more specific examples of your technical skills", "Include quantifiable achievements", "Tailor your resume to the specific role"]
        strengths = ["Strong technical foundation", "Relevant experience"]

    # Generate roadmap and other data
    roadmap = [f"Step {i+1}: Learn and implement {skill}" for i, skill in enumerate(missing_skills)]

    questions = []
    for skill in required_skills[:5]:
        questions.append(f"What is {skill} and how have you used it?")
        questions.append(f"Describe a project where you applied {skill}.")

    notes = {skill: SKILL_NOTES.get(skill, "Learn this skill and explore hands-on examples.") for skill in missing_skills}
    resources = {skill: SKILL_RESOURCES.get(skill, "Search for beginner guides and tutorials to build this skill.") for skill in missing_skills}

    # Role recommendations
    role_scores = []
    for role_name, skill_list in ROLE_SKILLS.items():
        matched_count = sum(1 for skill in skill_list if skill in detected_skills)
        total_count = len(skill_list)
        percentage = int((matched_count / total_count) * 100) if total_count else 0
        role_scores.append((role_name, percentage, matched_count, total_count))

    role_scores.sort(key=lambda x: (x[1], x[2]), reverse=True)
    recommended_roles = [f"{role.title()} ({percent}%)" for role, percent, _, _ in role_scores[:3] if role != matched_role][:3]

    # Category stats
    category_stats = {}
    for skill in required_skills:
        category = SKILL_CATEGORIES.get(skill, "Other")
        category_stats.setdefault(category, {"found": [], "missing": []})
        if skill in detected_skills:
            category_stats[category]["found"].append(skill)
        else:
            category_stats[category]["missing"].append(skill)

    category_summary = [
        f"{category}: {len(stats['found'])}/{len(stats['found']) + len(stats['missing'])} skills covered"
        for category, stats in category_stats.items()
    ]

    bullet_suggestions = []
    for skill in missing_skills:
        suggestion = SKILL_BULLETS.get(skill, f"Add experience or projects demonstrating {skill}.")
        bullet_suggestions.append(suggestion)

    tips = []
    if score == 100:
        tips.append("Excellent! Your resume includes all expected role skills.")
        tips.append("Keep adding concrete project examples for each skill.")
    else:
        tips.extend(suggestions)
        if score < 70:
            tips.append("Focus first on the core technical skills for your selected role.")
            tips.append("Use a clean format to show accomplishments and measurable results.")
        else:
            tips.append("You are close; strengthen your resume by mentioning the missing skills clearly.")
            tips.append("Show how you used related tools or technologies in your work or projects.")

    return {
        "Role": matched_role,
        "Score": f"{score}%",
        "Detected Skills": detected_skills,
        "Missing Skills": missing_skills,
        "Skill Notes": notes,
        "Skill Resources": resources,
        "Recommended Roles": recommended_roles,
        "Skill Categories": category_summary,
        "Suggested Resume Bullets": bullet_suggestions,
        "Improvement Tips": tips,
        "Roadmap": roadmap,
        "Interview Questions": questions,
        "Strengths": strengths
    }


# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return redirect("/dashboard") if "user" in session else redirect("/login")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Email and password are required")
            return redirect("/signup")

        db = get_db()
        try:
            if db.query(models.User).filter_by(email=email).first():
                flash("User already exists")
                return redirect("/signup")

            user = models.User(email=email)
            user.set_password(password)
            db.add(user)
            db.commit()
            flash("Signup successful")
            return redirect("/login")
        except Exception as e:
            db.rollback()
            flash(f"Error: {str(e)}")
            return redirect("/signup")
        finally:
            db.close()

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Email and password are required")
            return redirect("/login")

        db = get_db()
        try:
            user = db.query(models.User).filter_by(email=email).first()

            if user and user.check_password(password):
                session["user"] = user.email
                return redirect("/dashboard")

            flash("Invalid credentials")
        except Exception as e:
            flash(f"Error: {str(e)}")
        finally:
            db.close()

    return render_template("login.html")


@app.route("/dashboard", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    result = None

    if request.method == "POST":
        role = request.form.get("role")
        resume_text = request.form.get("resume")
        file = request.files.get("file")

        # FILE HANDLING
        if file and file.filename:
            try:
                if file.filename.lower().endswith(".pdf"):
                    pdf = PdfReader(file)
                    resume_text = "".join([page.extract_text() or "" for page in pdf.pages])

                elif file.filename.lower().endswith(".docx"):
                    doc = docx.Document(file)
                    resume_text = "\n".join([p.text for p in doc.paragraphs])

                elif file.filename.lower().endswith(".txt"):
                    resume_text = file.read().decode('utf-8')

                else:
                    flash("Supported formats: PDF, DOCX, TXT")
                    return redirect("/dashboard")

            except Exception as e:
                flash(f"File error: {str(e)}")
                return redirect("/dashboard")

        # ANALYSIS
        if resume_text and role:
            result = analyze_resume(resume_text, role)

            db = get_db()
            try:
                user = db.query(models.User).filter_by(email=session["user"]).first()

                db.add(models.Report(
                    user_id=user.id,
                    resume_text=resume_text,
                    results=json.dumps(result)
                ))
                
                # Track analytics
                db.add(models.Analytics(
                    user_id=user.id,
                    action="resume_analysis",
                    data=json.dumps({"role": role, "score": result.get("Score", "0%")}),
                    timestamp=str(datetime.now())
                ))
                
                db.commit()
            except Exception as e:
                db.rollback()
                flash(f"Database error: {str(e)}")
            finally:
                db.close()
        else:
            flash("Enter role and resume")

    return render_template("dashboard.html", result=result)


@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    try:
        user = db.query(models.User).filter_by(email=session["user"]).first()
        reports = db.query(models.Report).filter_by(user_id=user.id).order_by(models.Report.id.desc()).all()

        formatted_reports = []
        for r in reports:
            try:
                result = json.loads(r.results)
            except Exception:
                result = {}
            formatted_reports.append({
                "id": r.id,
                "role": result.get("Role", "Unknown"),
                "score": result.get("Score", "N/A"),
                "missing": result.get("Missing Skills", []),
                "detected": result.get("Detected Skills", []),
                "roadmap": result.get("Roadmap", []),
                "resume_preview": (r.resume_text[:200] + "...") if len(r.resume_text) > 200 else r.resume_text
            })

        return render_template("history.html", reports=formatted_reports)
    finally:
        db.close()


@app.route("/history/<int:report_id>")
def history_detail(report_id):
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    try:
        user = db.query(models.User).filter_by(email=session["user"]).first()
        report = db.query(models.Report).filter_by(id=report_id, user_id=user.id).first()
        if not report:
            flash("Report not found")
            return redirect("/history")

        try:
            result = json.loads(report.results)
        except Exception:
            result = {}

        return render_template("history_detail.html", report=report, result=result)
    finally:
        db.close()


@app.route("/history/delete/<int:report_id>", methods=["POST"])
def delete_history(report_id):
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    try:
        user = db.query(models.User).filter_by(email=session["user"]).first()
        report = db.query(models.Report).filter_by(id=report_id, user_id=user.id).first()
        if report:
            db.delete(report)
            db.commit()
            flash("Report deleted successfully")
        else:
            flash("Report not found")
    except Exception as e:
        db.rollback()
        flash(f"Unable to delete report: {str(e)}")
    finally:
        db.close()

    return redirect("/history")


@app.route("/analytics")
def analytics():
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    try:
        user = db.query(models.User).filter_by(email=session["user"]).first()
        
        # Get user's analytics
        user_analytics = db.query(models.Analytics).filter_by(user_id=user.id).all()
        
        # Simple stats
        total_analyses = len([a for a in user_analytics if a.action == "resume_analysis"])
        avg_score = 0
        if total_analyses > 0:
            scores = []
            for a in user_analytics:
                if a.action == "resume_analysis" and a.data:
                    data = json.loads(a.data)
                    score_str = data.get("score", "0%")
                    scores.append(int(score_str.rstrip("%")))
            avg_score = sum(scores) / len(scores) if scores else 0
        
        return render_template("analytics.html", 
                             total_analyses=total_analyses, 
                             avg_score=round(avg_score, 1))
    finally:
        db.close()


if __name__ == "__main__":
    app.run(debug=False)