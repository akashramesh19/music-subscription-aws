# Music Subscription AWS

A cloud-based music subscription web application built with Python and AWS services (DynamoDB, S3, EC2, ECS, Lambda + API Gateway).

## Team Members

| Name | Student ID |
|------|------------|
| Akash Ramesh | S4097941 |
| Abdul Rahman Sahabudeen | S4123171|
| Murali GMD | S4110587 |
| Varun S V | S4129948 |

## How to Run

### 1. Setup — DynamoDB Tables & S3

```bash
cd setup
python create_login_table.py
python create_music_table.py       # also loads song data from 2026a2_songs.json
python create_subscriptions_table.py
python upload_images_to_s3.py
```

### 2. Backend

**EC2**
```bash
cd backend/ec2
pip install -r requirements.txt
python app.py
```

**ECS**
```bash
cd backend/ecs
docker build -t music-subscription .
docker run -p 80:80 music-subscription
```

**Lambda**
Deploy each function under `backend/lambda/` via the AWS Console or AWS CLI, then configure API Gateway routes.

### 3. Frontend

Upload the contents of `frontend/` to an S3 bucket configured for static website hosting, or open `login.html` directly in a browser pointed at the active backend.
