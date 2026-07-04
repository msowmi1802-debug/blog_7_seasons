import os
import smtplib

from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()



EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
if EMAIL_ADDRESS is None:
    print("🚨 CODE ALERT: EMAIL_ADDRESS is completely empty (None)!")
else:
    print("✅ CODE ALERT: EMAIL_ADDRESS successfully detected.")

if EMAIL_PASSWORD is None:
    print("🚨 CODE ALERT: EMAIL_PASSWORD is completely empty (None)!")
else:
    print("✅ CODE ALERT: EMAIL_PASSWORD successfully
 detected.")
if EMAIL_ADDRESS:
    EMAIL_ADDRESS = EMAIL_ADDRESS.strip()

if EMAIL_PASSWORD:
    EMAIL_PASSWORD = EMAIL_PASSWORD.strip()



def send_otp_email(receiver_email, otp):

    message = EmailMessage()

    message["Subject"] = "Your 7_Seasons OTP"

    message["From"] = EMAIL_ADDRESS

    message["To"] = receiver_email

    message.set_content(
        f"""
Hello,

Your OTP is:

{otp}

This OTP is valid for 2 minutes.

Do not share it with anyone.

- 7_Seasons
"""
    )

    with smtplib.SMTP("smtp.gmail.com", 2525,timeout=10) as smtp:

        smtp.starttls()

        smtp.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD,
        )

        smtp.send_message(message)
