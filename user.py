from datetime import datetime
from http import HTTPStatus
from flask import request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from flask_restful import Resource
from mysql.connector.errors import Error
import mysql.connector
from mysql_connection import get_connection
from email_validator import validate_email, EmailNotValidError
from utils import check_password, hash_password

# Flask 프레임워크의 기본 문법이 괄호에 Resource 적는 것임.
# POST /users/register
class UserRegisterResource(Resource):
    def post(self):

        # 데이터 입력 예시
        # {
        # "username":"홍길동" , 
        # "email":"abc@naver.com" , 
        # "password" : 1234
        # }

        # 1. 클라이언트가 body 에 보내준 json을 받아온다.
        data = request.get_json()

        # 2. 이메일 주소형식이 제대로 된 주소형식인지 확인하는 코드 작성  
        email = data['email']

        try:
            email = validate_email(email).email
        
        except EmailNotValidError as e:
           return {"error" : str(e)} , 400

        
        # 3. 비밀번호의 길이가 유효한지 체크한다.
        if len(data['password']) < 4 or len(data['password']) > 12 :
            return { "error" : '비밀번호 길이는 4자 이상 12자 이하로 작성하세요.'} , 400


         # 4. 비밀번호 암호화
        password = data['password']
        
        hashed_password = hash_password(password)

        # 5. 데이터베이스에 회원정보를 저장한다.

        try :
            # 데이터 insert
            # 5-1. DB 연결
            connection = get_connection()

            # 5-2. 쿼리문 만들기 (%s는 변수 처리해준다는 뜻) 
            query = '''insert into user
                    (username, email, password)
                    values
                    ( %s, %s, %s);'''

            record = (data['username'], data['email'], hashed_password )
            
            # 5-3. 커서를 가져온다.
            cursor = connection.cursor()

            # 5-4. 커서를 이용해서 쿼리문을 실행한다.
            cursor.execute(query, record)

            # 5-5. 커넥션을 커밋해줘야 한다. == DB에 영구적으로 반영하라는 것임.
            connection.commit()

            # 5-6. user_id 값을 가져온다.
            user_id = cursor.lastrowid

            # 5-7. 자원 해제
            cursor.close()
            connection.close()

        except mysql.connector.Error as e:
            print(e)
            cursor.close()
            connection.close()
            # HTTPStatus.SERVICE_UNAVAILABLE  == 503
            return {'error' : str(e)}, 503

        # user_id 를 바로 보내면 안되고,
        # JWT 로 암호화 해서 보내준다.
        # 암호화 하는 방법
        access_token = create_access_token(user_id)

        return {'result' : 'success', 
                'access_token' : access_token }, 200

        ### 회원가입 시 user_id에 대한 정보가 없음
        ### user_id는 두 테이블을 이어주는 Foreign Key 가 되기 때문에 중요함.
        ### user 테이블의 id를 recipe 테이블의 user_id로 넣어줘야한다는 뜻

       
class UserLoginResource(Resource):
    def post(self):

    # {
    # "email":"abc123@naver.com" ,
    # "password":"1234"
    # }

        data = request.get_json()
        email = data['email']

        #1. 로그인 시 들어온 email로 DB데이터 가져오기
        try :
            
            connection = get_connection()

            query = '''select * from user
                    where email = %s;'''
            
            record = (email,)

            # select 문은 dictionary = True 해준다.

            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, record)

            # select 문은, 아래 함수를 이용해서, 데이터를 가져온다.
            result_list = cursor.fetchall()

            print(result_list)

            # 중요! 디비에서 가져온 timestamp 는 
            # 파이썬의 datetime 으로 자동 변경된다.
            # 문제는! 이데이터를 json 으로 바로 보낼수 없으므로,
            # 문자열로 바꿔서 다시 저장해서 보낸다.
            i = 0
            for record in result_list :
                result_list[i]['created_at'] = record['created_at'].isoformat()
                result_list[i]['updated_at'] = record['updated_at'].isoformat()
                i = i + 1      

            cursor.close()
            connection.close()

        except mysql.connector.Error as e:
            print(e)
            cursor.close()
            connection.close()

            return {"error": str(e)}, 503

        # 3. result 의 행의 개수가 1개이면 유저 데이터를 정상적으로 받아온 것이고
        #    행의 갯수가 0이면, 요청한 이메일은, 회원가입이 되어있지않은 이메일이다.
        if len(result_list) != 1:
            return {"error": '회원가입이 안된 이메일입니다.'}, 400

        # 4. 비밀번호가 맞는지 확인한다.
        user_info = result_list[0]

        # data['password']와 user_info['password']를 비교
        
        check = check_password(data['password'], user_info['password'])

        if check == False :
            return {'error' : '비밀번호가 맞지 않습니다.'}
        
        access_token = create_access_token(user_info['id'])

        # JWT_ACCESS_TOKEN_EXPIRES 를 True로 두고 
        # create_access_token(user_id, expires_delta=datetime.timedelta(minutes= 1)) 을 하면 1분이 지나면 로그아웃된다.

        return {'result':'success',
        'user_id' : access_token}, 200 

jwt_blacklist = set()

# 로그아웃 클래스
class UserLogoutResource(Resource):
    # 로그인한 유저만 로그아웃할 수 있으므로 jwt_required
    @jwt_required()
    def post(self):

        jti = get_jwt()['jti']
        print(jti)

        jwt_blacklist.add(jti)

        return {'result' : 'success'}, 200