# **Reviewfy - Django Rating System**

## **Project Overview**

Welcome to **Reviewfy**! This Django-based application allows users to view articles and submit ratings. Each article has a title and content, and users can rate articles on a scale from 0 to 5. The system efficiently handles large amounts of ratings and ensures that short-term rating spikes (such as mass manipulation) do not heavily impact the overall scores.

## **Technologies Used**

This project is built using the following technologies:

- **Django**: A high-level Python web framework that encourages rapid development and clean, pragmatic design.
- **Django REST Framework (DRF)**: A powerful toolkit for building Web APIs in Django.
- **Celery**: Asynchronous task queue/job queue based on distributed message passing. It's used here for background tasks, such as processing ratings and ensuring proper validation.
- **Redis**: A data store used for caching, queuing tasks, and managing ratings in the background.
- **PostgreSQL**: The relational database management system used for storing the application's data.
- **JWT Authentication**: Using JSON Web Tokens (JWT) for securing the API and enabling user authentication.
- **Docker**: Containerization tool used for packaging the application, making it easier to deploy across different environments.

---

## **Functionalities**

### **1. Article List**
- Displays a list of articles with the following details:
  - **Title** of the article.
  - **Number of Ratings**: Shows how many users have rated the article.
  - **Average Rating**: The average score of the ratings for the article.
  - **User's Rating** (if the user has rated the article): Shows the score the logged-in user has given to the article.

  The list is optimized to handle large amounts of data and ensure that performance remains unaffected even under high load (thousands of requests per second).

### **2. Rating an Article**
- Users can submit a rating between **0 to 5** for an article.
- If the user has already rated the article, their previous rating will be **updated** instead of creating a new entry.
- The system ensures that short-term rating spikes do not distort the average score (e.g., a campaign to downvote an article won't have a sudden massive impact).

---

## **Setup and Installation**

### **Prerequisites**
Make sure the following software is installed on your system:

- Python 3.8 or later
- Docker (for containerization)
- PostgreSQL
- Redis
- Celery

### **Local Setup Without Docker**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/amirerfantim/Reviewfy.git
   cd Reviewfy
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**:
   Create a `.env` file in the project root with the following content:
   ```ini
   # redis
   REDIS_HOST=redis
   REDIS_PORT=6379
   REDIS_CACHE_LOCATION=redis://redis:6379/2

   # app
   SUSPICION_THRESHOLD=0.2

   # celery
   CELERY_BROKER_URL=redis://redis:6379/0
   CELERY_ACCEPT_CONTENT=json
   CELERY_TASK_SERIALIZER=json
   CELERY_RESULT_BACKEND=redis://redis:6379/1
   CELERY_TIMEZONE=UTC

   # django
   SECRET_KEY=your_secret_key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   # postgresql
   DATABASE_URL=postgres://postgres:postgres@db:5432/reviewfy
   POSTGRES_DB=reviewfy
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_HOST=db
   POSTGRES_PORT=5432

   # cache
   CACHE_ENABLED=True
   CACHE_DEFAULT_TIMEOUT=100
   ARTICLES_LIST_CACHE_TIMEOUT=60

   # jwt
   JWT_ACCESS_TOKEN_LIFETIME=720
   JWT_REFRESH_TOKEN_LIFETIME=7
   ```

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser** (for accessing the Django admin):
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

Now, you can access the application at `http://127.0.0.1:8000`.

---

### **Local Setup Using Docker**

1. **Build the Docker image**:
   ```bash
   docker-compose build
   ```

2. **Start the containers**:
   ```bash
   docker-compose up
   ```

   This will run all necessary services: Django app, PostgreSQL, Redis, and Celery.

3. **Access the application**:  
   Visit `http://127.0.0.1:8000` in your browser.

---

## **How It Works**

### **Rating System**
- When a user submits a rating for an article, the rating is initially stored in **Redis**.
- A periodic task runs that calculates the **suspicion factor** for the rating. This suspicion factor helps to identify and manage potentially manipulated ratings.

### **Suspicious Rating Handling**
- If the **suspicion factor** of a rating is above the defined **threshold**, it is classified as suspicious and processed in a specific task designed for suspicious ratings.
- If the suspicion factor is below the threshold, the rating is processed normally.
- The system applies only 20% of the older ratings each time to ensure that a sudden surge in ratings (like a spam attack) doesn't drastically alter the average score. 

Thanks for the clarification! Here’s the updated explanation for the **Hourly Rating Fluctuation** factor in the **Reviewfy** project, reflecting that the comparison is made with the same time on the previous day, rather than the previous hour:



### **Suspicion Factor Calculation Explained**

The **suspicion factor** for each rating is calculated based on the following factors:

1. **Hourly Rating Fluctuation**:
   - This factor checks how the number of ratings for an article has changed in the last hour compared to the same hour on the previous day. If there is a significant increase in ratings (over 100%), it may indicate that a large group of users suddenly started rating the article, which could be an attempt to manipulate the score. If this happens, the suspicion factor is applied.
   
   - **For example**:  
     If there were 10 ratings for an article between 2:00 PM and 3:00 PM on the previous day, and there are 30 ratings for the article between 2:00 PM and 3:00 PM today, this represents a **200% increase**. This would trigger a suspicion factor increase to account for potential manipulation.

2. **User's Rating History**:
   - If a user has been consistently giving extreme ratings (either 0 or 5) for different articles, it could indicate abnormal behavior. This increases the suspicion factor.
   
   - **For example**:  
     If the user has rated 10 articles recently, and 8 of them are rated either 0 or 5, this triggers a higher suspicion factor.

3. **Recent Article Ratings**:
   - This factor compares the current rating to the recent ratings of the article over the last week. If the score deviates significantly from the mean of recent ratings, it is considered suspicious.
   
   - **For example**:  
     If an article has been rated around 3.5 for the last week and a new rating is suddenly 5 or 0, this could be flagged as suspicious and a suspicion factor is applied.

---

## **Testing the Application**

### **1. Unit Tests**
Unit tests are included in the project to verify functionality, especially for critical components such as rating submission, updating, and article listing.

- To run the tests, use:
  ```bash
  python manage.py test
  ```

### **2. API Testing**
You can test the APIs using tools like **Postman** or **cURL**. Here are the available endpoints:

- **POST /api/auth/register/**: Register a new user.
- **POST /api/auth/login/**: Login to get a JWT token.
- **GET /api/articles/**: List all articles with their ratings and average score.
- **POST /api/articles/create/**: Create a new article.
- **POST /api/articles/rate/**: Rate an article.

---

## **Conclusion**

This project provides a scalable solution for managing articles and their ratings. It efficiently handles millions of ratings without performance degradation and includes protective measures to prevent manipulation of article scores. The use of Django, DRF, Celery, and Redis ensures that the application can handle high traffic and large datasets effectively.

We hope this README helps you set up and test the project. Enjoy building and testing your Django Rating System!

---

Let me know if you'd like any further changes or adjustments!