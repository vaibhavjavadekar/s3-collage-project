# S3 Cloud Drive & Collage Generator (Microservices Architecture)

## 📖 Project Overview
This project is a scalable, cloud-native microservices application built to simulate a Cloud Drive (like Google Drive or Dropbox) with a special feature that dynamically stitches user-uploaded images into a collage. 

The application demonstrates enterprise-level system design patterns, specifically the **Separation of Concerns** between unstructured data (files) and structured data (metadata), and utilizes **Presigned URLs** to allow the frontend to upload heavy files directly to S3 without bottlenecking the backend servers.

## 🏗️ Architecture & Microservices
The system is divided into four distinct, stateless Python microservices and two stateful infrastructure components, all orchestrated via Kubernetes:

1. **UI Service (Frontend & Image Processing)**
   * Serves the HTML/CSS/JS frontend interface.
   * Fetches user-specific images from the Download Service.
   * Uses the `Pillow` library to dynamically stitch images together into a custom collage on the fly.

2. **Upload Service (API Gateway for S3)**
   * Generates secure, temporary **Presigned URLs** from S3.
   * Allows the browser to upload large videos/images directly to the S3 bucket via CORS, bypassing the Python backend entirely for maximum performance.

3. **Download Service (Retrieval API)**
   * Queries the Metadata Service for a specific user's file list.
   * Fetches the raw file bytes from S3 and serves them to the UI.

4. **Metadata Service (Database Manager)**
   * Uses SQLAlchemy to interface with PostgreSQL.
   * Tracks user uploads (who uploaded what, file types, and S3 object keys) while keeping the actual heavy files out of the database.

## 🚀 Technology Stack
* **Programming Language:** Python 3.10
* **Web Framework:** Flask (REST APIs & HTML Serving)
* **Cloud Infrastructure (Mock):** LocalStack (Simulating AWS S3)
* **Database:** PostgreSQL (Relational metadata tracking)
* **Containerization:** Docker
* **Orchestration:** Kubernetes (via OrbStack for local M-series Mac compatibility)
* **Image Processing:** Pillow (PIL)
* **Database Management Tool:** DBeaver

## 🧠 Key Cloud Engineering Concepts Applied
* **Stateless Microservices:** The Python APIs store no local data, meaning they can be scaled horizontally (e.g., `kubectl scale deployment ui-service --replicas=3`) to handle traffic spikes.
* **Direct-to-Cloud Uploads:** Implemented S3 Presigned URLs to handle massive file uploads (videos/images) efficiently.
* **Polyglot/Component Isolation:** PostgreSQL is strictly reserved for fast metadata queries (user, filename, object key), while LocalStack (S3) handles cheap, infinitely scalable BLOB/Object storage.
* **Kubernetes Networking:** Utilized `ClusterIP` for internal, secure microservice-to-microservice communication, and `LoadBalancer` to expose the UI, Upload API, and Postgres directly to `localhost`.

<img width="2780" height="1745" alt="mermaid-diagram-1791120176218" src="https://github.com/user-attachments/assets/0b65ede4-01fd-49bf-b7ae-60d07fbe0efb" />
