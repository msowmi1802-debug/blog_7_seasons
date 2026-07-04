import random
from datetime import datetime, timedelta


def generate_otp():
    """
    Generate a random 6-digit OTP.
    """

    otp = random.randint(100000, 999999)

    return str(otp)
def save_otp(cursor,user_id, otp):


    expires_at = datetime.now() + timedelta(minutes=2)
    print("Saving OTP:", otp)
 
    print("User ID:", user_id)

    cursor.execute(
    """
    INSERT INTO otp_codes
    (user_id, otp, expires_at)

    VALUES (?, ?, ?)
    """,
    (
        user_id,
        otp,
        expires_at,
    ),
 )


def verify_user_otp(cursor, user_id, otp):

    cursor.execute(
        """
        SELECT *
        FROM otp_codes
        WHERE user_id = ?
        AND otp = ?
        """,
        (
            user_id,
            otp,
        ),
    )

    otp_record = cursor.fetchone()

    if otp_record is None:
        return False

    expires_at = datetime.fromisoformat(
        otp_record["expires_at"]
    )

    if datetime.now() > expires_at:
        return False

    return True   
