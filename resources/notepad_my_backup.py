from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from mysql.connector.errors import Error
from mysql_connection import get_connection
import mysql.connector


class NotepadaddResource(Resource):
    @jwt_required()
    def get(self):
        # 쿼리 스트링으로 오는 데이터는 아래처럼 처리해준다.
        offset = request.args.get('offset')
        limit = request.args.get('limit')

        # 디비로부터 데이터를 받아서, 클라이언트에 보내준다.
        try :
            connection = get_connection()

            user_id = get_jwt_identity()

            query = '''select *
                    from notepad
                    where user_id = %s;'''

            record = (user_id, )
            
            # select 문은, dictionary = True 를 해준다.
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
                result_list[i]['date'] = record['date'].isoformat()
                result_list[i]['created_at'] = record['created_at'].isoformat()
                result_list[i]['updated_at'] = record['updated_at'].isoformat()
                i = i + 1                

            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()

            return {"error" : str(e)}, 503


        return { "result" : "success" , 
                "count" : len(result_list) ,
                "result_list" : result_list }, 200
    
    @jwt_required()
    def post(self):
        
        # api 실행 코드를 여기에 작성

        # 클라이언트에서, body 부분에 작성한 json 을
        # 받아오는 코드
        data = request.get_json()

        user_id = get_jwt_identity()

        # 받아온 데이터를 디비 저장하면 된다.
        try :
            # 데이터 insert 
            # 1. DB에 연결
            connection = get_connection()

            # 2. 쿼리문 만들기
            query = '''insert into notepad
                        (title, date, content , user_id)
                        values
                        (%s, %s ,%s, %s );'''
            
            record = (data['title'], data['date'], data['content'], user_id  )

            # 3. 커서를 가져온다.
            cursor = connection.cursor()

            # 4. 쿼리문을 커서를 이용해서 실행한다.
            cursor.execute(query, record)

            # 5. 커넥션을 커밋해줘야 한다 => 디비에 영구적으로 반영하라는 뜻
            connection.commit()

            # 6. 자원 해제
            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 503

        return {"result" : "success"}, 200
    
class NotepadModifiedResource(Resource):
    @jwt_required()
    def delete(self, memo_id):
        try :
            # 데이터 삭제
            # 1. DB에 연결
            connection = get_connection()

            user_id = get_jwt_identity()

            ### 먼저 recipe_id 에 들어있는 user_id가
            ### 이 사람인지 먼저 확인한다.

            query = '''select user_id 
                        from notepad
                        where id = %s;'''
            record = (memo_id, )
           
            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, record)

            result_list = cursor.fetchall()

            memo = result_list[0]

            if memo['user_id'] != user_id :
                cursor.close()
                connection.close()
                return {'error' : '다른 유저의 레시피를 삭제할 수 없습니다.'}, 401

            # 2. 쿼리문 만들기
            query = '''delete from notepad
                    where id = %s ;'''
            
            record = ( memo_id, )

            # 3. 커서를 가져온다.
            cursor = connection.cursor()

            # 4. 쿼리문을 커서를 이용해서 실행한다.
            cursor.execute(query, record)

            # 5. 커넥션을 커밋해줘야 한다 => 디비에 영구적으로 반영하라는 뜻
            connection.commit()

            # 6. 자원 해제
            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {'error' : str(e)}, 503

        return {'result' : 'success'}, 200

    ######### 이 부분만 해결하면 됨.
    @jwt_required()
    def put(self, memo_id) :

        # body에서 전달된 데이터를 처리
        data = request.get_json()

        user_id = get_jwt_identity()

        # 디비 업데이트 실행코드
        try :
            # 데이터 업데이트 
            # 1. DB에 연결
            connection = get_connection()

            ### 먼저 recipe_id 에 들어있는 user_id가
            ### 이 사람인지 먼저 확인한다.

            query = '''select user_id 
                        from notepad
                        where id = %s;'''
            record = (memo_id, )
           
            cursor = connection.cursor(dictionary = True)

            cursor.execute(query, record)

            result_list = cursor.fetchall()

            memo = result_list[0]

            if memo['user_id'] != user_id :
                cursor.close()
                connection.close()
                return {'error' : '다른 유저의 레시피를 수정할수 없습니다.'}, 401


            # 2. 쿼리문 만들기
            query = '''update notepad
                    set title = %s , date = %s , 
                    content = %s 
                    where id = %s;'''
            
            record = (data['title'], data['date'], data['content'], memo_id )

            # 3. 커서를 가져온다.
            cursor = connection.cursor()

            # 4. 쿼리문을 커서를 이용해서 실행한다.
            cursor.execute(query, record)

            # 5. 커넥션을 커밋해줘야 한다 => 디비에 영구적으로 반영하라는 뜻
            connection.commit()

            # 6. 자원 해제
            cursor.close()
            connection.close()

        except mysql.connector.Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {'error' : str(e)}, 503

        return {'result' :'success'}, 200