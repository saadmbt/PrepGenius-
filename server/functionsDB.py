from dotenv import load_dotenv
import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError


# Load environment variables from .env file
load_dotenv()
mongodb_url=os.environ.get("MONGO_URL")  
mongodb_name=os.environ.get("MONGO_DB")
# Connect to MongoDB
client = MongoClient(mongodb_url)
db = client[mongodb_name]
# get the last id in any collection 
def lastID(collection_name):
    try:
        collection = db[collection_name]
        last_document = collection.find_one(sort=[("id", -1)])
        id=last_document.get("id") if last_document else None

        return id+1
    except PyMongoError as e:
        return f"Error fetching last id: {str(e)}"
def insert_user(user_data):
    try:
        collection = db["users"]
        # Check if the user already exists
        existing_email = collection.find_one({'email': user_data["email"]})
        if existing_email:
            return "error : email already exists"
        existing_username = collection.find_one({'username': user_data["username"]})
        if existing_username:
            return "error : Username already exists"

        # If user does not exist, insert the new user
        result=collection.insert_one(user_data)
        return result.inserted_id
        
    except PyMongoError as e:
            return f"Error : fetching user :{str(e)}"

def Fetch_user(user_Info,typeInfo):
    try:
        collection = db["users"]
        if typeInfo =="email":
            user = collection.find_one({"email": user_Info})
        if typeInfo =="objectid":
            user = collection.find_one({"_id": user_Info})
        if user is None:
            return "error : User not found"
        else :
            return user
    except PyMongoError as e:
        return f"Error : fetching user {str(e)}"

def insert_Lessons(lesson_obj):
    try:
        collection=db["lessons"]
        lesson=lesson_obj
        existing_Lesson = collection.find_one({'id': lesson["id"]})
        # {"content":,"lesson-url":,"language":,"createdAt":}
        if existing_Lesson:
            return "error : lesson already exist"
        
        result=collection.insert_one(lesson)
        return result.inserted_id

    except PyMongoError as e :
        return f"Error : inserting lesson {str(e)}"
    
def Fetch_Lesson(lesson_id):
    try :
        collection=db["lessons"]
        lesson=collection.find_one({"_id": lesson_id})
        if lesson is None:
            return "error :Lesson not found"
        else :
            lesson["_id"]=str(lesson["_id"])
            return lesson
    except PyMongoError as e :
        return  f"Error fetching lessondetails{str(e)}"

def fetch_all_lessons_by_user(user_id):
    try :
        # return list of the lessons in the db created by the author 
        collection=db["lessons"]
        lessons=list(collection.find({"author":user_id}))
        for lesson in lessons:
            lesson["_id"]=str(lesson["_id"])
            lesson["id"]=str(lesson["id"])
        return lessons
    
    except PyMongoError as e :
        return f"Error fetching lessons: {str(e)}"

def insert_Quizzes(Quiz_data):
    try:
        collection=db["quizzes"]
        quiz=Quiz_data
        existing_quiz = collection.find_one({'id': quiz["id"]})
        if existing_quiz:
            return "error : quiz already exist"
        # Quiz_data formt :{"questinId":,"questions":,"type":,"createdAt":,"updatedAt":}
        result=collection.insert_one(quiz)
        return result.inserted_id
    except PyMongoError as e :
        return f"Error inserting quiz {str(e)}"
    
def Fetch_Quizzes(Quiz_id):
    try :
        collection=db["quizzes"]
        quiz=collection.find_one({"_id": Quiz_id})
        if quiz is None:
            return "error : Quiz not found"
        else :
            quiz["_id"]=str(quiz["_id"])
            return quiz
    except PyMongoError as e :
        return f"Error : fetching quiz {str(e)}"

def Insert_Quiz_Results(Quiz_res):
    try:
        collection=db["quizzResult"]
        quizzResult=Quiz_res
        existing_quiz = collection.find_one({'id': quizzResult["id"]})
        if existing_quiz:
            return "error : quizResult already exist"
        #Quiz_res formt should be like : {"userId":,"quizId":,"score":,"attemptDate":,"updatedAt":}
        result=collection.insert_one(quizzResult)
        return result.inserted_id
    except PyMongoError as e:
        return f"Error: inserting quiz result {str(e)}"

def Fetch_Quiz_Results(Quiz_res_id):
    try :
        collection=db["quizzResult"]
        quiz_res=collection.find_one({"_id": Quiz_res_id})
        if quiz_res is None:
            return f"error : Quiz result not found "
        else :
            return quiz_res
    except PyMongoError as e :
        return f"Error fetching quiz result :{str(e)}" 