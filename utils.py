from passlib.hash import pbkdf2_sha256

# 원문 비밀번호를, 암호화 하는 함수
def hash_password(original_password):
    # 비밀번호는 복호화할 필요가 없다. 
    # 암호화만 되는 것을 hash 라고 부른다
    # 비밀번호만 작성하면 패턴을 찾기 쉬워지기 때문에
    # 랜덤의 시드값과 같이 특정 그룹만의 특정 문자열을 더하여 암호화를 시키는 게 salt라고 한다.

    salt = 'yh*hello12'

    password = str(original_password) + salt

    password = pbkdf2_sha256.hash(password)

    return password

# 비밀번호가 맞는지 확인하는 함수, 리턴은 True, False
def check_password(original_password, hashed_password):
    salt = 'yh*hello12'
    check = pbkdf2_sha256.verify(original_password+salt, hashed_password)
    return check
