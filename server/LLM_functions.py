import googleapiclient
from groq import Groq
from dotenv import load_dotenv
import os
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from functionsDB import (Fetch_Lesson,insert_Quizzes,lastID)
from prompts_config import base_prompt ,flashcards_prompt
# Load environment variables from .env file
load_dotenv()
mongodb_url=os.environ.get("MONGO_URL")  
mongodb_name=os.environ.get("MONGO_DB")
# Connect to MongoDB
client = MongoClient(mongodb_url)
db = client[mongodb_name]

groq_client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),  
)

# take text and transform it to array of keywords for youtube video suggesting
def generate_keywords(lesson_id):
    lesson = Fetch_Lesson(lesson_id)
    if not lesson:
        raise ValueError("Lesson content is empty")
    text = lesson['content']
    if not text:
        raise ValueError("Lesson content is empty")
    if len(text) > 20000:
        text = text[:9000]
    # Generate keywords using Groq API
    try:
        completion = groq_client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {"role": "system", "content": "Given the following text, extract the most 3 relevant sentences or title that can be used to generate YouTube suggested videos. The response should only include the extracted sentence or title without any additional context or explanation ,and the return must be a list formatting."},
                        {"role": "user","content":text} 
                    ],
                    temperature=1,
                )
                
        # Extract the content from the response 
        keywords = completion.choices[0].message.content.strip()
        # Convert the keywords string into a list 
        resulat=[keyword.strip() for keyword in keywords.split(',')] if keywords else None
        if not resulat:
            raise ValueError("No keywords generated")
        return (resulat)
    except Exception as e:
        return f"An error occurred while generating keywords: {e}"
    
def generate_youtube_suggestions(keywords):
    """
    Suggest YouTube videos based on the provided keywords.
    
    Args:
        keywords (list): A list of keywords to search for on YouTube.
        
    Returns:
        list: A list of YouTube video suggestions.
    """
    api_key = os.environ.get('YOUTUBE_API_KEY')
    youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=api_key)
    
    video_suggestions = []
    
    for keyword in keywords:
        request = youtube.search().list(
            q=keyword,
            part="snippet",
            maxResults=8,
            type="video"
        )
        response = request.execute()
        
        for item in response['items']:
            video_suggestions.append({
                "title": item['snippet']['title'],
                "video_id": item['id']['videoId'],
                "channel_title": item['snippet']['channelTitle'],
                "thumbnail": item['snippet']['thumbnails']['default']['url'],
                "timestamp": item['snippet']['publishedAt'],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            })

    return video_suggestions
#  generation of flashcards based on the lesson content from the db using groq
def generate_flashcards(lesson_id):
    try:
        lesson_id = ObjectId(lesson_id)
        # Fetch the lesson from the database
        lesson = Fetch_Lesson(lesson_id)
        if not lesson:
            raise ValueError("Lesson not found")
        # Extract lesson content
        content = lesson['content']
        title = lesson['title']
        if not title:
            title = "Lesson Title"
        if not content:
            raise ValueError("Lesson content is empty")
        if len(content) > 20000:
            content = content[:12000]
        # Generate flashcards using Groq API
        prompt = flashcards_prompt.format(content=content)
        # Appeler l'API Groq pour générer les questions

        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are an expert flashcard generator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500,
        )

        # Afficher la réponse complète de l'API pour le débogage
        Flashcards_text = completion.choices[0].message.content.strip()
        # Parse the response to extract the list of Flashcards
        try:
            # Find the start and end of the JSON-like structure
            start_index = Flashcards_text.find('[')
            end_index = Flashcards_text.rfind(']') + 1

            if start_index == -1 or end_index == 0:
                raise ValueError("Invalid response format - no list found")
            # Extract the JSON-like string
            Flashcards_json = Flashcards_text[start_index:end_index]

            # Parse the JSON-like string into a Python list of dictionaries
            Flashcards = eval(Flashcards_json)
            print(Flashcards)

        except Exception as e:
            print(f"Error parsing the response: {e}")
            return None
        return Flashcards
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        return None


# MongoDB collections for lessons and quizzes
lessons_collection = db["lessons"]
quizzes_collection = db["quizzes"]

def generate_and_insert_questions(lesson_id, question_type, num_questions, difficulty):
    """Reads a lesson from MongoDB, generates questions using the Groq API,
    and inserts the generated questions into the "quizzes" collection."""
    try:
        # Convertir l'ID de la leçon en ObjectId si nécessaire
        if not isinstance(lesson_id, ObjectId):
            lesson_id = ObjectId(lesson_id)
        
        # Récupérer la leçon de MongoDB
        lesson = Fetch_Lesson(lesson_id)
        if not lesson:
            raise ValueError("Leçon introuvable")
        
        # Récupérer le contenu de la leçon
        content = lesson.get('content')
        title = lesson.get('title')
        author = lesson.get('author')
        if not title:
            raise ValueError("Le titre de la leçon est vide")

        if not content:
            raise ValueError("Le contenu de la leçon est vide")
        
        if len(content) > 20000:
            content= content[:19000]
        
        # Construire la requête pour l'API Groq en fonction des paramètres
        # Standardize prompt format
        prompt = base_prompt[question_type].format(
            num=num_questions,
            difficulty=difficulty,
            content=content
        )
        # Appeler l'API Groq pour générer les questions
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Tu es un professeur expert. Génère des questions de qualité pour un quiz."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500,
        )

        # Afficher la réponse complète de l'API pour le débogage
        questions_text = completion.choices[0].message.content.strip()
        # Parse the response to extract the list of questions
        try:
            # Find the start and end of the JSON-like structure
            start_index = questions_text.find('[')
            end_index = questions_text.rfind(']') + 1

            if start_index == -1 or end_index == 0:
                raise ValueError("Invalid response format - no list found")
            # Extract the JSON-like string
            questions_json = questions_text[start_index:end_index]

            # Parse the JSON-like string into a Python list of dictionaries
            questions = eval(questions_json)
            print(questions)

        except Exception as e:
            print(f"Error parsing the response: {e}")
            return None
        # Insérer les questions dans MongoDB
        question_id = lastID('quizzes')
        if not isinstance(question_id, int):
            raise ValueError(f"Invalid question ID returned by lastID: {question_id}")
        quiz = {
            "id": question_id + 1,
            "title": title,
            "generated_by": author,
            "type": question_type,
            "questions": questions,
            "createdAt": datetime.now()
        }
        inserted_quiz_id = insert_Quizzes(quiz)
        if isinstance(inserted_quiz_id, ObjectId):
            print(f"Questions générées et insérées avec succès. ID du quiz : {str(inserted_quiz_id)}")
            quiz["_id"] = str(inserted_quiz_id)
            return quiz
        else:
            raise ValueError("Erreur lors de l'insertion du quiz.")
    except Exception as e:
        print(f"Erreur lors de la génération des questions : {e}")
        return None