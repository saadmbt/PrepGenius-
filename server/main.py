from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity, decode_token, get_jwt
)
from bson.objectid import ObjectId
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
from functionsDB import (
    insert_Lessons, Fetch_Lesson, 
    fetch_all_lessons_by_user, Fetch_Quizzes,
    Insert_Quiz_Results, Fetch_Quiz_Results, lastID,
    insert_group, add_student_to_group, get_group_by_code,
    get_professor_groups, get_student_groups, Fetch_Groups, get_group_by_id, get_professor_by_id
)
from main_functions import (save_to_azure_storage, create_token, check_request_body, get_file_type)
from file_handling import file_handler
from image_Handling import image_handler
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, auth
import tempfile
from LLM_functions import generate_and_insert_questions 
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app, origins=['http://localhost:5173'], methods=['GET', 'POST', 'PUT', 'DELETE'], headers=['Content-Type', 'Authorization'])

# Load credentials from environment variables
load_dotenv()
# Load the service account key from the environment variable
service_account_key = json.loads(os.environ['SERVICE_ACCOUNT_KEY'])
# Initialize Firebase Admin
cred = credentials.Certificate(service_account_key) 
firebase_admin.initialize_app(cred)

# JWT Configuration
app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_TOKEN_SECRET')
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=3)
jwt = JWTManager(app)

# Replace with your Dropbox access token
DropBox_Access_Token = os.environ.get('DropBox_access_token')

# User Management Endpoints
@app.route('/api/auth', methods=['POST'])
def login():
    """
    Authenticate a user using the Firebase Auth uid.

    :return: A JSON response with an access token
    """
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    uid = data["uid"]
    try:
        user = auth.get_user(uid)
        if user is None:
            return jsonify({"error": "Invalid or unknown UID"}), 401

        access_token = create_token(uid)
        response = jsonify({"access_token": access_token})

        # Set the access token in a cookie
        response.set_cookie(
            'access_token', 
            access_token, 
            # httponly=True,  # Prevent JavaScript access to the cookie
            # secure=True,    # Use secure cookies (only sent over HTTPS)
            # samesite='Lax'  # Helps prevent CSRF attacks
        )
        return response, 201
    except ValueError as e:
        return jsonify({'error': f'Invalid token format: {str(e)}'}), 400
    except auth.InvalidIdTokenError:
        return jsonify({'error': 'Invalid or expired token'}), 401
    except Exception as e:
        return jsonify({'error': f'Authentication failed: {str(e)}'}), 500

@app.route('/api/profile', methods=['GET'])
# @jwt_required()
def profile():
    uid = "get_jwt_identity()"
    try:
        user = auth.get_user(uid)
        # dictionary of user information
        user_info = {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "createdAt": user.user_metadata.creation_timestamp,
            "lastLoginAt": user.user_metadata.last_sign_in_timestamp,
        }
        response = jsonify({"user": user_info})
        return response, 200
    except auth.UserNotFoundError:
        return jsonify({'error': 'User not found'}), 404

# Lesson Management Endpoints
@app.route('/api/upload', methods=['POST'])
# @jwt_required()
def handle_theuploaded():
    # Check if the request body is text, file, or image
    request_type = check_request_body()
    if request_type is None:
        return jsonify({"error": "Request type could not be determined."}), 400

    # Limit file size to 10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    New_id = lastID("lessons")

    if request_type == "text":
        lesson_obj = {
            "title": request.form["title"],
            "id": New_id,
            "author": "get_jwt_identity()",
            "content": request.form['text'],
            "uploadedAt": datetime.now(timezone.utc).isoformat(),
        }
        lesson_objid = insert_Lessons(lesson_obj)
        response = jsonify({'message': 'Lesson uploaded successfully', "lesson_id": str(lesson_objid)})
        return response, 201
    
    elif request_type == "file":
        file = request.files['file']
        filename = secure_filename(file.filename)
        if file.content_length > MAX_FILE_SIZE:
            return response,400
    # Limit file size to 10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    New_id = lastID("lessons")

    if request_type=="text":
        # Get the data from the request body
        lesson_obj={
            "title":request.form["title"],
            "id":New_id,
            "author":"get_jwt_identity()",
            "content" :request.form['text'],
            "uploadedAt": datetime.now(timezone.utc).isoformat(),
        }
        # Save the text to the database
        lesson_objid = insert_Lessons(lesson_obj)
        response =jsonify({'message': 'Lesson uploaded successfully',"lesson_id":str(lesson_objid)})
        return response, 201
    
    elif request_type=="file":
        # Get the file from the request

        file=request.files['file']
        # Secure the filename
        filename = secure_filename(file.filename)
        # Check file size
        if file.content_length > MAX_FILE_SIZE:
            return jsonify({"error": "File size exceeds the 10MB limit."}), 400
        # Save the file to Azure storage

        try:
            # Proccess the file 
            file_content = file.read()
            file_extracted_text=file_handler(file_content,filename)
            print("l317 :",len(file_extracted_text))
            url = save_to_azure_storage(file_content,filename)
            print("l 311",url)
            # Get the data from the request body
            lesson_obj={
                "title":request.form["title"],
                "id":New_id,
                "author":"get_jwt_identity()",
                "content" :file_extracted_text,
                "lesson_save_link":str(url),
                "uploadedAt": datetime.now(timezone.utc).isoformat(),
            }
            # Save the dictionary Lesson to the database
            lesson_objid = insert_Lessons(lesson_obj)
            response =jsonify({'message': 'Lesson uploaded successfully',"lesson_id":str(lesson_objid)})
            return response, 200
        except Exception as e:
            response = jsonify({"error": "File processing error: " + str(e)})

            return response, 400
        
    # case if the file is image
    elif request_type=="img":
        # Get the image from the request

        image=request.files['file']
        # Secure the filename
        try:
            filename = secure_filename(image.filename)
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                image.save(temp_file.name)

                # Upload to Azure Blob Storage (if needed)
                url = save_to_azure_storage(temp_file.name, filename)  # Pass the temporary file path

                # Read image data from the temporary file **after saving**
                with open(temp_file.name, 'rb') as f:
                    image_data = f.read()
                    print(f"Image data read: {len(image_data)} bytes")  # For debugging

                # Process the image
                extracted_text = image_handler(image_data, filename)
            # Get the data from the request body
            lesson_obj={
                "title":request.form["title"],
                "id":New_id,
                "author":"get_jwt_identity()",
                "content" :extracted_text,
                "lesson_save_link":str(url),
                "uploadedAt": datetime.now(timezone.utc).isoformat(),
            }
            # Save the dictionary Lesson to the database
            lesson_objid = insert_Lessons(lesson_obj)
            response =jsonify({'message': 'Lesson uploaded successfully',"lesson_id":str(lesson_objid)})
            return response, 201 
        except Exception as e:
            return jsonify({"error image": str(e)}), 400
        # finally:
        # # Clean up the temporary file
        # if os.path.exists(temp_file_name):
        #     os.remove(temp)
    else:
        return jsonify({"error": "Invalid request type"}), 400
    
@app.route('/api/lessons', methods=['GET'])
# @jwt_required()
def fetch_lessons():
    """
    Fetch all lessons for the authenticated user.
    Returns:
        Response: JSON response containing the lessons or an error message.
    """
    # Get the user's id from the JWT token 
    user_id = "get_jwt_identity()"
    # Fetch all lessons for the authenticated user.
    lessons = fetch_all_lessons_by_user(user_id)
    print("lenght of the array",len(lessons))
    if lessons is None or len(lessons) == 0:
        return jsonify({"error": "No lessons found"}), 404
    if isinstance(lessons, str) and "error" in lessons.lower():
        return jsonify({"error": lessons}), 500

    return jsonify(lessons), 200

@app.route('/api/lessons/<lesson_id>', methods=['GET'])
# @jwt_required()
def fetch_lesson(lesson_id):
    """
    Fetch a specific lesson by its ID.
    
    Args:
        lesson_id (str): The ID of the lesson to fetch.
        
    Returns:
        Response: JSON response containing the lesson or an error message.
    """
    try:
        lesson_obj_id = ObjectId(lesson_id)
    except Exception as e:
        return jsonify({"error": "Invalid lesson_id"}), 400

    try:
        lesson = Fetch_Lesson(lesson_obj_id)
        return jsonify(lesson), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 404

# Quiz Management Endpoints
@app.route('/api/create_quiz', methods=['POST'])
# @jwt_required()
def create_quiz():
    #par: lessonid, type of question, number of question, dif of question
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    lesson_id = data["lesson_id"]
    question_type = data["type"]
    num_questions = data["number"]
    difficulty = data["difficulty"]
    if not lesson_id or not question_type or not num_questions or not difficulty:
        return jsonify({"error": "Missing required parameters"}), 400
    # function to create the quiz and insert it to the database and return the quiz id
    quiz_result=generate_and_insert_questions(lesson_id,question_type,num_questions,difficulty)
    if "error" in str(quiz_result).lower():
        return jsonify({"error": quiz_result}), 400

    return jsonify({"message": "Quiz created successfully", "quiz_id": str(quiz_result)}), 201
#just for show the quiz if needed 
@app.route('/api/quizzes/<quiz_id>', methods=['GET'])
# @jwt_required()
def fetch_quiz(quiz_id):
    quiz = Fetch_Quizzes(ObjectId(quiz_id))
    if quiz is None:
        return jsonify({"error": "Quiz not found"}), 404
    if isinstance(quiz, str) and "error" in quiz.lower():
        return jsonify({"error": str(quiz)}), 404

    return jsonify(quiz), 200
"""yet"""
# Quiz Results Management Endpoints
@app.route('/api/quiz_results/<quiz_id>', methods=['GET'])
# @jwt_required()
def fetch_quiz_results(quiz_id):
    """Fetches the quiz results for a given quiz ID.
    This endpoint requires a valid JWT token to access.
    Args:
        quiz_id (str): The ID of the quiz for which results are to be fetched.
    Returns:
        Response: A JSON response containing the quiz results if found, 
                or an error message if the quiz results are not found or an error occurs.
                The response status code is 200 for success and 404 for errors.
    """
    quiz_results = Fetch_Quiz_Results(ObjectId(quiz_id))
    if quiz_results is None:
        return jsonify({"error": "Quiz results not found"}), 404
    if isinstance(quiz_results, str) and "error" in quiz_results.lower():
        return jsonify({"error": str(quiz_results)}), 404
    
    return jsonify(quiz_results), 200

# Quiz Results Management Endpoints
@app.route('/api/quiz_results/insert', methods=['POST'])
# @jwt_required()
def create_quiz_results():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    quiz_id = data["quiz_id"]
    user_id = data["user_id"]
    score = data["score"]
    attempt_date = data["attempt_date"]
    if not attempt_date:
        attempt_date = datetime.now(timezone.utc).isoformat()
    if not quiz_id or not user_id or not score:
        return jsonify({"error": "Missing required parameters"}), 400
    # function to create the quiz and insert it to the database and return the quiz id
    quiz_result = {
        "quiz_id": quiz_id,
        "user_id": user_id,
        "score": score,
        "attempt_date": attempt_date,
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }
    # Insert the quiz result into the database
    quiz_result_id = Insert_Quiz_Results(quiz_result)
    if "error" in str(quiz_result_id).lower():
        return jsonify({"error": str(quiz_result_id)}), 500
    
    return jsonify({"message": "Quiz result created successfully", "quiz_result_id": str(quiz_result_id)}), 201
#groups management
# 1. Fetch Groups for a Professor (GET /api/groups/<ProfId>)
@app.route('/api/groups/<ProfId>', methods=['GET'])
# @jwt_required()
def get_groups(ProfId):
    groups = Fetch_Groups(ProfId)
    if isinstance(groups, str) and "error" in groups.lower():
        return jsonify({"error": str(groups)}), 500
    if not groups:
        return jsonify({"error": "Groups not found"}), 404
    return jsonify(groups), 200

# 2. Create a New Group (POST /api/groups)
@app.route('/api/groups', methods=['POST'])
def create_group():
    try:
        data = request.get_json()
        if not data or not all(key in data for key in ["group_name", "prof_id"]):
            return jsonify({
                "success": False,
                "error": "Missing required fields"
            }), 400

        result = insert_group(data)
        if result.get("success"):
            return jsonify(result), 201
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 4. Get a Group by Group ID and Professor ID (GET /api/groups/<group_id>/<prof_id>)
@app.route('/api/groups/<group_id>/<prof_id>', methods=['GET'])
# @jwt_required()
def get_group(group_id, prof_id):
    group = get_group_by_code(group_id, prof_id)
    if isinstance(group, str) and "error" in group.lower():
        return jsonify({"error": str(group)}), 500
    if not group:
        return jsonify({"error": "Group not found"}), 404
    return jsonify(group), 200

# 5. Get All Groups Created by a Professor (GET /api/professor-groups/<prof_id>)
@app.route('/api/professor-groups/<prof_id>', methods=['GET'])
# @jwt_required()
def get_professor_groups_route(prof_id):
    groups = get_professor_groups(prof_id)
    if isinstance(groups, str) and "error" in groups.lower():
        return jsonify({"error": str(groups)}), 500
    if not groups:
        return jsonify({"error": "No groups found for this professor"}), 404
    return jsonify(groups), 200

# 6. Get All Groups a Student Belongs To (GET /api/student-groups/<student_uid>)
@app.route('/api/student-groups/<student_uid>', methods=['GET'])
# @jwt_required()
def get_student_groups_route(student_uid):
    groups = get_student_groups(student_uid)
    if isinstance(groups, str) and "error" in groups.lower():
        return jsonify({"error": str(groups)}), 500
    if not groups:
        return jsonify({"error": "No groups found for this student"}), 404
    return jsonify(groups), 200

# Generate invitation link
@app.route('/api/generate-invite-link', methods=['POST'])
def generate_invite_link():
    try:
        data = request.get_json()
        if not data or 'group_id' not in data:
            return jsonify({"error": "Missing group_id in request"}), 400

        group_id = data['group_id']
        
        # Verify group exists
        group = get_group_by_id(group_id)
        if not group:
            return jsonify({"error": "Group not found"}), 404

        # Create token
        token = create_access_token(
            identity={"group_id": group_id},
            expires_delta=timedelta(days=7)
        )
        
        invite_link = f"http://localhost:5173/Student/join-group/{token}"
        return jsonify({"invite_link": invite_link}), 200

    except Exception as e:
        print(f"Error generating invite link: {str(e)}")
        return jsonify({"error": "Failed to generate invitation link"}), 500

# Join a group
@app.route('/api/groups/join', methods=['POST'])
@jwt_required()
def join_group():
    try:
        data = request.get_json()
        if not data or 'token' not in data:
            return jsonify({"error": "Missing token"}), 400

        student_uid = get_jwt_identity()
        token = data['token']
        
        # Decode the invitation token
        try:
            decoded = decode_token(token)
            group_id = decoded['sub'].get('group_id') if isinstance(decoded['sub'], dict) else None
            
            if not group_id:
                return jsonify({"error": "Invalid invitation token"}), 400
            
            # Verify group exists
            group = get_group_by_id(group_id)
            if not group:
                return jsonify({"error": "Group not found"}), 404
            
            # Add student to group
            result = add_student_to_group(group_id, student_uid)
            if isinstance(result, str) and "error" in result.lower():
                return jsonify({"error": result}), 500
            if not result:
                return jsonify({"error": "Failed to add student to group"}), 400
            
            return jsonify({"message": "Successfully joined group", "group": group}), 200
            
        except Exception as e:
            return jsonify({"error": f"Invalid token: {str(e)}"}), 400
            
    except Exception as e:
        return jsonify({"error": f"Failed to join group: {str(e)}"}), 500

# Validate invitation token
@app.route('/api/validate-invite-token', methods=['POST'])
@jwt_required()
def validate_invite_token():
    token = request.json.get('token')
    
    if not token:
        return jsonify({"error": "Missing token"}), 400
    
    try:
        # Decode the token to get professor ID and group ID
        decoded = decode_token(token)
        token_payload = decoded['sub']
        
        # Handle both string and dictionary identities
        if isinstance(token_payload, dict):
            professor_id = token_payload.get('prof_id')
            group_id = token_payload.get('group_id')
        else:
            # For backward compatibility with older tokens
            professor_id = token_payload
            group_id = None
            
        if not group_id:
            return jsonify({"error": "Invalid token: missing group_id"}), 400
        
        # Get group information using group_id
        group = get_group_by_id(group_id)
        if not group:
            return jsonify({"error": "Group not found"}), 404
        
        # Get professor information
        professor = get_professor_by_id(professor_id)
        
        # Return group and professor info
        return jsonify({
            "group_name": group.get("group_name", "Unknown Group"),
            "professor_name": professor.get("name", "Unknown Professor"),
            "professor_id": professor_id,
            "group_id": group_id
        }), 200
    except Exception as e:
        return jsonify({"error": f"Invalid token: {str(e)}"}), 400





@app.route('/api/refresh_token', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = "get_jwt_identity()"
    new_access_token = create_access_token(identity=current_user)
    return jsonify({"access_token":new_access_token}), 200

@app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = (now + timedelta(minutes=20)).timestamp()
        
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity="get_jwt_identity()")
            data = response.get_json()
            if isinstance(data, dict):  # Check if the response data is a dictionary
                data["access_token"] = access_token 
                import json
                response.set_data(json.dumps(data))  # Update the response data
                response.content_type = "application/json"  # Ensure the content type is set to JSON
                # Set the access token in a cookie
                response.set_cookie(
                    'access_token', 
                    access_token, 
                    httponly=True,  # Prevent JavaScript access to the cookie
                    secure=True,    # Use secure cookies (only sent over HTTPS)
                    samesite='Lax'  # Helps prevent CSRF attacks
                )
        return response
    except (RuntimeError, KeyError):
        return response
@app.route('/api/')
def hello_world():
    print("hi")
    return "Hello, World!"

if __name__ == "__main__":
    app.run()
