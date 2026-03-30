from flask_restful import Resource # Class
from flask import request, jsonify, make_response
from models import Song, User
from werkzeug.security import check_password_hash as cph



def check_isUser(json_data):
    email = json_data.get('email')
    password = json_data.get('password')

    user_obj = User.query.filter_by(email=email).first()
    if user_obj and user_obj.password==password:
        return user_obj

    return False

class Test(Resource): # EXTEND
    def get(self):
        dict_data_input = request.json
        dict_data_output = {"message": "Hi with GET", "input_received": dict_data_input}
        
        json = jsonify(dict_data_output)
        return make_response(json, 200)
    
    def post(self):
        dict_data_input = request.json
        dict_data_output = {"message": "Hi with POST", "input_received": dict_data_input}
        
        json = jsonify(dict_data_output)
        return make_response(json, 200)
    
class Song(Resource):
    def get(self):
        json_data = request.json
        current_login_user = check_isUser(json_data=json_data)

        
        if current_login_user:
            songs_objs =current_login_user.songs

            output_data = [{"user_name": current_login_user.username}]
            for song in songs_objs:
                d = {
                    "id": song.id,
                    "name": song.name,
                    "isBlacklisted": song.isBlacklisted,
                }
                output_data.append(d)
            
            return make_response(jsonify(output_data), 200)
        return make_response(jsonify({"message": "User doesnot exist!!"}), 403)

